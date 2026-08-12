"""Tests for the provider abstraction layer (mock client + factory)."""

import json

import pytest

from llm_client import MockClient, get_client


def test_mock_client_intake_shape():
    client = MockClient()
    raw = client.generate("You are the Intake Agent...", "some input")
    data = json.loads(raw)
    assert "customer_goal" in data
    assert "emotional_drivers" in data


def test_mock_client_research_shape():
    client = MockClient()
    raw = client.generate("You are the Research Agent...", "some input")
    data = json.loads(raw)
    assert "scarcity_score" in data
    assert "risks" in data


def test_mock_client_recommendation_shape():
    client = MockClient()
    raw = client.generate("You are the Recommendation Agent...", "some input")
    data = json.loads(raw)
    assert "recommendation" in data
    assert "next_steps" in data


def test_get_client_factory_mock():
    client = get_client("mock")
    assert isinstance(client, MockClient)


def test_get_client_factory_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_client("not-a-real-provider")
