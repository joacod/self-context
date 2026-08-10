#!/usr/bin/env python3
"""Create and retain pre-write ZIP backups for a SelfContext vault."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple


BACKUP_DIR_NAME = "backups"
BACKUP_NAME_PATTERN = re.compile(
    r"^vault-(?P<timestamp>\d{8}T\d{6}Z)(?:-(?P<sequence>\d+))?\.zip$"
)
RETENTION_LIMIT = 3


class BackupError(RuntimeError):
    """Raised when a complete backup cannot be created or retained."""


def _timestamp(now: Optional[dt.datetime] = None) -> str:
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.timezone.utc)
    return current.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _managed_backups(backup_dir: Path) -> List[Path]:
    if not backup_dir.is_dir():
        return []

    backups = [
        path
        for path in backup_dir.iterdir()
        if path.is_file()
        and not path.is_symlink()
        and BACKUP_NAME_PATTERN.fullmatch(path.name)
    ]
    return sorted(backups, key=_backup_sort_key)


def _backup_sort_key(path: Path) -> Tuple[str, int, str]:
    match = BACKUP_NAME_PATTERN.fullmatch(path.name)
    if match is None:
        raise ValueError(f"not a managed backup filename: {path.name}")
    sequence = match.group("sequence")
    return (match.group("timestamp"), int(sequence or 0), path.name)


def _next_destination(backup_dir: Path, timestamp: str) -> Path:
    destination = backup_dir / f"vault-{timestamp}.zip"
    if not destination.exists():
        return destination

    sequence = 1
    while True:
        destination = backup_dir / f"vault-{timestamp}-{sequence:02d}.zip"
        if not destination.exists():
            return destination
        sequence += 1


def _archive_entries(vault: Path) -> List[Tuple[Path, str]]:
    entries: List[Tuple[Path, str]] = []
    for path in vault.rglob("*"):
        relative = path.relative_to(vault)
        # Keep stale operational backup state out of new portable snapshots.
        if relative.parts and relative.parts[0] == BACKUP_DIR_NAME:
            continue
        if path.is_dir():
            archive_name = f"{relative.as_posix()}/"
        elif path.is_file():
            archive_name = relative.as_posix()
        else:
            continue
        entries.append((path, archive_name))
    return sorted(entries, key=lambda entry: entry[1])


def create_backup(
    vault: Path, now: Optional[dt.datetime] = None
) -> Tuple[Path, List[Path]]:
    """Create one backup and delete managed archives older than the newest three."""

    vault = vault.expanduser().resolve()
    if not vault.exists():
        raise BackupError(f"vault does not exist: {vault}")
    if not vault.is_dir():
        raise BackupError(f"vault path is not a directory: {vault}")

    # The vault is expected at <repository-root>/vault, so keep operational
    # backups beside it rather than making them part of the portable vault.
    backup_dir = vault.parent / BACKUP_DIR_NAME
    if backup_dir.is_symlink():
        raise BackupError(f"backup directory is a symlink: {backup_dir}")
    try:
        backup_dir.mkdir(exist_ok=True)
    except OSError as error:
        raise BackupError(f"could not create backup directory: {backup_dir}") from error

    destination = _next_destination(backup_dir, _timestamp(now))
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=backup_dir,
            prefix=".vault-backup-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)

        with zipfile.ZipFile(
            temporary_path, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path, archive_name in _archive_entries(vault):
                archive.write(path, archive_name)

        os.replace(temporary_path, destination)
        temporary_path = None
    except Exception as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise BackupError(f"could not create vault backup: {destination}") from error

    try:
        backups = _managed_backups(backup_dir)
        removed = backups[:-RETENTION_LIMIT]
        for old_backup in removed:
            old_backup.unlink()
    except OSError as error:
        raise BackupError(
            f"created {destination}, but could not enforce {RETENTION_LIMIT}-backup retention"
        ) from error

    return destination, removed


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a timestamped pre-write backup of a SelfContext vault"
    )
    parser.add_argument(
        "vault", nargs="?", default="vault", help="Path to the vault (default: ./vault)"
    )
    args = parser.parse_args(argv)

    try:
        destination, removed = create_backup(Path(args.vault))
    except BackupError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Created vault backup: {destination}")
    for old_backup in removed:
        print(f"Removed older vault backup: {old_backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
