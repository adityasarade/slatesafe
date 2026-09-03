# Public bring-your-own-key deployment

Use this mode for a public SlateSafe demo when the operator must not pay for
visitor-triggered Gemini calls.

## Required configuration

Set these environment variables on the service:

```text
SLATESAFE_LIVE_GEMINI=true
SLATESAFE_PUBLIC_BYOK=true
```

Do **not** set `GOOGLE_API_KEY`, `GEMINI_API_KEY`, or an application-default
credential with Vertex AI permission on the public runtime. Use a dedicated
Cloud Run runtime service account with no `roles/aiplatform.user` grant.

With public BYOK enabled, a Gemini handoff fails closed unless the requester
supplies `X-SlateSafe-Gemini-Key`. The API key is accepted only in an HTTPS
header, is used to construct the request-scoped ADK Gemini client, and is not
written to process environment, logs, storage, response data, or downloaded
producer packets. It is not accepted in a query string or JSON body.

The clearance ledger remains a server-side ClickHouse MCP integration. Its
least-privilege credentials must be delivered as deployment secrets, never
committed to the repository or exposed to the browser.

## Deployment review checklist

1. Confirm `.env` is excluded from the image and Git (`.dockerignore` and
   `.gitignore` cover it).
2. Inspect the deployed service variables: public BYOK is true, no operator
   Gemini API key is present, and the runtime service account has no Vertex AI
   user role.
3. Serve only over Cloud Run HTTPS; do not terminate TLS at an untrusted proxy.
4. Run one request without a key. It must return HTTP 428 before any Gemini or
   ClickHouse MCP call. Then run a request with a visitor-controlled key and
   confirm the downloaded packet contains no key.
5. Never turn on `SLATESAFE_LIVE_GEMINI` without `SLATESAFE_PUBLIC_BYOK` for a
   public service. That private operator mode is only for a controlled demo.

This eliminates spending of an operator Gemini API key for visitor requests.
It cannot prevent a visitor from spending their own key, so the UI identifies
that responsibility before they run a live handoff.
