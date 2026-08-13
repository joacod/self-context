#!/usr/bin/env python3
"""Dependency-free, read-only lexical retrieval for a SelfContext vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from vault_utils import (
        canonical_markdown_files,
        durable_page_records,
        is_deep_report,
        normalized_text,
        normalized_tokens,
        parse_schema,
        safe_read_text,
    )
except ImportError:  # pragma: no cover
    from .vault_utils import (  # type: ignore
        canonical_markdown_files,
        durable_page_records,
        is_deep_report,
        normalized_text,
        normalized_tokens,
        parse_schema,
        safe_read_text,
    )


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "where",
    "which",
    "with",
}


def _headings(body: str) -> List[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)
    ]


def _vertical_for_path(path: str, catalog: Optional[Dict[str, Any]]) -> Optional[str]:
    if not catalog:
        return None
    first = Path(path).parts[0] if Path(path).parts else ""
    for record in catalog.get("verticals", []):
        if record.get("vault_area") == first:
            return str(record.get("id"))
    return None


def _snippet(body: str, terms: Sequence[str], limit: int = 220) -> str:
    compact = " ".join(line.strip() for line in body.splitlines() if line.strip())
    if len(compact) <= limit:
        return compact
    lowered = compact.casefold()
    positions = [lowered.find(term.casefold()) for term in terms if lowered.find(term.casefold()) >= 0]
    start = max(0, min(positions or [0]) - 60)
    snippet = compact[start : start + limit].strip()
    if start > 0:
        snippet = "…" + snippet
    if start + limit < len(compact):
        snippet += "…"
    return snippet


def _contains_exact(value: str, query: str) -> bool:
    return normalized_text(value) == normalized_text(query)


def _score_record(record: Dict[str, Any], query: str, query_tokens: Sequence[str]) -> Tuple[int, List[str]]:
    fields = record.get("frontmatter")
    if not isinstance(fields, dict):
        return (0, [])
    identifier = str(fields.get("id") or "")
    title = str(fields.get("title") or "")
    aliases = [str(item) for item in fields.get("aliases", [])] if isinstance(fields.get("aliases"), list) else []
    description = str(fields.get("description") or "")
    tags = [str(item) for item in fields.get("tags", [])] if isinstance(fields.get("tags"), list) else []
    headings = _headings(str(record.get("body") or ""))
    body = str(record.get("body") or "")
    matched: List[str] = []
    score = 0

    exact_id = _contains_exact(identifier, query)
    exact_title_or_alias = _contains_exact(title, query) or any(
        _contains_exact(alias, query) for alias in aliases
    )
    title_alias_tokens = set(normalized_tokens(" ".join([title] + aliases)))
    title_matches = [token for token in query_tokens if token in title_alias_tokens]
    description_tokens = set(normalized_tokens(description + " " + " ".join(tags)))
    description_matches = [token for token in query_tokens if token in description_tokens]
    heading_tokens = set(normalized_tokens(" ".join(headings)))
    heading_matches = [token for token in query_tokens if token in heading_tokens]
    body_tokens = set(normalized_tokens(body))
    body_matches = [token for token in query_tokens if token in body_tokens]

    if exact_id:
        score = 1_000_000_000
        matched.append("id")
    elif exact_title_or_alias:
        score = 900_000_000
        matched.append("title" if _contains_exact(title, query) else "alias")
    elif title_matches:
        score = 700_000_000 + len(title_matches)
        matched.append("title_or_alias")
    elif description_matches:
        score = 500_000_000 + len(description_matches)
        matched.append("description_or_tags")
    elif heading_matches:
        score = 300_000_000 + len(heading_matches)
        matched.append("headings")
    elif body_matches:
        score = 100_000_000 + len(body_matches)
        matched.append("body")

    # Report every field that matched even though ranking uses the strongest
    # matching field only. This keeps ranking deterministic and explainable.
    if description_matches and "description_or_tags" not in matched:
        matched.append("description_or_tags")
    if heading_matches and "headings" not in matched:
        matched.append("headings")
    if body_matches and "body" not in matched:
        matched.append("body")
    return score, matched


def search_vault(
    vault: Path,
    query: str,
    limit: int = 10,
    vertical: Optional[str] = None,
    include_sources: bool = False,
    include_archived: bool = False,
    include_superseded: bool = False,
) -> Dict[str, Any]:
    vault = vault.expanduser()
    if not vault.exists() or vault.is_symlink() or not vault.is_dir():
        return {"query": query, "results": [], "findings": [f"vault is not a real directory: {vault}"]}
    try:
        catalog = json.loads(
            (Path(__file__).resolve().parent.parent / "references" / "verticals.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, json.JSONDecodeError):
        catalog = None
    terms = [token for token in normalized_tokens(query) if token not in STOPWORDS]
    if not terms:
        terms = normalized_tokens(query)
    results: List[Dict[str, Any]] = []
    for record in durable_page_records(vault):
        path = str(record["path"])
        if record.get("is_deep_report") or path.startswith("review/deep-reviews/"):
            continue
        fields = record.get("frontmatter")
        if not isinstance(fields, dict):
            continue
        if vertical and _vertical_for_path(path, catalog) != vertical:
            continue
        assertion = fields.get("assertion_kind")
        if assertion == "source_record" and not include_sources:
            continue
        status = fields.get("status")
        # Archived and superseded pages remain searchable by default, but rank
        # lower below active/review context. The flags are retained as an
        # explicit caller vocabulary and do not remove historical evidence.
        score, matched = _score_record(record, query, terms)
        if score <= 0:
            continue
        # Active concepts outrank raw sources and prior syntheses by default;
        # this is a tie-breaker, never an epistemic reclassification.
        if status == "active":
            score += 2_000
        elif status == "review":
            score += 1_200
        elif status in {"archived", "superseded"}:
            score -= 3_000
        if assertion == "source_record":
            score -= 20
        elif assertion == "derived_synthesis":
            score -= 10
        results.append(
            {
                "path": path,
                "title": fields.get("title"),
                "description": fields.get("description"),
                "status": status,
                "assertion_kind": assertion,
                "matched_fields": matched,
                "vertical": _vertical_for_path(path, catalog),
                "snippet": _snippet(str(record.get("body") or ""), terms),
                "_score": score,
            }
        )
    results.sort(key=lambda item: (-int(item["_score"]), str(item["path"])))
    for item in results:
        item.pop("_score", None)
    return {"query": query, "limit": limit, "results": results[: max(0, limit)], "findings": []}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Search a SelfContext vault lexically")
    parser.add_argument("query", help="query text")
    parser.add_argument("vault", nargs="?", default="vault")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--vertical")
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument("--include-archived", action="store_true")
    parser.add_argument("--include-superseded", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    report = search_vault(
        Path(args.vault),
        args.query,
        limit=args.limit,
        vertical=args.vertical,
        include_sources=args.include_sources,
        include_archived=args.include_archived,
        include_superseded=args.include_superseded,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for finding in report.get("findings", []):
            print(f"ERROR: {finding}")
        for result in report.get("results", []):
            print(
                f"- {result['title']} [{result['status']}] "
                f"({result['path']}): {result['snippet']}"
            )
        if not report.get("results") and not report.get("findings"):
            print("No matching canonical pages")
    return 1 if report.get("findings") else 0


if __name__ == "__main__":
    raise SystemExit(main())
