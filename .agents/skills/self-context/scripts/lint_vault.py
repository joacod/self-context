#!/usr/bin/env python3
"""Deterministic ordinary and deep validation for a SelfContext vault.

Ordinary lint intentionally stays fast and backward-compatible.  Deep lint is
also deterministic, but adds inventory, catalog, reachability, contract, and
maintenance checks without judging whether a personal claim is true.
"""

from __future__ import annotations

import argparse
import datetime as date
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

try:
    import sync_indexes
    from vault_utils import (
        ALLOWED_ASSERTIONS,
        ALLOWED_STATUSES,
        ALLOWED_TYPES,
        REQUIRED_FIELDS,
        REQUIRED_NON_NULL_FIELDS,
        WRITING_ROLE_COMBINATIONS,
        as_list,
        body_hash,
        canonical_files,
        canonical_markdown_files,
        catalog_records,
        durable_page_records,
        infer_enabled_contracts,
        is_control_page,
        is_deep_report,
        is_external,
        is_noncanonical,
        iter_markdown_links,
        iter_symlinks,
        link_target,
        markdown_link_records,
        malformed_links,
        nearest_index,
        normalized_text,
        parse_frontmatter_text,
        parse_iso_date,
        parse_schema,
        relative_label,
        safe_read_text,
        snapshot_id,
        validate_vertical_catalog,
        load_vertical_catalog,
        runtime_compatibility,
        runtime_compatibility_finding,
    )
except ImportError:  # pragma: no cover - useful when imported as a package
    from . import sync_indexes  # type: ignore
    from .vault_utils import (  # type: ignore
        ALLOWED_ASSERTIONS,
        ALLOWED_STATUSES,
        ALLOWED_TYPES,
        REQUIRED_FIELDS,
        REQUIRED_NON_NULL_FIELDS,
        WRITING_ROLE_COMBINATIONS,
        as_list,
        body_hash,
        canonical_files,
        canonical_markdown_files,
        catalog_records,
        durable_page_records,
        infer_enabled_contracts,
        is_control_page,
        is_deep_report,
        is_external,
        is_noncanonical,
        iter_markdown_links,
        iter_symlinks,
        link_target,
        markdown_link_records,
        malformed_links,
        nearest_index,
        normalized_text,
        parse_frontmatter_text,
        parse_iso_date,
        parse_schema,
        relative_label,
        safe_read_text,
        snapshot_id,
        validate_vertical_catalog,
        load_vertical_catalog,
        runtime_compatibility,
        runtime_compatibility_finding,
    )

# Preserve the small helper API used by earlier callers and tests.
REQUIRED_ROOT_FILES = ("SCHEMA.md", "index.md", "log.md")
# Keep the historical public constant shape; the helper additionally excludes
# macOS .DS_Store files from canonical inventory.
NON_CANONICAL_DIRECTORIES = {".obsidian", "backups"}


def parse_frontmatter(path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    text, error = safe_read_text(path)
    if text is None:
        return None, [error or "unable to read file"]
    fields, errors, _ = parse_frontmatter_text(text)
    return fields, errors


def is_under_noncanonical_directory(path: Path, root: Path) -> bool:
    return is_noncanonical(path, root)


def is_non_durable_page(path: Path, root: Path) -> bool:
    return is_control_page(path, root)


def _finding(
    severity: str,
    classification: str,
    message: str,
    path: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "severity": severity,
        "classification": classification,
        "message": message,
    }
    if path:
        result["path"] = path
    result.update(extra)
    return result


def _legacy(finding: Dict[str, Any]) -> str:
    path = finding.get("path")
    message = str(finding.get("message", ""))
    return f"{path}: {message}" if path else message


def _read_error_classification(error: Optional[str]) -> str:
    return "utf8" if (error or "").startswith("UnicodeDecodeError") else "filesystem"


def _known_top_level_areas() -> Set[str]:
    known = {"core", "review", "sources", "derived"}
    try:
        known.update(
            str(record.get("vault_area"))
            for record in catalog_records(load_vertical_catalog())
            if record.get("vault_area")
        )
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return known


def _is_custom_top_level(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    if len(parts) == 1 and parts[0] in {"SCHEMA.md", "index.md", "log.md"}:
        return False
    return bool(parts) and parts[0] not in _known_top_level_areas() and parts[0] not in {".obsidian", "backups", ".DS_Store"}


def _schema_findings(root: Path) -> List[Dict[str, Any]]:
    schema = parse_schema(root)
    if schema.get("error"):
        error = str(schema["error"])
        return [_finding("error", _read_error_classification(error), error, "SCHEMA.md")]
    version = schema.get("version")
    if version is None:
        return [_finding("warning", "schema", "SCHEMA.md does not declare a parseable schema_version; activation state is ambiguous")]
    if version not in {(0, 1), (0, 2)}:
        return [
            _finding(
                "warning",
                "schema",
                f"SCHEMA.md declares unsupported schema_version: {schema.get('version_text')}; activation state is ambiguous",
                "SCHEMA.md",
            )
        ]
    return []


def _ordinary_findings(
    root: Path,
    today: date.date,
    *,
    allow_legacy_source: bool = False,
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if not root.exists():
        return [_finding("error", "vault", f"vault does not exist: {root}")]
    if not root.is_dir():
        return [_finding("error", "vault", f"vault path is not a directory: {root}")]

    for required in ("SCHEMA.md", "index.md", "log.md"):
        if not (root / required).is_file():
            findings.append(_finding("error", "control-file", f"missing required root file: {required}"))
    findings.extend(_schema_findings(root))
    if not allow_legacy_source:
        compatibility = runtime_compatibility(root)
        if not compatibility.get("ok"):
            findings.append(runtime_compatibility_finding(compatibility))

    # The ordinary path remains a structural pass over canonical Markdown.  It
    # now catches read failures as findings rather than allowing a traceback.
    titles: Dict[str, Path] = {}
    ids: Dict[str, Path] = {}
    markdown_files = canonical_markdown_files(root)
    for path in markdown_files:
        relative = relative_label(path, root)
        if is_under_noncanonical_directory(path, root):
            continue
        text, error = safe_read_text(path)
        if text is None:
            findings.append(
                _finding(
                    "error",
                    _read_error_classification(error),
                    error or "unable to read file",
                    relative,
                )
            )
            continue

        if "[[" in text:
            findings.append(
                _finding("error", "links", "canonical Markdown must not contain wikilinks", relative)
            )
        for destination in iter_markdown_links(text):
            if is_external(destination) or not destination:
                continue
            try:
                target = link_target(path, destination, root)
            except (OSError, RuntimeError, ValueError):
                findings.append(
                    _finding("error", "links", f"unsafe link target: {destination}", relative)
                )
                continue
            if target is None:
                continue
            try:
                target.relative_to(root.resolve())
            except (OSError, RuntimeError, ValueError):
                findings.append(
                    _finding("error", "links", f"link leaves vault: {destination}", relative)
                )
                continue
            try:
                exists = target.is_file()
            except (OSError, RuntimeError, ValueError):
                findings.append(
                    _finding("error", "links", f"unsafe link target: {destination}", relative)
                )
                continue
            if not exists:
                findings.append(
                    _finding("error", "links", f"broken link: {destination}", relative)
                )

        if is_control_page(path, root) or _is_custom_top_level(path, root):
            # Custom top-level areas retain their own portable taxonomy. Keep
            # universal link safety above, but do not require SelfContext page
            # frontmatter or managed metadata for content the migration must
            # preserve rather than reinterpret.
            continue
        fields, frontmatter_errors, _ = parse_frontmatter_text(text)
        for problem in frontmatter_errors:
            findings.append(_finding("error", "frontmatter", problem, relative))
        if fields is None:
            continue
        for field in REQUIRED_FIELDS:
            if field not in fields or (
                field in REQUIRED_NON_NULL_FIELDS and (fields.get(field) is None or fields.get(field) == "")
            ):
                findings.append(_finding("error", "frontmatter", f"missing required field: {field}", relative))

        page_type = fields.get("type")
        status = fields.get("status")
        assertion = fields.get("assertion_kind")
        if not isinstance(page_type, str) or page_type not in ALLOWED_TYPES:
            findings.append(_finding("error", "metadata", f"invalid type: {page_type!r}", relative))
        if not isinstance(status, str) or status not in ALLOWED_STATUSES:
            findings.append(_finding("error", "metadata", f"invalid status: {status!r}", relative))
        if not isinstance(assertion, str) or assertion not in ALLOWED_ASSERTIONS:
            findings.append(_finding("error", "metadata", f"invalid assertion_kind: {assertion!r}", relative))

        tags = fields.get("tags")
        if isinstance(page_type, str) and page_type in {"source", "synthesis"} and isinstance(tags, list) and "writing" in tags:
            role_fields = (
                fields.get("writing_evidence_role"),
                fields.get("authorship"),
                fields.get("ai_involvement"),
            )
            if any(not isinstance(value, str) or value in {"", "null"} for value in role_fields):
                findings.append(
                    _finding(
                        "error",
                        "writing-artifact",
                        "writing source/artifact requires writing_evidence_role, authorship, and ai_involvement",
                        relative,
                    )
                )
            elif role_fields not in WRITING_ROLE_COMBINATIONS:
                findings.append(
                    _finding(
                        "error",
                        "writing-artifact",
                        f"invalid Writing artifact role combination: {role_fields!r}",
                        relative,
                    )
                )

        title = fields.get("title")
        if isinstance(title, str) and title.strip():
            key = normalized_text(title)
            if key in titles:
                findings.append(
                    _finding(
                        "warning",
                        "duplicate-title",
                        f"duplicate title also used by {relative_label(titles[key], root)}",
                        relative,
                    )
                )
            else:
                titles[key] = path

        page_id = fields.get("id")
        if isinstance(page_id, str) and page_id.strip():
            if page_id in ids:
                findings.append(
                    _finding(
                        "error",
                        "duplicate-id",
                        f"duplicate id also used by {relative_label(ids[page_id], root)}",
                        relative,
                    )
                )
            else:
                ids[page_id] = path

        for field in ("generated", "verified", "observed", "reviewed", "updated", "stale_after"):
            value = fields.get(field)
            if value not in (None, "", "null") and parse_iso_date(value) is None:
                findings.append(_finding("error", "metadata", f"{field} is not an ISO date or datetime", relative))
        stale_after = fields.get("stale_after")
        if stale_after not in (None, "", "null"):
            stale_date = parse_iso_date(stale_after)
            if stale_date is None:
                findings.append(_finding("error", "metadata", "stale_after is not an ISO date", relative))
            elif stale_date < today:
                findings.append(
                    _finding("warning", "freshness", f"stale_after has passed ({stale_after})", relative)
                )

        if (
            (assertion == "agent_inference" or page_type == "observation")
            and (not isinstance(status, str) or status not in {"archived", "superseded"})
        ):
            if fields.get("verified") in (None, "", "null"):
                findings.append(_finding("warning", "review", "observation or inference is unverified", relative))
            if status != "review":
                findings.append(
                    _finding("warning", "review", "observation or inference should normally have status: review", relative)
                )

        if "title" in fields and not isinstance(fields.get("title"), str):
            findings.append(_finding("error", "metadata", "title must be a YAML string", relative))
        if "description" in fields and not isinstance(fields.get("description"), str):
            findings.append(_finding("error", "metadata", "description must be a YAML string", relative))
        if "tags" in fields and not isinstance(fields.get("tags"), list):
            findings.append(_finding("error", "metadata", "tags must be a YAML list (use [] when empty)", relative))
        elif isinstance(fields.get("tags"), list) and any(
            not isinstance(tag, str) or not tag.strip() for tag in fields["tags"]
        ):
            findings.append(_finding("error", "metadata", "tags must contain only non-empty strings", relative))

        if "sources" in fields and not isinstance(fields.get("sources"), list):
            findings.append(_finding("error", "metadata", "sources must be a YAML list (use [] when empty)", relative))
        elif isinstance(fields.get("sources"), list) and any(
            not isinstance(source, str) or not source.strip() for source in fields["sources"]
        ):
            findings.append(_finding("error", "metadata", "sources must contain only non-empty strings", relative))

        sources = as_list(fields.get("sources"))
        if isinstance(assertion, str) and assertion in {"source_derived_fact", "derived_synthesis"} and not sources:
            findings.append(_finding("warning", "provenance", f"{assertion} has no sources", relative))
        for source in sources:
            if not isinstance(source, str) or is_external(source):
                continue
            try:
                source_target = link_target(path, source, root)
            except (OSError, RuntimeError, ValueError):
                findings.append(_finding("error", "provenance", f"unsafe source reference: {source}", relative))
                continue
            if source_target is None:
                continue
            try:
                source_target.relative_to(root.resolve())
            except (OSError, RuntimeError, ValueError):
                findings.append(_finding("error", "provenance", f"source reference leaves vault: {source}", relative))
                continue
            try:
                exists = source_target.is_file()
            except (OSError, RuntimeError, ValueError):
                findings.append(_finding("error", "provenance", f"unsafe source reference: {source}", relative))
                continue
            if not exists:
                findings.append(_finding("error", "provenance", f"missing source reference: {source}", relative))

    root_index = root / "index.md"
    root_text, root_error = safe_read_text(root_index)
    if root_error:
        findings.append(_finding("error", _read_error_classification(root_error), root_error, "index.md"))
    root_text = root_text or ""
    for expected in (
        "SCHEMA.md",
        "core/index.md",
        "review/index.md",
        "sources/index.md",
        "derived/index.md",
        "log.md",
    ):
        if expected not in root_text:
            findings.append(_finding("warning", "navigation", f"index.md does not mention {expected}"))
    try:
        catalog = load_vertical_catalog()
        for record in catalog_records(catalog):
            area = record.get("vault_area")
            expected = record.get("index_path")
            if isinstance(area, str) and isinstance(expected, str) and (root / area).is_dir():
                if expected not in root_text:
                    findings.append(_finding("warning", "navigation", f"index.md does not mention {expected}"))
    except (OSError, ValueError, json.JSONDecodeError):
        # Repository catalog consistency is a deep/repository check; ordinary
        # lint stays usable if the operational catalog is unavailable.
        pass
    return findings


def lint_vault(
    root: Path,
    today: date.date,
    *,
    allow_legacy_source: bool = False,
) -> Tuple[List[str], List[str]]:
    """Validate a current vault, or explicitly validate a migration source."""

    findings = _ordinary_findings(
        root.expanduser(), today, allow_legacy_source=allow_legacy_source
    )
    errors = [_legacy(item) for item in findings if item["severity"] == "error"]
    warnings = [_legacy(item) for item in findings if item["severity"] == "warning"]
    return errors, warnings


def _record_path(record: Dict[str, Any]) -> str:
    return str(record.get("path", ""))


_PAGE_DATE_FIELDS = ("generated", "verified", "observed", "reviewed", "updated", "stale_after")


def _owning_vertical(path: str, catalog: Dict[str, Any]) -> Optional[str]:
    parts = Path(path).parts
    if not parts:
        return None
    area = parts[0]
    for record in catalog_records(catalog):
        if isinstance(record, dict) and record.get("vault_area") == area:
            identifier = record.get("id")
            return str(identifier) if identifier is not None else None
    # core, review, sources, and derived are shared areas rather than verticals.
    return None


def _valid_date_metadata(value: Any) -> bool:
    return value is None or parse_iso_date(value) is not None


def _valid_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def _target_kind(record: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(record, dict):
        return None
    fields = record.get("frontmatter")
    if not isinstance(fields, dict):
        return None
    page_type = fields.get("type")
    assertion = fields.get("assertion_kind")
    if page_type == "source" or assertion == "source_record":
        return "source"
    if page_type == "synthesis" or assertion == "derived_synthesis":
        return "derived"
    return page_type if isinstance(page_type, str) and page_type in ALLOWED_TYPES else None


def _source_relationships(
    record: Dict[str, Any],
    root: Path,
    records_by_path: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    fields = record.get("frontmatter")
    if not isinstance(fields, dict) or not isinstance(fields.get("sources"), list):
        return []

    source_page = root / str(record["path"])
    relationships: List[Dict[str, Any]] = []
    for source in fields["sources"]:
        if not isinstance(source, str) or not source.strip():
            continue
        original = source.strip()
        external = is_external(original)
        relationship: Dict[str, Any] = {
            "original": original,
            "normalized_target": original if external else None,
            "internal": not external,
            "external": external,
            "exists": None if external else False,
            "target_kind": None,
        }
        if external:
            relationships.append(relationship)
            continue

        try:
            target = link_target(source_page, original, root)
        except (OSError, RuntimeError, ValueError):
            target = None
        if target is None:
            relationships.append(relationship)
            continue
        try:
            target.relative_to(root.resolve())
        except (OSError, RuntimeError, ValueError):
            # Do not expose absolute paths from malformed/out-of-vault links.
            relationships.append(relationship)
            continue

        try:
            normalized_target = relative_label(target, root)
        except (OSError, RuntimeError, ValueError):
            relationships.append(relationship)
            continue
        relationship["normalized_target"] = normalized_target
        try:
            relationship["exists"] = target.is_file()
        except (OSError, RuntimeError, ValueError):
            relationship["exists"] = False
        relationship["target_kind"] = _target_kind(records_by_path.get(normalized_target))
        relationships.append(relationship)
    return relationships


def _target_label(source: Path, destination: str, root: Path) -> Optional[str]:
    if is_external(destination):
        return None
    try:
        target = link_target(source, destination, root)
    except (OSError, RuntimeError, ValueError):
        return None
    if target is None:
        return None
    try:
        return relative_label(target, root)
    except (OSError, RuntimeError, ValueError):
        return str(target)


def _managed_target_labels(index: Path, text: str, root: Path) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    for entry in sync_indexes.managed_entries(text):
        target = _target_label(index, entry["path"], root)
        if target is not None:
            labels[target] = entry["path"]
    return labels


def _contract_map(catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(record.get("id")): record
        for record in catalog_records(catalog)
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }


def _contract_strings(contracts: Iterable[Dict[str, Any]]) -> List[str]:
    return [
        str(item.get("raw"))
        if item.get("raw") is not None
        else f"{item.get('id')}@{item.get('version')}"
        for item in contracts
    ]


def _path_compatibility(record: Dict[str, Any], root: Path) -> List[Dict[str, Any]]:
    path = str(record.get("path", ""))
    fields = record.get("frontmatter")
    if not isinstance(fields, dict):
        return []
    page_type = fields.get("type")
    assertion = fields.get("assertion_kind")
    parts = Path(path).parts
    findings: List[Dict[str, Any]] = []
    if page_type == "source" and assertion != "source_record":
        findings.append(_finding("error", "type-assertion-compatibility", "source pages must use assertion_kind: source_record", path))
    if assertion == "source_record" and page_type != "source":
        findings.append(_finding("error", "type-assertion-compatibility", "source_record pages must have type: source", path))
    if page_type == "synthesis" and assertion != "derived_synthesis":
        findings.append(_finding("error", "type-assertion-compatibility", "synthesis pages must use assertion_kind: derived_synthesis", path))
    if assertion == "derived_synthesis" and page_type != "synthesis":
        findings.append(_finding("error", "type-assertion-compatibility", "derived_synthesis pages must have type: synthesis", path))
    if parts and parts[0] == "sources" and page_type != "source":
        findings.append(_finding("error", "path-compatibility", "pages under sources/ must have type: source", path))
    if parts and parts[0] == "derived" and page_type != "synthesis":
        findings.append(_finding("error", "path-compatibility", "pages under derived/ must have type: synthesis", path))
    if len(parts) >= 2 and parts[0] == "review" and parts[1] == "observations":
        if page_type != "observation" or not isinstance(assertion, str) or assertion not in {"agent_inference", "mixed"}:
            findings.append(_finding("error", "path-compatibility", "review observations must be observation pages with an inference-compatible assertion kind", path))
    if assertion == "agent_inference" and (
        not isinstance(fields.get("status"), str)
        or fields.get("status") not in {"review", "archived", "superseded"}
    ):
        findings.append(_finding("error", "review-lifecycle", "active agent inferences must remain inside the review lifecycle", path))
    return findings


def _supersession_findings(record: Dict[str, Any], root: Path, records_by_path: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    fields = record.get("frontmatter")
    if not isinstance(fields, dict):
        return []
    path = root / str(record["path"])
    status = fields.get("status")
    successor = fields.get("superseded_by")
    findings: List[Dict[str, Any]] = []
    if successor not in (None, "", "null") and not isinstance(successor, str):
        findings.append(_finding("error", "supersession", "superseded_by must be a relative Markdown link", record["path"]))
        return findings
    if status == "superseded":
        if not isinstance(successor, str) or not successor.strip():
            findings.append(_finding("warning", "supersession", "status: superseded needs a valid superseded_by link", record["path"]))
            return findings
    if isinstance(successor, str) and successor.strip():
        try:
            target = link_target(path, successor, root)
        except (OSError, RuntimeError, ValueError):
            target = None
        valid = target is not None and target.suffix.lower() == ".md"
        if valid:
            try:
                target_label = relative_label(target, root)
                valid = target_label in records_by_path and target_label != record["path"]
            except (OSError, RuntimeError, ValueError):
                valid = False
        if not valid:
            findings.append(_finding("warning", "supersession", f"invalid superseded_by link: {successor}", record["path"]))
    return findings


def _generated_or_updated_date(fields: Dict[str, Any]) -> Optional[date.date]:
    values = [
        parsed
        for key in ("generated", "updated")
        if (parsed := parse_iso_date(fields.get(key))) is not None
    ]
    return max(values) if values else None


def _source_graph_findings(records: List[Dict[str, Any]], root: Path) -> List[Dict[str, Any]]:
    records_by_path = {str(record["path"]): record for record in records}
    graph: Dict[str, List[str]] = defaultdict(list)
    findings: List[Dict[str, Any]] = []
    for record in records:
        fields = record.get("frontmatter")
        if not isinstance(fields, dict):
            continue
        source_page = root / str(record["path"])
        for source in as_list(fields.get("sources")):
            if not isinstance(source, str) or is_external(source):
                continue
            try:
                target = link_target(source_page, source, root)
            except (OSError, RuntimeError, ValueError):
                continue
            if target is None:
                continue
            try:
                label = relative_label(target, root)
            except (OSError, RuntimeError, ValueError):
                continue
            if label in records_by_path:
                graph[str(record["path"])].append(label)

    state: Dict[str, int] = {}
    stack: List[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for target in graph.get(node, []):
            if state.get(target, 0) == 0:
                visit(target)
            elif state.get(target) == 1:
                cycle = " -> ".join(stack[stack.index(target) :] + [target])
                findings.append(_finding("error", "source-cycle", f"source-reference cycle: {cycle}", node))
        stack.pop()
        state[node] = 2

    for node in sorted(records_by_path):
        if state.get(node, 0) == 0:
            visit(node)

    for record in records:
        fields = record.get("frontmatter")
        if not isinstance(fields, dict) or fields.get("assertion_kind") != "derived_synthesis":
            continue
        path = str(record["path"])
        targets = graph.get(path, [])
        if targets and all(
            records_by_path.get(target, {}).get("frontmatter", {}).get("assertion_kind") == "derived_synthesis"
            or records_by_path.get(target, {}).get("frontmatter", {}).get("type") == "synthesis"
            for target in targets
        ):
            findings.append(_finding("error", "derived-source-chain", "derived synthesis is supported only by other derived syntheses", path))
        own_date = _generated_or_updated_date(fields)
        if own_date is None:
            continue
        for target in targets:
            source_fields = records_by_path.get(target, {}).get("frontmatter")
            if not isinstance(source_fields, dict):
                continue
            source_date = _generated_or_updated_date(source_fields)
            if source_date and source_date > own_date:
                findings.append(
                    _finding(
                        "warning",
                        "derived-freshness",
                        "Linked source has a newer generated or updated timestamp than this derived synthesis. Review whether regeneration is needed.",
                        path,
                        source_path=target,
                    )
                )
    return findings


def _deep_findings(
    root: Path,
    today: date.date,
    *,
    allow_legacy_source: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    root = root.expanduser()
    ordinary_findings = _ordinary_findings(
        root, today, allow_legacy_source=allow_legacy_source
    )
    # Unknown custom top-level areas are informational in deep lint. Preserve
    # ordinary findings for the known canonical contract, but do not validate a
    # user's custom taxonomy as if it were SelfContext-managed content.
    findings = [
        item for item in ordinary_findings
        if not (item.get("path") and _is_custom_top_level(root / str(item["path"]), root))
    ]
    reported_read_paths = {
        str(item["path"])
        for item in findings
        if item.get("classification") in {"utf8", "filesystem"} and item.get("path")
    }
    if not root.exists() or not root.is_dir():
        return findings, {
            "schema_version": None,
            "enabled_vertical_contracts": [],
            "available_vertical_contracts": [],
            "enabled_verticals": [],
            "applied_vertical_contracts": [],
            "legacy_inferred_verticals": [],
            "enabled_contract_source": "none",
            "snapshot_id": "",
            "pages": [],
            "links": [],
            "index_relationships": [],
            "runtime_compatibility": runtime_compatibility(root),
        }

    if root.is_symlink():
        findings.append(_finding("error", "symlink", "vault path itself is a symlink", str(root)))
    for path in iter_symlinks(root):
        findings.append(_finding("error", "symlink", "symlink found in vault content", relative_label(path, root)))
    for path in iter_symlinks(root, include_noncanonical=True):
        if is_noncanonical(path, root):
            findings.append(_finding("info", "noncanonical-state", "noncanonical symlink remains excluded from canonical state", relative_label(path, root)))

    # Read every canonical file as UTF-8 in deep mode, including custom
    # areas. The snapshot itself is byte-hash based so a malformed file still
    # receives a deterministic ID. Ordinary findings already cover managed
    # files, so avoid emitting the same read finding twice.
    for path in canonical_files(root):
        relative = relative_label(path, root)
        _, error = safe_read_text(path)
        if error and relative not in reported_read_paths:
            findings.append(_finding("error", _read_error_classification(error), error, relative))

    try:
        catalog = load_vertical_catalog()
        for problem in validate_vertical_catalog():
            findings.append(_finding("error", "vertical-catalog", problem, "references/verticals.json"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        catalog = {"verticals": []}
        findings.append(_finding("error", "vertical-catalog", f"vertical catalog cannot be loaded: {error}"))

    all_records = durable_page_records(root)
    custom_records = [record for record in all_records if _is_custom_top_level(root / str(record["path"]), root)]
    for record in custom_records:
        findings.append(_finding("info", "custom-area", "unrecognized custom top-level area preserved", str(record["path"])))
    records = [record for record in all_records if record not in custom_records]
    records_by_path = {str(record["path"]): record for record in records}
    page_metadata: List[Dict[str, Any]] = []
    for record in records:
        path = str(record["path"])
        fields = record.get("frontmatter")
        page_metadata_item: Dict[str, Any] = {
            "path": path,
            "content_hash": record.get("content_hash"),
            "owner_index": None,
            "vertical": _owning_vertical(path, catalog),
            "outbound_links": [],
            "inbound_links": [],
            "sources": [],
            "source_relationships": [],
        }
        owner = nearest_index(root / path, root)
        if owner:
            page_metadata_item["owner_index"] = relative_label(owner, root)
        if isinstance(fields, dict):
            if isinstance(fields.get("id"), str) and fields["id"].strip():
                page_metadata_item["id"] = fields["id"]
            if isinstance(fields.get("type"), str) and fields["type"] in ALLOWED_TYPES:
                page_metadata_item["type"] = fields["type"]
            if isinstance(fields.get("title"), str) and fields["title"].strip():
                page_metadata_item["title"] = fields["title"]
            if isinstance(fields.get("description"), str) and fields["description"].strip():
                page_metadata_item["description"] = fields["description"]
            if isinstance(fields.get("status"), str) and fields["status"] in ALLOWED_STATUSES:
                page_metadata_item["status"] = fields["status"]
            if isinstance(fields.get("assertion_kind"), str) and fields["assertion_kind"] in ALLOWED_ASSERTIONS:
                page_metadata_item["assertion_kind"] = fields["assertion_kind"]
            if _valid_string_list(fields.get("aliases")):
                page_metadata_item["aliases"] = fields["aliases"]
            if _valid_string_list(fields.get("tags")):
                page_metadata_item["tags"] = fields["tags"]
            if _valid_string_list(fields.get("sources")):
                page_metadata_item["sources"] = fields["sources"]
            if isinstance(fields.get("superseded_by"), str) and fields["superseded_by"].strip():
                page_metadata_item["superseded_by"] = fields["superseded_by"]
            for key in _PAGE_DATE_FIELDS:
                if key in fields and _valid_date_metadata(fields[key]):
                    page_metadata_item[key] = fields[key]
            page_metadata_item["source_relationships"] = _source_relationships(
                record, root, records_by_path
            )
        page_metadata.append(page_metadata_item)
        findings.extend(_path_compatibility(record, root))
        findings.extend(_supersession_findings(record, root, records_by_path))
        aliases = fields.get("aliases") if isinstance(fields, dict) else None
        if aliases not in (None, "", "null") and not isinstance(aliases, list):
            findings.append(_finding("error", "aliases", "aliases must be a YAML list", path))
        if isinstance(aliases, list):
            for alias in aliases:
                if not isinstance(alias, str) or not alias.strip():
                    findings.append(_finding("error", "aliases", "aliases must contain only non-empty strings", path))

    # Exact normalized title/alias collision detection and stable duplicate
    # content detection are intentionally warnings/errors, never truth judgments.
    names: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    contents: Dict[str, List[str]] = defaultdict(list)
    for record in records:
        fields = record.get("frontmatter")
        if not isinstance(fields, dict):
            continue
        path = str(record["path"])
        title = fields.get("title")
        if isinstance(title, str) and title.strip():
            names[normalized_text(title)].append((path, "title"))
        aliases = fields.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str) and alias.strip():
                    names[normalized_text(alias)].append((path, "alias"))
        digest = body_hash(record)
        if digest:
            contents[digest].append(path)
    for name, uses in sorted(names.items()):
        paths = sorted({path for path, _ in uses})
        if len(uses) > 1:
            findings.append(_finding("error", "title-alias-collision", f"exact normalized title/alias collision: {name} ({', '.join(paths)})"))
    for digest, paths in sorted(contents.items()):
        if len(paths) > 1:
            findings.append(_finding("warning", "duplicate-content", f"exact duplicate durable-page content: {', '.join(sorted(paths))}"))

    findings.extend(_source_graph_findings(records, root))

    # Link and index relationships are kept as metadata only.  They are also
    # used to determine root reachability and weak contextual connectivity.
    link_relationships: List[Dict[str, Any]] = []
    by_source: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    canonical_markdown_paths = canonical_markdown_files(root)
    canonical_labels = {
        relative_label(path, root)
        for path in canonical_markdown_paths
    }
    managed_labels = {
        relative_label(path, root)
        for path in canonical_markdown_paths
        if not _is_custom_top_level(path, root)
    }
    managed_index_labels = {
        relative_label(path, root)
        for path in canonical_markdown_paths
        if path.name == "index.md" and not _is_custom_top_level(path, root)
    }
    for path in canonical_markdown_paths:
        text, error = safe_read_text(path)
        if error or text is None:
            continue
        for link in markdown_link_records(path, root, text):
            link_relationships.append(link)
            by_source[link["source"]].append(link)
            if link.get("resolution_error"):
                findings.append(_finding("error", "links", f"unsafe link target: {link['destination']}", link["source"]))
            elif link.get("leaves_vault"):
                findings.append(_finding("error", "links", f"link leaves vault: {link['destination']}", link["source"]))
            elif not link.get("external") and not link.get("exists"):
                findings.append(_finding("error", "links", f"broken link: {link['destination']}", link["source"]))

    # Page-local direction is a compact navigation aid.  Frontmatter sources
    # stay separate in source_relationships so ordinary body links are never
    # promoted to provenance.
    metadata_by_path = {str(item["path"]): item for item in page_metadata}
    outbound_by_source: Dict[str, Set[str]] = defaultdict(set)
    inbound_by_target: Dict[str, Set[str]] = defaultdict(set)
    for link in link_relationships:
        if link.get("external") or link.get("leaves_vault") or link.get("resolution_error"):
            continue
        source = link.get("source")
        target = link.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        outbound_by_source[source].add(target)
        if target in canonical_labels:
            inbound_by_target[target].add(source)
    for path, item in metadata_by_path.items():
        item["outbound_links"] = sorted(outbound_by_source.get(path, set()))
        item["inbound_links"] = sorted(inbound_by_target.get(path, set()))

    # Stable ordering keeps JSON inventories comparable across repeated runs.
    link_relationships.sort(
        key=lambda item: (
            str(item.get("source", "")),
            str(item.get("target") or ""),
            str(item.get("destination", "")),
            str(item.get("kind", "")),
        )
    )

    root_index = root / "index.md"
    reachable: Set[str] = set()
    queue: deque[str] = deque()
    processed_indexes: Set[str] = set()
    scheduled_indexes: Set[str] = set()
    if root_index.is_file():
        root_label = relative_label(root_index, root)
        reachable.add(root_label)
        queue.append(root_label)
        scheduled_indexes.add(root_label)
    while queue:
        source_label = queue.popleft()
        if source_label in processed_indexes:
            continue
        # Mark before expanding links. A permanent processed set is required
        # for both cycles and duplicate links; queue membership alone is not a
        # traversal invariant.
        processed_indexes.add(source_label)
        for link in by_source.get(source_label, []):
            target = link.get("target")
            if not target or target not in canonical_labels:
                continue
            if target not in reachable:
                reachable.add(target)
            if (
                target in managed_index_labels
                and target not in processed_indexes
                and target not in scheduled_indexes
            ):
                queue.append(target)
                scheduled_indexes.add(target)
    for path in sorted(records_by_path):
        if path not in reachable:
            findings.append(_finding("error", "root-reachability", "durable page is not reachable from root index through index links", path))
    for index_path in sorted(managed_index_labels):
        if index_path not in reachable:
            findings.append(_finding("error", "root-reachability", "index is not reachable from root index", index_path))

    owner_entries: Dict[str, Dict[str, str]] = {}
    for index in canonical_markdown_paths:
        if index.name != "index.md":
            continue
        label = relative_label(index, root)
        if label not in managed_index_labels:
            continue
        text, error = safe_read_text(index)
        if text is None:
            continue
        owner_entries[label] = _managed_target_labels(index, text, root)
        for target_label in owner_entries[label]:
            owner_entries[label][target_label] = target_label
        for entry in sync_indexes.managed_entries(text):
            target = _target_label(index, entry["path"], root)
            if target is None or target not in managed_labels:
                findings.append(_finding("error", "dead-catalog-entry", f"dead catalog entry: {entry['path']}", label))

    sync_result = sync_indexes.synchronize(root, write=False)
    for item in sync_result.get("findings", []):
        classification = item.get("classification")
        if classification in {"catalog-sync", "catalog-missing"}:
            # Keep catalog-sync as the deep-lint compatibility umbrella while
            # retaining the more precise missing-block state from the sync
            # report. This lets callers distinguish absence from drift.
            finding = _finding(
                "error",
                "catalog-sync",
                item.get("message", "managed catalog block is out of sync"),
                item.get("path"),
                state=item.get("state"),
            )
            findings.append(finding)
            if classification == "catalog-missing":
                findings.append(
                    _finding(
                        "error",
                        "catalog-missing",
                        item.get("message", "managed catalog block is missing"),
                        item.get("path"),
                        state=item.get("state"),
                    )
                )
        elif item.get("severity") == "error":
            findings.append(
                _finding(
                    "error",
                    item.get("classification", "catalog"),
                    item.get("message", ""),
                    item.get("path"),
                    state=item.get("state"),
                )
            )

    for record in records:
        path = str(record["path"])
        owner = nearest_index(root / path, root)
        if owner is None:
            findings.append(_finding("error", "nearest-index-ownership", "durable page has no nearest ancestor index", path))
            continue
        owner_label = relative_label(owner, root)
        # Construct the relative path directly for the ownership check.
        import posixpath

        expected = posixpath.normpath(
            posixpath.relpath(path, start=Path(owner_label).parent.as_posix() or ".")
        )
        if path not in owner_entries.get(owner_label, {}) and expected not in owner_entries.get(owner_label, {}):
            findings.append(_finding("error", "nearest-index-ownership", "durable page is missing from its nearest owning managed catalog", path, owner_index=owner_label))

    contextual_inbound: Dict[str, Set[str]] = defaultdict(set)
    for link in link_relationships:
        if (
            link.get("kind") == "contextual"
            and link.get("source") in managed_labels
            and link.get("target") in records_by_path
        ):
            contextual_inbound[str(link["target"])].add(str(link["source"]))
    for path in sorted(records_by_path):
        if path in reachable and not contextual_inbound.get(path):
            findings.append(_finding("warning", "weak-connectivity", "page is reachable only through an index and has no contextual inbound links", path))

    # Enabled/applied contract checks are deliberately version-aware. Legacy
    # 0.1 vaults get an inferred report but no migration finding.
    schema = parse_schema(root)
    enabled, enabled_source = infer_enabled_contracts(root, catalog)
    records_by_id = _contract_map(catalog)

    if schema.get("version") == (0, 2):
        if not schema.get("contract_section_present"):
            findings.append(_finding("error", "vertical-contract", "schema 0.2 must declare a vertical_contracts section", "SCHEMA.md"))
        for error in schema.get("contract_errors", []):
            findings.append(_finding("error", "vertical-contract", str(error), "SCHEMA.md"))

    # Contract validity is keyed by vertical ID. A contract can be current,
    # older-but-readable, or future-and-unsafe; currency is not validity.
    # Schema 0.1 area inference is legacy structure, not an applied contract,
    # so version comparison is only performed for explicit schema 0.2 entries.
    seen_ids: Set[str] = set()
    valid_applied: List[Dict[str, Any]] = []
    contract_entries = schema.get("contract_entries", []) if schema.get("version") == (0, 2) else []
    contracts_to_check = contract_entries
    for contract in contracts_to_check:
        identifier = contract.get("id")
        version = contract.get("version")
        raw = str(contract.get("raw") or f"{identifier}@{version}")
        if not isinstance(identifier, str):
            continue
        if identifier in seen_ids:
            findings.append(_finding("error", "vertical-contract", f"duplicate applied vertical contract for {identifier}: {raw}", "SCHEMA.md"))
        seen_ids.add(identifier)

        record = records_by_id.get(identifier)
        if record is None:
            findings.append(_finding("error", "vertical-contract", f"applied vertical is not available: {raw}", "SCHEMA.md"))
            continue
        if not isinstance(version, int):
            continue
        valid_applied.append(contract)

        available_version = record.get("contract_version")
        if not isinstance(available_version, int):
            findings.append(_finding("error", "vertical-contract", f"available contract version is invalid for {identifier}: {available_version!r}", "references/verticals.json"))
            continue
        if version > available_version:
            findings.append(_finding("error", "vertical-contract", f"applied contract is newer than available version: {raw} (available {identifier}@{available_version})", "SCHEMA.md"))
        elif version < available_version:
            findings.append(_finding("warning", "vertical-contract-update", f"contract update available: {raw} -> {identifier}@{available_version}; no automatic migration performed", "SCHEMA.md"))

        area = str(record.get("vault_area"))
        index_path = str(record.get("index_path"))
        if not (root / area).is_dir():
            findings.append(_finding("error", "vertical-contract", f"enabled vertical is missing its area: {area}/", "SCHEMA.md"))
        if not (root / index_path).is_file():
            findings.append(_finding("error", "vertical-contract", f"enabled vertical is missing its index: {index_path}", "SCHEMA.md"))
        root_text, _ = safe_read_text(root / "index.md")
        if index_path not in (root_text or ""):
            findings.append(_finding("error", "vertical-contract", f"enabled vertical is missing its root index link: {index_path}", "index.md"))

    if schema.get("version") == (0, 2):
        explicit_ids = {str(item.get("id")) for item in valid_applied if item.get("id") is not None}
        for record in catalog_records(catalog):
            area = record.get("vault_area")
            if isinstance(area, str) and (root / area).is_dir() and str(record.get("id")) not in explicit_ids:
                findings.append(_finding("error", "vertical-contract", f"known vertical area is present but not versioned in schema 0.2: {area}/", "SCHEMA.md"))
    known_areas = {"core", "review", "sources", "derived"} | {
        str(record.get("vault_area")) for record in catalog_records(catalog)
    }
    if root.is_dir():
        try:
            children = sorted(root.iterdir(), key=lambda path: path.name)
        except OSError as error:
            children = []
            findings.append(
                _finding(
                    "error",
                    "filesystem",
                    f"{type(error).__name__}: unable to inspect vault root",
                )
            )
        for child in children:
            if child.is_dir() and child.name not in known_areas and child.name not in {".obsidian", "backups"}:
                findings.append(_finding("info", "custom-area", f"unrecognized custom top-level area preserved: {child.name}/", child.name + "/"))

    # Recent-log validation is intentionally conservative about content: only
    # malformed or broken links become findings, never log prose.
    log_text, log_error = safe_read_text(root / "log.md")
    if log_error:
        findings.append(_finding("error", _read_error_classification(log_error), log_error, "log.md"))
    elif log_text is not None:
        for malformed in malformed_links(log_text):
            findings.append(_finding("warning", "log-link", f"malformed Markdown link in recent log entry: {malformed}" , "log.md"))
        for destination in iter_markdown_links(log_text):
            if is_external(destination):
                continue
            try:
                target = link_target(root / "log.md", destination, root)
            except (OSError, RuntimeError, ValueError):
                findings.append(_finding("warning", "log-link", f"unsafe log link target: {destination}", "log.md"))
                continue
            if target is None:
                continue
            try:
                label = relative_label(target, root)
            except (OSError, RuntimeError, ValueError):
                findings.append(_finding("warning", "log-link", f"log link leaves vault: {destination}", "log.md"))
                continue
            try:
                exists = target.is_file()
            except (OSError, RuntimeError, ValueError):
                findings.append(_finding("warning", "log-link", f"unsafe log link target: {destination}", "log.md"))
                continue
            if not exists:
                findings.append(_finding("warning", "log-link", f"broken link in recent log entry: {destination}", "log.md"))

    root_text, _ = safe_read_text(root / "index.md")
    enabled_verticals: Set[str] = set()
    legacy_inferred_verticals: Set[str] = set()
    structural_entries = valid_applied if schema.get("version") == (0, 2) else []
    for contract in structural_entries:
        identifier = contract.get("id")
        if isinstance(identifier, str) and identifier in records_by_id:
            # The marker establishes the enabled ID; area/index/root checks
            # above independently report structural corruption.
            enabled_verticals.add(identifier)

    legacy_entries = enabled if enabled_source == "inferred-legacy" else []
    for contract in legacy_entries:
        identifier = contract.get("id")
        record = records_by_id.get(str(identifier))
        if not isinstance(record, dict):
            continue
        area = record.get("vault_area")
        index_path = record.get("index_path")
        if (
            isinstance(area, str)
            and isinstance(index_path, str)
            and (root / area).is_dir()
            and (root / index_path).is_file()
            and index_path in (root_text or "")
        ):
            legacy_inferred_verticals.add(str(identifier))

    available_contracts = [
        f"{record.get('id')}@{record.get('contract_version')}"
        for record in catalog_records(catalog)
        if isinstance(record, dict)
        and record.get("id") is not None
        and record.get("contract_version") is not None
    ]
    applied_contracts = (
        _contract_strings(contract_entries)
        if schema.get("version") == (0, 2)
        else []
    )
    metadata = {
        "schema_version": schema.get("version_text"),
        "runtime_compatibility": runtime_compatibility(root),
        # Retain the historical field as an alias for explicit applied
        # contracts; legacy schema 0.1 area inference is exposed separately.
        "enabled_vertical_contracts": applied_contracts,
        "available_vertical_contracts": available_contracts,
        "enabled_verticals": sorted(enabled_verticals),
        "applied_vertical_contracts": applied_contracts,
        "legacy_inferred_verticals": sorted(legacy_inferred_verticals),
        "enabled_contract_source": enabled_source,
        "snapshot_id": snapshot_id(root),
        "pages": page_metadata,
        "links": link_relationships,
        "index_relationships": [
            link for link in link_relationships if link.get("kind") == "index"
        ],
    }
    return findings, metadata


def deep_lint_vault(
    root: Path,
    today: date.date,
    *,
    allow_legacy_source: bool = False,
) -> Dict[str, Any]:
    findings, metadata = _deep_findings(
        root.expanduser(), today, allow_legacy_source=allow_legacy_source
    )
    counts = {"error": 0, "warning": 0, "info": 0}
    for item in findings:
        severity = item.get("severity")
        if severity in counts:
            counts[severity] += 1
    return {
        **metadata,
        "findings": findings,
        "severity_counts": counts,
    }


def _print_text_findings(findings: Iterable[Dict[str, Any]]) -> None:
    for item in findings:
        severity = str(item.get("severity", "info")).upper()
        path = item.get("path")
        message = item.get("message", "")
        print(f"{severity}: {path}: {message}" if path else f"{severity}: {message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a SelfContext vault")
    parser.add_argument("vault", nargs="?", default="vault", help="Path to the vault (default: ./vault)")
    parser.add_argument("--today", help="ISO date used for stale_after checks (default: today)")
    parser.add_argument("--deep", action="store_true", help="run deterministic deep maintenance lint")
    parser.add_argument(
        "--migration-source",
        action="store_true",
        help="validate a recognized historical vault as a migration source; do not treat it as current",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    today = date.date.today()
    if args.today:
        try:
            today = date.date.fromisoformat(args.today)
        except ValueError:
            print(f"ERROR: invalid --today date: {args.today}", file=sys.stderr)
            return 1

    if args.deep:
        report = deep_lint_vault(
            Path(args.vault), today, allow_legacy_source=args.migration_source
        )
        if args.format == "json":
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            _print_text_findings(report["findings"])
            counts = report["severity_counts"]
            print(
                "SelfContext deep lint: "
                f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['info']} info finding(s)"
            )
        return 1 if report["severity_counts"]["error"] else 0

    errors, warnings = lint_vault(
        Path(args.vault), today, allow_legacy_source=args.migration_source
    )
    if args.format == "json":
        report = {
            "schema_version": parse_schema(Path(args.vault)).get("version_text"),
            "errors": errors,
            "warnings": warnings,
            "severity_counts": {"error": len(errors), "warning": len(warnings), "info": 0},
        }
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for finding in errors:
            print(f"ERROR: {finding}")
        for finding in warnings:
            print(f"WARNING: {finding}")
        print(f"SelfContext lint: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
