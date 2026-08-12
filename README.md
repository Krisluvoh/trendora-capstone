# Trendora — Multi-Agent Sales Concierge (CAP 931 Capstone)

Trendora is a three-agent, memory-backed sales concierge prototype for
high-demand, limited-release "hype-cycle" products (limited sneaker drops,
boutique luxury exclusives, viral seasonal gadgets). Built for the Per
Scholas CAP 931 capstone brief ("Build a Sales Agent Prototype Using
Multi-Agent GPT Models"), implemented primarily against Claude, with
OpenAI and Groq kept as swappable alternative providers.

Project setup and dependency management use **[uv](https://docs.astral.sh/uv/)**.

## 1. Quick start

```bash
uv sync                 # installs everything from pyproject.toml / uv.lock
uv run main.py           # runs the 3-scenario demo — no API key needed (MockClient)
uv run pytest -q         # runs the full test suite — also no API key needed
```

To run against a real model, copy `.env.example` to `.env`, fill in the key(s)
you want to use, and set `TRENDORA_PROVIDER`:

```bash
cp .env.example .env
# edit .env: set TRENDORA_PROVIDER=anthropic and ANTHROPIC_API_KEY=sk-ant-...
uv run main.py
```

Supported providers: `anthropic` (default recommendation), `openai`, `groq`, `mock`.

## 2. Architecture

```
pyproject.toml / uv.lock   uv-managed dependencies
main.py                    demo entry point / scenario runner
orchestrator.py             wires the three agents together, manages memory
memory.py                   TrendoraMemory: cross-turn contextual memory
schemas.py                   pydantic schemas — one per agent's required JSON shape
llm_client.py                 pluggable model backend: Anthropic / OpenAI / Groq / Mock
agents/
  base_agent.py                shared prompt-building, JSON parsing, retry, validation
  intake_agent.py               Agent 1 — goals, budget, urgency, emotional drivers
  research_agent.py             Agent 2 — hype/scarcity analysis, alternatives, risk
  recommendation_agent.py       Agent 3 — final call, objection handling, next steps
tests/
  test_llm_client.py            provider factory + mock output shape
  test_memory.py                memory update hooks, dedup, persistence
  test_agents.py                each agent in isolation, role-boundary checks
  test_orchestrator.py          full pipeline + objection-handling integration tests
docs/
  ASSIGNMENT_BRIEF.md            original capstone assignment, transcribed
  INSTRUCTOR_NOTES_SUMMARY.md    how the instructor's patterns map onto this build
  instructor_notes_raw.md        full instructor course notes, for reference
```

Each agent:
- Has its own system prompt and stays inside its own role (enforced in the prompt text and unit-tested in `tests/test_agents.py`).
- Returns **only** a JSON object matching a fixed schema (`schemas.py`).
- Is validated with pydantic before its output is trusted by the orchestrator or the next agent.
- Reads and writes to a shared `TrendoraMemory` object, so later turns can reference what Intake or Research said earlier.

The orchestrator is the only piece that knows about all three agents — no
agent calls another agent directly, matching the "never perform another
agent's role" requirement. In the instructor's chain-vs-agent framing, this
is a **chain** (a fixed, orchestrator-defined sequence), not a model-driven
agent-with-tools — appropriate since the workflow doesn't need dynamic tool
selection.

## 3. Inputs

Each scenario run takes:
- `user_message` — free-text customer message (goal, budget, urgency, mood)
- `product_name` — the hype-cycle item in question

Optional follow-up turns take a `user_objection` string and route directly
to the Recommendation Agent, since objection handling is explicitly its
responsibility.

## 4. LLM Model Selection & Use

Default: **Claude** (`claude-sonnet-4-6`) via the `anthropic` SDK — chosen
for strong structured-JSON adherence and instruction-following on a fixed,
non-negotiable schema, which is the main technical risk in this project (a
stray sentence outside the JSON object breaks the pipeline).

Alternate providers, selectable via `TRENDORA_PROVIDER`:
- `openai` — GPT-4o-mini by default, via the `openai` SDK.
- `groq` — Qwen3-32B by default, via `langchain-groq`'s `ChatGroq`, per the
  instructor's notes on free-tier prototyping.
- `mock` — deterministic offline fixture data; default, so `uv run main.py`
  and `uv run pytest` work with zero setup.

## 5. Outputs

Every agent turn produces the exact JSON object specified for that role,
plus an `evaluation` block:

```json
{
  "evaluation": {
    "relevance": "0-10",
    "clarity": "0-10",
    "engagement": "0-10",
    "deal_likelihood": "0-10"
  }
}
```

Full run transcripts (all three agents' input/output for every scenario) are
saved to `output/transcript_<customer_id>.json`, and persistent customer
memory is saved to `output/memory_<customer_id>.json` (both git-ignored,
generated at runtime).

## 6. Optional Enhancements (enabled)

| Enhancement | Where it lives |
|---|---|
| Hype prediction | `hype_cycle_analysis` field, Research Agent |
| Scarcity forecasting | `scarcity_score`, `drop_timing`, Research Agent |
| Drop alerts | surfaced in Recommendation Agent `next_steps` |
| Risk scoring | `risks` + `confidence`, Research Agent |
| Emotional alignment | `emotional_drivers`, Intake Agent |
| Strategy switching | `strategy_adaptation`, Recommendation Agent, driven by `past_objections` in memory |

## 7. Guardrails (a deliberate design choice, not in the original brief)

The Recommendation Agent's system prompt explicitly instructs it **not** to
pressure a customer who has raised a genuine price or risk objection, and to
offer a real "wait" or "alternative" path when warranted. A sales agent that
always says "buy now" regardless of stated hesitation is a weaker, less
trustworthy product — this was a deliberate product decision, worth calling
out in a capstone writeup as an example of product judgment beyond just
following the spec literally.

## 8. Testing

```bash
uv run pytest -q
```

24 tests covering: provider factory behavior, memory update/dedup/persistence
logic, each agent in isolation (schema validation + role-boundary checks —
no agent's output should contain another role's fields), and full-pipeline
integration (all three agents run in sequence, memory updates correctly,
objection follow-ups route to the right agent). All tests run against
`MockClient`, so the suite is free and requires no network access — matching
the instructor's "test each agent individually" guidance.

## 9. Time & Duration

Built to the assignment's 2-day scope:
- Day 1: architecture, schemas, memory model, agent prompts, mock client, pipeline wiring.
- Day 2: real-provider integration (Anthropic/OpenAI/Groq), `uv`-based project setup, test suite, three end-to-end scenarios, objection-handling follow-up turns, documentation.

## 10. Challenges & Solutions

| Challenge | Solution |
|---|---|
| LLMs sometimes wrap JSON in prose or code fences despite instructions | `BaseAgent._extract_json` strips fences/prose and retries once with a corrective message before failing loudly |
| Agents drifting into another agent's role over a long conversation | Each system prompt states its role boundary twice; unit-tested directly in `tests/test_agents.py` (asserts no cross-role fields leak) |
| Memory growing unbounded over many turns | `as_context_string()` caps injected product history to the last 5 entries; covered by `test_memory.py` |
| Testing/demoing without burning API credits or requiring a key | `MockClient` produces schema-valid fixture JSON for offline runs and the entire test suite |
| Risk of the "hype/urgency" framing tipping into manipulative sales pressure | Recommendation Agent prompt explicitly forbids pressuring a customer past a stated objection and requires a genuine wait/alternative option when warranted |
| Wanting reproducible, pinned dependencies instead of a loose `requirements.txt` | Switched project setup to `uv init` / `uv add`, producing `pyproject.toml` + a fully pinned `uv.lock` |

## 11. Production Deployment Considerations

- **Provider portability**: swap Anthropic/OpenAI/Groq/mock via one factory call or an environment variable.
- **Schema enforcement**: pydantic validation catches drift before it reaches a user or the next agent.
- **Persistent memory**: JSON-file memory here is a placeholder for a real customer datastore (e.g., a managed database) in production.
- **Retry/backoff**: current retry is a single corrective re-prompt; production would add exponential backoff and rate-limit handling on the client classes.
- **Observability**: transcripts are saved per customer; production would pipe these to structured logging for the eval metrics as a monitoring signal.
- **Cost control**: mock/dev mode already separated from paid inference, so CI, tests, and grading don't consume API quota.
- **Reproducible environments**: `uv.lock` pins the exact dependency graph, so `uv sync` reproduces the same environment anywhere.
