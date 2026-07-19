import { describe, expect, it } from "vitest";
import { initialProgress, normalizeRunEvent, parseProgressEvent, progressReducer } from "./progress";

describe("generation progress", () => {
  it("normalizes versioned event names", () => {
    expect(normalizeRunEvent("v1.planner.started")).toBe("planner.started");
    expect(normalizeRunEvent("solver.completed:v2")).toBe("solver.completed");
  });

  it("tracks stages and terminal readiness", () => {
    let state = progressReducer(initialProgress, { type: "event", event: "v1.planner.started" });
    expect(state).toMatchObject({ status: "running", stage: "planner" });
    state = progressReducer(state, { type: "event", event: "designer.completed.v1" });
    expect(state.completed).toContain("designer");
    state = progressReducer(state, { type: "event", event: "game.ready", data: { game_id: "game-1" } });
    expect(state).toMatchObject({ status: "ready", gameId: "game-1" });
  });

  it("parses typed and failed server events", () => {
    const action = parseProgressEvent(new MessageEvent("message", { data: JSON.stringify({ type: "run.failed", error: "No solution" }) }));
    const state = progressReducer(initialProgress, action);
    expect(state).toMatchObject({ status: "failed", message: "No solution" });
  });
});
