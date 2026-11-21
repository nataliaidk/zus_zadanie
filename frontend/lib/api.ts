import type {
  CalculationResult,
  Charity,
  ChatResponse,
  ExplainResponse,
  GraphEdge,
  GraphNode,
  ParentProfile,
  SampleCase,
} from "./types";

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
    return JSON.stringify(body);
  } catch {
    return response.statusText;
  }
}

export async function calculate(profile: ParentProfile): Promise<CalculationResult> {
  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function chat(body: {
  session_id?: string;
  action: "start" | "answer" | "question";
  button_id?: string;
  message?: string;
}): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function explain(nodeId: string): Promise<ExplainResponse> {
  const response = await fetch(
    `/api/graph/explain?node_id=${encodeURIComponent(nodeId)}`,
  );
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function loadGraph(): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
  const response = await fetch("/api/graph");
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function loadParams(): Promise<Record<string, unknown>> {
  const response = await fetch("/api/admin/params");
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function saveParams(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await fetch("/api/admin/params", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function uploadPdf(file: File): Promise<Record<string, unknown>> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch("/api/pdf/calculate", {
    method: "POST",
    body: form,
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function loadCharities(): Promise<Charity[]> {
  const response = await fetch("/api/charities");
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function loadSamples(): Promise<SampleCase[]> {
  const response = await fetch("/api/samples");
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function calculateSample(id: string): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/samples/${encodeURIComponent(id)}/calculate`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function runSim(kind: string, profile?: ParentProfile | null): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/sim/${encodeURIComponent(kind)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: profile ? JSON.stringify(profile) : undefined,
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}
