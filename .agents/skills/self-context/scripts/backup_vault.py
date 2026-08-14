#!/usr/bin/env python3
"""Create and retain post-write ZIP snapshots for a SelfContext vault.

Callers should invoke this helper after a mutation and its relevant validation
so the archive represents the resulting vault state. Archives contain private
vault content and are not encrypted.  No encryption
dependency is used; users who need encryption should protect or copy the ZIPs
with a separate user-controlled tool.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


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


def _restrictive_permissions(path: Path, mode: int) -> None:
    try:
        os.chmod(path, mode)
    except (OSError, NotImplementedError):
        # Windows and some portable filesystems do not expose POSIX modes.
        pass


def _managed_backups(backup_dir: Path) -> List[Path]:
    if not backup_dir.is_dir() or backup_dir.is_symlink():
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
    if not destination.exists() and not destination.is_symlink():
        return destination

    sequence = 1
    while True:
        destination = backup_dir / f"vault-{timestamp}-{sequence:02d}.zip"
        if not destination.exists() and not destination.is_symlink():
            return destination
        sequence += 1


def _walk_entries(vault: Path) -> Iterable[Path]:
    """Yield all entries without following links, including special files."""

    for current, directories, files in os.walk(vault, followlinks=False):
        current_path = Path(current)
        directories.sort()
        files.sort()
        for name in directories:
            yield current_path / name
        for name in files:
            yield current_path / name
        directories[:] = [
            name for name in directories if not (current_path / name).is_symlink()
        ]


def _ensure_below(path: Path, root: Path) -> None:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except ValueError as error:
        raise BackupError(f"archive path escapes vault root: {path}") from error
    except OSError as error:
        raise BackupError(f"could not resolve archive path: {path}") from error


def _archive_entries(vault: Path) -> List[Tuple[Path, str]]:
    root = vault.resolve(strict=True)
    entries: List[Tuple[Path, str]] = []
    for path in _walk_entries(vault):
        relative = path.relative_to(vault)
        # Viewer state and copied legacy backup state are noncanonical.  Skip
        # them, but never skip a linked entry in canonical content.
        if relative.parts and relative.parts[0] in {BACKUP_DIR_NAME, ".obsidian", ".DS_Store"}:
            continue
        if path.is_symlink():
            raise BackupError(f"symlink is not allowed inside vault: {path}")
        _ensure_below(path, root)
        if path.is_dir():
            archive_name = f"{relative.as_posix()}/"
        elif path.is_file():
            archive_name = relative.as_posix()
        else:
            raise BackupError(f"unsupported vault entry would be omitted: {path}")
        entries.append((path, archive_name))
    return sorted(entries, key=lambda entry: entry[1])


def _validate_temporary_zip(path: Path, vault: Path) -> None:
    try:
        with zipfile.ZipFile(path, mode="r") as archive:
            bad = archive.testzip()
            if bad is not None:
                raise BackupError(f"temporary ZIP failed validation at {bad}")
            for info in archive.infolist():
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or any(part == ".." for part in name.split("/")):
                    raise BackupError(f"temporary ZIP contains unsafe path: {info.filename}")
                # Reading every member verifies the archive before replacement.
                if not name.endswith("/"):
                    archive.read(info)
    except BackupError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise BackupError(f"temporary ZIP failed validation: {error}") from error


def create_backup(
    vault: Path, now: Optional[dt.datetime] = None
) -> Tuple[Path, List[Path]]:
    """Create one backup and delete managed archives older than the newest three."""

    supplied = vault.expanduser()
    if supplied.is_symlink():
        raise BackupError(f"vault path is a symlink: {supplied}")
    if not supplied.exists():
        raise BackupError(f"vault does not exist: {supplied}")
    if not supplied.is_dir():
        raise BackupError(f"vault path is not a directory: {supplied}")
    vault = supplied.resolve(strict=True)

    backup_dir = vault.parent / BACKUP_DIR_NAME
    if backup_dir.is_symlink():
        raise BackupError(f"backup directory is a symlink: {backup_dir}")
    try:
        backup_dir.mkdir(exist_ok=True, mode=0o700)
        _restrictive_permissions(backup_dir, stat.S_IRWXU)
    except OSError as error:
        raise BackupError(f"could not create backup directory: {backup_dir}") from error

    entries = _archive_entries(vault)
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
        _restrictive_permissions(temporary_path, stat.S_IRUSR | stat.S_IWUSR)

        with zipfile.ZipFile(
            temporary_path, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for path, archive_name in entries:
                _ensure_below(path, vault)
                archive.write(path, archive_name)
        _validate_temporary_zip(temporary_path, vault)
        os.replace(temporary_path, destination)
        temporary_path = None
        _restrictive_permissions(destination, stat.S_IRUSR | stat.S_IWUSR)
    except Exception as error:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        if isinstance(error, BackupError):
            raise
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
        description="Create a timestamped post-write snapshot of a SelfContext vault"
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
