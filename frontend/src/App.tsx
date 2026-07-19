import { useEffect, useState } from "react";
import { ApiError, forgetConversation, gameContentUrl, getOrCreateConversationId, submitMessage, listGames, type GameRecord } from "./api/client";
import { RUN_STAGES } from "./features/forge/progress";
import { useRunProgress } from "./features/forge/useRunProgress";
import type { GameSpecV1 } from "./types/game";

const Bolt = () => <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m13 2-8 12h7l-1 8 8-12h-7l1-8Z" /></svg>;
type ChatMessage = { role: "user" | "assistant"; content: string };

export function App() {
  const [creatorSpec, setCreatorSpec] = useState<GameSpecV1 | undefined>();
  const [creatorGameId, setCreatorGameId] = useState<string | undefined>();
  const [learnerSpec, setLearnerSpec] = useState<GameSpecV1 | undefined>();
  const [learnerGameId, setLearnerGameId] = useState<string | undefined>();
  const [source, setSource] = useState<"api" | "fixture">("api");
  const [concept, setConcept] = useState("");
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [forgeError, setForgeError] = useState<string>();
  const [runId, setRunId] = useState<string>();
  const [muted, setMuted] = useState(false);
  const [view, setView] = useState<"creator" | "learner">("creator");
  const [dbGames, setDbGames] = useState<GameRecord[]>([]);
  const [loadingGames, setLoadingGames] = useState(false);

  useEffect(() => {
    getOrCreateConversationId().then(setConversationId).catch(() => setForgeError("The forge is offline."));
  }, []);

  useEffect(() => {
    if (view === "learner") {
      setLoadingGames(true);
      listGames()
        .then(setDbGames)
        .catch(err => console.error("Failed to load games list", err))
        .finally(() => setLoadingGames(false));
    }
  }, [view]);

  function loadCreatorGame(game: GameSpecV1, nextSource: "api" | "fixture" = "api", nextGameId?: string) { setCreatorSpec(game); setSource(nextSource); setCreatorGameId(nextGameId); }
  function finishClarification(message: string) {
    setMessages(current => [...current, { role: "assistant", content: message }]);
    setRunId(undefined); setSubmitting(false);
  }

  const progress = useRunProgress(runId, {
    onReady: record => {
      loadCreatorGame(record.spec,"api",record.id);
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
        loadCreatorGame(response.game,"api",response.game_id);
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
    setCreatorSpec(undefined); setCreatorGameId(undefined);
    void getOrCreateConversationId().then(setConversationId).catch(() => setForgeError("Could not start a new forge session."));
  }

  const prompt = messages.at(-1)?.role === "assistant" ? "Reply with the missing detail…" : "Describe the concept and learning goal—no coding required…";

  const conceptText = creatorSpec ? (creatorSpec.math_concept || (creatorSpec as any).concept) : "";
  const principleText = creatorSpec ? ((creatorSpec as any).learning?.principle || creatorSpec.title) : "";
  const explanationText = creatorSpec ? ((creatorSpec as any).learning?.explanation || creatorSpec.scene_description) : "";
  const equationText = creatorSpec ? ((creatorSpec as any).game_type ? (creatorSpec as any).game_type.replaceAll("_", " ") : "Interactive Puzzle") : "Interactive Puzzle";
  const missionText = creatorSpec ? ((creatorSpec as any).instructions || creatorSpec.question) : "";
  const eyebrowText = creatorSpec ? ((creatorSpec as any).eyebrow || "MATH PUZZLE") : "MATH PUZZLE";
  const difficultyText = creatorSpec ? ((creatorSpec as any).difficulty || "standard") : "standard";
  const schemaVersionText = creatorSpec ? ((creatorSpec as any).schema_version || "1.0") : "1.0";

  return <main className={`app-${view}`}>
    <header className="topbar">
      <a className="brand" href="#main">
        <span className="brand-mark"><Bolt /></span>
        <span>PHYSICS<span>FORGE</span><small>GAMIFIED LEARNING</small></span>
      </a>
      <nav aria-label="Workspace">
        <button className={view==="creator"?"active":""} onClick={()=>setView("creator")}>Creator</button>
        <button className={view==="learner"?"active":""} onClick={()=>{
          if (creatorSpec && !learnerSpec) {
            setLearnerSpec(creatorSpec);
            setLearnerGameId(creatorGameId);
          }
          setView("learner");
        }}>Learner view</button>
      </nav>
      <div className="head-actions">
        {view==="creator"&&<button type="button" className="new-lesson" onClick={newConcept}>New lesson</button>}
        <button className="icon" aria-label={muted ? "Turn sound on" : "Mute sound"} onClick={() => setMuted(!muted)}>{muted ? "×" : "♪"}</button>
        <i>RK</i>
      </div>
    </header>
    {view==="creator"&&<>
    <section className="forge"><div><span className="live" /><b>TEXT-TO-INTERACTIVE</b><small>Turn an educator’s idea into a solver-verified learning experience in minutes.</small></div><form onSubmit={event => { event.preventDefault(); void forge(); }}><label className="sr-only" htmlFor="concept">Describe a learning concept</label><input id="concept" value={concept} placeholder={prompt} disabled={submitting} onChange={event => setConcept(event.target.value)} /><button type="submit" disabled={submitting || !concept.trim()}><Bolt />{submitting ? "Building…" : messages.length ? "Send" : "Create lesson"}</button></form>
      {messages.length > 0 && <div className="forge-chat" aria-live="polite">{messages.map((message, index) => <p key={index} className={message.role}><strong>{message.role === "user" ? "You" : "Forge"}</strong>{message.content}</p>)}</div>}
      {runId && <div className="forge-progress" role="status" aria-live="polite"><span>{progress.status === "connecting" ? "Connecting to forge…" : `${progress.stage ?? "planner"} in progress`}</span><ol>{RUN_STAGES.map(stage => <li key={stage} className={progress.completed.includes(stage) ? "done" : progress.stage === stage ? "active" : ""}>{stage}</li>)}</ol></div>}{forgeError && <p className="forge-status" role="alert">{forgeError} <button type="button" onClick={newConcept}>Start over</button></p>}</section>
    {creatorSpec ? (
      <div className="workspace" id="main"><aside className="lesson"><div className="index">01 <i /></div><p className="kicker">CONCEPT LOADED</p><h1>{conceptText}</h1><p><strong>{principleText}.</strong> {explanationText}</p><div className="equation">{equationText}</div><div className="mission"><span>YOUR MISSION</span><p>{missionText}</p></div><div className="verified"><span>✓</span><div><strong>Solver verified</strong><small>This challenge is proven winnable</small></div></div></aside>
        <section className="game creator-preview" aria-labelledby="game-title"><header><div><p>CREATOR PREVIEW · {eyebrowText}</p><h2 id="game-title">{creatorSpec.title}</h2></div><button className="open-learner" onClick={()=>{ setLearnerSpec(creatorSpec); setLearnerGameId(creatorGameId); setView("learner"); }}>Open learner view</button><div className="meta"><span>{source === "api" ? "GAME READY" : "DEMO READY"}</span><div>{difficultyText.toUpperCase()}</div></div></header><iframe key={gameContentUrl(creatorGameId)} title={`${creatorSpec.title} creator preview`} src={gameContentUrl(creatorGameId)} sandbox="allow-scripts" /></section>
      </div>
    ) : (
      <div className="workspace-empty" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "350px", padding: "40px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "6px", margin: "30px 40px", textAlign: "center" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>⚡</div>
        <h3 style={{ margin: "0 0 10px", color: "var(--ink)", fontSize: "20px", fontWeight: 800 }}>No active lesson</h3>
        <p style={{ margin: 0, color: "var(--muted)", maxWidth: "480px", fontSize: "14px", lineHeight: "1.6" }}>
          Describe a math or physics learning concept in the text input box above (for example: <em>"projectile motion from a cliff"</em>) to build a solver-verified interactive game lesson!
        </p>
      </div>
    )}
    </>}
    {view==="learner"&&<section className="learner-shell" id="main">
      <div className="learner-heading">
        <div>
          <span>LEARNER EXPERIENCE</span>
          <h1>{learnerSpec ? learnerSpec.title : "Select a Lesson"}</h1>
        </div>
        <button onClick={()=>setView("creator")}>Back to creator</button>
      </div>
      <div className="learner-layout">
        <aside className="learner-sidebar">
          <h3>Available Lessons</h3>
          {loadingGames ? (
            <p className="loading-text" style={{ font: "500 11px var(--mono)", color: "var(--muted)" }}>Loading lessons...</p>
          ) : dbGames.length === 0 ? (
            <p className="empty-text" style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.5 }}>No lessons found in the database. Go to the Creator view and create one!</p>
          ) : (
            <div className="game-list">
              {dbGames.map(game => (
                <button
                  key={game.id}
                  className={`game-list-item ${learnerGameId === game.id ? "active" : ""}`}
                  onClick={() => { setLearnerSpec(game.spec); setLearnerGameId(game.id); }}
                >
                  <h4>{game.spec.title}</h4>
                  <p>{game.spec.math_concept || (game.spec as any).concept || "Physics concept"}</p>
                </button>
              ))}
            </div>
          )}
        </aside>
        <div className="learner-content">
          {learnerSpec ? (
            <iframe key={`learner-${gameContentUrl(learnerGameId)}`} title={`${learnerSpec.title} learner game`} src={gameContentUrl(learnerGameId)} sandbox="allow-scripts" />
          ) : (
            <div className="learner-empty-state">
              <div style={{ fontSize: "40px", marginBottom: "12px" }}>🕹️</div>
              <h3>Choose a Puzzle</h3>
              <p>Select any math/physics lesson from the list on the left to start playing and learning.</p>
            </div>
          )}
        </div>
      </div>
    </section>}
    <footer><span>LESSONS TURNED INTO GAMES · KNOWLEDGE THAT STICKS</span><span>HTML ARTIFACT · GAME SPEC v{schemaVersionText}</span></footer>
  </main>;
}
