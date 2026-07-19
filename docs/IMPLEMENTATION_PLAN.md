# PhysicsForge Rebuild: Implementation Plan

## 1. Objective

Rebuild the current Python CLI as a web application in this repository with:

- a React and TypeScript frontend that follows the visual language of the
  `openai-hackathon` demo;
- a Python FastAPI backend around the existing LangGraph workflow;
- PostgreSQL for conversations, messages, generated games, workflow runs, and
  LangGraph checkpoints;
- structured, validated game specifications returned by the API;
- trusted React SVG/Canvas renderers instead of model-generated HTML, CSS, and
  JavaScript;
- deterministic solvers that prove every generated game is playable; and
- consistent, responsive, accessible game UI enforced by a shared design
  system.

The demo repository is a visual and behavior reference. This repository will
become the new source of truth.

## 2. Product Scope

### MVP

The first production-shaped version will support:

1. Starting a new puzzle conversation.
2. Describing a math or physics learning concept in natural language.
3. Answering one or more essential clarification questions.
4. Viewing generation progress.
5. Receiving a schema-valid and solver-verified game.
6. Playing the game in a consistent PhysicsForge UI.
7. Receiving hints, attempt-aware feedback, and a teaching explanation.
8. Replaying a game without another model call.
9. Restoring conversations and games after a page refresh.
10. Creating a new session or regenerating a failed/unwanted game.

### Deferred

- Authentication and multi-user accounts
- Real streaks, achievements, and profiles
- Social sharing and public galleries
- Teacher dashboards and analytics
- Collaborative games
- Arbitrary model-generated code
- Standalone HTML export
- Native mobile applications
- Object storage for large artifacts and screenshots

Standalone HTML can later be exported deterministically from a stored
`GameSpec`; it should not be authored directly by the model.

## 3. Architectural Principles

1. **The model generates data, not frontend code.** The model selects a known
   game mechanic and supplies bounded parameters, educational content, and
   scene choices.
2. **React owns presentation and interaction.** Layout, styling, animation,
   accessibility, and state transitions live in tested frontend components.
3. **The backend is authoritative.** FastAPI validates specifications, verifies
   the solution, persists state, and controls model access.
4. **One physics contract is shared.** The backend solver and frontend renderer
   must implement the same versioned formulas and constants.
5. **Only verified games are playable.** A game cannot reach `ready` unless its
   schema, semantic rules, and solver all pass.
6. **Persistence is explicit.** PostgreSQL is the normal runtime dependency;
   in-memory or preset behavior is an intentional demo/test mode only.
7. **Visual consistency is deterministic.** Design tokens, renderer components,
   and screenshot tests enforce the style guidelines.

## 4. Target System

```text
React + TypeScript (Vite)
  ├── Forge/chat experience
  ├── PhysicsForge design system
  ├── Game renderer registry
  └── SVG/Canvas renderers
              │
              │ REST + Server-Sent Events
              ▼
FastAPI
  ├── Conversation API
  ├── Generation/run API
  ├── LangGraph orchestration
  ├── Pydantic GameSpec validation
  ├── Deterministic solver registry
  └── Persistence services
              │
              ▼
PostgreSQL
  ├── Application tables
  └── LangGraph checkpoint tables
```

### Proposed repository layout

```text
namaste-hackathon/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── app/
│   │   ├── components/
│   │   ├── design-system/
│   │   ├── features/forge/
│   │   ├── features/games/
│   │   │   ├── renderers/
│   │   │   ├── scenes/
│   │   │   ├── effects/
│   │   │   └── solver/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── types/
│   ├── tests/
│   ├── package.json
│   └── vite.config.ts
├── src/math_puzzle_agent/
│   ├── api/
│   │   ├── app.py
│   │   ├── dependencies.py
│   │   ├── errors.py
│   │   └── routes/
│   ├── db/
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── session.py
│   ├── games/
│   │   ├── schemas.py
│   │   ├── registry.py
│   │   ├── validators.py
│   │   └── solvers/
│   ├── services/
│   │   ├── conversations.py
│   │   └── generation.py
│   ├── workflow.py
│   ├── prompts.py
│   └── config.py
├── migrations/
├── tests/
│   ├── api/
│   ├── games/
│   ├── integration/
│   └── workflow/
├── docs/
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 5. Canonical Game Contract

The backend Pydantic model is the canonical contract. The frontend TypeScript
type should be generated from the backend OpenAPI schema or checked against it
in CI to prevent drift.

### Base specification

```json
{
  "schema_version": "1.0",
  "game_type": "projectile_target",
  "title": "Arc Runner",
  "concept": "Projectile Motion",
  "eyebrow": "MOTION · GRAVITY",
  "instructions": "Guide the probe through the elevated gate.",
  "difficulty": "starter",
  "scene": {
    "theme": "stadium",
    "player_object": "probe",
    "target_object": "energy_gate",
    "effect": "orange_trail"
  },
  "controls": [],
  "parameters": {},
  "solution": {},
  "learning": {
    "principle": "You shaped a projectile arc",
    "explanation": "Horizontal velocity and gravity created the arc.",
    "hint": "Increase airtime by raising the angle slightly."
  }
}
```

### Contract rules

- `schema_version` is mandatory and immutable for an existing game.
- `game_type` must exist in the backend and frontend registries.
- Every game type has a discriminated Pydantic subtype.
- Numeric values have explicit ranges and units.
- Scene choices come from enumerations; arbitrary CSS and SVG are forbidden.
- The client never receives hidden solver-only solution values until the API
  contract explicitly permits them. During the MVP, solution parameters may be
  delivered to the browser because game logic runs client-side, but they must
  not be displayed before the teaching/reveal state.
- A stored game records the solver and renderer contract version used to
  verify it.

### Initial game mechanics

Start narrow and build each mechanic completely:

1. `projectile_target`
2. `falling_object`
3. `balance_torque`
4. `momentum_collision`
5. `fraction_grouping`
6. `graph_match`

The first vertical slice should implement only `projectile_target`. Additional
mechanics are added after the registry and test harness are stable.

## 6. Game Renderer Architecture

### Renderer registry

```text
GameRenderer
  ├── validates supported schema version
  ├── selects renderer by game_type
  └── wraps renderer in the shared GameShell

Renderer registry
  ├── projectile_target -> ProjectileTargetGame
  ├── falling_object    -> FallingObjectGame
  ├── balance_torque    -> BalanceTorqueGame
  ├── momentum_collision -> MomentumCollisionGame
  ├── fraction_grouping -> FractionGroupingGame
  └── graph_match       -> GraphMatchGame
```

### SVG versus Canvas

- Use SVG by default for scenes, controls, trajectories, labels, targets, and
  moderate animations.
- Use Canvas only when a mechanic needs high-frequency drawing or many moving
  objects.
- Keep game state and physics outside the drawing layer so SVG and Canvas
  renderers can consume the same simulation result.
- Support reduced motion and keyboard operation.

### Shared game shell

All games use the same trusted components:

- `GameHeader`
- `MissionPanel`
- `GameStage`
- `GameControls`
- `AttemptCounter`
- `HintPanel`
- `FeedbackBanner`
- `SuccessOverlay`
- `LearningExplanation`
- `ReplayButton`

The model cannot replace or restyle these components.

## 7. Design-System Plan

Port the useful visual rules from the demo into a small first-party design
system rather than copying one large page stylesheet.

### Foundations

- Color tokens: ink, forest, paper, surface, orange, success, danger, muted
- Typography: display/sans and technical/mono roles
- Spacing scale
- Borders, radii, and shadows
- Responsive breakpoints
- Focus rings and disabled states
- Animation durations and easing
- Reduced-motion variants

### Components

- Button, icon button, input, range control
- Badge and status indicator
- Card and panel
- Header/navigation
- Progress indicator
- Modal/overlay
- Empty, loading, and error states

### Scene library

Trusted SVG components will provide visual variety without arbitrary markup:

- Themes: laboratory, moon, stadium, orbit, cliff, classroom
- Actors: probe, ball, cart, block, basket
- Targets: hoop, gate, platform, zone, graph point
- Decorations: grid, measurement arrows, trajectory guide
- Effects: trail, pulse, impact burst, correct glow, miss indicator

### Visual acceptance

- The forge shell should closely match the demo at desktop and mobile widths.
- Every renderer must look native to the same product.
- No game may introduce its own fonts, color palette, or page layout.
- Canonical screenshots must pass visual regression tests.

## 8. Backend Workflow Redesign

Replace the HTML-oriented workflow with a structured game pipeline.

### Nodes

1. **Planner**
   - Reads conversation history.
   - Asks one essential clarification question when required.
   - Produces an educational `PuzzleSpec` when ready.
2. **Game designer**
   - Maps the puzzle to a supported `game_type`.
   - Produces a typed `GameSpec` using structured model output.
3. **Schema validator**
   - Validates the discriminated Pydantic model and bounded values.
4. **Solver**
   - Replays the proposed solution using the authoritative backend contract.
5. **Reviewer**
   - Checks educational clarity, consistency, difficulty, and scene choices.
   - It does not review generated CSS or arbitrary HTML.
6. **Repair loop**
   - Returns precise validation/solver/reviewer failures to the game designer.
   - Uses a bounded retry count.
7. **Persist and finish**
   - Stores only a valid, solver-verified game.
   - Returns the game identifier and public specification.

### State changes

Remove these HTML-specific fields:

- `generated_html`
- `output_path`

Add:

- `puzzle_spec`
- `game_spec`
- `validation_errors`
- `solver_result`
- `reviewer_decision`
- `generation_attempts`
- `game_id`

### Preset fallback

Preserve a no-credentials demo path for local UI development and automated
tests. Presets must use the exact same schemas and solvers as generated games.

## 9. FastAPI Contract

All endpoints are prefixed with `/api/v1`.

### System

```http
GET /health
GET /ready
```

`health` confirms the process is alive. `ready` confirms required dependencies
such as PostgreSQL are available.

### Conversations

```http
POST   /conversations
GET    /conversations
GET    /conversations/{conversation_id}
DELETE /conversations/{conversation_id}
```

Create response:

```json
{
  "id": "uuid",
  "title": null,
  "status": "active",
  "created_at": "timestamp"
}
```

Deletion should be soft deletion during the MVP.

### Messages

```http
GET  /conversations/{conversation_id}/messages
POST /conversations/{conversation_id}/messages
```

Request:

```json
{
  "content": "Build a projectile-motion game about a ball and a hoop"
}
```

Possible immediate response when clarification is needed:

```json
{
  "status": "needs_more_info",
  "assistant_message": {
    "id": "uuid",
    "content": "How far away and how high should the hoop be?"
  }
}
```

Generation response:

```json
{
  "status": "processing",
  "run_id": "uuid"
}
```

### Runs and progress

```http
GET  /runs/{run_id}
GET  /runs/{run_id}/events
POST /runs/{run_id}/cancel
```

`events` uses Server-Sent Events for these versioned event types:

- `planner.started`
- `planner.needs_more_info`
- `planner.completed`
- `designer.started`
- `validator.completed`
- `solver.completed`
- `reviewer.started`
- `repair.started`
- `game.ready`
- `run.failed`
- `run.cancelled`

The database remains authoritative. Reconnecting clients first fetch the run
and then subscribe for subsequent events.

### Games

```http
GET  /games/{game_id}
GET  /conversations/{conversation_id}/games
POST /games/{game_id}/attempts
POST /games/{game_id}/regenerate
```

Attempt persistence can be included in the MVP if it is needed for restore and
learning history; otherwise it is the first post-MVP addition.

### Error envelope

```json
{
  "error": {
    "code": "unsupported_game_type",
    "message": "This puzzle cannot be rendered yet.",
    "request_id": "uuid",
    "details": null
  }
}
```

Do not return stack traces, prompts, credentials, or raw provider errors.

## 10. PostgreSQL Model

Use migrations; do not create production tables lazily during requests.

### `conversations`

- `id UUID PRIMARY KEY`
- `title TEXT NULL`
- `status TEXT NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`
- `deleted_at TIMESTAMPTZ NULL`

### `messages`

- `id UUID PRIMARY KEY`
- `conversation_id UUID NOT NULL REFERENCES conversations(id)`
- `role TEXT NOT NULL`
- `content TEXT NOT NULL`
- `metadata JSONB NOT NULL DEFAULT '{}'`
- `created_at TIMESTAMPTZ NOT NULL`

Index `(conversation_id, created_at)`.

### `generation_runs`

- `id UUID PRIMARY KEY`
- `conversation_id UUID NOT NULL REFERENCES conversations(id)`
- `status TEXT NOT NULL`
- `puzzle_spec JSONB NULL`
- `candidate_game_spec JSONB NULL`
- `solver_result JSONB NULL`
- `review_result JSONB NULL`
- `attempt_count INTEGER NOT NULL DEFAULT 0`
- `error_code TEXT NULL`
- `error_message TEXT NULL`
- `started_at TIMESTAMPTZ NOT NULL`
- `completed_at TIMESTAMPTZ NULL`

Indexes on `(conversation_id, started_at)` and `status`.

### `games`

- `id UUID PRIMARY KEY`
- `conversation_id UUID NOT NULL REFERENCES conversations(id)`
- `generation_run_id UUID NOT NULL REFERENCES generation_runs(id)`
- `schema_version TEXT NOT NULL`
- `contract_version TEXT NOT NULL`
- `game_type TEXT NOT NULL`
- `title TEXT NOT NULL`
- `concept TEXT NOT NULL`
- `spec JSONB NOT NULL`
- `verification_status TEXT NOT NULL`
- `solver_result JSONB NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`

Indexes on `(conversation_id, created_at)`, `game_type`, and a normalized
concept key if verified game reuse is introduced.

### `game_attempts` (MVP optional)

- `id UUID PRIMARY KEY`
- `game_id UUID NOT NULL REFERENCES games(id)`
- `conversation_id UUID NOT NULL REFERENCES conversations(id)`
- `input JSONB NOT NULL`
- `result JSONB NOT NULL`
- `succeeded BOOLEAN NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

### LangGraph checkpoints

Use the supported PostgreSQL checkpointer and its own tables. Do not mix
checkpoint records into application-domain tables. Use the conversation UUID
as `thread_id` and the run UUID as additional metadata where supported.

## 11. Frontend Application Flow

### Initial load

1. Load or create a conversation.
2. Fetch its messages and games.
3. Restore an active run if one exists.
4. Show the latest ready game or the forge empty state.

### Submission

1. Validate and normalize input in the browser.
2. Optimistically add the user message.
3. POST the message.
4. If clarification is returned, display it and focus the input.
5. If a run starts, show the staged loader and subscribe to SSE.
6. On `game.ready`, fetch the canonical game record.
7. Render it through the registry.
8. On failure, show a recoverable error and retry/regenerate action.

### Game state

Each renderer uses an explicit state machine:

```text
ready -> playing -> success
               └-> miss -> playing
ready/playing -> paused (when applicable)
```

The renderer must clean up animation frames and timers on unmount.

## 12. Solver and Verification Strategy

Every mechanic must ship with:

1. A typed schema.
2. A backend solver.
3. A frontend simulation implementation or shared test vectors.
4. Valid parameter bounds.
5. Canonical winning and losing cases.
6. Property or boundary tests where appropriate.

For projectile motion, define and version:

- coordinate system;
- launch point;
- time step;
- thrust/speed conversion;
- gravity scaling;
- termination bounds; and
- target tolerance.

Generate a fixture set from the backend and replay it in frontend tests. This
detects formula drift without requiring Python code in the browser.

## 13. Security and Reliability

- Keep all model credentials server-side.
- Validate request length and reject control characters/markup-like input.
- Enforce Pydantic schemas on every model response.
- Apply per-IP or per-session rate limits to generation endpoints.
- Add model and workflow timeouts.
- Bound all repair loops.
- Use request IDs and structured logging.
- Make run creation idempotent where practical.
- Prevent two active generation runs for the same conversation unless the
  product explicitly supports it.
- Use database transactions when finalizing a run and creating a game.
- Return safe fallbacks only when they satisfy the same validation and solver
  requirements.
- Configure CORS narrowly by environment.
- Never expose chain-of-thought, internal prompts, or provider payloads.

Removing arbitrary generated HTML eliminates the largest browser security risk.

## 14. Testing Strategy

### Backend unit tests

- Schema acceptance and rejection
- Workflow routing
- Clarification behavior
- Solver correctness and boundaries
- Repair loop limits
- Preset verification
- Repository behavior
- Error mapping

### Backend integration tests

- FastAPI with a temporary PostgreSQL database
- Conversation and message persistence
- Checkpoint restoration across application instances
- Successful generation finalization
- Provider timeout and invalid structured output
- Concurrent-run protection
- SSE reconnect behavior

### Frontend tests

- API client and error handling
- Forge form behavior
- Clarification flow
- Progress event reducer
- Renderer registry and unsupported versions
- Per-renderer state transitions
- Keyboard and reduced-motion behavior
- Refresh restoration

### Contract tests

- Generate frontend types from OpenAPI or validate checked-in types in CI.
- Maintain one valid and several invalid fixtures for every game type.
- Replay backend solver fixtures against frontend simulations.

### Visual tests

Use Playwright screenshots for:

- Forge empty, loading, clarification, failure, and ready states
- Every game renderer in ready, miss, and success states
- Desktop, tablet, and mobile widths
- Light/default theme
- Reduced-motion mode where meaningful

The approved screenshots become the enforceable style guideline.

### End-to-end scenarios

1. Create conversation, submit concept, answer clarification, play game.
2. Refresh during generation and restore progress.
3. Refresh after completion and restore the game.
4. Fail a game attempt, receive a hint, then succeed.
5. Regenerate a game while preserving conversation history.
6. Handle model failure without losing user input.

## 15. Delivery Phases

### Phase 0: Contract and visual baseline

- Capture reference screenshots from the demo.
- Extract design tokens and component inventory.
- Approve `GameSpec` base fields and the first mechanic subtype.
- Freeze the projectile physics contract and canonical demo values.

**Exit criteria:** one approved GameSpec fixture and desktop/mobile visual
references exist.

### Phase 1: Project foundation

- Scaffold React, Vite, and TypeScript in `frontend/`.
- Add FastAPI application factory.
- Add PostgreSQL configuration and connection lifecycle.
- Add migrations and Docker Compose.
- Add health/readiness endpoints.
- Add unified local development instructions.

**Exit criteria:** frontend and backend run locally; readiness confirms the
database connection; CI can run both test suites.

### Phase 2: Game contract and projectile vertical slice

- Implement canonical Pydantic schemas.
- Implement TypeScript contract generation/checking.
- Implement backend projectile solver.
- Port the trusted projectile renderer from the demo.
- Build the shared game shell and core design tokens.
- Verify canonical winning and losing inputs in both runtimes.

**Exit criteria:** a static fixture from FastAPI renders as a polished,
playable, solver-consistent React game.

### Phase 3: Persistence and conversation APIs

- Add conversations, messages, runs, and games tables.
- Add repositories and transaction boundaries.
- Implement conversation and message endpoints.
- Implement game retrieval endpoints.
- Replace SQLite with PostgreSQL LangGraph checkpointing.

**Exit criteria:** conversations and fixture games survive process restarts.

### Phase 4: Structured LangGraph generation

- Refactor CLI setup out of the workflow service.
- Replace the HTML generator node with the game designer node.
- Add schema validation, solver, reviewer, and repair nodes.
- Persist workflow progress and final verified games.
- Preserve a deterministic preset mode for tests/local development.

**Exit criteria:** a prompt produces a stored, verified projectile GameSpec
without generating HTML.

### Phase 5: Async run experience

- Implement run status endpoints and SSE.
- Publish versioned workflow progress events.
- Add reconnect and refresh recovery.
- Add cancellation if the workflow execution model supports safe cancellation.
- Build staged React loading and error states.

**Exit criteria:** the UI remains responsive during generation and restores an
active run after refresh.

### Phase 6: Demo UI parity

- Port the demo header, forge bar, lesson panel, game card, badges, controls,
  success overlay, and responsive rules into reusable components.
- Remove fake product behavior or clearly mark placeholders.
- Complete accessibility and keyboard review.
- Establish Playwright visual baselines.

**Exit criteria:** approved desktop and mobile screenshots closely match the
demo while using the new API flow.

### Phase 7: Additional mechanics

Add mechanics one at a time using the full checklist: schema, solver,
renderer, fixtures, unit tests, visual tests, and prompt examples.

Recommended order:

1. Falling object
2. Balance/torque
3. Momentum/collision
4. Fraction grouping
5. Graph matching

**Exit criteria:** each mechanic is independently solver-verified and visually
approved before the next begins.

### Phase 8: Hardening and deployment

- Add production logging, request IDs, rate limiting, and timeouts.
- Run database migration and rollback checks.
- Add frontend/backend production builds.
- Add deployment configuration and environment documentation.
- Run load, failure-recovery, accessibility, and full E2E checks.

**Exit criteria:** production checklist passes and a clean environment can be
deployed from the documented instructions.

## 16. Definition of Done

The rebuild is complete when:

- the CLI workflow is available through FastAPI;
- SQLite is no longer the web runtime checkpoint store;
- PostgreSQL restores conversations, messages, runs, and games;
- the model returns structured GameSpecs rather than HTML;
- every playable game is schema-valid and solver-verified;
- React renders all games through trusted versioned components;
- the UI follows the demo design system at desktop and mobile sizes;
- generation progress survives reconnects and refreshes;
- secrets and raw provider errors never reach the frontend;
- unit, integration, contract, E2E, accessibility, and visual tests pass; and
- setup and deployment are documented from a clean checkout.

## 17. Fine-Tuning Decision

Do not fine-tune for the initial rebuild. First enforce quality through:

- structured model output;
- strict Pydantic schemas;
- enumerated scenes and mechanics;
- deterministic validation and solvers;
- curated prompt examples;
- trusted React renderers; and
- visual regression tests.

Collect rejected and corrected GameSpecs during real use. Revisit fine-tuning
only when there is a sufficiently large, reviewed dataset and a measured
failure pattern that prompt/schema improvements do not solve. Fine-tuning may
improve mechanic selection and educational content, but it will not replace
the React design system.

## 18. First Implementation Slice

The first implementation PR should be deliberately small:

1. Add frontend and FastAPI foundations.
2. Add PostgreSQL migrations and readiness checks.
3. Define `GameSpecV1` and `ProjectileTargetGameSpec`.
4. Serve one verified projectile fixture from FastAPI.
5. Render it in the React PhysicsForge game shell.
6. Add backend solver tests, frontend interaction tests, and two visual
   screenshots.

This proves the architecture before modifying the LangGraph workflow or adding
more game mechanics.
