const get = (id) => document.getElementById(id);
let lastDecision = null;

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
})[character]);
const timecodes = () => Object.fromEntries(get("timecodes").value.split(",").map((item) => {
  const [assetId, timecode] = item.split("=").map((part) => part.trim());
  return [assetId, timecode];
}).filter(([assetId, timecode]) => assetId && timecode));
const formValue = () => ({
  title: get("title").value,
  territory: get("territory").value.toUpperCase(),
  release_date: get("release-date").value,
  script_excerpt: get("script").value,
  asset_ids: get("assets").value.split(",").map((item) => item.trim()).filter(Boolean),
  asset_timecodes: timecodes(),
});

function findingCard(finding) {
  return `<article class="finding ${finding.severity}">
    <div class="finding-top"><span>${escapeHtml(finding.severity)}</span><code>${escapeHtml(finding.asset_id)}</code><time>${escapeHtml(finding.timecode)}</time></div>
    <h3>${escapeHtml(finding.category)}</h3><p>${escapeHtml(finding.detail)}</p>
    <div class="evidence"><b>Ledger evidence</b>${escapeHtml(finding.evidence)}</div>
    <div class="remediation"><b>Next best action</b>${escapeHtml(finding.remediation)}</div>
  </article>`;
}

function render(decision) {
  const view = get("result-template").content.cloneNode(true);
  view.querySelector("h2").textContent = decision.status === "blocker" ? "HOLD" : decision.status.toUpperCase();
  view.querySelector("h2").classList.add(decision.status);
  view.querySelector(".one-line").textContent = decision.one_line;
  view.querySelector(".confidence strong").textContent = `${decision.ledger_coverage}%`;
  const modeLabel = decision.evidence_mode === "live_clickhouse_mcp" ? "Live ClickHouse MCP" : "Fictional demo fixture";
  const evaluatedAt = new Date(decision.evaluated_at).toLocaleString();
  view.querySelector(".packet-meta").innerHTML = `<span>${escapeHtml(decision.packet_id)}</span><span>${escapeHtml(modeLabel)}</span><span>${escapeHtml(evaluatedAt)}</span>`;
  view.querySelector(".trace").innerHTML = `<p>DECISION TRACE</p>${decision.trace.map((step, i) => `<div><span>0${i + 1}</span>${escapeHtml(step)}</div>`).join("")}`;
  const summary = decision.gemini_summary ? `<div class="gemini-summary"><b>Gemini producer handoff</b>${escapeHtml(decision.gemini_summary)}</div>` : "";
  view.querySelector(".findings").innerHTML = `${summary}<p>FINDINGS / ${decision.findings.length}</p>${decision.findings.map(findingCard).join("")}`;
  const result = get("decision"); result.replaceChildren(view);
}

get("check").addEventListener("click", async () => {
  const button = get("check"); button.disabled = true; button.textContent = "Querying release ledger…";
  try {
    const response = await fetch("/api/release-check", {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(formValue())});
    if (!response.ok) throw new Error("The release brief needs valid fields.");
    lastDecision = await response.json();
    render(lastDecision);
    get("download").disabled = false;
  } catch (error) {
    get("decision").innerHTML = `<div class="error">${error.message}</div>`;
  } finally { button.disabled = false; button.innerHTML = "Run release check <span>→</span>"; }
});

get("download").addEventListener("click", () => {
  if (!lastDecision) return;
  const blob = new Blob([JSON.stringify(lastDecision, null, 2)], {type: "application/json"});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${lastDecision.packet_id.toLowerCase()}-producer-packet.json`;
  link.click();
  URL.revokeObjectURL(link.href);
});
