"""Fictional scenarios shared by retrieval tests and explicit agent evaluations."""

from pathlib import Path

import sync_indexes
from synthetic_vault import build_synthetic_vault, write_page


def build_context_scenarios(project: Path) -> Path:
    vault = build_synthetic_vault(project)
    write_page(vault, "sources/session.md", page_type="source", title="John Doe interview",
               assertion_kind="source_record", body="John described technical leadership, remote work, and two days of weekly availability.\n")
    write_page(vault, "career/leadership.md", title="Liderazgo técnico", aliases=["Dirección técnica"],
               sources=["../sources/session.md"], assertion_kind="source_derived_fact",
               body="John Doe lideró una migración técnica en MyContext Systems.\n")
    write_page(vault, "career/current-role.md", title="Current role", stale_after="2026-01-01",
               body="As of 2025-10-01, John Doe was an engineer at MyContext Systems. Currentness is unknown.\n")
    write_page(vault, "core/availability.md", title="Weekly availability",
               body="As of 2026-08-12, John Doe reported two days per week available for projects.\n")
    write_page(vault, "core/remote-work.md", title="Remote work", status="review",
               body="John Doe reported working remotely. This has not been explicitly confirmed.\n")
    write_page(vault, "career/expansion-old.md", title="Expansion decision", status="superseded",
               superseded_by="maintenance.md", body="John Doe previously planned expansion.\n")
    write_page(vault, "career/maintenance.md", title="Maintenance decision",
               body="John Doe chose maintenance until repeat use is demonstrated.\n")
    write_page(vault, "review/observations/expansion-constraint.md", page_type="observation",
               title="Expansion constraint", assertion_kind="agent_inference", status="review",
               sources=["../../core/availability.md"],
               body="Expansion may exceed John's two-day availability. This is an unresolved inference, not a confirmed constraint.\n")
    write_page(vault, "core/work-arrangement.md", title="Work arrangement",
               sources=["../sources/session.md"],
               body="## Location\n\nJohn works remotely.\n\n## Availability\n\nJohn reported two days weekly as of 2026-08-12.\n")
    sync_indexes.synchronize(vault, write=True)
    return vault
