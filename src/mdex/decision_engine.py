"""
Decision Engine — the critical technical function of MDEX.

Given a belief state, a set of candidate actions, and an economic model,
ranks actions by computing their true decision-theoretic value:

For INFORMATION-GATHERING actions (kind = 'drill_hole', 'geophysical_survey', etc.):
  value = VOI (value of information) 
         = E[BestAction(posterior)] - BestAction(prior) - cost
         
For TERMINAL actions ('hold', 'stop', etc.):
  value = EMV(belief, action) - cost(action)

The ranking sorts actions by value in descending order, with infeasible
actions sorted last for transparency.

[ASSUMPTION] Single-step-lookahead VOI: we compute VOI as the value of one
information acquisition, not optimally sequenced multi-step campaigns. A full
sequential (POMDP) solution is out of scope for this TRL-3 POC.
"""
from dataclasses import dataclass, field

from .belief import BeliefState
from .economics import EconomicModel
from .evidence import EvidenceItem
from .information_value import CandidateAction, voi_for_information_action, expected_uncertainty_reduction




@dataclass
class ActionEvaluation:
    action: CandidateAction
    feasible: bool
    voi_usd: float  # renamed from evoi_usd for clarity
    action_value_usd: float  # direct terminal value (EMV - cost) for non-information actions
    total_value_usd: float  # final ranking value (VOI for info actions, EMV-cost for terminal)
    uncertainty_reduction_bits: float
    rationale: str
    assumptions: list[str] = field(default_factory=list)
    evidence_provenance: list[str] = field(default_factory=list)
    is_information_action: bool = False


def evaluate_action(
    belief: BeliefState,
    action: CandidateAction,
    all_candidate_actions: list[CandidateAction],  # all actions for VOI context
    econ: EconomicModel,
    evidence_used: list[EvidenceItem],
) -> ActionEvaluation:
    """
    Evaluate a single candidate action under the current belief.
    
    For information-gathering actions, computes true VOI (value of information).
    For terminal actions, computes direct EMV minus cost.
    """
    feasible = econ.feasible(action.cost)
    unc_reduction = expected_uncertainty_reduction(belief, action)
    
    # Determine action type and compute value
    is_information_gathering = action.kind in ["drill_hole", "geophysical_survey", "geochemical_sampling"]
    
    if is_information_gathering:
        # For information actions: VOI already includes cost subtraction
        voi = voi_for_information_action(belief, action, all_candidate_actions, econ)
        total_value = voi
        action_value = 0.0  # not applicable for info actions
        action_type = "information-gathering"
    else:
        # For terminal actions: direct EMV calculation
        action_value = econ.expected_monetary_value(belief, action.cost)
        total_value = action_value
        voi = 0.0  # not applicable for terminal actions
        action_type = "terminal"
    
    most_likely_h, p = belief.most_likely()
    rationale = (
        f"Action '{action.name}' ({action_type}): "
        f"current belief favors {most_likely_h.value} (p={p:.2f}, entropy={belief.entropy():.2f} bits). "
        f"Cost ${action.cost.amount_usd:,.0f} ({action.cost.provenance.value}), "
    )
    
    if is_information_gathering:
        rationale += (
            f"expected entropy reduction {unc_reduction:.2f} bits, "
            f"VOI (value of better future decisions) ${voi:,.0f}, "
            f"total value ${total_value:,.0f}. "
        )
    else:
        rationale += (
            f"direct EMV (expected payoff - cost) ${action_value:,.0f}. "
        )
    
    rationale += (
        f"{'FEASIBLE' if feasible else 'INFEASIBLE'} under remaining budget "
        f"${econ.budget_remaining_usd:,.0f}."
    )
    
    assumptions = [
        "Single-step-lookahead decision model (not full POMDP).",
        f"Action type: {action_type}.",
        f"Action cost provenance: {action.cost.provenance.value}.",
    ]
    evidence_provenance = [f"{e.id} ({e.provenance.value}, source: {e.source})" for e in evidence_used]

    return ActionEvaluation(
        action=action,
        feasible=feasible,
        voi_usd=voi,
        action_value_usd=action_value,
        total_value_usd=total_value,
        uncertainty_reduction_bits=unc_reduction,
        rationale=rationale,
        assumptions=assumptions,
        evidence_provenance=evidence_provenance,
        is_information_action=is_information_gathering,
    )


def rank_actions(
    belief: BeliefState,
    candidate_actions: list[CandidateAction],
    econ: EconomicModel,
    evidence_used: list[EvidenceItem],
) -> list[ActionEvaluation]:
    """
    Rank all candidate actions by their decision value (VOI for info actions, EMV for terminal).
    
    Feasible actions are sorted before infeasible ones, with infeasible actions reported
    for transparency rather than silently excluded.
    """
    evaluations = [
        evaluate_action(belief, a, candidate_actions, econ, evidence_used)
        for a in candidate_actions
    ]
    # Infeasible actions are still reported (transparency) but sorted after feasible ones.
    return sorted(
        evaluations,
        key=lambda ev: (not ev.feasible, -ev.total_value_usd),
    )


def recommend(
    belief: BeliefState,
    candidate_actions: list[CandidateAction],
    econ: EconomicModel,
    evidence_used: list[EvidenceItem],
) -> ActionEvaluation:
    ranked = rank_actions(belief, candidate_actions, econ, evidence_used)
    feasible_ranked = [ev for ev in ranked if ev.feasible]
    if not feasible_ranked:
        raise ValueError("No feasible action within remaining budget")
    return feasible_ranked[0]
