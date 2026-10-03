from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from openai_codex import ApprovalMode, Codex, CodexConfig, Sandbox

import yaml

import token_usage
from visual_refs import build_visual_block


# ===========================================================================
# 用户配置区：Codex 执行复杂度档位（L0 / L1A / L1B / L1C / L2）
# ---------------------------------------------------------------------------
# 档位由用户配置：直接改下面的 ARCBENCH_EFFORT_DEFAULT，或用环境变量
# ARCBENCH_EFFORT 覆盖（优先级更高），例如：ARCBENCH_EFFORT=3 python3 main.py
#
#   L0  (0) —— 基线（旧行为）：完整 9 条自证契约 + 逐条证据罗列 + 读 SKILL.md
#              + verify gate。最稳、最贵。
#   L1A (1) —— 轻减·保留测试（最保守）：契约一字不改，只砍服务/浏览全项目/
#              结论一行；测试套件照跑。工程保障最接近 L0，省得最少。
#   L1B (2) —— 轻减·允许构建检查（折中）：同 L1A，但禁完整测试套件，允许跑
#              一次 build/tsc 抓编译错。省 15–25%，工程风险居中。
#   L1C (3) —— 轻减·禁测试（最激进）：同 L1A，且禁跑测试套件。省 15–25%，
#              工程风险最高。
#   L2  (4) —— 中减：契约压缩为四条铁律（精确可访问名/角色/hover opacity/
#              fixture 限定词），免逐条证据；仍读 SKILL.md + verify gate 兜底。
#              评分风险低，省 35–50% token。
# ---------------------------------------------------------------------------
# 铁律不可删：四条铁律是 P3 用 26 个失败换来的全部根因（CONTRACT.md），
# 平台 strict 测试逐字断言，任何档位都保留；L2 只是压缩表述。
# 实验提示：L1A / L1B / L1C 只差"测试策略"一个变量，其余完全相同，
# 适合做对照实验决定长期默认档。
# ===========================================================================
ARCBENCH_EFFORT_DEFAULT = 0


@dataclass(frozen=True)
class RequirementModule:
    index: int
    total: int
    node_id: str
    name: str
    subtree: dict[str, Any]


# Frontend interaction design spec (arcbench-frontend-spec skill). Opt-out via
# ARCBENCH_FRONTEND_SPEC=0 so the feature can be toggled without code edits.
FRONTEND_SPEC_SKILL = "arcbench-frontend-spec"

# Runtime telemetry skills (git checkpoints, progress signals, traceability).
# They only serve the ARC-Bench runtime frontend, never the generated code, and
# cost agent turns to run. Opt-in via ARCBENCH_TELEMETRY=1; off by default so
# Codex spends its turns on the implementation itself.
TELEMETRY_SKILLS = (
    "arcbench-checkpoint",
    "arcbench-runtime-signals",
    "arcbench-traceability",
)


def frontend_spec_enabled() -> bool:
    value = os.environ.get("ARCBENCH_FRONTEND_SPEC", "1").strip().lower()
    return value not in ("0", "false", "no", "off")


def verify_enabled() -> bool:
    value = os.environ.get("ARCBENCH_VERIFY", "1").strip().lower()
    return value not in ("0", "false", "no", "off")


def telemetry_enabled() -> bool:
    value = os.environ.get("ARCBENCH_TELEMETRY", "0").strip().lower()
    return value in ("1", "true", "yes", "on")


def visual_enabled() -> bool:
    """Reference-image analysis via the platform's visual model.

    Default ON (frontend-spec style): the vision calls only actually happen
    when the subtree references images AND a usable visual-model config is
    present (see visual_refs.build_visual_block), otherwise it degrades to
    warnings and a text-only prompt. Set ARCBENCH_VISUAL=0 to disable.
    """
    value = os.environ.get("ARCBENCH_VISUAL", "1").strip().lower()
    return value not in ("0", "false", "no", "off")


def verbose_enabled() -> bool:
    value = os.environ.get("ARCBENCH_VERBOSE", "0").strip().lower()
    return value in ("1", "true", "yes", "on")


_EFFORT_LABELS = {0: "L0", 1: "L1A", 2: "L1B", 3: "L1C", 4: "L2"}


def effort_level() -> int:
    """Resolve the configured execution-complexity gear.

    Levels: 0=L0, 1=L1A, 2=L1B, 3=L1C, 4=L2. Precedence: ARCBENCH_EFFORT env
    var (user override) > the head-of-file ARCBENCH_EFFORT_DEFAULT constant.
    Invalid values fall back to the default with a warning instead of failing
    the run.
    """
    raw = os.environ.get("ARCBENCH_EFFORT", str(ARCBENCH_EFFORT_DEFAULT)).strip()
    try:
        level = int(raw)
    except ValueError:
        level = -1
    if level not in (0, 1, 2, 3, 4):
        print(
            f"[codex] WARNING: invalid ARCBENCH_EFFORT={raw!r}; "
            f"falling back to L{ARCBENCH_EFFORT_DEFAULT}",
            flush=True,
        )
        return ARCBENCH_EFFORT_DEFAULT
    return level


def effort_label(level: int | None = None) -> str:
    """Human-readable gear label, e.g. 1 -> 'L1A'. Defaults to current level."""
    return _EFFORT_LABELS.get(effort_level() if level is None else level, f"L{level}")


def _verbose(*args: Any) -> None:
    """Print a verbose-level diagnostic; shown only with ARCBENCH_VERBOSE=1."""
    if verbose_enabled():
        print("[codex][verbose]", *args, flush=True)


# --- Token usage capture (S0) ----------------------------------------------
# Streaming a turn is the only way to see per-model-call usage (the blocking
# `Thread.run` returns a single cumulative snapshot per turn). The SDK pieces
# below are private, so their absence only disables the finer granularity.
try:  # pragma: no cover - depends on the pinned SDK layout
    from openai_codex._run import _collect_turn_result as _sdk_collect_turn_result
except Exception:  # noqa: BLE001
    _sdk_collect_turn_result = None

try:  # pragma: no cover - depends on the pinned SDK layout
    from openai_codex import TurnHandle as _SdkTurnHandle
except Exception:  # noqa: BLE001
    _SdkTurnHandle = None

# Set once a streaming attempt fails, so later modules use the blocking path
# instead of paying for another broken attempt.
_STREAMING_DISABLED = False
_STREAMING_NOTICE_SHOWN = False


def streaming_available(thread: Any) -> bool:
    """Pre-flight check before starting a turn (never mid-turn)."""
    global _STREAMING_NOTICE_SHOWN
    if _STREAMING_DISABLED:
        return False
    reason = ""
    if _sdk_collect_turn_result is None:
        reason = "the SDK exposes no _collect_turn_result"
    elif not hasattr(thread, "turn"):
        reason = "the SDK thread exposes no turn()"
    elif _SdkTurnHandle is not None and not hasattr(_SdkTurnHandle, "stream"):
        reason = "TurnHandle exposes no stream()"
    if not reason:
        return True
    if not _STREAMING_NOTICE_SHOWN:
        _STREAMING_NOTICE_SHOWN = True
        print(
            f"[codex] note: per-call token capture unavailable ({reason}); "
            "recording per-turn totals only",
            flush=True,
        )
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Implement an ARC-Bench task with Codex.")
    parser.add_argument("requirement_path", help="Directory containing requirements.yaml.")
    parser.add_argument("--output-dir", required=True, help="Target directory for the generated project.")
    parser.add_argument(
        "--type",
        dest="task_type",
        default=os.environ.get("ARCBENCH_TASK_TYPE", "web"),
        help="Task type supplied by ARC-Bench.",
    )
    return parser.parse_args()


def copy_template_contents(template_dir: Path, output_dir: Path) -> None:
    """Copy the bundled template's children into the output directory."""
    if not template_dir.is_dir():
        # ARC-Bench assembles the authoritative task template before invoking
        # the agent (and evolution runs already contain the previous-stage
        # application). Reference archives intentionally omit a duplicate
        # template directory, so preserve the prepared output in that case.
        if output_dir.is_dir() and any(output_dir.iterdir()):
            print(
                f"[codex] template dir missing ({template_dir}); output already "
                "populated, skipping copy",
                flush=True,
            )
            return
        print(
            f"[codex] ERROR: starter template directory not found: {template_dir}",
            flush=True,
        )
        raise FileNotFoundError(f"Starter template directory not found: {template_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for source in sorted(template_dir.iterdir()):
        if source.name == "template.yaml":
            continue
        destination = output_dir / source.name
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)
        copied += 1
        _verbose(f"copied template item: {source.name}")
    print(f"[codex] copied {copied} template item(s) to {output_dir}", flush=True)


def copy_skills_to_output(skills_dir: Path, output_dir: Path, exclude: set[str] | None = None) -> Path:
    """Make the bundled ARC-Bench skills available inside Codex's workspace.

    Optional ``exclude`` skips top-level skill directories (used to uninstall a
    skill from the produced artifact without deleting its source).
    """
    if not skills_dir.is_dir():
        print(f"[codex] ERROR: skills directory not found: {skills_dir}", flush=True)
        raise FileNotFoundError(f"Skills directory not found: {skills_dir}")
    destination = output_dir / ".codex" / "skills"
    exclude = exclude or set()
    if not exclude:
        shutil.copytree(skills_dir, destination, dirs_exist_ok=True)
        print(f"[codex] copied all skills to {destination}", flush=True)
        return destination
    destination.mkdir(parents=True, exist_ok=True)
    copied = 0
    excluded = 0
    for source in sorted(skills_dir.iterdir()):
        if source.name in exclude:
            excluded += 1
            _verbose(f"excluded skill: {source.name}")
            continue
        target = destination / source.name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
        copied += 1
        _verbose(f"copied skill: {source.name}")
    print(
        f"[codex] copied {copied} skill(s) to {destination} (excluded {excluded})",
        flush=True,
    )
    return destination


def load_root_modules(requirements_dir: Path) -> list[RequirementModule]:
    requirements_path = requirements_dir / "requirements.yaml"
    if not requirements_path.is_file():
        print(
            f"[codex] ERROR: requirements.yaml not found: {requirements_path}",
            flush=True,
        )
        raise FileNotFoundError(f"requirements.yaml not found: {requirements_path}")

    payload = yaml.safe_load(requirements_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or str(payload.get("id") or "").strip() != "ROOT":
        detail = (
            f"id={payload.get('id')!r}"
            if isinstance(payload, dict)
            else f"payload type={type(payload).__name__}"
        )
        print(
            f"[codex] ERROR: requirements.yaml must contain a ROOT mapping ({detail})",
            flush=True,
        )
        raise ValueError("requirements.yaml must contain a ROOT mapping")

    raw_children = payload.get("children", [])
    children = [item for item in raw_children if isinstance(item, dict)]
    if not children:
        print("[codex] ERROR: ROOT must contain at least one child module", flush=True)
        raise ValueError("ROOT must contain at least one child module")
    if isinstance(raw_children, list) and len(children) != len(raw_children):
        _verbose(f"filtered {len(raw_children) - len(children)} non-dict ROOT child entrie(s)")

    modules: list[RequirementModule] = []
    for index, subtree in enumerate(children, start=1):
        node_id = str(subtree.get("id") or subtree.get("req_id") or "").strip()
        if not node_id:
            print(f"[codex] ERROR: ROOT child {index} has no id", flush=True)
            raise ValueError(f"ROOT child {index} has no id")
        name = str(subtree.get("name") or node_id).strip()
        modules.append(
            RequirementModule(
                index=index,
                total=len(children),
                node_id=node_id,
                name=name,
                subtree=subtree,
            )
        )
        _verbose(f"module {index}/{len(children)}: {node_id} - {name}")
    print(f"[codex] loaded {len(modules)} ROOT module(s) from {requirements_path}", flush=True)
    return modules


CODEX_ROLLOUT_DIR = ".arc/codex-rollouts"
CODEX_ROLLOUT_MAX_MB = 30.0
_ROLLOUT_LIMIT_WARNED = False


def _collect_codex_rollouts(output_dir: Path, since: float | None = None) -> int:
    """Copy the CLI's rollout JSONL into the artifact (S0 cross-check source).

    The Codex CLI mirrors every model response's usage into
    ``$CODEX_HOME/sessions/**/rollout-*.jsonl`` (``token_usage_record`` events
    carrying response_id, per-call and per-turn/thread totals). That home lives
    inside the container and dies with it, while the in-process ledger only
    keeps what this route parsed. Copying the files out gives an independent,
    finer-grained audit trail — and unlike pointing CODEX_HOME elsewhere, it
    touches nothing the CLI reads.

    Best effort: returns the number of files copied; any failure warns and
    returns 0. Disable with ARCBENCH_CODEX_ROLLOUTS=0.
    """
    global _ROLLOUT_LIMIT_WARNED
    raw = os.environ.get("ARCBENCH_CODEX_ROLLOUTS", "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return 0
    try:
        source = os.environ.get("CODEX_HOME", "").strip()
        home = Path(source) if source else Path.home() / ".codex"
        sessions = home / "sessions"
        if not sessions.is_dir():
            return 0
        target_root = Path(output_dir) / CODEX_ROLLOUT_DIR
        copied = 0
        budget = CODEX_ROLLOUT_MAX_MB * 1024 * 1024
        used = sum(f.stat().st_size for f in target_root.rglob("*") if f.is_file()) if target_root.is_dir() else 0
        for path in sorted(sessions.rglob("rollout-*.jsonl")):
            try:
                stat = path.stat()
            except OSError:
                continue
            if since is not None and stat.st_mtime < since:
                continue
            if used + stat.st_size > budget:
                if not _ROLLOUT_LIMIT_WARNED:
                    _ROLLOUT_LIMIT_WARNED = True
                    print(
                        f"[codex] WARNING: rollout copies stopped at {CODEX_ROLLOUT_MAX_MB:.0f}MB "
                        "(set ARCBENCH_CODEX_ROLLOUTS=0 to opt out)",
                        flush=True,
                    )
                break
            target = target_root / path.relative_to(sessions)
            try:
                if target.is_file() and target.stat().st_size == stat.st_size:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            except OSError:
                continue
            used += stat.st_size
            copied += 1
        return copied
    except Exception as exc:  # noqa: BLE001 - an audit copy must never break a run
        print(f"[codex] WARNING: rollout copy failed: {exc}", flush=True)
        return 0


def _codex_config(CodexConfig: Any) -> Any:
    env = os.environ.copy()
    overrides: list[str] = []
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
    if base_url:
        env["OPENAI_BASE_URL"] = base_url
        overrides.append(f"openai_base_url={json.dumps(base_url)}")
        # Route model calls through a custom provider whose name is NOT "OpenAI"
        # so the Codex runtime never selects remote compaction v2: the ARC-Bench
        # gateway / DeepSeek backend does not implement OpenAI's native
        # compaction protocol, which fatals with "remote compaction v2 expected
        # exactly one compaction output item". Compaction then falls back to the
        # local summarization path, which the gateway serves like any model call.
        overrides.append("model_provider=arcbench")
        overrides.append(f"model_providers.arcbench.name={json.dumps('arc-bench-gateway')}")
        overrides.append(f"model_providers.arcbench.base_url={json.dumps(base_url)}")
        overrides.append(f"model_providers.arcbench.env_key={json.dumps('OPENAI_API_KEY')}")
        overrides.append(f"model_providers.arcbench.wire_api={json.dumps('responses')}")
        print(
            f"[codex] OPENAI_BASE_URL override active ({len(overrides)} config override(s))",
            flush=True,
        )
        _verbose(f"config overrides: {overrides}")
    else:
        print("[codex] OPENAI_BASE_URL unset; no config overrides", flush=True)
    return CodexConfig(env=env, config_overrides=tuple(overrides))


def _developer_instructions(
    skills_dir: Path,
    include_frontend_spec: bool = True,
    include_telemetry: bool = True,
) -> str:
    lines = [
        "You implement an ARC-Bench application in the current working directory.",
        "The directory already contains an initialized starter application. Preserve existing work.",
        "",
        "Each request supplies exactly one direct child subtree of ROOT. Implement that subtree,",
        "including all of its descendants, in the current project. Do not ask for or read the",
        "complete requirements.yaml. Make practical code changes and leave the application runnable.",
    ]
    if include_telemetry:
        lines += [
            "",
            f"ARC-Bench skills are available in {skills_dir}:",
            "- Read arcbench-runtime-signals/SKILL.md to report module progress when useful.",
            "- Read arcbench-traceability/SKILL.md when recording generated interfaces or tests.",
            "- Read arcbench-checkpoint/SKILL.md when creating a coherent git checkpoint.",
            "Run their scripts from the current project with --project-dir .; do not hand-write",
            "runner events or traceability JSON when a bundled script covers the action.",
        ]
    if include_frontend_spec:
        lines += [
            "",
            "- Read arcbench-frontend-spec/SKILL.md before implementing frontend interaction code",
            "(buttons, menus, dialogs, notifications, hover behavior, forms).",
        ]
    return "\n".join(lines).strip()


# Full 9-item assertable-contract checklist (used verbatim by L0 and L1).
# L0 appends the per-item evidence dump; L1 compresses the verdicts and adds
# execution constraints. Kept separate from the header so both can share it.
_FULL_CONTRACT_ITEMS = """\
1. Every named fixture entity this subtree mentions (e.g. a note titled
   "Study schedule", a book named "book_8_2", a shelf named "Shelf 4.1",
   a user account, a product named "Hummingbird detail t-shirt") MUST exist
   verbatim in the backend seed data, and be reachable on the initial screen
   OR on a page one click from a primary navigation link. On ANY listing page
   (products, books, shelves, posts, orders), a named fixture MUST render on
   the FIRST PAGE of that listing: official tests click fixtures by name on
   page 1 and never paginate, so an entity that only appears after clicking
   page 2+ is unreachable to them (observed p13 prestashop: "Hummingbird
   detail t-shirt" seeded on Men page 2 -> 13 product-flow tests failed).
   Adjust seed order / page size so every named entity lands on page 1; the
   gate probe `fixtures` blocks on "only visible after pagination". Any
   display name the requirement does NOT quote
   (user first/last name, alias, custom title) MUST be keyword-neutral:
   no action verb or field word root (delete/remove/edit/rename/create/
   update/save/cart/name/address/search/view/...) — these names render
   in global chrome (header full-name link, sidebar, breadcrumb) where
   substring locators collide with them — see
   arcbench-frontend-spec/SKILL.md rule G.
2. Every data-entry <form> has an accessible name
   (aria-label="Login form" style); a logo/home link has "logo" in its
   accessible name; list items expose entity names in their accessible
   name.
3. Every state-changing action shows assertable feedback: create/save
   navigates to the created entity's details page; delete/archive shows
   wording matching the action.
4. The authenticated homepage renders the state-widget sections the
   requirements name (recent drafts / recently viewed / favourites /
   recently updated).
5. No global control, data-entry <form>, toolbar/group/dialog/aside or
   list-row wrapper (li/div) carries a form-field word root or a page
   entity name in its accessible name. A form's own aria-label must share
   NO WORD with any field label inside it ("Catalog lookup" / "Recipient
   information" are fine; "Address form" AND "New address details" both
   still shadow the "Address" field, because the field resolver takes the
   first getByLabel(/word/i) hit in document order and an ancestor always
   precedes its descendants, so fill() then fails with "Element is not an
   <input>"). A list-row wrapper must not repeat the row's entity name.
   The gate probe `label-shadowing` blocks on any hit; renaming that keeps
   the word does not clear it. The authoritative word-root list and
   container rules live in arcbench-frontend-spec/SKILL.md rule D2.
6. Every interactive control this subtree's scenario text quotes by name
    (e.g. "Take a note", "Settings", "Undo", "Archive", "More options",
    "Pin note", "Note editor", "Search") has an accessible name EXACTLY
    equal to that quoted name — no ellipsis, no ": detail" / "— detail"
    suffix, no extra " menu"/" button"/" note" suffix, no decorative
    prefix. Decoration belongs in visible text/placeholder/title, never
    in aria-label; a visible-text button may pair exact text with an
    aria-label (visible "Take a note..." + aria-label="Take a note").
    Screenshot visible text is NOT authoritative — the scenario-quoted
    name is (see arcbench-frontend-spec/SKILL.md rule B).
7. Control roles match official semantics: navigation/list items/primary
    CTAs a test may click are <button> (or explicit role="button"), not
    bare links; selectable dialog options (labels/tags/flags) are native
    checkboxes or groups, not button-simulated toggles; an input the
    scenario calls a textbox is type="text" (type="search" resolves to
    role searchbox, which does not match getByRole('textbox')) — see
    arcbench-frontend-spec/SKILL.md rules A and D1. EXCEPTION (SKILL rule
    E.5, narrowed after p20): a chrome entry may lose its button role ONLY
    when the graded suite resolves that name globally AND the same name is a
    page action on the page — e.g. a header "Sign in" as a plain link on
    /login so the login form's "SIGN IN" submit is the only button with that
    name (observed p13 prestashop: 12 account/checkout tests failed without
    it). A navigation entry that lives inside <nav>/<aside>/
    role="complementary" is NEVER a candidate for that demotion: official
    helpers scope those queries (getByRole('complementary').getByRole(
    'button',{name:/^Archive$/i})), so removing the button role makes every
    such test time out (observed p20 keep: 6 tests lost, 90.6 -> 40.6).
    Prefer making the page action win document order, or giving it its own
    requirement qualifier. Gate probes: `name-shadow` (blocks only on a
    proven global collision) and `landmark-roles` (blocks a demoted landmark
    entry).
8. Hover-revealed action rows stay in the accessibility tree: revealed
    with opacity only, never visibility/display-hidden (see
    arcbench-frontend-spec/SKILL.md rule A).
9. Every "Seed data: ..." clause in this subtree's requirement text is a
   STATE contract, not just an existence list. Reproduce each qualifier
   verbatim in the backend seed data: "that is not pinned" -> the note
   is seeded WITHOUT pinned:true; "with the \"Work\" label" / "without
   the \"Work\" label" -> the note's labels include/exclude it; "with a
   white background" -> color stays default/white; "active"/"archived"
   -> the note starts unarchived/archived; "default label X" -> a label
   row named X exists. Do not flip or omit a state qualifier (a seed
   that pins a note the requirement says is not pinned fails the gate).
   When listing seed evidence, state the QUALIFIER outcome too, e.g.
   '"Meeting agenda 2.8.2" -> pinned=false (requirement: not pinned)'.
10. Seed initial state = the OFFICIAL TEST flow's pre-action state (arrange-
   act; -t tasks: the official tests are the final logic). A state-changing
   action the tests perform FIRST — delete/remove/trash, archive, pin,
   favorite — requires its target to START in the pre-action state: a
   "deletable" note must be on the main list (NOT pre-trashed), a book whose
   test clicks "Favorite" must NOT be pre-favorited, an "archived" action
   needs an active target. Never pre-set an end-state just to fill a view
   (observed: p19 keep REQ-2.3.3 pre-trashed 'Delete me 2.3.3' -> the delete
   step found no card; p18 bookstack REQ-8.2 pre-favorited Book 8.2 -> the
   Favorite button already read "Unfavorite"). The gate parses the official
   spec flow (staging/tests-context) and blocks on pre-set end-states; when
   the specs are not visible, derive the pre-action state from the
   requirement's WHEN step ("clicks Delete" -> target starts present)."""

# Execution constraints for the L1 family (A/B/C differ ONLY in the test
# strategy — everything else is identical, so they form a clean controlled
# experiment). Ordered by strength, A (most conservative) -> C (most
# aggressive). L0 does NOT get these so the baseline keeps the original
# behavior byte-for-byte.
#
# L1A: keep the test suite (and the full 9-item checklist), cut only the
# cheap things — no server, no whole-project re-browsing, one-line summary.
# Most conservative: closest to L0 in engineering safety.
_BEHAVIOR_CONSTRAINT_A = """\
The codebase is already substantially complete. Implement this module with
the minimal diff: do not restructure existing code, do not add unrelated
features, and do not start a long-running server. Read only the files this
module needs; do not re-browse the whole project."""

# L1B: forbid the full test suite but ALLOW one build / type-check pass so
# compile errors are still caught cheaply (recommended middle ground).
_BEHAVIOR_CONSTRAINT_B = """\
The codebase is already substantially complete. Implement this module in ONE
pass with the minimal diff: do not restructure existing code, do not add
unrelated features, and do not start a long-running server. Do not run the
full test suite, but you MAY run a single build or type-check (e.g.
npm run build / tsc) to catch compile errors before finishing. Read only the
files this module needs; do not re-browse the whole project."""

# L1C: forbid running the test suite entirely (max token saving, most risk).
# Most aggressive of the L1 family.
_BEHAVIOR_CONSTRAINT_C = """\
The codebase is already substantially complete. Implement this module in ONE
pass with the minimal diff: do not restructure existing code, do not add
unrelated features, do not run the test suite, and do not start a long-running
server. Read only the files this module needs; do not re-browse the whole
project."""

# L2 compact contract: the four iron rules behind all 26 P3 failures
# (CONTRACT.md), plus codebase-convention guidance to replace the verbose
# checklist. Verify silently; report only deviations.
_COMPACT_CONTRACT = """\
Data contract (verify each silently; report only deviations):
1. Accessible names quoted in the scenario text match EXACTLY — no ellipsis,
   no "menu" / ": detail" / "— detail" suffix, no decorative prefix.
   Screenshot visible text is NOT authoritative; the scenario-quoted name is.
2. Roles: clickable CTAs are <button> (or explicit role="button"), not bare
   links; selectable dialog options are native checkboxes or groups; a
   scenario "textbox" input is type="text", not type="search".
3. Hover-revealed action rows stay in the accessibility tree: reveal with
   opacity only, never visibility/display-hidden.
4. Every "Seed data: ..." clause is a STATE contract: reproduce each qualifier
   verbatim (pinned / not pinned, labeled / unlabeled, archived / active,
   default color); do not flip or omit a qualifier.
5. Seed initial state = the test flow's pre-action state: a note the test
   DELETES first must start on the main list (not pre-trashed); a book the
   test clicks "Favorite" on must start unfavorited. Never pre-set an
   end-state to fill a view.
For form aria-labels, logo naming, feedback wording and homepage widgets,
follow the existing patterns already established in this codebase.
Finish with a one-line summary of files changed."""

_CONTRACT_HEADER = (
    "Data contract (assertable-contract checklist — verify each item before\n"
    "finishing; the post-implementation gate re-checks these automatically):\n"
)


def _contract_section(effort: int) -> str:
    """Build the contract + execution-constraint block for the module prompt.

    L0:  full 9-item checklist + per-item evidence dump (original behavior).
    L1A: full checklist verbatim; test suite kept; verdicts one short line.
         Most conservative of the L1 family (closest to L0).
    L1B: same as L1A but one build/type-check allowed instead of the suite.
    L1C: same as L1A but test suite forbidden. Most aggressive of L1 family.
    L2:  checklist replaced by the four iron rules; L1C-style (most
         aggressive) constraints.
    """
    if effort == 0:
        return (
            _CONTRACT_HEADER
            + _FULL_CONTRACT_ITEMS
            + "\nBefore finishing, list each fixture entity -> seed evidence "
            "(file + row)\n-> reachable page, plus the outcome of each "
            "checklist item above.\n\n"
            "Finish by summarizing the files changed. Do not start a "
            "long-running server."
        )
    if effort in (1, 2, 3):
        base = (
            _CONTRACT_HEADER
            + _FULL_CONTRACT_ITEMS
            + "\nBefore finishing, verify each checklist item silently and "
            "give its verdict in\none short line — no long evidence dump.\n\n"
            "Finish by summarizing the files changed in one line.\n\n"
        )
        if effort == 1:
            return base + _BEHAVIOR_CONSTRAINT_A
        if effort == 2:
            return base + _BEHAVIOR_CONSTRAINT_B
        return base + _BEHAVIOR_CONSTRAINT_C
    return _BEHAVIOR_CONSTRAINT_C + "\n\n" + _COMPACT_CONTRACT


def _module_prompt(
    module: RequirementModule,
    requirements_dir: Path,
    completed_ids: list[str],
    skills_dir: Path,
    visual_block: str = "",
) -> str:
    completed = ", ".join(completed_ids) if completed_ids else "none"
    effort = effort_level()
    prompt = textwrap.dedent(
        f"""
        Implement ROOT module {module.index}/{module.total}: {module.node_id} - {module.name}

        Requirement source directory: {requirements_dir}
        Previously completed ROOT modules: {completed}
        Skills directory: {skills_dir}

        Implement this complete subtree in the current target directory:
        ```json
        {json.dumps(module.subtree, ensure_ascii=False, indent=2)}
        ```
        """
    ).strip()
    prompt += "\n\n" + _contract_section(effort)
    if visual_block:
        prompt += "\n" + visual_block
    return prompt


_COMPACTION_FAILURE_MARKERS = ("remote compact", "compaction")


def _load_completed(progress_file: Path) -> list[str]:
    """Load the on-disk list of completed module ids for resumability."""
    try:
        data = json.loads(progress_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _verbose(f"no progress file at {progress_file}; starting fresh")
        return []
    except (OSError, ValueError) as exc:
        print(
            f"[codex] WARNING: could not read progress file {progress_file}: "
            f"{exc}; starting fresh",
            flush=True,
        )
        return []
    ids = data.get("completed_ids") if isinstance(data, dict) else None
    result = [str(item) for item in ids] if isinstance(ids, list) else []
    _verbose(f"progress file {progress_file}: {len(result)} completed id(s) loaded")
    return result


def _save_completed(progress_file: Path, completed_ids: list[str]) -> None:
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        progress_file.write_text(
            json.dumps({"completed_ids": completed_ids}, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        print(
            f"[codex] ERROR: failed to write progress file {progress_file}: {exc}",
            flush=True,
        )
        raise
    _verbose(f"progress saved ({len(completed_ids)} completed) -> {progress_file}")


def _disable_streaming(reason: str) -> None:
    """Stop attempting per-call capture after the first failure."""
    global _STREAMING_DISABLED
    if not _STREAMING_DISABLED:
        _STREAMING_DISABLED = True
        print(
            f"[codex] WARNING: per-call token capture disabled ({reason}); "
            "recording per-turn totals only",
            flush=True,
        )


def _record_usage_notification(
    output_dir: Path,
    event: Any,
    *,
    phase: str,
    module_id: str,
    module_index: int,
    attempt: int,
    model: str | None,
) -> None:
    """Record one model response's usage from a turn-stream notification."""
    payload = getattr(event, "payload", None)
    usage = getattr(payload, "token_usage", None)
    if usage is None:
        return
    per_call = token_usage.breakdown_to_dict(getattr(usage, "last", None))
    if not per_call:
        return
    token_usage.append(
        output_dir,
        {
            "phase": phase,
            "kind": "model_call",
            "module_id": module_id,
            "module_index": module_index,
            "attempt": attempt,
            "model": model or "",
            "effort": effort_label(),
            "thread_id": str(getattr(payload, "thread_id", "") or ""),
            "turn_id": str(getattr(payload, "turn_id", "") or ""),
            "context_window": getattr(usage, "model_context_window", None),
            **per_call,
        },
    )


def _record_turn_total(
    output_dir: Path,
    result: Any,
    *,
    phase: str,
    module_id: str,
    module_index: int,
    attempt: int,
    model: str | None,
) -> None:
    """Record the turn's cumulative usage (also the plain-run fallback)."""
    usage = getattr(result, "usage", None)
    totals = token_usage.breakdown_to_dict(getattr(usage, "total", None))
    if not totals:
        return
    token_usage.append(
        output_dir,
        {
            "phase": phase,
            "kind": "turn_total",
            "module_id": module_id,
            "module_index": module_index,
            "attempt": attempt,
            "model": model or "",
            "effort": effort_label(),
            "turn_id": str(getattr(result, "id", "") or ""),
            "context_window": getattr(usage, "model_context_window", None),
            **totals,
        },
    )


def _run_turn(
    thread: Any,
    prompt: str,
    *,
    output_dir: Path,
    phase: str,
    module_id: str,
    module_index: int,
    attempt: int,
    model: str | None,
) -> Any:
    """Run exactly one turn, recording token usage at the finest available grain.

    Preferred path: ``thread.turn()`` + ``handle.stream()``, which emits one
    token-usage notification per model response (input / cached / cache-write /
    output / reasoning, attributed to the turn). When the SDK does not expose
    that surface, fall back to the blocking ``thread.run()``, which still records
    the turn's cumulative totals.
    """
    meta = {
        "phase": phase,
        "module_id": module_id,
        "module_index": module_index,
        "attempt": attempt,
        "model": model,
    }
    if streaming_available(thread):
        handle = thread.turn(prompt)
        turn_id = getattr(handle, "id", None)
        if turn_id:
            def relay() -> Any:
                for event in handle.stream():
                    try:
                        _record_usage_notification(output_dir, event, **meta)
                    except Exception as exc:  # noqa: BLE001 - capture is best effort
                        print(f"[codex] WARNING: usage capture failed: {exc}", flush=True)
                    yield event

            try:
                result = _sdk_collect_turn_result(relay(), turn_id=turn_id)
            except Exception as exc:  # noqa: BLE001 - keep the run's failure semantics
                _disable_streaming(f"stream failed: {type(exc).__name__}: {exc}")
                raise
            _record_turn_total(output_dir, result, **meta)
            return result
        _disable_streaming("turn handle exposes no id")
    result = thread.run(prompt)
    _record_turn_total(output_dir, result, **meta)
    return result


def _run_module_with_retry(
    codex: Codex,
    output_dir: Path,
    module: RequirementModule,
    requirements_dir: Path,
    completed_ids: list[str],
    skills_dir: Path,
    model: str | None,
    max_attempts: int = 3,
    include_frontend_spec: bool = True,
    include_telemetry: bool = True,
    visual_block: str = "",
) -> Any:
    """Implement one module on a fresh thread.

    A fresh thread per module keeps every turn's context small, so the Codex
    runtime never auto-compacts across modules (remote compaction v2 is
    incompatible with the ARC-Bench gateway / DeepSeek backend). If the runtime
    still fatals on compaction, retry the module on a brand-new thread.
    """
    for attempt in range(1, max_attempts + 1):
        _verbose(
            f"module {module.node_id}: starting attempt {attempt}/{max_attempts} "
            f"(model={model}, cwd={output_dir})"
        )
        thread = codex.thread_start(
            cwd=str(output_dir),
            sandbox=Sandbox.full_access,
            approval_mode=ApprovalMode.deny_all,
            model=model,
            developer_instructions=_developer_instructions(
                skills_dir, include_frontend_spec, include_telemetry
            ),
        )
        prompt = _module_prompt(module, requirements_dir, completed_ids, skills_dir, visual_block)
        _verbose(f"module {module.node_id}: prompt is {len(prompt)} chars")
        try:
            result = _run_turn(
                thread,
                prompt,
                output_dir=output_dir,
                phase="module",
                module_id=module.node_id,
                module_index=module.index,
                attempt=attempt,
                model=model,
            )
        except RuntimeError as exc:
            message = str(exc)
            if any(marker in message for marker in _COMPACTION_FAILURE_MARKERS) and attempt < max_attempts:
                print(
                    f"[codex] compaction failed on {module.node_id}; retrying with a "
                    f"fresh thread ({attempt}/{max_attempts}): {message}",
                    flush=True,
                )
                continue
            print(
                f"[codex] ERROR: RuntimeError on {module.node_id} "
                f"(attempt {attempt}/{max_attempts}): {message}",
                flush=True,
            )
            raise
        if getattr(result, "error", None) is not None:
            print(
                f"[codex] ERROR: Codex failed on {module.node_id}: {result.error}",
                flush=True,
            )
            raise RuntimeError(f"Codex failed on {module.node_id}: {result.error}")
        _verbose(f"module {module.node_id}: attempt {attempt} returned successfully")
        print(
            "[codex][usage] "
            + token_usage.format_row(
                f"module {module.node_id}",
                token_usage.scope(output_dir, phase="module", module_id=module.node_id),
            ),
            flush=True,
        )
        return result
    print(
        f"[codex] ERROR: Codex failed on {module.node_id} after {max_attempts} attempts",
        flush=True,
    )
    raise RuntimeError(f"Codex failed on {module.node_id} after {max_attempts} attempts")


def implement_modules(
    requirements_dir: Path,
    output_dir: Path,
    modules: list[RequirementModule],
    skills_dir: Path,
    include_frontend_spec: bool = True,
    include_telemetry: bool = True,
) -> None:
    model = os.environ.get("MODEL", "").strip() or None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    wall_started = time.time()
    print(f"[codex] model: {model if model else '<unset>'}", flush=True)
    print(f"[codex] api key: {'set' if api_key else 'unset'}", flush=True)
    progress_file = output_dir / ".arc" / "completed_modules.json"

    completed_ids = _load_completed(progress_file)
    pending = [module for module in modules if module.node_id not in completed_ids]
    print(
        f"[codex] Resuming with {len(completed_ids)}/{len(modules)} completed; "
        f"{len(pending)} pending module(s).",
        flush=True,
    )
    _verbose(f"completed ids: {completed_ids}")
    _verbose(f"pending module ids: {[m.node_id for m in pending]}")

    with Codex(config=_codex_config(CodexConfig)) as codex:
        if api_key:
            print("[codex] logging in with OPENAI_API_KEY", flush=True)
            codex.login_api_key(api_key)
        for module in pending:
            print(f"[codex] Implementing {module.index}/{module.total}: {module.node_id}", flush=True)
            visual_block = ""
            if visual_enabled():
                visual_block = build_visual_block(
                    module.subtree,
                    requirements_dir,
                    output_dir,
                    verbose=verbose_enabled(),
                )
            start = time.monotonic()
            _run_module_with_retry(
                codex,
                output_dir,
                module,
                requirements_dir,
                completed_ids,
                skills_dir,
                model,
                include_frontend_spec=include_frontend_spec,
                include_telemetry=include_telemetry,
                visual_block=visual_block,
            )
            elapsed = time.monotonic() - start
            completed_ids.append(module.node_id)
            _save_completed(progress_file, completed_ids)
            # Keep the CLI's per-call rollout trail close to the artifact, so a
            # timeout mid-run still leaves an audit trail for the modules done.
            copied = _collect_codex_rollouts(output_dir, since=wall_started)
            if copied:
                _verbose(f"copied {copied} codex rollout file(s) into {CODEX_ROLLOUT_DIR}")
            print(
                f"[codex] Completed {module.node_id} in {elapsed:.1f}s "
                f"({len(completed_ids)}/{len(modules)} done)",
                flush=True,
            )


def _main() -> int:
    started = time.monotonic()
    wall_started = time.time()
    args = parse_args()
    requirements_dir = Path(args.requirement_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    print(f"[codex] task type: {args.task_type}", flush=True)
    print(f"[codex] requirement dir: {requirements_dir}", flush=True)
    print(f"[codex] output dir: {output_dir}", flush=True)
    if not requirements_dir.is_dir():
        print(
            f"[codex] ERROR: requirement directory not found: {requirements_dir}",
            flush=True,
        )
        raise FileNotFoundError(f"Requirement directory not found: {requirements_dir}")

    agent_root = Path(__file__).resolve().parent
    copy_template_contents(agent_root / "template", output_dir)
    include_frontend_spec = frontend_spec_enabled()
    include_telemetry = telemetry_enabled()
    print(
        f"[codex] features: frontend_spec={include_frontend_spec}, "
        f"telemetry={include_telemetry}, visual={visual_enabled()}, "
        f"effort={effort_label()}",
        flush=True,
    )
    excluded_skills: set[str] = set()
    if not include_frontend_spec:
        excluded_skills.add(FRONTEND_SPEC_SKILL)
    if not include_telemetry:
        excluded_skills.update(TELEMETRY_SKILLS)
    skills_dir = copy_skills_to_output(agent_root / "skills", output_dir, exclude=excluded_skills)
    modules = load_root_modules(requirements_dir)
    implement_modules(
        requirements_dir,
        output_dir,
        modules,
        skills_dir,
        include_frontend_spec=include_frontend_spec,
        include_telemetry=include_telemetry,
    )

    if verify_enabled():
        report = _run_verification(requirements_dir, output_dir)
        gate = (report or {}).get("gate") or {}
        if gate.get("passed") is False:
            print(
                f"[codex][gate] HARD GATE FAILED with {len(gate.get('blocking') or [])} "
                "blocking defect(s); starting exactly one repair round",
                flush=True,
            )
            _repair_against_gate(
                requirements_dir,
                output_dir,
                skills_dir,
                report,
                include_frontend_spec=include_frontend_spec,
                include_telemetry=include_telemetry,
            )
            final = _run_verification(requirements_dir, output_dir)
            final_gate = (final or {}).get("gate") or {}
            if final_gate.get("passed") is True:
                print("[codex][gate] repair round cleared the gate", flush=True)
            else:
                print(
                    "[codex][gate] gate still failing after one repair round: "
                    f"{json.dumps(final_gate, ensure_ascii=False)}",
                    flush=True,
                )
        else:
            print(
                f"[codex][gate] gate verdict: {json.dumps(gate, ensure_ascii=False)}",
                flush=True,
            )
    else:
        print("[codex] verification disabled (ARCBENCH_VERIFY=0)", flush=True)

    copied = _collect_codex_rollouts(output_dir, since=wall_started)
    if copied:
        print(f"[codex][usage] copied {copied} codex rollout file(s) -> {CODEX_ROLLOUT_DIR}", flush=True)
    _report_token_usage(output_dir)
    print(
        f"[codex] finished {len(modules)} module(s) in {time.monotonic() - started:.1f}s; "
        f"output at {output_dir}",
        flush=True,
    )
    return 0


def _report_token_usage(output_dir: Path) -> None:
    """Print the per-phase token ledger summary (S0). Informational only."""
    try:
        records = token_usage.read_all(output_dir)
        if not records:
            print(
                "[codex][usage] no token records captured "
                f"(ledger: {token_usage.ledger_path(output_dir)})",
                flush=True,
            )
            return
        for phase in ("module", "repair", "vision"):
            subset = [record for record in records if record.get("phase") == phase]
            if subset:
                print(
                    "[codex][usage] "
                    + token_usage.format_row(phase, token_usage.summarize(subset)),
                    flush=True,
                )
        print(
            "[codex][usage] "
            + token_usage.format_row("run total", token_usage.summarize(records)),
            flush=True,
        )
        print(f"[codex][usage] ledger: {token_usage.ledger_path(output_dir)}", flush=True)
    except Exception as exc:  # noqa: BLE001 - reporting must never break a run
        print(f"[codex] WARNING: token usage report failed: {exc}", flush=True)


def _run_verification(requirements_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Run the post-implementation verification (see verify/verify.py) and return its report.

    Verification itself never crashes the run: import or runtime failures
    degrade to a warning plus a minimal report. The report's `gate` field
    decides whether the hard gate triggers one repair round (see
    _repair_against_gate).
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from verify.verify import verify_application  # type: ignore[import-not-found]

        report = verify_application(requirements_dir, output_dir)
        print(
            f"[codex] verification report: {json.dumps(report, ensure_ascii=False)}",
            flush=True,
        )
        return report
    except Exception as exc:  # noqa: BLE001 - verification must never break the run
        print(
            f"[codex] WARNING: verification failed to run: {exc}",
            flush=True,
        )
        return {"error": str(exc)}


def _repair_against_gate(
    requirements_dir: Path,
    output_dir: Path,
    skills_dir: Path,
    report: dict[str, Any],
    include_frontend_spec: bool = True,
    include_telemetry: bool = True,
) -> bool:
    """Run exactly ONE repair round against a failing gate report.

    The gate's blocking defects (plus a few advisory hints) are fed back to a
    fresh Codex thread as the sole task; no retry is attempted, so the repair
    round costs at most one agent turn regardless of outcome.
    """
    gate = (report or {}).get("gate") or {}
    blocking = gate.get("blocking") or []
    advisory = gate.get("advisory") or []
    if not blocking:
        return False
    model = os.environ.get("MODEL", "").strip() or None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    bullets_b = "\n".join(f"- {line}" for line in blocking)
    bullets_a = "\n".join(f"- {line}" for line in advisory[:10]) if advisory else "(none)"
    prompt = textwrap.dedent(
        f"""
        The automated gate check on the generated application found the defects
        below. Fix ONLY these defects, in ONE pass, in the current project.
        Do not restructure the app, add unrelated features, or change behavior
        beyond what the defects require. For each defect make the minimal change,
        then report "defect -> file -> change".

        If a defect says an own test suite exited non-zero, the implementation is
        what must change: NEVER delete, skip, comment out, or weaken a test (or
        its assertions) to make the suite green, and never rewrite a test to
        assert something easier. If a test itself contradicts the requirement
        text, fix the implementation to satisfy the requirement and say so.

        BLOCKING DEFECTS:
        {bullets_b}

        ADVISORY (fix only if trivial):
        {bullets_a}

        Read arcbench-frontend-spec/SKILL.md before touching frontend
        interaction code. Do not start a long-running server. Finish with a
        short summary of the changes you made.
        """
    ).strip()
    print(
        f"[codex][gate] launching one repair round for {len(blocking)} blocking defect(s)",
        flush=True,
    )
    try:
        with Codex(config=_codex_config(CodexConfig)) as codex:
            if api_key:
                codex.login_api_key(api_key)
            thread = codex.thread_start(
                cwd=str(output_dir),
                sandbox=Sandbox.full_access,
                approval_mode=ApprovalMode.deny_all,
                model=model,
                developer_instructions=_developer_instructions(
                    skills_dir, include_frontend_spec, include_telemetry
                ),
            )
            result = _run_turn(
                thread,
                prompt,
                output_dir=output_dir,
                phase="repair",
                module_id="gate-repair",
                module_index=0,
                attempt=1,
                model=model,
            )
            if getattr(result, "error", None) is not None:
                print(f"[codex][gate] repair round errored: {result.error}", flush=True)
                return True
            print("[codex][gate] repair round finished", flush=True)
            print(
                "[codex][usage] "
                + token_usage.format_row(
                    "repair round",
                    token_usage.scope(output_dir, phase="repair", module_id="gate-repair"),
                ),
                flush=True,
            )
            return True
    except Exception as exc:  # noqa: BLE001 - repair must never break the run
        print(f"[codex][gate] repair round failed to run: {exc}", flush=True)
        return True


def main() -> int:
    try:
        return _main()
    except Exception:
        print("[codex] ERROR: fatal error", flush=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
