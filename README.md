# Trendora — Multi-Agent Sales Concierge (CAP 931 Capstone)

Trendora is a sales concierge prototype for "hype-cycle" products — think
limited sneaker drops, boutique luxury exclusives, viral seasonal gadgets.
It uses three AI agents that each handle one part of the sales conversation,
and it remembers customers across turns so later messages can reference
what was said earlier.

This was built for the Per Scholas CAP 931 capstone assignment ("Build a
Sales Agent Prototype Using Multi-Agent GPT Models"). It runs on Claude by
default, with OpenAI and Groq available as drop-in alternatives.

Setup and dependencies are managed with **[uv](https://docs.astral.sh/uv/)**.

## 1. Quick start

```bash
uv sync                  # installs everything from pyproject.toml / uv.lock
uv run main.py            # runs the 3-scenario demo — no API key needed (uses a mock client)
uv run pytest -q          # runs the test suite — also no API key needed
```

To run it against a real model, copy `.env.example` to `.env`, add your
API key(s), and set which provider to use:

```bash
cp .env.example .env
# edit .env: set TRENDORA_PROVIDER=anthropic and ANTHROPIC_API_KEY=sk-ant-...
uv run main.py
```

Supported providers: `anthropic` (recommended default), `openai`, `groq`, `mock`.

## 2. How it's put together

```
pyproject.toml / uv.lock   uv-managed dependencies
main.py                    demo entry point / scenario runner
orchestrator.py            wires the three agents together, manages memory
memory.py                  TrendoraMemory: cross-turn contextual memory
schemas.py                 pydantic schemas — one per agent's required JSON shape
llm_client.py              pluggable model backend: Anthropic / OpenAI / Groq / Mock
agents/
  base_agent.py              shared prompt-building, JSON parsing, retry, validation
  intake_agent.py             Agent 1 — goals, budget, urgency, emotional drivers
  research_agent.py           Agent 2 — hype/scarcity analysis, alternatives, risk
  recommendation_agent.py     Agent 3 — final call, objection handling, next steps
tests/
  test_llm_client.py          provider factory + mock output shape
  test_memory.py              memory update hooks, dedup, persistence
  test_agents.py              each agent in isolation, role-boundary checks
  test_orchestrator.py        full pipeline + objection-handling integration tests
docs/
  ASSIGNMENT_BRIEF.md            original capstone assignment, transcribed
  INSTRUCTOR_NOTES_SUMMARY.md    how the instructor's guidance maps onto this build
  instructor_notes_raw.md        full instructor course notes, for reference
  Trendora_Capstone_Report.docx  formal capstone report, mapped to the grading rubric
examples/
  sample_run_output/             a committed mock run (transcripts + memory) so you can see output without running anything
```

Each agent sticks to its own lane: it has its own system prompt, only
returns JSON matching a fixed schema (see `schemas.py`), and that output
gets checked with pydantic before the orchestrator or the next agent trusts
it. All three agents read and write to a shared `TrendoraMemory` object, so
if Intake learns the customer's budget, Research and Recommendation can see
it too.

The orchestrator is the only piece of code that talks to all three agents —
no agent calls another agent directly. That was one of the assignment's
requirements (agents shouldn't perform each other's jobs). In the
instructor's terms, this makes it a **chain** rather than a model-driven
agent with tools: the sequence is fixed by the orchestrator, not decided by
the model, which fits fine since nothing here needs dynamic tool selection.

## 3. What it takes as input

Each scenario run needs:
- `user_message` — the customer's free-text message (their goal, budget, urgency, mood)
- `product_name` — the hype-cycle item they're asking about

You can also send a follow-up `user_objection` string, which routes
straight to the Recommendation Agent since handling objections is its job.

## 4. Which model, and why

By default this runs on **Claude** (`claude-sonnet-4-6`) through the
`anthropic` SDK. I picked Claude because it's reliably good at sticking to
a strict JSON schema — that's the biggest technical risk in this project,
since one stray sentence outside the JSON breaks the whole pipeline.

You can switch providers with `TRENDORA_PROVIDER`:
- `openai` — GPT-4o-mini by default, via the `openai` SDK.
- `groq` — Qwen3-32B by default, via `langchain-groq`'s `ChatGroq` (the
  instructor mentioned Groq's free tier as good for prototyping).
- `mock` — canned offline responses, no API calls at all. This is the
  default, so `uv run main.py` and `uv run pytest` both work out of the box
  with zero setup.

## 5. What it outputs

Every agent turn produces the JSON object for its role, plus a small
evaluation block scoring the response:

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

Full transcripts (every agent's input/output for each scenario) get saved
to `output/transcript_<customer_id>.json`, and each customer's memory gets
saved to `output/memory_<customer_id>.json`. Both are generated at runtime
and git-ignored.

## 6. Extra features beyond the baseline

| Feature | Where to find it |
|---|---|
| Hype prediction | `hype_cycle_analysis` field, Research Agent |
| Scarcity forecasting | `scarcity_score`, `drop_timing`, Research Agent |
| Drop alerts | shows up in Recommendation Agent's `next_steps` |
| Risk scoring | `risks` + `confidence`, Research Agent |
| Emotional alignment | `emotional_drivers`, Intake Agent |
| Strategy switching | `strategy_adaptation`, Recommendation Agent — adjusts based on `past_objections` in memory |

## 7. A guardrail I added on purpose

The assignment didn't ask for this, but I wanted the Recommendation Agent
to not be pushy. Its prompt tells it explicitly not to pressure a customer
who's raised a real price or risk concern, and to offer a genuine "wait" or
"try something else" option when that's the honest answer. An agent that
just says "buy now" no matter what the customer says isn't a very
trustworthy salesperson, so this felt worth building in even though it
wasn't spelled out in the brief.

## 8. Testing

```bash
uv run pytest -q
```

24 tests cover the provider factory, memory update/dedup/persistence,
each agent in isolation (schema validation, plus checks that no agent's
output leaks fields that belong to another role), and the full pipeline
end to end (all three agents running in sequence, memory updating
correctly, objection follow-ups routing to the right agent). Everything
runs against the mock client, so the whole suite is free and works without
internet access — which matches the instructor's advice to test each agent
individually.

## 9. Timeline

Built inside the assignment's 2-day window:
- Day 1: architecture, schemas, memory model, agent prompts, mock client, pipeline wiring.
- Day 2: hooking up real providers (Anthropic/OpenAI/Groq), setting up the project with `uv`, writing the test suite, three end-to-end scenarios, objection-handling follow-ups, and documentation.

## 10. Problems I ran into, and how I fixed them

| Problem | Fix |
|---|---|
| Models sometimes wrap JSON in prose or code fences even when told not to | `BaseAgent._extract_json` strips that out and retries once with a corrective message before giving up |
| Agents drifting into another agent's job over a longer conversation | Each system prompt states its role boundary twice, and `tests/test_agents.py` checks directly that no cross-role fields leak through |
| Memory growing without bound over many turns | `as_context_string()` only injects the last 5 product-history entries; covered by `test_memory.py` |
| Needing to test and demo without burning API credits or requiring a key | The mock client produces schema-valid fixture data for offline runs and the whole test suite |
| The "hype/urgency" angle risking real manipulative sales pressure | Recommendation Agent's prompt forbids pushing past a stated objection and requires offering a genuine alternative or "wait" path |
| Wanting pinned, reproducible dependencies instead of a loose `requirements.txt` | Switched to `uv init` / `uv add`, which gives you `pyproject.toml` plus a fully pinned `uv.lock` |

## 11. If this went to production

- **Swappable providers**: switching between Anthropic/OpenAI/Groq/mock is one factory call or one environment variable.
- **Schema enforcement**: pydantic catches any drift in the model's output before it reaches a user or the next agent.
- **Memory**: right now it's just JSON files — fine for a prototype, but a real deployment would use an actual customer database.
- **Retries**: currently one corrective re-prompt if the model messes up the JSON. Production would need real exponential backoff and rate-limit handling.
- **Observability**: transcripts are saved per customer already; in production these would feed into structured logging so the eval scores could actually be monitored.
- **Cost control**: mock mode is already fully separate from paid inference, so tests, CI, and grading never touch API quota.
- **Reproducibility**: `uv.lock` pins the exact dependency graph, so `uv sync` gives you the same environment anywhere.
