# SlateSafe

**An evidence-first release-readiness control room for production teams.**

SlateSafe finds the moments that will hold up a media release before the team spends time on a late-stage legal scramble. A producer supplies a release brief and the asset IDs detected in the cut. The system queries the clearance ledger through the official ClickHouse MCP server, then uses a Gemini-powered Google Cloud Agent Development Kit (ADK) agent to explain a specific, traceable greenlight decision.

> All bundled records and story content are fictional. SlateSafe is a hackathon prototype, not legal advice.

## Why this matters

Rights clearance, music windows, and delivery metadata arrive from scattered departments at different times. A release producer has to reconcile hundreds of timecoded assets against territories and release dates; one expired cue can block the final delivery.

SlateSafe makes this operational rather than conversational:

1. Gemini Enterprise Agent Platform receives the release brief and scene context.
2. The agent requests policy evidence from `mcp-clickhouse`—the official ClickHouse MCP server.
3. ClickHouse returns the current rights window for every asset.
4. The agent creates a hold / review / clear decision and a remediation queue. It never invents clearance status.

## Contest compliance

- **Google Cloud / Gemini:** `google-adk` defines the Gemini release-counsel agent. The application must be run with Google Cloud Application Default Credentials and Vertex AI configuration in production.
- **ClickHouse:** `slatesafe.clickhouse_mcp.ClickHouseMcpGateway` launches the official `mcp-clickhouse` server and invokes `run_query` at runtime.
- **No other AI provider:** the project uses only Gemini through Google Cloud. The deterministic policy layer is standard application code, not an AI service.
- **Open source:** Apache-2.0 license is included at repository root.

## Run locally

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/), a Google Cloud project with Vertex AI enabled, and a ClickHouse Cloud cluster.

```bash
uv sync --all-groups
cp .env.example .env
uv run uvicorn slatesafe.app:app --reload
```

Open `http://127.0.0.1:8000`. The included demo path is deterministic and uses fictional records so it can be reviewed without credentials. Before submission, configure real services and use the live `ClickHouseMcpGateway` in the deployed Cloud Run service.

### Run the actual MCP path without cloud spend

For a reproducible local ClickHouse ledger and the official MCP runtime,
run `docker compose up --build` and open `http://127.0.0.1:8010`.
See [the zero-cost local demo guide](docs/LOCAL-MCP-DEMO.md).
This enables the live ledger switch but intentionally leaves the Gemini call
off until a confirmed spend-safe Google Cloud path is available.

## Required production environment

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GEMINI_MODEL="gemini-2.5-flash"

export CLICKHOUSE_HOST="your-instance.clickhouse.cloud"
export CLICKHOUSE_USER="slatesafe_agent"
export CLICKHOUSE_PASSWORD="..."
export CLICKHOUSE_DATABASE="slatesafe"
export CLICKHOUSE_SECURE=true
```

Create a least-privilege ClickHouse user with access only to the release-ledger tables. The official MCP server is read-only by default; SlateSafe explicitly retains that default.

## ClickHouse schema

```sql
CREATE DATABASE IF NOT EXISTS slatesafe;

CREATE TABLE slatesafe.clearance_events (
  asset_id String,
  category LowCardinality(String),
  territories Array(String),
  expires_at Date,
  release_date Date,
  evidence_url String,
  ingested_at DateTime DEFAULT now()
) ENGINE = MergeTree
ORDER BY (asset_id, expires_at);
```

## Quality checks

```bash
uv run ruff check .
uv run pytest
```

## Deployment checklist

1. Create a new Google Cloud project (or obtain Owner/editor access to an eligible project), enable Vertex AI and Cloud Run, then deploy this service to Cloud Run.
2. Create a ClickHouse Cloud service and a least-privilege `slatesafe_agent` user; load the fictional demo ledger.
3. Record a 3-minute product walkthrough showing an actual Gemini/ADK run and the corresponding official ClickHouse MCP tool query.
4. Publish this repository to GitHub with the Apache-2.0 license visible, then submit the Cloud Run URL, GitHub URL, and public YouTube/Vimeo demo on Devpost.
