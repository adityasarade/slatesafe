const get = (id) => document.getElementById(id);
const formValue = () => ({
  title: get("title").value,
  territory: get("territory").value.toUpperCase(),
  release_date: get("release-date").value,
  script_excerpt: get("script").value,
  asset_ids: get("assets").value.split(",").map((item) => item.trim()).filter(Boolean),
});

function findingCard(finding) {
  return `<article class="finding ${finding.severity}">
    <div class="finding-top"><span>${finding.severity}</span><code>${finding.asset_id}</code><time>${finding.timecode}</time></div>
    <h3>${finding.category}</h3><p>${finding.detail}</p>
    <div class="evidence"><b>Ledger evidence</b>${finding.evidence}</div>
    <div class="remediation"><b>Next best action</b>${finding.remediation}</div>
  </article>`;
}

function render(decision) {
  const view = get("result-template").content.cloneNode(true);
  view.querySelector("h2").textContent = decision.status === "blocker" ? "HOLD" : decision.status.toUpperCase();
  view.querySelector("h2").classList.add(decision.status);
  view.querySelector(".one-line").textContent = decision.one_line;
  view.querySelector(".confidence strong").textContent = `${decision.confidence}%`;
  view.querySelector(".trace").innerHTML = `<p>DECISION TRACE</p>${decision.trace.map((step, i) => `<div><span>0${i + 1}</span>${step}</div>`).join("")}`;
  const summary = decision.gemini_summary ? `<div class="gemini-summary"><b>Gemini producer handoff</b>${decision.gemini_summary}</div>` : "";
  view.querySelector(".findings").innerHTML = `${summary}<p>FINDINGS / ${decision.findings.length}</p>${decision.findings.map(findingCard).join("")}`;
  const result = get("decision"); result.replaceChildren(view);
}

get("check").addEventListener("click", async () => {
  const button = get("check"); button.disabled = true; button.textContent = "Querying release ledger…";
  try {
    const response = await fetch("/api/release-check", {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(formValue())});
    if (!response.ok) throw new Error("The release brief needs valid fields.");
    render(await response.json());
  } catch (error) {
    get("decision").innerHTML = `<div class="error">${error.message}</div>`;
  } finally { button.disabled = false; button.innerHTML = "Run release check <span>→</span>"; }
});
