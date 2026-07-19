import type { PuzzleSpec, ProjectileGameSpec } from "../../types/game";

export const projectileGameFixture: ProjectileGameSpec = {
  schema_version:"1.0", game_type:"projectile_target", renderer_version:"projectile-svg@1", solver_version:"projectile@1",
  title:"Arc Runner", concept:"Projectile Motion", eyebrow:"MOTION · GRAVITY", difficulty:"intermediate",
  instructions:"Balance horizontal speed and airtime to cross the elevated target.",
  scene:{theme:"stadium",player_object:"probe",target_object:"energy_gate",effect:"orange_trail"},
  controls:{angle:{id:"angle",label:"Launch angle",min:20,max:65,step:1,default:42,unit:"degrees"},thrust:{id:"thrust",label:"Thrust",min:55,max:100,step:1,default:76,unit:"percent"}},
  physics:{gravity:9.8,target_x:566,target_y:181,launch_point:{x:102,y:366},thrust_scale:3.32,target_tolerance:42,timestep_seconds:0.025,max_steps:320},
  solution:{angle:48,power:76},
  learning:{principle:"You shaped a projectile arc",explanation:"Horizontal velocity carried the probe forward while gravity bent its path into a parabola.",hint:"Raise the angle for more airtime, or add thrust for more range."}
};

export const projectileFixture: PuzzleSpec = {
  title: "The 3–4–5 Triangle Challenge",
  math_concept: "Pythagorean theorem",
  scene_description: "A clean educational scene shows a large right-angled triangle centered on a simple pale-blue sky background, with the ground line near the bottom at y≈460px and a narrow earth strip beneath it. The 3 cm horizontal leg runs along the lower center from left to right, the 4 cm vertical leg rises at the left end, and the unknown slanted side connects the upper-left vertex to the lower-right vertex.",
  question: "What is the length of the hypotenuse of this right-angled triangle in centimeters?",
  known_values: [
    { name: "First leg", value: "3 cm" },
    { name: "Second leg", value: "4 cm" }
  ],
  learner_answer_label: "Hypotenuse length (cm)",
  correct_answer: 5.0,
  accepted_tolerance: 0.15,
  answer_unit: "cm",
  formulas: ["c² = a² + b²", "c = √(a² + b²)"],
  solution_steps: [
    "1. Identify the two perpendicular legs: a = 3 cm and b = 4 cm.",
    "2. Apply the Pythagorean theorem: c² = 3² + 4² = 9 + 16 = 25.",
    "3. Take the positive square root because a length is positive: c = √25 = 5 cm."
  ],
  hint: "The side opposite the right angle is the hypotenuse. Square both known leg lengths, add the results, and take the square root.",
  animation_description: "During the animation, the two known side labels glow, then a dashed square grid briefly traces the right angle and the hypotenuse is highlighted from the lower-left to upper-right vertex.",
  assumptions: [
    "The triangle is right-angled at the vertex where the 3 cm and 4 cm legs meet.",
    "The requested unknown side is the hypotenuse.",
    "The diagram is not drawn to scale; the measurements and labels determine the answer."
  ]
};
