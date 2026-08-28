#!/usr/bin/env python3
"""Schema migration topology and deterministic path resolution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple


LATEST_SUPPORTED_SCHEMA = "0.2"


class MigrationRegistryError(ValueError):
    """A migration registry cannot safely resolve the requested path."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MigrationEdge:
    """One deterministic schema transition in a migration graph.

    The topology layer only needs ``source`` and ``target``.  ``planner`` and
    the optional validators are execution bindings kept injectable for the
    migration engine and tests; the production topology does not define them.
    """

    def __init__(
        self,
        source: Any,
        target: Any,
        planner: Optional[Callable[[Path], Dict[str, Any]]] = None,
        *,
        validator: Optional[Callable[[Path], Dict[str, Any]]] = None,
        active_validator: Optional[Callable[[Path, Mapping[str, Any]], Dict[str, Any]]] = None,
        name: Optional[str] = None,
    ) -> None:
        self.source = _schema_label(source)
        self.target = _schema_label(target)
        self.planner = planner
        self.validator = validator
        self.active_validator = active_validator
        self.name = name or f"{self.source}->{self.target}"

    @property
    def label(self) -> str:
        return f"{self.source}->{self.target}"


def _schema_label(value: Any) -> str:
    if isinstance(value, tuple) and len(value) == 2:
        return f"{int(value[0])}.{int(value[1])}"
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"invalid schema label: {value!r}")


def _numeric_schema_label(value: str) -> Optional[Tuple[int, int]]:
    match = re.fullmatch(r"(\d+)\.(\d+)", value)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def is_future_schema(value: str, latest: str) -> bool:
    current_number = _numeric_schema_label(value)
    latest_number = _numeric_schema_label(latest)
    return bool(current_number and latest_number and current_number > latest_number)


def _registry_finding(
    severity: str,
    path: str,
    message: str,
    classification: str = "migration",
    **extra: Any,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "severity": severity,
        "classification": classification,
        "path": path,
        "message": message,
    }
    result.update(extra)
    return result


class MigrationRegistry:
    """Dependency-free directed graph for supported schema migrations."""

    def __init__(self, latest: Any, edges: Iterable[MigrationEdge]) -> None:
        self.latest = _schema_label(latest)
        self.edges = tuple(edges)

    @property
    def latest_supported_schema(self) -> str:
        return self.latest

    @property
    def supported_versions(self) -> List[str]:
        return sorted(
            {self.latest, *(edge.source for edge in self.edges), *(edge.target for edge in self.edges)},
            key=lambda value: (
                _numeric_schema_label(value) is None,
                _numeric_schema_label(value) or (0, 0),
                value,
            ),
        )

    def validation_findings(self) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        seen: Dict[Tuple[str, str], str] = {}
        adjacency: Dict[str, List[MigrationEdge]] = {}
        nodes = {self.latest}
        for edge in self.edges:
            nodes.update((edge.source, edge.target))
            key = (edge.source, edge.target)
            if key in seen:
                findings.append(
                    _registry_finding(
                        "error",
                        "",
                        f"duplicate migration edge {edge.label} ({seen[key]} and {edge.name})",
                        "migration-registry",
                        code="duplicate-edge",
                    )
                )
            else:
                seen[key] = edge.name
            if edge.source == edge.target:
                findings.append(
                    _registry_finding(
                        "error",
                        "",
                        f"migration edge cannot point to itself: {edge.label}",
                        "migration-registry",
                        code="cycle",
                    )
                )
            adjacency.setdefault(edge.source, []).append(edge)

        for source in adjacency:
            adjacency[source].sort(key=lambda edge: (edge.target, edge.name))

        visit_state: Dict[str, int] = {}
        cycle_keys: set[Tuple[str, str]] = set()

        def visit(node: str) -> None:
            visit_state[node] = 1
            for edge in adjacency.get(node, []):
                state = visit_state.get(edge.target, 0)
                if state == 1:
                    cycle = (node, edge.target)
                    if cycle not in cycle_keys:
                        cycle_keys.add(cycle)
                        findings.append(
                            _registry_finding(
                                "error",
                                "",
                                f"cyclic migration graph includes {edge.label}",
                                "migration-registry",
                                code="cycle",
                            )
                        )
                elif state == 0:
                    visit(edge.target)
            visit_state[node] = 2

        for node in sorted(nodes):
            if visit_state.get(node, 0) == 0:
                visit(node)

        if self.latest not in nodes:
            findings.append(
                _registry_finding(
                    "error",
                    "",
                    f"latest supported schema is not represented: {self.latest}",
                    "migration-registry",
                    code="missing-latest",
                )
            )
        return findings

    def validate(self) -> List[str]:
        """Return deterministic human-readable registry validation errors."""

        return [str(item["message"]) for item in self.validation_findings()]

    def resolve_path(self, source: Any, target: Any) -> List[MigrationEdge]:
        source_label = _schema_label(source)
        target_label = self.latest if _schema_label(target) == "latest" else _schema_label(target)
        findings = self.validation_findings()
        if findings:
            raise MigrationRegistryError("invalid-registry", "; ".join(self.validate()))
        if target_label not in self.supported_versions:
            raise MigrationRegistryError(
                "unsupported-target",
                f"unsupported migration target schema: {target_label}",
            )
        if is_future_schema(source_label, self.latest):
            raise MigrationRegistryError(
                "future-schema",
                f"vault declares future unsupported schema: {source_label}",
            )
        if source_label not in self.supported_versions:
            raise MigrationRegistryError(
                "missing-path",
                f"no migration path starts at schema {source_label}",
            )
        if source_label == target_label:
            return []

        adjacency: Dict[str, List[MigrationEdge]] = {}
        for edge in self.edges:
            adjacency.setdefault(edge.source, []).append(edge)
        for source_edges in adjacency.values():
            source_edges.sort(key=lambda edge: (edge.target, edge.name))

        queue: List[Tuple[str, List[MigrationEdge]]] = [(source_label, [])]
        visited = {source_label}
        while queue:
            node, path = queue.pop(0)
            for edge in adjacency.get(node, []):
                candidate = path + [edge]
                if edge.target == target_label:
                    return candidate
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append((edge.target, candidate))
        raise MigrationRegistryError(
            "missing-path",
            f"no complete migration path from schema {source_label} to {target_label}",
        )


def default_migration_registry() -> MigrationRegistry:
    """Return the production schema topology without executable planners."""

    return MigrationRegistry(
        LATEST_SUPPORTED_SCHEMA,
        (MigrationEdge("0.1", "0.2", name="schema-0.1-to-0.2"),),
    )
