export const RUN_STAGES = ["planner", "designer", "validator", "solver", "reviewer", "repair"] as const;
export type RunStage = typeof RUN_STAGES[number];
export type ProgressStatus = "idle" | "connecting" | "running" | "ready" | "needs_more_info" | "failed";
export type ProgressState = {
  status: ProgressStatus;
  stage?: RunStage;
  completed: RunStage[];
  message?: string;
  gameId?: string;
};

export type ProgressAction =
  | { type: "connect" }
  | { type: "event"; event: string; data?: Record<string, unknown> }
  | { type: "failed"; message: string }
  | { type: "needs_more_info"; message: string }
  | { type: "reset" };

export const initialProgress: ProgressState = { status: "idle", completed: [] };

export function normalizeRunEvent(value: string) {
  return value.toLowerCase().replace(/^v\d+[.:]/, "").replace(/[.:]v\d+$/, "");
}

export function progressReducer(state: ProgressState, action: ProgressAction): ProgressState {
  if (action.type === "reset") return initialProgress;
  if (action.type === "connect") return { ...state, status: state.status === "running" ? "running" : "connecting" };
  if (action.type === "failed") return { ...state, status: "failed", message: action.message };
  if (action.type === "needs_more_info") return { ...state, status: "needs_more_info", message: action.message };
  const event = normalizeRunEvent(action.event);
  if (event === "game.ready") return { ...state, status: "ready", gameId: stringValue(action.data?.game_id) };
  if (event === "planner.needs_more_info") return { ...state, status: "needs_more_info", message: stringValue(action.data?.message) ?? "The planner needs another detail." };
  if (event === "run.failed") return { ...state, status: "failed", message: stringValue(action.data?.message) ?? stringValue(action.data?.error) ?? "Game generation failed." };
  const stage = RUN_STAGES.find(item => event === item || event.startsWith(`${item}.`));
  if (!stage) return state;
  const completed = event.endsWith(".completed") || event.endsWith(".ready")
    ? Array.from(new Set([...state.completed, stage]))
    : state.completed;
  return { ...state, status: "running", stage, completed, message: stringValue(action.data?.message) };
}

export function parseProgressEvent(event: MessageEvent<string>, fallbackType = "message"): ProgressAction {
  let data: Record<string, unknown> = {};
  try { data = JSON.parse(event.data) as Record<string, unknown>; } catch { data = { message: event.data }; }
  const type = stringValue(data.type) ?? stringValue(data.event) ?? fallbackType;
  return { type: "event", event: type, data };
}

function stringValue(value: unknown) { return typeof value === "string" && value ? value : undefined; }
