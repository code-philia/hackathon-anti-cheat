#!/usr/bin/env python3
"""Validate the structural invariants of a core-strategy log."""

from __future__ import annotations

import re
import sys
from pathlib import Path

COVERAGE_LINE = "分析覆盖：RAG/RETRIEVAL=已检查；PREPARED-KNOWLEDGE=已检查；CODE-REUSE=已检查；PROMPT-ORCHESTRATION=已检查；MODEL-ROUTING=已检查；TOOLS/EXECUTION=已检查；ITERATION/EVALUATION=已检查；STATE/PERSISTENCE=已检查"
HEADING = re.compile(r"^STRATEGY-(\d{3}) \[([^\]]+)\] .+")
VALID_CATEGORIES = {"RAG/RETRIEVAL", "PREPARED-KNOWLEDGE", "CODE-REUSE", "PROMPT-ORCHESTRATION", "MODEL-ROUTING", "TOOLS/EXECUTION", "ITERATION/EVALUATION", "STATE/PERSISTENCE"}
REQUIRED_DIMENSIONS = ("状态", "作用", "输入/知识源", "选择/检索", "生成/使用", "输出")
REQUIRED_PARTS = ("具体说明", "代码/文档定位", "详细解释")
GENERIC_SUMMARIES = {"生成页面", "组件库", "关键词选择", "模型生成", "输出代码", "生成代码", "无", "未知"}


def part_value(section: list[str], part: str) -> str | None:
    prefix = f"    {REQUIRED_PARTS.index(part) + 1}. {part}："
    return next((line.removeprefix(prefix).strip() for line in section if line.startswith(prefix)), None)


def dimension_section(block: list[str], dimension: str) -> list[str] | None:
    marker = f"  - {dimension}："
    try:
        start = block.index(marker)
    except ValueError:
        return None
    end = len(block)
    for index in range(start + 1, len(block)):
        if any(block[index] == f"  - {candidate}：" for candidate in REQUIRED_DIMENSIONS):
            end = index
            break
    return block[start + 1:end]


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"report does not exist: {path}"]
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        return [f"report is not valid UTF-8: byte {error.start}: {error.reason}"]
    errors = []
    if "\ufffd" in text:
        errors.append("report contains Unicode replacement characters")
    if any("\ue000" <= character <= "\uf8ff" for character in text):
        errors.append("report contains private-use characters")
    if re.search(r"\?{3,}", text):
        errors.append("report contains three or more consecutive question marks")
    lines = text.splitlines()
    for required in ("[核心结论]", "[策略清单]", "[未发现或未解决]", COVERAGE_LINE):
        if required not in lines:
            errors.append(f"missing required line: {required}")
    if not lines or lines[-1] != "分析完成":
        errors.append("last non-empty line must be 分析完成")
    headings = [(index, match) for index, line in enumerate(lines) if (match := HEADING.match(line))]
    numbers = [int(match.group(1)) for _, match in headings]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append("strategy numbering must be consecutive from 001")
    for position, (start, match) in enumerate(headings):
        if match.group(2) not in VALID_CATEGORIES:
            errors.append(f"STRATEGY-{match.group(1)} has unknown category: {match.group(2)}")
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        block = lines[start + 1:end]
        for dimension in REQUIRED_DIMENSIONS:
            section = dimension_section(block, dimension)
            if section is None:
                errors.append(f"STRATEGY-{match.group(1)} missing dimension: {dimension}")
                continue
            values = {}
            for part in REQUIRED_PARTS:
                value = part_value(section, part)
                values[part] = value
                if not value:
                    errors.append(f"STRATEGY-{match.group(1)} {dimension} missing part: {part}")
            summary = values.get("具体说明")
            if summary:
                if summary in GENERIC_SUMMARIES or len(summary) < 10:
                    errors.append(f"STRATEGY-{match.group(1)} {dimension} 具体说明 is too terse or generic")
                if dimension == "状态" and not re.match(r"^(confirmed|inferred|unresolved)\b", summary):
                    errors.append(f"STRATEGY-{match.group(1)} 状态 must begin with confirmed, inferred, or unresolved")
            location = values.get("代码/文档定位")
            if location and not re.search(r"[^；;，,\s]+:\d+", location):
                errors.append(f"STRATEGY-{match.group(1)} {dimension} location must contain path:line")
            explanation = values.get("详细解释")
            if explanation and len(explanation) < 30:
                errors.append(f"STRATEGY-{match.group(1)} {dimension} 详细解释 is too short")
    if "RAG" not in text or "代码复用" not in text:
        errors.append("report must explicitly state RAG and code-reuse conclusions")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_report.py <result.log>", file=sys.stderr)
        return 2
    errors = validate(Path(sys.argv[1]))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("report structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
