#!/usr/bin/env python3
"""Dependency-free, read-only lexical retrieval for a SelfContext vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

try:
    from vault_utils import (
        durable_page_records,
        is_external,
        link_target,
        normalized_text,
        normalized_tokens,
        runtime_compatibility,
    )
except ImportError:  # pragma: no cover
    from .vault_utils import (  # type: ignore
        durable_page_records,
        is_external,
        link_target,
        normalized_text,
        normalized_tokens,
        runtime_compatibility,
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

# The lexical score is deliberately a transparent ordering heuristic. Coverage
# is the largest component so one incidental title token cannot beat a page
# that matches most of a task query. Field, phrase, and proximity components
# then make similarly covered pages inspectably different.
FIELD_WEIGHTS = {
    "title_or_alias": 100,
    "description_or_tags": 55,
    "headings": 45,
    "body": 30,
}
FIELD_ORDER = tuple(FIELD_WEIGHTS)
STATUS_ADJUSTMENTS = {
    "active": 50_000,
    "review": 25_000,
    "draft": 5_000,
    "archived": -50_000,
    "superseded": -60_000,
}
TYPE_ADJUSTMENTS = {
    "concept": 2_000,
    "observation": 1_000,
    "synthesis": -10_000,
    "source": -3_000_000,
}


def _headings(body: str) -> List[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)
    ]


def _body_without_headings(body: str) -> str:
    return "\n".join(
        line for line in body.splitlines() if not re.match(r"^#{1,6}\s+", line)
    )


@dataclass(frozen=True)
class _IndexedRecord:
    record: Dict[str, Any]
    normalized_identifier: str
    normalized_title: str
    normalized_aliases: Tuple[str, ...]
    field_token_lists: Dict[str, Tuple[Tuple[str, ...], ...]]
    field_token_sets: Dict[str, FrozenSet[str]]


@dataclass(frozen=True)
class _SearchCorpus:
    vault: Path
    catalog: Optional[Dict[str, Any]]
    records: Tuple[_IndexedRecord, ...]
    records_by_path: Dict[str, Dict[str, Any]]


def _index_record(record: Dict[str, Any]) -> _IndexedRecord:
    fields = record.get("frontmatter")
    if not isinstance(fields, dict):
        return _IndexedRecord(record, "", "", (), {}, {})

    identifier = str(fields.get("id") or "")
    title = str(fields.get("title") or "")
    aliases = tuple(
        str(item)
        for item in fields.get("aliases", [])
        if item is not None and str(item).strip()
    ) if isinstance(fields.get("aliases"), list) else ()
    description = str(fields.get("description") or "")
    tags = tuple(
        str(item)
        for item in fields.get("tags", [])
        if item is not None and str(item).strip()
    ) if isinstance(fields.get("tags"), list) else ()
    body = str(record.get("body") or "")
    headings = _headings(body)
    body_without_headings = _body_without_headings(body)
    field_values: Dict[str, List[str]] = {
        "title_or_alias": [title] + list(aliases),
        "description_or_tags": [description] + list(tags),
        "headings": headings,
        "body": [body_without_headings],
    }
    field_token_lists = {
        field: tuple(tuple(normalized_tokens(value)) for value in values)
        for field, values in field_values.items()
    }
    field_token_sets = {
        field: frozenset(token for tokens in values for token in tokens)
        for field, values in field_token_lists.items()
    }
    return _IndexedRecord(
        record=record,
        normalized_identifier=normalized_text(identifier),
        normalized_title=normalized_text(title),
        normalized_aliases=tuple(normalized_text(alias) for alias in aliases),
        field_token_lists=field_token_lists,
        field_token_sets=field_token_sets,
    )


def _load_vertical_catalog() -> Optional[Dict[str, Any]]:
    try:
        return json.loads(
            (Path(__file__).resolve().parent.parent / "references" / "verticals.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _build_search_corpus(vault: Path) -> _SearchCorpus:
    records = tuple(durable_page_records(vault))
    records_by_path = {
        str(record.get("path")): record for record in records if record.get("path")
    }
    indexed_records = tuple(_index_record(record) for record in records)
    return _SearchCorpus(
        vault=vault,
        catalog=_load_vertical_catalog(),
        records=indexed_records,
        records_by_path=records_by_path,
    )


def _vertical_for_path(path: str, catalog: Optional[Dict[str, Any]]) -> Optional[str]:
    if not catalog:
        return None
    first = Path(path).parts[0] if Path(path).parts else ""
    for record in catalog.get("verticals", []):
        if record.get("vault_area") == first:
            return str(record.get("id"))
    return None


def _normalize_scopes(scope: Optional[Sequence[str]]) -> Tuple[List[str], List[str]]:
    """Normalize explicit vault-relative retrieval scopes without guessing intent."""

    if not scope:
        return [], []
    values: List[str] = []
    findings: List[str] = []
    for raw in scope:
        value = str(raw).strip().replace("\\", "/")
        while value.startswith("./"):
            value = value[2:]
        value = value.rstrip("/")
        parts = Path(value).parts if value else ()
        if not value or Path(value).is_absolute() or ".." in parts:
            findings.append(f"invalid retrieval scope: {raw!r}; use a vault-relative area or path")
            continue
        if value not in values:
            values.append(value)
    return values, findings


def normalize_scopes(scope: Optional[Sequence[str]]) -> Tuple[List[str], List[str]]:
    """Expose the search scope normalization for read-only composition helpers."""

    return _normalize_scopes(scope)


def _path_matches_scope(path: str, scopes: Sequence[str]) -> bool:
    return not scopes or any(path == scope or path.startswith(scope + "/") for scope in scopes)


def _linked_source_paths(
    record: Dict[str, Any], vault: Path, records_by_path: Dict[str, Dict[str, Any]]
) -> List[str]:
    """Return existing source-record links from a canonical page's frontmatter."""

    fields = record.get("frontmatter")
    if not isinstance(fields, dict):
        return []
    raw_sources = fields.get("sources", [])
    if isinstance(raw_sources, str):
        raw_sources = [raw_sources]
    if not isinstance(raw_sources, list):
        return []

    page = vault / str(record.get("path") or "")
    linked: List[str] = []
    for raw_source in raw_sources:
        destination = str(raw_source).strip()
        if not destination or is_external(destination):
            continue
        target = link_target(page, destination, vault)
        if target is None:
            continue
        try:
            relative = target.resolve().relative_to(vault.resolve()).as_posix()
        except (OSError, RuntimeError, ValueError):
            continue
        target_record = records_by_path.get(relative)
        target_fields = target_record.get("frontmatter") if target_record else None
        if not isinstance(target_fields, dict):
            continue
        if target_fields.get("type") != "source" and target_fields.get("assertion_kind") != "source_record":
            continue
        if relative not in linked:
            linked.append(relative)
    return linked


def _render_result(
    record: Dict[str, Any],
    catalog: Optional[Dict[str, Any]],
    terms: Sequence[str],
    matched_fields: Sequence[str],
    summary: Dict[str, Any],
    score: int,
    linked_from: Optional[str] = None,
    include_identity: bool = False,
) -> Dict[str, Any]:
    fields = record.get("frontmatter")
    if not isinstance(fields, dict):
        fields = {}
    sources = fields.get("sources")
    if not isinstance(sources, list):
        sources = []
    result = {
        "path": record.get("path"),
        "type": fields.get("type"),
        "title": fields.get("title"),
        "description": fields.get("description"),
        "status": fields.get("status"),
        "assertion_kind": fields.get("assertion_kind"),
        "generated": fields.get("generated"),
        "verified": fields.get("verified"),
        "stale_after": fields.get("stale_after"),
        "sources": sources,
        "matched_fields": list(matched_fields),
        "vertical": _vertical_for_path(str(record.get("path") or ""), catalog),
        "snippet": _snippet(str(record.get("body") or ""), terms),
        "match_type": summary["match_type"],
        "query_term_coverage": summary["query_term_coverage"],
        "matched_term_count": summary["matched_term_count"],
        "query_term_count": summary["query_term_count"],
        "phrase_fields": summary["phrase_fields"],
        "rank_score": score,
        "linked_from": linked_from,
    }
    if include_identity:
        aliases = fields.get("aliases")
        result["id"] = fields.get("id")
        result["aliases"] = aliases if isinstance(aliases, list) else []
    return result


def _snippet(body: str, terms: Sequence[str], limit: int = 220) -> str:
    compact = " ".join(line.strip() for line in body.splitlines() if line.strip())
    if len(compact) <= limit:
        return compact
    lowered = compact.casefold()
    positions = [
        lowered.find(term.casefold())
        for term in terms
        if lowered.find(term.casefold()) >= 0
    ]
    start = max(0, min(positions or [0]) - 60)
    snippet = compact[start : start + limit].strip()
    if start > 0:
        snippet = "…" + snippet
    if start + limit < len(compact):
        snippet += "…"
    return snippet


def _unique_tokens(tokens: Iterable[str]) -> List[str]:
    unique: List[str] = []
    seen = set()
    for token in tokens:
        if token not in seen:
            unique.append(token)
            seen.add(token)
    return unique


def _contains_token_phrase_tokens(
    tokens: Sequence[str], phrase_tokens: Sequence[str]
) -> bool:
    if not phrase_tokens:
        return False
    phrase = tuple(phrase_tokens)
    width = len(phrase)
    return any(
        tuple(tokens[offset : offset + width]) == phrase
        for offset in range(len(tokens) - width + 1)
    )


def _minimum_token_span(tokens: Sequence[str], terms: Sequence[str]) -> Optional[int]:
    """Return the shortest inclusive token span containing every term."""

    if not terms:
        return None
    target = set(terms)
    counts: Dict[str, int] = {}
    left = 0
    best: Optional[int] = None
    for right, token in enumerate(tokens):
        if token in target:
            counts[token] = counts.get(token, 0) + 1
        while len(counts) == len(target):
            span = right - left + 1
            best = span if best is None else min(best, span)
            left_token = tokens[left]
            if left_token in target:
                remaining = counts[left_token] - 1
                if remaining:
                    counts[left_token] = remaining
                else:
                    del counts[left_token]
            left += 1
    return best


def _record_adjustment(fields: Dict[str, Any]) -> int:
    status = fields.get("status")
    page_type = fields.get("type")
    assertion = fields.get("assertion_kind")
    adjustment = STATUS_ADJUSTMENTS.get(status, 0) if isinstance(status, str) else 0
    adjustment += TYPE_ADJUSTMENTS.get(page_type, 0) if isinstance(page_type, str) else 0
    if assertion == "source_record":
        adjustment -= 2_000_000
    elif assertion == "derived_synthesis":
        adjustment -= 10_000
    return adjustment


def _score_record(
    indexed: _IndexedRecord,
    query_normalized: str,
    query_tokens: Sequence[str],
    phrase_tokens: Sequence[str],
) -> Tuple[int, List[str], Dict[str, Any]]:
    fields = indexed.record.get("frontmatter")
    if not isinstance(fields, dict):
        return 0, [], {
            "match_type": "none",
            "query_term_coverage": 0.0,
            "matched_term_count": 0,
            "query_term_count": len(query_tokens),
            "phrase_fields": [],
        }

    exact_id = indexed.normalized_identifier == query_normalized
    exact_title = indexed.normalized_title == query_normalized
    exact_alias = query_normalized in indexed.normalized_aliases
    field_token_lists = indexed.field_token_lists
    field_token_sets = indexed.field_token_sets
    field_matches = {
        field: [token for token in query_tokens if token in tokens]
        for field, tokens in field_token_sets.items()
    }
    matched_terms = [
        token
        for token in query_tokens
        if any(token in tokens for tokens in field_token_sets.values())
    ]
    title_alias_matches = [
        token for token in query_tokens if token in field_token_sets["title_or_alias"]
    ]

    title_phrase = _contains_token_phrase_tokens(
        field_token_lists["title_or_alias"][0], phrase_tokens
    )
    alias_phrase = any(
        _contains_token_phrase_tokens(tokens, phrase_tokens)
        for tokens in field_token_lists["title_or_alias"][1:]
    )
    phrase_fields: List[str] = []
    if title_phrase:
        phrase_fields.append("title")
    if alias_phrase:
        phrase_fields.append("alias")
    if any(
        _contains_token_phrase_tokens(tokens, phrase_tokens)
        for tokens in field_token_lists["description_or_tags"]
    ):
        phrase_fields.append("description_or_tags")
    if any(
        _contains_token_phrase_tokens(tokens, phrase_tokens)
        for tokens in field_token_lists["headings"]
    ):
        phrase_fields.append("headings")
    if any(
        _contains_token_phrase_tokens(tokens, phrase_tokens)
        for tokens in field_token_lists["body"]
    ):
        phrase_fields.append("body")

    if exact_id:
        score = 1_000_000_000
        match_type = "exact_id"
        primary_fields = ["id"]
        summary_count = len(query_tokens)
    elif exact_title:
        score = 900_000_000
        match_type = "exact_title"
        primary_fields = ["title"]
        summary_count = len(query_tokens)
    elif exact_alias:
        score = 850_000_000
        match_type = "exact_alias"
        primary_fields = ["alias"]
        summary_count = len(query_tokens)
    elif matched_terms:
        matched_count = len(matched_terms)
        term_count = len(query_tokens)
        coverage_score = (matched_count * 100_000_000) // term_count
        count_score = matched_count * 100_000
        title_alias_score = len(title_alias_matches) * 1_000_000
        field_score = sum(
            max(
                (FIELD_WEIGHTS[field] for field in FIELD_ORDER if token in field_token_sets[field]),
                default=0,
            )
            for token in matched_terms
        )
        phrase_bonus = max(
            (
                20_000_000 if "title" in phrase_fields else 0,
                18_000_000 if "alias" in phrase_fields else 0,
                4_000_000 if "description_or_tags" in phrase_fields else 0,
                3_000_000 if "headings" in phrase_fields else 0,
                2_000_000 if "body" in phrase_fields else 0,
            )
        )

        best_span: Optional[int] = None
        for values in field_token_lists.values():
            for tokens in values:
                span = _minimum_token_span(tokens, query_tokens)
                if span is not None:
                    best_span = span if best_span is None else min(best_span, span)
        proximity_bonus = 0
        if best_span is not None:
            distance = max(0, best_span - term_count)
            proximity_bonus = max(0, 750_000 - distance * 25_000)

        score = (
            coverage_score
            + count_score
            + title_alias_score
            + field_score
            + phrase_bonus
            + proximity_bonus
        )
        if title_phrase:
            match_type = "title_phrase"
        elif alias_phrase:
            match_type = "alias_phrase"
        elif phrase_fields:
            match_type = "phrase"
        else:
            match_type = "lexical"
        primary_fields = []
        summary_count = matched_count
    else:
        return 0, [], {
            "match_type": "none",
            "query_term_coverage": 0.0,
            "matched_term_count": 0,
            "query_term_count": len(query_tokens),
            "phrase_fields": [],
        }

    matched_fields: List[str] = []
    for field in primary_fields:
        if field not in matched_fields:
            matched_fields.append(field)
    for field in FIELD_ORDER:
        if field not in matched_fields and field_matches[field]:
            # Exact title/alias results already have a more precise primary
            # label; keep the legacy combined label out of that duplicate.
            if field == "title_or_alias" and {"title", "alias"}.intersection(primary_fields):
                continue
            matched_fields.append(field)

    term_count = len(query_tokens)
    coverage = round(summary_count / term_count, 3) if term_count else 1.0
    summary = {
        "match_type": match_type,
        "query_term_coverage": coverage,
        "matched_term_count": summary_count,
        "query_term_count": term_count,
        "phrase_fields": phrase_fields,
    }
    return score, matched_fields, summary


def _search_corpus(
    corpus: _SearchCorpus,
    query: str,
    *,
    limit: int,
    vertical: Optional[str],
    scopes: Sequence[str],
    contextual: bool,
    include_sources: bool,
    include_derived: bool,
    expand_linked_sources: bool,
    exclude_archived: bool,
    exclude_superseded: bool,
    include_identity: bool,
    compatibility: Dict[str, Any],
) -> Dict[str, Any]:
    raw_terms = _unique_tokens(normalized_tokens(query))
    terms = [token for token in raw_terms if token not in STOPWORDS] or raw_terms
    phrase_tokens = normalized_tokens(query)
    normalized_query = normalized_text(query)
    results: List[Dict[str, Any]] = []
    for indexed in corpus.records:
        record = indexed.record
        path = str(record["path"])
        if record.get("is_deep_report") or path.startswith("review/deep-reviews/"):
            continue
        fields = record.get("frontmatter")
        if not isinstance(fields, dict):
            continue
        if vertical and _vertical_for_path(path, corpus.catalog) != vertical:
            continue
        if not _path_matches_scope(path, scopes):
            continue
        assertion = fields.get("assertion_kind")
        if assertion == "source_record" and not include_sources:
            continue
        status = fields.get("status")
        if status == "archived" and exclude_archived:
            continue
        if status == "superseded" and exclude_superseded:
            continue

        score, matched, summary = _score_record(
            indexed, normalized_query, terms, phrase_tokens
        )
        if score <= 0:
            continue
        if contextual and len(terms) > 1 and summary["query_term_coverage"] < 0.5:
            continue
        score += _record_adjustment(fields)
        results.append(
            _render_result(
                record,
                corpus.catalog,
                terms,
                matched,
                summary,
                score,
                include_identity=include_identity,
            )
        )
    results.sort(key=lambda item: (-int(item["rank_score"]), str(item["path"])))
    result_limit = max(0, limit)
    primary_limit = result_limit
    if expand_linked_sources and result_limit:
        # Reserve at most three result slots for provenance without allowing
        # linked sources to expand an otherwise bounded retrieval.
        primary_limit = max(1, result_limit - min(3, result_limit))
    if contextual and not include_derived:
        canonical_present = any(
            (corpus.records_by_path.get(str(item.get("path")), {}).get("frontmatter") or {}).get(
                "type"
            )
            != "synthesis"
            for item in results
        )
        if canonical_present:
            results = [
                item
                for item in results
                if (
                    corpus.records_by_path.get(str(item.get("path")), {}).get("frontmatter")
                    or {}
                ).get("type")
                != "synthesis"
            ]
    results = results[:primary_limit]

    if expand_linked_sources:
        seen_paths = {str(item.get("path")) for item in results}
        linked_budget = min(3, max(0, result_limit - len(results)))
        linked_results: List[Dict[str, Any]] = []
        linked_summary = {
            "match_type": "linked_source",
            "query_term_coverage": 0.0,
            "matched_term_count": 0,
            "query_term_count": len(terms),
            "phrase_fields": [],
        }
        for item in list(results):
            source_paths = _linked_source_paths(
                corpus.records_by_path.get(str(item.get("path")), {}),
                corpus.vault,
                corpus.records_by_path,
            )
            for source_path in source_paths:
                if len(linked_results) >= linked_budget:
                    break
                if source_path in seen_paths:
                    continue
                source_record = corpus.records_by_path.get(source_path)
                if source_record is None:
                    continue
                linked_results.append(
                    _render_result(
                        source_record,
                        corpus.catalog,
                        terms,
                        [],
                        linked_summary,
                        -1,
                        linked_from=str(item.get("path")),
                        include_identity=include_identity,
                    )
                )
                seen_paths.add(source_path)
            if len(linked_results) >= linked_budget:
                break
        results.extend(linked_results)

    return {
        "query": query,
        "limit": limit,
        "scope": list(scopes),
        "vertical": vertical,
        "contextual": contextual,
        "include_derived": include_derived,
        "expand_linked_sources": expand_linked_sources,
        "results": results,
        "findings": [],
        "runtime_compatibility": compatibility,
    }


def search_vault(
    vault: Path,
    query: str,
    limit: int = 10,
    vertical: Optional[str] = None,
    scope: Optional[Sequence[str]] = None,
    contextual: bool = False,
    include_sources: bool = False,
    include_derived: bool = False,
    expand_linked_sources: bool = False,
    include_archived: bool = False,
    include_superseded: bool = False,
    exclude_archived: bool = False,
    exclude_superseded: bool = False,
    include_identity: bool = False,
) -> Dict[str, Any]:
    """Search canonical pages without mutating or indexing the vault.

    ``scope`` restricts results to vault-relative areas or paths. ``contextual``
    applies the conservative coverage and canonical-over-derived rules used by
    contextual Query. ``expand_linked_sources`` appends a bounded set of source
    records linked from matched canonical pages. ``include_archived`` and
    ``include_superseded`` remain accepted as compatibility parameters, but are
    intentionally no-ops: historical pages are included by default. Use the
    exclusion parameters to omit them.
    """

    # Keep the deprecated parameters in the API for one compatibility cycle.
    del include_archived, include_superseded
    vault = vault.expanduser()
    scopes, scope_findings = _normalize_scopes(scope)
    if scope_findings:
        return {"query": query, "scope": scopes, "results": [], "findings": scope_findings}
    if not vault.exists() or vault.is_symlink() or not vault.is_dir():
        return {
            "query": query,
            "scope": scopes,
            "results": [],
            "findings": [f"vault is not a real directory: {vault}"],
        }

    compatibility = runtime_compatibility(vault)
    if not compatibility.get("ok"):
        return {
            "query": query,
            "limit": limit,
            "scope": scopes,
            "results": [],
            "findings": [str(compatibility.get("message") or "vault is not current")],
            "runtime_compatibility": compatibility,
        }
    corpus = _build_search_corpus(vault)
    return _search_corpus(
        corpus,
        query,
        limit=limit,
        vertical=vertical,
        scopes=scopes,
        contextual=contextual,
        include_sources=include_sources,
        include_derived=include_derived,
        expand_linked_sources=expand_linked_sources,
        exclude_archived=exclude_archived,
        exclude_superseded=exclude_superseded,
        include_identity=include_identity,
        compatibility=compatibility,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Search a SelfContext vault lexically or with explicit contextual "
            "scope; archived and superseded pages are included by default with "
            "lower ranking"
        )
    )
    parser.add_argument("query", help="query text")
    parser.add_argument("vault", nargs="?", default="vault")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        metavar="PATH",
        help="restrict retrieval to one or more vault-relative areas or paths (repeatable)",
    )
    parser.add_argument("--vertical")
    parser.add_argument(
        "--contextual",
        action="store_true",
        help="apply scoped contextual retrieval: ignore low-coverage matches and prefer canonical pages",
    )
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument(
        "--include-derived",
        action="store_true",
        help="allow derived syntheses in contextual retrieval when explicitly useful",
    )
    parser.add_argument(
        "--expand-linked-sources",
        action="store_true",
        help="append linked source records from matched canonical pages without broad source search",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help=(
            "Deprecated compatibility option; archived pages are included by "
            "default. Use --exclude-archived to omit them."
        ),
    )
    parser.add_argument(
        "--include-superseded",
        action="store_true",
        help=(
            "Deprecated compatibility option; superseded pages are included "
            "by default. Use --exclude-superseded to omit them."
        ),
    )
    parser.add_argument(
        "--exclude-archived",
        action="store_true",
        help="exclude pages whose status is archived",
    )
    parser.add_argument(
        "--exclude-superseded",
        action="store_true",
        help="exclude pages whose status is superseded",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    if args.include_archived:
        print(
            "WARNING: --include-archived is deprecated; archived pages are "
            "included by default. Use --exclude-archived instead.",
            file=sys.stderr,
        )
    if args.include_superseded:
        print(
            "WARNING: --include-superseded is deprecated; superseded pages are "
            "included by default. Use --exclude-superseded instead.",
            file=sys.stderr,
        )

    report = search_vault(
        Path(args.vault),
        args.query,
        limit=args.limit,
        vertical=args.vertical,
        scope=args.scope,
        contextual=args.contextual,
        include_sources=args.include_sources,
        include_derived=args.include_derived,
        expand_linked_sources=args.expand_linked_sources,
        include_archived=args.include_archived,
        include_superseded=args.include_superseded,
        exclude_archived=args.exclude_archived,
        exclude_superseded=args.exclude_superseded,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for finding in report.get("findings", []):
            print(f"ERROR: {finding}")
        for result in report.get("results", []):
            coverage = (
                f"{result['matched_term_count']}/{result['query_term_count']}"
            )
            fields = ",".join(result["matched_fields"]) or "none"
            linked_from = (
                f"; linked from {result['linked_from']}"
                if result.get("linked_from")
                else ""
            )
            print(
                f"- {result['title']} [{result['status']}] "
                f"({result['path']}) "
                f"[{result['match_type']}; coverage {coverage}; fields {fields}{linked_from}]: "
                f"{result['snippet']}"
            )
        if not report.get("results") and not report.get("findings"):
            print("No matching canonical pages")
    return 1 if report.get("findings") else 0


if __name__ == "__main__":
    raise SystemExit(main())
