# CAP 931 — Instructor Course Notes (Raw)

*Saved verbatim (formatting cleaned up for Markdown) from the instructor's
class channel, for project reference. Author: Alexandros Karales, Technical
Instructor, Per Scholas. These are teaching examples/building blocks, not
a completed capstone, and not the assignment spec — see `ASSIGNMENT_BRIEF.md`
for that.*

## Homework framing

> Focus on building something that works first. Get your agents
> communicating. Get the workflow running. Test it with real examples. Then
> improve the prompts, code structure, and output. A simple working
> multi-agent prototype is much more valuable than an overly complicated
> system that never gets finished.

## Part 1 — Python patterns for multi-agent capstones

Key ideas demonstrated:
- One agent = one function = one responsibility.
- Pass information between agents via plain Python dicts.
- Give each agent a name/role/goal (even before adding an LLM).
- A simple `Agent` class can standardize agent structure.
- Chain small functions into a workflow: intake → research → recommendation.
- Keep prompt-building in dedicated functions, separate from orchestration.
- Prefer structured (dict/object) agent output over free text.
- Add basic error handling (e.g. `try/except KeyError` for missing fields).
- Test each agent individually before wiring the full workflow.

Suggested structure:
```
capstone_project/
├── main.py
├── agents/
│   ├── sales_agent.py
│   ├── research_agent.py
│   └── recommendation_agent.py
├── prompts/
│   └── prompts.py
├── tests/
│   └── test_agents.py
└── README.md
```

Suggested build order: one working agent → second agent → pass data between
them → third agent only if it serves a clear purpose → test each agent
individually → connect into a workflow → add LLM/API integration → improve
prompts → add error handling → clean up structure.

## Part 2 — LangChain

Core idea: LangChain provides abstractions connecting
`Prompt → Model → Output`, and later `User → Agent → Tools → Other
Agents/Chains → Final Response`. It does not design the application for
you — the workflow design is still the developer's job.

Demonstrated pattern:
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-5-mini", temperature=0)

sales_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sales assistant. Understand the customer's needs. Do not recommend a product yet."),
    ("human", "Customer request:\n{customer_request}\n\nIdentify:\n1. Customer goal\n2. Budget\n3. Important requirements\n4. Missing information"),
])

sales_chain = sales_prompt | model | StrOutputParser()

result = sales_chain.invoke({"customer_request": "I need a laptop for Python programming under $1,000."})
```

Chaining multiple specialized components (sales → research →
recommendation), each with its own prompt and clear role boundary, with one
component's output becoming the next component's input.

Structured output via Pydantic:
```python
from pydantic import BaseModel, Field

class CustomerNeeds(BaseModel):
    budget: int | None = Field(description="Customer budget in dollars")
    use_case: str = Field(description="Primary use for the product")
    priority: str = Field(description="Most important customer priority")

structured_model = model.with_structured_output(CustomerNeeds)
```

Tools and agents:
- A **tool** is a Python function the model can call (`@tool` decorator).
- An **agent** is an LLM-powered component that decides which tool/action
  to invoke, versus a **chain**, where the developer defines the fixed
  sequence.
- Not every agent needs every tool — scope tools to each agent's actual
  responsibility.

Suggested structure adds `prompts/`, `tools/`, `models/schemas.py`,
`tests/` alongside `agents/`.

## Part 3 — LangChain + Groq

Groq is presented as a free-tier-friendly provider for learning/prototyping,
integrated via `langchain-groq` / `ChatGroq`, documented as a near drop-in
replacement for `ChatOpenAI`:

```python
from langchain_groq import ChatGroq

model = ChatGroq(model="qwen/qwen3-32b", temperature=0)
```

Everything else (prompt templates, chains, structured output, tools,
agents) stays the same — only the model provider changes. This is called
out as the core lesson: **separate what your application does from which
model provider it uses.**

Caution noted: Groq's free tier has rate limits; avoid unbounded retry
loops (`while True: model.invoke(...)`).

Suggested testing order: test model directly → add prompt template → add
parser → build one chain → add a second component → pass structured data →
add tools → experiment with an agent → add error handling → organize into
files.

## Big-picture takeaway (instructor's framing)

> A simple system that works and that you can explain is better than a
> complicated system you cannot explain.
