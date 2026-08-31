"""Sprint 3 ingestion pipeline — orchestrates M0→M1→M2→M3→M4→M5.

Pipeline stages:
  M0: Normalize raw conversation → NormalizedConversation
  M1: Session understanding → topics, entities, intents
  M2: Extract facts + decisions from messages
  M3: Temporal supersession (old facts → historical)
  M4: Graph persistence (entities, relationships)
  M5: Retrieve/rank at query time (no indexing step needed)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Fact, Decision, GraphNode, GraphEdge, Source, Session,
    NormalizedMessage, Message, Project, IngestJob,
)
from app.services.connectors import normalize
from app.services.m1_session import understand_session
from app.services.m2_facts import extract_facts, extract_decisions
from app.services.m3_temporal import supersede_fact, supersede_decision
from app.services.m4_graph import extract_graph_elements, persist_graph


async def run_pipeline(
    db: AsyncSession,
    *,
    workspace_id: str,
    tenant_id: str,
    project_id: str | None = None,
    user_id: str | None = None,
    source_type: str = "text",
    raw_content: str | dict,
    title: str | None = None,
    config: dict | None = None,
) -> dict[str, Any]:
    """Run the full M0→M1→M2→M3→M4 pipeline."""
    now = datetime.now(timezone.utc)

    # M0: Normalize
    conversation = normalize(raw_content, source_type=source_type)
    if title is None and conversation.title:
        title = conversation.title

    source = Source(
        project_id=project_id or "",
        workspace_id=workspace_id,
        tenant_id=tenant_id,
        source_type=conversation.source_type,
        external_id=conversation.external_id,
        title=title or f"Ingested {conversation.source_type}",
        message_count=len(conversation.messages),
        status="processing",
        stage="M0",
        config=config,
    )
    db.add(source)
    await db.flush()
    source_id = str(source.id)

    try:
        # Create session
        session = Session(
            workspace_id=workspace_id,
            user_id=user_id or "",
            title=title or f"Session from {conversation.source_type}",
            extra_metadata={"source_id": source_id, "pipeline": "sprint3"},
        )
        db.add(session)
        await db.flush()
        session_id = str(session.id)

        # Persist normalized messages
        normalized_msg_ids = []
        for i, msg in enumerate(conversation.messages):
            norm_msg = NormalizedMessage(
                source_id=source_id,
                session_id=session_id,
                message_index=i,
                external_id=msg.external_id,
                role=msg.role,
                content=msg.content,
                extra_metadata=msg.metadata or None,
                timestamp=msg.timestamp,
            )
            db.add(norm_msg)
            await db.flush()
            normalized_msg_ids.append(str(norm_msg.id))

        source.stage = "M1"
        source.progress = 25
        await db.flush()

        # M1: Session understanding
        m1_result = understand_session(conversation.messages)
        source.stage = "M2"
        source.progress = 50
        await db.flush()

        # M2: Fact + Decision extraction
        facts, decisions = extract_facts_and_decisions(conversation.messages)

        facts_created = 0
        for fact in facts:
            # M3: Check for supersession or duplication
            existing = await _find_current_fact(db, workspace_id, fact.subject, fact.predicate)
            if existing:
                if existing.object.lower() != fact.object.lower():
                    # Same subject/predicate but new object → supersede old
                    existing.temporal_status = "historical"
                    existing.updated_at = now
                    # Create the new fact
                    db_fact = Fact(
                        workspace_id=workspace_id,
                        project_id=project_id,
                        source_id=source_id,
                        session_id=session_id,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        object=fact.object,
                        content=fact.content,
                        confidence=fact.confidence,
                        authority=fact.authority,
                        temporal_status="current",
                        status="active",
                    )
                    db.add(db_fact)
                    facts_created += 1
                # else: exact same fact already exists — skip (dedup)
            else:
                # No existing fact, create new
                db_fact = Fact(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    source_id=source_id,
                    session_id=session_id,
                    subject=fact.subject,
                    predicate=fact.predicate,
                    object=fact.object,
                    content=fact.content,
                    confidence=fact.confidence,
                    authority=fact.authority,
                    temporal_status="current",
                    status="active",
                )
                db.add(db_fact)
                facts_created += 1

        decisions_created = 0
        for dec in decisions:
            db_dec = Decision(
                workspace_id=workspace_id,
                project_id=project_id,
                source_id=source_id,
                session_id=session_id,
                content=dec.content,
                context=dec.context or "",
                confidence=dec.confidence,
                authority=dec.authority,
                temporal_status="current",
                status="active",
            )
            db.add(db_dec)
            decisions_created += 1

        source.stage = "M3"
        source.progress = 75
        await db.flush()

        # M3 temporal done (handled inline above)
        source.stage = "M4"
        source.progress = 85
        await db.flush()

        # M4: Graph persistence
        all_text = "\n".join(m.content for m in conversation.messages)
        nodes_data, edges_data = extract_graph_elements(all_text)
        graph_result = await persist_graph(
            db=db,
            workspace_id=workspace_id,
            nodes_data=nodes_data,
            edges_data=edges_data,
            project_id=project_id,
            source_id=source_id,
        )

        source.stage = "M5"
        source.progress = 100
        source.status = "completed"
        source.completed_at = now
        source.message_count = len(conversation.messages)
        await db.flush()

        return {
            "source_id": source_id,
            "session_id": session_id,
            "status": "completed",
            "stage": "M5",
            "messages_processed": len(conversation.messages),
            "facts_created": facts_created,
            "decisions_created": decisions_created,
            "graph_nodes_created": graph_result["nodes_created"],
            "graph_edges_created": graph_result["edges_created"],
            "topics": m1_result.topics,
            "entities": m1_result.entities_mentioned,
        }

    except Exception as exc:
        source.status = "failed"
        source.error_message = str(exc)
        await db.flush()
        raise


async def _find_current_fact(db: AsyncSession, workspace_id: str, subject: str, predicate: str):
    from app.models import Fact
    result = await db.execute(
        select(Fact).where(
            Fact.workspace_id == workspace_id,
            Fact.subject == subject,
            Fact.predicate == predicate,
            Fact.temporal_status == "current",
            Fact.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


def extract_facts_and_decisions(messages: list[Any]) -> tuple[list[Any], list[Any]]:
    from app.services.m2_facts import run_m2
    return run_m2(messages)
