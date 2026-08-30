"""
Exploration Economic Engine.

Provides cost, budget-feasibility, and expected-monetary-value (EMV)
calculations. Real historical cost/price figures are used only where
documented; otherwise parameters are exposed as configurable [ASSUMPTION]
defaults (see configs/economics.yaml) and are never silently presented as
historical fact.
"""
from dataclasses import dataclass
from enum import Enum

from .belief import BeliefState, Hypothesis


class ParamProvenance(str, Enum):
    HISTORICAL = "HISTORICAL"
    ASSUMPTION = "ASSUMPTION"


@dataclass
class ActionCost:
    amount_usd: float
    duration_days: int
    provenance: ParamProvenance
    note: str = ""


@dataclass
class EconomicModel:
    """Hypothesis-conditional economic payoff table (USD, expected value if
    that hypothesis turns out to be true and the project proceeds), plus a
    hard exploration budget."""
    payoff_by_hypothesis: dict[Hypothesis, float]
    budget_remaining_usd: float

    def feasible(self, cost: ActionCost) -> bool:
        return cost.amount_usd <= self.budget_remaining_usd

    def expected_monetary_value(self, belief: BeliefState, cost: ActionCost) -> float:
        """EMV = sum_h P(h) * payoff(h) - cost.

        This is a simplified, single-stage EMV appropriate to a TRL-3 POC.
        It does not discount for time value of money or model optionality
        beyond the current decision point; that refinement is TRL 4+ work
        (see docs/OPEN_ISSUES.md).
        """
        expected_payoff = sum(
            belief.posterior[h] * self.payoff_by_hypothesis.get(h, 0.0)
            for h in belief.posterior
        )
        return expected_payoff - cost.amount_usd

    def spend(self, cost: ActionCost) -> None:
        if not self.feasible(cost):
            raise ValueError("Attempted to spend beyond remaining budget")
        self.budget_remaining_usd -= cost.amount_usd
