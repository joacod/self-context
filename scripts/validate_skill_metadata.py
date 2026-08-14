#!/usr/bin/env python3
"""Validate tracked Agent Skill metadata without third-party dependencies."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION_MAX_CHARS = 1024
DESCRIPTION_WARNING_CHARS = 900
NAME_MAX_CHARS = 64
COMPATIBILITY_MAX_CHARS = 500
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BLOCK_SCALAR_MARKERS = {">", "|", ">-", "|-", ">+", "|+"}


def tracked_skill_paths(root: Path = ROOT) -> List[Path]:
    """Return tracked project skill entry points."""

    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(detail or "git ls-files failed")

    paths: List[Path] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(os.fsdecode(raw_path))
        if (
            len(relative.parts) == 4
            and relative.parts[:2] == (".agents", "skills")
            and relative.name == "SKILL.md"
        ):
            paths.append(root / relative)
    return sorted(paths)


def _frontmatter_lines(text: str) -> List[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index]
    raise ValueError("frontmatter has no closing ---")


def _block_scalar_value(style: str, lines: List[str]) -> str:
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return ""

    indent = min(len(line) - len(line.lstrip()) for line in non_empty)
    content = [line[indent:] if line.strip() else "" for line in lines]
    if style.startswith("|"):
        return "\n".join(content)

    folded: List[str] = []
    for index, line in enumerate(content):
        folded.append(line)
        if index == len(content) - 1:
            continue
        next_line = content[index + 1]
        folded.append("\n" if not line or not next_line else " ")
    return "".join(folded)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) < 2 or value[0] != value[-1] or value[0] not in {"'", '"'}:
        return value
    if value[0] == "'":
        return value[1:-1].replace("''", "'")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value[1:-1]
    return parsed if isinstance(parsed, str) else value[1:-1]


def parse_frontmatter(text: str) -> Dict[str, str]:
    """Parse the small frontmatter subset used by project Agent Skills."""

    lines = _frontmatter_lines(text)
    values: Dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line[0].isspace() or ":" not in line:
            raise ValueError(f"malformed frontmatter line: {line!r}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise ValueError("frontmatter contains an empty field name")

        if raw_value in BLOCK_SCALAR_MARKERS:
            index += 1
            block_lines: List[str] = []
            while index < len(lines):
                candidate = lines[index]
                if not candidate.strip():
                    block_lines.append("")
                    index += 1
                    continue
                if not candidate[0].isspace():
                    break
                block_lines.append(candidate)
                index += 1
            values[key] = _block_scalar_value(raw_value, block_lines)
            continue

        continuations: List[str] = []
        lookahead = index + 1
        while lookahead < len(lines):
            candidate = lines[lookahead]
            if not candidate.strip():
                break
            if not candidate[0].isspace():
                break
            continuations.append(candidate.strip())
            lookahead += 1
        if continuations:
            raw_value = " ".join([raw_value, *continuations]).strip()
            index = lookahead
        else:
            index += 1
        values[key] = _unquote(raw_value)

    return values


def validate_skill_text(label: str, text: str) -> Tuple[List[str], List[str]]:
    """Return hard failures and advisory warnings for one skill file."""

    problems: List[str] = []
    warnings: List[str] = []
    try:
        metadata = parse_frontmatter(text)
    except (ValueError, UnicodeError) as error:
        return [f"{label}: {error}"], warnings

    name = metadata.get("name", "").strip()
    if not name:
        problems.append(f"{label}: missing name")
    elif len(name) > NAME_MAX_CHARS:
        problems.append(f"{label}: name exceeds {NAME_MAX_CHARS} characters")
    elif not NAME_PATTERN.fullmatch(name):
        problems.append(f"{label}: name is not kebab-case: {name!r}")

    description = metadata.get("description", "").strip()
    if not description:
        problems.append(f"{label}: missing description")
    else:
        if "<" in description or ">" in description:
            problems.append(f"{label}: description contains angle brackets")
        description_length = len(description)
        if description_length > DESCRIPTION_MAX_CHARS:
            problems.append(
                f"{label}: description is {description_length} characters; "
                f"maximum is {DESCRIPTION_MAX_CHARS}"
            )
        elif description_length > DESCRIPTION_WARNING_CHARS:
            warnings.append(
                f"{label}: description is {description_length} characters; "
                f"recommended budget is {DESCRIPTION_WARNING_CHARS}"
            )

    compatibility = metadata.get("compatibility", "").strip()
    if len(compatibility) > COMPATIBILITY_MAX_CHARS:
        problems.append(
            f"{label}: compatibility is {len(compatibility)} characters; "
            f"maximum is {COMPATIBILITY_MAX_CHARS}"
        )

    return problems, warnings


def validate_skill_metadata(
    root: Path = ROOT,
) -> Tuple[List[Path], List[str], List[str]]:
    """Validate all tracked project skill entry points."""

    paths = tracked_skill_paths(root)
    problems: List[str] = []
    warnings: List[str] = []
    for path in paths:
        label = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            problems.append(f"{label}: unable to read metadata: {error}")
            continue
        file_problems, file_warnings = validate_skill_text(label, text)
        problems.extend(file_problems)
        warnings.extend(file_warnings)
    return paths, problems, warnings


def main() -> int:
    try:
        paths, problems, warnings = validate_skill_metadata()
    except Exception as error:
        print(f"[FAIL] skill metadata validation failed: {type(error).__name__}: {error}")
        return 1

    for warning in warnings:
        print(f"[WARN] skill metadata: {warning}")
    if problems:
        for problem in problems:
            print(f"[FAIL] skill metadata: {problem}")
        return 1

    print(
        f"[PASS] skill metadata: {len(paths)} skill files checked "
        f"(maximum description {DESCRIPTION_MAX_CHARS}; "
        f"recommended budget {DESCRIPTION_WARNING_CHARS})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
