# Competition audit — Agentic Cinema / ClickHouse track

Audit date: 3 September 2026. This is a build and proof checklist, not a claim
that an unverified cloud path has already run.

## What judges screen for first

The official rules use a pass/fail viability screen before scoring. A valid
entry needs a hosted, functional web/Android/iOS project; a public,
open-source repository with a visible license; a public English (or
English-subtitled) video of no more than three minutes; and actual runtime
use of both Google Cloud AI and the selected partner service.

For the ClickHouse track, the partner requirement is explicit: the project
must use the official `mcp-clickhouse` server at runtime against a ClickHouse
Cloud or self-hosted cluster. The code must be imported and called, not merely
named in documentation.

Sources: [hackathon overview](https://agentic-cinema.devpost.com/) and
[official rules](https://agentic-cinema.devpost.com/rules).

## SlateSafe evidence map

| Requirement | Evidence in this repository |
| --- | --- |
| Media workflow | Evidence-first release clearance for producers: hold, review, or clear before distribution. |
| Google Cloud AI | `google-adk` agent in `src/slatesafe/agent.py`; Vertex AI Gemini configuration is documented in `.env.example`. |
| ClickHouse at runtime | `ClickHouseMcpGateway` launches `mcp-clickhouse` and invokes `run_query`; `docker compose` starts a self-hosted cluster. |
| Agent safety | Deterministic policy decides rights status. Gemini receives evidence and may only explain it, never override it. |
| Coherent product | Release brief, evidence-backed greenlight packet, remediation queue, explicit provenance, and downloadable producer packet. |
| Reproducibility | `docker compose up --build`, fictional seed ledger, tests, Apache-2.0 license, and local demo guide. |

## Highest-scoring demonstration sequence

1. Open the hosted app and state the producer problem in one sentence: an
   unlicensed background asset can stop delivery after picture lock.
2. Submit a release brief with three asset IDs. Show the visible `HOLD`, the
   exact timecode, the ledger evidence, and its remediation.
3. Show the packet provenance: `Live ClickHouse MCP`, packet ID, and timestamp.
4. Show the server trace/log line proving `mcp-clickhouse` issued `run_query`.
5. Enable the Gemini/ADK production configuration and show the concise producer
   handoff. Call out the guardrail: Gemini explains verified evidence but does
   not create clearances.
6. Remove the blocking asset and rerun the check to show a data-driven decision
   change. Download the producer packet.

## Scoring strategy

The four Stage Two dimensions are equally weighted: technical implementation,
design, potential impact, and quality of idea. SlateSafe is strongest when the
demo emphasizes that it is not generic database chat: it makes a consequential
release decision with a verifiable chain of evidence and a concrete next action.

Use one named audience throughout: release producers at studios and streamers.
Use one measurable framing: catching a clearance conflict before final delivery
avoids a last-minute edit, re-licensing negotiation, or regional release delay.

## Release gate still required before submission

- Deploy the same container to a genuinely spend-safe hosted runtime.
- Run the Gemini/ADK path with verified Google Cloud credentials and record it.
- Publish the three-minute demo to YouTube or Vimeo.
- Add the hosted URL, repository URL, video URL, and factual track answers to
  Devpost.

Do not represent the demo fixture as a live ledger or claim Gemini was invoked
until those calls are shown in the recording.
