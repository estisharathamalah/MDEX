"""
Information Value Engine.

Implements a discrete pre-posterior Value-of-Information calculation
(Howard-style VOI) for candidate exploration actions:

  EVOI(a) = E_outcomes[ EMV(decision | posterior after outcome) ] - EMV(decision | current belief)

Because full outcome spaces for real assays are continuous, this POC
discretizes each action's possible outcomes into a small enumerated set
(e.g. "high-grade hit", "low-grade hit", "barren") with outcome
probabilities derived from the current belief and a hand-authored
likelihood table. This discretization is an explicit [ASSUMPTION] and is
documented per action definition.
"""
from dataclasses import dataclass
from typing import Callable

from .belief import BeliefState, Hypothesis, bayes_update
from .economics import ActionCost, EconomicModel


@dataclass
class OutcomeScenario:
    """One discretized possible result of taking an action."""
    name: str
    probability_by_hypothesis: dict[Hypothesis, float]  # P(this outcome | H)


@dataclass
class CandidateAction:
    name: str
    kind: str  # drill_hole, geophysical_survey, geochemical_sampling, hold, stop, analysis, jv_farmout
    cost: ActionCost
    outcome_scenarios: list[OutcomeScenario]
    description: str = ""


def _outcome_prior_probability(belief: BeliefState, scenario: OutcomeScenario) -> float:
    return sum(belief.posterior[h] * scenario.probability_by_hypothesis.get(h, 0.0) for h in belief.posterior)


def expected_uncertainty_reduction(belief: BeliefState, action: CandidateAction) -> float:
    """Expected drop in Shannon entropy after observing this action's outcome."""
    current_entropy = belief.entropy()
    expected_posterior_entropy = 0.0
    for scenario in action.outcome_scenarios:
        p_outcome = _outcome_prior_probability(belief, scenario)
        if p_outcome <= 0:
            continue
        posterior = bayes_update(belief.posterior, scenario.probability_by_hypothesis)
        posterior_entropy = -sum(p * __import__("math").log2(p) for p in posterior.values() if p > 0)
        expected_posterior_entropy += p_outcome * posterior_entropy
    return max(0.0, current_entropy - expected_posterior_entropy)


def evoi(belief: BeliefState, action: CandidateAction, econ: EconomicModel) -> float:
    """Expected Value of Information for a candidate action, in USD.

    EVOI = E[best achievable EMV after the action's outcome is known]
           - best achievable EMV under current belief (i.e. taking no further action)

    In this simplified single-action-lookahead POC, "best achievable EMV"
    collapses to the EMV of proceeding with the current best economic
    payoff estimate; the action's own cost is netted separately by the
    Economic Engine / Decision Engine, not double-counted here.
    """
    prior_emv = econ.expected_monetary_value(belief, ActionCost(0.0, 0, cost_provenance_placeholder()))
    expected_posterior_emv = 0.0
    for scenario in action.outcome_scenarios:
        p_outcome = _outcome_prior_probability(belief, scenario)
        if p_outcome <= 0:
            continue
        posterior = bayes_update(belief.posterior, scenario.probability_by_hypothesis)
        posterior_belief = BeliefState(posterior=posterior)
        posterior_emv = econ.expected_monetary_value(posterior_belief, ActionCost(0.0, 0, cost_provenance_placeholder()))
        expected_posterior_emv += p_outcome * posterior_emv
    return expected_posterior_emv - prior_emv


def cost_provenance_placeholder():
    # local import to avoid circularity in type-checking-only contexts
    from .economics import ParamProvenance
    return ParamProvenance.ASSUMPTION
