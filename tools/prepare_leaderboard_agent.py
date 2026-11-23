"""Prepare a clean anti-cheat audit input from a leaderboard export ZIP."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


def clean_component(value: object) -> str:
    text = re.sub(r"[^\w.-]+", "_", str(value), flags=re.UNICODE).strip("_")
    return text or "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="leaderboard-export.zip")
    parser.add_argument("--output-root", type=Path, default=Path("input"))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.archive.is_file():
        raise SystemExit(f"archive not found: {args.archive}")
    with zipfile.ZipFile(args.archive) as export:
        manifest = json.loads(export.read("manifest.json"))
        board = manifest["leaderboard"]
        agent_members = [
            item["file"]
            for item in manifest.get("files", [])
            if str(item.get("file", "")).startswith("agents/")
            and str(item.get("file", "")).endswith("/agent.zip")
        ]
        if len(agent_members) != 1:
            raise SystemExit(f"expected exactly one agent.zip, found {len(agent_members)}")
        agent_member = agent_members[0]
        directory_name = (
            f"leaderboard_{clean_component(board['username'])}"
            f"_track-{clean_component(board['track'])}"
            f"_score-{clean_component(board['score'])}"
            f"_pass_rate-{clean_component(board['pass_rate'])}"
        )
        output_dir = args.output_root / directory_name
        if output_dir.exists():
            if not args.overwrite:
                raise SystemExit(f"output exists (use --overwrite): {output_dir}")
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)
        agent_dir = output_dir / "agent"
        agent_dir.mkdir()
        with tempfile.TemporaryDirectory() as temp_dir:
            agent_zip = Path(temp_dir) / "agent.zip"
            agent_zip.write_bytes(export.read(agent_member))
            with zipfile.ZipFile(agent_zip) as agent:
                agent.extractall(agent_dir)
        summary = {
            "username": board["username"],
            "track": board["track"],
            "score": board["score"],
            "pass_rate": board["pass_rate"],
        }
        (output_dir / "leaderboard-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
