"""
streamlit_app.py
-----------------
Streamlit front end for Trendora, built for deployment on Streamlit
Community Cloud (free, and — unlike Hugging Face Spaces' free tier —
supports running real server-side Python with proper secrets management).

Wraps TrendoraOrchestrator in a small chat-style UI. Streamlit reruns this
whole script on every interaction, so the orchestrator + memory for the
current browser session live in st.session_state rather than as local
variables.

Provider defaults to Groq (free tier) via TRENDORA_PROVIDER / GROQ_API_KEY.
On Streamlit Cloud, set GROQ_API_KEY in the app's Settings -> Secrets; it's
read from st.secrets there. Locally, it falls back to a .env file. Falls
back to the mock client if no key is configured, so the app still loads
and is explorable without one.
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from llm_client import get_client
from memory import TrendoraMemory
from orchestrator import TrendoraOrchestrator

load_dotenv()

PROVIDER = os.environ.get("TRENDORA_PROVIDER", "groq")

if "GROQ_API_KEY" in st.secrets and not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]


def _build_orchestrator() -> tuple[TrendoraOrchestrator, str | None]:
    """Returns (orchestrator, warning). Falls back to mock if the provider errors out."""
    try:
        client = get_client(PROVIDER)
        return TrendoraOrchestrator(client, TrendoraMemory(customer_id="web_guest")), None
    except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
        client = get_client("mock")
        warning = (
            f"Could not start the '{PROVIDER}' provider ({exc}). "
            "Falling back to mock responses — set GROQ_API_KEY in this app's secrets to use a real model."
        )
        return TrendoraOrchestrator(client, TrendoraMemory(customer_id="web_guest")), warning


def _render_result(result: dict) -> None:
    intake, research, rec = result["intake"], result["research"], result["recommendation"]

    st.markdown("#### Intake")
    st.markdown(
        f"- **Goal:** {intake.get('customer_goal')}\n"
        f"- **Budget:** {intake.get('budget')}\n"
        f"- **Urgency:** {intake.get('urgency_level')}\n"
        f"- **Emotional drivers:** {', '.join(intake.get('emotional_drivers') or []) or '—'}"
    )

    st.markdown("#### Research")
    st.markdown(
        f"- **Hype cycle:** {research.get('hype_cycle_analysis')}\n"
        f"- **Scarcity score:** {research.get('scarcity_score')}\n"
        f"- **Drop timing:** {research.get('drop_timing')}\n"
        f"- **Risks:** {', '.join(research.get('risks') or []) or '—'}"
    )

    st.markdown("#### Recommendation")
    st.markdown(
        f"- **Call:** {rec.get('recommendation')}\n"
        f"- **Reasoning:** {rec.get('reasoning')}\n"
        f"- **Next steps:** {rec.get('next_steps')}"
    )


st.set_page_config(page_title="Trendora — Sales Concierge", page_icon="🛍️")
st.title("Trendora")
st.caption(
    "A three-agent sales concierge for hype-cycle products (limited drops, "
    f"boutique exclusives, viral gadgets). Running on **{PROVIDER}**."
)

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
    st.session_state.product_name = None
    st.session_state.result = None
    st.session_state.warning = None
    st.session_state.followup = None

with st.form("intake_form"):
    product_name = st.text_input("Product", placeholder="e.g. Aurora X1 Limited Sneaker Drop")
    user_message = st.text_area(
        "Your message",
        placeholder=(
            "e.g. I need these before Friday, budget around $400, "
            "it's for my collection not resale."
        ),
    )
    submitted = st.form_submit_button("Ask Trendora", type="primary")

if submitted:
    if not product_name.strip() or not user_message.strip():
        st.warning("Enter both a product name and a message first.")
    else:
        orchestrator, warning = _build_orchestrator()
        result = orchestrator.run_scenario(user_message, product_name)
        st.session_state.orchestrator = orchestrator
        st.session_state.product_name = product_name
        st.session_state.result = result
        st.session_state.warning = warning
        st.session_state.followup = None

if st.session_state.warning:
    st.warning(st.session_state.warning)

if st.session_state.result:
    _render_result(st.session_state.result)

    st.markdown("---")
    with st.form("objection_form"):
        objection_text = st.text_input(
            "Got a pushback? (optional follow-up)",
            placeholder="e.g. That feels like a lot to spend on shoes I'd only wear a few times.",
        )
        objection_submitted = st.form_submit_button("Send objection")

    if objection_submitted:
        if not objection_text.strip():
            st.warning("Enter an objection first.")
        else:
            followup = st.session_state.orchestrator.handle_objection(
                st.session_state.product_name, objection_text
            )
            st.session_state.followup = followup

    if st.session_state.followup:
        f = st.session_state.followup
        st.markdown("#### Updated recommendation (after objection)")
        st.markdown(
            f"- **Call:** {f.get('recommendation')}\n"
            f"- **Objection handling:** {f.get('objection_handling')}\n"
            f"- **Strategy adaptation:** {f.get('strategy_adaptation')}\n"
            f"- **Next steps:** {f.get('next_steps')}"
        )
