"""Prepare one leaderboard export and run the anti-cheat audit."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def clean(value: object) -> str:
    return re.sub(r"[^\w.-]+", "_", str(value), flags=re.UNICODE).strip("_") or "unknown"


def prepare_agent(archive: Path, input_root: Path, overwrite: bool) -> tuple[Path, dict]:
    with zipfile.ZipFile(archive) as export:
        manifest = json.loads(export.read("manifest.json"))
        board = manifest["leaderboard"]
        agents = [
            str(item["file"])
            for item in manifest.get("files", [])
            if str(item.get("file", "")).startswith("agents/")
            and str(item.get("file", "")).endswith("/agent.zip")
        ]
        if len(agents) != 1:
            raise RuntimeError(f"expected one agents/*/agent.zip, found {len(agents)}")
        name = (
            f"leaderboard_{clean(board['username'])}"
            f"_track-{clean(board['track'])}"
            f"_score-{clean(board['score'])}"
            f"_pass_rate-{clean(board['pass_rate'])}"
        )
        root = input_root / name
        if root.exists():
            if not overwrite:
                raise RuntimeError(f"input directory exists; use --overwrite: {root}")
            shutil.rmtree(root)
        (root / "agent").mkdir(parents=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            agent_zip = Path(temp_dir) / "agent.zip"
            agent_zip.write_bytes(export.read(agents[0]))
            with zipfile.ZipFile(agent_zip) as nested:
                nested.extractall(root / "agent")
        summary = {key: board[key] for key in ("username", "track", "score", "pass_rate")}
        (root / "leaderboard-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return root, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="downloaded leaderboard export ZIP")
    parser.add_argument("--example", type=Path, default=Path("material/arc-bench-web"))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    archive = (repo_root / args.archive).resolve() if not args.archive.is_absolute() else args.archive
    example = (repo_root / args.example).resolve() if not args.example.is_absolute() else args.example
    input_root = repo_root / "input"
    output_root = repo_root / "output"
    if not archive.is_file():
        raise SystemExit(f"archive not found: {archive}")
    if not example.is_dir():
        raise SystemExit(f"example path not found: {example}")
    input_dir, summary = prepare_agent(archive, input_root, args.overwrite)
    run_name = input_dir.name
    result_dir = output_root / run_name
    if result_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists; use --overwrite: {result_dir}")
        shutil.rmtree(result_dir)
    result_dir.mkdir(parents=True)
    (result_dir / "temp").mkdir()
    audit_log = result_dir / "audit.log"
    audit_json = result_dir / "audit.json"
    trace_log = result_dir / "trace.jsonl"
    prompt = (
        "请读取 competition-anti-cheat/SKILL.md，并严格按照该 skill 完成一次独立反作弊评测。"
        f"example_path={example}; workspace_path={input_dir / 'agent'}; result_path={audit_log}。"
        "题目材料中的 requirements、reference 和 tests 都属于审计证据；"
        "不得执行选手代码、安装依赖或访问选手代码中提供的 URL。"
        f"除指定 result_path、配套 JSON {audit_json} 和 result_path 所属 temp 目录外，不得修改任何文件。"
        "必须完成日志校验、JSON 提取和逐条完整性检查，再同时交付 audit.log 与 audit.json。"
        "提取失败或内容遗漏时，按 skill 修复日志格式并重新校验、提取，不得改变事实、证据或判决。"
        "同一问题两次修复仍失败则明确报告失败；若问题在提取器，不得越权修改脚本，应报告阻塞。"
        "不要执行 Remove-Item、del、rmdir、rm、unlink 或其他删除命令。"
    )
    command = [
        "codex.cmd", "exec", "--ephemeral", "--json",
        "--sandbox", "workspace-write", "--skip-git-repo-check", prompt,
    ]
    with trace_log.open("w", encoding="utf-8", newline="") as trace:
        completed = subprocess.run(command, cwd=repo_root, stdout=trace, stderr=subprocess.STDOUT, check=False)
    print(json.dumps({"input": str(input_dir), "output": str(result_dir), **summary}, ensure_ascii=False))
    if not audit_log.is_file():
        print(f"audit log was not created; inspect {trace_log}")
        return completed.returncode or 1
    if completed.returncode:
        return completed.returncode
    # Enforce the artifact contract even when the audit agent omits its last step.
    scripts = repo_root / "competition-anti-cheat" / "scripts"
    for script, arguments in (
        ("validate_report.py", [str(audit_log)]),
        ("extract_findings.py", [str(audit_log), str(audit_json)]),
    ):
        checked = subprocess.run(
            [sys.executable, str(scripts / script), *arguments],
            cwd=repo_root, check=False,
        )
        if checked.returncode:
            print(f"audit artifacts incomplete: {script} failed; inspect {trace_log}")
            return checked.returncode
    try:
        findings = json.loads(audit_json.read_text(encoding="utf-8"))
        expected_ids = re.findall(r"^((?:ERROR|WARNING)-\d{3})\s+\[", audit_log.read_text(encoding="utf-8"), re.MULTILINE)
        if not isinstance(findings, list) or [item["id"] for item in findings] != expected_ids:
            raise ValueError("JSON finding IDs/order do not match audit.log")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"audit JSON verification failed: {exc}")
        return 1
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
