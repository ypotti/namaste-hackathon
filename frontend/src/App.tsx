import { useEffect, useState } from "react";
import { getDemoGame, getOrCreateConversationId, submitMessage } from "./api/client";
import { RUN_STAGES } from "./features/forge/progress";
import { useRunProgress } from "./features/forge/useRunProgress";
import { projectileFixture } from "./features/games/fixture";
import { GameRenderer } from "./features/games/GameRenderer";
import type { GameSpecV1 } from "./types/game";

const Bolt = () => <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m13 2-8 12h7l-1 8 8-12h-7l1-8Z" /></svg>;

export function App() {
  const [spec, setSpec] = useState<GameSpecV1>(projectileFixture);
  const [source, setSource] = useState<"api" | "fixture">("fixture");
  const [concept, setConcept] = useState("Projectile Motion");
  const [conversationId, setConversationId] = useState<string>();
  const [submitting, setSubmitting] = useState(false);
  const [forgeError, setForgeError] = useState<string>();
  const [runId, setRunId] = useState<string>();
  const [muted, setMuted] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getDemoGame(controller.signal)
      .then(game => loadGame(game, "api"))
      .catch(error => { if (!(error instanceof DOMException && error.name === "AbortError")) setSource("fixture"); });
    getOrCreateConversationId().then(setConversationId).catch(() => setForgeError("The forge is offline. You can still play the demo game."));
    return () => controller.abort();
  }, []);

  function loadGame(game: GameSpecV1, nextSource: "api" | "fixture" = "api") {
    setSpec(game);
    setSource(nextSource);
  }

  const progress = useRunProgress(runId, {
    onReady: game => { loadGame(game); setRunId(undefined); setSubmitting(false); },
    onFailed: message => { setForgeError(message); setRunId(undefined); setSubmitting(false); },
  });

  async function forge() {
    const content = concept.trim();
    if (!content || submitting) return;
    setSubmitting(true); setForgeError(undefined); setRunId(undefined);
    try {
      const id = conversationId ?? await getOrCreateConversationId();
      setConversationId(id);
      const response = await submitMessage(id, content);
      if (response.status === "ready") { loadGame(response.game); setSubmitting(false); }
      else if (response.status === "needs_more_info") { setForgeError(response.assistant_message.content); setSubmitting(false); }
      else setRunId(response.run_id);
    } catch (error) {
      setForgeError(error instanceof Error ? error.message : "The forge could not create this game. The demo remains available.");
      setSubmitting(false);
    }
  }

  return <main>
    <header className="topbar"><a className="brand" href="#main"><span className="brand-mark"><Bolt /></span><span>PHYSICS<span>FORGE</span></span></a><nav aria-label="Primary"><button className="active">Forge</button><button>My concepts</button></nav><div className="head-actions"><button className="icon" aria-label={muted ? "Turn sound on" : "Mute sound"} onClick={() => setMuted(!muted)}>{muted ? "×" : "♪"}</button><i>RK</i></div></header>
    <section className="forge"><div><span className="live" /><b>AI GAME FORGE</b><small>Describe a concept. We’ll turn it into a winnable challenge.</small></div><form onSubmit={event => { event.preventDefault(); void forge(); }}><label className="sr-only" htmlFor="concept">Learning concept</label><input id="concept" value={concept} disabled={submitting} onChange={event => setConcept(event.target.value)} /><button type="submit" disabled={submitting || !concept.trim()}><Bolt />{submitting ? "Forging…" : "Forge game"}</button></form>{runId && <div className="forge-progress" role="status" aria-live="polite"><span>{progress.status === "connecting" ? "Connecting to forge…" : `${progress.stage ?? "planner"} in progress`}</span><ol>{RUN_STAGES.map(stage => <li key={stage} className={progress.completed.includes(stage) ? "done" : progress.stage === stage ? "active" : ""}>{stage}</li>)}</ol></div>}{forgeError && <p className="forge-status" role="alert">{forgeError}</p>}</section>
    <div className="workspace" id="main"><aside className="lesson"><div className="index">01 <i /></div><p className="kicker">CONCEPT LOADED</p><h1>{spec.concept}</h1><p><strong>{spec.learning.principle}.</strong> {spec.learning.explanation}</p><div className="equation">{spec.game_type.replaceAll("_", " ")}</div><div className="mission"><span>YOUR MISSION</span><p>{spec.instructions}</p></div><div className="verified"><span>✓</span><div><strong>Solver verified</strong><small>This challenge is proven winnable</small></div></div></aside>
      <section className="game" aria-labelledby="game-title"><header><div><p>{spec.eyebrow}</p><h2 id="game-title">{spec.title}</h2></div><div className="meta"><span>{source === "api" ? "VERIFIED API" : "VERIFIED FIXTURE"}</span><div>{spec.difficulty.toUpperCase()}</div></div></header><GameRenderer key={`${spec.game_type}:${spec.title}`} spec={spec} /></section>
    </div><footer><span>BUILT WITH OPENAI · VERIFIED BY PHYSICS</span><span>GAME SPEC v{spec.schema_version}</span></footer>
  </main>;
}
