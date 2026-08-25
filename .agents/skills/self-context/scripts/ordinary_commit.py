#!/usr/bin/env python3
"""Commit prepared ordinary mutations to an existing current SelfContext vault.

The caller owns semantic decisions and supplies a filesystem-oriented proposal.
This module owns proposal safety, current-runtime gating, staged control/index/
log planning, backup lifecycle, active replacement, validation, rollback, and a
compact structured receipt.  It deliberately does not initialize a vault or
route schema migration.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import stat
import sys
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import backup_vault
    import file_transaction
    import lint_vault
    import log_utils
    import sync_indexes
    import vault_utils
    from vault_controls import root_has_link, root_with_links, schema_with_contracts, vertical_index_template
except ImportError:  # pragma: no cover - useful when imported as a package
    from . import backup_vault, file_transaction, lint_vault, log_utils, sync_indexes, vault_utils  # type: ignore
    from .vault_controls import (  # type: ignore
        root_has_link,
        root_with_links,
        schema_with_contracts,
        vertical_index_template,
    )


CONTROL_PATHS = {"SCHEMA.md", "index.md", "log.md"}
UNIVERSAL_INDEXES = (
    "core/index.md",
    "review/index.md",
    "sources/index.md",
    "derived/index.md",
)
DELETION_FIELDS = {"delete", "deletes", "deletion", "deletions", "remove", "removes"}



def _finding(
    severity: str,
    path: str,
    message: str,
    classification: str,
    **extra: Any,
) -> Dict[str, Any]:
    finding: Dict[str, Any] = {
        "severity": severity,
        "path": path,
        "message": message,
        "classification": classification,
    }
    finding.update(extra)
    return finding



def _base_receipt(vault: Path) -> Dict[str, Any]:
    return {
        "status": "blocked",
        "state": "unknown",
        "vault": str(vault.expanduser()),
        "source_snapshot_id": "",
        "expected_snapshot_id": None,
        "proposed_snapshot_id": "",
        "final_snapshot_id": "",
        "changed": [],
        "created": [],
        "modified": [],
        "planned_changed": [],
        "planned_created": [],
        "planned_modified": [],
        "activations": [],
        "provisional_backup": None,
        "provisional_backup_removed": [],
        "removed_backups": [],
        "provisional_discarded": False,
        "final_backup": None,
        "validation": {
            "proposed": None,
            "active": None,
        },
        "rollback": {"status": "not-needed", "ok": True},
        "findings": [],
    }



def _canonical_bytes(root: Path) -> Dict[str, bytes]:
    result: Dict[str, bytes] = {}
    for path in vault_utils.canonical_files(root):
        content, error = vault_utils.safe_read_bytes(path)
        if content is None:
            raise OSError(error or f"unable to read {path}")
        result[vault_utils.relative_label(path, root)] = content
    return result



def _diff_bytes(
    original: Mapping[str, bytes], proposed: Mapping[str, bytes]
) -> Tuple[List[str], List[str], List[str]]:
    created = sorted(set(proposed) - set(original))
    deleted = sorted(set(original) - set(proposed))
    modified = sorted(
        label
        for label in set(original).intersection(proposed)
        if original[label] != proposed[label]
    )
    return created, modified, deleted



def _safe_snapshot(vault: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        return vault_utils.snapshot_id(vault), None
    except (OSError, RuntimeError, ValueError) as error:
        return None, str(error)



def _is_real_regular(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False



def _path_safety_finding(
    vault: Path,
    label: Any,
    *,
    for_write: bool,
) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
    """Validate one agent-supplied relative filesystem label."""

    if not isinstance(label, str):
        return None, _finding(
            "error", "", "path labels must be strings", "input-path"
        )
    if not label:
        return None, _finding(
            "error", label, "path label must not be empty", "input-path"
        )
    if "\x00" in label:
        return None, _finding(
            "error", label, "path label contains a NUL byte", "input-path"
        )
    if label != unicodedata.normalize("NFC", label):
        return None, _finding(
            "error", label, "path label is not NFC-normalized", "input-path"
        )
    if "\\" in label:
        return None, _finding(
            "error", label, "path label must use canonical POSIX separators", "input-path"
        )

    relative = PurePosixPath(label)
    if relative.is_absolute() or relative.as_posix() != label:
        return None, _finding(
            "error", label, "path label must be a canonical relative POSIX path", "input-path"
        )
    parts = relative.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return None, _finding(
            "error", label, "path label contains an unsafe traversal component", "input-path"
        )
    if any(part in vault_utils.NON_CANONICAL_DIRECTORIES for part in parts):
        return None, _finding(
            "error",
            label,
            "path targets excluded private or viewer state",
            "input-path",
        )
    if any(part.startswith(".") for part in parts):
        return None, _finding(
            "error", label, "hidden operational paths are not canonical mutation targets", "input-path"
        )
    if for_write and (label in CONTROL_PATHS or relative.name == "index.md"):
        return None, _finding(
            "error",
            label,
            "control and managed index files are code-owned; supply semantic files and explicit activations instead",
            "input-control-path",
        )

    try:
        resolved_vault = vault.resolve(strict=True)
        target = vault.joinpath(*parts)
        target.resolve(strict=False).relative_to(resolved_vault)
    except (OSError, RuntimeError, ValueError) as error:
        return None, _finding(
            "error", label, f"path resolves outside the vault or cannot be resolved: {error}", "input-path"
        )

    current = vault
    for part in parts[:-1]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as error:
            return None, _finding(
                "error", label, f"path parent cannot be inspected: {error}", "input-path"
            )
        if stat.S_ISLNK(mode):
            return None, _finding(
                "error", label, "path traverses a symlink", "input-symlink"
            )
        if not stat.S_ISDIR(mode):
            return None, _finding(
                "error", label, "path parent is not a regular directory", "input-path"
            )

    target = vault.joinpath(*parts)
    try:
        mode = target.lstat().st_mode
    except FileNotFoundError:
        return target, None
    except OSError as error:
        return None, _finding(
            "error", label, f"path target cannot be inspected: {error}", "input-path"
        )
    if stat.S_ISLNK(mode):
        return None, _finding(
            "error", label, "path targets a symlink", "input-symlink"
        )
    if not stat.S_ISREG(mode):
        return None, _finding(
            "error", label, "path target is not a regular file", "input-object"
        )
    return target, None



def _validate_log(
    vault: Path,
    raw_log: Any,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    findings: List[Dict[str, Any]] = []
    if not isinstance(raw_log, Mapping):
        return None, [
            _finding(
                "error", "log", "log metadata must be an object", "input-contract"
            )
        ]
    unknown = sorted(set(raw_log) - {"operation", "summary", "paths"})
    if unknown:
        findings.append(
            _finding(
                "error",
                "log",
                "unsupported log fields: " + ", ".join(str(item) for item in unknown),
                "input-contract",
            )
        )
    operation = raw_log.get("operation")
    summary = raw_log.get("summary")
    paths = raw_log.get("paths")
    if not isinstance(operation, str) or not log_utils.OPERATION_IDENTIFIER_PATTERN.fullmatch(operation):
        findings.append(
            _finding(
                "error",
                "log.operation",
                "operation must be a lowercase identifier using letters, numbers, '-' or '_'",
                "input-log",
            )
        )
    if not isinstance(summary, str) or not summary.strip() or any(
        character in summary for character in "\r\n"
    ):
        findings.append(
            _finding(
                "error",
                "log.summary",
                "summary must be a non-empty single-line string",
                "input-log",
            )
        )
    if not isinstance(paths, Sequence) or isinstance(paths, (str, bytes, bytearray)):
        findings.append(
            _finding(
                "error", "log.paths", "paths must be a sequence", "input-log"
            )
        )
        paths = []
    clean_paths: List[str] = []
    for label in paths:
        _, finding = _path_safety_finding(vault, label, for_write=False)
        if finding is not None:
            finding["path"] = f"log.paths: {finding.get('path', '')}".rstrip()
            findings.append(finding)
            continue
        clean_paths.append(str(label))
    if not clean_paths:
        findings.append(
            _finding(
                "error",
                "log.paths",
                "paths must contain at least one affected label",
                "input-log",
            )
        )
    if findings:
        return None, findings
    return {
        "operation": str(operation),
        "summary": str(summary).strip(),
        "paths": sorted(set(clean_paths)),
    }, findings



def _validate_proposal(
    vault: Path,
    proposal: Any,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    findings: List[Dict[str, Any]] = []
    if not isinstance(proposal, Mapping):
        return None, [
            _finding(
                "error", "proposal", "commit proposal must be an object", "input-contract"
            )
        ]

    unknown = sorted(set(proposal) - {"expected_snapshot", "writes", "activations", "log"} - DELETION_FIELDS)
    if unknown:
        findings.append(
            _finding(
                "error",
                "proposal",
                "unsupported proposal fields: " + ", ".join(str(item) for item in unknown),
                "input-contract",
            )
        )
    deletion_fields = sorted(set(proposal).intersection(DELETION_FIELDS))
    if deletion_fields:
        findings.append(
            _finding(
                "error",
                ",".join(deletion_fields),
                "arbitrary deletion is unsupported by the ordinary commit boundary",
                "unsupported-deletion",
            )
        )

    expected_snapshot = proposal.get("expected_snapshot")
    if expected_snapshot is not None and (
        not isinstance(expected_snapshot, str) or not expected_snapshot
    ):
        findings.append(
            _finding(
                "error",
                "expected_snapshot",
                "expected_snapshot must be a non-empty snapshot identifier when supplied",
                "input-contract",
            )
        )

    raw_writes = proposal.get("writes", {})
    if not isinstance(raw_writes, Mapping):
        findings.append(
            _finding(
                "error", "writes", "writes must be an object mapping labels to bytes or text", "input-contract"
            )
        )
        raw_writes = {}
    writes: Dict[str, bytes] = {}
    for label, content in raw_writes.items():
        _, finding = _path_safety_finding(vault, label, for_write=True)
        if finding is not None:
            findings.append(finding)
            continue
        if PurePosixPath(label).suffix != ".md":
            findings.append(
                _finding(
                    "error",
                    label,
                    "ordinary semantic writes must target Markdown files with a .md extension",
                    "input-file-type",
                )
            )
            continue
        if content is None:
            findings.append(
                _finding(
                    "error",
                    str(label),
                    "delete/remove proposals are unsupported; do not model deletion as a null write",
                    "unsupported-deletion",
                )
            )
            continue
        if isinstance(content, str):
            writes[str(label)] = content.encode("utf-8")
        elif isinstance(content, (bytes, bytearray)):
            writes[str(label)] = bytes(content)
        else:
            findings.append(
                _finding(
                    "error",
                    str(label),
                    "write content must be UTF-8 text or bytes",
                    "input-content",
                )
            )

    raw_activations = proposal.get("activations", [])
    if not isinstance(raw_activations, Sequence) or isinstance(
        raw_activations, (str, bytes, bytearray)
    ):
        findings.append(
            _finding(
                "error", "activations", "activations must be a list of catalog vertical IDs", "input-contract"
            )
        )
        raw_activations = []
    activations: List[str] = []
    for identifier in raw_activations:
        if not isinstance(identifier, str) or not identifier:
            findings.append(
                _finding(
                    "error", "activations", "activation IDs must be non-empty strings", "input-activation"
                )
            )
            continue
        if identifier in activations:
            findings.append(
                _finding(
                    "error", identifier, "activation IDs must not be duplicated", "input-activation"
                )
            )
            continue
        activations.append(identifier)

    raw_log = proposal.get("log")
    log, log_findings = _validate_log(vault, raw_log) if raw_log is not None else (None, [])
    findings.extend(log_findings)

    if findings:
        return None, findings
    return {
        "expected_snapshot": expected_snapshot,
        "writes": writes,
        "activations": sorted(activations),
        "log": log,
    }, findings



def _initialization_finding(vault: Path) -> Optional[Dict[str, Any]]:
    if not vault.exists():
        return _finding(
            "error",
            str(vault),
            "ordinary commit does not initialize a missing vault; use the existing initialization procedure",
            "initialization-required",
        )
    if vault.is_symlink() or not vault.is_dir():
        return _finding(
            "error",
            str(vault),
            "ordinary commit requires an existing real vault directory",
            "initialization-required",
        )
    required = (*vault_utils.REQUIRED_ROOT_FILES, *UNIVERSAL_INDEXES)
    missing = [
        label
        for label in required
        if not _is_real_regular(vault / label)
    ]
    if missing:
        return _finding(
            "error",
            "vault",
            "ordinary commit does not initialize an uninitialized vault; missing: "
            + ", ".join(missing),
            "initialization-required",
        )
    return None



def _catalog_by_id(catalog: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {
        str(record.get("id")): record
        for record in catalog.get("verticals", [])
        if isinstance(record, Mapping) and record.get("id") is not None
    }



def _apply_stage_write(stage: Path, label: str, content: bytes) -> None:
    path = stage / label
    current = stage
    for part in PurePosixPath(label).parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise OSError(f"staged path parent is not a real directory: {current}")
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise OSError(f"staged target is not a regular file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)



def _stage_activations(
    stage: Path,
    activation_ids: Sequence[str],
    catalog: Mapping[str, Any],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    if not activation_ids:
        return [], []

    findings: List[Dict[str, Any]] = []
    records = _catalog_by_id(catalog)
    schema = vault_utils.parse_schema(stage)
    existing_entries = list(schema.get("contract_entries", []))
    existing_by_id = {
        str(entry.get("id")): entry
        for entry in existing_entries
        if isinstance(entry, Mapping) and entry.get("id") is not None
    }
    requested_contracts: List[Dict[str, Any]] = []
    new_contracts = list(existing_entries)
    new_ids = set(existing_by_id)

    for identifier in activation_ids:
        record = records.get(identifier)
        if record is None:
            findings.append(
                _finding(
                    "error",
                    identifier,
                    "activation ID is not present in the authoritative vertical catalog",
                    "activation",
                )
            )
            continue
        version = record.get("contract_version")
        area = record.get("vault_area")
        index = record.get("index_path")
        if not isinstance(version, int) or not isinstance(area, str) or not isinstance(index, str):
            findings.append(
                _finding(
                    "error", identifier, "catalog record is not safe to activate", "activation"
                )
            )
            continue
        requested_contracts.append({"id": identifier, "version": version})
        area_path = stage / area
        index_path = stage / index
        if area_path.is_symlink() or (area_path.exists() and not area_path.is_dir()):
            findings.append(
                _finding(
                    "error", f"{area}/", "vertical area is not a real directory", "activation"
                )
            )
            continue
        area_path.mkdir(parents=True, exist_ok=True)
        if index_path.is_symlink() or (index_path.exists() and not index_path.is_file()):
            findings.append(
                _finding("error", index, "vertical index is not a regular file", "activation")
            )
            continue
        if not index_path.exists():
            _apply_stage_write(
                stage,
                index,
                vertical_index_template(record).encode("utf-8"),
            )
        if identifier not in new_ids:
            new_contracts.append({"id": identifier, "version": version})
            new_ids.add(identifier)

    if findings:
        return [], findings

    if len(new_contracts) != len(existing_entries):
        schema_text, schema_error = vault_utils.safe_read_text(stage / "SCHEMA.md")
        if schema_error or schema_text is None:
            findings.append(
                _finding(
                    "error", "SCHEMA.md", schema_error or "unable to read schema", "activation"
                )
            )
        else:
            try:
                candidate = schema_with_contracts(
                    schema_text,
                    [
                        {"id": str(entry["id"]), "version": int(entry["version"])}
                        for entry in new_contracts
                    ],
                )
                _apply_stage_write(stage, "SCHEMA.md", candidate.encode("utf-8"))
            except (KeyError, TypeError, ValueError) as error:
                findings.append(
                    _finding("error", "SCHEMA.md", str(error), "activation")
                )

    root_text, root_error = vault_utils.safe_read_text(stage / "index.md")
    if root_error or root_text is None:
        findings.append(
            _finding("error", "index.md", root_error or "unable to read root index", "activation")
        )
    else:
        try:
            root_candidate, _ = root_with_links(
                stage, requested_contracts, catalog, root_text
            )
            if root_candidate != root_text:
                _apply_stage_write(stage, "index.md", root_candidate.encode("utf-8"))
        except (OSError, RuntimeError, ValueError) as error:
            findings.append(_finding("error", "index.md", str(error), "activation"))

    return list(activation_ids), findings



def _validate_control_state(root: Path) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    try:
        catalog = vault_utils.load_vertical_catalog()
        catalog_problems = vault_utils.validate_vertical_catalog()
    except (OSError, ValueError, KeyError) as error:
        return {
            "ok": False,
            "errors": [{"path": "references/verticals.json", "message": str(error)}],
        }
    errors.extend(
        {"path": "references/verticals.json", "message": problem}
        for problem in catalog_problems
    )
    schema = vault_utils.parse_schema(root)
    if schema.get("version") != (0, 2):
        errors.append({"path": "SCHEMA.md", "message": "resulting schema is not 0.2"})
    if not schema.get("contract_section_present"):
        errors.append(
            {"path": "SCHEMA.md", "message": "schema 0.2 must declare vertical_contracts"}
        )
    errors.extend(
        {"path": "SCHEMA.md", "message": str(problem)}
        for problem in schema.get("contract_errors", [])
    )
    records = _catalog_by_id(catalog)
    entries = list(schema.get("contract_entries", []))
    seen: set[str] = set()
    root_text, root_error = vault_utils.safe_read_text(root / "index.md")
    if root_error or root_text is None:
        errors.append({"path": "index.md", "message": root_error or "missing root index"})
        root_text = ""

    for entry in entries:
        identifier = entry.get("id")
        version = entry.get("version")
        raw = str(entry.get("raw") or f"{identifier}@{version}")
        if not isinstance(identifier, str) or not isinstance(version, int):
            continue
        if identifier in seen:
            errors.append(
                {"path": "SCHEMA.md", "message": f"duplicate applied vertical contract: {raw}"}
            )
            continue
        seen.add(identifier)
        record = records.get(identifier)
        if record is None:
            errors.append(
                {"path": "SCHEMA.md", "message": f"applied vertical is not available: {raw}"}
            )
            continue
        available = record.get("contract_version")
        if version != available:
            errors.append(
                {
                    "path": "SCHEMA.md",
                    "message": f"applied vertical contract is not current: {raw} (available {identifier}@{available})",
                }
            )
        area = record.get("vault_area")
        index = record.get("index_path")
        if not isinstance(area, str) or not (root / area).is_dir():
            errors.append(
                {"path": f"{area or identifier}/", "message": "enabled vertical is missing its area"}
            )
        if not isinstance(index, str) or not _is_real_regular(root / index):
            errors.append(
                {"path": str(index or identifier), "message": "enabled vertical is missing its index"}
            )
        elif not root_has_link(root, index, root_text):
            errors.append(
                {
                    "path": "index.md",
                    "message": f"enabled vertical is missing its root index link: {index}",
                }
            )

    for identifier, record in records.items():
        area = record.get("vault_area")
        if isinstance(area, str) and (root / area).is_dir() and identifier not in seen:
            errors.append(
                {
                    "path": "SCHEMA.md",
                    "message": f"known vertical area is present but not explicitly activated: {area}/",
                }
            )

    for required in UNIVERSAL_INDEXES:
        if not _is_real_regular(root / required):
            errors.append({"path": required, "message": "missing required universal index"})

    return {"ok": not errors, "errors": errors}



def _filesystem_safety(root: Path) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    for path in vault_utils.iter_all_entries(root):
        if vault_utils.is_noncanonical(path, root):
            continue
        label = vault_utils.relative_label(path, root)
        try:
            mode = path.lstat().st_mode
        except OSError as error:
            errors.append({"path": label, "message": str(error)})
            continue
        if stat.S_ISLNK(mode):
            errors.append({"path": label, "message": "canonical vault content may not contain symlinks"})
        elif not stat.S_ISDIR(mode) and not stat.S_ISREG(mode):
            errors.append({"path": label, "message": "canonical vault content must use regular files and directories"})
    return {"ok": not errors, "errors": errors}



def _validate_state(root: Path) -> Dict[str, Any]:
    compatibility = vault_utils.runtime_compatibility(root)
    ordinary_errors, ordinary_warnings = lint_vault.lint_vault(root, dt.date.today())
    catalog = sync_indexes.synchronize(root, write=False)
    controls = _validate_control_state(root)
    filesystem = _filesystem_safety(root)
    ordinary = {
        "ok": not ordinary_errors,
        "errors": list(ordinary_errors),
        "warnings": list(ordinary_warnings),
    }
    catalog_errors = [
        {
            "path": str(item.get("path", "")),
            "message": str(item.get("message", "")),
            "classification": str(item.get("classification", "catalog")),
        }
        for item in catalog.get("findings", [])
        if item.get("severity") == "error"
    ]
    catalog_summary = {
        "ok": not catalog_errors,
        "status": catalog.get("status"),
        "changed": list(catalog.get("changed", [])),
        "errors": catalog_errors,
    }
    runtime_summary = {
        "ok": bool(compatibility.get("ok")),
        "state": compatibility.get("state"),
        "schema_version": compatibility.get("schema_version"),
        "latest_supported_schema": compatibility.get("latest_supported_schema"),
        "message": compatibility.get("message"),
    }
    ok = (
        bool(compatibility.get("ok"))
        and bool(ordinary["ok"])
        and bool(catalog_summary["ok"])
        and bool(controls["ok"])
        and bool(filesystem["ok"])
    )
    return {
        "ok": ok,
        "runtime_compatibility": runtime_summary,
        "ordinary": ordinary,
        "catalog_sync": catalog_summary,
        "controls": controls,
        "filesystem": filesystem,
    }



def _validation_findings(
    validation: Mapping[str, Any], classification: str
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if validation.get("ok"):
        return findings
    runtime = validation.get("runtime_compatibility")
    if isinstance(runtime, Mapping) and not runtime.get("ok"):
        findings.append(
            _finding(
                "error",
                "SCHEMA.md",
                str(runtime.get("message") or "vault is not current"),
                f"{classification}-runtime",
                state=runtime.get("state"),
            )
        )
    for section_name in ("ordinary", "catalog_sync", "controls", "filesystem"):
        section = validation.get(section_name)
        if not isinstance(section, Mapping):
            continue
        errors = section.get("errors", [])
        if isinstance(errors, list):
            for item in errors:
                if isinstance(item, Mapping):
                    findings.append(
                        _finding(
                            "error",
                            str(item.get("path", "")),
                            str(item.get("message", "")),
                            f"{classification}-{section_name}",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            "error", "", str(item), f"{classification}-{section_name}"
                        )
                    )
    return findings



def _verify_rollback_snapshot(
    rollback: Mapping[str, Any],
    vault: Path,
    source_snapshot: str,
) -> Dict[str, Any]:
    if not rollback.get("ok"):
        return dict(rollback)
    current_snapshot, error = _safe_snapshot(vault)
    if error is None and current_snapshot == source_snapshot:
        return dict(rollback)
    verified = dict(rollback)
    verified["ok"] = False
    verified["status"] = "rollback-failed"
    failures = list(verified.get("failures", []))
    failures.append(
        "rollback snapshot does not match the original source snapshot"
        if error is None
        else f"unable to verify rollback snapshot: {error}"
    )
    verified["failures"] = failures
    return verified


def _rollback_and_verify(
    transaction: Mapping[str, Any],
    vault: Path,
    source_snapshot: str,
) -> Dict[str, Any]:
    rollback = file_transaction.rollback_transaction(transaction)
    return _verify_rollback_snapshot(rollback, vault, source_snapshot)



def _failure_after_backup(
    receipt: Dict[str, Any],
    transaction: Mapping[str, Any],
    vault: Path,
    source_snapshot: str,
    message: str,
    classification: str,
) -> Dict[str, Any]:
    rollback = _rollback_and_verify(transaction, vault, source_snapshot)
    receipt["rollback"] = rollback
    receipt["status"] = "failed"
    receipt["state"] = classification
    receipt["findings"].append(_finding("error", "", message, classification))
    if not rollback.get("ok"):
        receipt["findings"].append(
            _finding(
                "error",
                "",
                "active-vault rollback could not be verified",
                "rollback",
                failures=list(rollback.get("failures", [])),
            )
        )
    return receipt



def commit_mutation(vault: Path, proposal: Mapping[str, Any]) -> Dict[str, Any]:
    """Commit one prepared CREATE/UPDATE proposal to an existing current vault."""

    supplied = Path(vault).expanduser()
    receipt = _base_receipt(supplied)
    initialization = _initialization_finding(supplied)
    source_snapshot = ""
    if initialization is None:
        captured, capture_error = _safe_snapshot(supplied)
        if capture_error is not None or captured is None:
            receipt["state"] = "snapshot-error"
            receipt["findings"].append(
                _finding(
                    "error",
                    "",
                    f"unable to capture source snapshot: {capture_error or 'unknown error'}",
                    "snapshot",
                )
            )
            return receipt
        source_snapshot = captured
        receipt["source_snapshot_id"] = source_snapshot

    if initialization is not None:
        receipt["state"] = "initialization-required"
        receipt["findings"].append(initialization)
        return receipt

    raw_expected_snapshot = (
        proposal.get("expected_snapshot")
        if isinstance(proposal, Mapping)
        else None
    )
    receipt["expected_snapshot_id"] = raw_expected_snapshot
    if (
        isinstance(raw_expected_snapshot, str)
        and raw_expected_snapshot
        and raw_expected_snapshot != source_snapshot
    ):
        receipt["state"] = "snapshot-mismatch"
        receipt["findings"].append(
            _finding(
                "error",
                "",
                "expected source snapshot does not match the active vault",
                "snapshot-mismatch",
                expected_snapshot=raw_expected_snapshot,
                current_snapshot=source_snapshot,
            )
        )
        return receipt

    validated, input_findings = _validate_proposal(supplied, proposal)
    if input_findings:
        receipt["state"] = "input-invalid"
        receipt["findings"].extend(input_findings)
        return receipt
    assert validated is not None
    receipt["expected_snapshot_id"] = validated["expected_snapshot"]

    expected_snapshot = validated["expected_snapshot"]
    if expected_snapshot is not None and expected_snapshot != source_snapshot:
        receipt["state"] = "snapshot-mismatch"
        receipt["findings"].append(
            _finding(
                "error",
                "",
                "expected source snapshot does not match the active vault",
                "snapshot-mismatch",
                expected_snapshot=expected_snapshot,
                current_snapshot=source_snapshot,
            )
        )
        return receipt

    compatibility = vault_utils.runtime_compatibility(supplied)
    if not compatibility.get("ok"):
        receipt["state"] = str(compatibility.get("state") or "runtime-blocked")
        receipt["validation"]["runtime"] = {
            "ok": False,
            "state": compatibility.get("state"),
            "message": compatibility.get("message"),
        }
        receipt["findings"].append(
            _finding(
                "error",
                "SCHEMA.md",
                str(compatibility.get("message") or "vault is not current"),
                "runtime-gate",
                state=compatibility.get("state"),
            )
        )
        return receipt

    try:
        catalog = vault_utils.load_vertical_catalog()
    except (OSError, ValueError, KeyError) as error:
        receipt["state"] = "catalog-invalid"
        receipt["findings"].append(
            _finding("error", "references/verticals.json", str(error), "catalog")
        )
        return receipt
    catalog_problems = vault_utils.validate_vertical_catalog()
    if catalog_problems:
        receipt["state"] = "catalog-invalid"
        receipt["findings"].extend(
            _finding("error", "references/verticals.json", problem, "catalog")
            for problem in catalog_problems
        )
        return receipt

    source_bytes = _canonical_bytes(supplied)
    temporary_directory: Optional[tempfile.TemporaryDirectory[str]] = None
    try:
        temporary_directory = tempfile.TemporaryDirectory(prefix="selfcontext-ordinary-")
        stage = Path(temporary_directory.name) / "vault"
        shutil.copytree(supplied, stage, symlinks=True)

        for label, content in validated["writes"].items():
            _apply_stage_write(stage, label, content)

        activations, activation_findings = _stage_activations(
            stage, validated["activations"], catalog
        )
        if activation_findings:
            receipt["state"] = "activation-invalid"
            receipt["findings"].extend(activation_findings)
            return receipt
        receipt["activations"] = activations

        sync_write = sync_indexes.synchronize(stage, write=True)
        sync_errors = [
            item for item in sync_write.get("findings", []) if item.get("severity") == "error"
        ]
        if sync_errors:
            receipt["state"] = "index-plan-invalid"
            receipt["findings"].extend(
                _finding(
                    "error",
                    str(item.get("path", "")),
                    str(item.get("message", "")),
                    "proposed-index",
                )
                for item in sync_errors
            )
            return receipt
        sync_after = sync_indexes.synchronize(stage, write=False)
        sync_after_errors = [
            item for item in sync_after.get("findings", []) if item.get("severity") == "error"
        ]
        if sync_after_errors:
            receipt["state"] = "index-plan-invalid"
            receipt["findings"].extend(
                _finding(
                    "error",
                    str(item.get("path", "")),
                    str(item.get("message", "")),
                    "proposed-index",
                )
                for item in sync_after_errors
            )
            return receipt

        pre_log_bytes = _canonical_bytes(stage)
        _, _, deleted_before_log = _diff_bytes(source_bytes, pre_log_bytes)
        if deleted_before_log:
            receipt["state"] = "unsupported-deletion"
            receipt["findings"].extend(
                _finding(
                    "error",
                    label,
                    "proposed state would delete an existing canonical file",
                    "unsupported-deletion",
                )
                for label in deleted_before_log
            )
            return receipt

        pre_log_created, pre_log_modified, _ = _diff_bytes(source_bytes, pre_log_bytes)
        if not pre_log_created and not pre_log_modified:
            receipt["status"] = "noop"
            receipt["state"] = "no-op"
            receipt["proposed_snapshot_id"] = source_snapshot
            receipt["final_snapshot_id"] = source_snapshot
            return receipt

        raw_log = validated.get("log")
        if raw_log is None:
            receipt["state"] = "input-log"
            receipt["findings"].append(
                _finding(
                    "error",
                    "log",
                    "a changed proposed state requires operation log metadata",
                    "input-log",
                )
            )
            return receipt
        log_text, log_error = vault_utils.safe_read_text(stage / "log.md")
        if log_error or log_text is None:
            receipt["state"] = "proposed-log-invalid"
            receipt["findings"].append(
                _finding(
                    "error", "log.md", log_error or "unable to read operation log", "proposed-log"
                )
            )
            return receipt
        try:
            log_candidate, _ = log_utils.append_operation_entry(
                log_text,
                operation=str(raw_log["operation"]),
                summary=str(raw_log["summary"]),
                paths=list(raw_log["paths"]),
            )
        except ValueError as error:
            receipt["state"] = "proposed-log-invalid"
            receipt["findings"].append(
                _finding("error", "log.md", str(error), "proposed-log")
            )
            return receipt
        _apply_stage_write(stage, "log.md", log_candidate.encode("utf-8"))

        proposed_bytes = _canonical_bytes(stage)
        created, modified, deleted = _diff_bytes(source_bytes, proposed_bytes)
        if deleted:
            receipt["state"] = "unsupported-deletion"
            receipt["findings"].extend(
                _finding(
                    "error",
                    label,
                    "proposed state would delete an existing canonical file",
                    "unsupported-deletion",
                )
                for label in deleted
            )
            return receipt
        receipt["planned_created"] = created
        receipt["planned_modified"] = modified
        receipt["planned_changed"] = sorted(set(created + modified))
        receipt["proposed_snapshot_id"] = vault_utils.snapshot_id(stage)

        try:
            proposed_validation = _validate_state(stage)
        except Exception as error:  # pragma: no cover - defensive validation boundary
            proposed_validation = {
                "ok": False,
                "ordinary": {
                    "errors": [{"path": "", "message": str(error)}],
                    "warnings": [],
                },
            }
        receipt["validation"]["proposed"] = proposed_validation
        if not proposed_validation.get("ok"):
            receipt["state"] = "proposed-validation"
            receipt["findings"].extend(
                _validation_findings(proposed_validation, "proposed")
            )
            return receipt

        current_snapshot, snapshot_error = _safe_snapshot(supplied)
        if snapshot_error is not None or current_snapshot != source_snapshot:
            receipt["state"] = "snapshot-drift"
            receipt["findings"].append(
                _finding(
                    "error",
                    "",
                    "source vault changed while the proposed state was being staged",
                    "snapshot-drift",
                    planned_snapshot=source_snapshot,
                    current_snapshot=current_snapshot or snapshot_error or "",
                )
            )
            return receipt

        compatibility_before_backup = vault_utils.runtime_compatibility(supplied)
        if not compatibility_before_backup.get("ok"):
            receipt["state"] = str(
                compatibility_before_backup.get("state") or "runtime-blocked"
            )
            receipt["findings"].append(
                _finding(
                    "error",
                    "SCHEMA.md",
                    str(
                        compatibility_before_backup.get("message")
                        or "vault is not current"
                    ),
                    "runtime-gate",
                    state=compatibility_before_backup.get("state"),
                )
            )
            return receipt

        try:
            provisional, removed = backup_vault.create_backup(supplied)
            provisional = Path(provisional)
            if not provisional.is_file():
                raise backup_vault.BackupError(
                    f"backup helper returned a path that does not exist: {provisional}"
                )
        except Exception as error:
            receipt["state"] = "provisional-backup"
            receipt["findings"].append(
                _finding(
                    "error",
                    "backups/",
                    f"provisional recovery backup failed: {error}",
                    "backup",
                )
            )
            return receipt

        receipt["provisional_backup"] = str(provisional)
        receipt["provisional_backup_removed"] = [str(path) for path in removed]
        receipt["removed_backups"] = list(receipt["provisional_backup_removed"])

        after_backup_snapshot, after_backup_error = _safe_snapshot(supplied)
        if after_backup_error is not None or after_backup_snapshot != source_snapshot:
            receipt["state"] = "snapshot-drift"
            receipt["findings"].append(
                _finding(
                    "error",
                    "",
                    "source vault changed after the provisional recovery backup",
                    "snapshot-drift",
                    planned_snapshot=source_snapshot,
                    current_snapshot=after_backup_snapshot or after_backup_error or "",
                )
            )
            return receipt

        compatibility_before_replace = vault_utils.runtime_compatibility(supplied)
        if not compatibility_before_replace.get("ok"):
            receipt["state"] = str(
                compatibility_before_replace.get("state") or "runtime-blocked"
            )
            receipt["findings"].append(
                _finding(
                    "error",
                    "SCHEMA.md",
                    str(
                        compatibility_before_replace.get("message")
                        or "vault is not current"
                    ),
                    "runtime-gate",
                    state=compatibility_before_replace.get("state"),
                )
            )
            return receipt

        updates = {
            label: proposed_bytes[label]
            for label in sorted(set(created + modified))
        }
        transaction = file_transaction.replace_planned_files(supplied, updates)
        if not transaction.get("ok"):
            receipt["rollback"] = transaction.get(
                "rollback", {"status": "unknown", "ok": False}
            )
            if receipt["rollback"].get("ok"):
                receipt["rollback"] = _verify_rollback_snapshot(
                    receipt["rollback"], supplied, source_snapshot
                )
            receipt["status"] = "failed"
            receipt["state"] = "active-replacement"
            receipt["findings"].append(
                _finding(
                    "error",
                    "",
                    f"active-vault replacement failed: {transaction.get('error', 'unknown error')}",
                    "active-replacement",
                )
            )
            if not receipt["rollback"].get("ok"):
                receipt["findings"].append(
                    _finding(
                        "error",
                        "",
                        "active-vault rollback could not be verified",
                        "rollback",
                        failures=list(receipt["rollback"].get("failures", [])),
                    )
                )
            return receipt

        try:
            active_validation = _validate_state(supplied)
        except Exception as error:  # pragma: no cover - rollback safety boundary
            active_validation = {
                "ok": False,
                "ordinary": {
                    "errors": [{"path": "", "message": str(error)}],
                    "warnings": [],
                },
            }
        receipt["validation"]["active"] = active_validation
        actual_final_snapshot, active_snapshot_error = _safe_snapshot(supplied)
        expected_final_snapshot = receipt["proposed_snapshot_id"]
        if active_snapshot_error is not None or actual_final_snapshot != expected_final_snapshot:
            active_validation = dict(active_validation)
            active_validation["ok"] = False
            active_validation.setdefault("filesystem", {}).setdefault("errors", []).append(
                {
                    "path": "",
                    "message": "active vault bytes differ from the validated proposed state",
                }
            )
            receipt["validation"]["active"] = active_validation

        if not active_validation.get("ok"):
            receipt["findings"].extend(
                _validation_findings(active_validation, "active")
            )
            return _failure_after_backup(
                receipt,
                transaction,
                supplied,
                source_snapshot,
                "active-vault validation failed; active changes were rolled back",
                "active-validation",
            )

        receipt["final_snapshot_id"] = str(actual_final_snapshot or "")
        try:
            final_backup, final_removed = backup_vault.create_backup(supplied)
            final_backup = Path(final_backup)
            if not final_backup.is_file():
                raise backup_vault.BackupError(
                    f"backup helper returned a path that does not exist: {final_backup}"
                )
        except Exception as error:
            receipt["findings"].append(
                _finding(
                    "error",
                    "backups/",
                    f"final backup failed: {error}",
                    "backup",
                )
            )
            return _failure_after_backup(
                receipt,
                transaction,
                supplied,
                source_snapshot,
                "final backup failed; active changes were rolled back",
                "final-backup",
            )

        receipt["final_backup"] = str(final_backup)
        receipt["provisional_backup_removed"].extend(str(path) for path in final_removed)
        receipt["removed_backups"].extend(str(path) for path in final_removed)
        receipt["created"] = list(receipt["planned_created"])
        receipt["modified"] = list(receipt["planned_modified"])
        receipt["changed"] = list(receipt["planned_changed"])
        receipt["status"] = "success"
        receipt["state"] = "committed"
        receipt["rollback"] = {"status": "not-needed", "ok": True}
        try:
            discarded = backup_vault.discard_backup(supplied, provisional)
            receipt["provisional_discarded"] = bool(discarded)
            if not discarded:
                receipt["findings"].append(
                    _finding(
                        "warning",
                        "backups/",
                        "provisional recovery backup was already absent after final backup success",
                        "backup-cleanup",
                    )
                )
        except Exception as error:
            receipt["findings"].append(
                _finding(
                    "warning",
                    "backups/",
                    f"provisional backup cleanup failed; archive retained: {error}",
                    "backup-cleanup",
                )
            )
        return receipt
    except Exception as error:  # pragma: no cover - defensive receipt boundary
        receipt["state"] = "internal-error"
        receipt["findings"].append(
            _finding("error", "", f"ordinary commit could not be completed: {error}", "internal")
        )
        return receipt
    finally:
        if temporary_directory is not None:
            temporary_directory.cleanup()
        receipt["findings"] = sorted(
            receipt["findings"],
            key=lambda item: (
                str(item.get("path", "")),
                str(item.get("classification", "")),
                str(item.get("message", "")),
            ),
        )



def _load_proposal(value: str) -> Mapping[str, Any]:
    if value == "-":
        text = sys.stdin.read()
    else:
        path = Path(value)
        text = path.read_text(encoding="utf-8") if path.is_file() else value
    parsed = json.loads(text)
    if not isinstance(parsed, Mapping):
        raise ValueError("proposal JSON must be an object")
    return parsed



def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Commit a prepared CREATE/UPDATE proposal to an existing current SelfContext vault"
    )
    parser.add_argument("vault", nargs="?", default="vault")
    parser.add_argument(
        "--proposal",
        required=True,
        help="JSON proposal text, a JSON file path, or '-' to read JSON from stdin",
    )
    args = parser.parse_args(argv)
    try:
        proposal = _load_proposal(args.proposal)
        result = commit_mutation(Path(args.vault), proposal)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result = _base_receipt(Path(args.vault))
        result["state"] = "input-invalid"
        result["findings"].append(
            _finding("error", "proposal", str(error), "input-contract")
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"success", "noop"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
