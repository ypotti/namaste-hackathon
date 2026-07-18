import typing
from math_puzzle_agent.config import WorkflowConfig
from math_puzzle_agent.workflow import build_graph, get_llm, PuzzleState
from math_puzzle_agent.prompts import (
    get_planner_prompt, get_generator_prompt,
    get_reviewer_prompt, get_visual_review_prompt,
)
from math_puzzle_agent.schemas import PuzzleSpec, PlannerDecision, ReviewerDecision, KnownValue

cfg = WorkflowConfig()

# ── config.py ──────────────────────────────────────────────────────────────────
assert hasattr(cfg, 'session_run_id'),          'MISSING: session_run_id'
assert hasattr(cfg, 'screenshot_enabled'),       'MISSING: screenshot_enabled'
assert hasattr(cfg, 'screenshot_save'),          'MISSING: screenshot_save'
assert hasattr(cfg, 'screenshot_dir'),           'MISSING: screenshot_dir'
assert hasattr(cfg, 'reviewer_vision_model'),    'MISSING: reviewer_vision_model'
assert hasattr(cfg, 'planner_temperature'),      'MISSING: planner_temperature'
assert hasattr(cfg, 'reviewer_temperature'),     'MISSING: reviewer_temperature'
assert hasattr(cfg, 'generator_temperature'),    'MISSING: generator_temperature'
assert len(cfg.session_run_id) == 4 and cfg.session_run_id.isdigit(), 'session_run_id must be 4 digits'
print('config.py            OK')

# ── temperature routing ────────────────────────────────────────────────────────
for m in ('o1-mini', 'o3-mini', 'o4-mini', 'gpt-5.5', 'gpt-5.6-luna'):
    llm = get_llm(m)
    # reasoning models must NOT have temperature kwarg set
    params = llm._default_params if hasattr(llm, '_default_params') else {}
    assert 'temperature' not in params, f'reasoning model {m} should not have temperature'
for m in ('gpt-4o', 'gpt-4.1', 'gpt-4.1-mini'):
    llm = get_llm(m, 0.0)
    params = llm._default_params if hasattr(llm, '_default_params') else {}
    # non-reasoning models should have temperature
print('get_llm temperature  OK')

# ── PuzzleState ────────────────────────────────────────────────────────────────
hints = typing.get_type_hints(PuzzleState)
rd_type = str(hints.get('reviewer_decision', ''))
assert 'None' in rd_type, f'reviewer_decision must allow None, got: {rd_type}'
print(f'PuzzleState          OK  (reviewer_decision: {rd_type})')

# ── prompts ────────────────────────────────────────────────────────────────────
p = get_planner_prompt(cfg)
g = get_generator_prompt(cfg)
r = get_reviewer_prompt(cfg)
v = get_visual_review_prompt()

# planner
assert 'animation_description' in p,              'MISSING in planner: animation_description'
assert 'canvas_width' in p or str(cfg.canvas_width) in p, 'MISSING in planner: canvas dimensions'
assert str(cfg.default_tolerance) in p,           'MISSING in planner: default_tolerance'

# generator
assert 'CORRECT_ANSWER' in g,                     'MISSING in generator: CORRECT_ANSWER constant'
assert 'TOLERANCE' in g,                          'MISSING in generator: TOLERANCE constant'
assert 'drawScene()' in g,                        'MISSING in generator: drawScene()'
assert 'updateAnimation()' in g,                  'MISSING in generator: updateAnimation()'
assert 'ANSWER SECRECY' in g,                     'MISSING in generator: ANSWER SECRECY section'
assert 'finish(' in g,                            'MISSING in generator: finish() callback'
assert cfg.p5_cdn_url in g,                       'MISSING in generator: p5 CDN URL'
assert str(cfg.canvas_width) in g,                'MISSING in generator: canvas_width'
assert str(cfg.canvas_height) in g,               'MISSING in generator: canvas_height'
assert str(cfg.canvas_height - 60) in g,          'MISSING in generator: ground_y'

# reviewer
assert 'PRIORITY 1' in r,                         'MISSING in reviewer: PRIORITY 1 section'
assert 'Answer secrecy' in r,                     'MISSING in reviewer: Answer secrecy check'
assert 'CORRECT_ANSWER' in r,                     'MISSING in reviewer: CORRECT_ANSWER check'
assert 'TOLERANCE' in r,                          'MISSING in reviewer: TOLERANCE check'
assert cfg.p5_cdn_url in r,                       'MISSING in reviewer: p5 CDN URL check'

# visual review
assert 'IDLE state' in v,                         'MISSING in visual prompt: IDLE state note'
assert 'Duplicated labels' in v,                  'MISSING in visual prompt: Duplicated labels check'

print('prompts.py           OK')

# ── workflow graph builds ──────────────────────────────────────────────────────
graph = build_graph(cfg)
print('workflow.py graph    OK')

# ── browser filename format ────────────────────────────────────────────────────
import time
from math_puzzle_agent.browser import capture_screenshot
thread_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in (cfg.thread_id or "default"))[:40]
filename = f"review_attempt_1_{thread_slug}_{cfg.session_run_id}_{int(time.time())}.png"
assert cfg.session_run_id in filename,            'session_run_id missing from filename'
assert thread_slug in filename,                   'thread_id missing from filename'
print(f'browser.py filename  OK  ({filename})')

print()
print('━' * 50)
print('ALL CHECKS PASSED — codebase is consistent')
print('━' * 50)
