"""Deterministic release-policy layer used for live and demo-safe checks.

This layer deliberately makes no AI judgement: it establishes policy facts that
the Gemini agent must cite. In production, the same query is executed over the
ClickHouse MCP server; demo mode uses the bundled fictional fixture.
"""

from __future__ import annotations

from datetime import date

from slatesafe.models import Finding, ReleaseCheckRequest, Severity

RIGHTS_CATALOG = {
    "NEON-CAB-07": {
        "category": "brand clearance",
        "territories": ["US", "CA"],
        "expires": "2026-09-01",
        "remediation": "Replace the vehicle side panel or secure a worldwide renewal.",
    },
    "SONG-HARBOR-21": {
        "category": "music synchronization",
        "territories": ["US", "GB", "IN"],
        "expires": "2027-01-31",
        "remediation": "Swap to the pre-cleared alternate cue or negotiate an SVOD extension.",
    },
    "POSTER-ORBIT-03": {
        "category": "artwork clearance",
        "territories": ["US", "IN"],
        "expires": "2026-12-31",
        "remediation": "Blur the poster in the diner shot or attach the distributor permission.",
    },
}


def policy_findings(request: ReleaseCheckRequest) -> list[Finding]:
    """Resolve known asset-clearance rules; all records are fictional demo data."""
    release_day = date.fromisoformat(request.release_date)
    findings: list[Finding] = []
    for asset_id in request.asset_ids:
        record = RIGHTS_CATALOG.get(asset_id)
        if not record:
            findings.append(
                Finding(
                    asset_id=asset_id,
                    timecode=request.asset_timecodes.get(asset_id, "Not supplied"),
                    category="provenance",
                    detail="No clearance record exists in the rights ledger.",
                    severity=Severity.BLOCKER,
                    evidence="ClickHouse lookup returned no active record.",
                    remediation="Attach source and clearance evidence before picture lock.",
                )
            )
            continue
        expired = date.fromisoformat(record["expires"]) < release_day
        territory_allowed = request.territory.upper() in record["territories"]
        if expired or not territory_allowed:
            reason = "expired before release" if expired else "not licensed for requested territory"
            findings.append(
                Finding(
                    asset_id=asset_id,
                    timecode=request.asset_timecodes.get(asset_id, "Not supplied"),
                    category=record["category"],
                    detail=f"Clearance is {reason}.",
                    severity=Severity.BLOCKER,
                    evidence=(
                        f"Ledger rights window: {', '.join(record['territories'])}, "
                        f"through {record['expires']}."
                    ),
                    remediation=record["remediation"],
                )
            )
        else:
            findings.append(
                Finding(
                    asset_id=asset_id,
                    timecode=request.asset_timecodes.get(asset_id, "Not supplied"),
                    category=record["category"],
                    detail="Clearance record covers this release.",
                    severity=Severity.CLEAR,
                    evidence=f"Ledger rights window remains active through {record['expires']}.",
                    remediation="No action required.",
                )
            )
    return findings
