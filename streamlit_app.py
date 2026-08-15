"""
streamlit_app.py
-----------------
Streamlit front end for Trendora, built for deployment on Streamlit
Community Cloud (free, and — unlike Hugging Face Spaces' free tier —
supports running real server-side Python with proper secrets management).

Wraps TrendoraOrchestrator in a small chat-style UI, styled as a quiet
boutique concierge rather than a generic form. Streamlit reruns this whole
script on every interaction, so the orchestrator + memory for the current
browser session live in st.session_state rather than as local variables.

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

try:
    if "GROQ_API_KEY" in st.secrets and not os.environ.get("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:  # noqa: BLE001 - no secrets.toml locally is expected, not an error
    pass


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Jost:wght@300;400;500&display=swap');

:root {
    --tr-gold: #C6A15B;
    --tr-gold-soft: rgba(198, 161, 91, 0.35);
    --tr-ink: #ECE7DA;
    --tr-muted: #9B9587;
    --tr-panel: #17171A;
    --tr-bg: #0E0E10;
}

html, body, [class*="css"] { font-family: 'Jost', sans-serif; }

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    max-width: 760px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}

.tr-hero { text-align: center; margin-bottom: 2.5rem; }
.tr-hero .tr-mark {
    font-family: 'Cormorant Garamond', serif;
    font-size: 3rem;
    font-weight: 500;
    letter-spacing: 0.35em;
    color: var(--tr-ink);
    margin: 0;
    text-transform: uppercase;
}
.tr-hero .tr-rule {
    width: 64px;
    height: 1px;
    background: var(--tr-gold);
    margin: 0.9rem auto;
    border: none;
}
.tr-hero .tr-tagline {
    font-family: 'Jost', sans-serif;
    font-size: 0.78rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--tr-muted);
    margin: 0;
}
.tr-hero .tr-provider {
    font-size: 0.7rem;
    color: var(--tr-muted);
    margin-top: 0.6rem;
    letter-spacing: 0.08em;
}
.tr-hero .tr-provider b { color: var(--tr-gold); font-weight: 500; }

div[data-testid="stForm"] {
    background: var(--tr-panel);
    border: 1px solid var(--tr-gold-soft);
    border-radius: 2px;
    padding: 2rem 2rem 1.4rem 2rem;
}

label[data-testid="stWidgetLabel"] p {
    font-family: 'Jost', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--tr-muted);
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: var(--tr-bg);
    border: 1px solid rgba(198, 161, 91, 0.25);
    border-radius: 2px;
    color: var(--tr-ink);
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: var(--tr-gold);
    box-shadow: none;
}

div[data-testid="stFormSubmitButton"] button,
div[data-testid="stBaseButton-primary"] button {
    width: 100%;
    background: transparent;
    color: var(--tr-gold);
    border: 1px solid var(--tr-gold);
    border-radius: 2px;
    font-family: 'Jost', sans-serif;
    font-size: 0.76rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    padding: 0.6rem 0;
    transition: background 0.2s ease, color 0.2s ease;
}
div[data-testid="stFormSubmitButton"] button:hover {
    background: var(--tr-gold);
    color: var(--tr-bg);
}

.tr-panel {
    border: 1px solid rgba(198, 161, 91, 0.2);
    border-top: 2px solid var(--tr-gold);
    background: var(--tr-panel);
    padding: 1.6rem 1.8rem;
    margin-top: 1.6rem;
    border-radius: 2px;
}
.tr-panel .tr-label {
    font-family: 'Jost', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--tr-gold);
    margin-bottom: 0.9rem;
}
.tr-panel .tr-row { margin-bottom: 0.55rem; font-size: 0.95rem; line-height: 1.5; }
.tr-panel .tr-row:last-child { margin-bottom: 0; }
.tr-panel .tr-row .tr-key {
    color: var(--tr-muted);
    font-size: 0.78rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-right: 0.4rem;
}
.tr-panel.tr-recommendation { border-top-color: var(--tr-gold); }
.tr-panel .tr-verdict {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 1.3rem;
    color: var(--tr-ink);
    margin-bottom: 0.8rem;
}

div[data-testid="stAlertContainer"] {
    background: rgba(198, 161, 91, 0.08) !important;
    border: 1px solid var(--tr-gold-soft) !important;
    border-radius: 2px !important;
}
div[data-testid="stAlertContainer"] p {
    color: var(--tr-ink) !important;
    font-family: 'Jost', sans-serif;
    font-size: 0.88rem;
}
div[data-testid="stAlertContainer"] svg { fill: var(--tr-gold) !important; }

.tr-divider {
    text-align: center;
    color: var(--tr-gold-soft);
    letter-spacing: 0.5em;
    margin: 2.4rem 0 1.6rem 0;
    font-size: 0.8rem;
}
</style>
"""


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


def _panel(label: str, rows: list[tuple[str, str]], extra_class: str = "") -> str:
    body = "".join(
        f'<div class="tr-row"><span class="tr-key">{key}</span>{value}</div>' for key, value in rows if value
    )
    return f'<div class="tr-panel {extra_class}"><div class="tr-label">{label}</div>{body}</div>'


def _render_result(result: dict) -> None:
    intake, research, rec = result["intake"], result["research"], result["recommendation"]

    st.markdown(
        _panel(
            "Client Intake",
            [
                ("Goal", intake.get("customer_goal")),
                ("Budget", intake.get("budget")),
                ("Urgency", intake.get("urgency_level")),
                ("Emotional drivers", ", ".join(intake.get("emotional_drivers") or []) or "—"),
            ],
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        _panel(
            "Market Research",
            [
                ("Hype cycle", research.get("hype_cycle_analysis")),
                ("Scarcity score", research.get("scarcity_score")),
                ("Drop timing", research.get("drop_timing")),
                ("Risks", ", ".join(research.get("risks") or []) or "—"),
            ],
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="tr-panel tr-recommendation"><div class="tr-label">Concierge Recommendation</div>'
        f'<div class="tr-verdict">"{rec.get("recommendation")}"</div>'
        + "".join(
            f'<div class="tr-row"><span class="tr-key">{key}</span>{value}</div>'
            for key, value in [
                ("Reasoning", rec.get("reasoning")),
                ("Next steps", rec.get("next_steps")),
            ]
            if value
        )
        + "</div>",
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Trendora — Sales Concierge", page_icon="💎", layout="centered")
st.markdown(THEME_CSS, unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="tr-hero">
        <p class="tr-mark">Trendora</p>
        <hr class="tr-rule" />
        <p class="tr-tagline">Private Concierge for Limited-Release Acquisitions</p>
        <p class="tr-provider">Advised by <b>{PROVIDER}</b></p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
    st.session_state.product_name = None
    st.session_state.result = None
    st.session_state.warning = None
    st.session_state.followup = None

with st.form("intake_form"):
    product_name = st.text_input("Item of Interest", placeholder="e.g. Aurora X1 Limited Sneaker Drop")
    user_message = st.text_area(
        "Tell Us What You're After",
        placeholder=(
            "e.g. I need these before Friday, budget around $400, "
            "it's for my collection not resale."
        ),
    )
    submitted = st.form_submit_button("Consult Trendora")

if submitted:
    if not product_name.strip() or not user_message.strip():
        st.warning("Enter both an item and a message first.")
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

    st.markdown('<div class="tr-divider">• • •</div>', unsafe_allow_html=True)
    with st.form("objection_form"):
        objection_text = st.text_input(
            "Have a Reservation?",
            placeholder="e.g. That feels like a lot to spend on shoes I'd only wear a few times.",
        )
        objection_submitted = st.form_submit_button("Share Your Concern")

    if objection_submitted:
        if not objection_text.strip():
            st.warning("Enter a concern first.")
        else:
            followup = st.session_state.orchestrator.handle_objection(
                st.session_state.product_name, objection_text
            )
            st.session_state.followup = followup

    if st.session_state.followup:
        f = st.session_state.followup
        st.markdown(
            f'<div class="tr-panel tr-recommendation"><div class="tr-label">Revised Counsel</div>'
            f'<div class="tr-verdict">"{f.get("recommendation")}"</div>'
            + "".join(
                f'<div class="tr-row"><span class="tr-key">{key}</span>{value}</div>'
                for key, value in [
                    ("Addressing your concern", f.get("objection_handling")),
                    ("Approach going forward", f.get("strategy_adaptation")),
                    ("Next steps", f.get("next_steps")),
                ]
                if value
            )
            + "</div>",
            unsafe_allow_html=True,
        )
