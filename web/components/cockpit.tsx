"use client";

import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileText,
  Plus,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { baseProfile, emptyDerogation, inventory } from "../lib/samples";
import type {
  ArtifactPreview,
  ArtifactResponse,
  AISystemInventory,
  ClassificationReport,
  InventoryItem,
  NullableBoolean,
  RegulatorySource,
  SchemaPayload,
  SystemProfile,
} from "../lib/types";

const fallbackSchema: SchemaPayload = {
  roles: ["provider", "deployer", "importer", "distributor", "authorized_representative"],
  annex_iii_areas: ["III.2", "III.4.a", "III.5.b", "III.5.c"],
  prohibited_practices: [],
  excluded_use_flags: [],
  artifacts: [
    "art-6-4-assessment",
    "fria",
    "annex-iv-checklist",
    "post-market-monitoring-plan",
    "serious-incident-register",
    "gpai-model-documentation",
    "training-content-summary",
  ],
  review_posture: "draft_only_human_review_required",
};

export function Cockpit() {
  const [schema, setSchema] = useState<SchemaPayload>(fallbackSchema);
  const [sources, setSources] = useState<RegulatorySource[]>([]);
  const [systemInventory, setSystemInventory] = useState<AISystemInventory | null>(null);
  const [profile, setProfile] = useState<SystemProfile>(() => cloneProfile(inventory[0].profile));
  const [selectedId, setSelectedId] = useState(inventory[0].id);
  const [includeAdvisory, setIncludeAdvisory] = useState(true);
  const [report, setReport] = useState<ClassificationReport | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactResponse | null>(null);
  const [activeArtifact, setActiveArtifact] = useState("fria");
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [reviewNotes, setReviewNotes] = useState<string[]>([]);

  useEffect(() => {
    void loadMetadata();
    void runClassification(inventory[0].profile, includeAdvisory);
    // The initial run intentionally uses the first inventory profile.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeArtifactPreview = useMemo(() => {
    if (!artifacts?.artifacts.length) {
      return null;
    }
    return (
      artifacts.artifacts.find((artifact) => artifact.name === activeArtifact) ??
      artifacts.artifacts[0]
    );
  }, [activeArtifact, artifacts]);

  async function loadMetadata() {
    try {
      const [schemaResult, sourceResult] = await Promise.all([
        fetchJson<SchemaPayload>("/api/schema"),
        fetchJson<RegulatorySource[]>("/api/sources"),
      ]);
      setSchema(schemaResult);
      setSources(sourceResult);
      const inventoryResult = await fetchJson<AISystemInventory>("/api/inventory");
      setSystemInventory(inventoryResult);
    } catch (metadataError) {
      setError(String(metadataError));
    }
  }

  async function runClassification(nextProfile = profile, advisory = includeAdvisory) {
    setStatus("Classifying");
    setError("");
    const payload = { profile: cleanProfile(nextProfile), include_advisory: advisory };
    try {
      const [reportResult, artifactResult] = await Promise.all([
        postJson<ClassificationReport>("/api/classify", payload),
        postJson<ArtifactResponse>("/api/artifacts", { ...payload, artifact: "all" }),
      ]);
      setReport(reportResult);
      setArtifacts(artifactResult);
      if (!artifactResult.artifacts.some((artifact) => artifact.name === activeArtifact)) {
        setActiveArtifact(artifactResult.artifacts[0]?.name ?? "fria");
      }
      setStatus("Reviewed by engine");
    } catch (classificationError) {
      setError(String(classificationError));
      setStatus("Needs attention");
    }
  }

  function selectInventoryItem(item: InventoryItem) {
    const cloned = cloneProfile(item.profile);
    setSelectedId(item.id);
    setProfile(cloned);
    setReviewNotes([]);
    void runClassification(cloned);
  }

  function updateProfile<K extends keyof SystemProfile>(key: K, value: SystemProfile[K]) {
    setProfile((current) => ({ ...current, [key]: value }));
  }

  function updateDerogation(key: keyof SystemProfile["derogation"], value: boolean) {
    setProfile((current) => ({
      ...current,
      derogation: { ...current.derogation, [key]: value },
    }));
  }

  function toggleArray(key: "roles" | "excluded_use_flags" | "prohibited_practices", value: string) {
    setProfile((current) => {
      const existing = new Set(current[key]);
      if (existing.has(value)) {
        existing.delete(value);
      } else {
        existing.add(value);
      }
      const nextValues = Array.from(existing);
      return { ...current, [key]: nextValues.length ? nextValues : key === "roles" ? ["provider"] : [] };
    });
  }

  function addReviewNote() {
    const trimmed = reviewNote.trim();
    if (!trimmed) {
      return;
    }
    setReviewNotes((current) => [trimmed, ...current]);
    setReviewNote("");
  }

  function loadBlank() {
    const blank = cloneProfile({ ...baseProfile, name: "New AI system", derogation: { ...emptyDerogation } });
    setSelectedId("new");
    setProfile(blank);
    setReport(null);
    setArtifacts(null);
    setReviewNotes([]);
  }

  function downloadArtifact(artifact: ArtifactPreview | null) {
    if (!artifact) {
      return;
    }
    const blob = new Blob([artifact.content], { type: "text/markdown;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = artifact.filename;
    anchor.click();
    URL.revokeObjectURL(href);
  }

  const sourceRows = report?.source_manifest.length ? report.source_manifest : sources;
  const isClassifying = status === "Classifying";

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <h1>EU AI Act Classifier</h1>
          <p>{status}</p>
        </div>
        <div className="toolbar" aria-label="Cockpit actions">
          <StatusPill label={report ? riskLabel(report.risk_tier) : "No result"} tone={riskTone(report?.risk_tier)} />
          <button
            className="iconButton"
            type="button"
            title="Run classification"
            aria-label="Run classification"
            aria-busy={isClassifying}
            disabled={isClassifying}
            onClick={() => void runClassification()}
          >
            <RefreshCw size={18} aria-hidden />
          </button>
          <button className="iconButton" type="button" title="New intake" aria-label="Start new intake" onClick={loadBlank}>
            <Plus size={18} aria-hidden />
          </button>
        </div>
      </header>

      {error ? (
        <div className="errorBanner" role="alert">
          <strong>Classification bridge needs attention.</strong>
          <span>{error}</span>
          <button className="secondaryButton" type="button" onClick={() => void loadMetadata()}>
            Retry metadata
          </button>
        </div>
      ) : null}

      <div className="cockpitGrid">
        <section className="panel inventoryPanel" aria-labelledby="inventory-heading">
          <div className="panelHeader">
            <div>
              <h2 id="inventory-heading">Inventory</h2>
              <p>{inventory.length} sample systems</p>
            </div>
            <ShieldCheck size={18} aria-hidden />
          </div>
          <div className="inventoryList">
            {inventory.map((item) => (
              <button
                className={`inventoryItem ${selectedId === item.id ? "selected" : ""}`}
                key={item.id}
                type="button"
                onClick={() => selectInventoryItem(item)}
              >
                <span>{item.name}</span>
                <small>{item.owner}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="panel intakePanel" aria-labelledby="intake-heading">
          <div className="panelHeader">
            <div>
              <h2 id="intake-heading">Guided Intake</h2>
              <p>{profile.name || "Unnamed system"}</p>
            </div>
            <button
              className="primaryButton"
              type="button"
              disabled={isClassifying}
              aria-busy={isClassifying}
              onClick={() => void runClassification()}
            >
              <ClipboardCheck size={16} aria-hidden />
              {isClassifying ? "Classifying" : "Classify"}
            </button>
          </div>

          <div className="formGrid">
            <TextField label="System name" value={profile.name} onChange={(value) => updateProfile("name", value)} />
            <TextField label="Sector" value={profile.sector} onChange={(value) => updateProfile("sector", value)} />
            <TextField
              label="Intended purpose"
              value={profile.purpose}
              onChange={(value) => updateProfile("purpose", value)}
            />
            <TextField
              label="Purpose source"
              value={profile.intended_purpose_source}
              onChange={(value) => updateProfile("intended_purpose_source", value)}
            />
          </div>

          <label className="field fieldWide">
            <span>Description</span>
            <textarea
              value={profile.description}
              onChange={(event) => updateProfile("description", event.target.value)}
              rows={3}
            />
          </label>

          <div className="sectionGrid">
            <div>
              <h3>Scope</h3>
              <TriStateControl label="AI system" value={profile.is_ai_system} onChange={(value) => updateProfile("is_ai_system", value)} />
              <TriStateControl label="EU nexus" value={profile.eu_nexus} onChange={(value) => updateProfile("eu_nexus", value)} />
              <TriStateControl
                label="Significant change"
                value={profile.significant_change_after_application_date}
                onChange={(value) => updateProfile("significant_change_after_application_date", value)}
              />
              <Toggle
                label="Public-authority use"
                checked={profile.public_authority_use}
                onChange={(checked) => updateProfile("public_authority_use", checked)}
              />
              <MultiCheck
                label="Excluded-use flags"
                options={schema.excluded_use_flags}
                selected={profile.excluded_use_flags}
                onToggle={(value) => toggleArray("excluded_use_flags", value)}
              />
            </div>

            <div>
              <h3>Actors</h3>
              <MultiCheck
                label="Roles"
                options={schema.roles}
                selected={profile.roles}
                onToggle={(value) => toggleArray("roles", value)}
              />
              <TriStateControl
                label="Public-law deployer"
                value={profile.deployer_public_law_body}
                onChange={(value) => updateProfile("deployer_public_law_body", value)}
              />
              <TriStateControl
                label="Private public-service deployer"
                value={profile.deployer_private_public_service}
                onChange={(value) => updateProfile("deployer_private_public_service", value)}
              />
              <Toggle
                label="Non-EU provider"
                checked={profile.provider_established_outside_eu}
                onChange={(checked) => updateProfile("provider_established_outside_eu", checked)}
              />
              <TriStateControl
                label="Authorised representative"
                value={profile.has_authorised_representative}
                onChange={(value) => updateProfile("has_authorised_representative", value)}
              />
            </div>

            <div>
              <h3>High Risk</h3>
              <label className="field">
                <span>Annex III area</span>
                <select
                  value={profile.annex_iii_area ?? ""}
                  onChange={(event) => updateProfile("annex_iii_area", event.target.value || null)}
                >
                  <option value="">None</option>
                  {schema.annex_iii_areas.map((area) => (
                    <option key={area} value={area}>
                      {formatLabel(area)}
                    </option>
                  ))}
                </select>
              </label>
              <Toggle
                label="Annex I safety component"
                checked={profile.annex_i_safety_component}
                onChange={(checked) => updateProfile("annex_i_safety_component", checked)}
              />
              <Toggle
                label="Third-party assessment"
                checked={profile.annex_i_third_party_assessment}
                onChange={(checked) => updateProfile("annex_i_third_party_assessment", checked)}
              />
              <Toggle
                label="Substantial modification"
                checked={profile.substantially_modifies_system}
                onChange={(checked) => updateProfile("substantially_modifies_system", checked)}
              />
              <Toggle
                label="Own-name placement"
                checked={profile.puts_name_or_trademark_on_system}
                onChange={(checked) => updateProfile("puts_name_or_trademark_on_system", checked)}
              />
            </div>

            <div>
              <h3>GPAI And Transparency</h3>
              <Toggle
                label="GPAI model"
                checked={profile.is_gpai_model}
                onChange={(checked) => updateProfile("is_gpai_model", checked)}
              />
              <NumberField
                label="Training FLOP"
                value={profile.training_flops}
                onChange={(value) => updateProfile("training_flops", value)}
              />
              <Toggle
                label="Systemic designation"
                checked={profile.gpai_systemic_risk_designated}
                onChange={(checked) => updateProfile("gpai_systemic_risk_designated", checked)}
              />
              <Toggle
                label="Natural-person interaction"
                checked={profile.interacts_with_natural_persons}
                onChange={(checked) => updateProfile("interacts_with_natural_persons", checked)}
              />
              <Toggle
                label="Deepfake generation"
                checked={profile.generates_deepfakes}
                onChange={(checked) => updateProfile("generates_deepfakes", checked)}
              />
            </div>
          </div>

          <div className="sectionGrid compact">
            <div>
              <h3>Article 6(3)</h3>
              {(Object.keys(profile.derogation) as Array<keyof SystemProfile["derogation"]>).map((key) => (
                <Toggle
                  key={key}
                  label={formatLabel(key)}
                  checked={profile.derogation[key]}
                  onChange={(checked) => updateDerogation(key, checked)}
                />
              ))}
            </div>
            <div>
              <h3>Prohibited Practices</h3>
              <MultiCheck
                label="Art. 5 flags"
                options={schema.prohibited_practices}
                selected={profile.prohibited_practices}
                onToggle={(value) => toggleArray("prohibited_practices", value)}
              />
            </div>
          </div>
        </section>

        <aside className="panel reviewPanel" aria-labelledby="review-heading">
          <div className="panelHeader">
            <div>
              <h2 id="review-heading">Review</h2>
              <p>{report?.disposition ?? "No report"}</p>
            </div>
            {report?.disposition === "requires_review" ? (
              <AlertTriangle size={18} aria-hidden />
            ) : (
              <CheckCircle2 size={18} aria-hidden />
            )}
          </div>

          <RiskMap report={report} />

          <div className="reviewBlock">
            <div className="blockHeader">
              <h3>Open Questions</h3>
              <span>{report?.open_questions.length ?? 0}</span>
            </div>
            <ul className="questionList">
              {report?.open_questions.length ? (
                report.open_questions.map((question) => <li key={question}>{question}</li>)
              ) : (
                <li>No open questions recorded.</li>
              )}
            </ul>
          </div>

          <div className="reviewBlock">
            <div className="blockHeader">
              <h3>Reviewer Notes</h3>
              <span>{reviewNotes.length}</span>
            </div>
            <textarea
              value={reviewNote}
              onChange={(event) => setReviewNote(event.target.value)}
              rows={3}
            />
            <button className="secondaryButton" type="button" onClick={addReviewNote}>
              <Plus size={15} aria-hidden />
              Add note
            </button>
            <ul className="notesList">
              {reviewNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </div>

          <label className="toggleLine">
            <input
              type="checkbox"
              checked={includeAdvisory}
              onChange={(event) => setIncludeAdvisory(event.target.checked)}
            />
            <span>Advisory overlay</span>
          </label>
        </aside>
      </div>

      {systemInventory ? <SystemInventoryPanel inventory={systemInventory} /> : null}

      <div className="lowerGrid">
        <section className="panel trackerPanel" aria-labelledby="tracker-heading">
          <div className="panelHeader">
            <div>
              <h2 id="tracker-heading">Obligation Tracker</h2>
              <p>{report?.obligation_graph.length ?? 0} graph items</p>
            </div>
            <FileText size={18} aria-hidden />
          </div>
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Article</th>
                  <th>Actor</th>
                  <th>Evidence</th>
                  <th>Due</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {report?.obligation_graph.length ? (
                  report.obligation_graph.map((item) => (
                    <tr key={item.obligation_id}>
                      <td>{item.article}</td>
                      <td>{item.actor}</td>
                      <td>{item.evidence_artifact}</td>
                      <td>{item.application_date}</td>
                      <td>{formatLabel(item.review_status)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>No obligation graph available.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel provenancePanel" aria-labelledby="provenance-heading">
          <div className="panelHeader">
            <div>
              <h2 id="provenance-heading">Source Provenance</h2>
              <p>{sourceRows.length} registry entries</p>
            </div>
            <ShieldCheck size={18} aria-hidden />
          </div>
          <div className="sourceList">
            {sourceRows.map((source) => (
              <a href={source.url} key={source.source_id} rel="noreferrer" target="_blank">
                <strong>{source.citation_label}</strong>
                <span>{formatLabel(source.legal_status)}</span>
                <small>Retrieved {source.retrieved_on}</small>
              </a>
            ))}
          </div>
        </section>

        <section className="panel exportPanel" aria-labelledby="export-heading">
          <div className="panelHeader">
            <div>
              <h2 id="export-heading">Export Pack</h2>
              <p>{artifacts?.review_status ?? "draft_only_human_review_required"}</p>
            </div>
            <button
              className="iconButton"
              type="button"
              title="Download draft artifact"
              aria-label="Download selected draft artifact"
              disabled={!activeArtifactPreview}
              onClick={() => downloadArtifact(activeArtifactPreview)}
            >
              <Download size={18} aria-hidden />
            </button>
          </div>
          {isClassifying ? (
            <p className="emptyState" aria-live="polite">
              Preparing draft review artifacts from the current profile.
            </p>
          ) : artifacts ? (
            <>
              <label className="field">
                <span>Draft artifact</span>
                <select
                  value={activeArtifactPreview?.name ?? activeArtifact}
                  onChange={(event) => setActiveArtifact(event.target.value)}
                >
                  {artifacts.artifacts.map((artifact) => (
                    <option key={artifact.name} value={artifact.name}>
                      {formatLabel(artifact.name)}
                    </option>
                  ))}
                </select>
              </label>
              <p className="reviewNotice">
                Draft-only output. A qualified reviewer must verify facts, source status and legal route before reliance.
              </p>
              <pre>{activeArtifactPreview?.content ?? "No artifact preview available."}</pre>
            </>
          ) : (
            <p className="emptyState">
              Run a classification to preview draft artifacts. Nothing here is a final legal assessment.
            </p>
          )}
        </section>
      </div>
    </main>
  );
}

function SystemInventoryPanel({ inventory }: { inventory: AISystemInventory }) {
  return (
    <section className="panel inventoryTrackerPanel" aria-labelledby="system-inventory-heading">
      <div className="panelHeader">
        <div>
          <h2 id="system-inventory-heading">AI Systems Inventory</h2>
          <p>
            {inventory.systems.length} profiles, {inventory.sourceRefs.length} source refs, {inventory.evidenceArtifacts.length} draft artifacts
          </p>
        </div>
        <StatusPill label={formatLabel(inventory.reviewStatus)} tone={reviewTone(inventory.reviewStatus)} />
      </div>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>System</th>
              <th>Role</th>
              <th>Risk tier</th>
              <th>Disposition</th>
              <th>Sources</th>
              <th>Open facts</th>
              <th>Obligations</th>
              <th>Draft artifacts</th>
              <th>Review</th>
              <th>Next action</th>
            </tr>
          </thead>
          <tbody>
            {inventory.systems.map((system) => (
              <tr key={system.system_id}>
                <td>
                  <strong>{system.name}</strong>
                  <small>{system.system_id}</small>
                </td>
                <td>{formatLabel(system.role)}</td>
                <td>{riskLabel(system.risk_tier)}</td>
                <td>{formatLabel(system.disposition)}</td>
                <td>{formatLabel(system.source_manifest_status)}</td>
                <td>{system.open_facts.length ? system.open_facts.length : "none"}</td>
                <td>{system.obligations.length}</td>
                <td>{system.draft_artifacts.length}</td>
                <td>
                  <StatusPill label={formatLabel(system.review_status)} tone={reviewTone(system.review_status)} />
                </td>
                <td>{system.next_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="reviewNotice">
        {inventory.schema ?? inventory.schema_id}, {inventory.sourceMode}, generated {inventory.generatedAt}
      </p>
      <div className="reviewTableHeader">
        <div>
          <h3>System aOS Review Profile</h3>
          <p>{inventory.reviewTable.aosProfile.reviewNotice}</p>
        </div>
        <StatusPill
          label={
            inventory.reviewTable.aosProfile.externalActionAllowed
              ? "external allowed"
              : "external blocked"
          }
          tone={inventory.reviewTable.aosProfile.externalActionAllowed ? "success" : "danger"}
        />
      </div>
      <div className="riskMap">
        <div>
          <span>Schema</span>
          <strong>
            {inventory.reviewTable.aosProfile.schema ?? inventory.reviewTable.aosProfile.schema_id}
          </strong>
        </div>
        <div>
          <span>Skills</span>
          <strong>{inventory.reviewTable.aosProfile.skills.length}</strong>
        </div>
        <div>
          <span>Trusted citations</span>
          <strong>
            {inventory.reviewTable.aosProfile.trustedSources.verifiedCitations}/
            {inventory.reviewTable.aosProfile.trustedSources.totalCitations}
          </strong>
        </div>
        <div>
          <span>Word package</span>
          <strong>{formatLabel(String(inventory.reviewTable.aosProfile.wordExportPackage.status))}</strong>
        </div>
      </div>
      <div className="controlGrid">
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Layer</th>
                <th>Status</th>
                <th>Evidence</th>
                <th>Gate</th>
              </tr>
            </thead>
            <tbody>
              {inventory.reviewTable.aosProfile.aosLayers.map((layer) => (
                <tr key={layer.key}>
                  <td>{layer.label}</td>
                  <td>
                    <StatusPill label={formatLabel(layer.status)} tone={reviewTone(layer.status)} />
                  </td>
                  <td>{layer.evidence}</td>
                  <td>{layer.gate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Skill</th>
                <th>Objective</th>
                <th>Review gate</th>
              </tr>
            </thead>
            <tbody>
              {inventory.reviewTable.aosProfile.skills.map((skill) => (
                <tr key={skill.id}>
                  <td>{skill.label}</td>
                  <td>{skill.objective}</td>
                  <td>{skill.reviewGate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="reviewTableHeader">
        <div>
          <h3>System Review Table</h3>
          <p>
            {inventory.reviewTable.summary.rows} rows, {inventory.reviewTable.summary.review_required} requiring review, {inventory.reviewTable.summary.blocked} blocked
          </p>
        </div>
        <StatusPill
          label={formatLabel(inventory.reviewTable.summary.blocked ? "blocked" : inventory.reviewStatus)}
          tone={inventory.reviewTable.summary.blocked ? "danger" : reviewTone(inventory.reviewStatus)}
        />
      </div>
      <div className="riskMap">
        <div>
          <span>Cell tasks</span>
          <strong>{inventory.reviewTable.reviewTableScale.estimatedCellTasks}</strong>
        </div>
        <div>
          <span>Columns</span>
          <strong>{inventory.reviewTable.reviewTableScale.columnCount}</strong>
        </div>
        <div>
          <span>Vault docs</span>
          <strong>{inventory.reviewTable.reviewTableScale.maxVaultDocuments}</strong>
        </div>
        <div>
          <span>Reset</span>
          <strong>{inventory.reviewTable.reviewTableScale.rowCount} rows</strong>
        </div>
      </div>
      <p className="reviewNotice">
        {inventory.reviewTable.reviewTableScale.resetStrategy}{" "}
        {inventory.reviewTable.reviewTableScale.needleInHaystackStrategy}
      </p>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>System</th>
              <th>Factor</th>
              <th>Classifier value</th>
              <th>Sources</th>
              <th>Pinpoint</th>
              <th>Obligations</th>
              <th>Artifacts</th>
              <th>Cell</th>
              <th>Review</th>
              <th>Next action</th>
            </tr>
          </thead>
          <tbody>
            {inventory.reviewTable.rows.slice(0, 12).map((row) => (
              <tr key={row.row_id}>
                <td>
                  <strong>{row.system_name}</strong>
                  <small>{row.system_id}</small>
                </td>
                <td>{row.factor_label}</td>
                <td>{formatLabel(row.classifier_value)}</td>
                <td>{formatLabel(row.source_status)}</td>
                <td>
                  {row.pinpoint_citations.length ? (
                    <>
                      <strong>{row.pinpoint_citations[0].support_ref}</strong>
                      <small>
                        {row.pinpoint_citations[0].citation_label},{" "}
                        {formatLabel(row.pinpoint_citations[0].source_class)},{" "}
                        {formatLabel(row.pinpoint_citations[0].legal_status_class)},{" "}
                        {row.pinpoint_citations[0].verified ? "verified" : "review required"}
                      </small>
                    </>
                  ) : (
                    "none"
                  )}
                </td>
                <td>{row.obligation_refs.length}</td>
                <td>{row.draft_artifacts.length}</td>
                <td>
                  <StatusPill label={formatLabel(row.cell_status)} tone={reviewTone(row.cell_status)} />
                </td>
                <td>
                  <StatusPill label={formatLabel(row.review_status)} tone={reviewTone(row.review_status)} />
                  <small>{row.reviewer_notes.length ? `${row.reviewer_notes.length} notes` : "no notes"}</small>
                </td>
                <td>{row.next_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="reviewTableHeader">
        <div>
          <h3>Review Control Profile</h3>
          <p>{inventory.reviewTable.controlProfile.routeSummary}</p>
        </div>
        <StatusPill
          label={inventory.reviewTable.controlProfile.externalActionAllowed ? "external allowed" : "external blocked"}
          tone={inventory.reviewTable.controlProfile.externalActionAllowed ? "success" : "danger"}
        />
      </div>
      <div className="controlGrid">
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Route</th>
                <th>Mode</th>
                <th>Status</th>
                <th>Gate</th>
              </tr>
            </thead>
            <tbody>
              {inventory.reviewTable.controlProfile.workflowRoutes.map((route) => (
                <tr key={route.key}>
                  <td>{route.label}</td>
                  <td>{formatLabel(route.route)}</td>
                  <td>
                    <StatusPill label={formatLabel(route.status)} tone={reviewTone(route.status)} />
                  </td>
                  <td>{route.gate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Connector</th>
                <th>Status</th>
                <th>Scope</th>
                <th>Gate</th>
              </tr>
            </thead>
            <tbody>
              {inventory.reviewTable.controlProfile.sourceConnectors.map((connector) => (
                <tr key={connector.key}>
                  <td>{connector.label}</td>
                  <td>
                    <StatusPill label={formatLabel(connector.status)} tone={reviewTone(connector.status)} />
                  </td>
                  <td>{connector.scope}</td>
                  <td>{connector.gate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="reviewNotice">{inventory.reviewTable.controlProfile.contextWindowStrategy}</p>
      <div className="promptBrief">
        <div>
          <small>{inventory.reviewTable.promptBrief.schema ?? inventory.reviewTable.promptBrief.schema_id}</small>
          <h3>Prompt Improvement Brief</h3>
          <p>{inventory.reviewTable.promptBrief.objective}</p>
        </div>
        <dl>
          <div>
            <dt>Actor</dt>
            <dd>{inventory.reviewTable.promptBrief.actor}</dd>
          </div>
          <div>
            <dt>Sources</dt>
            <dd>{inventory.reviewTable.promptBrief.sourceHierarchy.join(" · ")}</dd>
          </div>
          <div>
            <dt>Review gate</dt>
            <dd>{inventory.reviewTable.promptBrief.reviewGate}</dd>
          </div>
          <div>
            <dt>Guided inputs</dt>
            <dd>{inventory.reviewTable.promptBrief.guidedInputs.map((input) => input.label).join(" · ")}</dd>
          </div>
        </dl>
        <pre>{inventory.reviewTable.promptBrief.suggestedPrompt}</pre>
      </div>
      <p className="reviewNotice">{inventory.reviewTable.reviewNotice}</p>
    </section>
  );
}

function RiskMap({ report }: { report: ClassificationReport | null }) {
  const lanes = [
    { label: "Scope", value: report?.scope.status ?? "pending" },
    { label: "Risk", value: report ? riskLabel(report.risk_tier) : "pending" },
    { label: "GPAI", value: report?.is_gpai ? "yes" : "no" },
    { label: "Questions", value: String(report?.open_questions.length ?? 0) },
  ];
  return (
    <div className="riskMap">
      {lanes.map((lane) => (
        <div key={lane.label}>
          <span>{lane.label}</span>
          <strong>{formatLabel(lane.value)}</strong>
        </div>
      ))}
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        inputMode="numeric"
        type="number"
        value={value ?? ""}
        onChange={(event) => {
          onChange(event.target.value ? Number(event.target.value) : null);
        }}
      />
    </label>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="toggleLine">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function TriStateControl({
  label,
  value,
  onChange,
}: {
  label: string;
  value: NullableBoolean;
  onChange: (value: NullableBoolean) => void;
}) {
  const options: Array<{ label: string; value: NullableBoolean }> = [
    { label: "Yes", value: true },
    { label: "No", value: false },
    { label: "Review", value: null },
  ];
  return (
    <div className="triState">
      <span>{label}</span>
      <div>
        {options.map((option) => (
          <button
            className={value === option.value ? "active" : ""}
            key={option.label}
            type="button"
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function MultiCheck({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div className="multiCheck">
      <span>{label}</span>
      <div>
        {options.length ? (
          options.map((option) => (
            <label key={option}>
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={() => onToggle(option)}
              />
              <span>{formatLabel(option)}</span>
            </label>
          ))
        ) : (
          <small>No options loaded.</small>
        )}
      </div>
    </div>
  );
}

function StatusPill({ label, tone }: { label: string; tone: string }) {
  return <span className={`statusPill ${tone}`}>{label}</span>;
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  return readJsonResponse<T>(response);
}

async function postJson<T>(url: string, payload: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJsonResponse<T>(response);
}

async function readJsonResponse<T>(response: Response): Promise<T> {
  const data = (await response.json()) as T & { error?: string };
  if (!response.ok) {
    throw new Error(data.error ?? response.statusText);
  }
  return data;
}

function cleanProfile(profile: SystemProfile): SystemProfile {
  return {
    ...profile,
    roles: profile.roles.length ? profile.roles : ["provider"],
    annex_iii_area: profile.annex_iii_area || null,
    placing_on_market_date: normalizeOptional(profile.placing_on_market_date),
    putting_into_service_date: normalizeOptional(profile.putting_into_service_date),
    derogation: { ...profile.derogation },
  };
}

function normalizeOptional(value: string | null): string | null {
  if (!value || !value.trim()) {
    return null;
  }
  return value.trim();
}

function cloneProfile(profile: SystemProfile): SystemProfile {
  return JSON.parse(JSON.stringify(profile)) as SystemProfile;
}

function formatLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replaceAll(".", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function riskLabel(value: string) {
  const labels: Record<string, string> = {
    outside_scope: "Outside scope",
    prohibited: "Prohibited",
    high_risk: "High risk",
    limited_risk: "Limited risk",
    minimal_risk: "Minimal risk",
  };
  return labels[value] ?? value;
}

function riskTone(value?: string) {
  if (value === "prohibited") {
    return "danger";
  }
  if (value === "high_risk") {
    return "warning";
  }
  if (value === "outside_scope") {
    return "neutral";
  }
  if (value === "limited_risk") {
    return "info";
  }
  return "success";
}

function reviewTone(value?: string) {
  if (value === "blocked") {
    return "danger";
  }
  if (value === "review_required") {
    return "warning";
  }
  return "success";
}
