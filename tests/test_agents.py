"""
Unit tests for each agent in isolation, using the MockClient — per the
instructor's guidance: "test each piece separately... if your workflow
fails, you want to know which component caused the problem."

These run entirely offline (no API key / network required).
"""

import pytest

from agents.intake_agent import IntakeAgent
from agents.recommendation_agent import RecommendationAgent
from agents.research_agent import ResearchAgent
from llm_client import MockClient
from memory import TrendoraMemory


@pytest.fixture
def client():
    return MockClient()


@pytest.fixture
def memory():
    return TrendoraMemory()


def test_intake_agent_returns_validated_schema(client, memory):
    agent = IntakeAgent(client)
    result = agent.run(memory, {"user_message": "I need sneakers fast", "product_name": "Aurora X1"})
    assert isinstance(result["preferences"], list)
    assert isinstance(result["objection_patterns"], list)
    assert "customer_goal" in result


def test_intake_agent_never_leaks_other_role_fields(client, memory):
    agent = IntakeAgent(client)
    result = agent.run(memory, {"user_message": "test", "product_name": "test product"})
    # Recommendation-only fields should not appear in Intake output
    assert "recommendation" not in result
    assert "scarcity_score" not in result


def test_research_agent_returns_validated_schema(client, memory):
    agent = ResearchAgent(client)
    result = agent.run(memory, {"product_name": "Aurora X1", "intake_summary": {}})
    assert "scarcity_score" in result
    assert "risks" in result
    assert isinstance(result["risks"], list)


def test_research_agent_never_leaks_other_role_fields(client, memory):
    agent = ResearchAgent(client)
    result = agent.run(memory, {"product_name": "test", "intake_summary": {}})
    assert "recommendation" not in result
    assert "customer_goal" not in result


def test_recommendation_agent_returns_validated_schema(client, memory):
    agent = RecommendationAgent(client)
    result = agent.run(
        memory,
        {"product_name": "Aurora X1", "intake_summary": {}, "research_summary": {}},
    )
    assert "recommendation" in result
    assert "next_steps" in result
    assert "objection_handling" in result


def test_recommendation_agent_never_leaks_other_role_fields(client, memory):
    agent = RecommendationAgent(client)
    result = agent.run(memory, {"product_name": "test"})
    assert "scarcity_score" not in result
    assert "customer_goal" not in result


def test_evaluation_scores_are_within_bounds_when_present(client, memory):
    agent = IntakeAgent(client)
    result = agent.run(memory, {"user_message": "test", "product_name": "test"})
    if result.get("evaluation"):
        for score in result["evaluation"].values():
            assert 0 <= score <= 10
