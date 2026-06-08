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

export type InventoryItem = {
  id: string;
  name: string;
  owner: string;
  profile: SystemProfile;
};
