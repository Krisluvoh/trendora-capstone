"""
orchestrator.py
----------------
Coordinates the three Trendora agents into a single pipeline run and keeps
TrendoraMemory in sync between them. This is the "system" in "multi-agent
system" — each agent only ever sees its own role's system prompt; the
orchestrator is what stitches their outputs together.

In the instructor's chain-vs-agent framing: this is a "chain" (a fixed,
orchestrator-defined sequence), not a model-driven agent-with-tools —
appropriate since Trendora's workflow doesn't need dynamic tool selection.
"""

from __future__ import annotations

import json
import os

from agents.intake_agent import IntakeAgent
from agents.recommendation_agent import RecommendationAgent
from agents.research_agent import ResearchAgent
from llm_client import LLMClient
from memory import TrendoraMemory


class TrendoraOrchestrator:
    """
    Runs one customer's session through all three agents in order and keeps
    a single TrendoraMemory in sync as each agent's output comes back. One
    instance = one customer's conversation; the memory and transcript below
    both accumulate across every run_scenario/handle_objection call made on
    the same instance.
    """

    def __init__(self, client: LLMClient, memory: TrendoraMemory | None = None):
        self.client = client
        self.memory = memory or TrendoraMemory()
        self.intake_agent = IntakeAgent(client)
        self.research_agent = ResearchAgent(client)
        self.recommendation_agent = RecommendationAgent(client)
        self.transcript: list[dict] = []

    def _log(self, agent: str, input_payload: dict, output_payload: dict) -> None:
        self.transcript.append({"agent": agent, "input": input_payload, "output": output_payload})

    def run_scenario(self, user_message: str, product_name: str) -> dict:
        """
        Runs one full Intake -> Research -> Recommendation pass for a single
        customer message about a single product, updating self.memory at each
        step along the way. Returns the three agents' structured outputs
        (self.memory itself is not part of the return value, but reflects the
        same updates and can be inspected or saved separately).
        """
        intake_input = {"user_message": user_message, "product_name": product_name}
        intake_output = self.intake_agent.run(self.memory, intake_input)
        self.memory.update_from_intake(intake_output)
        self._log("intake", intake_input, intake_output)

        research_input = {
            "product_name": product_name,
            "intake_summary": intake_output,
        }
        research_output = self.research_agent.run(self.memory, research_input)
        self.memory.update_from_research(product_name, research_output)
        self._log("research", research_input, research_output)

        recommendation_input = {
            "product_name": product_name,
            "intake_summary": intake_output,
            "research_summary": research_output,
        }
        recommendation_output = self.recommendation_agent.run(self.memory, recommendation_input)
        self.memory.update_from_recommendation(recommendation_output)
        self._log("recommendation", recommendation_input, recommendation_output)

        return {
            "product_name": product_name,
            "intake": intake_output,
            "research": research_output,
            "recommendation": recommendation_output,
        }

    def handle_objection(self, product_name: str, objection_text: str) -> dict:
        """
        Follow-up turn: user pushes back after a recommendation. Routes straight
        to the Recommendation Agent (objection handling is its job), with the
        objection recorded to memory first so strategy_adaptation reflects it.
        """
        self.memory.register_user_objection(objection_text)

        recommendation_input = {
            "product_name": product_name,
            "user_objection": objection_text,
            "instruction": "The customer has raised a new objection. Adapt strategy accordingly.",
        }
        recommendation_output = self.recommendation_agent.run(self.memory, recommendation_input)
        self.memory.update_from_recommendation(recommendation_output)
        self._log("recommendation_followup", recommendation_input, recommendation_output)
        return recommendation_output

    def save_transcript(self, path: str) -> None:
        """Writes every agent turn logged so far (via _log) to a JSON file."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.transcript, f, indent=2)
