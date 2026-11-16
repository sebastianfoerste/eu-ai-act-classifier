// The application-date timeline (D3): which dates the report gives, what starts on
// each, and which items rest on a contested or conditional reading. It only arranges
// what the report already carries. No date is computed, parsed or compared with the
// current day here: dates are the report's own ISO strings, and whether an item
// applies on the assessment date is the engine's `applies_on_assessment_date`.

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
    // A note on the date means the dating rests on a contested reading (Art. 113)
    // or on a condition such as an Art. 111 transitional rule.
    contested: Boolean(item.application_date_note),
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
