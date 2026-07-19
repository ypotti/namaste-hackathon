# Pitch Deck Alignment

This document maps the July 2026 **Gamified Learning** pitch deck to the
implemented product and keeps demo claims honest.

## Product promise

**Lessons turned into games. Knowledge that sticks.** Educators describe a
concept and learning goal in natural language. The application asks only for
essential details, generates a structured interactive lesson, verifies that
its puzzle is solvable, and renders it without requiring the educator to
program.

## Deck-to-product mapping

| Pitch claim | Product evidence | Status |
| --- | --- | --- |
| Pedagogy should not require programming | Natural-language forge with clarification chat | Delivered |
| Text-to-animation | Structured `GameSpec` generation and trusted React/SVG renderers | Delivered |
| Puzzle Mode | Target, solver, hints, answer checks, win/loss feedback, replay | Delivered |
| Sandbox Mode | Explicit mode switch, live variable controls, immediate visual response, reset | Delivered |
| Planner → Generator → Reviewer/QA | LangGraph planner, structured generator, deterministic solver/reviewer | Delivered |
| Real-time rendering | Browser-side SVG rendering responds immediately to controls | Delivered |
| Consistent quality | Shared design tokens, renderer chrome, schema validation, visual regression tests | Delivered |
| Rapid creation and reuse | Persistent conversations, runs, and games in PostgreSQL | Delivered |
| LMS-ready artifact | Deterministic embed/export package generated from a verified `GameSpec` | Next release |
| Course SyncLab | Video ingestion, transcript extraction, and timed widgets | Roadmap |
| Multi-step conceptual flow | Course-level decomposition into linked micro-simulations | Roadmap |

## Architecture wording for the pitch

The deck currently says that the model generates p5.js and every simulation is
a dependency-free HTML file. The production architecture intentionally improves
on this:

1. The model generates bounded educational data, not executable code.
2. Pydantic validates the contract.
3. A deterministic solver proves the puzzle is winnable.
4. Trusted, versioned React/SVG renderers provide the interaction and visuals.
5. A future export service can package the verified spec and renderer as an LMS
   embed without asking the model to write arbitrary JavaScript.

For demos and judging, describe this as **structured generation with solver
verification**. Do not claim that standalone LMS export, Course SyncLab, or
multi-step curriculum generation is already shipped.

## Recommended deck corrections

- Slide 5: change “Text-to-Animation” to “Text-to-Interactive Learning.”
- Slide 8: change “Code Generator” to “Structured Game Generator.”
- Slide 8: change “Produces responsive p5.js visual logic” to “Produces a
  validated game specification for trusted renderers.”
- Slide 8: change “self-contained HTML” to “portable, versioned embed package”
  once export is implemented; until then label this item as roadmap.
- Keep Course SyncLab and Multi-Step Conceptual Flow explicitly labeled as the
  road ahead.

