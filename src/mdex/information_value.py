"""
Information Value Engine.

Implements a decision-theoretically correct discrete pre-posterior
Value-of-Information calculation (Howard 1966 framework) for candidate
exploration actions:

  VOI(a) = E_outcomes[ OptimalDecision(posterior after outcome) ]
           - OptimalDecision(current belief)
           - cost(a)

where "OptimalDecision(belief)" means:
  max over feasible actions of [EMV(belief, action) - cost(action)]

Because full outcome spaces for real assays are continuous, this POC
discretizes each action's possible outcomes into a small enumerated set
(e.g. "high-grade hit", "low-grade hit", "barren") with outcome
probabilities derived from the current belief and a hand-authored
likelihood table. This discretization is an explicit [ASSUMPTION] and is
documented per action definition.

Key difference from previous implementation:
The prior version computed: E[EMV(posterior)] - E[EMV(prior)].
The correct version computes: E[max_action(EMV(posterior, action))] - max_action(EMV(prior, action)).
This ensures that VOI reflects the value of making a BETTER decision after the information,
not merely the change in economic estimate.
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


def _best_action_value(belief: BeliefState, terminal_actions: list[CandidateAction], econ: EconomicModel) -> float:
    """
    Compute the value of the best feasible TERMINAL action under the current belief.
    
    Terminal actions are decision endpoints (drill, hold, stop) that produce economic payoffs.
    Information-gathering actions (survey, geochemical sampling) are explicitly EXCLUDED
    because they do not receive payoff_by_hypothesis; their value is computed separately via VOI.
    
    Value of terminal action a = EMV(belief, a) - cost(a)
    The 'hold' action (outside option) is treated as having value 0 by definition.
    
    Args:
        belief: Current belief state
        terminal_actions: Only terminal decision actions (drill, hold, stop)
                         Must NOT include information-gathering actions
        econ: Economic model
    
    Returns:
        Maximum value over all feasible terminal actions, or 0 if none are feasible
            or only 'hold' is available (outside option value = 0).
    """
    if not terminal_actions:
        return 0.0
    
    best_value = 0.0  # default: hold / outside option = 0
    for action in terminal_actions:
        # Skip 'hold' (outside option has value 0 by definition)
        if action.kind == "hold":
            continue
        if not econ.feasible(action.cost):
            continue
        action_value = econ.expected_monetary_value(belief, action.cost, action)
        best_value = max(best_value, action_value)
    
    return best_value


def voi_for_information_action(
    belief: BeliefState,
    information_action: CandidateAction,
    terminal_actions: list[CandidateAction],
    econ: EconomicModel,
) -> float:
    """
    Compute the true decision-theoretic Value of Information (VOI) for an information-gathering action.
    
    VOI(information_action) 
        = E_outcomes[ BestTerminalActionValue(posterior after outcome) ]
          - BestTerminalActionValue(current belief)
          - cost(information_action)
    
    where BestTerminalActionValue(belief) = max over feasible terminal actions of [EMV(belief, a) - cost(a)].
    
    Critical constraint: terminal_actions must contain ONLY decision endpoints (drill, hold, stop).
    It MUST NOT include the information_action itself or any other information-gathering actions.
    Violations of this constraint lead to circular valuation where information actions wrongly
    receive payoff_by_hypothesis as if they were terminal actions.
    
    Args:
        belief: Current belief state.
        information_action: The action that gathers information (geophysical_survey, geochemical_sampling, etc.).
                           This is the action being valued, NOT included in terminal_actions.
        terminal_actions: The set of TERMINAL decision actions available AFTER the information is received.
                         Must include 'hold' (outside option) but NOT the information_action itself.
                         Example: [drill_Southwest, drill_Central, hold].
        econ: Economic model with budget, payoffs, etc.
    
    Returns:
        Expected value of information in USD. Can be negative if the information is not valuable
        or if the action is too expensive. Already accounts for cost subtraction (not double-subtracted).
    
    Raises:
        AssertionError: If information_action appears in terminal_actions (architecture violation).
    """
    # Enforce architectural constraint: information action must not be in terminal_actions
    assert all(action.name != information_action.name for action in terminal_actions), \
        f"Architecture violation: information action '{information_action.name}' found in terminal_actions. " \
        "Information actions are valued via VOI, not as terminal decision endpoints."
    
    # Current best achievable value without the information
    current_best_value = _best_action_value(belief, terminal_actions, econ)
    
    # Expected value after acquiring information
    expected_posterior_best_value = 0.0
    
    for scenario in information_action.outcome_scenarios:
        p_outcome = _outcome_prior_probability(belief, scenario)
        if p_outcome <= 0:
            continue
        
        # Update belief based on this outcome scenario
        posterior = bayes_update(belief.posterior, scenario.probability_by_hypothesis)
        posterior_belief = BeliefState(posterior=posterior)
        
        # What is the best action we can take with this posterior belief?
        posterior_best_value = _best_action_value(posterior_belief, terminal_actions, econ)
        
        # Weight by outcome probability
        expected_posterior_best_value += p_outcome * posterior_best_value
    
    # VOI = expected future value - current best value - cost
    # The cost is subtracted exactly once here, not separately in the decision engine
    voi = expected_posterior_best_value - current_best_value - information_action.cost.amount_usd
    
    return voi
