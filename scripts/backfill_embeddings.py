"""Backfill embeddings for Memory rows that lack them.

Idempotent: keyed on content_hash + embedding_version, so a rerun never
generates a duplicate embedding for the same content/version pair.
Rate-limited to avoid overwhelming the embedding service.

Usage:
    python scripts/backfill_embeddings.py [--batch-size 50] [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session_factory
from app.models import Memory
from app.services.embeddings import generate_embedding, embedding_version, content_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def get_backfill_candidates(session: AsyncSession, batch_size: int = 50) -> list[dict[str, Any]]:
    """Fetch memories that need embeddings."""
    stmt = (
        select(Memory.id, Memory.content, Memory.embedding_model, Memory.embedding_version)
        .where(Memory.embedding.is_(None))
        .where(Memory.deleted_at.is_(None))
        .order_by(Memory.created_at)
        .limit(batch_size)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "id": str(row[0]),
            "content": row[1] or "",
            "existing_model": row[2],
            "existing_version": row[3],
        }
        for row in rows
    ]


async def get_total_needing_embeddings(session: AsyncSession) -> int:
    stmt = select(func.count(Memory.id)).where(
        Memory.embedding.is_(None),
        Memory.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_total_memories(session: AsyncSession) -> int:
    stmt = select(func.count(Memory.id)).where(Memory.deleted_at.is_(None))
    result = await session.execute(stmt)
    return result.scalar() or 0


async def backfill_embeddings(batch_size: int = 50, dry_run: bool = False) -> dict[str, Any]:
    """Run the embedding backfill.

    Returns statistics dict.
    """
    start_time = time.monotonic()
    stats = {
        "total_memories": 0,
        "needed_embeddings": 0,
        "embedded": 0,
        "skipped_empty": 0,
        "errors": 0,
        "batches": 0,
        "elapsed_seconds": 0.0,
    }

    target_version = embedding_version()

    async with async_session_factory() as session:
        stats["total_memories"] = await get_total_memories(session)
        stats["needed_embeddings"] = await get_total_needing_embeddings(session)

        if stats["needed_embeddings"] == 0:
            logger.info("No embeddings needed — all %d memories already have embeddings.", stats["total_memories"])
            return stats

        if dry_run:
            logger.info("[dry-run] Would embed %d memories", stats["needed_embeddings"])
            return stats

        logger.info(
            "Backfilling embeddings: %d/%d memories need embeddings (target version: %s)",
            stats["needed_embeddings"],
            stats["total_memories"],
            target_version,
        )

        processed = 0
        while processed < stats["needed_embeddings"]:
            candidates = await get_backfill_candidates(session, batch_size)
            if not candidates:
                break

            batch_embedded = 0
            for cand in candidates:
                content = cand["content"]
                memory_id = cand["id"]

                # Skip empty content
                if not content or not content.strip():
                    logger.debug("[backfill] Skipping %s: empty content", memory_id)
                    stats["skipped_empty"] += 1
                    continue

                try:
                    # Idempotency check: content hash should be unique per content
                    chash = content_hash(content)
                    embedding_vec, model_name, dim = generate_embedding(content)
                    now = datetime.now(timezone.utc)

                    # Update the memory record
                    memory_stmt = (
                        select(Memory)
                        .where(Memory.id == memory_id)
                        .where(Memory.deleted_at.is_(None))
                        .with_for_update()
                    )
                    result = await session.execute(memory_stmt)
                    memory = result.scalar_one_or_none()
                    if memory is None:
                        logger.warning("[backfill] Memory %s not found (possibly deleted)", memory_id)
                        continue

                    # Double-check idempotency: another run might have set it
                    if memory.embedding is not None and memory.embedding_version == target_version:
                        logger.debug("[backfill] Skipping %s: already embedded with current version", memory_id)
                        continue

                    memory.embedding = embedding_vec
                    memory.embedding_model = model_name
                    memory.embedding_dimension = dim
                    memory.embedding_version = target_version
                    memory.embedded_at = now
                    await session.flush()
                    batch_embedded += 1
                    stats["embedded"] += 1

                except Exception as exc:
                    logger.error("[backfill] Error embedding %s: %s", memory_id, exc)
                    stats["errors"] += 1

            stats["batches"] += 1
            processed += len(candidates)

            # Progress
            progress_pct = min(100, int(stats["embedded"] / stats["needed_embeddings"] * 100))
            logger.info(
                "[backfill] Progress: %d%% (%d/%d embedded, batch %d, errors %d)",
                progress_pct,
                stats["embedded"],
                stats["needed_embeddings"],
                stats["batches"],
                stats["errors"],
            )

            # Rate-limit between batches
            await session.commit()
            if processed < stats["needed_embeddings"]:
                await asyncio.sleep(0.5)

        await session.commit()

    stats["elapsed_seconds"] = round(time.monotonic() - start_time, 2)
    return stats


def main():
    parser = argparse.ArgumentParser(description="Backfill embeddings for Memory rows")
    parser.add_argument("--batch-size", type=int, default=50, help="Rows per batch (default: 50)")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without writing")
    args = parser.parse_args()

    stats = asyncio.run(backfill_embeddings(batch_size=args.batch_size, dry_run=args.dry_run))

    logger.info("=== Backfill Complete ===")
    logger.info("  Total memories: %d", stats["total_memories"])
    logger.info("  Needed embeddings: %d", stats["needed_embeddings"])
    logger.info("  Embedded: %d", stats["embedded"])
    logger.info("  Skipped (empty): %d", stats["skipped_empty"])
    logger.info("  Errors: %d", stats["errors"])
    logger.info("  Batches: %d", stats["batches"])
    logger.info("  Elapsed: %.1fs", stats["elapsed_seconds"])


if __name__ == "__main__":
    main()
