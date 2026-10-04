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
from itertools import islice
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
DEFAULT_REPLACEMENT_DEPTH_LIMIT = vault_utils.REPLACEMENT_DEPTH_LIMIT
DEFAULT_RELATED_REPLACEMENT_LIMIT = vault_utils.RELATED_REPLACEMENT_LIMIT
DEFAULT_EVIDENCE_PAGE_LIMIT = 3
DEFAULT_EVIDENCE_BYTE_LIMIT = 24 * 1024
DEFAULT_PACKET_BYTE_LIMIT = 32 * 1024
SNIPPET_LIMIT = 220
LOG_SNIPPET_LIMIT = 240
SOURCE_REFERENCE_LIMIT = 12
METADATA_LIMIT = 240
PATH_LIMIT = 400
DATE_LIMIT = 64
OMIT_PAGE_TOO_LARGE = "page too large"
OMIT_BUDGET_EXHAUSTED = "aggregate budget exhausted"
OMIT_PAGE_LIMIT = "page limit exhausted"
OMIT_UNREADABLE = "unreadable"


def _non_negative(value: int, name: str) -> int:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _bounded_text(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _bounded_optional(value: Any, limit: int = METADATA_LIMIT) -> Any:
    if value is None:
        return None
    return _bounded_text(value, limit)


def _compact_text_list(value: Any, *, count: int, limit: int = METADATA_LIMIT) -> List[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = [str(item) for item in value]
    else:
        values = []
    return [_bounded_text(item, limit) for item in values[:count]]


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
        managed_candidates = sync_indexes.managed_entries(text, limit=limit + 1)
        managed = [
            _compact_navigation_entry(entry)
            for entry in managed_candidates[:limit]
            if isinstance(entry, Mapping)
        ]
        links = [
            _compact_link(link)
            for link in vault_utils.markdown_link_records(path, root, text, limit=limit)
            if isinstance(link, Mapping)
        ]
        managed_truncated = len(managed_candidates) > limit
        links_truncated = any(islice(vault_utils.iter_markdown_links(text), limit, limit + 1))
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
        managed_truncated = False
        links_truncated = False

    return {
        "path": _bounded_text(label, PATH_LIMIT),
        "selected_by": _bounded_text(reason, PATH_LIMIT),
        "heading": _bounded_text(vault_utils.first_heading(text), METADATA_LIMIT),
        "description": _bounded_text(vault_utils.index_description(text), SNIPPET_LIMIT),
        "managed_entries": managed,
        "links": links,
        "managed_entries_truncated": managed_truncated,
        "links_truncated": links_truncated,
    }


def _compact_navigation_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "title": _bounded_text(entry.get("title"), METADATA_LIMIT),
        "path": _bounded_text(entry.get("path"), PATH_LIMIT),
        "description": _bounded_text(entry.get("description"), METADATA_LIMIT),
        "status": _bounded_text(entry.get("status"), DATE_LIMIT),
    }


def _compact_link(link: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "source": _bounded_text(link.get("source"), PATH_LIMIT),
        "destination": _bounded_text(link.get("destination"), PATH_LIMIT),
        "target": _bounded_optional(link.get("target"), PATH_LIMIT),
        "external": bool(link.get("external")),
        "exists": bool(link.get("exists")),
        "leaves_vault": bool(link.get("leaves_vault")),
        "kind": _bounded_text(link.get("kind"), DATE_LIMIT),
    }


def _compact_match(item: Mapping[str, Any], anchors: Sequence[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "id": _bounded_optional(item.get("id"), PATH_LIMIT),
        "path": _bounded_text(item.get("path"), PATH_LIMIT),
        "title": _bounded_text(item.get("title"), METADATA_LIMIT),
        "aliases": _compact_text_list(
            item.get("aliases"), count=SOURCE_REFERENCE_LIMIT
        ),
        "type": _bounded_optional(item.get("type"), DATE_LIMIT),
        "description": _bounded_optional(item.get("description")),
        "status": _bounded_optional(item.get("status"), DATE_LIMIT),
        "assertion_kind": _bounded_optional(item.get("assertion_kind"), DATE_LIMIT),
        "generated": _bounded_optional(item.get("generated"), DATE_LIMIT),
        "verified": _bounded_optional(item.get("verified"), DATE_LIMIT),
        "stale_after": _bounded_optional(item.get("stale_after"), DATE_LIMIT),
        "sources": _compact_text_list(
            item.get("sources"), count=SOURCE_REFERENCE_LIMIT, limit=PATH_LIMIT
        ),
        "vertical": _bounded_optional(item.get("vertical"), DATE_LIMIT),
        "matched_fields": _compact_text_list(
            item.get("matched_fields"), count=SOURCE_REFERENCE_LIMIT, limit=DATE_LIMIT
        ),
        "snippet": _bounded_text(item.get("snippet"), SNIPPET_LIMIT),
        "match_type": _bounded_optional(item.get("match_type"), DATE_LIMIT),
        "query_term_coverage": item.get("query_term_coverage"),
        "matched_term_count": item.get("matched_term_count"),
        "query_term_count": item.get("query_term_count"),
        "phrase_fields": _compact_text_list(
            item.get("phrase_fields"), count=SOURCE_REFERENCE_LIMIT, limit=DATE_LIMIT
        ),
        "rank_score": item.get("rank_score"),
        "accent_folded": bool(item.get("accent_folded")),
    }
    if item.get("superseded_by"):
        result["superseded_by"] = _bounded_text(item.get("superseded_by"), PATH_LIMIT)
    if anchors:
        result["matched_anchors"] = _compact_text_list(
            anchors, count=SOURCE_REFERENCE_LIMIT
        )
    if item.get("linked_from"):
        result["linked_from"] = _bounded_text(item.get("linked_from"), PATH_LIMIT)
    pages = item.get("linked_from_pages")
    if isinstance(pages, list) and len(pages) > 1:
        result["linked_from_pages"] = _compact_text_list(
            pages, count=SOURCE_REFERENCE_LIMIT, limit=PATH_LIMIT
        )
    return result


def _compact_related_replacement(item: Mapping[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "path": _bounded_text(item.get("path"), PATH_LIMIT),
        "title": _bounded_text(item.get("title"), METADATA_LIMIT),
        "type": _bounded_optional(item.get("type"), DATE_LIMIT),
        "status": _bounded_optional(item.get("status"), DATE_LIMIT),
        "assertion_kind": _bounded_optional(item.get("assertion_kind"), DATE_LIMIT),
        "generated": _bounded_optional(item.get("generated"), DATE_LIMIT),
        "verified": _bounded_optional(item.get("verified"), DATE_LIMIT),
        "stale_after": _bounded_optional(item.get("stale_after"), DATE_LIMIT),
        "from": _bounded_text(item.get("from"), PATH_LIMIT),
        "relationship": _bounded_text(item.get("relationship"), DATE_LIMIT),
        "chain": _compact_text_list(
            item.get("chain"), count=SOURCE_REFERENCE_LIMIT, limit=PATH_LIMIT
        ),
        "depth": item.get("depth"),
    }
    if item.get("id") not in (None, ""):
        result["id"] = _bounded_text(item.get("id"), PATH_LIMIT)
    if item.get("superseded_by"):
        result["superseded_by"] = _bounded_text(item.get("superseded_by"), PATH_LIMIT)
    return result


def _compact_unresolved_replacement(item: Mapping[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "from": _bounded_text(item.get("from"), PATH_LIMIT),
        "path": _bounded_text(item.get("path"), PATH_LIMIT),
        "relationship": _bounded_text(item.get("relationship"), DATE_LIMIT),
        "chain": _compact_text_list(
            item.get("chain"), count=SOURCE_REFERENCE_LIMIT, limit=PATH_LIMIT
        ),
        "depth": item.get("depth"),
        "reason": _bounded_text(item.get("reason"), METADATA_LIMIT),
    }
    if "superseded_by" in item:
        result["superseded_by"] = _bounded_optional(item.get("superseded_by"), PATH_LIMIT)
    return result


def _terms_for_matches(matches: Sequence[Mapping[str, Any]]) -> List[str]:
    for item in matches:
        for anchor in item.get("matched_anchors") or []:
            return search_vault._query_terms(str(anchor))
    return []


def _anchors_for_parents(
    parent_paths: Sequence[str],
    anchors_by_path: Mapping[str, Sequence[str]],
) -> List[str]:
    anchors: List[str] = []
    seen: set[str] = set()
    for parent_path in parent_paths:
        for anchor in anchors_by_path.get(parent_path, ()):
            if anchor in seen:
                continue
            seen.add(anchor)
            anchors.append(anchor)
    return anchors


def _merge_search_results(
    reports: Sequence[Tuple[int, str, Mapping[str, Any]]],
    result_limit: int,
    linked_source_limit: int,
    *,
    corpus: Optional[search_vault._SearchCorpus] = None,
    include_identity: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Union same-path retrieval hits without semantic deduplication.

    Primary matches are merged, ranked, and truncated first. Linked sources are
    then selected from those surviving pages rather than from independently
    truncated per-anchor provenance lists.
    """

    matches: Dict[str, Dict[str, Any]] = {}
    for anchor_number, anchor, report in reports:
        for raw_item in report.get("results", []) or []:
            if not isinstance(raw_item, Mapping):
                continue
            path = str(raw_item.get("path") or "")
            if not path or raw_item.get("linked_from"):
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
            if search_vault.ranking_key(candidate) < search_vault.ranking_key(previous):
                candidate["matched_anchors"] = anchors
                candidate["_anchor_number"] = min(
                    int(previous.get("_anchor_number", anchor_number)), anchor_number
                )
                matches[path] = candidate

    ordered_matches = sorted(
        matches.values(),
        key=search_vault.ranking_key,
    )[:result_limit]
    for item in ordered_matches:
        item.pop("_anchor_number", None)
    if (
        linked_source_limit <= 0
        or not ordered_matches
        or corpus is None
    ):
        return ordered_matches, []

    raw_linked = search_vault._expand_linked_sources(
        corpus,
        ordered_matches,
        budget=linked_source_limit,
        terms=_terms_for_matches(ordered_matches),
        include_identity=include_identity,
    )
    anchors_by_path = {
        str(item.get("path") or ""): list(item.get("matched_anchors") or [])
        for item in ordered_matches
        if item.get("path")
    }
    ordered_linked: List[Dict[str, Any]] = []
    for raw_item in raw_linked:
        parents = raw_item.get("linked_from_pages")
        if not isinstance(parents, list) or not parents:
            parent = raw_item.get("linked_from")
            parents = [parent] if parent else []
        ordered_linked.append(
            _compact_match(raw_item, _anchors_for_parents(parents, anchors_by_path))
        )
    return ordered_matches, ordered_linked


def _serialized_utf8_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def _record_for_selected_path(
    path: str,
    root: Path,
    records_by_path: Optional[Mapping[str, Mapping[str, Any]]],
) -> Tuple[Optional[Mapping[str, Any]], Optional[str]]:
    if records_by_path is not None and path in records_by_path:
        record = records_by_path[path]
        if isinstance(record.get("text"), str) and isinstance(record.get("content_hash"), str):
            return record, None
        return record, OMIT_UNREADABLE
    return vault_utils.page_record_for_label(root, path)


def _select_complete_evidence(
    matches: Sequence[Mapping[str, Any]],
    *,
    root: Path,
    records_by_path: Optional[Mapping[str, Mapping[str, Any]]],
    page_limit: int,
    byte_limit: int,
    related: Sequence[Mapping[str, Any]] = (),
    replacement_depth_limit: int = DEFAULT_REPLACEMENT_DEPTH_LIMIT,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Include complete original pages for selected candidates, without truncation.

    ``page_limit`` and ``byte_limit`` bound this evidence section only. The
    ranked ``matches`` list stays unchanged. Within its first ``page_limit``
    candidates, successor/predecessor evidence is allocated before unrelated
    matches. The furthest discovered successor comes first for tight budgets;
    it is not necessarily current when traversal reports an unresolved edge.
    """

    included: List[Dict[str, Any]] = []
    omitted: List[Dict[str, Any]] = []
    used_bytes = 2  # JSON list brackets; each following entry adds a separator.
    considered: set[str] = set()

    def consider(path: str) -> None:
        nonlocal used_bytes
        if len(included) >= page_limit:
            omitted.append({"path": path, "reason": OMIT_PAGE_LIMIT})
            return
        record, error = _record_for_selected_path(path, root, records_by_path)
        evidence = (
            vault_utils.complete_page_evidence(record) if record is not None else None
        )
        if evidence is None:
            omitted.append({"path": path, "reason": error or OMIT_UNREADABLE})
            return
        size = _serialized_utf8_size(evidence)
        if size + 2 > byte_limit:
            omitted.append({"path": path, "reason": OMIT_PAGE_TOO_LARGE})
            return
        size += 2 if included else 0
        if used_bytes + size > byte_limit:
            omitted.append({"path": path, "reason": OMIT_BUDGET_EXHAUSTED})
            return
        included.append(evidence)
        used_bytes += size

    selected = matches[:page_limit]
    visible = {str(item.get("path")): item for item in [*matches, *related]}
    priority: List[Mapping[str, Any]] = []
    for item in selected:
        successors: List[Mapping[str, Any]] = []
        current = item
        visited = {str(item.get("path"))}
        if item.get("status") != "superseded":
            continue
        for _ in range(replacement_depth_limit):
            target, error = vault_utils.resolve_superseded_by_target(
                str(current.get("path")), current.get("superseded_by"), root, scopes=()
            )
            if error or target not in visible or target in visited:
                break
            visited.add(target)
            current = visible[target]
            successors.append(current)
        if successors:
            priority.extend([successors[-1], item, *successors[:-1]])

    for item in [*priority, *selected, *related]:
        path = str(item.get("path") or "")
        if not path or path in considered:
            continue
        considered.add(path)
        consider(path)
    return included, omitted


def _bound_packet(packet: Dict[str, Any], byte_limit: int) -> Dict[str, Any]:
    """Bound compact JSON output without ever truncating page contents."""
    controls = packet["controls"]
    controls["packet_byte_limit"] = byte_limit
    controls["packet_omissions"] = {}
    omissions = controls["packet_omissions"]
    if _serialized_utf8_size(packet) <= byte_limit:
        return packet

    def trim(items: List[Any], label: str) -> None:
        while items and _serialized_utf8_size(packet) > byte_limit:
            item = items.pop()
            omissions[label] = omissions.get(label, 0) + 1
            if label == "evidence":
                packet["evidence_omitted"].append({
                    "path": item["path"], "reason": "packet budget exhausted",
                })

    for entry in reversed(packet["navigation"]):
        for key, flag in (("links", "links_truncated"), ("managed_entries", "managed_entries_truncated")):
            before = len(entry[key])
            trim(entry[key], f"navigation.{key}")
            entry[flag] = entry[flag] or len(entry[key]) < before
    for section in ("recent", "navigation", "evidence", "linked_sources", "matches",
                    "related_replacements", "evidence_omitted"):
        trim(packet.get(section, []), section)
    # Never discard runtime findings or unresolved replacement qualifications
    # while returning usable evidence. If required safety metadata cannot fit,
    # block the entire packet instead of issuing an apparently complete result.
    if _serialized_utf8_size(packet) > byte_limit:
        return {
            "runtime": {"state": "packet-budget-exceeded", "ok": False, "blocked": True,
                        "original_state": _bounded_text(packet["runtime"].get("state"), 80)},
            "controls": {"read_only": True, "mutation_ready": False, "expected_snapshot": None,
                         "packet_byte_limit": byte_limit},
            "findings": [{"severity": "error", "state": "packet-budget-exceeded",
                          "message": "Required safety metadata exceeds the packet budget; retry with a larger budget or narrower scope."}],
            "matches": [], "evidence": [],
        }
    return packet


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
    include_evidence: bool = False,
    evidence_page_limit: int = DEFAULT_EVIDENCE_PAGE_LIMIT,
    evidence_byte_limit: int = DEFAULT_EVIDENCE_BYTE_LIMIT,
    replacement_depth_limit: int = DEFAULT_REPLACEMENT_DEPTH_LIMIT,
    related_replacement_limit: int = DEFAULT_RELATED_REPLACEMENT_LIMIT,
    for_update: bool = False,
    packet_byte_limit: int = DEFAULT_PACKET_BYTE_LIMIT,
) -> Dict[str, Any]:
    """Return a compact, bounded, read-only context-preparation packet.

    ``explicit_scope`` is intentionally required for candidate search.  An
    empty scope never means "search every vertical"; the caller must make the
    scope decision before this helper runs.  ``index_paths`` is accepted as a
    compatibility alias for manually selected navigation paths.

    ``for_update`` captures a canonical snapshot before reading and checks it
    afterward. Only a current, unchanged vault receives a mutation-ready
    ``expected_snapshot``. Normal queries avoid those whole-vault reads.

    ``include_evidence`` is opt-in. When disabled, the packet remains
    metadata-only. When enabled, a separate evidence section may include
    complete original page bytes for a small number of ranked canonical
    matches and related replacement pages. ``evidence_page_limit`` and
    ``evidence_byte_limit`` bound that section, including each included
    page's metadata; they do not bound the rest of the packet or an exact
    number of model tokens.

    After ranked matches are selected, explicit ``superseded_by`` links from
    selected superseded pages are followed into ``related_replacements``.
    Those successors do not need to match the query, do not consume the
    primary result limit, and are not mixed into ``linked_sources``.
    Unresolved links and stopping reasons appear in
    ``unresolved_replacements``.
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
    evidence_page_limit = _non_negative(evidence_page_limit, "evidence_page_limit")
    evidence_byte_limit = _non_negative(evidence_byte_limit, "evidence_byte_limit")
    replacement_depth_limit = _non_negative(
        replacement_depth_limit, "replacement_depth_limit"
    )
    related_replacement_limit = _non_negative(
        related_replacement_limit, "related_replacement_limit"
    )
    linked_source_limit = min(DEFAULT_LINKED_SOURCE_LIMIT, linked_source_limit)
    if packet_byte_limit < 1024:
        raise ValueError("packet_byte_limit must be at least 1024 bytes")

    root = Path(vault).expanduser()
    planning_snapshot: Optional[str] = None
    snapshot_error = False
    if for_update and root.is_dir() and not root.is_symlink():
        try:
            planning_snapshot = vault_utils.snapshot_id(root, require_readable=True)
        except (OSError, RuntimeError, ValueError):
            snapshot_error = True

    def finish(packet: Dict[str, Any]) -> Dict[str, Any]:
        if not for_update:
            return _bound_packet(packet, packet_byte_limit)
        controls = packet["controls"]
        controls.update({"mutation_ready": False, "expected_snapshot": None})
        if not packet["runtime"].get("ok"):
            return _bound_packet(packet, packet_byte_limit)
        try:
            unchanged = (
                not snapshot_error
                and planning_snapshot is not None
                and vault_utils.snapshot_id(root, require_readable=True) == planning_snapshot
            )
        except (OSError, RuntimeError, ValueError):
            unchanged = False
        if unchanged:
            controls.update({"mutation_ready": True, "expected_snapshot": planning_snapshot})
        else:
            packet["findings"].append({
                "severity": "error",
                "classification": "mutation-precondition",
                "state": "snapshot-unavailable-or-changed",
                "message": "mutation context changed or could not be snapshotted; reread before planning a write",
            })
        return _bound_packet(packet, packet_byte_limit)

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
        "requested_scope": _compact_text_list(
            requested_scope, count=32, limit=PATH_LIMIT
        ),
        "scope": _compact_text_list(scopes, count=32, limit=PATH_LIMIT),
        "search_anchors": _compact_text_list(
            search_anchors, count=32, limit=METADATA_LIMIT
        ),
        "recent_limit": recent_limit,
        "result_limit": result_limit,
        "linked_source_limit": linked_source_limit if expand_linked_sources else 0,
        "navigation_limit": navigation_limit,
        "search_scope_required": True,
        "search_performed": False,
        "replacement_depth_limit": replacement_depth_limit,
        "related_replacement_limit": related_replacement_limit,
    }
    if include_evidence:
        controls["include_evidence"] = True
        controls["evidence_page_limit"] = evidence_page_limit
        controls["evidence_byte_limit"] = evidence_byte_limit

    packet: Dict[str, Any] = {
        "runtime": runtime,
        "schema": _schema_packet(schema),
        "controls": controls,
        "recent": [],
        "navigation": [],
        "matches": [],
        "linked_sources": [],
        "related_replacements": [],
        "unresolved_replacements": [],
        "findings": findings,
    }
    if include_evidence:
        packet["evidence"] = []
        packet["evidence_omitted"] = []

    if not presence["present"]:
        return finish(packet)

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
        return finish(packet)
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
        return finish(packet)
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
        return finish(packet)

    controls["search_performed"] = True
    reports: List[Tuple[int, str, Mapping[str, Any]]] = []
    records_by_path: Optional[Mapping[str, Mapping[str, Any]]] = None
    corpus = search_vault._build_search_corpus(
        root,
        scopes=scopes,
        include_sources=include_sources,
        exclude_archived=exclude_archived,
        exclude_superseded=exclude_superseded,
        load_candidates=result_limit > 0,
    )
    records_by_path = corpus.records_by_path
    for anchor_number, anchor in enumerate(search_anchors):
        report = search_vault._search_corpus(
            corpus,
            anchor,
            limit=result_limit,
            vertical=None,
            scopes=scopes,
            contextual=contextual,
            include_derived=include_derived,
            expand_linked_sources=False,
            include_identity=True,
            compatibility=runtime,
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
        corpus=corpus,
    )
    replacements, unresolved = vault_utils.follow_explicit_replacements(
        matches,
        root=root,
        records_by_path=records_by_path,
        scopes=scopes,
        depth_limit=replacement_depth_limit,
        related_limit=related_replacement_limit,
    )
    related_replacements = [
        _compact_related_replacement(item) for item in replacements
    ]
    unresolved_replacements = [
        _compact_unresolved_replacement(item) for item in unresolved
    ]
    packet["matches"] = matches
    packet["linked_sources"] = linked_sources
    packet["related_replacements"] = related_replacements
    packet["unresolved_replacements"] = unresolved_replacements
    if include_evidence:
        packet["evidence"], packet["evidence_omitted"] = _select_complete_evidence(
            matches,
            root=root,
            records_by_path=records_by_path,
            page_limit=evidence_page_limit,
            byte_limit=evidence_byte_limit,
            related=related_replacements,
            replacement_depth_limit=replacement_depth_limit,
        )
    return finish(packet)


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
    parser.add_argument("--packet-byte-limit", type=_non_negative_int, default=DEFAULT_PACKET_BYTE_LIMIT,
                        help="maximum compact UTF-8 JSON packet bytes (minimum 1024; default 32768)")
    parser.add_argument(
        "--for-update", action="store_true",
        help="capture and check a read-time snapshot for an ordinary mutation proposal",
    )
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument("--include-derived", action="store_true")
    parser.add_argument("--exclude-archived", action="store_true")
    parser.add_argument("--exclude-superseded", action="store_true")
    parser.add_argument(
        "--include-evidence",
        action="store_true",
        help="include complete original contents for a bounded set of ranked canonical pages",
    )
    parser.add_argument(
        "--evidence-page-limit",
        type=_non_negative_int,
        default=DEFAULT_EVIDENCE_PAGE_LIMIT,
        help="maximum complete pages in the evidence section (default: 3)",
    )
    parser.add_argument(
        "--evidence-byte-limit",
        type=_non_negative_int,
        default=DEFAULT_EVIDENCE_BYTE_LIMIT,
        help=(
            "maximum UTF-8 bytes for the serialized evidence section, including "
            "metadata; not a token limit or a cap on the rest of the packet "
            f"(default: {DEFAULT_EVIDENCE_BYTE_LIMIT})"
        ),
    )
    parser.add_argument(
        "--replacement-depth-limit",
        type=_non_negative_int,
        default=DEFAULT_REPLACEMENT_DEPTH_LIMIT,
        help=(
            "maximum explicit superseded_by edges to follow from selected "
            f"superseded matches (default: {DEFAULT_REPLACEMENT_DEPTH_LIMIT})"
        ),
    )
    parser.add_argument(
        "--related-replacement-limit",
        type=_non_negative_int,
        default=DEFAULT_RELATED_REPLACEMENT_LIMIT,
        help=(
            "maximum related replacement pages to include besides ranked "
            f"matches (default: {DEFAULT_RELATED_REPLACEMENT_LIMIT})"
        ),
    )
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)
    if args.packet_byte_limit < 1024:
        parser.error("--packet-byte-limit must be at least 1024")

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
        include_evidence=args.include_evidence,
        evidence_page_limit=args.evidence_page_limit,
        evidence_byte_limit=args.evidence_byte_limit,
        replacement_depth_limit=args.replacement_depth_limit,
        related_replacement_limit=args.related_replacement_limit,
        for_update=args.for_update,
        packet_byte_limit=args.packet_byte_limit,
    )
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
