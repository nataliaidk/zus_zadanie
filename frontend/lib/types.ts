export type EmploymentForm = "umowa_o_prace" | "zlecenie" | "jdg" | "b2b";

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
