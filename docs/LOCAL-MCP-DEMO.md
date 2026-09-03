# Zero-cost local MCP demo

This path runs the product and a self-hosted ClickHouse ledger locally. It is
useful for a reproducible demo without deploying a cloud resource or enabling
billing.

## Start the full stack

```bash
docker compose up --build
```

Open <http://127.0.0.1:8010>. The app runs with
`SLATESAFE_LIVE_LEDGER=true`, so each release check launches the official
`mcp-clickhouse` server and uses its `run_query` tool against the local ledger.
The browser never receives ClickHouse credentials.

## Demo sequence

1. Set territory to `IN` and release date to `2026-09-01`.
2. Enter `MUSIC-NEON-07`, `LOGO-COLA-22`, and `ART-POSTER-11`.
3. Run the release check. The US-only, expired `LOGO-COLA-22` record creates a
   visible hold for India; the other records remain traceable evidence.
4. Change the asset list to the two cleared assets and run the check again to
   show the decision change.

## Gemini recording pass

The local ledger demo costs nothing. To record a true Gemini/ADK handoff,
provide Google Cloud Application Default Credentials and set
`SLATESAFE_LIVE_GEMINI=true` before starting the stack. Do this only in a
project with a confirmed spend-safe billing/credit path.

All seed data is fictional.
The Compose-only ClickHouse credential is also fictional and is scoped to the
local container; do not reuse it outside this demo.
