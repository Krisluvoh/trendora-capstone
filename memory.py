"""
memory.py
---------
Contextual memory shared across Trendora's three agents within a session,
and persisted to disk so it survives across sessions for a returning
customer. This is what lets the Recommendation Agent say things like
"since you passed on the sneaker drop last time over price, here's a
budget-friendly alternative" instead of treating every turn as stateless.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


@dataclass
class TrendoraMemory:
    """
    One instance per customer. Each agent calls one of the update_from_*
    methods below with its own output after it runs (see orchestrator.py),
    so by the time the Recommendation Agent runs, memory already has
    everything Intake and Research learned. as_context_string() is what
    actually gets shown to the model each turn.
    """

    customer_id: str = "guest"
    customer_profile: dict = field(default_factory=dict)
    past_preferences: list = field(default_factory=list)
    past_objections: list = field(default_factory=list)
    product_interest_history: list = field(default_factory=list)
    hype_cycle_context: dict = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # ---------- update hooks, one per agent ----------

    def update_from_intake(self, intake_output: dict) -> None:
        """Called after the Intake Agent runs. Saves goal/budget/urgency and
        appends any new preferences or objections."""
        self.customer_profile.update(
            {
                "customer_goal": intake_output.get("customer_goal"),
                "budget": intake_output.get("budget"),
                "urgency_level": intake_output.get("urgency_level"),
            }
        )
        self._merge_unique(self.past_preferences, intake_output.get("preferences", []))
        self._merge_unique(self.past_objections, intake_output.get("objection_patterns", []))
        self._touch()

    def update_from_research(self, product_name: str, research_output: dict) -> None:
        """Called after the Research Agent runs. Logs this product to the
        interest history and caches its hype/scarcity context."""
        self.product_interest_history.append(
            {
                "product": product_name,
                "scarcity_score": research_output.get("scarcity_score"),
                "hype_cycle_analysis": research_output.get("hype_cycle_analysis"),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        self.hype_cycle_context[product_name] = {
            "drop_timing": research_output.get("drop_timing"),
            "confidence": research_output.get("confidence"),
        }
        self._touch()

    def update_from_recommendation(self, recommendation_output: dict) -> None:
        """Called after the Recommendation Agent runs. Remembers its
        strategy so a later turn can keep it consistent."""
        adaptation = recommendation_output.get("strategy_adaptation")
        if adaptation:
            self.customer_profile["last_strategy_adaptation"] = adaptation
        self._touch()

    def register_user_objection(self, objection: str) -> None:
        """Called directly by orchestrator.handle_objection, before the
        follow-up turn even runs, so the Recommendation Agent sees it as
        prior context."""
        self._merge_unique(self.past_objections, [objection])
        self._touch()

    # ---------- helpers ----------

    @staticmethod
    def _merge_unique(target: list, new_items: list) -> None:
        """Appends items not already present, in place, so repeated
        preferences/objections across turns don't get duplicated."""
        for item in new_items or []:
            if item not in target:
                target.append(item)

    def _touch(self) -> None:
        self.last_updated = datetime.now(UTC).isoformat()

    def as_context_string(self) -> str:
        """Compact summary injected into every agent prompt as MEMORY context."""
        return json.dumps(
            {
                "customer_profile": self.customer_profile,
                "past_preferences": self.past_preferences,
                "past_objections": self.past_objections,
                "product_interest_history": self.product_interest_history[-5:],
                "hype_cycle_context": self.hype_cycle_context,
            },
            indent=2,
        )

    # ---------- persistence ----------

    def save(self, path: str) -> None:
        """Writes this memory to a JSON file, creating parent folders if needed."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str, customer_id: str = "guest") -> TrendoraMemory:
        """Loads a saved memory file if one exists for this customer, otherwise starts a fresh one."""
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            return cls(**data)
        return cls(customer_id=customer_id)
