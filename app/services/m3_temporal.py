"""M3 — Temporal truth management.

Tracks supersession of facts and decisions over time.
When a new fact conflicts with an existing current fact, the old one
becomes historical and the new one becomes current.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def supersede_fact(
    db: Any,
    workspace_id: str,
    subject: str,
    predicate: str,
    new_object: str,
    new_content: str,
    project_id: str | None = None,
    source_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Supersede any current fact with the same subject+predicate.

    This implements temporal truth:
    - Find any active/current fact with matching (workspace_id, subject, predicate)
    - Mark it as historical, set superseded_by
    - Create the new fact as current

    Args:
        db: Database session
        workspace_id: Workspace scope
        subject: Fact subject (e.g., "Project Alpha")
        predicate: Fact predicate (e.g., "uses")
        new_object: New object value (e.g., "PostgreSQL")
        new_content: Full fact text
        project_id: Optional project scope
        source_id: Optional source reference
        session_id: Optional session reference

    Returns:
        Dict with 'superseded' (list of old fact IDs) and 'created' (new fact ID)
    """
    from app.models import Fact

    now = datetime.now(timezone.utc)
    result = {"superseded": [], "created": None}

    # Find current facts matching subject+predicate in this workspace
    existing = db.execute(
        __import__("sqlalchemy").select(Fact).where(
            Fact.workspace_id == workspace_id,
            Fact.subject == subject,
            Fact.predicate == predicate,
            Fact.temporal_status == "current",
            Fact.deleted_at.is_(None),
        )
    ).scalars().all()

    for old_fact in existing:
        # If same object, no change needed
        if old_fact.object.lower() == new_object.lower():
            return result

        # Mark old as historical
        old_fact.temporal_status = "historical"
        old_fact.updated_at = now
        result["superseded"].append(str(old_fact.id))

    # Create new current fact
    new_fact = Fact(
        workspace_id=workspace_id,
        project_id=project_id,
        source_id=source_id,
        session_id=session_id,
        subject=subject,
        predicate=predicate,
        object=new_object,
        content=new_content,
        confidence=1.0,
        authority=1.0,
        temporal_status="current",
        status="active",
    )
    db.add(new_fact)
    db.flush()
    result["created"] = str(new_fact.id)

    return result


def supersede_decision(
    db: Any,
    workspace_id: str,
    new_content: str,
    project_id: str | None = None,
    source_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Supersede current decisions when a conflicting one is found.

    Args:
        db: Database session
        workspace_id: Workspace scope
        new_content: The new decision text
        project_id: Optional project scope
        source_id: Optional source reference
        session_id: Optional session reference

    Returns:
        Dict with 'superseded' and 'created'
    """
    from app.models import Decision

    now = datetime.now(timezone.utc)
    result = {"superseded": [], "created": None}

    # Find current decisions in this workspace (exact match on content = no change)
    existing = db.execute(
        __import__("sqlalchemy").select(Decision).where(
            Decision.workspace_id == workspace_id,
            Decision.temporal_status == "current",
            Decision.deleted_at.is_(None),
        )
    ).scalars().all()

    for old_dec in existing:
        if old_dec.content.strip().lower() == new_content.strip().lower():
            return result

        # Mark old as historical
        old_dec.temporal_status = "historical"
        old_dec.updated_at = now
        result["superseded"].append(str(old_dec.id))

    new_dec = Decision(
        workspace_id=workspace_id,
        project_id=project_id,
        source_id=source_id,
        session_id=session_id,
        content=new_content,
        context=new_content[:500],
        confidence=1.0,
        authority=1.0,
        temporal_status="current",
        status="active",
    )
    db.add(new_dec)
    db.flush()
    result["created"] = str(new_dec.id)

    return result


def get_current_facts(db: Any, workspace_id: str, project_id: str | None = None) -> list[Any]:
    """Get all current (non-historical) facts for a workspace.

    Args:
        db: Database session
        workspace_id: Workspace to query
        project_id: Optional project filter

    Returns:
        List of current Fact objects
    """
    from app.models import Fact
    from sqlalchemy import select

    stmt = select(Fact).where(
        Fact.workspace_id == workspace_id,
        Fact.temporal_status == "current",
        Fact.deleted_at.is_(None),
    )
    if project_id:
        stmt = stmt.where(Fact.project_id == project_id)
    return list(db.execute(stmt).scalars().all())


def get_current_decisions(db: Any, workspace_id: str, project_id: str | None = None) -> list[Any]:
    """Get all current decisions for a workspace.

    Args:
        db: Database session
        workspace_id: Workspace to query
        project_id: Optional project filter

    Returns:
        List of current Decision objects
    """
    from app.models import Decision
    from sqlalchemy import select

    stmt = select(Decision).where(
        Decision.workspace_id == workspace_id,
        Decision.temporal_status == "current",
        Decision.deleted_at.is_(None),
    )
    if project_id:
        stmt = stmt.where(Decision.project_id == project_id)
    return list(db.execute(stmt).scalars().all())
