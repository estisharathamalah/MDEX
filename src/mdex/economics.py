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

    def expected_monetary_value(self, belief: BeliefState, cost: ActionCost, action: 'CandidateAction' = None) -> float:
        """EMV = sum_h P(h) * payoff(h) - cost.

        This is a simplified, single-stage EMV appropriate to a TRL-3 POC.
        It does not discount for time value of money or model optionality
        beyond the current decision point; that refinement is TRL 4+ work
        (see docs/OPEN_ISSUES.md).
        
        If action is provided and this model supports action-specific payoffs,
        uses those; otherwise uses global payoff_by_hypothesis.
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


class ActionSpecificEconomicModel(EconomicModel):
    """Economic model where payoffs are specific to (hypothesis, action) pairs.
    
    Used primarily for rigorous testing of VOI calculation where different actions
    have different payoff structures. Example:
    
        payoff_by_hypothesis_per_action = {
            "action_A": {H1: $100, H2: $0},
            "action_B": {H1: $0, H2: $60},
        }
    
    This allows testing that VOI correctly captures the value of information
    when it changes which action is optimal.
    """
    
    def __init__(self, payoff_by_hypothesis_per_action: dict, budget_remaining_usd: float):
        """Initialize with action-specific payoff tables.
        
        Args:
            payoff_by_hypothesis_per_action: dict mapping action name to {hypothesis: payoff}
            budget_remaining_usd: exploration budget
        """
        self.payoff_by_hypothesis_per_action = payoff_by_hypothesis_per_action
        self.budget_remaining_usd = budget_remaining_usd
        # Set a dummy global payoff table (not used, but keeps parent class happy)
        super().__init__(
            payoff_by_hypothesis={},
            budget_remaining_usd=budget_remaining_usd
        )
    
    def expected_monetary_value(self, belief, cost, action=None):
        """Compute EMV using action-specific payoffs if available.
        
        Args:
            belief: BeliefState
            cost: ActionCost
            action: CandidateAction (optional; if provided and in payoff table, use those payoffs)
        
        Returns:
            Expected monetary value: E[payoff] - cost
        """
        if action is None or action.name not in self.payoff_by_hypothesis_per_action:
            # Fall back to parent (but parent will return 0 since payoff_by_hypothesis is empty)
            raise ValueError(f"Action {action.name if action else 'None'} not found in payoff table")
        
        payoff_for_action = self.payoff_by_hypothesis_per_action[action.name]
        expected_payoff = sum(
            belief.posterior.get(h, 0.0) * payoff_for_action.get(h, 0.0)
            for h in payoff_for_action
        )
        return expected_payoff - cost.amount_usd
