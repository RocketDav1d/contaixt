import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router
from app.api.jobs import router as jobs_router
from app.api.projects import router as projects_router
from app.api.query import router as query_router
from app.api.sources import router as sources_router
from app.api.vaults import router as vaults_router
from app.api.webhooks import router as webhooks_router
from app.api.workspaces import router as workspaces_router

app = FastAPI(title="Contaixt API", version="0.1.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspaces_router)
app.include_router(vaults_router)
app.include_router(projects_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(jobs_router)
app.include_router(sources_router)
app.include_router(webhooks_router)


@app.get("/v1/health")
async def health():
    return {"status": "ok"}
