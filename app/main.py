from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db import init_db
from app.api import auth, workspace, projects, sessions, chat, memory, ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspace.router)
app.include_router(projects.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(ingest.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
