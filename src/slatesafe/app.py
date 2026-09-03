from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent import build_release_agent, evaluate_release_check
from .models import ReleaseCheckRequest, ReleaseDecision

# Editable local installs keep assets beside the repository root; the container
# installs the package into site-packages and explicitly points back to /app.
ROOT = Path(os.getenv("SLATESAFE_ROOT", Path(__file__).resolve().parents[2]))
app = FastAPI(title="SlateSafe", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "agent": build_release_agent().name}


@app.post("/api/release-check", response_model=ReleaseDecision)
async def release_check(
    request: ReleaseCheckRequest,
    gemini_api_key: str | None = Header(default=None, alias="X-SlateSafe-Gemini-Key"),
) -> ReleaseDecision:
    """Evaluate without accepting credentials in the URL or request body."""
    if gemini_api_key is not None and not 20 <= len(gemini_api_key) <= 512:
        raise HTTPException(status_code=400, detail="Invalid Gemini API key format.")
    try:
        return await evaluate_release_check(request, gemini_api_key)
    except PermissionError as error:
        raise HTTPException(status_code=428, detail=str(error)) from error
