export type NullableBoolean = boolean | null;

export type Derogation = {
  narrow_procedural_task: boolean;
  improves_prior_human_activity: boolean;
  detects_patterns_without_replacing_human: boolean;
  preparatory_task: boolean;
  performs_profiling: boolean;
};

export type SystemProfile = {
  name: string;
  description: string;
  roles: string[];
  purpose: string;
  sector: string;
  is_ai_system: NullableBoolean;
  intended_purpose_source: string;
  eu_nexus: NullableBoolean;
  excluded_use_flags: string[];
  placing_on_market_date: string | null;
  putting_into_service_date: string | null;
  significant_change_after_application_date: NullableBoolean;
  public_authority_use: boolean;
  deployer_public_law_body: NullableBoolean;
  deployer_private_public_service: NullableBoolean;
  provider_established_outside_eu: boolean;
  has_authorised_representative: NullableBoolean;
  substantially_modifies_system: boolean;
  puts_name_or_trademark_on_system: boolean;
  is_gpai_model: boolean;
  training_flops: number | null;
  gpai_systemic_risk_designated: boolean;
  prohibited_practices: string[];
  annex_i_safety_component: boolean;
  annex_i_third_party_assessment: boolean;
  annex_iii_area: string | null;
  derogation: Derogation;
  interacts_with_natural_persons: boolean;
  generates_synthetic_content: boolean;
  deploys_emotion_or_biometric_categorisation: boolean;
  generates_deepfakes: boolean;
};

export type SchemaPayload = {
  roles: string[];
  annex_iii_areas: string[];
  prohibited_practices: string[];
  excluded_use_flags: string[];
  artifacts: string[];
  review_posture: string;
};

export type Finding = {
  rule_id: string;
  citation: string;
  citation_verified: boolean;
  title: string;
  detail: string;
  severity: string;
  tier: string | null;
};

export type Obligation = {
  article: string;
  citation_verified: boolean;
  title: string;
  applies_to: string;
  requirement: string;
};

export type ScopeAssessment = {
  status: string;
  is_ai_system: NullableBoolean;
  intended_purpose_source: string;
  eu_nexus: NullableBoolean;
  excluded_use_flags: string[];
  transitional_status: string;
  notes: string[];
};

export type ObligationGraphItem = {
  obligation_id: string;
  article: string;
  actor: string;
  trigger: string;
  requirement: string;
  evidence_artifact: string;
  source_status: string;
  source_url: string;
  application_date: string;
  review_status: string;
};

export type RegulatorySource = {
  source_id: string;
  title: string;
  legal_status: string;
  url: string;
  retrieved_on: string;
  citation_label: string;
  implementation_note: string;
};

export type AdvisoryNote = {
  note_id: string;
  title: string;
  detail: string;
  source_id: string;
  source_status: string;
  source_url: string;
  review_status: string;
};

export type TimelineItem = {
  provision: string;
  applies_from: string;
  note: string;
  source_status: string;
  source_id: string;
  source_url: string;
};

export type ClassificationReport = {
  system: string;
  regulation: string;
  risk_tier: string;
  disposition: string;
  scope: ScopeAssessment;
  roles: string[];
  is_gpai: boolean;
  gpai_systemic: boolean;
  findings: Finding[];
  obligations: Obligation[];
  documentation_required: Obligation[];
  transparency_obligations: Obligation[];
  obligation_graph: ObligationGraphItem[];
  timeline: TimelineItem[];
  source_manifest: RegulatorySource[];
  advisory_notes: AdvisoryNote[];
  open_questions: string[];
  unverified_citations: string[];
  disclaimer: string;
};

export type ArtifactPreview = {
  name: string;
  filename: string;
  content: string;
};

export type ArtifactResponse = {
  system: string;
  review_status: string;
  artifacts: ArtifactPreview[];
  source_manifest: RegulatorySource[];
};

export type ReviewDossierArtifact = ArtifactPreview & {
  draft_only: boolean;
};

export type ReviewDossier = {
  schema: "eu-ai-act.review-dossier.v1";
  system: string;
  risk_tier: string;
  disposition: string;
  scope_status: string;
  review_status: "draft_only_human_review_required";
  draft_notice: string;
  next_actions: string[];
  classification_report: ClassificationReport;
  obligation_graph: ObligationGraphItem[];
  open_questions: string[];
  source_manifest: RegulatorySource[];
  source_summary: Record<string, number>;
  artifacts: ReviewDossierArtifact[];
};

export type InventoryItem = {
  id: string;
  name: string;
  owner: string;
  profile: SystemProfile;
};

export type AISystemInventoryRow = {
  system_id: string;
  name: string;
  role: string;
  risk_tier: string;
  disposition: string;
  source_manifest_status: "complete" | "review_required" | "missing";
  open_facts: string[];
  obligations: string[];
  draft_artifacts: string[];
  review_status: "determined" | "review_required" | "blocked";
  next_action: string;
};

export type AISystemInventory = {
  schema?: "eu-ai-act-classifier.system-inventory.v1";
  schema_id?: "eu-ai-act-classifier.system-inventory.v1";
  sourceMode: "example_profiles" | "runtime_projection";
  generatedAt: string;
  subjectId: string;
  module: "eu-ai-act-classifier";
  sourceRefs: string[];
  evidenceArtifacts: string[];
  reviewStatus: "determined" | "review_required" | "blocked";
  blockers: string[];
  warnings: string[];
  exportAllowed: boolean;
  externalActionAllowed: boolean;
  nextAction: string;
  systems: AISystemInventoryRow[];
  reviewTable: AISystemReviewTable;
};

export type AISystemPinpointCitation = {
  source_id: string;
  source_class: "binding_law" | "official_guidance" | "provisional_context" | "advisory_source";
  citation_label: string;
  url: string;
  verified: boolean;
  legal_status_class: string;
  source_status: string;
  support_ref: string;
  quote?: string | null;
  offset_start?: number | null;
  offset_end?: number | null;
  derived_from: "classifier_finding" | "obligation_graph" | "source_manifest";
};

export type AISystemReviewTableRow = {
  row_id: string;
  system_id: string;
  system_name: string;
  factor_id: string;
  factor_label: string;
  classifier_value: string;
  source_status: "complete" | "review_required" | "missing";
  obligation_refs: string[];
  draft_artifacts: string[];
  pinpoint_citations: AISystemPinpointCitation[];
  reviewer_notes: string[];
  cell_status: "complete" | "review_required" | "blocked";
  review_status: "determined" | "review_required" | "blocked";
  next_action: string;
};

export type AISystemReviewLayer = {
  key:
    | "large_language_models"
    | "agentic_harness"
    | "data_integrations"
    | "context_knowledge"
    | "legal_capabilities"
    | "products_interfaces"
    | "security_governance";
  label: string;
  status: "implemented" | "metadata_only" | "blocked";
  evidence: string;
  gate: string;
};

export type AISystemReviewSkill = {
  id: string;
  label: string;
  objective: string;
  outputSchema: string[];
  reviewGate: string;
  externalActionAllowed: boolean;
};

export type AISystemReviewProfile = {
  schema?: "eu-ai-act-classifier.system-review-profile.v1";
  schema_id?: "eu-ai-act-classifier.system-review-profile.v1";
  reviewLayers: AISystemReviewLayer[];
  agentPlan: {
    plan: string;
    execute: string;
    review: string;
    deliver: string;
  };
  skills: AISystemReviewSkill[];
  tabularReview: Record<string, string | number | boolean>;
  trustedSources: Record<string, string | number | boolean>;
  editorDraft: Record<string, string | boolean>;
  wordExportPackage: Record<string, string | string[] | boolean>;
  portalRoom: Record<string, string | boolean>;
  monitors: Record<string, string | string[]>;
  lists: {
    status: string;
    items: {
      key: string;
      label: string;
      owner: string;
      signOffRequired: boolean;
    }[];
  };
  securityGovernance: Record<string, string | boolean>;
  vendorIntegration: "none";
  externalActionAllowed: boolean;
  reviewNotice: string;
};

export type AISystemReviewTable = {
  schema?: "eu-ai-act-classifier.system-review-table.v1";
  schema_id?: "eu-ai-act-classifier.system-review-table.v1";
  generatedAt: string;
  summary: {
    rows: number;
    blocked: number;
    review_required: number;
    determined: number;
  };
  rows: AISystemReviewTableRow[];
  controlProfile: {
    schema?: "eu-ai-act-classifier.review-control-profile.v1";
    schema_id?: "eu-ai-act-classifier.review-control-profile.v1";
    externalActionAllowed: boolean;
    routeSummary: string;
    contextWindowStrategy: string;
    workflowRoutes: {
      key: string;
      label: string;
      route: "deterministic_classifier" | "draft_artifact_builder" | "external_action";
      status: "determined" | "review_required" | "blocked";
      gate: string;
    }[];
    sourceConnectors: {
      key: string;
      label: string;
      status: "enabled" | "review_required" | "blocked";
      scope: string;
      gate: string;
    }[];
  };
  reviewTableScale: {
    schema?: "eu-ai-act-classifier.system-review-table-scale.v1";
    schema_id?: "eu-ai-act-classifier.system-review-table-scale.v1";
    rowCount: number;
    columnCount: number;
    estimatedCellTasks: number;
    maxVaultDocuments: number;
    resetStrategy: string;
    needleInHaystackStrategy: string;
  };
  promptBrief: {
    schema?: "eu-ai-act-classifier.system-prompt-brief.v1";
    schema_id?: "eu-ai-act-classifier.system-prompt-brief.v1";
    objective: string;
    actor: string;
    jurisdiction: string;
    sourceHierarchy: string[];
    requiredInputs: string[];
    guidedInputs: {
      key: string;
      label: string;
      prompt: string;
      required: boolean;
    }[];
    outputFormat: string[];
    reviewGate: string;
    failureConditions: string[];
    suggestedPrompt: string;
  };
  reviewProfile: AISystemReviewProfile;
  reviewNotice: string;
};
