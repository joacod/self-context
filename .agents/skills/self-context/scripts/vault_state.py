#!/usr/bin/env python3
"""Canonical byte snapshots and diffs for SelfContext vault state."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Mapping, Tuple

try:
    from vault_utils import canonical_files, relative_label, safe_read_bytes
except ImportError:  # pragma: no cover - package-style import fallback
    from .vault_utils import canonical_files, relative_label, safe_read_bytes  # type: ignore


def canonical_bytes(root: Path) -> Dict[str, bytes]:
    """Read the canonical vault files as a relative-path byte snapshot."""

    result: Dict[str, bytes] = {}
    for path in canonical_files(root):
        content, error = safe_read_bytes(path)
        if content is None:
            raise OSError(error or f"unable to read {path}")
        result[relative_label(path, root)] = content
    return result


def diff_bytes(
    original: Mapping[str, bytes], proposed: Mapping[str, bytes]
) -> Tuple[List[str], List[str], List[str]]:
    """Return created, modified, and deleted relative paths in stable order."""

    created = sorted(set(proposed) - set(original))
    deleted = sorted(set(original) - set(proposed))
    modified = sorted(
        label
        for label in set(original).intersection(proposed)
        if original[label] != proposed[label]
    )
    return created, modified, deleted
