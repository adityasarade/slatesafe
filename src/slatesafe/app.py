from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent import build_release_agent, evaluate_release_check
from .models import ReleaseCheckRequest, ReleaseDecision

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title="SlateSafe", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "agent": build_release_agent().name}


@app.post("/api/release-check", response_model=ReleaseDecision)
async def release_check(request: ReleaseCheckRequest) -> ReleaseDecision:
    return await evaluate_release_check(request)
