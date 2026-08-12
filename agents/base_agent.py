"""
agents/base_agent.py
---------------------
Shared machinery for every Trendora agent:
  - injects memory context into the prompt
  - forces strict JSON-only output
  - parses + validates the response against a pydantic schema
  - retries once on malformed JSON (LLMs occasionally wrap JSON in prose
    or code fences despite instructions — handle it rather than crash)
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError

from llm_client import LLMClient
from memory import TrendoraMemory


class AgentError(RuntimeError):
    """Raised when an agent cannot produce valid structured output after retries."""


class BaseAgent:
    role_name: str = "BaseAgent"
    system_prompt: str = ""
    output_schema: type[BaseModel] | None = None

    def __init__(self, client: LLMClient):
        self.client = client

    def build_user_message(self, memory: TrendoraMemory, turn_input: dict) -> str:
        return (
            "MEMORY CONTEXT (JSON):\n"
            f"{memory.as_context_string()}\n\n"
            "NEW INPUT FOR THIS TURN (JSON):\n"
            f"{json.dumps(turn_input, indent=2)}\n\n"
            "Return ONLY the JSON object specified in your instructions. "
            "No prose, no markdown fences, no commentary."
        )

    @staticmethod
    def _extract_json(raw: str) -> dict:
        text = raw.strip()
        # Strip ```json ... ``` fences if the model added them anyway.
        fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1)
        else:
            brace_match = re.search(r"\{.*\}", text, re.DOTALL)
            if brace_match:
                text = brace_match.group(0)
        return json.loads(text)

    def run(self, memory: TrendoraMemory, turn_input: dict) -> dict:
        user_message = self.build_user_message(memory, turn_input)

        last_error: Exception | None = None
        for _attempt in range(2):
            raw = self.client.generate(self.system_prompt, user_message)
            try:
                parsed = self._extract_json(raw)
                if self.output_schema is not None:
                    validated = self.output_schema(**parsed)
                    return validated.model_dump()
                return parsed
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                user_message += (
                    "\n\nYour previous response was not valid JSON matching the "
                    "required schema. Return ONLY a single valid JSON object, "
                    "with no other text."
                )
        raise AgentError(f"{self.role_name} failed to produce valid JSON after retries: {last_error}")
