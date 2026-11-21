export type EmploymentForm = "umowa_o_prace" | "zlecenie" | "jdg" | "b2b";
export type FamilyPath = "birth" | "adoption" | "foster";

export type ParentProfile = {
  employment_form: EmploymentForm;
  company_insured_above_20: boolean;
  birth_date: string;
  number_of_children: number;
  preterm?: boolean;
  za_zyciem_certificate?: boolean;
  part_time?: boolean;
  b2b_arrears?: boolean;
  request_days_after_birth?: number | null;
  transfer_first_14_weeks_to_other_parent?: boolean;
  family_path?: FamilyPath;
  insured?: boolean;
  insurance_days?: number | null;
  stillbirth?: boolean;
  child_age_years?: number | null;
  school_deferred?: boolean;
  employer_bankruptcy?: boolean;
  unlawful_dismissal?: boolean;
  job_ended_before_birth?: boolean;
  apparent_contract?: boolean;
  benefit_base_pln?: number | null;
  combine_work_fraction?: number;
  parental_together?: boolean;
  rehab_after_sickness?: boolean;
  mother_hospitalized?: boolean;
  mother_incapacity?: boolean;
};

export type LeaveItem = {
  leave_type: string;
  title: string;
  weeks: number | null;
  days: number | null;
  rate_percent: number;
  transferable: boolean;
  mother_only: boolean;
  graph_node_id: string;
  plain_language: string;
  amount_pln: number | null;
  calendar_weeks: number | null;
};

export type DocumentItem = {
  code: string;
  title: string;
  active: boolean;
  replaced_by: string | null;
  plain_language: string;
  graph_node_id: string;
};

export type RiskItem = {
  code: string;
  title: string;
  severity: string;
  plain_language: string;
  graph_node_id: string;
};

export type PregnancyItem = {
  code: string;
  title: string;
  entitled: boolean;
  rate_percent: number | null;
  max_days: number | null;
  amount_pln: number | null;
  plain_language: string;
};

export type FilingItem = {
  where: string;
  what: string;
  deadline: string;
  plain_language: string;
};

export type CalculationResult = {
  legal_as_of: string;
  waiting_period_days: number;
  payer: "pracodawca" | "ZUS";
  combined_rate_applied: boolean;
  leaves: LeaveItem[];
  documents: DocumentItem[];
  risks: RiskItem[];
  blocked: boolean;
  block_reason: string | null;
  explanation_node_ids: string[];
  poka_yoke: string[];
  pregnancy: PregnancyItem[];
  filing: FilingItem[];
  monthly_base_pln: number | null;
  family_path: string;
};

export type ChatButton = { id: string; label: string };

export type ChatCitation = {
  node_id: string;
  title: string;
  plain_language: string;
  legal_basis: string;
};

export type ChatResponse = {
  session_id: string;
  mode: "step" | "question" | "result";
  question: string | null;
  helper: string | null;
  buttons: ChatButton[];
  answer: string | null;
  citations: ChatCitation[];
  profile: Record<string, unknown> | null;
  calculation: CalculationResult | null;
  complete: boolean;
};

export type GraphNode = {
  id: string;
  type: string;
  title: string;
  plain_language: string;
  legal_basis: string;
};

export type GraphEdge = {
  source: string;
  target: string;
  relation: string;
  plain_language: string;
};

export type ExplainResponse = {
  question: string;
  node_id: string;
  target_id: string | null;
  narrative: string[];
  path: string[];
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type ProfileId = "guest" | "anna" | "piotr" | "kasia" | "custom";

export type A11yState = {
  language: "plain" | "legal";
  hardSituation: boolean;
  highContrast: boolean;
  fontScale: 100 | 125 | 150;
};

export type Charity = {
  id: string;
  name: string;
  situations: string[];
  help: string;
  url: string;
};

export type SampleCase = {
  id: string;
  title: string;
  document: string;
  outcome: string;
  benefit_base_pln?: number | null;
  kind: string;
};

export function pln(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toLocaleString("pl-PL", { style: "currency", currency: "PLN" });
}
