# LangChain Math Puzzle Agent

This is a production-style, multi-turn LangGraph application for generating a single interactive p5.js math-puzzle page from a chat.

The user chats with a single agent interface. Internally, the agent orchestrates a multi-agent LangGraph workflow featuring a Planner, Generator, and Reviewer loop.

```mermaid
graph TD
    Start([START]) --> Planner[Planner Agent]
    Planner --> RoutePlanning{route_after_planning}
    
    RoutePlanning -- "status == 'needs_more_info'" --> AskUser[Ask User]
    AskUser --> End([END])
    
    RoutePlanning -- "status == 'ready'" --> Generator[Generator Agent]
    Generator --> Reviewer[Reviewer Agent]
    Reviewer --> RouteReview{route_after_review}
    
    RouteReview -- "approved == false AND attempts < 3" --> Generator
    RouteReview -- "approved == true OR attempts >= 3" --> WriteFile[Write File & Finish]
    WriteFile --> End
```

### Flow Architecture & Core Nodes

1. **Planner Node (`planner`)**:
   - Acts as the initial coordinator. Inspects conversation history and determines if there are enough details to define the math puzzle.
   - Outputs a structured `PlannerDecision` containing:
     - `status`: Either `"needs_more_info"` or `"ready"`.
     - `next_question`: Clarification prompt for the user.
     - `puzzle_spec`: A validated `PuzzleSpec` defining the math properties, physics criteria, hint/solution text, and animation steps.
2. **Ask User Node (`ask_user`)**:
   - Presents the planner's clarification question to the user and pauses execution, waiting for the user's reply.
3. **Generator Node (`generator`)**:
   - Triggered once the planner's status is `"ready"`.
   - Synthesizes a standalone, interactive HTML/JS/CSS page using `p5.js` for canvas rendering.
   - If returning from a review cycle, receives the previous code draft and the reviewer's feedback to make target fixes.
4. **Reviewer Node (`reviewer`)**:
   - Inspects the generated HTML code against the `PuzzleSpec` and design rules.
   - Outputs a structured `ReviewerDecision` containing:
     - `approved`: Boolean flag.
     - `feedback`: Detailed issues found (e.g. animation logic errors, contrast violations, missing elements).
5. **Write File & Finish Node (`write_file_and_finish`)**:
   - Performed upon approval or after a fallback limit of `3` attempts to prevent infinite loops.
   - Saves the verified HTML code directly to `generated/math_puzzle.html` and provides the file link to the user.

Conversation state is persisted in `puzzle_agent.sqlite` using LangGraph's SQLite checkpointer. Re-running the CLI continues the same conversation when `PUZZLE_THREAD_ID` has the same value.

## Setup

```bash
cd "/Users/yaswanthpotti/Documents/Personal Work/langchain-math-puzzle-agent"
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
uv sync
uv run python -m math_puzzle_agent.cli
```

Use a different conversation by setting `PUZZLE_THREAD_ID` in `.env`. The generated one-file page is saved to `generated/math_puzzle.html`; open it in a browser to play the puzzle.

## Example chat

```text
You: Make a puzzle about a boy throwing a ball through a hoop.
Agent: How far away and how high is the hoop?

You: It is 8 metres away and 3 metres high. Use a launch speed of 12 m/s.
Agent: Your interactive puzzle is ready: .../generated/math_puzzle.html
```

## Test without an API key

```bash
uv run pytest
```

`OPENAI_MODEL` is configurable in `.env`; select a model available to your OpenAI account.
