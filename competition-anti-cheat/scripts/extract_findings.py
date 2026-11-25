#!/usr/bin/env python3
"""Extract findings only from an audit log into a sibling JSON file."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(ERROR|WARNING)-\d{3}\s+\[([^\]]+)\]\s+(.*)$")
LOCATION = re.compile(r"^(.+?):(\d+)(?:`)?\s*[:：]\s*(.*)$")
FIELDS = {"知识类型", "检索方案", "生成方案", "泛用估计", "综合判断"}


def extract(text: str) -> list[dict]:
    findings = []
    current = None
    section = None
    for line in text.splitlines():
        if line in ("[ERROR]", "[WARNING]") or line.startswith("判决："):
            current = None
            section = line if line.startswith("[") else None
            continue
        match = HEADING.match(line)
        if match and section in ("[ERROR]", "[WARNING]"):
            severity = line.split("-", 1)[0].lower()
            current = {"id": line.split()[0], "severity": severity,
                       "rule_id": match[2], "description": match[3], "evidence": []}
            findings.append(current)
        elif current is not None and line.strip() and line.strip() != "无":
            if line.startswith("  - "):
                content = line[4:]
                field, separator, value = content.partition("：")
                if separator and field in FIELDS:
                    current.setdefault("classification", {})[field] = value
                    continue
                location = LOCATION.match(content)
                if location:
                    path = location[1].strip("`")
                    current["evidence"].append({"path": path, "line": int(location[2]),
                                               "explanation": location[3]})
                else:
                    current["evidence"].append({"text": content})
            else:
                current.setdefault("details", []).append(line.strip())
    return findings


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: extract_findings.py <audit.log> [audit.json]", file=sys.stderr)
        return 2
    source = Path(sys.argv[1])
    target = Path(sys.argv[2]) if len(sys.argv) == 3 else source.with_suffix(".json")
    if source.resolve() == target.resolve():
        print("ERROR: JSON output must differ from input log", file=sys.stderr)
        return 1
    result = extract(source.read_text(encoding="utf-8-sig"))
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(result)} findings to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
