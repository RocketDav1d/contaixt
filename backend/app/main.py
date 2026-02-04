from fastapi import FastAPI

from app.api.ingest import router as ingest_router
from app.api.workspaces import router as workspaces_router

app = FastAPI(title="Contaixt API", version="0.1.0")

app.include_router(workspaces_router)
app.include_router(ingest_router)


@app.get("/v1/health")
async def health():
    return {"status": "ok"}
