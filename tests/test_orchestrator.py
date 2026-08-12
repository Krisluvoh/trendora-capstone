"""
Integration test for the full Intake -> Research -> Recommendation pipeline,
plus the objection-handling follow-up path, using the MockClient.
"""

from llm_client import MockClient
from memory import TrendoraMemory
from orchestrator import TrendoraOrchestrator


def test_full_pipeline_produces_all_three_outputs():
    orchestrator = TrendoraOrchestrator(MockClient(), TrendoraMemory())
    result = orchestrator.run_scenario(
        user_message="I need the Aurora X1 before Friday, budget $400",
        product_name="Aurora X1",
    )
    assert set(result.keys()) == {
        "product_name",
        "intake",
        "research",
        "recommendation",
    }
    assert result["intake"]["customer_goal"]
    assert result["research"]["scarcity_score"]
    assert result["recommendation"]["recommendation"]


def test_memory_updated_after_full_pipeline_run():
    orchestrator = TrendoraOrchestrator(MockClient(), TrendoraMemory())
    orchestrator.run_scenario(user_message="test request", product_name="Test Product")
    assert orchestrator.memory.customer_profile.get("customer_goal")
    assert len(orchestrator.memory.product_interest_history) == 1
    assert "Test Product" in orchestrator.memory.hype_cycle_context


def test_transcript_logs_all_three_agent_turns():
    orchestrator = TrendoraOrchestrator(MockClient(), TrendoraMemory())
    orchestrator.run_scenario(user_message="test", product_name="Test Product")
    agents_logged = [entry["agent"] for entry in orchestrator.transcript]
    assert agents_logged == ["intake", "research", "recommendation"]


def test_objection_followup_routes_to_recommendation_only():
    orchestrator = TrendoraOrchestrator(MockClient(), TrendoraMemory())
    orchestrator.run_scenario(user_message="test", product_name="Test Product")
    followup = orchestrator.handle_objection("Test Product", "too expensive for me")
    assert "recommendation" in followup
    assert "too expensive for me" in orchestrator.memory.past_objections
    assert orchestrator.transcript[-1]["agent"] == "recommendation_followup"


def test_pipeline_runs_with_pre_existing_memory():
    memory = TrendoraMemory(customer_id="returning_user")
    memory.register_user_objection("burned by a past price spike")
    orchestrator = TrendoraOrchestrator(MockClient(), memory)
    result = orchestrator.run_scenario(user_message="test", product_name="Test Product")
    assert result["recommendation"]["recommendation"]
    assert "burned by a past price spike" in orchestrator.memory.past_objections
