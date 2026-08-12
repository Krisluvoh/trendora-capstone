# Instructor Notes — Multi-Agent Patterns, LangChain, Groq, and uv

*(Course-channel notes from the CAP 931 instructor, Alexandros Karales,
saved for reference alongside the capstone deliverable. These are teaching
examples/building blocks, not the assignment spec itself — see
`ASSIGNMENT_BRIEF.md` for that.)*

## How this shaped Trendora's design

1. **One agent, one responsibility** — mirrored by Trendora's strict
   Intake / Research / Recommendation role separation, enforced in each
   agent's system prompt.
2. **Pass structured data between agents, not prose** — mirrored by
   `schemas.py` (pydantic-validated JSON contracts) instead of passing raw
   strings between agents.
3. **Separate the model provider from the application architecture** — the
   notes show the same LangChain chain working unchanged across
   `ChatOpenAI` and `ChatGroq`. Trendora achieves the equivalent with its
   own lightweight `llm_client.py` abstraction (`AnthropicClient` /
   `OpenAIClient` / `GroqClient` / `MockClient`), without requiring the
   full LangChain runtime as a hard dependency for the core pipeline (Groq
   is wired through `langchain-groq`'s `ChatGroq`, since that's the
   documented, maintained integration for that provider).
4. **Test each agent individually before wiring the full workflow** — see
   `tests/`, which exercises each agent in isolation against the
   `MockClient` so a broken component fails fast and identifiably, plus an
   integration test (`test_orchestrator.py`) for the full chain.
5. **Build small, then connect** — the notes' suggested order (one model
   call → one prompt template → one chain → pass data → add structure →
   add tools/agents only when needed) matches how this project is staged:
   working single-agent call → three agents wired with dict/JSON handoff →
   memory layer → provider abstraction → tests → docs.
6. **Use `uv` for project/dependency management** — this project was
   initialized with `uv init`, dependencies added with `uv add`
   (`anthropic`, `openai`, `langchain-groq`, `pydantic`, `python-dotenv`,
   plus `pytest` as a dev dependency), and is run with `uv run main.py` /
   `uv run pytest`. `pyproject.toml` + `uv.lock` replace a hand-written
   `requirements.txt` and pin the full dependency graph reproducibly.

## Why Trendora uses direct Anthropic/OpenAI SDK calls instead of full LangChain chains

The instructor's notes are explicit that **LangChain is optional tooling,
not a requirement** — "LangChain does not magically design your
application. You still need to design the workflow," and "Use the simplest
architecture that solves the problem."

Trendora's core pipeline is a fixed, three-step sequence (no dynamic
tool-selection or agent-driven branching), so direct SDK calls per agent
plus a thin custom provider abstraction were the simpler choice for this
project's actual requirements, per that same guidance. The `langchain-groq`
package is used specifically for the Groq provider (there's no first-party
Groq SDK as lightweight as Anthropic's/OpenAI's), which is itself a small
example of using the right tool for one job rather than adopting a whole
framework everywhere. The LangChain `ChatPromptTemplate | model | parser`
pattern from the notes would be a straightforward drop-in replacement for
the rest of `llm_client.py` if the project later needs LangChain-specific
tooling (its agent/tool-calling layer, retrievers, memory integrations) —
the prompts and schemas defined in `agents/` and `schemas.py` would not
need to change to make that swap.

## Reference: patterns from the notes

- **Chain vs. Agent** — a *chain* follows a sequence you define; an *agent*
  lets the model decide which tool/action to invoke next. Trendora's
  Intake → Research → Recommendation flow is a **chain**
  (orchestrator-defined sequence, see `orchestrator.py`), not an
  agent-with-tools pattern, matching the "use the simplest architecture"
  guidance since no dynamic tool selection is required.
- **Structured output over free text** — the notes' `CustomerNeeds`
  pydantic example is the same pattern as Trendora's `IntakeOutput`,
  `ResearchOutput`, and `RecommendationOutput` models in `schemas.py`.
- **Provider swap** — the notes swap `ChatOpenAI` for `ChatGroq` with
  almost no other code changes. `llm_client.py`'s `get_client(provider=...)`
  factory is the same idea applied to this project's client layer, with a
  fourth `mock` option for offline testing/grading.
- **Suggested project structure** (`agents/`, `prompts/`, `tools/`,
  `models/`, `tests/`) — Trendora's actual structure (`agents/`,
  `schemas.py`, `memory.py`, `llm_client.py`, `tests/`) is a direct
  adaptation of this, with prompts kept inline in each agent module rather
  than a separate `prompts/` package since each agent has exactly one
  prompt, and no separate `tools/` package since this pipeline doesn't use
  tool-calling.

The full original notes (Python patterns, LangChain examples, Groq
integration examples) are preserved in `docs/instructor_notes_raw.md` for
reference.
