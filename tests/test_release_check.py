from slatesafe.agent import deterministic_release_check
from slatesafe.models import ReleaseCheckRequest, Severity


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
    assert any(finding.asset_id == "NEON-CAB-07" for finding in decision.findings)


def test_unknown_asset_requires_provenance_review() -> None:
    decision = deterministic_release_check(
        ReleaseCheckRequest(
            title="The Last Harbor",
            territory="IN",
            release_date="2026-08-01",
            script_excerpt="The crew needs a source record for a background prop in the diner.",
            asset_ids=["UNTRACKED-PROP-99"],
        )
    )
    assert decision.status is Severity.REVIEW
