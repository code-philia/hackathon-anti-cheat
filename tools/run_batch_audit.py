"""Run the single-audit pipeline serially for a fixed ZIP list."""

from __future__ import annotations

import subprocess
import sys
import argparse
from pathlib import Path


# Keep this list explicit for reproducible batch governance. Edit this list;
# the script intentionally does not expand a wildcard at runtime.
ARCHIVES = [
    Path("download/leaderboard-export (30).zip")
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print the fixed ZIP list without running audits")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    runner = repo_root / "tools" / "run_single_audit.py"
    results: list[tuple[Path, int]] = []
    for archive in ARCHIVES:
        archive_path = archive if archive.is_absolute() else repo_root / archive
        if args.dry_run:
            print(f"[batch] would run {archive_path}", flush=True)
            continue
        print(f"[batch] starting {archive_path}", flush=True)
        completed = subprocess.run(
            [sys.executable, str(runner), str(archive_path), "--overwrite"],
            cwd=repo_root,
            check=False,
        )
        results.append((archive, completed.returncode))
        status = "ok" if completed.returncode == 0 else f"failed ({completed.returncode})"
        print(f"[batch] {archive}: {status}", flush=True)
    print("[batch] summary", flush=True)
    for archive, code in results:
        print(f"  - {archive}: {'ok' if code == 0 else f'failed ({code})'}", flush=True)
    return 0 if all(code == 0 for _, code in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
