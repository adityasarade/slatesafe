from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    BLOCKER = "blocker"
    REVIEW = "review"
    CLEAR = "clear"


class EvidenceMode(StrEnum):
    """Make the provenance of a release packet explicit to the producer."""

    DEMO_FIXTURE = "demo_fixture"
    LIVE_CLICKHOUSE_MCP = "live_clickhouse_mcp"


class Finding(BaseModel):
    asset_id: str
    timecode: str
    category: str
    detail: str
    severity: Severity
    evidence: str
    remediation: str


class ReleaseCheckRequest(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    territory: str = Field(min_length=2, max_length=8)
    release_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    script_excerpt: str = Field(min_length=20, max_length=6000)
    asset_ids: list[str] = Field(min_length=1, max_length=50)
    asset_timecodes: dict[str, str] = Field(default_factory=dict)


class ReleaseDecision(BaseModel):
    packet_id: str
    title: str
    status: Severity
    one_line: str
    ledger_coverage: int = Field(ge=0, le=100)
    findings: list[Finding]
    trace: list[str]
    evidence_mode: EvidenceMode
    evaluated_at: datetime
    gemini_summary: str | None = None
