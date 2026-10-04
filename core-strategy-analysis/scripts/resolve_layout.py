#!/usr/bin/env python3
"""Resolve example/group/submission layout for strategy-analysis batch runs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GROUP_PATTERN = re.compile(r"^(?P<task>.+)-top\d+$", re.IGNORECASE)


def event_roots(example_root: Path) -> list[Path]:
    if any(path.is_file() for path in example_root.glob("*/requirements.yaml")):
        return [example_root.resolve()]
    return sorted(path.resolve() for path in example_root.iterdir() if path.is_dir())


def matching_events(group_task: str, events: list[Path]) -> list[Path]:
    return [event for event in events if group_task == event.name or group_task.startswith(event.name + "-")]


def workspace_groups(workspace_root: Path) -> list[Path]:
    if GROUP_PATTERN.fullmatch(workspace_root.name):
        return [workspace_root]
    return sorted(path for path in workspace_root.iterdir() if path.is_dir())


def resolve(example_root: Path, workspace_root: Path, result_root: Path) -> dict:
    events = event_roots(example_root)
    pairs, issues = [], []
    for group in workspace_groups(workspace_root):
        match = GROUP_PATTERN.fullmatch(group.name)
        if not match:
            issues.append({"severity": "error", "path": str(group.resolve()), "message": "group name does not match <event>-<track>-top<N>"})
            continue
        candidates = matching_events(match.group("task"), events)
        if len(candidates) != 1:
            issues.append({"severity": "error", "path": str(group.resolve()), "message": f"expected exactly one example event for {match.group('task')}, found {len(candidates)}"})
            continue
        submissions = sorted(path for path in group.iterdir() if path.is_dir())
        if not submissions:
            issues.append({"severity": "warning", "path": str(group.resolve()), "message": "submission group is empty"})
        for submission in submissions:
            pairs.append({
                "example": str(candidates[0]),
                "submission": str(submission.resolve()),
                "result": str(result_root.resolve() / group.name / f"{submission.name}.log"),
            })
    return {"pairs": pairs, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve example paths for grouped competition submissions")
    parser.add_argument("--example-root", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    args = parser.parse_args()
    for label, path in (("example root", args.example_root), ("workspace root", args.workspace_root)):
        if not path.is_dir():
            print(f"{label} is not a directory: {path}", file=sys.stderr)
            return 2
    output = resolve(args.example_root, args.workspace_root, args.result_root)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if any(issue["severity"] == "error" for issue in output["issues"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())

