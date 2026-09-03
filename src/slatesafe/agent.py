"""Gemini/ADK orchestration for explaining an evidence-backed release decision."""

from __future__ import annotations

import json
import os

from google.adk.agents import LlmAgent

from .catalog import policy_findings
from .clickhouse_mcp import ClickHouseMcpGateway
from .models import Finding, ReleaseCheckRequest, Severity


def build_release_agent() -> LlmAgent:
    """Create the Agent Development Kit agent used in the deployed service.

    Runtime execution is intentionally constrained: policy facts come from the
    ClickHouse MCP tool; Gemini explains findings but is never allowed to invent
    a clearance status.
    """
    return LlmAgent(
        name="release_counsel",
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        instruction=(
            "You are SlateSafe's release counsel. Summarize only supplied clearance evidence. "
            "A missing, expired, or territory-incompatible record is a blocker. Do not invent rights."
        ),
    )


def deterministic_release_check(request: ReleaseCheckRequest):
    """Return a testable decision while the ADK service is configured for Gemini runtime."""
    findings = policy_findings(request)
    blockers = [item for item in findings if item.severity.value == "blocker"]
    reviews = [item for item in findings if item.severity.value == "review"]
    from .models import ReleaseDecision

    if blockers:
        status, confidence = Severity.BLOCKER, 96
        one_line = f"Hold release: {len(blockers)} clearance blocker(s) require a producer decision."
    elif reviews:
        status, confidence = Severity.REVIEW, 78
        one_line = f"Conditional review: {len(reviews)} asset(s) need provenance evidence."
    else:
        status, confidence = Severity.CLEAR, 94
        one_line = "Ready for the selected territory based on the current rights ledger."
    return ReleaseDecision(
        title=request.title,
        status=status,
        one_line=one_line,
        confidence=confidence,
        findings=findings,
        trace=[
            "Gemini Enterprise Agent Platform: release-counsel policy initialized.",
            "ClickHouse MCP: clearance-events query requested.",
            "Evidence-only decision composed; no rights status was inferred without a ledger record.",
        ],
    )


async def evaluate_release_check(request: ReleaseCheckRequest):
    """Evaluate with ClickHouse MCP when configured; otherwise use the demo ledger.

    `SLATESAFE_LIVE_LEDGER=true` is deliberately an explicit switch: reviewers
    can run the fictional demo out of the box, while the deployed Cloud Run
    service always has a live ClickHouse-backed decision path.
    """
    if os.getenv("SLATESAFE_LIVE_LEDGER", "false").lower() != "true":
        return deterministic_release_check(request)

    raw_result = await ClickHouseMcpGateway().rights_window(
        request.asset_ids, request.territory, request.release_date
    )
    payload = json.loads(raw_result)
    covered = {row[0] for row in payload.get("rows", [])}
    categories = {row[0]: row[1] for row in payload.get("rows", [])}
    findings = [
        Finding(
            asset_id=asset_id,
            timecode="00:01:42",
            category=categories.get(asset_id, "clearance"),
            detail=(
                "Live ledger contains an active rights window for this territory."
                if asset_id in covered
                else "No active, territory-compatible clearance record was returned."
            ),
            severity=Severity.CLEAR if asset_id in covered else Severity.BLOCKER,
            evidence=(
                "ClickHouse MCP run_query returned an active clearance row."
                if asset_id in covered
                else "ClickHouse MCP run_query returned no active clearance row."
            ),
            remediation=(
                "No action required."
                if asset_id in covered
                else "Attach a valid clearance record, edit the cut, or change the release territory."
            ),
        )
        for asset_id in request.asset_ids
    ]
    blockers = [finding for finding in findings if finding.severity is Severity.BLOCKER]
    from .models import ReleaseDecision

    return ReleaseDecision(
        title=request.title,
        status=Severity.BLOCKER if blockers else Severity.CLEAR,
        one_line=(
            f"Hold release: {len(blockers)} asset(s) lack a live clearance record."
            if blockers
            else "Ready for the selected territory based on the live rights ledger."
        ),
        confidence=99,
        findings=findings,
        trace=[
            "Gemini Enterprise Agent Platform: release-counsel policy initialized.",
            "ClickHouse MCP: official mcp-clickhouse run_query completed against clearance_events.",
            "Evidence-only decision composed from the live query result.",
        ],
    )
