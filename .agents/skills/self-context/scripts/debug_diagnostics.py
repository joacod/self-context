#!/usr/bin/env python3
"""Closed-enum, privacy-safe SelfContext developer diagnostics.

The helper emits only generated metadata and validated allowlisted values. A
wrapped script is selected from a fixed mapping and inherits stdout/stderr;
those streams, its arguments, and exception text never enter a report.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

FORMAT_VERSION = "1"
DEBUG_DIR_ENV = "SELF_CONTEXT_DEBUG_DIR"
SCRIPT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_ROOT.parents[4]
UNKNOWN = "unknown"

SCRIPT_COMPONENTS = {
    "backup-vault": "backup_vault.py",
    "lint-vault": "lint_vault.py",
    "migrate-vault": "migrate_vault.py",
    "ordinary-commit": "ordinary_commit.py",
    "prepare-context": "prepare_context.py",
    "recent-log": "recent_log.py",
    "search-log": "search_log.py",
    "search-vault": "search_vault.py",
    "sync-indexes": "sync_indexes.py",
}
COMPONENTS = frozenset((*SCRIPT_COMPONENTS, "diagnostic-helper", "harness"))
OPERATIONS = frozenset(
    (
        "query",
        "ingest",
        "checkpoint",
        "lint",
        "review",
        "upgrade",
        "migration",
        "deep-maintenance",
        "advisor",
        UNKNOWN,
    )
)
PHASES = frozenset(
    (
        "session",
        "preflight",
        "context-preparation",
        "retrieval",
        "semantic-processing",
        "proposal",
        "validation",
        "transaction",
        "rollback",
        "backup",
        "response",
        "harness",
        UNKNOWN,
    )
)
EVENTS = frozenset(
    (
        "session-started",
        "session-completed",
        "session-incomplete",
        "script-started",
        "script-succeeded",
        "script-failed",
        "script-timeout",
        "tool-input-rejected",
        "tool-call-failed",
        "edit-mismatch",
        "retry-started",
        "output-contract-invalid",
        "unexpected-noop",
        "unexpected-behavior",
        "receipt-failed",
        "validation-failed",
        "rollback-failed",
        "backup-failed",
    )
)
STATUSES = frozenset(("complete", "partial", "failed", UNKNOWN))
FINDING_CLASSIFICATIONS = frozenset(
    (
        "backup",
        "contract",
        "filesystem",
        "freshness",
        "link",
        "metadata",
        "ownership",
        "provenance",
        "reachability",
        "runtime",
        "schema",
        "transaction",
        UNKNOWN,
    )
)
EVENT_FIELDS = frozenset(
    (
        "event",
        "component",
        "phase",
        "operation",
        "attempt",
        "exit_code",
        "duration_ms",
        "finding_counts",
        "validation_ok",
        "rollback_ok",
        "provisional_backup_ok",
        "final_backup_ok",
        "retry_count",
        "failure_count",
        "status",
    )
)

_FILENAME_PATTERN = re.compile(
    r"^self-context-debug-(?P<timestamp>\d{8}T\d{6}Z)-(?P<session>[0-9a-f]{16})\.md$"
)
_EVENT_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
)
_PYTHON_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
HARNESSES = frozenset(("opencode", "codex", "claude-code", "other", UNKNOWN))
PLATFORMS = frozenset(("linux", "darwin", "windows", UNKNOWN))
_MAX_NUMBER = 1_000_000_000
_MAX_EXIT_CODE = 2_147_483_647
_MAX_TIMEOUT_MS = 3_600_000


class DiagnosticError(ValueError):
    """Raised when a safe diagnostic operation cannot be completed."""


def _reject(condition: bool, message: str = "unsupported diagnostic input") -> None:
    if condition:
        raise DiagnosticError(message)


def _enum(value: Any, allowed: frozenset[str], label: str) -> str:
    _reject(not isinstance(value, str) or value not in allowed, f"invalid {label}")
    return value


def _number(
    value: Any, *, label: str, minimum: int = 0, maximum: int = _MAX_NUMBER
) -> int:
    _reject(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
        or value > maximum,
        f"invalid {label}",
    )
    return value


def _finding_counts(value: Any) -> Dict[str, int]:
    _reject(
        not isinstance(value, Mapping)
        or isinstance(value, (str, bytes, bytearray)),
        "invalid finding counts",
    )
    result = {}
    for key, count in value.items():
        _enum(key, FINDING_CLASSIFICATIONS, "finding classification")
        result[key] = _number(count, label="finding count")
    return dict(sorted(result.items()))


def _normalize_event(fields: Mapping[str, Any]) -> Dict[str, Any]:
    _reject(
        not isinstance(fields, Mapping)
        or isinstance(fields, (str, bytes, bytearray)),
        "invalid event",
    )
    _reject(bool(set(fields) - EVENT_FIELDS), "unsupported diagnostic field")
    result: Dict[str, Any] = {
        "event": _enum(fields.get("event"), EVENTS, "event"),
        "component": _enum(fields.get("component"), COMPONENTS, "component"),
        "phase": _enum(fields.get("phase"), PHASES, "phase"),
        "operation": _enum(fields.get("operation", UNKNOWN), OPERATIONS, "operation"),
        "attempt": _number(fields.get("attempt", 1), label="attempt", minimum=1),
    }
    for field, minimum, maximum in (
        ("exit_code", -_MAX_EXIT_CODE, _MAX_EXIT_CODE),
        ("duration_ms", 0, _MAX_NUMBER),
        ("retry_count", 0, _MAX_NUMBER),
        ("failure_count", 0, _MAX_NUMBER),
    ):
        if field in fields:
            result[field] = _number(
                fields[field], label=field, minimum=minimum, maximum=maximum
            )
    if "finding_counts" in fields:
        result["finding_counts"] = _finding_counts(fields["finding_counts"])
    for field in (
        "validation_ok",
        "rollback_ok",
        "provisional_backup_ok",
        "final_backup_ok",
    ):
        if field in fields:
            _reject(not isinstance(fields[field], bool), f"invalid {field}")
            result[field] = fields[field]
    if "status" in fields:
        result["status"] = _enum(fields["status"], STATUSES, "status")
    return result


def _expanduser(value: Path, error: str) -> Path:
    try:
        return value.expanduser()
    except (OSError, RuntimeError) as cause:
        raise DiagnosticError(error) from cause


def _repository_root(value: Path) -> Path:
    candidate = _expanduser(value, "invalid repository root")
    _reject(candidate.is_symlink(), "invalid repository root")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise DiagnosticError("invalid repository root") from error
    _reject(not resolved.is_dir(), "invalid repository root")
    return resolved


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _destination(output_dir: Optional[Path]) -> Path:
    if output_dir is not None:
        return _expanduser(output_dir, "invalid diagnostic directory")
    configured = os.environ.get(DEBUG_DIR_ENV)
    if configured is not None:
        _reject(not configured.strip(), "invalid diagnostic directory")
        return _expanduser(Path(configured), "invalid diagnostic directory")
    return _expanduser(Path.home() / "Downloads", "invalid diagnostic directory")


def _permissions(path: Path, mode: int) -> None:
    if os.name != "posix":
        return
    try:
        os.chmod(path, mode)
    except OSError as error:
        raise DiagnosticError("could not apply diagnostic permissions") from error

def _output_dir(path: Path, root: Path, *, create: bool) -> Path:
    candidate = _expanduser(path, "invalid diagnostic directory")
    try:
        if candidate.is_symlink():
            raise DiagnosticError("invalid diagnostic directory")
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise DiagnosticError("invalid diagnostic directory") from error
    _reject(_inside(resolved, root), "invalid diagnostic directory")
    created = False
    if create:
        created = not candidate.exists()
        try:
            candidate.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as error:
            raise DiagnosticError("could not create diagnostic directory") from error
    _reject(candidate.is_symlink(), "invalid diagnostic directory")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise DiagnosticError("invalid diagnostic directory") from error
    _reject(not resolved.is_dir() or _inside(resolved, root), "invalid diagnostic directory")
    if created:
        _permissions(resolved, 0o700)
    return resolved


def _repository_sha(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return UNKNOWN
    value = result.stdout.strip().lower()
    return value if result.returncode == 0 and _SHA_PATTERN.fullmatch(value) else UNKNOWN


def _timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _event_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _platform() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("win"):
        return "windows"
    return UNKNOWN


def _filename(timestamp: str, session_id: str) -> str:
    _reject(not re.fullmatch(r"\d{8}T\d{6}Z", timestamp), "invalid timestamp")
    _reject(not re.fullmatch(r"[0-9a-f]{16}", session_id), "invalid session id")
    return f"self-context-debug-{timestamp}-{session_id}.md"


def _flags(base: int) -> int:
    return base | getattr(os, "O_NOFOLLOW", 0)


def _new_file(path: Path, content: str) -> None:
    try:
        descriptor = os.open(
            path, _flags(os.O_WRONLY | os.O_CREAT | os.O_EXCL), 0o600
        )
    except FileExistsError:
        raise
    except OSError as error:
        raise DiagnosticError("could not create diagnostic report") from error
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except (OSError, UnicodeError) as error:
        try:
            path.unlink()
        except OSError:
            pass
        raise DiagnosticError("could not write diagnostic report") from error
    _permissions(path, 0o600)


def _append_file(path: Path, content: str) -> None:
    try:
        descriptor = os.open(path, _flags(os.O_WRONLY | os.O_APPEND))
    except OSError as error:
        raise DiagnosticError("could not append diagnostic report") from error
    try:
        with os.fdopen(descriptor, "a", encoding="ascii", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except (OSError, UnicodeError) as error:
        raise DiagnosticError("could not append diagnostic report") from error
    _permissions(path, 0o600)


def _header(root: Path, session_id: str, started_at: str, harness: str) -> str:
    return (
        "# SelfContext debug report\n\n"
        f"format_version: {FORMAT_VERSION}\n"
        f"session_id: {session_id}\n"
        f"started_at: {started_at}\n"
        f"repository_sha: {_repository_sha(root)}\n"
        f"python_version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
        f"platform: {_platform()}\n"
        f"harness: {harness}\n\n"
    )


def _render_event(fields: Mapping[str, Any]) -> str:
    event = _normalize_event(fields)
    lines = [
        "## Event\n",
        f"timestamp: {_event_timestamp()}\n",
        f"event: {event['event']}\n",
        f"component: {event['component']}\n",
        f"phase: {event['phase']}\n",
        f"operation: {event['operation']}\n",
        f"attempt: {event['attempt']}\n",
    ]
    for field in ("status", "exit_code", "duration_ms"):
        if field in event:
            lines.append(f"{field}: {event[field]}\n")
    for field in (
        "validation_ok",
        "rollback_ok",
        "provisional_backup_ok",
        "final_backup_ok",
    ):
        if field in event:
            lines.append(f"{field}: {str(event[field]).lower()}\n")
    for field in ("retry_count", "failure_count"):
        if field in event:
            lines.append(f"{field}: {event[field]}\n")
    if "finding_counts" in event:
        counts = ",".join(
            f"{key}={value}" for key, value in event["finding_counts"].items()
        )
        lines.append(f"finding_counts: {counts}\n")
    return "".join(lines) + "\n"


def _parse_event_value(key: str, value: str) -> Any:
    if key in {"event", "component", "phase", "operation", "status"}:
        return value
    if key in {
        "attempt",
        "exit_code",
        "duration_ms",
        "retry_count",
        "failure_count",
    }:
        _reject(not re.fullmatch(r"-?\d+", value), "invalid diagnostic report")
        return int(value)
    if key in {
        "validation_ok",
        "rollback_ok",
        "provisional_backup_ok",
        "final_backup_ok",
    }:
        _reject(value not in {"true", "false"}, "invalid diagnostic report")
        return value == "true"
    if key == "finding_counts":
        if not value:
            return {}
        counts: Dict[str, int] = {}
        for item in value.split(","):
            _reject(item.count("=") != 1, "invalid diagnostic report")
            finding, raw_count = item.split("=")
            _enum(finding, FINDING_CLASSIFICATIONS, "finding classification")
            _reject(finding in counts, "invalid diagnostic report")
            _reject(not re.fullmatch(r"\d+", raw_count), "invalid diagnostic report")
            counts[finding] = int(raw_count)
        return counts
    raise DiagnosticError("invalid diagnostic report")


def _validate_report_contents(path: Path, filename: re.Match[str]) -> None:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise DiagnosticError("invalid diagnostic report") from error
    _reject(len(lines) < 11, "invalid diagnostic report")
    _reject(lines[0:2] != ["# SelfContext debug report", ""], "invalid diagnostic report")
    header: Dict[str, str] = {}
    for line in lines[2:9]:
        _reject(": " not in line, "invalid diagnostic report")
        key, value = line.split(": ", 1)
        _reject(key in header, "invalid diagnostic report")
        header[key] = value
    _reject(
        set(header)
        != {
            "format_version",
            "session_id",
            "started_at",
            "repository_sha",
            "python_version",
            "platform",
            "harness",
        },
        "invalid diagnostic report",
    )
    _reject(header["format_version"] != FORMAT_VERSION, "invalid diagnostic report")
    _reject(header["session_id"] != filename.group("session"), "invalid diagnostic report")
    _reject(header["started_at"] != filename.group("timestamp"), "invalid diagnostic report")
    _reject(
        header["repository_sha"] != UNKNOWN
        and not _SHA_PATTERN.fullmatch(header["repository_sha"]),
        "invalid diagnostic report",
    )
    _reject(
        not _PYTHON_VERSION_PATTERN.fullmatch(header["python_version"]),
        "invalid diagnostic report",
    )
    _enum(header["platform"], PLATFORMS, "platform")
    _enum(header["harness"], HARNESSES, "harness")
    _reject(lines[9] != "", "invalid diagnostic report")

    index = 10
    event_seen = False
    while index < len(lines):
        _reject(lines[index] != "## Event", "invalid diagnostic report")
        event_seen = True
        index += 1
        timestamp_line = lines[index]
        _reject(
            not timestamp_line.startswith("timestamp: "),
            "invalid diagnostic report",
        )
        _reject(
            not _EVENT_TIMESTAMP_PATTERN.fullmatch(timestamp_line[11:]),
            "invalid diagnostic report",
        )
        index += 1
        fields: Dict[str, Any] = {}
        while index < len(lines) and lines[index] not in {"## Event", ""}:
            line = lines[index]
            _reject(": " not in line, "invalid diagnostic report")
            key, value = line.split(": ", 1)
            _reject(key in fields or key == "timestamp", "invalid diagnostic report")
            fields[key] = _parse_event_value(key, value)
            index += 1
        _normalize_event(fields)
        if index < len(lines) and lines[index] == "":
            index += 1


def _report_path(report: Path, root: Path) -> Path:
    candidate = _expanduser(report, "invalid diagnostic report")
    filename = _FILENAME_PATTERN.fullmatch(candidate.name)
    _reject(filename is None, "invalid diagnostic report")
    try:
        if candidate.is_symlink() or not candidate.is_file():
            raise DiagnosticError("invalid diagnostic report")
        parent = candidate.parent.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise DiagnosticError("invalid diagnostic report") from error
    _output_dir(parent, root, create=False)
    _validate_report_contents(candidate, filename)
    return parent / candidate.name


def start_session(
    *,
    output_dir: Optional[Path] = None,
    repository_root: Path = PROJECT_ROOT,
    harness: str = UNKNOWN,
) -> Path:
    """Create an incremental report and return its safe filename path."""

    root = _repository_root(repository_root)
    harness = _enum(harness, HARNESSES, "harness")
    destination = _output_dir(_destination(output_dir), root, create=True)
    for _ in range(8):
        timestamp = _timestamp()
        session_id = secrets.token_hex(8)
        report = destination / _filename(timestamp, session_id)
        initial = _header(root, session_id, timestamp, harness) + _render_event(
            {
                "event": "session-started",
                "component": "diagnostic-helper",
                "phase": "session",
                "operation": UNKNOWN,
                "status": "partial",
            }
        )
        try:
            _new_file(report, initial)
        except FileExistsError:
            continue
        return report
    raise DiagnosticError("could not allocate diagnostic report")


def append_event(
    report: Path,
    fields: Mapping[str, Any],
    *,
    repository_root: Path = PROJECT_ROOT,
) -> None:
    """Append one event after validating every field and value."""

    root = _repository_root(repository_root)
    target = _report_path(report, root)
    _append_file(target, _render_event(fields))


def finish_session(
    report: Path,
    *,
    status: str,
    operation: str = UNKNOWN,
    duration_ms: Optional[int] = None,
    retry_count: Optional[int] = None,
    failure_count: Optional[int] = None,
    validation_ok: Optional[bool] = None,
    rollback_ok: Optional[bool] = None,
    provisional_backup_ok: Optional[bool] = None,
    final_backup_ok: Optional[bool] = None,
    repository_root: Path = PROJECT_ROOT,
) -> None:
    """Append a fixed complete or incomplete session event."""

    status = _enum(status, STATUSES, "status")
    fields: Dict[str, Any] = {
        "event": "session-completed" if status == "complete" else "session-incomplete",
        "component": "diagnostic-helper",
        "phase": "session",
        "operation": _enum(operation, OPERATIONS, "operation"),
        "status": status,
    }
    for name, value in (
        ("duration_ms", duration_ms),
        ("retry_count", retry_count),
        ("failure_count", failure_count),
        ("validation_ok", validation_ok),
        ("rollback_ok", rollback_ok),
        ("provisional_backup_ok", provisional_backup_ok),
        ("final_backup_ok", final_backup_ok),
    ):
        if value is not None:
            fields[name] = value
    append_event(report, fields, repository_root=repository_root)


def run_wrapped(
    report: Path,
    *,
    component: str,
    phase: str,
    operation: str = UNKNOWN,
    script_args: Sequence[str] = (),
    attempt: int = 1,
    timeout_ms: Optional[int] = None,
    repository_root: Path = PROJECT_ROOT,
) -> int:
    """Run one mapped SelfContext script without capturing its output."""

    root = _repository_root(repository_root)
    component = _enum(component, frozenset(SCRIPT_COMPONENTS), "component")
    phase = _enum(phase, PHASES, "phase")
    operation = _enum(operation, OPERATIONS, "operation")
    attempt = _number(attempt, label="attempt", minimum=1)
    if timeout_ms is not None:
        _number(timeout_ms, label="timeout", maximum=_MAX_TIMEOUT_MS)
    _reject(any(not isinstance(argument, str) for argument in script_args), "invalid script arguments")
    script = SCRIPT_ROOT / SCRIPT_COMPONENTS[component]
    _reject(not script.is_file() or script.is_symlink(), "invalid SelfContext component")

    common = {
        "component": component,
        "phase": phase,
        "operation": operation,
        "attempt": attempt,
    }
    append_event(report, {"event": "script-started", **common}, repository_root=root)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [sys.executable, str(script), *script_args],
            cwd=str(root),
            check=False,
            timeout=None if timeout_ms is None else timeout_ms / 1000,
        )
    except subprocess.TimeoutExpired:
        result = {"event": "script-timeout", **common, "exit_code": 124}
        result["duration_ms"] = max(0, int((time.monotonic() - started) * 1000))
        try:
            append_event(report, result, repository_root=root)
        except DiagnosticError:
            print("SelfContext debug diagnostics unavailable", file=sys.stderr)
        return 124
    except (OSError, ValueError, subprocess.SubprocessError):
        result = {"event": "tool-call-failed", **common}
        result["duration_ms"] = max(0, int((time.monotonic() - started) * 1000))
        try:
            append_event(report, result, repository_root=root)
        except DiagnosticError:
            print("SelfContext debug diagnostics unavailable", file=sys.stderr)
        return 1

    result = {
        "event": "script-succeeded" if completed.returncode == 0 else "script-failed",
        **common,
        "exit_code": completed.returncode,
        "duration_ms": max(0, int((time.monotonic() - started) * 1000)),
    }
    try:
        append_event(report, result, repository_root=root)
    except DiagnosticError:
        print("SelfContext debug diagnostics unavailable", file=sys.stderr)
    return completed.returncode


def _bool_arg(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError("must be true or false")


def _int_arg(value: str, *, minimum: int = 0, maximum: int = _MAX_NUMBER) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed < minimum or parsed > maximum:
        raise argparse.ArgumentTypeError("integer is outside the supported range")
    return parsed


def _finding_arg(value: str) -> Tuple[str, int]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("must use classification=count")
    key, raw_count = value.split("=", 1)
    if key not in FINDING_CLASSIFICATIONS:
        raise argparse.ArgumentTypeError("unsupported finding classification")
    return key, _int_arg(raw_count)


def _event_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--report", required=True)
    parser.add_argument("--component", choices=sorted(COMPONENTS), required=True)
    parser.add_argument("--phase", choices=sorted(PHASES), required=True)
    parser.add_argument("--operation", choices=sorted(OPERATIONS), default=UNKNOWN)
    parser.add_argument("--attempt", type=lambda value: _int_arg(value, minimum=1), default=1)
    parser.add_argument(
        "--exit-code",
        type=lambda value: _int_arg(
            value, minimum=-_MAX_EXIT_CODE, maximum=_MAX_EXIT_CODE
        ),
    )
    parser.add_argument("--duration-ms", type=_int_arg)
    parser.add_argument("--finding-count", type=_finding_arg, action="append", default=[])
    for name in ("validation_ok", "rollback_ok", "provisional_backup_ok", "final_backup_ok"):
        parser.add_argument(f"--{name.replace('_', '-')}", type=_bool_arg)
    parser.add_argument("--retry-count", type=_int_arg)
    parser.add_argument("--failure-count", type=_int_arg)
    parser.add_argument("--status", choices=sorted(STATUSES))


def _event_fields(args: argparse.Namespace) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
        "event": args.event,
        "component": args.component,
        "phase": args.phase,
        "operation": args.operation,
        "attempt": args.attempt,
    }
    for name in (
        "exit_code",
        "duration_ms",
        "validation_ok",
        "rollback_ok",
        "provisional_backup_ok",
        "final_backup_ok",
        "retry_count",
        "failure_count",
        "status",
    ):
        value = getattr(args, name, None)
        if value is not None:
            fields[name] = value
    if args.finding_count:
        fields["finding_counts"] = dict(args.finding_count)
    return fields


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SelfContext developer diagnostics")
    commands = parser.add_subparsers(dest="command", required=True)

    start = commands.add_parser("start", help="create an incremental report")
    start.add_argument(
        "--harness",
        choices=("opencode", "codex", "claude-code", "other", UNKNOWN),
        default=UNKNOWN,
    )

    event = commands.add_parser("event", help="append one closed-enum event")
    _event_options(event)
    event.add_argument("--event", choices=sorted(EVENTS), required=True)

    finish = commands.add_parser("finish", help="append a fixed session status")
    finish.add_argument("--report", required=True)
    finish.add_argument("--status", choices=sorted(STATUSES), required=True)
    finish.add_argument("--operation", choices=sorted(OPERATIONS), default=UNKNOWN)
    finish.add_argument("--duration-ms", type=_int_arg)
    finish.add_argument("--retry-count", type=_int_arg)
    finish.add_argument("--failure-count", type=_int_arg)
    for name in ("validation_ok", "rollback_ok", "provisional_backup_ok", "final_backup_ok"):
        finish.add_argument(f"--{name.replace('_', '-')}", type=_bool_arg)

    run = commands.add_parser("run", help="run one mapped SelfContext script")
    run.add_argument("--report", required=True)
    run.add_argument("--component", choices=sorted(SCRIPT_COMPONENTS), required=True)
    run.add_argument("--phase", choices=sorted(PHASES), required=True)
    run.add_argument("--operation", choices=sorted(OPERATIONS), default=UNKNOWN)
    run.add_argument("--attempt", type=lambda value: _int_arg(value, minimum=1), default=1)
    run.add_argument("--timeout-ms", type=_int_arg)
    run.add_argument("script_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "start":
            print(start_session(harness=args.harness))
            return 0
        if args.command == "event":
            append_event(Path(args.report), _event_fields(args))
            return 0
        if args.command == "finish":
            finish_session(
                Path(args.report),
                status=args.status,
                operation=args.operation,
                duration_ms=args.duration_ms,
                retry_count=args.retry_count,
                failure_count=args.failure_count,
                validation_ok=args.validation_ok,
                rollback_ok=args.rollback_ok,
                provisional_backup_ok=args.provisional_backup_ok,
                final_backup_ok=args.final_backup_ok,
            )
            return 0
        script_args = list(args.script_args)
        if script_args and script_args[0] == "--":
            script_args.pop(0)
        return run_wrapped(
            Path(args.report),
            component=args.component,
            phase=args.phase,
            operation=args.operation,
            script_args=script_args,
            attempt=args.attempt,
            timeout_ms=args.timeout_ms,
        )
    except (DiagnosticError, OSError, RuntimeError):
        print("SelfContext debug diagnostics unavailable", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
