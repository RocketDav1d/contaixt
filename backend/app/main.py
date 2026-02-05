import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from fastapi import FastAPI

from app.api.ingest import router as ingest_router
from app.api.jobs import router as jobs_router
from app.api.query import router as query_router
from app.api.sources import router as sources_router
from app.api.vaults import router as vaults_router
from app.api.webhooks import router as webhooks_router
from app.api.workspaces import router as workspaces_router

app = FastAPI(title="Contaixt API", version="0.1.0")

app.include_router(workspaces_router)
app.include_router(vaults_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(jobs_router)
app.include_router(sources_router)
app.include_router(webhooks_router)


@app.get("/v1/health")
async def health():
    return {"status": "ok"}
