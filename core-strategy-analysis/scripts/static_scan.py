#!/usr/bin/env python3
"""Collect read-only mechanical leads for core generation strategy analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 50_000_000
MAX_MATCHES_PER_CATEGORY = 100
SKIP_PARTS = {".git", ".hg", ".svn", "__pycache__"}

PATTERNS = {
    "RAG/RETRIEVAL": re.compile(r"(?i)(rag|retriev|embedding|vector(?:store|db)?|faiss|chroma|milvus|similarity|semantic.search|bm25|knowledge.base|corpus|index.query)"),
    "PREPARED-KNOWLEDGE": re.compile(r"(?i)(template|boilerplate|example|few.shot|skill|playbook|checklist|knowledge|prompt.library|reference)"),
    "CODE-REUSE": re.compile(r"(?i)(copytree|copyfile|shutil\.copy|unpack_archive|apply_patch|git\s+apply|reuse|component.library|starter|scaffold)"),
    "PROMPT-ORCHESTRATION": re.compile(r"(?i)(system_prompt|user_prompt|prompt_template|messages\s*=|planner|critic|reviewer|agent|delegate|subtask|context.compress|summari[sz])"),
    "MODEL-ROUTING": re.compile(r"(?i)(base_url|api_key|model\s*=|fallback.model|secondary.model|route.model|chat\.completions|responses\.create|litellm|openai|anthropic)"),
    "TOOLS/EXECUTION": re.compile(r"(?i)(subprocess\.(run|Popen)|os\.system|child_process|shell=True|tool_call|function_call|browser|playwright|selenium|read_text|write_text)"),
    "ITERATION/EVALUATION": re.compile(r"(?i)(retry|iteration|feedback|self.crit|evaluate|validator|pytest|test\s|build\s|lint|score|refine|repair|fix.loop)"),
    "STATE/PERSISTENCE": re.compile(r"(?i)(checkpoint|cache|memory|session|history|state|persist|sqlite|jsonl|artifact|resume)"),
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


def scan_tree(root: Path) -> dict:
    inventory, lines, gaps = [], [], []
    total = 0
    for path in sorted(root.rglob("*")):
        relative_path = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative_path.parts):
            continue
        relative = relative_path.as_posix()
        if path.is_symlink():
            inventory.append({"path": relative, "bytes": None, "sha256": None, "type": "symlink"})
            gaps.append({"location": relative, "reason": "symbolic link was not followed"})
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
        data = path.read_bytes()
        inventory[-1]["sha256"] = hashlib.sha256(data).hexdigest()
        text = decode(data)
        total += len(data)
        if text is not None:
            lines.extend(TextLine(relative, number, value) for number, value in enumerate(text.splitlines(), 1))
    return {"inventory": inventory, "lines": lines, "inspection_gaps": gaps}


def discover_example_tasks(root: Path) -> list[Path]:
    root = root.resolve()
    if (root / "requirements.yaml").is_file():
        return [root]
    return sorted({marker.parent.resolve() for marker in root.rglob("requirements.yaml")}) or [root]


def collect_matches(lines: list[TextLine]) -> dict[str, list[dict]]:
    matches = {category: [] for category in PATTERNS}
    for line in lines:
        for category, pattern in PATTERNS.items():
            if len(matches[category]) < MAX_MATCHES_PER_CATEGORY and pattern.search(line.text):
                matches[category].append({"location": f"{line.location}:{line.number}", "text": line.text.strip()[:500]})
    return {category: evidence for category, evidence in matches.items() if evidence}


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
    return [{"example": example_index[digest][:3], "submission": submission_index[digest][:3]} for digest in sorted(set(example_index) & set(submission_index))[:100]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect mechanical strategy leads without executing submission code")
    parser.add_argument("--example", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    for label, path in (("example", args.example), ("submission", args.submission)):
        if not path.is_dir():
            print(f"{label} path is not a directory: {path}", file=sys.stderr)
            return 2
    tasks = discover_example_tasks(args.example)
    examples = [(task, scan_tree(task)) for task in tasks]
    submission = scan_tree(args.submission.resolve())
    overlaps = []
    for task, example in examples:
        overlaps.extend({"example_task": str(task), **lead} for lead in overlap_leads(example["lines"], submission["lines"]))
    report = {
        "example_root": str(args.example.resolve()),
        "example_tasks": [str(task) for task in tasks],
        "submission_root": str(args.submission.resolve()),
        "submission_inventory": submission["inventory"],
        "strategy_leads": collect_matches(submission["lines"]),
        "long_line_overlaps": overlaps[:100],
        "inspection_gaps": submission["inspection_gaps"],
        "limits": {"max_file_bytes": MAX_FILE_BYTES, "max_total_bytes": MAX_TOTAL_BYTES},
        "notice": "Leads are not conclusions. Inspect original code and data flow.",
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
