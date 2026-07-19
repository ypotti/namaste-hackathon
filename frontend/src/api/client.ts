import type { GameSpecV1 } from "../types/game";

const API_ROOT = "/api/v1";
export const CONVERSATION_PARAM_KEY = "conversation_id";

export class ApiError extends Error {
  constructor(message: string, readonly status: number) { super(message); this.name = "ApiError"; }
}

export type Conversation = {
  id: string;
  title: string | null;
  status: string;
  created_at: string;
};

type AssistantMessage = { id: string; content: string };
export type MessageResponse =
  | { status: "ready"; game_id: string; game: GameSpecV1; assistant_message?: AssistantMessage; run_id?: string }
  | { status: "needs_more_info"; assistant_message: AssistantMessage; run_id?: string }
  | { status: "processing"; run_id: string; assistant_message?: AssistantMessage };

export type RunStatus = "queued" | "processing" | "completed" | "failed" | "cancelled" | "needs_more_info";
export type GenerationRun = {
  id: string;
  status: RunStatus;
  stage?: string | null;
  game_id?: string | null;
  message?: string | null;
  error?: { code?: string | null; message?: string | null } | null;
};
export type GameRecord = { id: string; spec: GameSpecV1 };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null) as { detail?: string } | null;
    throw new ApiError(detail?.detail ?? `Request failed (${response.status})`, response.status);
  }
  return response.json() as Promise<T>;
}

export function getDemoGame(signal?: AbortSignal) {
  return request<GameSpecV1>("/games/demo", { signal });
}

export function createConversation() {
  return request<Conversation>("/conversations", { method: "POST", body: "{}" });
}

export function getConversation(conversationId: string) {
  return request<Conversation>(`/conversations/${encodeURIComponent(conversationId)}`);
}

export function submitMessage(conversationId: string, content: string) {
  return request<MessageResponse>(`/conversations/${encodeURIComponent(conversationId)}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function getRun(runId: string, signal?: AbortSignal) {
  return request<GenerationRun>(`/runs/${encodeURIComponent(runId)}`, { signal });
}

export function getGame(gameId: string, signal?: AbortSignal) {
  return request<GameRecord>(`/games/${encodeURIComponent(gameId)}`, { signal });
}

export function gameContentUrl(gameId?: string) {
  return gameId ? `${API_ROOT}/games/${encodeURIComponent(gameId)}/content` : `${API_ROOT}/games/demo/content`;
}

export function runEventsUrl(runId: string) {
  return `${API_ROOT}/runs/${encodeURIComponent(runId)}/events`;
}

function getUrlParam(name: string): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

function setUrlParam(name: string, value: string | null) {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (value) {
    url.searchParams.set(name, value);
  } else {
    url.searchParams.delete(name);
  }
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

export async function getOrCreateConversationId() {
  const stored = getUrlParam(CONVERSATION_PARAM_KEY);
  if (stored) {
    try {
      await getConversation(stored);
      return stored;
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404) throw error;
      setUrlParam(CONVERSATION_PARAM_KEY, null);
    }
  }
  const conversation = await createConversation();
  setUrlParam(CONVERSATION_PARAM_KEY, conversation.id);
  return conversation.id;
}

export function forgetConversation() {
  setUrlParam(CONVERSATION_PARAM_KEY, null);
}
