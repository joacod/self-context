#!/usr/bin/env python3
"""Dependency-free parsing and retrieval helpers for the operation log.

The Markdown log remains the canonical history.  These helpers only read it,
parse the documented level-two operation entries, and return bounded views.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple

try:
    from vault_utils import normalized_text, normalized_tokens
except ImportError:  # pragma: no cover
    from .vault_utils import normalized_text, normalized_tokens  # type: ignore


DEFAULT_LOG_LIMIT = 10
TAIL_CHUNK_SIZE = 64 * 1024
ENTRY_HEADING_PATTERN = re.compile(r"^##(?!#)[ \t]+(.+?)\s*$")
ENTRY_START_BYTES_PATTERN = re.compile(rb"(?m)^##(?!#)[ \t]+")
DATE_PATTERN = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")
OPERATION_PATTERN = re.compile(
    r"(?mi)^[ \t]*-[ \t]*operation:[ \t]*(\S.*?)\s*$"
)


class LogReadError(RuntimeError):
    """A stable, user-facing operation-log read failure."""


@dataclass(frozen=True)
class LogEntry:
    """One complete level-two operation entry, preserving its source text."""

    text: str
    ordinal: int
    heading: str
    date: Optional[str]
    operation: Optional[str]

    @classmethod
    def from_text(cls, text: str, ordinal: int) -> "LogEntry":
        lines = text.splitlines()
        heading_line = lines[0].rstrip("\r\n") if lines else ""
        heading_match = ENTRY_HEADING_PATTERN.match(heading_line)
        heading = heading_match.group(1).strip() if heading_match else heading_line.strip()
        date_match = DATE_PATTERN.search(heading)
        operation_match = OPERATION_PATTERN.search(text)
        return cls(
            text=text,
            ordinal=ordinal,
            heading=heading,
            date=date_match.group(1) if date_match else None,
            operation=operation_match.group(1).strip() if operation_match else None,
        )


def is_entry_heading(line: str) -> bool:
    """Return whether *line* starts a documented operation entry."""

    return ENTRY_HEADING_PATTERN.match(line.rstrip("\r\n")) is not None


def iter_log_entries(lines: Iterable[str]) -> Iterator[LogEntry]:
    """Yield complete operation entries from a line stream.

    The preamble before the first ``##`` entry heading is intentionally ignored;
    it is the log title or other control prose, not an operation entry.  A
    level-three-or-deeper heading remains part of the current entry.
    """

    current: Optional[List[str]] = None
    ordinal = 0
    for line in lines:
        if is_entry_heading(line):
            if current is not None:
                yield LogEntry.from_text("".join(current), ordinal)
                ordinal += 1
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        yield LogEntry.from_text("".join(current), ordinal)


def iter_log_file(path: Path) -> Iterator[LogEntry]:
    """Stream complete entries from a UTF-8 operation log."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from iter_log_entries(handle)


def operation_log_path(vault: Path) -> Path:
    """Validate a vault path and return its canonical operation-log path."""

    vault = vault.expanduser()
    if not vault.exists() or vault.is_symlink() or not vault.is_dir():
        raise LogReadError(f"vault path is not a real directory: {vault}")
    path = vault / "log.md"
    if not path.exists() or path.is_symlink() or not path.is_file():
        raise LogReadError(f"missing required operation log: {path}")
    return path


def _entry_start_offsets(data: bytes, file_start: bool) -> List[int]:
    starts: List[int] = []
    for match in ENTRY_START_BYTES_PATTERN.finditer(data):
        # A tail chunk can begin in the middle of a line.  A match at offset
        # zero is only a trustworthy heading when the buffer starts at EOF's
        # opposite boundary (the beginning of the file).
        if match.start() == 0 and not file_start:
            continue
        starts.append(match.start())
    return starts


def _decode_selected(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LogReadError("UnicodeDecodeError: file is not valid UTF-8") from error


def read_recent_text(path: Path, limit: int = DEFAULT_LOG_LIMIT) -> str:
    """Return the newest *limit* complete entries without reading old history.

    The file is read backwards in bounded chunks and stops after the requested
    number of entry headings is present.  The selected bytes begin at an entry
    boundary and are decoded only after selection.
    """

    if limit < 0:
        raise ValueError("limit must be non-negative")
    if limit == 0:
        return ""

    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            end = handle.tell()
            tail = b""
            buffer_start = end
            starts: List[int] = []
            while end > 0:
                start = max(0, end - TAIL_CHUNK_SIZE)
                handle.seek(start)
                tail = handle.read(end - start) + tail
                buffer_start = start
                starts = _entry_start_offsets(tail, file_start=buffer_start == 0)
                if len(starts) >= limit:
                    return _decode_selected(tail[starts[-limit] :])
                end = start
            return _decode_selected(tail[starts[0] :] if starts else b"")
    except FileNotFoundError as error:
        raise LogReadError(f"missing required operation log: {path}") from error
    except IsADirectoryError as error:
        raise LogReadError(f"operation log is not a regular file: {path}") from error
    except UnicodeError:
        raise
    except OSError as error:
        raise LogReadError(f"unable to read operation log: {path}") from error


def read_recent_entries(path: Path, limit: int = DEFAULT_LOG_LIMIT) -> List[LogEntry]:
    """Return the newest entries in source order, oldest selected first."""

    text = read_recent_text(path, limit=limit)
    return list(iter_log_entries(text.splitlines(keepends=True)))


def _unique_tokens(values: Sequence[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


@dataclass(frozen=True)
class LogMatch:
    entry: LogEntry
    score: int
    matched_terms: Tuple[str, ...]
    query_term_coverage: float


def score_log_entry(entry: LogEntry, query: str) -> Optional[LogMatch]:
    """Score one entry with transparent exact/coverage lexical priorities."""

    query_text = normalized_text(query)
    query_terms = _unique_tokens(normalized_tokens(query))
    if not query_terms:
        return None

    entry_text = normalized_text(entry.text)
    entry_tokens = set(normalized_tokens(entry.text))
    matched_terms = tuple(term for term in query_terms if term in entry_tokens)
    if not matched_terms:
        return None

    coverage = len(matched_terms) / len(query_terms)
    score = int(coverage * 1_000_000) + len(matched_terms) * 10_000
    if query_text and query_text in entry_text:
        score += 3_000_000
    heading_text = normalized_text(entry.heading)
    if query_text and query_text in heading_text:
        score += 1_000_000
    operation_text = normalized_text(entry.operation or "")
    if query_text and query_text in operation_text:
        score += 2_000_000

    return LogMatch(
        entry=entry,
        score=score,
        matched_terms=matched_terms,
        query_term_coverage=round(coverage, 3),
    )


def search_log_entries(
    path: Path, query: str, limit: int = DEFAULT_LOG_LIMIT
) -> List[LogMatch]:
    """Stream the complete log and return bounded, deterministically ranked matches."""

    if limit < 0:
        raise ValueError("limit must be non-negative")
    if limit == 0:
        return []

    matches: List[LogMatch] = []
    try:
        for entry in iter_log_file(path):
            match = score_log_entry(entry, query)
            if match is not None:
                matches.append(match)
    except FileNotFoundError as error:
        raise LogReadError(f"missing required operation log: {path}") from error
    except IsADirectoryError as error:
        raise LogReadError(f"operation log is not a regular file: {path}") from error
    except UnicodeDecodeError as error:
        raise LogReadError("UnicodeDecodeError: file is not valid UTF-8") from error
    except OSError as error:
        raise LogReadError(f"unable to read operation log: {path}") from error

    matches.sort(key=lambda match: (-match.score, -match.entry.ordinal))
    return matches[:limit]
