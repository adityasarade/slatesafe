# Final demo and submission runbook

This is a truth-first runbook for the final Agentic Cinema submission. Do not
replace a required live result with a fixture, another project URL, or a video
that cannot be reviewed publicly.

## Gates before recording

All four gates must be satisfied before presenting SlateSafe as complete:

| Gate | Required proof |
| --- | --- |
| Hosted application | A stable HTTPS URL that loads the SlateSafe control room. |
| ClickHouse | `SLATESAFE_LIVE_LEDGER=true` against the intended ClickHouse Cloud service; a check response reports `live_clickhouse_mcp`. |
| Gemini / ADK | A genuine `SLATESAFE_LIVE_GEMINI=true` run returns a non-empty `gemini_summary` and the trace says the ADK call completed. |
| Cost boundary | ClickHouse is confirmed as a no-card trial or within a known free credit, and Cloud Run / Gemini use has an account-holder-approved cap. Budget alerts alone are not a hard guarantee. |

The public demo should use `SLATESAFE_PUBLIC_BYOK=true` so that no visitor can
spend an operator Gemini API key. It requires each visitor's own key only for
the Gemini handoff; requests without a key are rejected before the ClickHouse
query. See [public BYOK security](PUBLIC-BYOK-SECURITY.md).

For the recorded judge proof, use a controlled, account-holder-approved Gemini
run and show the actual response. Do not say the public BYOK path is Vertex AI;
it constructs an ADK Gemini client from the visitor's key. The video must make
the verified Google runtime and the official ClickHouse MCP query visible.

## 2:45 recording script

Use fictional records only. Keep the recording continuous, in English, and
under three minutes.

| Time | Screen and narration |
| --- | --- |
| 0:00–0:15 | State the problem: a picture-locked release can still be delayed by one timecoded asset with the wrong rights window. |
| 0:15–0:35 | Show the live hosted SlateSafe form. Enter `Neon Harbor Trailer`, territory `IN`, release date `2026-09-01`, then the `MUSIC-NEON-07` and `LOGO-COLA-22` asset IDs with their timecodes. |
| 0:35–1:10 | Run the check. Highlight `Live ClickHouse MCP`, the packet ID, 100% ledger coverage, and the HOLD. Read the exact logo reason: it is not licensed for IN and expired on 2026-08-31. |
| 1:10–1:30 | Show the ClickHouse MCP server trace/log proving `run_query` completed. Then point out that the Gemini/ADK handoff is constrained to explain this verified evidence. |
| 1:30–1:55 | Show the actual non-empty Gemini producer handoff and its ADK completion trace. Do not substitute a fixture or prewritten text. |
| 1:55–2:20 | Remove `LOGO-COLA-22` and rerun. Show the CLEAR result and the retained active music right through 2026-12-31. |
| 2:20–2:35 | Download the producer packet and show `evidence_mode: live_clickhouse_mcp`, the trace, and the remediation / clear evidence. |
| 2:35–2:45 | Close with the producer outcome: one defensible release decision with a source, condition, timecode, and next action. |

## Devpost completion checklist

Enter only the following factual values after the corresponding evidence exists:

- **Repository:** `https://github.com/adityasarade/slatesafe`
- **Hosted project:** the final HTTPS SlateSafe URL
- **Video:** the final public YouTube or Vimeo URL
- **Partner track:** ClickHouse
- **Project story:** [`docs/DEVPOST.md`](DEVPOST.md)
- **Thumbnail:** `assets/slatesafe-submission-thumbnail.png`

The current draft must not be submitted until the hosted URL and public video
are populated. Before pressing Devpost's final submit button, recheck that the
demo link is publicly viewable without an account and that every claim in the
story has visible evidence in the recording.
