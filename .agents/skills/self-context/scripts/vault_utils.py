#!/usr/bin/env python3
"""Shared dependency-free helpers for SelfContext maintenance scripts.

This module is an implementation detail of the deterministic helpers.  The
Markdown vault remains the canonical source of truth; these functions never
create a permanent index or store page bodies in a maintenance report.
"""

from __future__ import annotations

import datetime as date
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import unquote

try:
    import migration_registry as _migration_registry_module
except ImportError:  # pragma: no cover - package-style import fallback
    from . import migration_registry as _migration_registry_module  # type: ignore


NON_CANONICAL_DIRECTORIES = {".obsidian", "backups", ".DS_Store"}
SCHEMA_VERSION_PATTERN = re.compile(
    r"^\s*schema_version:\s*([0-9]+)\.([0-9]+)\s*$", re.MULTILINE
)
CONTRACT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CONTRACT_VERSION_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)$")
# Link labels may contain backslash-escaped Markdown punctuation. Generated
# catalogs use this form for titles containing brackets, backslashes, or
# backticks, so the shared link scanner must not stop at an escaped bracket.
LINK_PATTERN = re.compile(r"(?<!!)\[(?:\\.|[^\\\]])*\]\(([^)\r\n]+)\)")
MALFORMED_LINK_PATTERN = re.compile(r"(?<!!)\[(?:\\.|[^\\\]])*\]\([^)]*$")

REQUIRED_ROOT_FILES = ("SCHEMA.md", "index.md", "log.md")
REQUIRED_FIELDS = (
    "type",
    "title",
    "description",
    "tags",
    "status",
    "generated",
    "verified",
    "sources",
    "assertion_kind",
    "stale_after",
)
REQUIRED_NON_NULL_FIELDS = {
    "type",
    "title",
    "description",
    "status",
    "generated",
    "assertion_kind",
}
ALLOWED_TYPES = {"concept", "observation", "source", "synthesis"}
ALLOWED_STATUSES = {"active", "draft", "review", "archived", "superseded"}
ALLOWED_ASSERTIONS = {
    "user_stated_fact",
    "source_derived_fact",
    "agent_inference",
    "derived_synthesis",
    "source_record",
    "mixed",
}


# Resolve the catalog relative to the SelfContext skill that owns it, rather
# than relative to the caller's working directory.
def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def catalog_path() -> Path:
    return skill_root() / "references" / "verticals.json"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        # The vault contract only needs simple scalar lists.  Accept JSON when
        # possible, then use a small YAML-compatible comma split.
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [parse_scalar(item) for item in inner.split(",") if item.strip()]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    return value


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == "null"


def parse_frontmatter_text(text: str) -> Tuple[Optional[Dict[str, Any]], List[str], str]:
    """Parse the deliberately small YAML subset used by durable pages."""

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["missing YAML frontmatter"], text

    closing = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if closing is None:
        return None, ["frontmatter has no closing ---"], text

    values: Dict[str, Any] = {}
    list_key: Optional[str] = None
    errors: List[str] = []
    for line in lines[1:closing]:
        if not line.strip():
            continue
        stripped = line.strip()
        if (line.startswith("  - ") or line.startswith("\t- ")) and list_key:
            current = values.get(list_key)
            if current is None:
                current = []
                values[list_key] = current
            if not isinstance(current, list):
                errors.append(f"field {list_key!r} mixes scalar and list values")
                continue
            current.append(parse_scalar(stripped[2:]))
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            errors.append(f"malformed frontmatter line: {line!r}")
            list_key = None
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            errors.append("frontmatter contains an empty field name")
            list_key = None
            continue
        raw_value = raw_value.strip()
        # Folded/literal YAML is outside the small page contract.  Retain an
        # empty scalar and let the description/type checks report what matters.
        if raw_value in {">", "|", ">-", "|-", ">+", "|+"}:
            value: Any = ""
        else:
            value = parse_scalar(raw_value)
        values[key] = value
        list_key = key if raw_value == "" else None

    body = "\n".join(lines[closing + 1 :])
    if text.endswith("\n"):
        body += "\n"
    return values, errors, body


def parse_frontmatter(path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    text = path.read_text(encoding="utf-8")
    fields, errors, _ = parse_frontmatter_text(text)
    return fields, errors


def safe_read_text(path: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeError:
        # Keep malformed input details out of reports.  The finding carries the
        # affected relative path, while this stable message is enough to
        # distinguish a decoding failure from other read errors.
        return None, "UnicodeDecodeError: file is not valid UTF-8"
    except OSError as error:
        return None, f"{type(error).__name__}: unable to read file"


def safe_read_bytes(path: Path) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        return path.read_bytes(), None
    except OSError as error:
        return None, f"{type(error).__name__}: {error}"


def _safe_read_page(
    path: Path,
) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    content, error = safe_read_bytes(path)
    if content is None:
        error_type = error.split(":", 1)[0] if error else "OSError"
        return None, None, f"{error_type}: unable to read file"
    try:
        return content, content.decode("utf-8"), None
    except UnicodeError:
        return content, None, "UnicodeDecodeError: file is not valid UTF-8"


def relative_label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.resolve().relative_to(root.resolve()).as_posix()


def relative_parts(path: Path, root: Path) -> Tuple[str, ...]:
    try:
        return tuple(path.relative_to(root).parts)
    except ValueError:
        try:
            return tuple(path.resolve().relative_to(root.resolve()).parts)
        except ValueError:
            return ()


def is_noncanonical(path: Path, root: Path) -> bool:
    parts = relative_parts(path, root)
    return bool(NON_CANONICAL_DIRECTORIES.intersection(parts) or path.name == ".DS_Store")


def is_control_page(path: Path, root: Path) -> bool:
    relative = Path(*relative_parts(path, root))
    return relative in {Path("SCHEMA.md"), Path("log.md")} or path.name == "index.md"


def is_deep_report(path: Path, root: Path) -> bool:
    parts = relative_parts(path, root)
    return len(parts) >= 2 and parts[0] == "review" and parts[1] == "deep-reviews"


def iter_vault_entries(root: Path) -> Iterator[Path]:
    """Yield all entries below root without following symlinked directories."""

    if not root.exists() or not root.is_dir() or root.is_symlink():
        return
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories.sort()
        files.sort()
        kept_directories: List[str] = []
        for name in directories:
            path = current_path / name
            if is_noncanonical(path, root):
                continue
            yield path
            if not path.is_symlink():
                kept_directories.append(name)
        directories[:] = kept_directories
        for name in files:
            path = current_path / name
            if not is_noncanonical(path, root):
                yield path


def iter_symlinks(root: Path, include_noncanonical: bool = False) -> Iterator[Path]:
    if root.is_symlink():
        yield root
        return
    for path in iter_all_entries(root):
        if path.is_symlink() and (include_noncanonical or not is_noncanonical(path, root)):
            yield path


def iter_all_entries(root: Path) -> Iterator[Path]:
    """Yield entries, including noncanonical directories, without following links."""

    if not root.exists() or not root.is_dir() or root.is_symlink():
        return
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories.sort()
        files.sort()
        for name in directories:
            yield current_path / name
        for name in files:
            yield current_path / name
        # os.walk does not descend into symlinked dirs when followlinks=False.
        directories[:] = [name for name in directories if not (current_path / name).is_symlink()]


def canonical_files(root: Path) -> List[Path]:
    return sorted(
        (
            path
            for path in iter_vault_entries(root)
            if path.is_file() and not path.is_symlink()
        ),
        key=lambda path: relative_label(path, root),
    )


def canonical_markdown_files(root: Path) -> List[Path]:
    return [path for path in canonical_files(root) if path.suffix.lower() == ".md"]


def normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def normalized_tokens(value: str) -> List[str]:
    return re.findall(r"[\w]+", normalized_text(value), flags=re.UNICODE)


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def parse_iso_date(value: Any) -> Optional[date.date]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def parse_contract_version(value: Any) -> Optional[int]:
    """Parse the intentionally small non-negative-integer version form."""

    if not isinstance(value, str):
        return None
    text = value
    if not CONTRACT_VERSION_PATTERN.fullmatch(text):
        return None
    return int(text)


def parse_contract_entry(value: str) -> Dict[str, Any]:
    """Parse one ``vertical@version`` entry without coercing malformed input.

    Contract versions intentionally use canonical non-negative decimal
    integers (for example, ``0``, ``1``, or ``2``). Semantic-version strings,
    ranges, and other formats are rejected because the current repository
    cannot compare them safely.
    """

    raw = value.strip()
    without_comment = raw.split("#", 1)[0].strip()
    identifier: Optional[str] = None
    version_text = ""
    if without_comment.count("@") == 1:
        # Outer YAML/list whitespace was removed above; whitespace inside the
        # pair is not normalized because malformed entries must remain errors.
        identifier, version_text = without_comment.split("@", 1)

    result: Dict[str, Any] = {
        "id": identifier,
        "version": parse_contract_version(version_text),
        "version_text": version_text,
        "raw": raw,
    }
    if identifier is None or not CONTRACT_ID_PATTERN.fullmatch(identifier):
        result["error"] = f"invalid vertical contract entry: {raw or '<empty>'}"
    elif result["version"] is None:
        result["error"] = (
            f"invalid contract version for {identifier}: "
            f"{version_text or '<empty>'} (expected a non-negative integer)"
        )
    return result


def iter_markdown_links(text: str) -> Iterable[str]:
    in_fence = False
    visible_lines: List[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            visible_lines.append(line)
    for match in LINK_PATTERN.finditer("\n".join(visible_lines)):
        destination = match.group(1).strip()
        if not destination:
            continue
        if destination.startswith("<") and ">" in destination:
            destination = destination[1 : destination.index(">")]
        else:
            destination = destination.split()[0]
        yield destination


def is_external(destination: str) -> bool:
    return destination.startswith(
        ("#", "//", "http://", "https://", "mailto:", "tel:")
    )


def link_target(source: Path, destination: str, root: Path) -> Optional[Path]:
    if is_external(destination):
        return None
    target_text = destination.split("#", 1)[0].split("?", 1)[0]
    if not target_text:
        return source
    raw_target = source.parent / unquote(target_text)
    try:
        target = raw_target.resolve()
    except (OSError, RuntimeError, ValueError):
        # Preserve a reportable path when resolution encounters an unreadable
        # target or a symlink loop. Callers will classify it as unsafe or
        # broken rather than allowing the linter to raise.
        return raw_target
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return target
    return target


def _safe_is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except (OSError, RuntimeError, ValueError):
        return False


def markdown_link_records(path: Path, root: Path, text: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for destination in iter_markdown_links(text):
        target = link_target(path, destination, root)
        external = is_external(destination)
        target_label: Optional[str] = None
        exists = True
        leaves = False
        resolution_error = False
        if not external and target is not None:
            try:
                target_label = relative_label(target, root)
                exists = _safe_is_file(target)
            except ValueError:
                # Keep link findings path-relative and avoid leaking absolute
                # filesystem paths into the JSON maintenance inventory.
                target_label = None
                leaves = True
                exists = False
            except (OSError, RuntimeError):
                target_label = None
                exists = False
                resolution_error = True
        record: Dict[str, Any] = {
            "source": relative_label(path, root),
            "destination": destination,
            "target": target_label,
            "external": external,
            "exists": exists,
            "leaves_vault": leaves,
            "kind": "index" if path.name == "index.md" else "contextual",
        }
        if resolution_error:
            record["resolution_error"] = True
        records.append(record)
    return records


def malformed_links(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if MALFORMED_LINK_PATTERN.search(line)]


def load_vertical_catalog(path: Optional[Path] = None) -> Dict[str, Any]:
    source = (path or catalog_path()).resolve()
    return json.loads(source.read_text(encoding="utf-8"))


def catalog_records(catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = catalog.get("verticals")
    return records if isinstance(records, list) else []


def procedure_header(path: Path) -> Dict[str, Any]:
    text, error = safe_read_text(path)
    if text is None:
        return {"_error": error or "unable to read"}
    fields, errors, _ = parse_frontmatter_text(text)
    if fields is not None and not errors:
        return fields
    header: Dict[str, Any] = {}
    for key in ("vertical_id", "contract_version", "vault_area", "advisor_skill"):
        match = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
        if match:
            header[key] = parse_scalar(match.group(1))
    if errors:
        header["_errors"] = errors
    return header


def validate_vertical_catalog(path: Optional[Path] = None) -> List[str]:
    source = (path or catalog_path()).resolve()
    problems: List[str] = []
    try:
        catalog = load_vertical_catalog(source)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"vertical catalog cannot be loaded: {error}"]

    version = catalog.get("catalog_version")
    if not isinstance(version, int) or version < 1:
        problems.append("vertical catalog has invalid catalog_version")
    records = catalog_records(catalog)
    seen_ids: Dict[str, int] = {}
    seen_areas: Dict[str, str] = {}
    seen_indexes: Dict[str, str] = {}
    seen_contracts: Dict[Tuple[str, int], str] = {}
    root = source.parent.parent
    for number, record in enumerate(records, start=1):
        prefix = f"vertical catalog record {number}"
        if not isinstance(record, dict):
            problems.append(f"{prefix} is not an object")
            continue
        for field in (
            "id",
            "display_name",
            "contract_version",
            "vault_area",
            "index_path",
            "procedure_path",
            "advisor_pack",
            "ownership",
            "exclusions",
            "activation_rule",
        ):
            if field not in record:
                problems.append(f"{prefix} is missing {field}")
        identifier = record.get("id")
        contract_version = record.get("contract_version")
        area = record.get("vault_area")
        index = record.get("index_path")
        if isinstance(identifier, str):
            if identifier in seen_ids:
                problems.append(f"duplicate vertical id: {identifier}")
            seen_ids[identifier] = number
        else:
            problems.append(f"{prefix} has invalid id")
        if not isinstance(contract_version, int) or contract_version < 1:
            problems.append(f"{prefix} has invalid contract_version")
        if isinstance(identifier, str) and isinstance(contract_version, int):
            key = (identifier, contract_version)
            if key in seen_contracts:
                problems.append(
                    f"duplicate vertical contract definition: {identifier}@{contract_version}"
                )
            seen_contracts[key] = prefix
        if isinstance(area, str):
            if area in seen_areas:
                problems.append(f"duplicate vertical area: {area}")
            seen_areas[area] = str(identifier)
            if not area or Path(area).is_absolute() or "/" in area or "\\" in area:
                problems.append(f"{prefix} has unsafe vault_area: {area!r}")
        else:
            problems.append(f"{prefix} has invalid vault_area")
        if isinstance(index, str):
            if index in seen_indexes:
                problems.append(f"duplicate vertical index: {index}")
            seen_indexes[index] = str(identifier)
            if Path(index).is_absolute() or not index.endswith("index.md"):
                problems.append(f"{prefix} has invalid index_path: {index!r}")
        else:
            problems.append(f"{prefix} has invalid index_path")
        procedure = record.get("procedure_path")
        if procedure is None:
            problems.append(f"{prefix} has no procedure_path")
        elif isinstance(procedure, str):
            procedure_file = root / procedure
            if not procedure_file.is_file():
                problems.append(f"{prefix} procedure does not exist: {procedure}")
            else:
                header = procedure_header(procedure_file)
                procedure_text, procedure_error = safe_read_text(procedure_file)
                if procedure_error:
                    problems.append(f"{procedure}: cannot be read: {procedure_error}")
                elif "## Contract migrations" not in (procedure_text or ""):
                    problems.append(f"{procedure}: missing Contract migrations section")
                expected = {
                    "vertical_id": identifier,
                    "contract_version": contract_version,
                    "vault_area": area,
                    "advisor_skill": record.get("advisor_skill", record.get("advisor_pack")),
                }
                for key, expected_value in expected.items():
                    if header.get(key) != expected_value:
                        problems.append(
                            f"{procedure}: {key} does not match catalog ({header.get(key)!r} != {expected_value!r})"
                        )
        else:
            problems.append(f"{prefix} has invalid procedure_path")
        advisor = record.get("advisor_pack")
        if advisor is not None:
            if not isinstance(advisor, str) or not advisor:
                problems.append(f"{prefix} has invalid advisor_pack")
            else:
                advisor_file = root.parent / advisor / "SKILL.md"
                if not advisor_file.is_file():
                    problems.append(f"{prefix} Advisor Pack does not exist: {advisor}")
    if len(records) != len(seen_ids):
        problems.append("vertical catalog contains records without unique ids")
    return problems


def parse_schema(root: Path) -> Dict[str, Any]:
    schema_path = root / "SCHEMA.md"
    text, error = safe_read_text(schema_path)
    result: Dict[str, Any] = {
        "version": None,
        "version_text": None,
        "enabled_contracts": [],
        "contract_entries": [],
        "contract_errors": [],
        "legacy_enabled_verticals": [],
        "error": error,
        "text": text or "",
    }
    if text is None:
        return result
    match = SCHEMA_VERSION_PATTERN.search(text)
    if match:
        result["version"] = (int(match.group(1)), int(match.group(2)))
        result["version_text"] = f"{match.group(1)}.{match.group(2)}"
    contracts: List[Dict[str, Any]] = []
    contract_errors: List[str] = []
    contract_section_present = False
    in_section = False
    for line in text.splitlines():
        section_match = re.match(r"^\s*vertical_contracts:\s*(.*)$", line)
        if section_match:
            contract_section_present = True
            in_section = True
            inline = section_match.group(1).strip()
            if inline and not inline.startswith("#"):
                if inline.startswith("[") and inline.endswith("]"):
                    for token in inline[1:-1].split(","):
                        if token.strip():
                            entry = parse_contract_entry(token)
                            contracts.append(entry)
                            if entry.get("error"):
                                contract_errors.append(str(entry["error"]))
                else:
                    error_message = f"invalid vertical_contracts value: {inline}"
                    contract_errors.append(error_message)
                    contracts.append({"id": None, "version": None, "version_text": "", "raw": inline, "error": error_message})
            continue
        if in_section:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("-"):
                entry = parse_contract_entry(stripped[1:].strip())
                contracts.append(entry)
                if entry.get("error"):
                    contract_errors.append(str(entry["error"]))
                continue
            if line.startswith((" ", "\t")):
                error_message = f"invalid vertical contract entry: {stripped}"
                contract_errors.append(error_message)
                contracts.append({"id": None, "version": None, "version_text": "", "raw": stripped, "error": error_message})
                continue
            in_section = False
    # Legacy vaults may have an explicit enabled_verticals section. Treat it
    # as a conservative signal; prose that merely lists available areas is not
    # enough to enable an absent vertical.
    legacy_enabled: List[str] = []
    legacy_section = False
    for line in text.splitlines():
        if re.match(r"^\s*(?:enabled_verticals|enabled_domains):\s*(?:\[.*\])?\s*$", line):
            legacy_section = True
            inline = line.split(":", 1)[1].strip()
            if inline.startswith("["):
                legacy_enabled.extend(
                    str(item).strip().strip("'\"")
                    for item in inline[1:-1].split(",")
                    if item.strip()
                )
            continue
        if legacy_section:
            if line.strip().startswith("-"):
                value = line.split("-", 1)[1].strip().split("@", 1)[0].strip("'\"")
                if value:
                    legacy_enabled.append(value)
                continue
            if line.strip() and not line.startswith((" ", "\t")):
                legacy_section = False
    result["contract_entries"] = contracts
    result["enabled_contracts"] = list(contracts)
    result["contract_errors"] = contract_errors
    result["legacy_enabled_verticals"] = legacy_enabled
    result["contract_section_present"] = contract_section_present
    return result


def infer_enabled_contracts(
    root: Path, catalog: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], str]:
    catalog = catalog or load_vertical_catalog()
    schema = parse_schema(root)
    try:
        latest = latest_schema_version()
    except (ImportError, OSError, RuntimeError, ValueError):
        latest = None
    if latest is not None and schema.get("version_text") == latest:
        return list(schema["enabled_contracts"]), "schema"
    if schema["version"] != (0, 1):
        # An unrecognized or malformed schema cannot safely identify enabled
        # verticals. Do not infer a migration or a current contract version.
        return [], "unknown-schema"
    root_index_text, _ = safe_read_text(root / "index.md")
    explicit_legacy = {str(identifier) for identifier in schema.get("legacy_enabled_verticals", [])}
    root_index_text = root_index_text or ""
    inferred: List[Dict[str, Any]] = []
    for record in catalog_records(catalog):
        area = record.get("vault_area")
        index = record.get("index_path")
        if not isinstance(area, str) or not isinstance(index, str):
            continue
        if (
            (root / area).is_dir()
            or (root / index).is_file()
            or index in root_index_text
            or str(record.get("id")) in explicit_legacy
        ):
            inferred.append(
                {
                    "id": record.get("id"),
                    "version": record.get("contract_version"),
                }
            )
    return inferred, "inferred-legacy"


def latest_schema_version(registry: Optional[Any] = None) -> str:
    """Return the current schema from the canonical migration registry."""

    migration_registry = registry or _migration_registry_module.default_migration_registry()
    return str(migration_registry.latest_supported_schema)


def supported_schema_versions(registry: Optional[Any] = None) -> List[str]:
    """Return schema versions recognized by the canonical migration registry."""

    migration_registry = registry or _migration_registry_module.default_migration_registry()
    return [str(value) for value in migration_registry.supported_versions]


def _schema_number(value: Any) -> Optional[Tuple[int, int]]:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)", value.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def runtime_compatibility(
    root: Path,
    *,
    registry: Optional[Any] = None,
    catalog: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Inspect whether a vault is safe for current runtime operations.

    Historical schemas and contract versions are intentionally still parsed so
    migration and diagnostics can recognize them.  A result is ``current``
    only when the schema is the registry's latest target and every applied
    contract exactly matches the current catalog.  This is an orientation
    boundary, not a second version field or a migration engine.
    """

    vault = root.expanduser()
    result: Dict[str, Any] = {
        "state": "malformed",
        "ok": False,
        "requires_upgrade": False,
        "blocked": True,
        "schema_state": "malformed",
        "contract_state": "not-checked",
        "schema_version": None,
        "latest_supported_schema": None,
        "applied_contracts": [],
        "older_contracts": [],
        "future_contracts": [],
        "upgrade_source": False,
        "migration_path_available": None,
        "message": "",
    }

    if not vault.exists() or vault.is_symlink() or not vault.is_dir():
        result["message"] = "This vault cannot be safely interpreted. Use the diagnostic or recovery path before normal use."
        return result

    try:
        migration_registry = registry or _migration_registry_module.default_migration_registry()
        latest = latest_schema_version(migration_registry)
        supported = set(supported_schema_versions(migration_registry))
        registry_findings = (
            migration_registry.validation_findings()
            if hasattr(migration_registry, "validation_findings")
            else []
        )
    except Exception as error:
        result["message"] = f"SelfContext compatibility metadata is unavailable: {error}"
        return result

    result["latest_supported_schema"] = latest
    if registry_findings:
        result["message"] = "SelfContext's migration registry is invalid; stop before mutating the vault."
        return result

    schema = parse_schema(vault)
    schema_text = str(schema.get("text") or "")
    declarations = SCHEMA_VERSION_PATTERN.findall(schema_text)
    current = schema.get("version_text")
    result["schema_version"] = current

    if (
        schema.get("error")
        or len(declarations) != 1
        or schema.get("version") is None
        or not isinstance(current, str)
    ):
        result["schema_state"] = "malformed"
        result["state"] = "malformed"
        result["message"] = (
            "This vault's SelfContext schema is malformed or unversioned. "
            "Use the diagnostic or migration recovery path before normal use."
        )
        return result

    if current == latest:
        result["schema_state"] = "current"
    else:
        numeric_current = _schema_number(current)
        numeric_latest = _schema_number(latest)
        if numeric_current and numeric_latest and numeric_current > numeric_latest:
            result["schema_state"] = "future"
            result["state"] = "future-schema"
            result["message"] = (
                f"This vault uses schema {current}, newer than the supported "
                f"SelfContext schema {latest}. Do not downgrade or mutate it. "
                "Update SelfContext before continuing."
            )
            return result
        if current in supported:
            try:
                path = migration_registry.resolve_path(current, "latest")
            except Exception:
                path = []
            result["schema_state"] = "older-supported"
            result["state"] = "older-supported-schema"
            result["requires_upgrade"] = True
            result["upgrade_source"] = True
            result["migration_path_available"] = bool(path)
            if path:
                result["message"] = (
                    f"Legacy SelfContext schema detected: {current}. "
                    f"Current runtime schema: {latest}. This recognized schema is "
                    "a migration source, not a normal runtime target. Run "
                    "`upgrade vault latest` before normal use."
                )
            else:
                result["message"] = (
                    f"Recognized SelfContext schema {current} has no complete "
                    f"migration path to current schema {latest}. Run "
                    "`upgrade vault latest` after the supported upgrade path is "
                    "available; normal use is currently blocked."
                )
            return result

        result["schema_state"] = "unsupported"
        result["state"] = "unsupported-schema"
        result["message"] = (
            f"This vault uses unrecognized schema {current}. Do not guess or "
            "mutate it; use the documented migration or recovery path."
        )
        return result

    # The schema is current.  Contract markers are the second compatibility
    # boundary; absent optional verticals remain valid and disabled.
    try:
        active_catalog = catalog or load_vertical_catalog()
        records = {
            str(record.get("id")): record
            for record in catalog_records(active_catalog)
            if isinstance(record, dict) and record.get("id") is not None
        }
    except (OSError, ValueError, json.JSONDecodeError):
        result["contract_state"] = "malformed"
        result["state"] = "malformed-contract"
        result["message"] = "SelfContext's vertical catalog cannot be read safely; stop before normal use."
        return result

    if not schema.get("contract_section_present") or schema.get("contract_errors"):
        result["contract_state"] = "malformed"
        result["state"] = "malformed-contract"
        result["message"] = (
            "This vault's applied vertical contract state is malformed. "
            "Repair it or run the documented upgrade/migration path before normal use."
        )
        return result

    entries = list(schema.get("contract_entries") or [])
    result["applied_contracts"] = [
        str(item.get("raw") or f"{item.get('id')}@{item.get('version')}")
        for item in entries
    ]
    seen: set[str] = set()
    older: List[str] = []
    future: List[str] = []
    malformed = False
    for entry in entries:
        identifier = entry.get("id")
        version = entry.get("version")
        raw = str(entry.get("raw") or f"{identifier}@{version}")
        if not isinstance(identifier, str) or not isinstance(version, int):
            malformed = True
            continue
        if identifier in seen or identifier not in records:
            malformed = True
            continue
        seen.add(identifier)
        available = records[identifier].get("contract_version")
        if not isinstance(available, int):
            malformed = True
        elif version > available:
            future.append(raw)
        elif version < available:
            older.append(raw)

    result["older_contracts"] = older
    result["future_contracts"] = future
    if malformed:
        result["contract_state"] = "malformed"
        result["state"] = "malformed-contract"
        result["message"] = (
            "This vault's applied vertical contract state is malformed or "
            "unknown. Do not guess or downgrade it; use the documented upgrade path."
        )
        return result
    if future:
        result["contract_state"] = "future"
        result["state"] = "future-contract"
        result["message"] = (
            "This vault uses a newer vertical contract than this repository "
            "supports. Do not downgrade or reinterpret it; update SelfContext first."
        )
        return result
    if older:
        result["contract_state"] = "older-supported"
        result["state"] = "older-contract"
        result["requires_upgrade"] = True
        result["upgrade_source"] = True
        result["message"] = (
            "Older SelfContext vertical contract detected: "
            f"{', '.join(older)}. Current runtime semantics require the current "
            "applied contract. Run `upgrade vault latest` before normal use."
        )
        return result

    result["contract_state"] = "current"
    result["state"] = "current"
    result["ok"] = True
    result["blocked"] = False
    result["message"] = "Vault schema and applied vertical contracts are current."
    return result


def runtime_compatibility_finding(
    compatibility: Mapping[str, Any], path: str = "SCHEMA.md"
) -> Dict[str, Any]:
    """Render one stable validation finding for a non-current runtime state."""

    state = str(compatibility.get("state") or "malformed")
    classification = (
        "runtime-contract"
        if "contract" in state
        else "runtime-schema"
        if "schema" in state
        else "runtime-compatibility"
    )
    return {
        "severity": "error",
        "classification": classification,
        "path": path,
        "message": str(compatibility.get("message") or "vault is not current"),
        "state": state,
        "schema_version": compatibility.get("schema_version"),
        "latest_supported_schema": compatibility.get("latest_supported_schema"),
        "requires_upgrade": bool(compatibility.get("requires_upgrade")),
        "upgrade_source": bool(compatibility.get("upgrade_source")),
    }


def canonical_inventory(root: Path) -> List[Dict[str, str]]:
    inventory: List[Dict[str, str]] = []
    for path in canonical_files(root):
        content, error = safe_read_bytes(path)
        digest = hashlib.sha256(content or b"").hexdigest()
        item: Dict[str, str] = {
            "path": relative_label(path, root),
            "content_hash": digest,
        }
        if error:
            item["read_error"] = error
        inventory.append(item)
    return inventory


def snapshot_id(root: Path) -> str:
    entries = canonical_inventory(root)
    payload = "".join(
        f"{entry['path']}\0{entry['content_hash']}\n" for entry in entries
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def page_record(path: Path, root: Path) -> Dict[str, Any]:
    label = relative_label(path, root)
    content, text, error = _safe_read_page(path)
    record: Dict[str, Any] = {
        "path": label,
        "is_index": path.name == "index.md",
        "is_control": is_control_page(path, root),
        "is_deep_report": is_deep_report(path, root),
        "read_error": error,
    }
    if content is None or text is None:
        record["content_hash"] = hashlib.sha256(b"").hexdigest()
        return record
    record["content_hash"] = hashlib.sha256(content).hexdigest()
    fields, frontmatter_errors, body = parse_frontmatter_text(text)
    record.update(
        {
            "frontmatter": fields,
            "frontmatter_errors": frontmatter_errors,
            "body": body,
            "text": text,
        }
    )
    if isinstance(fields, dict):
        for key in (
            "type",
            "title",
            "description",
            "status",
            "generated",
            "verified",
            "assertion_kind",
            "stale_after",
            "id",
            "aliases",
            "superseded_by",
        ):
            if key in fields:
                record[key] = fields[key]
    return record


def durable_page_records(root: Path, include_reports: bool = False) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in canonical_markdown_files(root):
        if is_control_page(path, root):
            continue
        record = page_record(path, root)
        if record.get("is_deep_report") and not include_reports:
            continue
        records.append(record)
    return records


def nearest_index(path: Path, root: Path) -> Optional[Path]:
    current = path.parent
    resolved_root = root.resolve()
    while True:
        candidate = current / "index.md"
        if candidate.is_file() and not candidate.is_symlink():
            return candidate
        if current.resolve() == resolved_root:
            break
        if current.parent == current:
            break
        current = current.parent
    return None


def body_hash(record: Dict[str, Any]) -> Optional[str]:
    body = record.get("body")
    if not isinstance(body, str) or not body.strip():
        return None
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def first_heading(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1)
    return ""


def index_description(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        if stripped.startswith(("- ", "* ")):
            continue
        lines.append(stripped)
    return " ".join(lines)
