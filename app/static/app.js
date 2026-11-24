// ED Cost Estimator front end. Plain JavaScript, no build step.
// All text from the server is inserted with textContent or escaped, never as raw HTML.

const $ = (id) => document.getElementById(id);
const AGENTS = [
  ["triage", "Safety screener", "Checks the request is a health problem and looks for emergency warning signs"],
  ["clinical", "Clinical planner", "Works out which visit level, tests and scans an ED would likely order"],
  ["pricing", "Pricing analyst", "Matches your insurer and prices the plan from the hospital's published rates"],
  ["advocate", "Patient advocate", "Explains the estimate, your rights and what to ask"],
];

const money = (n) => "$" + Math.round(Number(n)).toLocaleString("en-US");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const show = (el, on = true) => { el.hidden = !on; };
let priceFile = { hospital: "the hospital", updated: "" };  // filled in from /api/meta

function fillList(el, items) {
  el.replaceChildren(...(items || []).map((text) => Object.assign(document.createElement("li"), { textContent: text })));
  show(el, (items || []).length > 0);
}

// ---- Insurance picker -----------------------------------------------------
// The dropdown sends plain text ("Aetna", "no insurance", ""); the pricing agent does the matching.
const INSURER_LABELS = { "UHC": "UHC (UnitedHealthcare)", "CtCare": "CtCare (ConnectiCare)", "Medicare Advantage - UHC": "Medicare Advantage - UHC (UnitedHealthcare)", "Medicare Advantage - CtCare": "Medicare Advantage - CtCare (ConnectiCare)" };
const INSURER_HINTS = {
  "": "Not sure? Leave it. You will see the middle of all insurers' rates.",
  "no insurance": "You will see the hospital's discounted cash price.",
  "__other__": "Type it the way you would say it, for example \"Blue Cross through my job\".",
};

function insuranceText() {
  const choice = $("insurer").value;
  return choice === "__other__" ? $("insurance").value.trim() : choice;
}

function syncInsurer() {
  const choice = $("insurer").value;
  show($("insurance"), choice === "__other__");
  $("insurer-hint").textContent = INSURER_HINTS[choice]
    ?? (/medicare$|medicaid/i.test(choice) ? "This hospital's file has no rates for this coverage, so you will see the middle of all insurers' rates."
        : "You will see this insurer's negotiated rates with the hospital.");
}

function setInsurance(text) {
  const match = [...$("insurer").options].find((o) => o.value.toLowerCase() === text.toLowerCase());
  $("insurer").value = match ? match.value : "__other__";
  $("insurance").value = match ? "" : text;
  syncInsurer();
}

$("insurer").addEventListener("change", () => { syncInsurer(); if ($("insurer").value === "__other__") $("insurance").focus(); });

// ---- Page setup -----------------------------------------------------------

async function loadMeta() {
  try {
    const meta = await (await fetch("/api/meta")).json();
    priceFile = { hospital: meta.hospital, updated: meta.last_updated };
    $("source").textContent = `Prices: ${meta.hospital}, file updated ${meta.last_updated} · Model: ${meta.model}`;
    $("complaint").maxLength = meta.max_input_chars;
    $("count").textContent = `0 / ${meta.max_input_chars}`;
    $("insurer-list").replaceChildren(...meta.payers.map((name) =>
      Object.assign(document.createElement("option"), { value: name, textContent: INSURER_LABELS[name] || name })));
    $("examples").replaceChildren(...meta.examples.map((ex) => {
      const b = Object.assign(document.createElement("button"), { type: "button", className: "chip", textContent: ex.label });
      b.addEventListener("click", () => {
        $("complaint").value = ex.complaint;
        setInsurance(ex.insurance);
        $("complaint").dispatchEvent(new Event("input"));
        $("complaint").focus();
      });
      return b;
    }));
    // One statement about saving, never both: the page says what this copy of the app actually does.
    if (meta.saves_text) {
      $("save-notice").textContent = "What you type here is saved so the tool can be improved. Do not enter a name or anything else that identifies a real person.";
      show($("save-notice"));
      $("privacy-note").textContent = "Takes about 20 seconds. What you type is saved.";
    } else {
      $("privacy-note").textContent = "Takes about 20 seconds. Your text is not saved.";
    }
    if (!meta.api_key_found) {
      showAlert("error", "No API key found", "Put PORTKEY_API_KEY in a .env file in this folder or the folder above it, then restart the app.");
    }
  } catch {
    showAlert("error", "Cannot reach the app", "The server is not responding. Check that it is still running.");
  }
}

$("complaint").addEventListener("input", () => {
  $("count").textContent = `${$("complaint").value.length} / ${$("complaint").maxLength}`;
});

// ---- Alerts ---------------------------------------------------------------

function showAlert(kind, title, message, items) {
  const el = $(kind);
  const h = Object.assign(document.createElement("h2"), { textContent: title });
  const p = Object.assign(document.createElement("p"), { textContent: message });
  el.replaceChildren(h, p);
  if (items && items.length) {
    const ul = document.createElement("ul");
    fillList(ul, items);
    el.append(ul);
  }
  show(el);
}

// ---- Emergencies: the warning and the reassurance come first, the estimate follows ----
function showEmergency(message, flags) {
  showAlert("emergency", "This may be an emergency", message, flags);
  $("emergency").append(Object.assign(document.createElement("a"), { className: "call-911", href: "tel:911", textContent: "Call 911" }));
  show($("care-first"));
}

// ---- Agent timeline -------------------------------------------------------

function resetTimeline() {
  $("timeline").replaceChildren(...AGENTS.map(([id, title, blurb]) => {
    const li = document.createElement("li");
    li.id = `step-${id}`;
    li.className = "step-waiting";
    li.innerHTML = `<span class="dot" aria-hidden="true"></span>
      <div><div class="step-title">${esc(title)}</div><div class="step-blurb">${esc(blurb)}</div>
      <div class="step-detail"></div><div class="step-meta"></div><div class="step-tools"></div></div>`;
    return li;
  }));
}

function updateStep(ev) {
  const li = $(`step-${ev.agent}`);
  if (!li) return;
  if (ev.status === "start") {
    li.className = "step-working";
    li.querySelector(".step-meta").textContent = "Working…";
    return;
  }
  li.className = "step-done";
  li.querySelector(".dot").textContent = "✓";
  li.querySelector(".step-detail").textContent = ev.detail || "";
  const u = ev.usage || {};
  li.querySelector(".step-meta").textContent = `${u.seconds} seconds`;
  const tools = ev.tools || [];
  if (tools.length) {
    const rows = tools.map((t) => {
      const args = Object.keys(t.args || {}).length ? JSON.stringify(t.args) : "";
      const rejected = String(t.result).startsWith("REJECTED");
      return `<code class="${rejected ? "rejected" : ""}"><b>${esc(t.tool)}</b>(${esc(args)})\n→ ${esc(t.result)}</code>`;
    }).join("");
    li.querySelector(".step-tools").innerHTML =
      `<details class="tools"><summary>${tools.length} tool call${tools.length === 1 ? "" : "s"}</summary>${rows}</details>`;
  }
}

// A run that ends early must not leave a step spinning.
function stopWorkingSteps(label) {
  document.querySelectorAll("#timeline li.step-working").forEach((li) => {
    li.className = "step-failed";
    li.querySelector(".dot").textContent = "!";
    li.querySelector(".step-meta").textContent = label;
  });
}

// ---- Result ---------------------------------------------------------------

function renderScenarios(est) {
  $("scenarios").replaceChildren(...est.scenarios.map((s) => {
    const div = document.createElement("div");
    div.className = `scenario ${s.key}`;
    const share = s.patient_share;
    const rows = [];
    if (share && est.basis.kind !== "self_pay") {
      if (share.copay) rows.push(["Copay", money(share.copay)]);
      if (share.deductible) rows.push(["Toward your deductible", money(share.deductible)]);
      if (share.coinsurance) rows.push(["Coinsurance", money(share.coinsurance)]);
      if (share.capped_by_oop_max) rows.push(["Capped at out-of-pocket max", "yes"]);
      rows.push(["Insurer's rate for the visit", money(s.allowed_total)]);
    }
    rows.push(["Hospital list price", `<span class="strike">${money(s.list_total)}</span>`]);
    if (est.basis.kind !== "self_pay") rows.push(["Cash price (no insurance)", money(s.cash_total)]);
    div.innerHTML = `
      <div class="s-label">${esc(s.label)}</div>
      <p class="s-amount">${money(share ? share.amount : s.allowed_total)}</p>
      <div class="s-what">${share ? "you might pay" : "the most you might pay"}</div>
      <dl>${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join("")}</dl>
      <p class="s-includes">${esc(s.visit_level_name)}. Includes ${esc(s.includes)}.</p>`;
    return div;
  }));
}

// The itemized list under the three figures: what adds up to the most-likely figure, and what could be added.
// Every amount comes from the estimate the pricing code produced; nothing here is model text.
function renderReceipt(est) {
  const by = Object.fromEntries(est.scenarios.map((s) => [s.key, s]));
  const low = by.low, typ = by.typical, high = by.high;
  const visit = (code) => est.lines.find((l) => l.likelihood === "visit" && l.code === code);
  const label = (l) => esc(l.name) + (l.quantity > 1 ? ` × ${l.quantity}` : "");
  const cents = (n) => "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });  // to the cent, so the lines add up exactly
  const row = (name, value, cls = "") => `<tr${cls ? ` class="${cls}"` : ""}><td>${name}</td><td class="num">${value}</td></tr>`;
  const insured = est.basis.kind !== "self_pay";
  const shareRow = (s) => (s.patient_share && insured
    ? row("What you would pay of that, under your plan" + (s.patient_share.capped_by_oop_max ? " (your out-of-pocket max)" : ""), cents(s.patient_share.amount), "share") : "");

  const where = est.basis.kind === "payer" ? `${est.basis.payer}'s rates` : est.basis.kind === "self_pay" ? "The hospital's discounted cash prices" : "The middle of all insurers' rates";
  $("receipt-source").textContent = `${where}, from ${priceFile.hospital}'s published price file${priceFile.updated ? ` (updated ${priceFile.updated})` : ""}.`;

  const typVisit = visit(typ.visit_level);
  const expected = est.lines.filter((l) => l.likelihood === "expected");
  let html = `<h3>Most likely visit</h3><table class="receipt"><tbody>
    ${row(esc(typVisit.name), cents(typVisit.rate))}
    ${expected.map((l) => row(label(l), cents(l.rate * l.quantity))).join("")}
    ${row("Most likely total", cents(typ.allowed_total), "total")}${shareRow(typ)}</tbody></table>`;

  const extras = [];
  if (high.visit_level !== typ.visit_level) {
    const highVisit = visit(high.visit_level);
    extras.push(row(`A more complex visit: ${esc(highVisit.name)}`, "+ " + cents(highVisit.rate - typVisit.rate)));
  }
  est.lines.filter((l) => l.likelihood === "possible").forEach((l) => extras.push(row(label(l), "+ " + cents(l.rate * l.quantity))));
  if (extras.length) {
    html += `<h3>Might be added</h3><p class="hint">Ordered for some patients. All of them together is the higher end.</p>
      <table class="receipt extras"><tbody>${extras.join("")}${row("Higher end total", cents(high.allowed_total), "total")}${shareRow(high)}</tbody></table>`;
  }
  if (low.visit_level !== typ.visit_level) {
    html += `<p class="hint receipt-low">Lower end: the same items with a simpler visit, ${esc(visit(low.visit_level).name)}: ${cents(low.allowed_total)}.</p>`;
  }
  $("receipt").innerHTML = html;
}

function renderLines(est) {
  const rateHead = est.basis.kind === "self_pay" ? "Cash price" : est.basis.kind === "payer" ? `${est.basis.payer} rate` : "Median insurer rate";
  const rows = est.lines.map((l) => `
    <tr>
      <td>${esc(l.name)}<div class="code">${esc(l.code)} · ${esc(l.hospital_description)}</div></td>
      <td><span class="tag tag-${esc(l.likelihood)}">${l.likelihood === "visit" ? "visit level" : esc(l.likelihood)}</span></td>
      <td class="num">${l.quantity}</td>
      <td class="num"><span class="strike">${money(l.list_price * l.quantity)}</span></td>
      <td class="num">${money(l.rate * l.quantity)}</td>
      <td class="num">${money(l.rate_low * l.quantity)} – ${money(l.rate_high * l.quantity)}</td>
    </tr>`).join("");
  $("lines").innerHTML = `<thead><tr><th>Service</th><th>Likelihood</th><th class="num">Qty</th><th class="num">List price</th>
    <th class="num">${esc(rateHead)}</th><th class="num">Range across insurers</th></tr></thead><tbody>${rows}</tbody>`;
}

function renderAdmission(est, summary) {
  const has = est.admission.length > 0 || est.observation.length > 0;
  show($("admission-panel"), has);
  if (!has) return;
  $("if-admitted").textContent = summary.if_admitted || "";
  const shareCol = est.admission.some((a) => a.patient_share);
  $("admission-table").innerHTML = est.admission.length ? `<thead><tr><th>If admitted for</th><th class="num">List price</th>
    <th class="num">Insurer's rate for the stay</th>${shareCol ? '<th class="num">You might pay</th>' : ""}<th class="num">Range across insurers</th></tr></thead>
    <tbody>${est.admission.map((a) => `<tr>
      <td>${esc(a.name)}<div class="code">DRG ${esc(a.code)} · one case rate for the whole stay</div></td>
      <td class="num"><span class="strike">${money(a.list_price)}</span></td>
      <td class="num">${money(a.rate)}</td>
      ${shareCol ? `<td class="num">${a.patient_share ? money(a.patient_share.amount) + (a.patient_share.capped_by_oop_max ? " (your max)" : "") : "–"}</td>` : ""}
      <td class="num">${money(a.rate_low)} – ${money(a.rate_high)}</td></tr>`).join("")}</tbody>` : "";
  $("observation").innerHTML = est.observation.length
    ? `<h3>If kept under observation instead (billed as outpatient, on top of the ED visit)</h3><ul>${
        est.observation.map((o) => `<li>${esc(o.name)}: ${money(o.rate)} <span class="code">(list price ${money(o.list_price)})</span></li>`).join("")}</ul>`
    : "";
}

function renderResult(r) {
  const est = r.estimate, s = r.summary;
  $("basis").textContent = `Priced on ${est.basis.label}`;
  $("headline").textContent = s.headline;
  $("headline-note").textContent = r.headline_note || "";
  renderScenarios(est);
  $("physician").textContent = est.physician_fee_note;
  $("summary").textContent = s.summary;
  fillList($("drivers"), s.cost_drivers);
  fillList($("questions-staff"), s.questions_for_staff);
  fillList($("questions-doctor"), s.questions_for_doctor);
  fillList($("rights"), s.rights);
  renderAdmission(est, s);
  renderReceipt(est);
  renderLines(est);
  $("basis-explanation").textContent = r.pricing_notes.basis_explanation;
  fillList($("caveats"), r.pricing_notes.caveats);
  fillList($("assumptions"), r.plan.assumptions.length ? r.plan.assumptions : ["None stated."]);
  $("run-note").textContent = "You asked this exact question before, so this answer came from memory.";
  show($("run-note"), Boolean(r.cached));
  // The steps the agents took move into a closed "How the AI worked" section.
  document.querySelectorAll("#answer details.more").forEach((d) => { d.open = false; });
  $("work-body").replaceChildren($("timeline"));
  show($("work"), !r.cached);
  show($("timeline-panel"), false);
  if (r.emergency && $("emergency").hidden) showEmergency(r.emergency_message, r.red_flags);
  show($("answer"));
  $("results").scrollIntoView({ block: "start" });
}

// ---- Submit ---------------------------------------------------------------

function numberOrNull(id) {
  const v = $(id).value.trim();
  return v === "" ? null : Number(v);
}

function handle(ev) {
  if (ev.type === "step") updateStep(ev);
  else if (ev.type === "emergency") showEmergency(ev.message, ev.red_flags);
  else if (ev.type === "refused") { showAlert("refused", "I can't estimate that", ev.message); show($("timeline-panel"), ev.stage === "triage"); }
  else if (ev.type === "need_more") { showAlert("refused", "Tell us a little more", `${ev.message} Add a sentence to the box above and try again.`); show($("timeline-panel"), false); }
  else if (ev.type === "error") { stopWorkingSteps("Stopped here"); showAlert("error", "Something went wrong", ev.message); }
  else if (ev.type === "result") renderResult(ev);
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const complaint = $("complaint").value.trim();
  for (const id of ["emergency", "error", "refused", "answer", "care-first"]) show($(id), false);
  show($("empty"), false);
  if (!complaint) {
    showAlert("refused", "Tell us what's going on", "Describe the symptoms or injury in a few words.");
    $("complaint").focus();
    return;
  }
  $("timeline-panel").append($("timeline"));  // back from the "How the AI worked" section
  resetTimeline();
  show($("timeline-panel"));
  // The form sits above the results, so bring the results into view.
  const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  $("results").scrollIntoView({ behavior: calm ? "auto" : "smooth", block: "start" });
  const button = $("submit");
  button.disabled = true;
  button.textContent = "Working on your estimate…";
  $("results").setAttribute("aria-busy", "true");
  try {
    const res = await fetch("/api/estimate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        complaint, insurance: insuranceText(), copay: numberOrNull("copay"),
        deductible_remaining: numberOrNull("deductible"), coinsurance_pct: numberOrNull("coinsurance"),
        oop_max_remaining: numberOrNull("oop"),
      }),
    });
    if (!res.ok || !res.body) {
      const detail = res.status === 422 ? "Check the numbers in your plan details and try again." : "The server returned an error. Please try again.";
      showAlert("error", "Something went wrong", detail);
      show($("timeline-panel"), false);
      return;
    }
    const reader = res.body.getReader(), decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) if (line.trim()) handle(JSON.parse(line));
    }
    if (buffer.trim()) handle(JSON.parse(buffer));
  } catch {
    showAlert("error", "Connection lost", "The estimate was interrupted. Check that the app is still running and try again.");
  } finally {
    stopWorkingSteps("Stopped here");
    button.disabled = false;
    button.textContent = "Estimate my cost";
    $("results").setAttribute("aria-busy", "false");
  }
});

loadMeta();
