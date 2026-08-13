#!/usr/bin/env python3
"""Plan or explicitly apply the conservative schema 0.1 -> 0.2 migration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import backup_vault
    import sync_indexes
    from vault_utils import (
        catalog_records,
        infer_enabled_contracts,
        load_vertical_catalog,
        parse_schema,
        relative_label,
        safe_read_text,
    )
except ImportError:  # pragma: no cover
    from . import backup_vault, sync_indexes  # type: ignore
    from .vault_utils import (  # type: ignore
        catalog_records,
        infer_enabled_contracts,
        load_vertical_catalog,
        parse_schema,
        relative_label,
        safe_read_text,
    )


SCHEMA_LINE = re.compile(r"^(\s*schema_version:\s*)0\.1(\s*)$", re.MULTILINE)


def _contract_strings(contracts: List[Dict[str, Any]]) -> List[str]:
    return [f"{item.get('id')}@{item.get('version')}" for item in contracts]


def _schema_with_contracts(text: str, contracts: List[Dict[str, Any]]) -> str:
    match = SCHEMA_LINE.search(text)
    if not match:
        raise ValueError("SCHEMA.md does not contain schema_version: 0.1")
    replacement = f"{match.group(1)}0.2{match.group(2)}"
    updated = text[: match.start()] + replacement + text[match.end() :]
    marker_match = re.search(r"^\s*vertical_contracts:\s*(?:\n(?:\s*-\s*[^\n]+\n?)*)?", updated, re.MULTILINE)
    block = "vertical_contracts:\n" + "".join(
        f"  - {contract['id']}@{contract['version']}\n" for contract in contracts
    )
    if marker_match:
        updated = updated[: marker_match.start()] + block + updated[marker_match.end() :]
    else:
        insertion = "\n" + block
        updated = updated[: match.start()] + insertion + updated[match.start() :]
    return updated


def _ensure_root_links(vault: Path, contracts: List[Dict[str, Any]], catalog: Dict[str, Any]) -> List[str]:
    root_index = vault / "index.md"
    text = root_index.read_text(encoding="utf-8")
    records = {str(record.get("id")): record for record in catalog_records(catalog)}
    additions: List[str] = []
    for contract in contracts:
        record = records.get(str(contract.get("id")))
        if not record:
            continue
        index_path = record.get("index_path")
        area = record.get("vault_area")
        if not isinstance(index_path, str) or not isinstance(area, str):
            continue
        if (vault / area).is_dir() and (vault / index_path).is_file() and index_path not in text:
            additions.append(f"- [{record.get('display_name', area)} context]({index_path})")
    if additions:
        separator = "" if text.endswith("\n") else "\n"
        root_index.write_text(text + separator + "\n".join(additions) + "\n", encoding="utf-8")
    return additions


def plan_migration(vault: Path) -> Dict[str, Any]:
    vault = vault.expanduser()
    schema = parse_schema(vault)
    catalog = load_vertical_catalog()
    contracts, source = infer_enabled_contracts(vault, catalog)
    findings: List[Dict[str, str]] = []
    if schema.get("error"):
        findings.append({"severity": "error", "path": "SCHEMA.md", "message": str(schema["error"])})
    version = schema.get("version")
    if version == (0, 2):
        findings.append({"severity": "info", "path": "SCHEMA.md", "message": "vault already uses schema 0.2; no migration needed"})
    elif version != (0, 1):
        findings.append({"severity": "error", "path": "SCHEMA.md", "message": "only schema 0.1 can be migrated explicitly"})
    for contract in contracts:
        record = next((item for item in catalog_records(catalog) if item.get("id") == contract.get("id")), None)
        if record is None:
            findings.append({"severity": "warning", "path": "SCHEMA.md", "message": f"ambiguous or unavailable vertical preserved: {contract.get('id')}"})
            continue
        area = record.get("vault_area")
        index = record.get("index_path")
        if isinstance(area, str) and not (vault / area).is_dir():
            findings.append({"severity": "warning", "path": area + "/", "message": "enabled vertical area is absent; migration will not create personal content"})
        if isinstance(index, str) and (vault / area).is_dir() and not (vault / index).is_file():
            findings.append({"severity": "info", "path": index, "message": "known vertical index can be added as control metadata"})
    known = {"core", "review", "sources", "derived"} | {str(item.get("vault_area")) for item in catalog_records(catalog)}
    if vault.is_dir():
        for child in sorted(vault.iterdir()):
            if child.is_dir() and child.name not in known and child.name not in {".obsidian", "backups"}:
                findings.append({"severity": "info", "path": child.name + "/", "message": "custom area preserved and not relocated"})
    return {
        "vault": str(vault.resolve()) if vault.exists() else str(vault),
        "from_schema": schema.get("version_text"),
        "to_schema": "0.2" if version == (0, 1) else schema.get("version_text"),
        "enabled_vertical_contracts": _contract_strings(contracts),
        "inference": source,
        "findings": findings,
        "would_change": ["SCHEMA.md", "index.md", "managed catalog blocks"] if version == (0, 1) else [],
    }


def apply_migration(vault: Path) -> Dict[str, Any]:
    plan = plan_migration(vault)
    if plan.get("from_schema") != "0.1":
        return plan
    if any(item.get("severity") == "error" for item in plan.get("findings", [])):
        return plan
    vault = vault.expanduser()
    try:
        backup_path, removed = backup_vault.create_backup(vault)
    except backup_vault.BackupError as error:
        plan["findings"].append({"severity": "error", "path": "backups/", "message": f"pre-write backup failed: {error}"})
        return plan

    schema_path = vault / "SCHEMA.md"
    schema_text = schema_path.read_text(encoding="utf-8")
    contracts = [
        {"id": item.split("@", 1)[0], "version": int(item.split("@", 1)[1])}
        for item in plan["enabled_vertical_contracts"]
    ]
    changed: List[str] = []
    schema_path.write_text(_schema_with_contracts(schema_text, contracts), encoding="utf-8")
    changed.append("SCHEMA.md")
    catalog = load_vertical_catalog()
    additions = _ensure_root_links(vault, contracts, catalog)
    if additions:
        changed.append("index.md")

    sync_result = sync_indexes.synchronize(vault, write=True)
    changed.extend(item for item in sync_result.get("changed", []) if item not in changed)
    plan.update(
        {
            "backup": str(backup_path),
            "removed_backups": [str(path) for path in removed],
            "changed": changed,
            "sync": sync_result,
        }
    )
    if any(item.get("severity") == "error" for item in sync_result.get("findings", [])):
        plan["findings"].append({"severity": "error", "path": "", "message": "post-migration catalog synchronization failed"})
    return plan


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or explicitly migrate a SelfContext vault to schema 0.2")
    parser.add_argument("vault", nargs="?", default="vault")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only migration plan")
    mode.add_argument("--write", action="store_true", help="create a backup and apply the migration")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    result = apply_migration(Path(args.vault)) if args.write else plan_migration(Path(args.vault))
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for item in result.get("findings", []):
            prefix = str(item.get("severity", "info")).upper()
            location = f"{item.get('path')}: " if item.get("path") else ""
            print(f"{prefix}: {location}{item.get('message', '')}")
        if result.get("backup"):
            print(f"Backup: {result['backup']}")
        if result.get("changed"):
            print("Changed: " + ", ".join(result["changed"]))
        elif not result.get("findings"):
            print("No migration changes needed")
    return 1 if any(item.get("severity") == "error" for item in result.get("findings", [])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
