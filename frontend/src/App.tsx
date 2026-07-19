import { useEffect, useState } from "react";
import { ApiError, forgetConversation, gameContentUrl, getDemoGame, getOrCreateConversationId, submitMessage } from "./api/client";
import { RUN_STAGES } from "./features/forge/progress";
import { useRunProgress } from "./features/forge/useRunProgress";
import { projectileFixture } from "./features/games/fixture";
import type { GameSpecV1 } from "./types/game";

const Bolt = () => <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m13 2-8 12h7l-1 8 8-12h-7l1-8Z" /></svg>;
type ChatMessage = { role: "user" | "assistant"; content: string };

export function App() {
  const [spec, setSpec] = useState<GameSpecV1>(projectileFixture);
  const [source, setSource] = useState<"api" | "fixture">("fixture");
  const [concept, setConcept] = useState("");
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [forgeError, setForgeError] = useState<string>();
  const [runId, setRunId] = useState<string>();
  const [muted, setMuted] = useState(false);
  const [gameId, setGameId] = useState<string>();
  const [view, setView] = useState<"creator" | "learner">("creator");

  useEffect(() => {
    const controller = new AbortController();
    getDemoGame(controller.signal).then(game => loadGame(game, "api")).catch(error => {
      if (!(error instanceof DOMException && error.name === "AbortError")) setSource("fixture");
    });
    getOrCreateConversationId().then(setConversationId).catch(() => setForgeError("The forge is offline. You can still play the demo game."));
    return () => controller.abort();
  }, []);

  function loadGame(game: GameSpecV1, nextSource: "api" | "fixture" = "api", nextGameId?: string) { setSpec(game); setSource(nextSource); setGameId(nextGameId); }
  function finishClarification(message: string) {
    setMessages(current => [...current, { role: "assistant", content: message }]);
    setRunId(undefined); setSubmitting(false);
  }

  const progress = useRunProgress(runId, {
    onReady: record => {
      loadGame(record.spec,"api",record.id);
      setMessages(current => [...current, { role: "assistant", content: `Your game “${record.spec.title}” is ready. Preview it here or open Learner view.` }]);
      setRunId(undefined); setSubmitting(false);
    },
    onNeedsMoreInfo: finishClarification,
    onFailed: message => { setForgeError(message); setRunId(undefined); setSubmitting(false); },
  });

  async function send(content: string, allowRetry = true) {
    try {
      const id = conversationId ?? await getOrCreateConversationId();
      setConversationId(id);
      return await submitMessage(id, content);
    } catch (error) {
      if (allowRetry && error instanceof ApiError && error.status === 404) {
        forgetConversation(); setConversationId(undefined);
        return send(content, false);
      }
      throw error;
    }
  }

  async function forge() {
    const content = concept.trim();
    if (!content || submitting) return;
    setSubmitting(true); setForgeError(undefined); setRunId(undefined); setConcept("");
    setMessages(current => [...current, { role: "user", content }]);
    try {
      const response = await send(content);
      if (response.status === "ready") {
        loadGame(response.game,"api",response.game_id);
        setMessages(current => [...current, { role: "assistant", content: response.assistant_message?.content ?? `Your game “${response.game.title}” is ready.` }]);
        setSubmitting(false);
      } else if (response.status === "needs_more_info") finishClarification(response.assistant_message.content);
      else setRunId(response.run_id);
    } catch (error) {
      setConcept(content);
      setForgeError(error instanceof Error ? error.message : "The forge could not create this game. The demo remains available.");
      setSubmitting(false);
    }
  }

  function newConcept() {
    forgetConversation();
    setConversationId(undefined); setMessages([]); setConcept(""); setForgeError(undefined); setRunId(undefined); setSubmitting(false);
    void getOrCreateConversationId().then(setConversationId).catch(() => setForgeError("Could not start a new forge session."));
  }

  const prompt = messages.at(-1)?.role === "assistant" ? "Reply with the missing detail…" : "Describe the concept and learning goal—no coding required…";

  const conceptText = spec.math_concept || (spec as any).concept;
  const principleText = (spec as any).learning?.principle || spec.title;
  const explanationText = (spec as any).learning?.explanation || spec.scene_description;
  const equationText = (spec as any).game_type ? (spec as any).game_type.replaceAll("_", " ") : "Interactive Puzzle";
  const missionText = (spec as any).instructions || spec.question;
  const eyebrowText = (spec as any).eyebrow || "MATH PUZZLE";
  const difficultyText = (spec as any).difficulty || "standard";
  const schemaVersionText = (spec as any).schema_version || "1.0";

  return <main className={`app-${view}`}>
    <header className="topbar"><a className="brand" href="#main"><span className="brand-mark"><Bolt /></span><span>PHYSICS<span>FORGE</span><small>GAMIFIED LEARNING</small></span></a><nav aria-label="Workspace"><button className={view==="creator"?"active":""} onClick={()=>setView("creator")}>Creator</button><button className={view==="learner"?"active":""} onClick={()=>setView("learner")}>Learner view</button></nav><div className="head-actions">{view==="creator"&&<button type="button" className="new-lesson" onClick={newConcept}>New lesson</button>}<button className="icon" aria-label={muted ? "Turn sound on" : "Mute sound"} onClick={() => setMuted(!muted)}>{muted ? "×" : "♪"}</button><i>RK</i></div></header>
    {view==="creator"&&<>
    <section className="forge"><div><span className="live" /><b>TEXT-TO-INTERACTIVE</b><small>Turn an educator’s idea into a solver-verified learning experience in minutes.</small></div><form onSubmit={event => { event.preventDefault(); void forge(); }}><label className="sr-only" htmlFor="concept">Describe a learning concept</label><input id="concept" value={concept} placeholder={prompt} disabled={submitting} onChange={event => setConcept(event.target.value)} /><button type="submit" disabled={submitting || !concept.trim()}><Bolt />{submitting ? "Building…" : messages.length ? "Send" : "Create lesson"}</button></form>
      {messages.length > 0 && <div className="forge-chat" aria-live="polite">{messages.map((message, index) => <p key={index} className={message.role}><strong>{message.role === "user" ? "You" : "Forge"}</strong>{message.content}</p>)}</div>}
      {runId && <div className="forge-progress" role="status" aria-live="polite"><span>{progress.status === "connecting" ? "Connecting to forge…" : `${progress.stage ?? "planner"} in progress`}</span><ol>{RUN_STAGES.map(stage => <li key={stage} className={progress.completed.includes(stage) ? "done" : progress.stage === stage ? "active" : ""}>{stage}</li>)}</ol></div>}{forgeError && <p className="forge-status" role="alert">{forgeError} <button type="button" onClick={newConcept}>Start over</button></p>}</section>
    <div className="workspace" id="main"><aside className="lesson"><div className="index">01 <i /></div><p className="kicker">CONCEPT LOADED</p><h1>{conceptText}</h1><p><strong>{principleText}.</strong> {explanationText}</p><div className="equation">{equationText}</div><div className="mission"><span>YOUR MISSION</span><p>{missionText}</p></div><div className="verified"><span>✓</span><div><strong>Solver verified</strong><small>This challenge is proven winnable</small></div></div></aside>
      <section className="game creator-preview" aria-labelledby="game-title"><header><div><p>CREATOR PREVIEW · {eyebrowText}</p><h2 id="game-title">{spec.title}</h2></div><button className="open-learner" onClick={()=>setView("learner")}>Open learner view</button><div className="meta"><span>{source === "api" ? "GAME READY" : "DEMO READY"}</span><div>{difficultyText.toUpperCase()}</div></div></header><iframe key={gameContentUrl(gameId)} title={`${spec.title} creator preview`} src={gameContentUrl(gameId)} sandbox="allow-scripts" /></section>
    </div></>}
    {view==="learner"&&<section className="learner-shell" id="main"><div className="learner-heading"><div><span>LEARNER EXPERIENCE</span><h1>{spec.title}</h1></div><button onClick={()=>setView("creator")}>Back to creator</button></div><iframe key={`learner-${gameContentUrl(gameId)}`} title={`${spec.title} learner game`} src={gameContentUrl(gameId)} sandbox="allow-scripts" /></section>}
    <footer><span>LESSONS TURNED INTO GAMES · KNOWLEDGE THAT STICKS</span><span>HTML ARTIFACT · GAME SPEC v{schemaVersionText}</span></footer>
  </main>;
}
