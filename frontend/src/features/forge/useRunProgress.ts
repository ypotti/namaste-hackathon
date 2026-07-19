import { useEffect, useReducer, useRef } from "react";
import { getGame, getRun, runEventsUrl } from "../../api/client";
import type { GameSpecV1 } from "../../types/game";
import { initialProgress, parseProgressEvent, progressReducer, RUN_STAGES } from "./progress";

type Options = { onReady: (game: GameSpecV1) => void; onFailed: (message: string) => void; onNeedsMoreInfo: (message: string) => void };

export function useRunProgress(runId: string | undefined, { onReady, onFailed, onNeedsMoreInfo }: Options) {
  const [state, dispatch] = useReducer(progressReducer, initialProgress);
  const callbacks = useRef({ onReady, onFailed, onNeedsMoreInfo });
  callbacks.current = { onReady, onFailed, onNeedsMoreInfo };
  useEffect(() => {
    if (!runId) { dispatch({ type: "reset" }); return; }
    let active = true;
    const controller = new AbortController();
    const source = new EventSource(runEventsUrl(runId));
    dispatch({ type: "connect" });
    const finish = async (gameId: string) => {
      try { const record = await getGame(gameId, controller.signal); if (active) callbacks.current.onReady(record.spec); }
      catch (error) { if (active) dispatch({ type: "failed", message: error instanceof Error ? error.message : "The finished game could not be loaded." }); }
    };
    const consume = (event: Event, eventType?: string) => {
      const action = parseProgressEvent(event as MessageEvent<string>, eventType);
      dispatch(action);
      if (action.type === "event") {
        const data = action.data;
        if (action.event.includes("game.ready") && typeof data?.game_id === "string") { source.close(); void finish(data.game_id); }
        if (action.event.includes("run.failed")) source.close();
      }
    };
    source.onmessage = consume;
    for (const stage of RUN_STAGES) for (const suffix of ["started", "completed"]) source.addEventListener(`${stage}.${suffix}`, event => consume(event, `${stage}.${suffix}`));
    source.addEventListener("game.ready", event => consume(event, "game.ready"));
    source.addEventListener("run.failed", event => consume(event, "run.failed"));
    source.addEventListener("planner.needs_more_info", event => { consume(event, "planner.needs_more_info"); source.close(); });
    source.onerror = () => { void getRun(runId, controller.signal).then(run => {
      if (!active) return;
      if (run.status === "completed" && run.game_id) { source.close(); void finish(run.game_id); }
      else if (run.status === "needs_more_info") { source.close(); dispatch({ type: "failed", message: run.message ?? "The planner needs another detail." }); }
      else if (run.status === "failed") { source.close(); dispatch({ type: "failed", message: run.error?.message ?? "Game generation failed." }); }
    }).catch(() => { /* EventSource reconnects automatically. */ }); };
    return () => { active = false; controller.abort(); source.close(); };
  }, [runId]);
  useEffect(() => {
    if (state.status === "failed") callbacks.current.onFailed(state.message ?? "Game generation failed.");
    if (state.status === "needs_more_info") callbacks.current.onNeedsMoreInfo(state.message ?? "What other detail should I use?");
  }, [state.status, state.message]);
  return state;
}
