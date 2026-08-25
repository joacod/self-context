#!/usr/bin/env python3
"""Bounded filesystem transactions for an existing vault root."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


def _write_temp_sibling(path: Path, content: bytes, suffix: str = "") -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.transaction-",
        suffix=suffix,
        dir=str(path.parent),
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            mode = path.stat().st_mode & 0o777
            os.chmod(temporary, mode)
        except (OSError, NotImplementedError):
            pass
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return temporary


def _cleanup_temporary(paths: Iterable[Path]) -> List[str]:
    failures: List[str] = []
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as error:
            failures.append(f"{path}: {error}")
    return failures


def _ensure_parent(path: Path, vault: Path, created: List[Path]) -> None:
    missing: List[Path] = []
    current = path.parent
    while current != vault and not current.exists():
        missing.append(current)
        current = current.parent
    if current != vault and (current.is_symlink() or not current.is_dir()):
        raise OSError(f"parent is not a real directory: {current}")
    for directory in reversed(missing):
        directory.mkdir()
        created.append(directory)


def _verify_rollback(transaction: Mapping[str, Any]) -> List[str]:
    failures: List[str] = []
    originals: Mapping[Path, Optional[bytes]] = transaction.get("originals", {})
    for path, original in originals.items():
        try:
            if original is None:
                if path.exists() or path.is_symlink():
                    failures.append(f"{path}: newly created file remains")
            elif not path.is_file() or path.read_bytes() != original:
                failures.append(f"{path}: original bytes were not restored")
        except OSError as error:
            failures.append(f"{path}: unable to verify rollback: {error}")
    for directory in transaction.get("created_dirs", []):
        if directory.exists():
            failures.append(f"{directory}: newly created directory remains")
    return failures


def rollback_transaction(transaction: Mapping[str, Any]) -> Dict[str, Any]:
    replaced = list(transaction.get("replaced", []))
    originals: Mapping[Path, Optional[bytes]] = transaction.get("originals", {})
    temporary: List[Path] = []
    failures: List[str] = []
    for path in reversed(replaced):
        original = originals.get(path)
        try:
            if original is None:
                path.unlink(missing_ok=True)
            else:
                rollback = _write_temp_sibling(path, original, suffix="-rollback")
                temporary.append(rollback)
                os.replace(rollback, path)
                temporary.remove(rollback)
        except Exception as error:
            failures.append(f"{path}: {error}")
    failures.extend(_cleanup_temporary(temporary))

    for directory in sorted(
        transaction.get("created_dirs", []),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except FileNotFoundError:
            pass
        except OSError as error:
            failures.append(f"{directory}: {error}")
    failures.extend(_verify_rollback(transaction))
    return {
        "status": "rolled-back" if not failures else "rollback-failed",
        "ok": not failures,
        "failures": failures,
    }


def replace_planned_files(vault: Path, updates: Mapping[str, bytes]) -> Dict[str, Any]:
    """Replace an existing root's planned file set with bounded rollback."""

    originals: Dict[Path, Optional[bytes]] = {}
    temporary: List[Path] = []
    temporary_by_path: Dict[Path, Path] = {}
    replaced: List[Path] = []
    created_dirs: List[Path] = []
    try:
        paths = {vault / label: content for label, content in updates.items()}
        ordered_paths = sorted(paths, key=lambda item: item.as_posix())
        for path in ordered_paths:
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise OSError(f"target is not a regular file: {path}")
            originals[path] = path.read_bytes() if path.exists() else None
            _ensure_parent(path, vault, created_dirs)
        for path in ordered_paths:
            temporary_path = _write_temp_sibling(path, paths[path])
            temporary.append(temporary_path)
            temporary_by_path[path] = temporary_path
        for path in ordered_paths:
            temporary_path = temporary_by_path[path]
            os.replace(temporary_path, path)
            temporary.remove(temporary_path)
            replaced.append(path)
        return {
            "ok": True,
            "replaced": replaced,
            "originals": originals,
            "created_dirs": created_dirs,
            "temporary": temporary,
        }
    except Exception as error:
        cleanup_failures = _cleanup_temporary(temporary)
        transaction = {
            "replaced": replaced,
            "originals": originals,
            "created_dirs": created_dirs,
        }
        rollback = rollback_transaction(transaction)
        failures = [str(error)] + cleanup_failures + rollback.get("failures", [])
        return {
            "ok": False,
            "error": str(error),
            "replaced": replaced,
            "originals": originals,
            "created_dirs": created_dirs,
            "temporary": [],
            "rollback": rollback,
            "failures": failures,
        }
