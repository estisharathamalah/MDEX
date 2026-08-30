"""
Unit tests for VOI (Value of Information) correctness.

These tests use analytically simple scenarios with known ground-truth
VOI values to verify that the implementation computes decision-theoretic
VOI correctly.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mdex.belief import BeliefState, Hypothesis, uniform_prior
from mdex.economics import ActionCost, EconomicModel, ParamProvenance, ActionSpecificEconomicModel
from mdex.information_value import (
    CandidateAction,
    OutcomeScenario,
    voi_for_information_action,
)


def test_voi_zero_when_information_is_not_valuable_and_cost_exceeds_benefit():
    """
    Scenario: two actions with symmetric payoffs, perfect information has zero value
    because the best action remains the same regardless.

    Action A: $100 if H1, $100 if H2 → value = $100 (constant)
    Action B (information): costs $25, perfectly distinguishes H1/H2
    
    VOI = (expected value after info) - (value now) - cost
        = $100 - $100 - $25
        = -$25
    
    Information is costly and provides no decision improvement.
    """
    belief = BeliefState(posterior={
        Hypothesis.H1_SHALLOW_SUPERGENE: 0.5,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.5,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
    })
    
    # Action A: constant payoff regardless of hypothesis
    action_a_cost = ActionCost(0.0, 0, ParamProvenance.ASSUMPTION)
    action_a = CandidateAction(
        name="drill_A",
        kind="drill_hole",
        cost=action_a_cost,
        outcome_scenarios=[],  # terminal action, no outcomes
        description="Constant value $100 regardless of hypothesis"
    )
    
    # Information action: costs $25, perfectly discriminates
    info_action_cost = ActionCost(25.0, 1, ParamProvenance.ASSUMPTION)
    info_action = CandidateAction(
        name="survey",
        kind="geophysical_survey",
        cost=info_action_cost,
        outcome_scenarios=[
            OutcomeScenario("H1_detected", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.99,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.01,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            }),
            OutcomeScenario("H2_detected", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.01,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.99,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            }),
        ]
    )
    
    econ = EconomicModel(
        payoff_by_hypothesis={
            Hypothesis.H1_SHALLOW_SUPERGENE: 100.0,
            Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 100.0,
            Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
            Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
        },
        budget_remaining_usd=1000.0,
    )
    
    voi = voi_for_information_action(belief, info_action, [action_a], econ)
    
    # Expected VOI ≈ -$25 (cost exceeds any benefit)
    assert voi < 0, f"VOI should be negative when cost exceeds benefit, got {voi}"
    assert abs(voi - (-25.0)) < 0.01, f"Expected VOI ≈ -$25, got {voi}"
    print(f"✓ test_voi_zero_when_information_is_not_valuable: VOI = ${voi:.2f} (expected ≈ -$25)")


def test_voi_positive_with_decision_change_ground_truth():
    """
    Ground-truth VOI test: information changes which action is optimal.
    
    Scenario:
    - Prior: H1 = 50%, H2 = 50% (uncertain which hypothesis is true)
    
    - Action A: H1→$100, H2→$0 (good if H1)
    - Action B: H1→$0, H2→$60 (good if H2)
    
    Decision WITHOUT information:
    - E[A] = 0.5×$100 + 0.5×$0 = $50 ← optimal
    - E[B] = 0.5×$0 + 0.5×$60 = $30
    - Best = $50
    
    Perfect information (survey cost $25):
    - If outcome reveals H1 (prob 0.5): choose A, get $100
    - If outcome reveals H2 (prob 0.5): choose B, get $60
    - E[best after info] = 0.5×$100 + 0.5×$60 = $80
    
    True VOI = $80 - $50 - $25 = $5
    
    This is POSITIVE because information changes the optimal decision.
    """
    belief = BeliefState(posterior={
        Hypothesis.H1_SHALLOW_SUPERGENE: 0.5,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.5,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
    })
    
    # Terminal actions with different payoff structures
    action_a_cost = ActionCost(0.0, 0, ParamProvenance.ASSUMPTION)
    action_a = CandidateAction(
        name="action_A",
        kind="drill_hole",
        cost=action_a_cost,
        outcome_scenarios=[],
        description="Action A: $100 if H1, $0 if H2"
    )
    
    action_b_cost = ActionCost(0.0, 0, ParamProvenance.ASSUMPTION)
    action_b = CandidateAction(
        name="action_B",
        kind="drill_hole",
        cost=action_b_cost,
        outcome_scenarios=[],
        description="Action B: $0 if H1, $60 if H2"
    )
    
    # Perfect information action: perfectly discriminates H1 vs H2
    survey_cost = ActionCost(25.0, 1, ParamProvenance.ASSUMPTION)
    survey = CandidateAction(
        name="perfect_survey",
        kind="geophysical_survey",
        cost=survey_cost,
        outcome_scenarios=[
            OutcomeScenario("perfectly_confirms_H1", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 1.0,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.0,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            }),
            OutcomeScenario("perfectly_confirms_H2", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.0,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 1.0,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            }),
        ]
    )
    
    # Economic model with action-specific payoffs
    econ = ActionSpecificEconomicModel(
        payoff_by_hypothesis_per_action={
            "action_A": {
                Hypothesis.H1_SHALLOW_SUPERGENE: 100.0,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.0,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            },
            "action_B": {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.0,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 60.0,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            },
        },
        budget_remaining_usd=1000.0,
    )
    
    # Compute VOI
    voi = voi_for_information_action(
        belief, survey, [action_a, action_b], econ
    )
    
    # Ground-truth assertion: VOI must be exactly $5
    print(f"test_voi_positive_with_decision_change: VOI = ${voi:.2f} (expected $5.00)")
    assert abs(voi - 5.0) < 1e-6, \
        f"Expected VOI = $5.00 for perfect information with decision change, got ${voi:.2f}"
    assert voi > 0, "VOI must be positive when information changes the optimal decision"



def test_voi_respects_budget_constraint():
    """
    Scenario: information action is too expensive relative to remaining budget.
    
    Even if VOI would be positive, the information action should still be marked
    as infeasible by the economic model, and VOI should reflect its true value
    (which may be high, but the action is not feasible to execute).
    """
    belief = BeliefState(posterior={
        Hypothesis.H1_SHALLOW_SUPERGENE: 0.5,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.5,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
    })
    
    action_a_cost = ActionCost(0.0, 0, ParamProvenance.ASSUMPTION)
    action_a = CandidateAction(
        name="drill",
        kind="drill_hole",
        cost=action_a_cost,
        outcome_scenarios=[],
    )
    
    # Expensive information
    info_action_cost = ActionCost(500.0, 10, ParamProvenance.ASSUMPTION)
    info_action = CandidateAction(
        name="expensive_survey",
        kind="geophysical_survey",
        cost=info_action_cost,
        outcome_scenarios=[
            OutcomeScenario("anomaly", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.3,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.7,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            }),
            OutcomeScenario("no_anomaly", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.7,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.3,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
            }),
        ]
    )
    
    # Very limited budget
    econ = EconomicModel(
        payoff_by_hypothesis={
            Hypothesis.H1_SHALLOW_SUPERGENE: 100.0,
            Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 100.0,
            Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.0,
            Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.0,
        },
        budget_remaining_usd=100.0,  # < $500 info cost
    )
    
    assert not econ.feasible(info_action_cost), "Info action should be infeasible"
    
    # VOI is still computed (for information purposes)
    # Terminal action after information is just action_a (only terminal action available)
    voi = voi_for_information_action(
        belief, info_action, [action_a], econ
    )
    
    # VOI will be negative because: (EMV benefit < $0) - (high cost $500)
    print(f"✓ test_voi_respects_budget: VOI = ${voi:.2f} (infeasible by budget constraint)")


if __name__ == "__main__":
    test_voi_zero_when_information_is_not_valuable_and_cost_exceeds_benefit()
    test_voi_positive_with_decision_change_ground_truth()
    test_voi_respects_budget_constraint()
    print("\n✓ All VOI correctness tests passed!")
