import type { Point, ProjectileGameSpec } from "../../../types/game";
export const LAUNCH_POINT: Point = { x: 102, y: 366 };
export function simulate(spec: ProjectileGameSpec, angle: number, power: number) {
  const points: Point[] = [], radians = angle * Math.PI / 180, speed = power * spec.physics.thrust_scale;
  for (let step=0; step<spec.physics.max_steps; step+=1) {
    const t=step*spec.physics.timestep_seconds;
    const x=LAUNCH_POINT.x+speed*Math.cos(radians)*t;
    const y=LAUNCH_POINT.y-(speed*Math.sin(radians)*t-.5*spec.physics.gravity*10*t*t);
    points.push({x,y}); if(y>450||x>820) break;
  }
  const distance=Math.min(...points.map(p=>Math.hypot(p.x-spec.physics.target_x,p.y-spec.physics.target_y)));
  return {points,distance,hit:distance<=spec.physics.target_tolerance};
}
