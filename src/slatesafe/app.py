from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent import build_release_agent, evaluate_release_check, public_byok_enabled
from .models import ReleaseCheckRequest, ReleaseDecision

# Editable local installs keep assets beside the repository root; the container
# installs the package into site-packages and explicitly points back to /app.
ROOT = Path(os.getenv("SLATESAFE_ROOT", Path(__file__).resolve().parents[2]))
app = FastAPI(title="SlateSafe", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

# The public Cloud Run service is deployed with one concurrent request and one
# maximum instance. This in-memory budget therefore caps all calls that can
# reach the shared ClickHouse trial ledger; Gemini stays visitor-BYOK.
_public_request_times: list[float] = []


def enforce_public_request_budget() -> None:
    """Bound public ledger use without retaining a visitor key or identity."""
    window_seconds = 60 * 60
    try:
        limit = int(os.getenv("SLATESAFE_PUBLIC_REQUESTS_PER_HOUR", "6"))
    except ValueError as error:
        raise RuntimeError("SLATESAFE_PUBLIC_REQUESTS_PER_HOUR must be an integer.") from error
    if limit < 1:
        raise RuntimeError("SLATESAFE_PUBLIC_REQUESTS_PER_HOUR must be at least one.")

    now = time.monotonic()
    _public_request_times[:] = [stamp for stamp in _public_request_times if now - stamp < window_seconds]
    if len(_public_request_times) >= limit:
        raise HTTPException(
            status_code=429,
            detail="The public demo ledger budget is temporarily exhausted. Please try again later.",
            headers={"Retry-After": "3600"},
        )
    _public_request_times.append(now)


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
    # This check deliberately happens before evaluating the release: on a live
    # deployment that evaluation would query ClickHouse. Anonymous callers must
    # not be able to consume either the operator's Gemini or ledger resources.
    if (
        public_byok_enabled()
        and os.getenv("SLATESAFE_LIVE_GEMINI", "false").lower() == "true"
        and not gemini_api_key
    ):
        raise HTTPException(
            status_code=428,
            detail="This public deployment requires your own Gemini API key for AI handoffs.",
        )
    if (
        public_byok_enabled()
        and os.getenv("SLATESAFE_LIVE_GEMINI", "false").lower() == "true"
    ):
        enforce_public_request_budget()
    try:
        return await evaluate_release_check(request, gemini_api_key)
    except PermissionError as error:
        raise HTTPException(status_code=428, detail=str(error)) from error
