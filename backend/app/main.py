import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ingest import router as ingest_router
from app.api.jobs import router as jobs_router
from app.api.query import router as query_router
from app.api.sources import router as sources_router
from app.api.vaults import router as vaults_router
from app.api.webhooks import router as webhooks_router
from app.api.workspaces import router as workspaces_router
from app.mcp import get_mcp_app

mcp_app = get_mcp_app()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with mcp_app.lifespan(mcp_app):
        yield


app = FastAPI(title="Contaixt API", version="0.1.0", lifespan=lifespan)

# CORS for frontend and MCP clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)

app.include_router(workspaces_router)
app.include_router(vaults_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(jobs_router)
app.include_router(sources_router)
app.include_router(webhooks_router)

# Mount MCP server at /mcp (Streamable HTTP)
app.mount("/mcp", mcp_app)


@app.get("/v1/health")
async def health():
    return {"status": "ok"}
