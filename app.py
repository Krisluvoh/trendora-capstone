"""
app.py
------
Gradio front end for Trendora, built for deployment on Hugging Face Spaces.

Wraps TrendoraOrchestrator in a small chat-style UI so the three-agent
pipeline (Intake -> Research -> Recommendation) is reachable from a browser
instead of only from the command line. Each browser session gets its own
in-memory TrendoraMemory + orchestrator via gr.State, so a session's
objection follow-ups and later questions still have context from earlier
in that same session.

Provider defaults to Groq (free tier) via TRENDORA_PROVIDER / GROQ_API_KEY,
set as a Space secret. Falls back to the mock client if no key is
configured, so the Space still loads and is explorable without one.
"""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv

from llm_client import get_client
from memory import TrendoraMemory
from orchestrator import TrendoraOrchestrator

load_dotenv()

PROVIDER = os.environ.get("TRENDORA_PROVIDER", "groq")


def _build_orchestrator() -> tuple[TrendoraOrchestrator, str | None]:
    """Returns (orchestrator, warning). Falls back to mock if the provider errors out."""
    try:
        client = get_client(PROVIDER)
        return TrendoraOrchestrator(client, TrendoraMemory(customer_id="web_guest")), None
    except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
        client = get_client("mock")
        warning = (
            f"Could not start the '{PROVIDER}' provider ({exc}). "
            "Falling back to mock responses — set an API key in this Space's secrets to use a real model."
        )
        return TrendoraOrchestrator(client, TrendoraMemory(customer_id="web_guest")), warning


def _format_result(result: dict) -> str:
    intake = result["intake"]
    research = result["research"]
    rec = result["recommendation"]
    return (
        f"### Intake\n"
        f"- **Goal:** {intake.get('customer_goal')}\n"
        f"- **Budget:** {intake.get('budget')}\n"
        f"- **Urgency:** {intake.get('urgency_level')}\n"
        f"- **Emotional drivers:** {', '.join(intake.get('emotional_drivers') or []) or '—'}\n\n"
        f"### Research\n"
        f"- **Hype cycle:** {research.get('hype_cycle_analysis')}\n"
        f"- **Scarcity score:** {research.get('scarcity_score')}\n"
        f"- **Drop timing:** {research.get('drop_timing')}\n"
        f"- **Risks:** {', '.join(research.get('risks') or []) or '—'}\n\n"
        f"### Recommendation\n"
        f"- **Call:** {rec.get('recommendation')}\n"
        f"- **Reasoning:** {rec.get('reasoning')}\n"
        f"- **Next steps:** {rec.get('next_steps')}\n"
    )


def start_conversation(product_name: str, user_message: str, orchestrator_state):
    if not product_name.strip() or not user_message.strip():
        return "Enter both a product name and a message first.", orchestrator_state, gr.update(visible=False)

    orchestrator, warning = orchestrator_state if orchestrator_state else _build_orchestrator()
    result = orchestrator.run_scenario(user_message, product_name)
    orchestrator.memory.customer_profile["current_product"] = product_name

    output = _format_result(result)
    if warning:
        output = f"> ⚠️ {warning}\n\n" + output

    return output, (orchestrator, product_name), gr.update(visible=True)


def raise_objection(objection_text: str, orchestrator_state):
    if not orchestrator_state:
        return "Start a conversation above first.", orchestrator_state
    orchestrator, product_name = orchestrator_state
    if not objection_text.strip():
        return "Enter an objection first.", orchestrator_state

    followup = orchestrator.handle_objection(product_name, objection_text)
    text = (
        f"### Updated recommendation (after objection)\n"
        f"- **Call:** {followup.get('recommendation')}\n"
        f"- **Objection handling:** {followup.get('objection_handling')}\n"
        f"- **Strategy adaptation:** {followup.get('strategy_adaptation')}\n"
        f"- **Next steps:** {followup.get('next_steps')}\n"
    )
    return text, (orchestrator, product_name)


with gr.Blocks(title="Trendora — Sales Concierge") as demo:
    gr.Markdown(
        "# Trendora\n"
        "A three-agent sales concierge for hype-cycle products (limited drops, "
        "boutique exclusives, viral gadgets). Describe what you're after, and "
        "Intake, Research, and Recommendation agents run in sequence.\n\n"
        f"Running on **{PROVIDER}**."
    )

    orchestrator_state = gr.State(None)

    with gr.Row():
        product_input = gr.Textbox(label="Product", placeholder="e.g. Aurora X1 Limited Sneaker Drop")
    with gr.Row():
        message_input = gr.Textbox(
            label="Your message",
            placeholder="e.g. I need these before Friday, budget around $400, it's for my collection not resale.",
            lines=3,
        )
    start_btn = gr.Button("Ask Trendora", variant="primary")
    result_box = gr.Markdown()

    with gr.Group(visible=False) as objection_group:
        objection_input = gr.Textbox(
            label="Got a pushback? (optional follow-up)",
            placeholder="e.g. That feels like a lot to spend on shoes I'd only wear a few times.",
        )
        objection_btn = gr.Button("Send objection")
        objection_box = gr.Markdown()

    start_btn.click(
        start_conversation,
        inputs=[product_input, message_input, orchestrator_state],
        outputs=[result_box, orchestrator_state, objection_group],
    )
    objection_btn.click(
        raise_objection,
        inputs=[objection_input, orchestrator_state],
        outputs=[objection_box, orchestrator_state],
    )

if __name__ == "__main__":
    demo.launch()
