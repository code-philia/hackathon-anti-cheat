#!/usr/bin/env python3
"""Read-only mechanical lead collection for the competition anti-cheat skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 50_000_000
MAX_MATCHES_PER_RULE = 100
SKIP_PARTS = {".git", ".hg", ".svn", "__pycache__"}
ZIP_SUFFIXES = {".zip", ".jar", ".whl", ".apk"}
ARCHIVE_SUFFIXES = {".7z", ".rar", ".tar", ".tgz", ".gz", ".bz2", ".xz"}

PATTERNS = {
    "AC-INTERFERENCE": re.compile(
        r"(?i)(ignore\s+(all\s+)?(previous|prior)\s+instructions|bypass|disable|evade|"
        r"neutralize|绕过|规避|禁用|无效化|忽略).{0,100}"
        r"(anti[-_ ]?cheat|checker|scanner|review|verdict|反作弊|审查|检测|判决)|"
        r"(anti[-_ ]?cheat|反作弊).{0,100}(bypass|disable|evade|绕过|规避|禁用|无效化)"
    ),
    "EXPLANATORY-CLAIM": re.compile(
        r"(?i)(unused|not\s+used|never\s+executed|not\s+executed|documentation\s+only|"
        r"example\s+only|fallback\s+only|generic|safe|no\s+(external\s+)?network|"
        r"does\s+not\s+(access|read|execute|contact|download)|"
        r"仅用于?(文档|说明|示例|备用)|未使用|不会执行|不访问|不读取|不联网|"
        r"无外部网络|通用(框架|模板|契约)|安全无害)"
    ),
    "MODEL-EXTERNAL": re.compile(
        r"(?i)(?<![a-z0-9])(?:[a-z0-9]+[_-])*(base[_-]?url|api[_-]?base|api[_-]?key)\b"
    ),
    "HARDCODED-API-KEY": re.compile(
        r"(?i)(\b(sk|key|token)-[a-z0-9_-]{16,}\b|"
        r"\b(api[_-]?key|access[_-]?token)\b\s*[:=]\s*['\"][^'\"$%{][^'\"]{7,}['\"]|"
        r"os\.environ(?:\[[^\]]*(key|token)[^\]]*\]|\.setdefault\([^,]*(key|token)[^,]*,)\s*=?.{0,10}['\"][^'\"]{8,}['\"])"
    ),
    "MODEL-METER-TAMPER": re.compile(
        r"(?i)(((token\s+usage|usage|billing|cost|meter|quota|调用记录|计量|计费).{0,60}"
        r"(tamper|hide|conceal|suppress|forge|inject|patch|override|rewrite|reset|delete|"
        r"隐藏|隐瞒|抑制|伪造|注入|篡改|清零|覆盖|删除))|"
        r"((tamper|hide|conceal|suppress|forge|inject|patch|override|rewrite|reset|delete|"
        r"隐藏|隐瞒|抑制|伪造|注入|篡改|清零|覆盖|删除).{0,60}"
        r"(token\s+usage|usage|billing|cost|meter|quota|调用记录|计量|计费|开销)))"
    ),
    "NET-EXTERNAL": re.compile(
        r"(?i)(https?://(?!localhost\b|127\.0\.0\.1\b|api\.arc-bench\.com/v1(?:[/\s'\"`]|$))|"
        r"\b(requests|httpx|aiohttp)\.(get|post|request)\s*\(|"
        r"\b(fetch|curl|wget)\s*\(|\bInvoke-WebRequest\b|"
        r"\b(git\s+clone|npm\s+view|pip\s+install)\b|"
        r"\b(ARC_TESTS_DIR|ARCBENCH_TESTS_DIR)\b|"
        r"/(workspace/tests|staging/tests-context)\b|"
        r"\b(find_tests_dir|_find_tests_dir|test_flow_clauses|official_query_shapes)\s*\(|"
        r"\btest_flow_source\b|"
        r"\b(open|read_text|read_bytes|readFile|readFileSync|glob)\s*\([^)]{0,120}"
        r"(\.spec\.ts|helpers\.ts|support/e2e\.ts))"
    ),
    "ENCODING-OR-EXEC": re.compile(
        r"(?i)(base64\.(b64decode|decodebytes)|atob\s*\(|fromCharCode\s*\(|"
        r"\beval\s*\(|\bexec\s*\(|child_process|subprocess\.(run|Popen|call)|"
        r"os\.system\s*\(|Invoke-Expression)"
    ),
}


@dataclass(frozen=True)
class TextLine:
    location: str
    number: int
    text: str


def decode(data: bytes) -> str | None:
    if b"\x00" in data[:4096]:
        return None
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return None


def scan_zip(path: Path, relative: str, budget: int) -> tuple[list[TextLine], list[dict], int]:
    lines: list[TextLine] = []
    gaps: list[dict] = []
    consumed = 0
    try:
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                location = f"{relative}!/{member.filename}"
                if member.is_dir():
                    continue
                if member.flag_bits & 0x1:
                    gaps.append({"location": location, "reason": "encrypted archive member"})
                    continue
                if member.file_size > MAX_FILE_BYTES or consumed + member.file_size > budget:
                    gaps.append({"location": location, "reason": "archive member exceeds scan limit"})
                    continue
                data = archive.read(member)
                text = decode(data)
                consumed += len(data)
                if text is not None:
                    lines.extend(TextLine(location, number, value) for number, value in enumerate(text.splitlines(), 1))
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        gaps.append({"location": relative, "reason": f"unreadable zip-compatible archive: {exc}"})
    return lines, gaps, consumed


def scan_tree(root: Path) -> dict:
    inventory: list[dict] = []
    lines: list[TextLine] = []
    gaps: list[dict] = []
    total = 0
    for path in sorted(root.rglob("*")):
        relative_path = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative_path.parts):
            continue
        relative = relative_path.as_posix()
        if path.is_symlink():
            inventory.append({"path": relative, "bytes": None, "sha256": None, "type": "symlink"})
            gaps.append({"location": relative, "reason": "symbolic link was not followed; inspect its repository-local purpose"})
            continue
        if not path.is_file():
            continue
        size = path.stat().st_size
        inventory.append({"path": relative, "bytes": size, "sha256": None})
        if size > MAX_FILE_BYTES:
            gaps.append({"location": relative, "reason": f"file exceeds {MAX_FILE_BYTES} byte scan limit"})
            continue
        if total + size > MAX_TOTAL_BYTES:
            gaps.append({"location": relative, "reason": f"repository exceeds {MAX_TOTAL_BYTES} byte text scan limit"})
            continue
        suffix = path.suffix.lower()
        if suffix in ZIP_SUFFIXES:
            archive_lines, archive_gaps, consumed = scan_zip(path, relative, MAX_TOTAL_BYTES - total)
            lines.extend(archive_lines)
            gaps.extend(archive_gaps)
            total += consumed
            continue
        if suffix in ARCHIVE_SUFFIXES:
            gaps.append({"location": relative, "reason": "unsupported archive format; inspect manually"})
        data = path.read_bytes()
        inventory[-1]["sha256"] = hashlib.sha256(data).hexdigest()
        text = decode(data)
        total += len(data)
        if text is not None:
            lines.extend(TextLine(relative, number, value) for number, value in enumerate(text.splitlines(), 1))
    return {"inventory": inventory, "lines": lines, "inspection_gaps": gaps}


def discover_example_tasks(root: Path) -> list[Path]:
    """Resolve one task root or every requirements.yaml-marked task in a collection."""
    root = root.resolve()
    if (root / "requirements.yaml").is_file():
        return [root]
    tasks = sorted({marker.parent.resolve() for marker in root.rglob("requirements.yaml")})
    return tasks or [root]


def collect_matches(lines: list[TextLine]) -> dict[str, list[dict]]:
    matches: dict[str, list[dict]] = {rule: [] for rule in PATTERNS}
    for line in lines:
        for rule, pattern in PATTERNS.items():
            if len(matches[rule]) < MAX_MATCHES_PER_RULE and pattern.search(line.text):
                matches[rule].append({"location": f"{line.location}:{line.number}", "text": line.text.strip()[:500]})
    return {rule: evidence for rule, evidence in matches.items() if evidence}


def normalized_long_lines(lines: list[TextLine]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for line in lines:
        value = re.sub(r"\s+", " ", line.text.strip())
        if len(value) < 100 or value.startswith(("#", "//", "*", "<!--")):
            continue
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        index.setdefault(digest, []).append(f"{line.location}:{line.number}")
    return index


def overlap_leads(example_lines: list[TextLine], submission_lines: list[TextLine]) -> list[dict]:
    example_index = normalized_long_lines(example_lines)
    submission_index = normalized_long_lines(submission_lines)
    return [
        {"example": example_index[digest][:3], "submission": submission_index[digest][:3]}
        for digest in sorted(set(example_index) & set(submission_index))[:100]
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect mechanical anti-cheat leads without executing submission code")
    parser.add_argument("--example", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for label, path in (("example", args.example), ("submission", args.submission)):
        if not path.is_dir():
            print(f"{label} path is not a directory: {path}", file=sys.stderr)
            return 2
    example_tasks = discover_example_tasks(args.example)
    examples = [(task, scan_tree(task)) for task in example_tasks]
    submission = scan_tree(args.submission.resolve())
    overlaps = []
    for task, example in examples:
        for lead in overlap_leads(example["lines"], submission["lines"]):
            overlaps.append({"example_task": str(task), **lead})
    report = {
        "example_root": str(args.example.resolve()),
        "example_tasks": [str(task) for task in example_tasks],
        "submission_root": str(args.submission.resolve()),
        "submission_inventory": submission["inventory"],
        "mechanical_leads": collect_matches(submission["lines"]),
        "long_line_overlaps": overlaps[:100],
        "inspection_gaps": submission["inspection_gaps"],
        "limits": {"max_file_bytes": MAX_FILE_BYTES, "max_total_bytes": MAX_TOTAL_BYTES},
        "notice": "Leads are not verdicts. Inspect original context before adjudicating.",
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
