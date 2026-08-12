"""
schemas.py
----------
Pydantic models that define and enforce the exact JSON contract for each
agent (this is the "models/schemas.py" file from the instructor's suggested
project layout). Agent output is parsed against these models before it is
handed to the next agent or returned to the caller — if a model call drifts
from the required shape, validation fails loudly instead of silently
passing bad data down the pipeline.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Evaluation(BaseModel):
    relevance: int = Field(ge=0, le=10)
    clarity: int = Field(ge=0, le=10)
    engagement: int = Field(ge=0, le=10)
    deal_likelihood: int = Field(ge=0, le=10)


class IntakeOutput(BaseModel):
    customer_goal: str = ""
    budget: str = ""
    urgency_level: str = ""
    preferences: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    emotional_drivers: list[str] = Field(default_factory=list)
    objection_patterns: list[str] = Field(default_factory=list)
    evaluation: Evaluation | None = None


class ResearchOutput(BaseModel):
    attributes_to_research: list[str] = Field(default_factory=list)
    hype_cycle_analysis: str = ""
    scarcity_score: str = ""
    drop_timing: str = ""
    product_comparison: list[Any] = Field(default_factory=list)
    collector_value: str = ""
    risks: list[str] = Field(default_factory=list)
    confidence: str = ""
    evaluation: Evaluation | None = None


class RecommendationOutput(BaseModel):
    recommendation: str = ""
    reasoning: str = ""
    objection_handling: str = ""
    strategy_adaptation: str = ""
    next_steps: str = ""
    evaluation: Evaluation | None = None


SCHEMAS = {
    "intake": IntakeOutput,
    "research": ResearchOutput,
    "recommendation": RecommendationOutput,
}
