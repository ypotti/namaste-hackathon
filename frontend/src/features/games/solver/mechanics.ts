import type { BalanceTorqueGameSpec,FallingObjectGameSpec,FractionGroupingGameSpec,GraphMatchGameSpec,MomentumCollisionGameSpec } from "../../../types/game";
export type ScalarResult={hit:boolean;actual:number;target:number;error:number};
const result=(actual:number,target:number,tolerance:number):ScalarResult=>({actual,target,error:Math.abs(actual-target),hit:Math.abs(actual-target)<=tolerance});
export const simulateFalling=(s:FallingObjectGameSpec,height:number)=>result(Math.sqrt(2*height/(s.physics.gravity*10)),s.physics.target_time,s.physics.time_tolerance);
export const simulateBalance=(s:BalanceTorqueGameSpec,distance:number)=>result(s.physics.right_weight*distance,s.physics.left_weight*s.physics.left_distance,s.physics.torque_tolerance);
export const simulateMomentum=(s:MomentumCollisionGameSpec,velocity:number)=>result((s.physics.player_mass*velocity+s.physics.other_mass*s.physics.other_velocity)/(s.physics.player_mass+s.physics.other_mass),s.physics.target_velocity,s.physics.velocity_tolerance);
export const simulateFraction=(s:FractionGroupingGameSpec,count:number)=>result(count,s.total_items*s.numerator/s.denominator,0);
export const simulateGraph=(s:GraphMatchGameSpec,m:number,b:number)=>{const error=Math.max(Math.abs(m-s.target_slope),Math.abs(b-s.target_intercept));return {hit:error<=s.tolerance,actual:error,target:0,error}};
