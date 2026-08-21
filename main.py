"""
main.py
-------
Demo entry point. Runs three representative Trendora scenarios end to end
(Intake -> Research -> Recommendation, plus one objection-handling turn),
printing each agent's structured JSON output and saving a full transcript.

Usage (with uv):
    uv run main.py                                   # MockClient, no API key needed
    TRENDORA_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... uv run main.py
    TRENDORA_PROVIDER=openai OPENAI_API_KEY=sk-... uv run main.py
    TRENDORA_PROVIDER=groq GROQ_API_KEY=gsk-... uv run main.py
"""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv

from llm_client import get_client
from memory import TrendoraMemory
from orchestrator import TrendoraOrchestrator

load_dotenv()

SCENARIOS = [
    {
        "customer_id": "user_001",
        "product_name": "Aurora X1 Limited Sneaker Drop",
        "user_message": (
            "I need to get the Aurora X1 sneakers before they sell out this "
            "Friday. My budget is around $300-$400. I've missed the last two "
            "drops and I really don't want to miss this one — it's for my "
            "collection, not resale."
        ),
        "follow_up_objection": (
            "Honestly $400 feels like a lot for shoes I might only wear a few "
            "times. Is there a cheaper way to still get something similar?"
        ),
    },
    {
        "customer_id": "user_002",
        "product_name": "Chronos Meridian Steel Watch (Boutique Exclusive)",
        "user_message": (
            "Looking for a gift for my partner's birthday next month — "
            "something in the luxury watch space that feels exclusive. "
            "Budget up to $2,500. I don't know much about watch brands or "
            "which models are actually hard to get right now."
        ),
        "follow_up_objection": None,
    },
    {
        "customer_id": "user_003",
        "product_name": "Nimbus Mini Portable Espresso Kit",
        "user_message": (
            "Everyone on social media is obsessed with this portable espresso "
            "gadget right now. I don't want to overpay for a fad that dies in "
            "two months. Budget is flexible but I'm skeptical it's worth it."
        ),
        "follow_up_objection": (
            "I'm still not convinced this isn't just hype that fades. Why "
            "should I buy now instead of waiting to see if it's still popular "
            "in a few months?"
        ),
    },
]


def run_all(provider: str = "mock") -> None:
    """Runs every scenario in SCENARIOS through the full pipeline, printing and saving each one."""
    client = get_client(provider)
    os.makedirs("output", exist_ok=True)

    for scenario in SCENARIOS:
        print("=" * 80)
        print(f"SCENARIO: {scenario['product_name']}  (customer: {scenario['customer_id']})")
        print("=" * 80)

        memory_path = f"output/memory_{scenario['customer_id']}.json"
        memory = TrendoraMemory.load(memory_path, customer_id=scenario["customer_id"])
        orchestrator = TrendoraOrchestrator(client, memory)

        result = orchestrator.run_scenario(scenario["user_message"], scenario["product_name"])

        print("\n--- INTAKE AGENT OUTPUT ---")
        print(json.dumps(result["intake"], indent=2))
        print("\n--- RESEARCH AGENT OUTPUT ---")
        print(json.dumps(result["research"], indent=2))
        print("\n--- RECOMMENDATION AGENT OUTPUT ---")
        print(json.dumps(result["recommendation"], indent=2))

        if scenario["follow_up_objection"]:
            print("\n--- CUSTOMER OBJECTION FOLLOW-UP ---")
            followup = orchestrator.handle_objection(
                scenario["product_name"], scenario["follow_up_objection"]
            )
            print(json.dumps(followup, indent=2))

        orchestrator.memory.save(memory_path)
        orchestrator.save_transcript(f"output/transcript_{scenario['customer_id']}.json")
        print(f"\nMemory saved to {memory_path}")
        print(f"Transcript saved to output/transcript_{scenario['customer_id']}.json\n")


if __name__ == "__main__":
    run_all(provider=os.environ.get("TRENDORA_PROVIDER", "mock"))
