# Frontend Guidelines: Interactive Math & Physics Puzzles

## 1. Tech Stack
- **Core:** Vanilla HTML5, CSS3, and modern client-side JavaScript.
- **Libraries:** [p5.js](https://p5js.org/) loaded via standard CDN: `https://cdn.jsdelivr.net/npm/p5@1.11.3/lib/p5.min.js`.
- **Packaging:** Do not use wrappers, frameworks, bundling systems, or external custom icons. The page must be a single, self-contained HTML file runnable directly.

---

## 2. HTML Layout Structure

Every page has a centered, responsive layout wrapped inside a single `<main>` element:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Title of the Challenge</title>
    <script src="https://cdn.jsdelivr.net/npm/p5@1.11.3/lib/p5.min.js"></script>
    <style>
      /* Style Sheet (see Section 3) */
    </style>
  </head>
  <body>
    <main>
      <h1>Title of the Challenge</h1>
      
      <!-- Fact summary parameters -->
      <p class="facts">
        Distance: <strong>X m</strong> &nbsp;•&nbsp;
        Altitude/Height: <strong>Y m</strong> &nbsp;•&nbsp;
        Launch Speed (v): <strong>Z m/s</strong> &nbsp;•&nbsp;
        Gravity (g): <strong>G m/s²</strong>
      </p>
      
      <!-- Puzzle question -->
      <p class="question">Question: What launch angle/parameter should be used?</p>
      
      <!-- Container holding the p5.js canvas -->
      <div id="sketch-holder"></div>
      
      <!-- User Input and interactive buttons -->
      <div class="controls">
        <label for="angle">Launch angle (degrees): </label>
        <input id="angle" type="number" min="1" max="89" step="0.1" placeholder="e.g. 45" />
        <button id="launch">Launch/Fire</button>
        <p id="message" aria-live="polite">Choose an angle and take aim.</p>
      </div>
      
      <!-- Educational details (Hint) -->
      <details class="study-panel">
        <summary>Hint</summary>
        <p>Step-by-step guidance details...</p>
        <div class="formula">Mathematical expression or formula</div>
      </details>
      
      <!-- Educational details (Solution) -->
      <details class="study-panel">
        <summary>Solution</summary>
        <p>Detailed math solving steps...</p>
        <div class="formula">Equation resolution...</div>
        <p class="answer">Final answer: [Value] is correct.</p>
      </details>
    </main>

    <script>
      // p5.js sketch and physics loop (see Section 4)
    </script>
  </body>
</html>
```

---

## 3. Styling & Color Palette (CSS)

The page styling uses a warm, academic, low-contrast design. The exact CSS stylesheet is detailed below:

```css
* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #f1dfb7;   /* Creamy Sand Background */
  color: #382716;        /* Deep Charcoal Brown */
  font-family: Georgia, serif;
}

main {
  width: min(900px, 100%);
  text-align: center;
}

h1 {
  margin: 0 0 8px;
}

#sketch-holder canvas {
  display: block;
  width: 100% !important;
  height: auto !important;
  border: 4px solid #6f482a; /* Wood Brown Border */
  border-radius: 12px;
}

.controls {
  margin-top: 16px;
  font-family: system-ui, sans-serif;
}

input, button {
  font: inherit;
  padding: 9px 12px;
  border-radius: 7px;
}

input {
  width: 100px;
  border: 1px solid #8b6b43;
}

button {
  margin-left: 8px;
  border: 0;
  background: #8b3a1f; /* Terracotta Red */
  color: white;
  cursor: pointer;
}

button:disabled {
  opacity: .55;
  cursor: wait;
}

#message {
  min-height: 1.5em;
  margin: 10px 0 0;
  font-weight: 700;
}

.facts {
  margin: 16px 0 0;
  font-family: system-ui, sans-serif;
}

.question {
  margin: 10px 0 14px;
  font: 600 1.05rem Georgia, serif;
}

.study-panel {
  margin-top: 18px;
  padding: 16px 20px;
  text-align: left;
  background: #fff8e7; /* Light Off-White Paper Background */
  border: 1px solid #b9935f;
  border-radius: 10px;
  font-family: system-ui, sans-serif;
}

.study-panel summary {
  cursor: pointer;
  font: 700 1.1rem Georgia, serif;
  color: #61361e;
}

.study-panel h3 {
  margin: 18px 0 8px;
  color: #61361e;
}

.study-panel p, .study-panel li {
  line-height: 1.55;
}

.formula {
  overflow-x: auto;
  padding: 11px;
  border-radius: 6px;
  background: #f3e6c8; /* Warm Tan Highlight */
  text-align: center;
  font: 1.08rem Georgia, serif;
}

.answer {
  color: #176b36; /* Success Forest Green */
  font-weight: 700;
}
```

---

## 4. Script & Logic Pattern

The scripts inside HTML pages handle DOM bindings, input verification, canvas setups, physics loop animations, and termination callbacks.

### DOM Binding & Event Listeners
Select elements relative to the document scope and attach event listeners:
```javascript
const angleInput = document.querySelector('#angle');
const launchButton = document.querySelector('#launch');
const message = document.querySelector('#message');

launchButton.addEventListener('click', launchProjectile);
angleInput.addEventListener('keydown', event => {
  if (event.key === 'Enter') launchProjectile();
});
```

### Canvas Setup (`setup()`)
Create a canvas sized 900x520 and parent it directly to `#sketch-holder`:
```javascript
function setup() {
  const canvas = createCanvas(900, 520);
  canvas.parent('sketch-holder');
}
```

### Rendering Loop (`draw()`)
Segregate concerns. Render background static visuals in `drawScene()` and update moving elements inside an animation step function:
```javascript
function draw() {
  drawScene();
  if (projectile) updateProjectile();
}
```

### Hit-checking & Angle Thresholds
To ensure the math puzzle maintains exact constraints:
1. Check projectile position when it crosses/reaches the target's distance threshold (frame-rate independent).
2. **Tolerance check:** Verify if the fired parameter (e.g. angle) is within a tight threshold (`±0.15°` of the correct mathematical solution).
   - **Decimal rounding rule:** If the exact mathematical answer contains a decimal value, both the exact decimal value, its floor value, and its rounded-up (ceil) value must be accepted as correct answers.
   - If within threshold of any correct values, trigger `finish('Direct hit message', true)`.
   - If not, allow the simulation to run out and trigger `finish('Miss message', false)` in its termination state (missed high / missed low).

### Hit Animation Effects
Direct hits should render visually premium effects:
- Concentric target rings (outer red `#da2323` and inner yellow `#ffd700`).
- Overlapping fire particles using random-sized radiating lines or circles centered on the hit target coordinate.

### Finish Callback
Reset variables and enable controls:
```javascript
function finish(text, hit) {
  message.textContent = text;
  message.style.color = hit ? '#176b36' : '#9b271e';
  if (hit) hitFlashUntil = millis() + 1200; // triggers spark draw loop duration
  projectile = null;
  launchButton.disabled = false;
}
```
