// The application-date timeline (D3): which dates the report gives, what starts on
// each, and which items carry a note on their date. It only arranges what the report
// already carries. No date is computed, parsed or compared with the current day here:
// dates are the report's own ISO strings, and whether an item applies on the
// assessment date is the engine's `applies_on_assessment_date`.

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

// One column per date: the binding timeline's milestones and the obligation-graph
// items dated that day. Items without a date go to `open`. ISO strings sort in date
// order as text, so ordering them needs no date arithmetic; a value that is not an
// ISO date is kept, after the ISO dates, in the order the report gives it.
export function timelineModel(report) {
  const columns = new Map();
  const column = date => {
    if (!columns.has(date)) columns.set(date, { date, milestones: [], items: [] });
    return columns.get(date);
  };
  for (const entry of report.timeline ?? []) {
    column(entry.applies_from).milestones.push({
      provision: entry.provision,
      note: entry.note,
      sourceStatus: entry.source_status,
    });
  }
  const open = [];
  for (const item of report.obligation_graph ?? []) {
    const view = graphItem(item);
    if (item.application_date == null) open.push(view);
    else column(item.application_date).items.push(view);
  }
  const dates = [...columns.values()];
  const iso = dates.filter(c => ISO_DATE.test(c.date)).sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  const other = dates.filter(c => !ISO_DATE.test(c.date));
  return { columns: [...iso, ...other], open };
}

function graphItem(item) {
  return {
    id: item.obligation_id,
    article: item.article,
    actor: item.actor,
    // The engine's note on this item's date. It can record a contested reading of
    // Art. 113, an Art. 111 transitional condition, a scope question that bears on
    // the item (Art. 2(2) for a Section B product, Art. 4 for a prohibited system) or
    // an explanation of the date. The timeline only says that a note exists; the
    // obligation graph section shows its text.
    hasDateNote: Boolean(item.application_date_note),
    note: item.application_date_note ?? null,
    reviewStatus: item.review_status,
    appliesOnAssessmentDate: item.applies_on_assessment_date ?? null,
  };
}

// The words that go with `applies_on_assessment_date`, or null where the report
// gives no assessment-date answer.
export function assessmentLabel(value) {
  if (value === true) return "applies on the assessment date";
  if (value === false) return "not yet applicable on the assessment date";
  return null;
}

// Every date string the model shows, for checks that nothing was invented.
export function shownDates(model) {
  return model.columns.map(c => c.date);
}

// The view: an ordered list, one entry per date, built with the given document so the
// tests can render it without a browser.
export function renderTimeline(doc, report, roleLabels = {}) {
  const model = timelineModel(report);
  if (!model.columns.length && !model.open.length) return null;
  const el = (tag, className, text) => {
    const element = doc.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const region = el("div", "timeline");
  region.setAttribute("role", "region");
  region.setAttribute("aria-label", "Application dates in date order");
  region.tabIndex = 0;
  const list = el("ol", "timeline-list");
  const columns = [...model.columns.map(c => [c.date, c.milestones, c.items]), ...(model.open.length ? [[null, [], model.open]] : [])];
  for (const [date, milestones, items] of columns) {
    const column = el("li", date ? "timeline-date" : "timeline-date is-open");
    column.append(el("p", "timeline-when", date ?? "Date open"));
    if (!date) column.append(el("p", "timeline-hint", "Turns on a fact the profile does not give; see each item's note in the obligation graph."));
    for (const milestone of milestones) column.append(el("p", "timeline-milestone", milestone.provision));
    if (items.length) {
      const entries = el("ul", "timeline-items");
      entries.setAttribute("aria-label", `Obligation graph items ${date ? `dated ${date}` : "without a date"}`);
      for (const item of items) {
        const entry = el("li", item.hasDateNote ? "timeline-item has-note" : "timeline-item");
        entry.append(el("span", "timeline-article", item.article), el("span", "timeline-actor", roleLabels[item.actor] ?? item.actor));
        if (item.hasDateNote) entry.append(el("span", "timeline-note", "see the date note"));
        const assessment = assessmentLabel(item.appliesOnAssessmentDate);
        if (assessment) entry.append(el("span", "timeline-status", assessment));
        entries.append(entry);
      }
      column.append(entries);
    }
    list.append(column);
  }
  region.append(list);
  return region;
}
