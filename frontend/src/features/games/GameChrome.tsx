import { useState,type ReactNode } from "react";
import type { GameSpecV1 } from "../../types/game";
export function GameChrome({spec,children,onCheck,onReset,feedback,won}:{spec:GameSpecV1;children:ReactNode;onCheck:()=>void;onReset:()=>void;feedback?:string;won:boolean}){
 const [hint,setHint]=useState(false);
 return <section aria-label={`${spec.title} game`}><div className="stage">{children}</div><div className="game-actions">
  <button className="launch" onClick={onCheck}>{won?"Solved":"Check answer"}</button><button type="button" onClick={()=>setHint(v=>!v)}>Hint</button><button type="button" onClick={()=>{setHint(false);onReset()}}>Replay</button>
 </div>{feedback&&<p role="status" aria-live="polite"><strong>{won?spec.learning.principle:"Keep experimenting"}</strong> — {feedback}</p>}{hint&&<p role="note">{spec.learning.hint}</p>}</section>
}
export const Slider=({label,value,set,min,max,step=1,unit}:{label:string;value:number;set:(v:number)=>void;min:number;max:number;step?:number;unit:string})=><label className="control"><span>{label} <output>{value}{unit}</output></span><input aria-label={label} type="range" min={min} max={max} step={step} value={value} onChange={e=>set(Number(e.target.value))}/></label>;
