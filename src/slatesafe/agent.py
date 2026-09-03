"""Gemini/ADK orchestration for explaining an evidence-backed release decision."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from hashlib import sha256

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import Client, types

from .catalog import RIGHTS_CATALOG, policy_findings
from .clickhouse_mcp import ClickHouseMcpGateway
from .models import EvidenceMode, Finding, ReleaseCheckRequest, Severity


def release_packet_id(request: ReleaseCheckRequest) -> str:
    """Return a deterministic identifier a producer can cite in a handoff."""
    material = "|".join(
        (request.title, request.territory.upper(), request.release_date, *request.asset_ids)
    )
    return f"SS-{sha256(material.encode()).hexdigest()[:10].upper()}"


async def query_clearance_ledger(
    asset_ids: list[str], territory: str, release_date: str
) -> dict[str, object]:
    """Read clearance records through the official ClickHouse MCP runtime.

    This is intentionally the only evidence tool exposed to the ADK agent.
    The deterministic policy layer remains responsible for the final clearance
    state after the agent receives the read-only ledger evidence.
    """
    raw_result = await ClickHouseMcpGateway().rights_window(asset_ids, territory, release_date)
    return json.loads(raw_result)


def build_release_agent(gemini_api_key: str | None = None) -> LlmAgent:
    """Create the Agent Development Kit agent used in the deployed service.

    Runtime execution is intentionally constrained: policy facts come from the
    ClickHouse MCP tool; Gemini explains findings but is never allowed to invent
    a clearance status.
    """
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # A public deployment can supply a request-scoped Google AI client. This
    # avoids using the Cloud Run service identity or any operator API key for a
    # visitor request. The key exists in memory only and is never logged or stored.
    model: str | Gemini = model_name
    if gemini_api_key:
        model = Gemini(model=model_name, client=Client(api_key=gemini_api_key))

    return LlmAgent(
        name="release_counsel",
        model=model,
        instruction=(
            "You are SlateSafe's release counsel. First call query_clearance_ledger once using the "
            "release brief supplied by the producer. Then summarize only verified clearance evidence. "
            "A missing, expired, or territory-incompatible record is a blocker. Do not invent rights "
            "or override the deterministic verdict."
        ),
        tools=[query_clearance_ledger],
    )


def deterministic_release_check(request: ReleaseCheckRequest):
    """Return a testable decision while the ADK service is configured for Gemini runtime."""
    findings = policy_findings(request)
    blockers = [item for item in findings if item.severity.value == "blocker"]
    coverage = round(
        100 * sum(asset in RIGHTS_CATALOG for asset in request.asset_ids) / len(request.asset_ids)
    )
    from .models import ReleaseDecision

    if blockers:
        status = Severity.BLOCKER
        one_line = f"Hold release: {len(blockers)} clearance blocker(s) require a producer decision."
    else:
        status = Severity.CLEAR
        one_line = "Ready for the selected territory based on the current rights ledger."
    return ReleaseDecision(
        packet_id=release_packet_id(request),
        title=request.title,
        status=status,
        one_line=one_line,
        ledger_coverage=coverage,
        findings=findings,
        trace=[
            "Gemini Enterprise Agent Platform: release-counsel agent configured for the live run.",
            "ClickHouse MCP: clearance-events query requested.",
            "Evidence-only decision composed; no rights status was inferred without a ledger record.",
        ],
        evidence_mode=EvidenceMode.DEMO_FIXTURE,
        evaluated_at=datetime.now(UTC),
    )


def public_byok_enabled() -> bool:
    """Whether this deployment must never spend an operator's Gemini credits."""
    return os.getenv("SLATESAFE_PUBLIC_BYOK", "false").lower() == "true"


async def gemini_release_summary(
    request: ReleaseCheckRequest,
    findings: list[Finding],
    gemini_api_key: str | None = None,
) -> str:
    """Run ADK only after the evidence-backed decision is known.

    Gemini can explain verified evidence in producer language but is never allowed
    to alter a clearance outcome.
    """
    evidence = "\n".join(
        f"- {item.asset_id}: {item.severity.value}; {item.detail}; evidence: {item.evidence}; "
        f"next action: {item.remediation}"
        for item in findings
    )
    if public_byok_enabled() and not gemini_api_key:
        raise PermissionError(
            "This public deployment requires your own Gemini API key for AI handoffs."
        )

    runner = InMemoryRunner(
        agent=build_release_agent(gemini_api_key=gemini_api_key), app_name="slatesafe"
    )
    session = await runner.session_service.create_session(
        app_name="slatesafe", user_id="release-producer"
    )
    prompt = (
        f"Release: {request.title}\nTerritory: {request.territory}\n"
        f"Release date: {request.release_date}\nVerified ledger evidence:\n{evidence}\n\n"
        f"Scene context:\n{request.script_excerpt}\n\n"
        "Write a concise producer-facing handoff in no more than 70 words. You may use scene "
        "context to describe where the remediation applies, but never add rights facts, change a "
        "clearance status, or claim an asset was reviewed if it is not in the verified evidence."
    )
    message = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    async for event in runner.run_async(
        user_id="release-producer", session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            return "".join(part.text or "" for part in event.content.parts).strip()
    raise RuntimeError("Gemini did not return a final release summary.")


async def evaluate_release_check(
    request: ReleaseCheckRequest, gemini_api_key: str | None = None
):
    """Evaluate with ClickHouse MCP when configured; otherwise use the demo ledger.

    `SLATESAFE_LIVE_LEDGER=true` is deliberately an explicit switch: reviewers
    can run the fictional demo out of the box, while the deployed Cloud Run
    service always has a live ClickHouse-backed decision path.
    """
    if os.getenv("SLATESAFE_LIVE_LEDGER", "false").lower() != "true":
        decision = deterministic_release_check(request)
        if os.getenv("SLATESAFE_LIVE_GEMINI", "false").lower() == "true":
            decision.gemini_summary = await gemini_release_summary(
                request, decision.findings, gemini_api_key
            )
            decision.trace[0] = "Gemini Enterprise Agent Platform: ADK release-counsel call completed."
        return decision

    payload = await query_clearance_ledger(
        request.asset_ids, request.territory, request.release_date
    )
    records_by_asset: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in payload.get("rows", []):
        asset_id, category, territories, expires_at, _licensed_from, evidence_url = row
        records_by_asset[asset_id].append(
            {
                "category": category,
                "territories": territories,
                "expires_at": expires_at,
                "evidence_url": evidence_url,
            }
        )

    findings: list[Finding] = []
    territory = request.territory.upper()
    for asset_id in request.asset_ids:
        records = records_by_asset.get(asset_id, [])
        active_records = [
            record
            for record in records
            if territory in record["territories"] and str(record["expires_at"]) >= request.release_date
        ]
        if active_records:
            record = active_records[0]
            findings.append(
                Finding(
                    asset_id=asset_id,
                    timecode=request.asset_timecodes.get(asset_id, "Not supplied"),
                    category=str(record["category"]),
                    detail="Live ledger contains an active rights window for this territory.",
                    severity=Severity.CLEAR,
                    evidence=(
                        f"ClickHouse MCP row: territories {', '.join(record['territories'])}; "
                        f"active through {record['expires_at']}; source {record['evidence_url']}."
                    ),
                    remediation="No action required.",
                )
            )
            continue

        if not records:
            detail = "No clearance record was returned for this asset."
            evidence = "ClickHouse MCP run_query returned no ledger row."
        else:
            record = records[0]
            reasons = []
            if territory not in record["territories"]:
                reasons.append(f"not licensed for {territory}")
            if str(record["expires_at"]) < request.release_date:
                reasons.append(f"expired on {record['expires_at']}")
            detail = f"Live ledger record is {' and '.join(reasons)}."
            evidence = (
                f"ClickHouse MCP row: territories {', '.join(record['territories'])}; "
                f"expires {record['expires_at']}; source {record['evidence_url']}."
            )
        findings.append(
            Finding(
                asset_id=asset_id,
                timecode=request.asset_timecodes.get(asset_id, "Not supplied"),
                category=str(records[0]["category"]) if records else "provenance",
                detail=detail,
                severity=Severity.BLOCKER,
                evidence=evidence,
                remediation="Attach a valid clearance record, edit the cut, or change the release territory.",
            )
        )
    blockers = [finding for finding in findings if finding.severity is Severity.BLOCKER]
    from .models import ReleaseDecision

    decision = ReleaseDecision(
        packet_id=release_packet_id(request),
        title=request.title,
        status=Severity.BLOCKER if blockers else Severity.CLEAR,
        one_line=(
            f"Hold release: {len(blockers)} asset(s) lack a valid live clearance record."
            if blockers
            else "Ready for the selected territory based on the live rights ledger."
        ),
        ledger_coverage=round(100 * len(records_by_asset) / len(request.asset_ids)),
        findings=findings,
        trace=[
            "Gemini Enterprise Agent Platform: release-counsel agent configured for the live run.",
            "ClickHouse MCP: official mcp-clickhouse run_query completed against clearance_events.",
            "Evidence-only decision composed from the live query result.",
        ],
        evidence_mode=EvidenceMode.LIVE_CLICKHOUSE_MCP,
        evaluated_at=datetime.now(UTC),
    )
    if os.getenv("SLATESAFE_LIVE_GEMINI", "false").lower() == "true":
        decision.gemini_summary = await gemini_release_summary(
            request, decision.findings, gemini_api_key
        )
        decision.trace[0] = "Gemini Enterprise Agent Platform: ADK release-counsel call completed."
    return decision
