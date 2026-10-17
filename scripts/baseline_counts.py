"""Baseline row counts for key tables."""
import asyncio
from sqlalchemy import text
from app.db import engine


async def main():
    tables = [
        "memories", "facts", "decisions",
        "graph_nodes", "graph_edges"
    ]
    async with engine.connect() as conn:
        for tbl in tables:
            result = await conn.execute(text(f"SELECT count(*) FROM {tbl}"))
            count = result.scalar()
            print(f"  {tbl}: {count}")


asyncio.run(main())
