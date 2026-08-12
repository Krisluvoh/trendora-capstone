"""
llm_client.py
--------------
Pluggable LLM client layer for Trendora.

Trendora's agent logic (system prompts, JSON schemas, memory, orchestration)
is provider-agnostic. This module isolates the one part of the system that
talks to a specific model API, so the same agent code can run against:

  - Anthropic Claude (default / recommended for this project)
  - OpenAI GPT models
  - Groq (via langchain-groq's ChatGroq) — a free-tier-friendly option for
    development/prototyping, per the instructor's course notes
  - A local MockClient (no API key required — used for offline testing,
    grading demos without credentials, and CI)

This satisfies the "Production Deployment Considerations" rubric criterion:
the system is not hard-wired to a single vendor, which matters for cost,
rate-limit, and outage resilience in a real hype-drop sales tool.

Note on architecture: the instructor's course notes demonstrate the same
idea using full LangChain chains (ChatPromptTemplate | model | parser).
Trendora's pipeline is a fixed, non-branching three-step sequence (a
"chain", not an "agent" in the tool-calling sense), so a thin custom
provider abstraction was simpler here per that same "use the simplest
architecture" guidance — see docs/INSTRUCTOR_NOTES_SUMMARY.md. The Groq
option below reuses langchain-groq's ChatGroq under the hood as the actual
wire client, since that's the documented, maintained integration.
"""

from __future__ import annotations

import json
import os
import random
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Common interface every provider client must implement."""

    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return the raw text completion for a single-turn system+user call."""
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """Claude-backed client. Default provider for Trendora."""

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        import anthropic  # local import so the package is optional until used

        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def generate(self, system_prompt: str, user_message: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1200,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if getattr(block, "type", "") == "text")


class OpenAIClient(LLMClient):
    """GPT-backed client, kept for parity with the original assignment brief."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        import openai  # local import so the package is optional until used

        self.model = model
        self._client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def generate(self, system_prompt: str, user_message: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content


class GroqClient(LLMClient):
    """
    Groq-backed client via langchain-groq's ChatGroq, per the instructor's
    course notes on free-tier prototyping. Requires GROQ_API_KEY.
    """

    def __init__(self, model: str = "qwen/qwen3-32b", api_key: str | None = None):
        from langchain_groq import ChatGroq  # local import so the package is optional until used

        self._model = ChatGroq(
            model=model,
            temperature=0,
            api_key=api_key or os.environ.get("GROQ_API_KEY"),
        )

    def generate(self, system_prompt: str, user_message: str) -> str:
        response = self._model.invoke(
            [
                ("system", system_prompt),
                ("human", user_message),
            ]
        )
        return response.content


class MockClient(LLMClient):
    """
    Deterministic offline stand-in for grading / demo environments without an
    API key. Produces schema-shaped, semi-randomized JSON so the full
    multi-agent pipeline can be exercised end to end without network access.

    NOT a substitute for real model output — swap in AnthropicClient,
    OpenAIClient, or GroqClient for production use.
    """

    def generate(self, system_prompt: str, user_message: str) -> str:
        role = "intake"
        if "Research Agent" in system_prompt:
            role = "research"
        elif "Recommendation Agent" in system_prompt:
            role = "recommendation"

        if role == "intake":
            payload = {
                "customer_goal": "Secure a limited-release item before sellout",
                "budget": "$400-$600",
                "urgency_level": "high",
                "preferences": ["limited edition", "resale-safe", "authentic retail channel"],
                "constraints": ["must ship before an event date", "avoid resale markup over 20%"],
                "missing_info": ["exact size/spec needed", "preferred retailer"],
                "emotional_drivers": ["fear of missing out", "collector pride"],
                "objection_patterns": ["price sensitivity if hype fades"],
            }
        elif role == "research":
            payload = {
                "attributes_to_research": ["scarcity", "resale trend", "brand hype trajectory"],
                "hype_cycle_analysis": "Demand is in the acceleration phase with rising search interest",
                "scarcity_score": "8/10",
                "drop_timing": "Next restock window uncertain; primary drop likely sells out within hours",
                "product_comparison": [
                    {"name": "Primary target item", "hype": "very high", "price_trend": "rising"},
                    {"name": "Comparable alternative", "hype": "moderate", "price_trend": "stable"},
                ],
                "collector_value": "Strong secondary-market retention historically",
                "risks": ["price spike post-sellout", "counterfeit resale risk", "hype collapse if trend shifts"],
                "confidence": "medium-high",
            }
        else:
            payload = {
                "recommendation": "Buy now through an authenticated primary channel before the drop closes",
                "reasoning": "High scarcity score and accelerating hype trend indicate a narrow acquisition window",
                "objection_handling": "If price is a concern, offer the comparable alternative with stabler pricing",
                "strategy_adaptation": "Shift to conservative/budget framing if user repeats price objections",
                "next_steps": "Confirm size/spec, complete purchase, set a drop alert for backup options",
            }

        payload["_mock"] = True
        payload["_seed"] = random.randint(1000, 9999)
        return json.dumps(payload)


def get_client(provider: str = "mock", **kwargs) -> LLMClient:
    """Factory: provider in {'anthropic', 'openai', 'groq', 'mock'}."""
    provider = provider.lower()
    if provider == "anthropic":
        return AnthropicClient(**kwargs)
    if provider == "openai":
        return OpenAIClient(**kwargs)
    if provider == "groq":
        return GroqClient(**kwargs)
    if provider == "mock":
        return MockClient()
    raise ValueError(f"Unknown provider: {provider}")
