#!/usr/bin/env python3
"""Deterministic metadata rules owned by the Writing vertical."""

from __future__ import annotations

from typing import Any, List, Mapping


WRITING_ROLE_COMBINATIONS = {
    ("primary", "user", "none"),
    ("human_edited_ai_assisted", "shared", "assisted"),
    ("generated_derived", "agent", "generated"),
    ("unknown", "unknown", "unknown"),
}


def validate_writing_metadata(fields: Mapping[str, Any]) -> List[str]:
    """Return deterministic errors for a tagged Writing source or artifact."""

    page_type = fields.get("type")
    tags = fields.get("tags")
    if not (
        isinstance(page_type, str)
        and page_type in {"source", "synthesis"}
        and isinstance(tags, list)
        and "writing" in tags
    ):
        return []

    role_fields = (
        fields.get("writing_evidence_role"),
        fields.get("authorship"),
        fields.get("ai_involvement"),
    )
    if any(not isinstance(value, str) or value in {"", "null"} for value in role_fields):
        return [
            "writing source/artifact requires writing_evidence_role, authorship, and ai_involvement"
        ]
    if role_fields not in WRITING_ROLE_COMBINATIONS:
        return [f"invalid Writing artifact role combination: {role_fields!r}"]
    return []
