#!/usr/bin/env python3
"""Validate structural invariants of a generated anti-cheat log."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FINDING_HEADING = re.compile(r"^(ERROR|WARNING)-\d{3}\s+\[([^\]]+)\]\s")
TEMPLATE_RULES = {"TEMPLATE-DIRECT", "TEMPLATE-INDIRECT"}
COVERAGE_LINE = (
    "审查覆盖：TEMPLATE-DIRECT/TEMPLATE-INDIRECT=已检查；MODEL-EXTERNAL=已检查；"
    "MODEL-METER-TAMPER=已检查；NET-EXTERNAL=已检查；AC-INTERFERENCE=已检查；"
    "OTHER-SUSPICIOUS/INSPECTION-GAP=已检查"
)
TEMPLATE_FIELDS = {
    "知识类型": re.compile(
        r"^  - 知识类型：(\(1\)完整代码实现|\(2\)代码片段|\(3\)代码实现逻辑/细节/约束|\(4\)更加泛化的设计知识)；"
        r"说明：.+；定位：.+:\d+(?:\b|`)"
    ),
    "检索方案": re.compile(
        r"^  - 检索方案：(\(1\)针对题面硬编码检索|\(2\)针对关键词硬编码检索|\(3\)基于模型宽泛检索|\(4\)无检索机制（全量使用）)；"
        r"说明：.+；定位：.+:\d+(?:\b|`)"
    ),
    "生成方案": re.compile(
        r"^  - 生成方案：(\(1\)无模型参与地使用代码|\(2\)将代码知识置入提示词，由模型复用拼接生成|\(3\)将领域知识置入提示词，由模型参考生成)；"
        r"说明：.+；定位：.+:\d+(?:\b|`)"
    ),
    "泛用估计": re.compile(
        r"^  - 泛用估计：(\(1\)知识仅可用于题面给定的需求|\(2\)知识在与题面功能一致的网页应用上可以兼容泛化|\(3\)知识在一般网页应用上兼容泛化)；说明：.+"
    ),
    "综合判断": re.compile(r"^  - 综合判断：.+"),
}
MOJIBAKE_FRAGMENTS = (
    "鍙嶄綔寮",
    "棰橀潰",
    "浣滅瓟",
    "瀹℃煡",
    "鎽樿",
    "鍒ゅ喅",
    "璇存槑",
    "锛",
    "銆",
    "鈥",
    "閸欏秳",
)


def read_report(path: Path) -> tuple[str | None, list[str]]:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        return None, [f"report is not valid UTF-8: byte {error.start}: {error.reason}"]

    errors = []
    if "\ufffd" in text:
        errors.append("report contains Unicode replacement characters (U+FFFD), indicating lost text")
    private_use_count = sum("\ue000" <= character <= "\uf8ff" for character in text)
    if private_use_count:
        errors.append(f"report contains {private_use_count} private-use character(s), indicating encoding corruption")
    if re.search(r"\?{3,}", text):
        errors.append("report contains a run of three or more question marks, indicating lost text")
    found_fragments = [fragment for fragment in MOJIBAKE_FRAGMENTS if fragment in text]
    if found_fragments:
        errors.append(f"report contains likely Chinese mojibake: {', '.join(found_fragments[:5])}")
    return text, errors


def finding_blocks(lines: list[str]) -> list[tuple[int, int, re.Match[str]]]:
    headings = [(index, match) for index, line in enumerate(lines) if (match := FINDING_HEADING.match(line))]
    blocks = []
    for position, (start, match) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        for marker in ("[ERROR]", "[WARNING]", "判决：通过", "判决：作弊"):
            try:
                marker_index = lines.index(marker, start + 1, end)
            except ValueError:
                continue
            end = min(end, marker_index)
        blocks.append((start, end, match))
    return blocks


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"report does not exist: {path}"]
    text, errors = read_report(path)
    if text is None:
        return errors
    lines = text.splitlines()
    if "[ERROR]" not in lines:
        errors.append("missing [ERROR] section")
    if "[WARNING]" not in lines:
        errors.append("missing [WARNING] section")
    if COVERAGE_LINE not in lines:
        errors.append("missing or malformed full-audit coverage declaration")
    if not lines or lines[-1] not in {"判决：通过", "判决：作弊"}:
        errors.append("last line must be an exact verdict")
    error_headings = [index for index, line in enumerate(lines) if re.match(r"^ERROR-\d{3}\s", line)]
    error_count = len(error_headings)
    warning_section = lines.index("[WARNING]") if "[WARNING]" in lines else len(lines)
    for position, start in enumerate(error_headings):
        end = error_headings[position + 1] if position + 1 < error_count else warning_section
        evidence = lines[start + 1:end]
        if not any(re.match(r"^\s{2}-\s+.+:\d+(?:\b|`)", line) for line in evidence):
            finding = lines[start].split(maxsplit=1)[0]
            errors.append(f"{finding} must cite an original source path:line evidence bullet")
    for start, end, match in finding_blocks(lines):
        finding = lines[start].split(maxsplit=1)[0]
        block = lines[start + 1:end]
        if match.group(1) == "WARNING" and match.group(2) == "AC-INTERFERENCE":
            if not any(re.match(r"^\s{2}-\s+.+:\d+(?:\b|`)", line) for line in block):
                errors.append(f"{finding} must cite the explanatory claim as path:line")
        if match.group(2) not in TEMPLATE_RULES:
            continue
        for field, pattern in TEMPLATE_FIELDS.items():
            if not any(pattern.match(line) for line in block):
                errors.append(f"{finding} has missing or malformed template field: {field}")
    if lines and lines[-1] == "判决：通过" and error_count:
        errors.append("passing verdict conflicts with error findings")
    if lines and lines[-1] == "判决：作弊" and not error_count:
        errors.append("cheating verdict requires at least one error finding")
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
