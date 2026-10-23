import { droppedFields, profileToAnswers } from "./intake.mjs";
import { createWizard } from "./wizard.mjs";
import { DISPOSITIONS, MAX_BYTES, ROLE_LABELS, TIERS, annexCitation, describeDefault, formatProfile, groupByRole, matchesQuery, parseProfile, practiceCitation, reportIsCurrent } from "./model.mjs";

const $ = id => document.getElementById(id);
const input = $("input");
let worker, timer, ready = false, busy = false, samples;
let report = null, reportText = "", checked = null, pending = null, requestId = 0, modified = false;
// Guided intake state. The JSON textarea stays the one profile that is
// classified and exported; the guided mode writes its profile there on Classify.
let mode = "guided", wizard = null, intake = null, answersChanged = false;
// True once the user has answered or changed a guided question that has not
// yet been classified; guards replacing the answers and leaving the page.
let guidedEdited = false;

const SEVERITY_TONE = { blocker: "tone-red", high: "tone-amber", medium: "tone-blue", info: "tone-grey" };
const SEVERITY_LABEL = { blocker: "Blocker", high: "High", medium: "Medium", info: "Info" };
const REVIEW_TONE = { determined: "tone-green", review_required: "tone-amber", draft: "tone-grey" };
const REVIEW_LABEL = { determined: "Determined", review_required: "Review required", draft: "Draft" };
const SOURCE_LABEL = { binding_level_1: "Binding", provisional_political_agreement: "Provisional", nonbinding_guidance: "Nonbinding guidance" };
const SCOPE_LABEL = { in_scope: "In scope", outside_ai_act_scope: "Outside AI Act scope", scope_requires_review: "Scope requires review" };

function showError(id, message = "") {
  $(id).textContent = message;
  $(id).hidden = !message;
}

const current = () => ({ text: input.value, advisory: $("advisory").checked });

function profileSummary(text) {
  try {
    const profile = parseProfile(text);
    const roles = Array.isArray(profile.roles) ? profile.roles : ["provider"];
    const parts = [roles.map(role => ROLE_LABELS[role] ?? role).join(", ")];
    if (profile.annex_iii_area) parts.push(annexCitation(profile.annex_iii_area));
    if (Array.isArray(profile.prohibited_practices)) parts.push(...profile.prohibited_practices.map(practiceCitation));
    if (profile.is_gpai_model) parts.push("GPAI model");
    return parts.join(" · ");
  } catch { return "Profile structure needs attention"; }
}

function syncDraft() {
  const size = new TextEncoder().encode(input.value).length;
  $("size").textContent = `${(size / 1024).toFixed(1)} KB`;
  $("summary").textContent = profileSummary(input.value);
  const fresh = reportIsCurrent(report, checked, current()) && !(mode === "guided" && answersChanged);
  $("stale").hidden = !report || fresh;
  $("export-json").disabled = !fresh || busy;
  $("export-text").disabled = !fresh || busy;
  $("classify").disabled = !ready || busy;
  $("classify").firstChild.textContent = busy ? "Classifying… " : "Classify ";
  $("result-state").textContent = busy ? "Classifying" : report ? (fresh ? "Classification complete" : "Profile changed") : "Awaiting classification";
  document.querySelector(".results-panel").setAttribute("aria-busy", String(busy));
  wizard?.refresh();
}

function setMode(next) {
  mode = next;
  $("guided").hidden = mode !== "guided";
  $("json-mode").hidden = mode !== "json";
  $("run-area").hidden = mode !== "json";
  $("mode-guided").setAttribute("aria-pressed", String(mode === "guided"));
  $("mode-json").setAttribute("aria-pressed", String(mode === "json"));
  $("mode-badge").textContent = mode === "guided" ? "GUIDED" : "JSON";
  syncDraft();
}

// Opens a JSON profile in the guided intake. Fields the intake does not know
// are refused rather than dropped, so nothing in the profile is lost silently.
function reviewInWizard(text) {
  if (!wizard) return false;
  const profile = parseProfile(text);
  const known = new Set([...Object.keys(intake.defaults), "$schema"]);
  const derogation = profile.derogation ?? {};
  const unknown = [...Object.keys(profile).filter(key => !known.has(key)),
    ...Object.keys(derogation).filter(key => !(key in intake.defaults.derogation)).map(key => `derogation.${key}`)];
  if (unknown.length) throw new Error(`The guided questions do not cover ${unknown.join(", ")}. Fix the profile in the JSON editor.`);
  const { skipped, unsupported } = droppedFields(intake, profile);
  if (unsupported.length) throw new Error(`The guided questions cannot show the value of ${unsupported.join(", ")} in this profile. Use the JSON editor for it.`);
  if (skipped.length) throw new Error(`Earlier answers in this profile skip the questions for ${skipped.join(", ")}, so the guided mode would drop their values. Edit the profile in the JSON editor.`);
  wizard.review(profileToAnswers(intake, profile));
  guidedEdited = false;
  return true;
}

$("mode-guided").onclick = () => {
  if (mode === "guided") return;
  // Open the edited JSON in the questions, unless that would replace answers
  // the user has not classified and they decline.
  if (modified && (!guidedEdited || window.confirm("Replace your guided answers with the profile from the JSON editor?"))) {
    try { reviewInWizard(input.value); }
    catch (error) { showError("input-error", error.message); return; }
  }
  setMode("guided");
};
$("mode-json").onclick = () => setMode("json");

async function loadIntake() {
  try {
    const response = await fetch("intake.json");
    if (!response.ok) throw new Error();
    intake = await response.json();
    wizard = createWizard({
      root: $("guided"),
      definition: intake,
      canClassify: () => ready && !busy,
      onChange: () => { answersChanged = true; guidedEdited = true; syncDraft(); },
      onClassify: profile => {
        input.value = JSON.stringify(profile, null, 2);
        modified = true;
        answersChanged = false;
        guidedEdited = false;
        clearInputState();
        syncDraft();
        runClassification();
      },
      onEditJson: profile => {
        replaceDraft(JSON.stringify(profile, null, 2));
        setMode("json");
        input.focus();
      },
    });
    wizard.reset();
    answersChanged = false;
    guidedEdited = false;
    syncDraft();
  } catch {
    $("guided").replaceChildren(node("p", "error", "The guided questions could not load. Use the JSON editor instead."));
    setMode("json");
  }
}

function clearInputState() {
  showError("input-error");
  showError("run-error");
  input.removeAttribute("aria-invalid");
}

input.addEventListener("input", () => {
  modified = true;
  clearInputState();
  syncDraft();
});
$("advisory").addEventListener("change", syncDraft);

function replaceDraft(text) {
  if (input.value && modified && !window.confirm("Replace this edited profile? Save a copy first if you need to keep it.")) return;
  input.value = text;
  modified = false;
  clearInputState();
  showError("sample-error");
  syncDraft();
}

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function link(url, text) {
  // Source URLs come from the classifier's catalogue; only https links are rendered.
  if (!/^https:\/\//.test(url ?? "")) return node("span", "", text);
  const anchor = node("a", "", text);
  anchor.href = url;
  anchor.rel = "noopener";
  anchor.target = "_blank";
  return anchor;
}

function fillExamples() {
  const select = $("example");
  select.replaceChildren();
  for (const group of samples.groups) {
    const optgroup = node("optgroup");
    optgroup.label = group.label;
    for (const sample of group.samples) {
      const option = node("option", "", `${sample.label} · ${samples.profiles[sample.key].name}`);
      option.value = sample.key;
      optgroup.append(option);
    }
    select.append(optgroup);
  }
  select.value = samples.default;
}

async function loadSamples() {
  try {
    const response = await fetch("samples.json");
    if (!response.ok) throw new Error();
    samples = await response.json();
    for (const key of Object.keys(samples.profiles)) parseProfile(JSON.stringify(samples.profiles[key]));
    fillExamples();
    if (!input.value) replaceDraft(JSON.stringify(samples.profiles[samples.default], null, 2));
    $("load-example").disabled = false;
    showError("sample-error");
  } catch {
    samples = null;
    $("load-example").disabled = false;
    showError("sample-error", "Examples could not load. Press Load to retry, or import or paste a JSON profile.");
  }
}

async function loadFields() {
  const guide = $("field-guide");
  try {
    const response = await fetch("fields.json");
    if (!response.ok) throw new Error();
    const { groups } = await response.json();
    guide.replaceChildren(...groups.map(group => {
      const section = node("section", "field-group");
      section.append(node("h4", "", group.label));
      const list = node("dl");
      for (const field of group.fields) {
        const term = node("dt");
        term.append(node("code", "", field.name), node("span", "field-type", field.type));
        const detail = node("dd");
        if (field.hint) detail.append(node("p", "", field.hint));
        if (field.options) {
          const options = node("ul", "field-options");
          for (const option of field.options) {
            const item = node("li");
            item.append(node("code", "", option.value), document.createTextNode(` ${option.label}`));
            options.append(item);
          }
          detail.append(options);
        }
        if (field.keys) detail.append(node("p", "field-default", `Booleans: ${field.keys.join(", ")}`));
        if (field.name !== "name") detail.append(node("p", "field-default", `Default: ${describeDefault(field)}`));
        list.append(term, detail);
      }
      section.append(list);
      return section;
    }));
  } catch {
    guide.replaceChildren(node("p", "field-guide-intro", "The field guide could not load. The SystemProfile model in models.py lists every field."));
  }
}

$("load-example").onclick = async () => {
  if (!samples) await loadSamples();
  if (!samples) return;
  const text = JSON.stringify(samples.profiles[$("example").value], null, 2);
  if (mode === "guided" && wizard) {
    if ((guidedEdited || modified) && !window.confirm("Replace your answers with this example? Save the profile JSON first if you need to keep them.")) return;
    input.value = text;
    modified = false;
    clearInputState();
    reviewInWizard(text);
    return;
  }
  replaceDraft(text);
};
$("import").onclick = () => $("file").click();
$("file").onchange = async event => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  const before = input.value;
  try {
    if (file.size > MAX_BYTES) throw new Error("The file exceeds the 1 MB playground limit. Use the CLI for larger files.");
    // file.text() would silently swap invalid bytes (e.g. a Windows-1252 export) for U+FFFD.
    let text;
    try { text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer()); }
    catch { throw new Error("The file is not valid UTF-8. Save it as UTF-8 JSON and import it again."); }
    parseProfile(text);
    if (input.value !== before) throw new Error("The profile changed while the file was opening. Import the file again when you are ready.");
    if (mode === "guided" && wizard) {
      if ((guidedEdited || modified) && !window.confirm("Replace your answers with the imported profile? Save the profile JSON first if you need to keep them.")) return;
      input.value = text;
      modified = false;
      clearInputState();
      syncDraft();
      try { reviewInWizard(text); }
      catch (error) { setMode("json"); throw error; }
    } else replaceDraft(text);
  } catch (error) { showError(mode === "guided" ? "sample-error" : "input-error", error.message || "The file could not be read. Try a UTF-8 JSON file."); }
};

$("format").onclick = () => {
  try {
    const formatted = formatProfile(input.value);
    if (formatted !== input.value) {
      input.value = formatted;
      modified = true;
    }
    clearInputState();
    syncDraft();
  } catch (error) { showError("input-error", error.message); }
};

function runtimeFailed(message) {
  clearTimeout(timer);
  worker?.terminate();
  ready = false;
  busy = false;
  $("status").textContent = message;
  $("status-dot").className = "status-dot error";
  $("retry").hidden = false;
  syncDraft();
}

function startRuntime() {
  worker?.terminate();
  clearTimeout(timer);
  ready = false;
  busy = false;
  $("retry").hidden = true;
  $("status-dot").className = "status-dot";
  $("status").textContent = "Loading Python runtime…";
  syncDraft();
  try {
    const instance = new Worker(new URL("runtime.mjs", import.meta.url), { type: "module" });
    worker = instance;
    timer = setTimeout(() => runtimeFailed("Loading timed out. Check your connection and retry; your profile is still here."), 90000);
    instance.onerror = event => {
      event.preventDefault();
      if (worker === instance) runtimeFailed("The rule engine stopped. Retry to reload it; your profile is still here.");
    };
    instance.onmessage = ({ data }) => {
      if (worker !== instance) return;
      if (data.type === "progress") $("status").textContent = data.text;
      if (data.type === "ready") {
        clearTimeout(timer);
        ready = true;
        $("status").textContent = "Ready. Classification runs locally in your browser.";
        $("status-dot").className = "status-dot ready";
        syncDraft();
      }
      if (data.type === "error") {
        if (data.id === undefined) runtimeFailed(data.text);
        else if (data.id === requestId) {
          clearTimeout(timer);
          busy = false;
          showError("run-error", data.text);
          syncDraft();
        }
      }
      if (data.type === "result" && data.id === requestId) {
        clearTimeout(timer);
        busy = false;
        if (data.errors) {
          const lines = data.errors.map(error => `• ${error.loc}: ${error.msg}`);
          showError(mode === "guided" ? "run-error" : "input-error", ["The profile does not fit the classifier's fields. Fix these and classify again:", ...lines].join("\n"));
          input.setAttribute("aria-invalid", "true");
        } else {
          report = data.report;
          reportText = data.text;
          checked = pending;
          renderReport();
        }
        syncDraft();
      }
    };
    const wheelName = document.querySelector("script[data-wheel]").dataset.wheel;
    instance.postMessage({ type: "init", wheelUrl: new URL(wheelName, location.href).href });
  } catch { runtimeFailed("This browser could not start the rule engine. Enable web workers and retry, or use the CLI."); }
}

function runClassification() {
  if (!ready || busy) return;
  clearInputState();
  try { parseProfile(input.value); }
  catch (error) {
    showError("input-error", error.message);
    input.setAttribute("aria-invalid", "true");
    input.focus();
    return;
  }
  busy = true;
  pending = current();
  requestId += 1;
  syncDraft();
  timer = setTimeout(() => runtimeFailed("The classification timed out. Retry the engine and classify again."), 30000);
  worker.postMessage({ type: "classify", id: requestId, text: pending.text, advisory: pending.advisory });
}
$("classify").onclick = runClassification;
$("retry").onclick = startRuntime;
input.addEventListener("keydown", event => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) { event.preventDefault(); runClassification(); }
});

function renderReport() {
  $("empty").hidden = true;
  $("results").hidden = false;
  const tier = TIERS[report.risk_tier] ?? { label: report.risk_tier, basis: "", tone: "grey" };
  $("report-title").textContent = report.system;
  const meta = [report.roles.map(role => ROLE_LABELS[role] ?? role).join(", "), SCOPE_LABEL[report.scope.status] ?? report.scope.status];
  if (report.is_gpai) meta.push(report.gpai_systemic ? "GPAI model with systemic risk (Art. 51 AIA)" : "General-purpose AI model");
  $("report-meta").textContent = meta.join(" · ");
  $("tier-card").className = `tier-card tone-${tier.tone}`;
  $("tier-label").textContent = tier.label;
  $("tier-basis").textContent = tier.basis;
  const needsReview = report.disposition === "requires_review";
  $("disposition").className = `badge ${needsReview ? "tone-amber" : "tone-green"}`;
  $("disposition").textContent = DISPOSITIONS[report.disposition] ?? report.disposition;
  $("review-boundary").textContent = needsReview
    ? "This classification turns on facts the engine cannot settle. Lawyer review is required before it is relied upon."
    : "Determined from the facts as submitted. A lawyer still confirms the characterisation before anyone relies on it.";
  const obligationCount = report.obligations.length + report.documentation_required.length + report.transparency_obligations.length;
  const counts = { findings: report.findings.length, obligations: obligationCount, questions: report.open_questions.length, unverified: report.unverified_citations.length };
  for (const [key, value] of Object.entries(counts)) {
    $("count-" + key).textContent = value;
    $("count-" + key).classList.toggle("is-zero", value === 0);
  }
  renderSections();
  if (matchMedia("(max-width: 800px)").matches) $("results-heading").scrollIntoView({ behavior: "smooth", block: "start" });
}

function itemCard(badge, title, citation, lines = [], meta = "") {
  const card = node("div", "item");
  const head = node("div", "item-head");
  if (badge) head.append(badge);
  head.append(node("span", "finding-label", title));
  card.append(head);
  if (citation) card.append(citation instanceof Node ? citation : node("p", "citation", citation));
  for (const line of lines.filter(Boolean)) card.append(line instanceof Node ? line : node("p", "item-text", line));
  if (meta) card.append(node("p", "finding-meta", meta));
  return card;
}

const badge = (tone, text) => node("span", `badge ${tone}`, text);
const unverifiedNote = verified => verified === false ? node("p", "item-text unverified", "noch zu verifizieren · citation pending verification") : null;
const dateNote = note => note ? node("p", "item-text date-note", note) : null;

function sectionDefinitions() {
  const r = report;
  return [
    {
      title: "Findings", open: true,
      items: r.findings.map(f => ({
        search: [f.rule_id, f.citation, f.title, f.detail, f.severity],
        render: () => itemCard(badge(SEVERITY_TONE[f.severity] ?? "tone-grey", SEVERITY_LABEL[f.severity] ?? f.severity), f.title, f.citation, [f.detail, unverifiedNote(f.citation_verified)], f.rule_id),
      })),
    },
    {
      title: "Open questions for review", open: true,
      items: r.open_questions.map(q => ({ search: [q], render: () => itemCard(badge("tone-amber", "Confirm"), q) })),
    },
    ...groupByRole(r.obligations).map(group => ({
      title: `Obligations · ${group.label}`, open: true,
      items: group.items.map(o => ({
        search: [o.article, o.title, o.requirement, group.label],
        render: () => itemCard(null, o.title, o.article, [o.requirement, unverifiedNote(o.citation_verified)]),
      })),
    })),
    {
      title: "Documentation to maintain",
      items: r.documentation_required.map(o => ({
        search: [o.article, o.title, o.requirement],
        render: () => itemCard(null, o.title, o.article, [o.requirement, unverifiedNote(o.citation_verified)], ROLE_LABELS[o.applies_to] ?? o.applies_to),
      })),
    },
    {
      title: "Transparency obligations", open: true,
      items: r.transparency_obligations.map(o => ({
        search: [o.article, o.title, o.requirement],
        render: () => itemCard(null, o.title, o.article, [o.requirement, unverifiedNote(o.citation_verified)], ROLE_LABELS[o.applies_to] ?? o.applies_to),
      })),
    },
    {
      title: "Obligation graph · evidence and review",
      items: r.obligation_graph.map(g => ({
        search: [g.obligation_id, g.article, g.actor, g.trigger, g.requirement, g.evidence_artifact, g.review_status, g.application_date_note],
        render: () => itemCard(badge(REVIEW_TONE[g.review_status] ?? "tone-grey", REVIEW_LABEL[g.review_status] ?? g.review_status), g.requirement, g.article,
          [`Trigger: ${g.trigger}`, `Evidence: ${g.evidence_artifact}`, dateNote(g.application_date_note)],
          `${ROLE_LABELS[g.actor] ?? g.actor} · applies from ${g.application_date} · ${SOURCE_LABEL[g.source_status] ?? g.source_status} · ${g.obligation_id}`),
      })),
    },
    {
      title: "Application timeline",
      items: r.timeline.map(t => ({
        search: [t.applies_from, t.provision, t.note, t.source_status],
        render: () => itemCard(badge(t.source_status === "binding_level_1" ? "tone-green" : "tone-amber", SOURCE_LABEL[t.source_status] ?? t.source_status), t.provision, t.applies_from, [t.note]),
      })),
    },
    {
      title: "Advisory notes · nonbinding guidance", open: true,
      items: r.advisory_notes.map(a => ({
        search: [a.title, a.detail, a.source_id],
        render: () => itemCard(badge("tone-blue", SOURCE_LABEL[a.source_status] ?? a.source_status), a.title, null, [a.detail, link(a.source_url, "Source ↗")], REVIEW_LABEL[a.review_status] ?? a.review_status),
      })),
    },
    {
      title: "Scope and intake",
      items: [{
        search: [r.scope.status, r.scope.transitional_status, r.scope.intended_purpose_source, ...r.scope.notes, ...r.scope.excluded_use_flags],
        render: () => itemCard(badge(r.scope.status === "in_scope" ? "tone-green" : "tone-amber", SCOPE_LABEL[r.scope.status] ?? r.scope.status), "Scope assessment", null, [
          `AI system: ${r.scope.is_ai_system} · EU nexus: ${r.scope.eu_nexus}`,
          r.scope.intended_purpose_source && `Intended-purpose source: ${r.scope.intended_purpose_source}`,
          r.scope.excluded_use_flags.length && `Excluded-use flags: ${r.scope.excluded_use_flags.join(", ")}`,
          `Transitional status: ${r.scope.transitional_status}`,
          ...r.scope.notes,
        ]),
      }],
    },
    {
      title: "Source manifest",
      items: r.source_manifest.map(s => ({
        search: [s.citation_label, s.title, s.legal_status, s.implementation_note],
        render: () => itemCard(badge(s.legal_status === "binding_level_1" ? "tone-green" : "tone-blue", SOURCE_LABEL[s.legal_status] ?? s.legal_status), s.title, link(s.url, `${s.citation_label} ↗`), [s.implementation_note], `Retrieved ${s.retrieved_on}`),
      })),
    },
    {
      title: "Citations pending verification", open: true,
      items: r.unverified_citations.map(c => ({ search: [c], render: () => itemCard(badge("tone-red", "noch zu verifizieren"), c) })),
    },
  ];
}

function renderSections() {
  if (!report) return;
  const query = $("search").value;
  const container = $("sections");
  container.replaceChildren();
  let total = 0, visible = 0;
  for (const section of sectionDefinitions()) {
    total += section.items.length;
    const items = section.items.filter(item => matchesQuery(item.search, query));
    visible += items.length;
    if (!items.length) continue;
    const details = node("details", "finding section");
    details.open = Boolean(section.open) || Boolean(query.trim());
    const summary = node("summary");
    const heading = node("div");
    heading.append(node("span", "finding-label", section.title));
    summary.append(heading, node("span", "count", String(items.length)));
    const body = node("div", "finding-body");
    body.append(...items.map(item => item.render()));
    details.append(summary, body);
    container.append(details);
  }
  $("visible-count").textContent = query.trim() ? `${visible} of ${total} items match` : `${total} items · findings and open questions first`;
  if (!visible) container.append(node("p", "no-findings", "Nothing matches this search. Try an article number such as Art. 9."));
}
$("search").oninput = renderSections;

function download(text, filename, type) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = node("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const exportName = () => (report?.system || "system").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "system";
$("download-draft").onclick = () => download(input.value, "system-profile.json", "application/json");
$("export-json").onclick = () => {
  if (!busy && reportIsCurrent(report, checked, current())) download(JSON.stringify(report, null, 2), `ai-act-classification-${exportName()}.json`, "application/json");
};
$("export-text").onclick = () => {
  if (!busy && reportIsCurrent(report, checked, current())) download(reportText, `ai-act-classification-${exportName()}.txt`, "text/plain;charset=utf-8");
};
window.addEventListener("beforeunload", event => {
  if (modified || guidedEdited) { event.preventDefault(); event.returnValue = ""; }
});

setMode("guided");
loadSamples();
loadFields();
loadIntake();
startRuntime();
