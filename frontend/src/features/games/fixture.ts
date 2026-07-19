import type { ProjectileGameSpec } from "../../types/game";
export const projectileFixture: ProjectileGameSpec = {
  schema_version:"1.0", game_type:"projectile_target", renderer_version:"projectile-svg@1", solver_version:"projectile@1",
  title:"Arc Runner", concept:"Projectile Motion", eyebrow:"MOTION · GRAVITY", difficulty:"intermediate",
  instructions:"Balance horizontal speed and airtime to cross the elevated target.",
  scene:{theme:"stadium",player_object:"probe",target_object:"energy_gate",effect:"orange_trail"},
  controls:{angle:{id:"angle",label:"Launch angle",min:20,max:65,step:1,default:42,unit:"degrees"},thrust:{id:"thrust",label:"Thrust",min:55,max:100,step:1,default:76,unit:"percent"}},
  physics:{gravity:9.8,target_x:566,target_y:181,launch_point:{x:102,y:366},thrust_scale:3.32,target_tolerance:42,timestep_seconds:0.025,max_steps:320},
  solution:{angle:48,power:76},
  learning:{principle:"You shaped a projectile arc",explanation:"Horizontal velocity carried the probe forward while gravity bent its path into a parabola.",hint:"Raise the angle for more airtime, or add thrust for more range."}
};
