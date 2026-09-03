# SlateSafe — Devpost project story

## Inspiration

The last mile of a film or episodic release is full of invisible risk. A producer may have a picture-locked cut, but a background logo, a music cue with the wrong territorial window, or an unverified poster can still stop delivery. The evidence sits in spreadsheets, email attachments, rights databases, and asset-management systems; by the time people reconcile it manually, the release date is already under pressure.

SlateSafe turns that late-stage scramble into a clear production decision: **hold, review, or clear**—with a specific asset, a specific piece of ledger evidence, and the next best remediation action.

## What it does

1. A producer enters a release brief: territory, release date, scene context, and asset IDs from the cut.
2. SlateSafe queries the clearance-event ledger through the official `mcp-clickhouse` MCP server.
3. The system evaluates every asset against active rights windows and territory coverage.
4. A Gemini Enterprise ADK release-counsel agent turns only the verified evidence into a short producer handoff. It cannot invent or override a clearance status.
5. The control room presents a visual greenlight packet with a traceable decision and a remediation queue.

## How we built it

- **Google Cloud / Gemini:** `google-adk` creates the release-counsel agent. The live path uses Google Cloud credentials and a Gemini model to produce a constrained producer summary from verified evidence.
- **ClickHouse:** `mcp-clickhouse`, ClickHouse's official MCP server, is launched at runtime and called with `run_query`. It reads the current clearance ledger using a least-privilege, read-only account.
- **Product:** FastAPI serves the workflow; a purpose-built HTML/CSS/JavaScript interface lets a nontechnical release producer understand exactly why a release is held.
- **Safety:** the application treats the ClickHouse result as the authority. Gemini can explain an outcome but cannot create a clearance record or change a hold into a clear.

## Challenges we ran into

The difficult part was not generating a risk list—it was making every conclusion auditable. We designed the workflow so that a missing record is a visible review or blocker, never a confident AI guess. We also separated the fully runnable fictional-data demo from the live ledger path, so judges can inspect the product immediately while the production configuration clearly demonstrates its Gemini/ADK and ClickHouse MCP calls.

## Accomplishments we’re proud of

- A complete producer experience rather than a database chat interface.
- Evidence-first decisioning that prevents hallucinated release approvals.
- A real official ClickHouse MCP gateway, verified against ClickHouse SQL Playground during development.
- A constrained Gemini ADK handoff that makes the result useful to an actual production team.

## What we learned

Media workflows are deeply temporal. A license can be valid for one territory and release date but block another; a useful agent has to expose those conditions, not hide them behind a generic answer. MCP gives the model an inspectable bridge to the operational system of record, while deterministic policy protects the final decision.

## What’s next

We would connect the service to a studio’s asset-management and rights systems, ingest timecoded detection events from the edit, and add role-based producer approvals. The core decision contract remains the same: every greenlight needs evidence.

## Built with

Python, FastAPI, Google Agent Development Kit (ADK), Gemini, Google Cloud, Vertex AI, ClickHouse, Model Context Protocol (MCP), mcp-clickhouse, Uvicorn, HTML, CSS, JavaScript
