#!/usr/bin/env python3
"""Extract ZIP archives recursively for workspace entries 021 through 030."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


FIRST_ENTRY = 21
LAST_ENTRY = 30
ENTRY_PATTERN = re.compile(r"^(\d{3})-")


def filesystem_path(path: Path) -> Path:
    """Use the Windows long-path form for filesystem I/O when available."""
    resolved = str(path.resolve())
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return Path("\\\\?\\" + resolved)
    return Path(resolved)


def selected_entries(workspace: Path) -> list[Path]:
    entries = []
    for path in workspace.iterdir():
        match = ENTRY_PATTERN.match(path.name)
        if path.is_dir() and match and FIRST_ENTRY <= int(match.group(1)) <= LAST_ENTRY:
            entries.append(path)
    return sorted(entries, key=lambda path: path.name)


def safe_members(archive: zipfile.ZipFile, target: Path) -> list[zipfile.ZipInfo]:
    target = target.resolve()
    members = []
    for member in archive.infolist():
        member_path = PurePosixPath(member.filename.replace("\\", "/"))
        if member_path.is_absolute() or ".." in member_path.parts:
            raise ValueError(f"unsafe archive path: {member.filename}")
        destination = target.joinpath(*member_path.parts).resolve()
        if not destination.is_relative_to(target):
            raise ValueError(f"archive path escapes target: {member.filename}")
        unix_mode = member.external_attr >> 16
        if stat.S_ISLNK(unix_mode):
            raise ValueError(f"symbolic link is not allowed: {member.filename}")
        if member.flag_bits & 0x1:
            raise ValueError(f"encrypted archive member is not supported: {member.filename}")
        members.append(member)
    return members


def extract_archive(archive_path: Path, target: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        members = safe_members(archive, target)
        for member in members:
            destination = filesystem_path(target.joinpath(*PurePosixPath(member.filename.replace("\\", "/")).parts))
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)


def process_entry(entry: Path, dry_run: bool) -> tuple[int, int]:
    extracted = 0
    skipped = 0
    handled: set[Path] = set()

    while True:
        archives = sorted(
            (path for path in entry.rglob("*") if path.is_file() and path.suffix.lower() == ".zip"),
            key=lambda path: str(path).lower(),
        )
        pending = [path for path in archives if path.resolve() not in handled]
        if not pending:
            break

        for archive_path in pending:
            handled.add(archive_path.resolve())
            target = archive_path.with_suffix("")
            relative_archive = archive_path.relative_to(entry)
            relative_target = target.relative_to(entry)
            if target.exists():
                print(f"SKIP    {entry.name}/{relative_archive} -> {relative_target} (target exists)")
                skipped += 1
                continue
            if dry_run:
                with zipfile.ZipFile(archive_path) as archive:
                    safe_members(archive, target)
                print(f"EXTRACT {entry.name}/{relative_archive} -> {relative_target}")
                extracted += 1
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
            try:
                extract_archive(archive_path, temporary)
                temporary.replace(target)
            except Exception:
                shutil.rmtree(temporary, ignore_errors=True)
                raise
            print(f"EXTRACT {entry.name}/{relative_archive} -> {relative_target}")
            extracted += 1

    return extracted, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recursively extract ZIP files only for workspace entries 021 through 030."
    )
    parser.add_argument("workspace", nargs="?", type=Path, default=Path("workspace"))
    parser.add_argument("--dry-run", action="store_true", help="validate and list top-level work without writing")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        parser.error(f"workspace directory does not exist: {workspace}")

    entries = selected_entries(workspace)
    if not entries:
        print("No workspace entries numbered 021 through 030 were found.", file=sys.stderr)
        return 1

    total_extracted = 0
    total_skipped = 0
    for entry in entries:
        extracted, skipped = process_entry(entry, args.dry_run)
        total_extracted += extracted
        total_skipped += skipped

    mode = "Dry run" if args.dry_run else "Done"
    print(f"{mode}: {len(entries)} entries, {total_extracted} archive(s) extracted, {total_skipped} skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
