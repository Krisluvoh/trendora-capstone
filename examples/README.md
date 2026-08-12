# Sample Run Output

Committed example output from `uv run main.py` using the built-in
`MockClient` (provider=`mock`, the default), so graders can see the
pipeline's output shape without needing an API key.

- `transcript_user_00N.json` — full Intake → Research → Recommendation
  transcript (plus objection follow-up where applicable) for each of the
  three demo scenarios in `main.py`.
- `memory_user_00N.json` — the persisted `TrendoraMemory` snapshot for
  that customer after the run.

These are illustrative fixture outputs from `MockClient`, not real model
reasoning — run with `TRENDORA_PROVIDER=anthropic` (or `openai`/`groq`) and
a real API key to see actual LLM-generated output. See the root `README.md`
for instructions.
