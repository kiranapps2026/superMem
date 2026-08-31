"""M4 — Graph persistence: extract and persist knowledge graph relationships.

Extracts entities and relationships from conversation text and persists
them as graph_nodes and graph_edges.
"""

from __future__ import annotations

import re
from typing import Any


# Relationship patterns: (regex, relationship_type)
RELATIONSHIP_PATTERNS = [
    (re.compile(
        r'(?P<source>(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))\s+'
        r'(?:uses?|runs?\s+on|built\s+with|powered\s+by)\s+'
        r'(?P<target>(?:[A-Z][A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+)*))',
        re.IGNORECASE
    ), "uses"),
    (re.compile(
        r'(?P<source>(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))\s+'
        r'(?:connects?\s+to|integrates?\s+with|talks?\s+to)\s+'
        r'(?P<target>(?:[A-Z][A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+)*))',
        re.IGNORECASE
    ), "connects_to"),
    (re.compile(
        r'(?P<source>(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))\s+'
        r'(?:depends?\s+on|relies?\s+on)\s+'
        r'(?P<target>(?:[A-Z][A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+)*))',
        re.IGNORECASE
    ), "depends_on"),
    (re.compile(
        r'(?P<source>(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))\s+'
        r'(?:is\s+a|is\s+an|is\s+the)\s+'
        r'(?P<target>(?:[A-Z][A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+)*))',
        re.IGNORECASE
    ), "is_a"),
]


def _normalize_label(label: str) -> str:
    """Normalize entity label for graph storage."""
    label = label.strip()
    label = re.sub(r'\s+', ' ', label)
    return label[:500]


def extract_graph_elements(text: str) -> tuple[list[dict], list[dict]]:
    """Extract graph nodes and edges from text.

    Returns:
        Tuple of (nodes_list, edges_list) where each is a list of dicts
        with keys matching GraphNode/GraphEdge fields
    """
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for pattern, rel_type in RELATIONSHIP_PATTERNS:
        for match in pattern.finditer(text):
            source_label = _normalize_label(match.group("source"))
            target_label = _normalize_label(match.group("target"))

            if len(source_label) < 2 or len(target_label) < 2:
                continue
            if source_label.lower() == target_label.lower():
                continue

            for label in (source_label, target_label):
                if label not in nodes:
                    nodes[label] = {
                        "label": label,
                        "node_type": _classify_node(label),
                    }

            edges.append({
                "source_label": source_label,
                "target_label": target_label,
                "relationship_type": rel_type,
            })

    return list(nodes.values()), edges


def _classify_node(label: str) -> str:
    """Classify a node based on its label."""
    tech_keywords = {
        "PostgreSQL", "MongoDB", "MySQL", "Redis", "Docker", "Kubernetes",
        "Python", "JavaScript", "TypeScript", "React", "Vue", "FastAPI",
        "AWS", "GCP", "Azure", "GraphQL", "REST",
    }
    for kw in tech_keywords:
        if kw.lower() in label.lower():
            return "technology"

    if re.match(r'^[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+$', label):
        return "project"

    return "entity"


async def persist_graph(
    db: Any,
    workspace_id: str,
    nodes_data: list[dict],
    edges_data: list[dict],
    project_id: str | None = None,
    source_id: str | None = None,
) -> dict[str, Any]:
    """Persist extracted graph elements to the database.

    Args:
        db: Async database session
        workspace_id: Workspace scope
        nodes_data: List of dicts with 'label', 'node_type'
        edges_data: List of dicts with 'source_label', 'target_label', 'relationship_type'
        project_id: Optional project scope
        source_id: Optional source reference

    Returns:
        Dict with 'nodes_created', 'edges_created'
    """
    from app.models import GraphNode, GraphEdge
    from sqlalchemy import select

    result = {"nodes_created": 0, "edges_created": 0}
    node_map: dict[str, str] = {}

    for node_data in nodes_data:
        label = node_data["label"]
        q = await db.execute(
            select(GraphNode).where(
                GraphNode.workspace_id == workspace_id,
                GraphNode.external_id == label,
                GraphNode.deleted_at.is_(None),
            )
        )
        existing = q.scalar_one_or_none()

        if existing is None:
            node = GraphNode(
                workspace_id=workspace_id,
                project_id=project_id,
                external_id=label,
                label=label,
                node_type=node_data.get("node_type", "entity"),
                properties={"source": "m4_extraction"},
            )
            db.add(node)
            await db.flush()
            node_map[label] = str(node.id)
            result["nodes_created"] += 1
        else:
            node_map[label] = str(existing.id)

    for edge_data in edges_data:
        s_label = edge_data["source_label"]
        t_label = edge_data["target_label"]
        s_id = node_map.get(s_label)
        t_id = node_map.get(t_label)

        if not s_id or not t_id:
            continue

        eq = await db.execute(
            select(GraphEdge).where(
                GraphEdge.workspace_id == workspace_id,
                GraphEdge.source_node_id == s_id,
                GraphEdge.target_node_id == t_id,
                GraphEdge.relationship_type == edge_data["relationship_type"],
                GraphEdge.temporal_status == "current",
                GraphEdge.deleted_at.is_(None),
            )
        )
        if eq.scalar_one_or_none() is not None:
            continue

        edge = GraphEdge(
            workspace_id=workspace_id,
            project_id=project_id,
            source_node_id=s_id,
            target_node_id=t_id,
            relationship_type=edge_data["relationship_type"],
            confidence=0.8,
            temporal_status="current",
            source_id=source_id,
        )
        db.add(edge)
        result["edges_created"] += 1

    await db.flush()
    return result
