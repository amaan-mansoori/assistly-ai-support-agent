export type User = { id: string; email: string | null; role: "customer" | "agent" | "admin" };
export type Conversation = { id: string; status: string; metadata: Record<string, unknown>; created_at: string; updated_at: string };
export type Message = { id: string; conversation_id: string; sender_type: string; content: string; created_at: string; metadata: Record<string, unknown> };
export type AgentRun = {
  id: string;
  conversation_id: string;
  request_id: string;
  decision: string;
  intent: string | null;
  intent_confidence: number | null;
  intent_reason: string | null;
  intent_source: string | null;
  evidence_status: string;
  evidence_reason: string | null;
  evidence: Array<{ source_id: string; retrieval_score: number; customer_message: string; support_response: string }>;
  grounding: { supported: boolean; score: number | null; reason: string } | null;
  escalation_reason: string | null;
  provider: string | null;
  model: string | null;
  latency_ms: number;
  processing_metadata: { stage_timings_ms?: Record<string, number>; [key: string]: unknown };
  error_category: string | null;
};
export type TicketAgentRun = AgentRun & { draft_reply: string | null };
export type ConversationDetail = Conversation & { messages: Message[] };
export type TicketDetail = Ticket & {
  agent_run: TicketAgentRun | null;
  conversation: Conversation;
  messages: Message[];
  resolution_metadata: Record<string, unknown> | null;
};
export type Submission = { status: string; customer_message: Message; assistant_message: Message | null; agent_run: AgentRun | null; ticket_id: string | null };
export type Ticket = { id: string; conversation_id: string; status: string; priority: string; reason: string; assigned_to: string | null; created_at: string };

function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!configured) {
    if (process.env.NODE_ENV === "production") {
      throw new Error("NEXT_PUBLIC_API_BASE_URL must be configured for production.");
    }
    return "http://localhost:8000";
  }
  let parsed: URL;
  try {
    parsed = new URL(configured);
  } catch {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute URL.");
  }
  const localHost = ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname);
  if (parsed.protocol !== "https:" && !(parsed.protocol === "http:" && localHost)) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must use HTTPS except for local development.");
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must not contain credentials, query, or fragment data.");
  }
  return configured.replace(/\/$/, "");
}

const baseUrl = getApiBaseUrl();

export function token(): string | null {
  return typeof window === "undefined" ? null : window.localStorage.getItem("support_token");
}

export function saveSession(accessToken: string, user: User): void {
  window.localStorage.setItem("support_token", accessToken);
  window.localStorage.setItem("support_user", JSON.stringify(user));
  window.dispatchEvent(new Event("support-session-change"));
}

export function currentUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const value = window.localStorage.getItem("support_user");
    return value ? JSON.parse(value) as User : null;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  window.localStorage.removeItem("support_token");
  window.localStorage.removeItem("support_user");
  window.dispatchEvent(new Event("support-session-change"));
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const accessToken = token();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${baseUrl}${path}`, { ...init, headers, cache: "no-store" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload?.error?.message ?? "The request could not be completed.";
    if (response.status === 401 && typeof window !== "undefined") clearSession();
    throw new Error(detail);
  }
  return payload as T;
}
