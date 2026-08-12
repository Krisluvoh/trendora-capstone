"""Tests for TrendoraMemory: update hooks, persistence, context injection."""

import json
import os
import tempfile

from memory import TrendoraMemory


def test_update_from_intake_sets_profile_and_merges_lists():
    memory = TrendoraMemory()
    memory.update_from_intake(
        {
            "customer_goal": "buy sneakers",
            "budget": "$300-$400",
            "urgency_level": "high",
            "preferences": ["limited edition"],
            "objection_patterns": ["price sensitivity"],
        }
    )
    assert memory.customer_profile["customer_goal"] == "buy sneakers"
    assert "limited edition" in memory.past_preferences
    assert "price sensitivity" in memory.past_objections


def test_update_from_intake_does_not_duplicate_preferences():
    memory = TrendoraMemory()
    memory.update_from_intake({"preferences": ["limited edition"]})
    memory.update_from_intake({"preferences": ["limited edition", "authentic channel"]})
    assert memory.past_preferences.count("limited edition") == 1
    assert "authentic channel" in memory.past_preferences


def test_update_from_research_appends_product_history():
    memory = TrendoraMemory()
    memory.update_from_research("Aurora X1", {"scarcity_score": "8/10", "hype_cycle_analysis": "rising"})
    assert len(memory.product_interest_history) == 1
    assert memory.product_interest_history[0]["product"] == "Aurora X1"
    assert "Aurora X1" in memory.hype_cycle_context


def test_register_user_objection_is_deduplicated():
    memory = TrendoraMemory()
    memory.register_user_objection("too expensive")
    memory.register_user_objection("too expensive")
    assert memory.past_objections.count("too expensive") == 1


def test_as_context_string_caps_product_history_to_five():
    memory = TrendoraMemory()
    for i in range(8):
        memory.update_from_research(f"product_{i}", {"scarcity_score": "5/10"})
    context = json.loads(memory.as_context_string())
    assert len(context["product_interest_history"]) == 5
    # most recent 5 should be kept
    assert context["product_interest_history"][-1]["product"] == "product_7"


def test_save_and_load_round_trip():
    memory = TrendoraMemory(customer_id="user_test")
    memory.update_from_intake({"customer_goal": "gift for partner", "budget": "$2500"})

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "memory.json")
        memory.save(path)
        loaded = TrendoraMemory.load(path)
        assert loaded.customer_id == "user_test"
        assert loaded.customer_profile["customer_goal"] == "gift for partner"


def test_load_returns_fresh_memory_when_file_missing():
    memory = TrendoraMemory.load("/tmp/definitely_does_not_exist_trendora.json", customer_id="new_user")
    assert memory.customer_id == "new_user"
    assert memory.customer_profile == {}
