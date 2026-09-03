from fastapi.testclient import TestClient

from slatesafe import agent
from slatesafe import app as web
from slatesafe.agent import build_release_agent, deterministic_release_check
from slatesafe.app import app
from slatesafe.models import EvidenceMode, ReleaseCheckRequest, Severity

REQUEST = {
    "title": "The Last Harbor",
    "territory": "IN",
    "release_date": "2026-10-15",
    "script_excerpt": "The taxi carries a neon panel as the song plays in the diner.",
    "asset_ids": ["NEON-CAB-07"],
}


def test_expired_clearance_holds_release() -> None:
    decision = deterministic_release_check(
        ReleaseCheckRequest(
            title="The Last Harbor",
            territory="IN",
            release_date="2026-10-15",
            script_excerpt="The taxi carries a neon panel as the song plays in the diner.",
            asset_ids=["NEON-CAB-07", "SONG-HARBOR-21"],
        )
    )
    assert decision.status is Severity.BLOCKER
    assert decision.packet_id.startswith("SS-")
    assert decision.evidence_mode is EvidenceMode.DEMO_FIXTURE
    assert decision.evaluated_at.tzinfo is not None
    assert any(finding.asset_id == "NEON-CAB-07" for finding in decision.findings)


def test_unknown_asset_fails_closed_for_provenance() -> None:
    decision = deterministic_release_check(
        ReleaseCheckRequest(
            title="The Last Harbor",
            territory="IN",
            release_date="2026-08-01",
            script_excerpt="The crew needs a source record for a background prop in the diner.",
            asset_ids=["UNTRACKED-PROP-99"],
        )
    )
    assert decision.status is Severity.BLOCKER


def test_adk_agent_exposes_only_the_read_only_clearance_tool() -> None:
    agent = build_release_agent()
    assert len(agent.tools) == 1
    assert agent.tools[0].__name__ == "query_clearance_ledger"


def test_public_byok_fails_closed_before_any_operator_resource_call(monkeypatch) -> None:
    monkeypatch.setenv("SLATESAFE_LIVE_GEMINI", "true")
    monkeypatch.setenv("SLATESAFE_PUBLIC_BYOK", "true")
    monkeypatch.setenv("SLATESAFE_LIVE_LEDGER", "true")

    async def should_not_run(*_args, **_kwargs):
        raise AssertionError("The request reached the operator-backed evaluator.")

    monkeypatch.setattr(web, "evaluate_release_check", should_not_run)

    response = TestClient(app).post("/api/release-check", json=REQUEST)

    assert response.status_code == 428
    assert "own Gemini API key" in response.json()["detail"]


def test_public_byok_forwards_key_without_returning_or_persisting_it(monkeypatch) -> None:
    monkeypatch.setenv("SLATESAFE_LIVE_GEMINI", "true")
    monkeypatch.setenv("SLATESAFE_PUBLIC_BYOK", "true")
    received: list[str | None] = []

    async def fake_summary(_request, _findings, gemini_api_key=None) -> str:
        received.append(gemini_api_key)
        return "Evidence-backed producer handoff."

    monkeypatch.setattr(agent, "gemini_release_summary", fake_summary)
    visitor_key = "not-a-real-gemini-key-for-test-only"
    response = TestClient(app).post(
        "/api/release-check",
        json=REQUEST,
        headers={"X-SlateSafe-Gemini-Key": visitor_key},
    )

    assert response.status_code == 200
    assert received == [visitor_key]
    assert visitor_key not in response.text
