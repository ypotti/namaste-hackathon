import { createContext,useContext,useState,type ReactNode } from "react";
import type { GameSpecV1 } from "../../types/game";
export type GameMode="puzzle"|"sandbox";
const GameModeContext=createContext<GameMode>("puzzle");
export const GameModeProvider=({mode,children}:{mode:GameMode;children:ReactNode})=><GameModeContext.Provider value={mode}>{children}</GameModeContext.Provider>;
export function GameChrome({spec,children,onCheck,onReset,feedback,won}:{spec:any;children:ReactNode;onCheck:()=>void;onReset:()=>void;feedback?:string;won:boolean}){
 const [hint,setHint]=useState(false);
 const mode=useContext(GameModeContext);
 const principle = (spec as any).learning?.principle || spec.math_concept || "Concept Mastered";
 const hintText = (spec as any).learning?.hint || spec.hint || "Try adjusting the variables.";
 return <section aria-label={`${spec.title} ${mode} game`}><div className="stage">{children}</div>{mode==="puzzle"?<><div className="game-actions">
  <button className="launch" onClick={onCheck}>{won?"Solved":"Check answer"}</button><button type="button" onClick={()=>setHint(v=>!v)}>Hint</button><button type="button" onClick={()=>{setHint(false);onReset()}}>Replay</button>
 </div>{feedback&&<p role="status" aria-live="polite"><strong>{won?principle:"Keep experimenting"}</strong> — {feedback}</p>}{hint&&<p role="note">{hintText}</p>}</>:<div className="sandbox-bar"><span><strong>Live exploration</strong> — adjust the variables and watch the model respond in real time.</span><button type="button" onClick={onReset}>Reset variables</button></div>}</section>
}
export const Slider=({label,value,set,min,max,step=1,unit}:{label:string;value:number;set:(v:number)=>void;min:number;max:number;step?:number;unit:string})=><label className="control"><span>{label} <output>{value}{unit}</output></span><input aria-label={label} type="range" min={min} max={max} step={step} value={value} onChange={e=>set(Number(e.target.value))}/></label>;
