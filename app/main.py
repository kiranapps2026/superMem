from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db import init_db
from app.api import auth, workspace, projects, sessions, chat, memory, ingest, provenance, dashboard, feedback

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(workspace.router)
api_v1.include_router(projects.router)
api_v1.include_router(sessions.router)
api_v1.include_router(chat.router)
api_v1.include_router(memory.router)
api_v1.include_router(ingest.router)
api_v1.include_router(provenance.router)
api_v1.include_router(dashboard.router)
api_v1.include_router(feedback.router)


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

app.include_router(api_v1)


@app.get("/health")
async def health():
    return {"status": "ok"}
