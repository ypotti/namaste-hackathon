"""Canonical verified fixtures for math puzzles."""

from __future__ import annotations

import math
from math_puzzle_agent.schemas import PuzzleSpec, KnownValue
from .schemas import (BalanceTorqueSpecV1, FallingObjectSpecV1, FractionGroupingSpecV1,
    GameSpecV1, GraphMatchSpecV1, MomentumCollisionSpecV1, ProjectileTargetSpecV1)


CANONICAL_PUZZLE = PuzzleSpec(
    title="The 3–4–5 Triangle Challenge",
    math_concept="Pythagorean theorem",
    scene_description="A clean educational scene shows a large right-angled triangle centered on a simple pale-blue sky background, with the ground line near the bottom at y≈460px and a narrow earth strip beneath it. The 3 cm horizontal leg runs along the lower center from left to right, the 4 cm vertical leg rises at the left end, and the unknown slanted side connects the upper-left vertex to the lower-right vertex.",
    question="What is the length of the hypotenuse of this right-angled triangle in centimeters?",
    known_values=[
        KnownValue(name="First leg", value="3 cm"),
        KnownValue(name="Second leg", value="4 cm")
    ],
    learner_answer_label="Hypotenuse length (cm)",
    correct_answer=5.0,
    accepted_tolerance=0.15,
    answer_unit="cm",
    formulas=["c² = a² + b²", "c = √(a² + b²)"],
    solution_steps=[
        "1. Identify the two perpendicular legs: a = 3 cm and b = 4 cm.",
        "2. Apply the Pythagorean theorem: c² = 3² + 4² = 9 + 16 = 25.",
        "3. Take the positive square root because a length is positive: c = √25 = 5 cm."
    ],
    hint="The side opposite the right angle is the hypotenuse. Square both known leg lengths, add the results, and take the square root.",
    animation_description="During the animation, the two known side labels glow, then a dashed square grid briefly traces the right angle and the hypotenuse is highlighted from the lower-left to upper-right vertex.",
    assumptions=[
        "The triangle is right-angled at the vertex where the 3 cm and 4 cm legs meet.",
        "The requested unknown side is the hypotenuse.",
        "The diagram is not drawn to scale; the measurements and labels determine the answer."
    ]
)

DEMO_GAME_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The 3–4–5 Triangle Challenge</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px;
  background: #f1dfb7; color: #382716; font-family: Georgia, serif;
}
main { width: min(900px, 100%); text-align: center; }
h1 { margin: 0 0 8px; }
#sketch-holder canvas {
  display: block; width: 100% !important; height: auto !important;
  border: 4px solid #6f482a; border-radius: 12px;
}
.controls { margin-top: 16px; font-family: system-ui, sans-serif; }
input, button { font: inherit; padding: 9px 12px; border-radius: 7px; }
input { width: 120px; border: 1px solid #8b6b43; }
button { margin-left: 8px; border: 0; background: #8b3a1f; color: white; cursor: pointer; }
button:disabled { opacity: .55; cursor: wait; }
#message { min-height: 1.5em; margin: 10px 0 0; font-weight: 700; }
.facts { margin: 16px 0 0; font-family: system-ui, sans-serif; }
.question { margin: 10px 0 14px; font: 600 1.05rem Georgia, serif; }
.study-panel {
  margin-top: 18px; padding: 16px 20px; text-align: left;
  background: #fff8e7; border: 1px solid #b9935f; border-radius: 10px;
  font-family: system-ui, sans-serif;
}
.study-panel summary { cursor: pointer; font: 700 1.1rem Georgia, serif; color: #61361e; }
.study-panel h3 { margin: 18px 0 8px; color: #61361e; }
.study-panel p, .study-panel li { line-height: 1.55; }
.formula {
  overflow-x: auto; padding: 11px; border-radius: 6px;
  background: #f3e6c8; text-align: center; font: 1.08rem Georgia, serif;
}
.answer { color: #176b36; font-weight: 700; }
</style>
</head>
<body>
<main>
  <h1>The 3–4–5 Triangle Challenge</h1>

  <p class="facts">
    First leg: <strong>3 cm</strong> &nbsp;•&nbsp;
    Second leg: <strong>4 cm</strong>
  </p>

  <p class="question">What is the length of the hypotenuse of this right-angled triangle in centimeters?</p>

  <div id="sketch-holder"></div>

  <div class="controls">
    <label for="answer-input">Hypotenuse length (cm): </label>
    <input id="answer-input" type="number" step="any" placeholder="e.g. 2.2" aria-label="Hypotenuse length in centimeters">
    <button id="submit-btn">Submit</button>
    <p id="message" aria-live="polite">Enter your answer and submit.</p>
  </div>

  <details class="study-panel">
    <summary>Hint</summary>
    <p>The side opposite the right angle is the hypotenuse. Square both known leg lengths, add the results, and take the square root.</p>
    <div class="formula">c² = a² + b²<br>c = √(a² + b²)</div>
  </details>

  <details class="study-panel">
    <summary>Solution</summary>
    <p>1. Identify the two perpendicular legs: a = 3 cm and b = 4 cm.<br>
    2. Apply the Pythagorean theorem: c² = 3² + 4² = 9 + 16 = 25.<br>
    3. Take the positive square root because a length is positive: c = √25 = 5 cm.</p>
    <div class="formula">c = √(3² + 4²) = √(9 + 16) = √25 = 5</div>
    <p class="answer">Answer: 5 cm</p>
  </details>
</main>

<script src="https://cdn.jsdelivr.net/npm/p5@1.11.3/lib/p5.min.js"></script>
<script>
// ── 1. Constants from spec (hardcode the values from the JSON) ──────────────
const CORRECT_ANSWER = 5.0;
const TOLERANCE      = 0.15;
const FIRST_LEG = 3;
const SECOND_LEG = 4;
const ANSWER_UNIT = 'cm';

// ── 2. State ────────────────────────────────────────────────────────────────
let animating = false;
let hitFlashUntil = 0;
let animationElapsed = 0;
let answerWasCorrect = false;
let resultState = null;
let lastHitX = 625;
let lastHitY = 460;

// ── 3. DOM bindings (run after DOMContentLoaded or at script end) ────────────
const inputField = document.getElementById('answer-input');
const submitBtn  = document.getElementById('submit-btn');
const message    = document.getElementById('message');

submitBtn.addEventListener('click', onSubmit);
inputField.addEventListener('keydown', e => { if (e.key === 'Enter') onSubmit(); });

// ── 4. p5.js setup ──────────────────────────────────────────────────────────
function setup() {
  const canvas = createCanvas(900, 520);
  canvas.parent('sketch-holder');
}

// ── 5. Draw loop ────────────────────────────────────────────────────────────
function draw() {
  drawScene();
  if (animating) updateAnimation();
  if (millis() < hitFlashUntil) drawSparkEffect();
}

// ── 6. drawScene() — ALL static elements drawn here, NOWHERE ELSE ───────────
function drawScene() {
  const leftX = 280;
  const rightX = 625;
  const topY = 0;
  const groundY = 460;

  background('#cce8f4');

  noStroke();
  fill('#8B6914');
  rect(0, groundY, width, height - groundY);

  stroke('#6f482a');
  strokeWeight(8);
  line(0, groundY, width, groundY);

  strokeWeight(5);
  stroke('#382716');
  fill('#fff8e7');
  triangle(leftX, topY, leftX, groundY, rightX, groundY);

  stroke('#6f482a');
  strokeWeight(7);
  line(leftX, groundY, rightX, groundY);
  line(leftX, topY, leftX, groundY);

  if (resultState) {
    stroke(resultState === 'correct' ? '#176b36' : '#d26a18');
    strokeWeight(10);
    line(leftX, topY, rightX, groundY);
  } else {
    stroke('#61361e');
    strokeWeight(5);
    line(leftX, topY, rightX, groundY);
  }

  noStroke();
  fill('#382716');
  textAlign(CENTER, CENTER);
  textSize(24);
  textStyle(BOLD);
  text('3 cm', (leftX + rightX) / 2, groundY - 27);

  push();
  translate(leftX - 34, (topY + groundY) / 2);
  rotate(-HALF_PI);
  text('4 cm', 0, 0);
  pop();

  push();
  translate((leftX + rightX) / 2 + 34, (topY + groundY) / 2 - 22);
  rotate(atan2(groundY - topY, rightX - leftX));
  fill(resultState === 'correct' ? '#176b36' : resultState === 'wrong' ? '#d26a18' : '#61361e');
  textSize(25);
  text('? cm', 0, -12);
  pop();

  noFill();
  stroke('#61361e');
  strokeWeight(3);
  rect(leftX, groundY - 58, 58, 58);

  noStroke();
  fill('#61361e');
  textAlign(LEFT, CENTER);
  textSize(18);
  textStyle(NORMAL);
  text('right angle', leftX + 72, groundY - 28);

  if (resultState === 'correct') {
    fill('#176b36');
    textAlign(CENTER, CENTER);
    textSize(38);
    textStyle(BOLD);
    text('✓', rightX + 32, groundY - 24);
  }
}

// ── 7. updateAnimation() — moves the animated element each frame ────────────
function updateAnimation() {
  animationElapsed += deltaTime / 1000;
  const phase = animationElapsed;

  const leftX = 280;
  const rightX = 625;
  const topY = 0;
  const groundY = 460;

  if (phase < 0.85) {
    noFill();
    stroke('#ffd700');
    strokeWeight(4);
    drawingContext.shadowBlur = 14;
    drawingContext.shadowColor = '#ffd700';
    line(leftX, groundY, rightX, groundY);
    line(leftX, topY, leftX, groundY);
    drawingContext.shadowBlur = 0;
  }

  if (phase >= 0.65 && phase < 1.8) {
    push();
    stroke('#8b5a2b');
    strokeWeight(3);
    drawingContext.setLineDash([9, 8]);
    noFill();
    rect(leftX + 12, groundY - 70, 70, 70);
    drawingContext.setLineDash([]);
    pop();
  }

  const progress = constrain((phase - 1.15) / 1.75, 0, 1);
  const eased = progress * progress * (3 - 2 * progress);
  const x = lerp(leftX, rightX, eased);
  const y = lerp(topY, groundY, eased);

  if (phase >= 1.15) {
    stroke(answerWasCorrect ? '#176b36' : '#d26a18');
    strokeWeight(10);
    line(leftX, topY, x, y);

    noStroke();
    fill(answerWasCorrect ? '#176b36' : '#d26a18');
    ellipse(x, y, 20, 20);

    fill('#fff8e7');
    ellipse(x, y, 7, 7);
  }

  if (phase >= 2.9) {
    lastHitX = rightX;
    lastHitY = groundY;
    resultState = answerWasCorrect ? 'correct' : 'wrong';
    finish(
      answerWasCorrect ? '🎯 Correct! Well done.' : 'Not quite. Open the Solution panel to see the working.',
      answerWasCorrect
    );
  }
}

// ── 8. onSubmit() ───────────────────────────────────────────────────────────
function onSubmit() {
  const userVal = parseFloat(inputField.value);
  if (isNaN(userVal)) return;

  const correct = (
    Math.abs(userVal - CORRECT_ANSWER) <= TOLERANCE ||
    userVal === Math.floor(CORRECT_ANSWER) ||
    userVal === Math.ceil(CORRECT_ANSWER)
  );

  submitBtn.disabled = true;
  inputField.disabled = true;
  animating = true;
  animationElapsed = 0;
  answerWasCorrect = correct;
  resultState = null;
}

// ── 9. finish() ──────────────────────────────────────────────────────────────
function finish(text, hit) {
  message.textContent = text;
  message.style.color = hit ? '#176b36' : '#9b271e';
  if (hit) hitFlashUntil = millis() + 1800;
  animating = false;
  submitBtn.disabled = false;
  inputField.disabled = false;
}

function drawSparkEffect() {
  const cx = lastHitX;
  const cy = lastHitY - 8;

  noFill();
  stroke('#da2323');
  strokeWeight(4);
  ellipse(cx, cy, 52, 52);

  noStroke();
  fill('#ffd700');
  ellipse(cx, cy, 26, 26);

  stroke('#ff9d00');
  strokeWeight(4);
  for (let i = 0; i < 10; i++) {
    const angle = TWO_PI * i / 10;
    const inner = 30;
    const outer = 50;
    line(
      cx + cos(angle) * inner,
      cy + sin(angle) * inner,
      cx + cos(angle) * outer,
      cy + sin(angle) * outer
    );
  }
}
</script>
</body>
</html>
"""

# Restoring legacy fixtures to keep tests in tests/games/ passing
_ANGLE = 48
_POWER = 76
_FLIGHT_TIME = 2.75
_GRAVITY = 9.8
_SPEED = _POWER * 3.32

CANONICAL_PROJECTILE_GAME = ProjectileTargetSpecV1.model_validate(
    {
        "title": "Arc Runner",
        "concept": "Projectile Motion",
        "eyebrow": "MOTION · GRAVITY",
        "instructions": "Balance horizontal speed and airtime to cross the elevated target.",
        "difficulty": "intermediate",
        "scene": {
            "theme": "stadium",
            "player_object": "probe",
            "target_object": "energy_gate",
            "effect": "orange_trail",
        },
        "controls": {},
        "physics": {
            "gravity": _GRAVITY,
            "target_x": round(102 + _SPEED * math.cos(math.radians(_ANGLE)) * _FLIGHT_TIME),
            "target_y": round(
                366
                - (
                    _SPEED * math.sin(math.radians(_ANGLE)) * _FLIGHT_TIME
                    - 0.5 * _GRAVITY * 10 * _FLIGHT_TIME**2
                )
            ),
        },
        "solution": {"angle": _ANGLE, "power": _POWER},
        "learning": {
            "principle": "You shaped a projectile arc",
            "explanation": "Horizontal velocity carried the probe forward while gravity bent its path into a parabola.",
            "hint": "Raise the angle for more airtime, or add thrust for more range.",
        },
    }
)

_COPY = {"title": "Precision Challenge", "concept": "Applied mathematics", "eyebrow": "TEST · LEARN",
         "instructions": "Adjust the control until the measured result matches the target.",
         "difficulty": "starter", "learning": {"principle": "Models predict outcomes",
         "explanation": "A mathematical relationship connects the controls to the observed result.",
         "hint": "Compare your result with the target, then adjust one control."}}

CANONICAL_FALLING_GAME = FallingObjectSpecV1.model_validate({**_COPY, "game_type": "falling_object", "scene": "tower",
    "physics": {"gravity": 10.0, "target_time": 2.0}, "solution_height": 200})
CANONICAL_BALANCE_GAME = BalanceTorqueSpecV1.model_validate({**_COPY, "game_type": "balance_torque", "scene": "workshop",
    "physics": {"left_weight": 20.0, "left_distance": 3.0, "right_weight": 15.0}, "solution_right_distance": 4.0})
CANONICAL_MOMENTUM_GAME = MomentumCollisionSpecV1.model_validate({**_COPY, "game_type": "momentum_collision", "scene": "track",
    "physics": {"player_mass": 10.0, "other_mass": 10.0, "other_velocity": 0.0, "target_velocity": 5.0}, "solution_player_velocity": 10.0})
CANONICAL_FRACTION_GAME = FractionGroupingSpecV1.model_validate({**_COPY, "game_type": "fraction_grouping", "scene": "garden",
    "total_items": 12, "numerator": 2, "denominator": 3, "solution_selected_count": 8})
CANONICAL_GRAPH_GAME = GraphMatchSpecV1.model_validate({**_COPY, "game_type": "graph_match", "scene": "coordinate_grid",
    "target_slope": 2.0, "target_intercept": -3.0, "solution_slope": 2.0, "solution_intercept": -3.0})

CANONICAL_GAMES = (CANONICAL_PROJECTILE_GAME, CANONICAL_FALLING_GAME, CANONICAL_BALANCE_GAME,
                   CANONICAL_MOMENTUM_GAME, CANONICAL_FRACTION_GAME, CANONICAL_GRAPH_GAME)
