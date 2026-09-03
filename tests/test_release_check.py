from slatesafe.agent import build_release_agent, deterministic_release_check
from slatesafe.models import EvidenceMode, ReleaseCheckRequest, Severity


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
