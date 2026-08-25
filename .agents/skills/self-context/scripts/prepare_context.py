#!/usr/bin/env python3
"""Prepare a bounded, read-only evidence packet for a SelfContext task.

This module composes the existing compatibility, log, navigation, and lexical
retrieval helpers.  It deliberately does not infer an owner, activate a
vertical, initialize a vault, write an index, run lint, or decide whether two
pages describe the same concept.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    import log_utils
    import search_vault
    import sync_indexes
    import vault_utils
except ImportError:  # pragma: no cover - package-style import fallback
    from . import log_utils, search_vault, sync_indexes, vault_utils  # type: ignore


DEFAULT_RESULT_LIMIT = 10
DEFAULT_NAVIGATION_LIMIT = 20
DEFAULT_LINKED_SOURCE_LIMIT = 3
SNIPPET_LIMIT = 220
LOG_SNIPPET_LIMIT = 240
SOURCE_REFERENCE_LIMIT = 12


def _non_negative(value: int, name: str) -> int:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _bounded_text(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _as_sequence(values: Optional[Sequence[Any]]) -> List[Any]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return list(values)


def _as_strings(values: Optional[Sequence[Any]]) -> List[str]:
    return [str(value) for value in _as_sequence(values)]


def _unique_anchors(query: Optional[str], anchors: Optional[Sequence[str]]) -> List[str]:
    values: List[str] = []
    seen: set[str] = set()
    for raw in ([query] if query is not None else []) + _as_sequence(anchors):
        value = str(raw).strip()
        if not value:
            continue
        normalized = vault_utils.normalized_text(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        values.append(value)
    return values


def _append_finding(findings: List[Dict[str, Any]], finding: Mapping[str, Any]) -> None:
    candidate = dict(finding)
    if candidate not in findings:
        findings.append(candidate)


def _schema_packet(schema: Mapping[str, Any]) -> Dict[str, Any]:
    contracts: List[Dict[str, Any]] = []
    for entry in schema.get("contract_entries", []) or []:
        if not isinstance(entry, Mapping):
            continue
        contracts.append(
            {
                "id": entry.get("id"),
                "version": entry.get("version"),
                "version_text": entry.get("version_text"),
                "raw": entry.get("raw"),
                "error": entry.get("error"),
            }
        )
    return {
        "version": schema.get("version_text"),
        "contract_section_present": bool(schema.get("contract_section_present")),
        "contracts": contracts,
        "contract_errors": list(schema.get("contract_errors", []) or []),
        "legacy_enabled_verticals": list(
            schema.get("legacy_enabled_verticals", []) or []
        ),
    }


def _runtime_packet(root: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return compatibility metadata and a small presence classification."""

    compatibility = dict(vault_utils.runtime_compatibility(root))
    if not root.exists() and not root.is_symlink():
        compatibility.update(
            {
                "state": "missing",
                "ok": False,
                "blocked": True,
                "schema_state": "missing",
                "contract_state": "not-checked",
                "message": "vault is missing; no files were created",
            }
        )
        return compatibility, {"state": "missing", "present": False}

    if not root.is_symlink() and root.is_dir():
        try:
            has_entries = any(root.iterdir())
        except OSError:
            has_entries = True
        if not has_entries:
            compatibility.update(
                {
                    "state": "empty",
                    "ok": False,
                    "blocked": True,
                    "schema_state": "empty",
                    "contract_state": "not-checked",
                    "message": "vault directory is empty; no files were created",
                }
            )
            return compatibility, {"state": "empty", "present": True}
        return compatibility, {"state": "present", "present": True}

    return compatibility, {"state": "incompatible", "present": False}


def _compact_log_entry(entry: log_utils.LogEntry) -> Dict[str, Any]:
    return {
        "ordinal": entry.ordinal,
        "heading": entry.heading,
        "date": entry.date,
        "operation": entry.operation,
        "snippet": _bounded_text(entry.text, LOG_SNIPPET_LIMIT),
    }


def _normalize_navigation_paths(
    values: Optional[Sequence[str]], findings: List[Dict[str, Any]]
) -> List[str]:
    normalized, scope_findings = search_vault.normalize_scopes(_as_sequence(values))
    for message in scope_findings:
        _append_finding(
            findings,
            {
                "severity": "warning",
                "classification": "navigation",
                "state": "invalid-selection",
                "message": message,
            },
        )
    return normalized


def _selected_index_paths(
    root: Path,
    scopes: Sequence[str],
    manual_paths: Sequence[str],
    findings: List[Dict[str, Any]],
) -> List[Tuple[Path, str]]:
    """Select root, explicit-scope, and manually selected indexes only."""

    selected: Dict[str, Tuple[Path, str]] = {}

    def add(path: Path, reason: str) -> None:
        try:
            label = vault_utils.relative_label(path, root)
        except (OSError, RuntimeError, ValueError):
            return
        if label not in selected:
            selected[label] = (path, reason)

    root_index = root / "index.md"
    if root_index.is_file() and not root_index.is_symlink():
        add(root_index, "root")
    else:
        _append_finding(
            findings,
            {
                "severity": "warning",
                "classification": "navigation",
                "state": "missing-root-index",
                "path": "index.md",
                "message": "root index is unavailable; no index was created",
            },
        )

    for scope in scopes:
        candidate = root / scope
        if candidate.is_dir() and not candidate.is_symlink():
            candidate = candidate / "index.md"
        elif candidate.is_file() and not candidate.is_symlink():
            candidate = vault_utils.nearest_index(candidate, root) or candidate
        else:
            continue
        if candidate.name != "index.md":
            continue
        if candidate.is_file() and not candidate.is_symlink():
            add(candidate, f"scope:{scope}")

    for path_text in manual_paths:
        candidate = root / path_text
        if candidate.is_dir() and not candidate.is_symlink():
            candidate = candidate / "index.md"
        if candidate.name != "index.md":
            _append_finding(
                findings,
                {
                    "severity": "warning",
                    "classification": "navigation",
                    "state": "not-an-index",
                    "path": path_text,
                    "message": "selected navigation path is not an index.md file",
                },
            )
            continue
        if not candidate.is_file() or candidate.is_symlink():
            _append_finding(
                findings,
                {
                    "severity": "info",
                    "classification": "navigation",
                    "state": "missing-selection",
                    "path": path_text,
                    "message": "selected navigation index is absent; no file was created",
                },
            )
            continue
        add(candidate, f"manual:{path_text}")

    return list(selected.values())


def _navigation_record(
    path: Path, reason: str, root: Path, limit: int, findings: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    text, error = vault_utils.safe_read_text(path)
    label = vault_utils.relative_label(path, root)
    if text is None:
        _append_finding(
            findings,
            {
                "severity": "warning",
                "classification": "navigation",
                "state": "unreadable-index",
                "path": label,
                "message": error or "unable to read selected index",
            },
        )
        return None

    try:
        managed = sync_indexes.managed_entries(text)[:limit]
        links = vault_utils.markdown_link_records(path, root, text)[:limit]
    except (OSError, RuntimeError, ValueError) as error:
        _append_finding(
            findings,
            {
                "severity": "warning",
                "classification": "navigation",
                "state": "index-metadata-unavailable",
                "path": label,
                "message": f"{type(error).__name__}: unable to inspect index metadata",
            },
        )
        managed = []
        links = []

    return {
        "path": label,
        "selected_by": reason,
        "heading": vault_utils.first_heading(text),
        "description": _bounded_text(vault_utils.index_description(text), SNIPPET_LIMIT),
        "managed_entries": managed,
        "links": links,
    }


def _compact_sources(value: Any) -> List[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = [str(item) for item in value]
    else:
        values = []
    return values[:SOURCE_REFERENCE_LIMIT]


def _compact_match(item: Mapping[str, Any], anchors: Sequence[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "id": item.get("id"),
        "path": item.get("path"),
        "title": item.get("title"),
        "aliases": list(item.get("aliases", []) or [])[:SOURCE_REFERENCE_LIMIT],
        "type": item.get("type"),
        "description": item.get("description"),
        "status": item.get("status"),
        "assertion_kind": item.get("assertion_kind"),
        "generated": item.get("generated"),
        "verified": item.get("verified"),
        "stale_after": item.get("stale_after"),
        "sources": _compact_sources(item.get("sources")),
        "vertical": item.get("vertical"),
        "matched_fields": list(item.get("matched_fields", []) or []),
        "snippet": _bounded_text(item.get("snippet"), SNIPPET_LIMIT),
        "match_type": item.get("match_type"),
        "query_term_coverage": item.get("query_term_coverage"),
        "matched_term_count": item.get("matched_term_count"),
        "query_term_count": item.get("query_term_count"),
        "phrase_fields": list(item.get("phrase_fields", []) or []),
        "rank_score": item.get("rank_score"),
    }
    if anchors:
        result["matched_anchors"] = list(anchors)
    if item.get("linked_from"):
        result["linked_from"] = item.get("linked_from")
    return result


def _merge_search_results(
    reports: Sequence[Tuple[int, str, Mapping[str, Any]]],
    result_limit: int,
    linked_source_limit: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Union same-path retrieval hits without semantic deduplication."""

    matches: Dict[str, Dict[str, Any]] = {}
    linked: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for anchor_number, anchor, report in reports:
        for raw_item in report.get("results", []) or []:
            if not isinstance(raw_item, Mapping):
                continue
            path = str(raw_item.get("path") or "")
            if not path:
                continue
            if raw_item.get("linked_from"):
                key = (path, str(raw_item.get("linked_from")))
                candidate = _compact_match(raw_item, [anchor])
                previous = linked.get(key)
                if previous is None:
                    candidate["_anchor_number"] = anchor_number
                    linked[key] = candidate
                else:
                    anchors = list(previous.get("matched_anchors", []))
                    if anchor not in anchors:
                        anchors.append(anchor)
                    previous["matched_anchors"] = anchors
                continue

            candidate = _compact_match(raw_item, [anchor])
            previous = matches.get(path)
            if previous is None:
                candidate["_anchor_number"] = anchor_number
                matches[path] = candidate
                continue
            anchors = list(previous.get("matched_anchors", []))
            if anchor not in anchors:
                anchors.append(anchor)
            previous["matched_anchors"] = anchors
            previous_score = int(previous.get("rank_score") or 0)
            candidate_score = int(candidate.get("rank_score") or 0)
            if candidate_score > previous_score:
                candidate["matched_anchors"] = anchors
                candidate["_anchor_number"] = min(
                    int(previous.get("_anchor_number", anchor_number)), anchor_number
                )
                matches[path] = candidate

    ordered_matches = sorted(
        matches.values(),
        key=lambda item: (
            -int(item.get("rank_score") or 0),
            str(item.get("path") or ""),
        ),
    )[:result_limit]
    ordered_linked = sorted(
        linked.values(),
        key=lambda item: (
            int(item.get("_anchor_number", 0)),
            str(item.get("linked_from") or ""),
            str(item.get("path") or ""),
        ),
    )[:linked_source_limit]
    for item in ordered_matches + ordered_linked:
        item.pop("_anchor_number", None)
    return ordered_matches, ordered_linked


def prepare_context(
    vault: Path,
    explicit_scope: Optional[Sequence[str]] = None,
    *,
    scope: Optional[Sequence[str]] = None,
    query: Optional[str] = None,
    anchors: Optional[Sequence[str]] = None,
    recent_limit: int = log_utils.DEFAULT_LOG_LIMIT,
    result_limit: int = DEFAULT_RESULT_LIMIT,
    linked_source_limit: int = DEFAULT_LINKED_SOURCE_LIMIT,
    expand_linked_sources: bool = False,
    navigation_paths: Optional[Sequence[str]] = None,
    index_paths: Optional[Sequence[str]] = None,
    navigation_limit: int = DEFAULT_NAVIGATION_LIMIT,
    contextual: bool = False,
    include_sources: bool = False,
    include_derived: bool = False,
    exclude_archived: bool = False,
    exclude_superseded: bool = False,
) -> Dict[str, Any]:
    """Return a compact, bounded, read-only context-preparation packet.

    ``explicit_scope`` is intentionally required for candidate search.  An
    empty scope never means "search every vertical"; the caller must make the
    scope decision before this helper runs.  ``index_paths`` is accepted as a
    compatibility alias for manually selected navigation paths.
    """

    if scope is not None:
        if explicit_scope is not None:
            raise ValueError("provide explicit_scope or scope, not both")
        explicit_scope = scope
    if index_paths is not None:
        if navigation_paths is not None:
            raise ValueError("provide navigation_paths or index_paths, not both")
        navigation_paths = index_paths

    recent_limit = _non_negative(recent_limit, "recent_limit")
    result_limit = _non_negative(result_limit, "result_limit")
    linked_source_limit = _non_negative(linked_source_limit, "linked_source_limit")
    navigation_limit = _non_negative(navigation_limit, "navigation_limit")
    linked_source_limit = min(DEFAULT_LINKED_SOURCE_LIMIT, linked_source_limit)

    root = Path(vault).expanduser()
    findings: List[Dict[str, Any]] = []
    scope_values = _as_sequence(explicit_scope)
    requested_scope = _as_strings(scope_values)
    scopes, scope_findings = search_vault.normalize_scopes(scope_values)
    for message in scope_findings:
        _append_finding(
            findings,
            {
                "severity": "warning",
                "classification": "scope",
                "state": "invalid-scope",
                "message": message,
            },
        )
    manual_navigation = _normalize_navigation_paths(navigation_paths, findings)
    search_anchors = _unique_anchors(query, anchors)

    runtime, presence = _runtime_packet(root)
    schema = vault_utils.parse_schema(root)
    if presence["state"] == "missing":
        _append_finding(
            findings,
            {
                "severity": "info",
                "classification": "vault-state",
                "state": "missing",
                "message": "vault is missing; read-only preparation made no filesystem changes",
            },
        )
    elif presence["state"] == "empty":
        _append_finding(
            findings,
            {
                "severity": "info",
                "classification": "vault-state",
                "state": "empty",
                "message": "vault directory is empty; read-only preparation made no filesystem changes",
            },
        )
    elif not runtime.get("ok"):
        _append_finding(findings, vault_utils.runtime_compatibility_finding(runtime))

    controls: Dict[str, Any] = {
        "read_only": True,
        "initializes_missing_vault": False,
        "runs_deep_lint": False,
        "requested_scope": requested_scope,
        "scope": scopes,
        "search_anchors": search_anchors,
        "recent_limit": recent_limit,
        "result_limit": result_limit,
        "linked_source_limit": linked_source_limit if expand_linked_sources else 0,
        "navigation_limit": navigation_limit,
        "search_scope_required": True,
        "search_performed": False,
    }

    packet: Dict[str, Any] = {
        "runtime": runtime,
        "schema": _schema_packet(schema),
        "controls": controls,
        "recent": [],
        "navigation": [],
        "matches": [],
        "linked_sources": [],
        "findings": findings,
    }

    if not presence["present"]:
        return packet

    selected_indexes = _selected_index_paths(root, scopes, manual_navigation, findings)
    for index_path, reason in selected_indexes:
        record = _navigation_record(
            index_path, reason, root, navigation_limit, findings
        )
        if record is not None:
            packet["navigation"].append(record)

    if recent_limit:
        try:
            log_path = log_utils.operation_log_path(root)
            entries = log_utils.read_recent_entries(log_path, limit=recent_limit)
            packet["recent"] = [_compact_log_entry(entry) for entry in entries]
        except (log_utils.LogReadError, OSError, UnicodeError) as error:
            _append_finding(
                findings,
                {
                    "severity": "warning",
                    "classification": "continuity",
                    "state": "recent-log-unavailable",
                    "path": "log.md",
                    "message": str(error).split(": ", 1)[0],
                },
            )

    if not search_anchors:
        return packet
    if not runtime.get("ok"):
        _append_finding(
            findings,
            {
                "severity": "info",
                "classification": "search",
                "state": "runtime-blocked",
                "message": "candidate search skipped because the vault is not current",
            },
        )
        return packet
    if not scopes:
        _append_finding(
            findings,
            {
                "severity": "warning",
                "classification": "search",
                "state": "scope-required",
                "message": "candidate search skipped; provide an explicit scope instead of searching every vertical",
            },
        )
        return packet

    controls["search_performed"] = True
    reports: List[Tuple[int, str, Mapping[str, Any]]] = []
    search_limit = result_limit
    if expand_linked_sources and result_limit:
        # search_vault reserves three slots for its existing linked-source
        # expansion.  The preparation packet applies the caller's smaller
        # linked-source cap after composition.
        search_limit += DEFAULT_LINKED_SOURCE_LIMIT
    for anchor_number, anchor in enumerate(search_anchors):
        report = search_vault.search_vault(
            root,
            anchor,
            limit=search_limit,
            scope=scopes,
            contextual=contextual,
            include_sources=include_sources,
            include_derived=include_derived,
            expand_linked_sources=expand_linked_sources,
            exclude_archived=exclude_archived,
            exclude_superseded=exclude_superseded,
            include_identity=True,
        )
        reports.append((anchor_number, anchor, report))
        for message in report.get("findings", []) or []:
            _append_finding(
                findings,
                {
                    "severity": "warning",
                    "classification": "search",
                    "state": "retrieval-finding",
                    "anchor": anchor,
                    "message": str(message),
                },
            )

    matches, linked_sources = _merge_search_results(
        reports,
        result_limit=result_limit,
        linked_source_limit=linked_source_limit if expand_linked_sources else 0,
    )
    packet["matches"] = matches
    packet["linked_sources"] = linked_sources
    return packet


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from error
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a bounded, read-only SelfContext evidence packet"
    )
    parser.add_argument("vault", nargs="?", default="vault")
    parser.add_argument("--scope", action="append", default=[], metavar="PATH")
    parser.add_argument("--query")
    parser.add_argument("--anchor", action="append", default=[], metavar="TEXT")
    parser.add_argument("--recent-limit", type=_non_negative_int, default=log_utils.DEFAULT_LOG_LIMIT)
    parser.add_argument("--result-limit", type=_non_negative_int, default=DEFAULT_RESULT_LIMIT)
    parser.add_argument("--linked-source-limit", type=_non_negative_int, default=DEFAULT_LINKED_SOURCE_LIMIT)
    parser.add_argument("--expand-linked-sources", action="store_true")
    parser.add_argument("--index", action="append", default=[], dest="navigation_paths", metavar="PATH")
    parser.add_argument("--navigation-limit", type=_non_negative_int, default=DEFAULT_NAVIGATION_LIMIT)
    parser.add_argument("--contextual", action="store_true")
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument("--include-derived", action="store_true")
    parser.add_argument("--exclude-archived", action="store_true")
    parser.add_argument("--exclude-superseded", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)

    packet = prepare_context(
        Path(args.vault),
        explicit_scope=args.scope,
        query=args.query,
        anchors=args.anchor,
        recent_limit=args.recent_limit,
        result_limit=args.result_limit,
        linked_source_limit=args.linked_source_limit,
        expand_linked_sources=args.expand_linked_sources,
        navigation_paths=args.navigation_paths,
        navigation_limit=args.navigation_limit,
        contextual=args.contextual,
        include_sources=args.include_sources,
        include_derived=args.include_derived,
        exclude_archived=args.exclude_archived,
        exclude_superseded=args.exclude_superseded,
    )
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
