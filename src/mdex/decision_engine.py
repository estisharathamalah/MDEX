"""
Decision Engine — the critical technical function of MDEX.

Given a belief state, a set of candidate actions, and an economic model,
ranks actions by an explicit expected decision value combining:
  - EVOI (information value engine)
  - EMV net of cost (economic engine)
  - budget feasibility (hard constraint)

expected_decision_value(a) = EVOI(a) + EMV(belief, cost(a))   [ASSUMPTION: additive combination]

This additive rule is a documented simplification. It is one reasonable
way to combine an information-value term and a direct-economic-value term
into a single ranking score; a full sequential (POMDP) solution that
optimizes the entire multi-step campaign jointly is out of scope for this
TRL-3 POC and is listed as TRL-4+ future work.
"""
from dataclasses import dataclass, field

from .belief import BeliefState
from .economics import EconomicModel
from .evidence import EvidenceItem
from .information_value import CandidateAction, evoi, expected_uncertainty_reduction


@dataclass
class ActionEvaluation:
    action: CandidateAction
    feasible: bool
    evoi_usd: float
    emv_usd: float
    expected_decision_value_usd: float
    uncertainty_reduction_bits: float
    rationale: str
    assumptions: list[str] = field(default_factory=list)
    evidence_provenance: list[str] = field(default_factory=list)


def evaluate_action(
    belief: BeliefState,
    action: CandidateAction,
    econ: EconomicModel,
    evidence_used: list[EvidenceItem],
) -> ActionEvaluation:
    feasible = econ.feasible(action.cost)
    v = evoi(belief, action, econ)
    m = econ.expected_monetary_value(belief, action.cost)
    edv = v + m
    unc_reduction = expected_uncertainty_reduction(belief, action)

    most_likely_h, p = belief.most_likely()
    rationale = (
        f"Current belief favors {most_likely_h.value} (p={p:.2f}, entropy={belief.entropy():.2f} bits). "
        f"Action '{action.name}' costs ${action.cost.amount_usd:,.0f} "
        f"({action.cost.provenance.value} cost estimate), is expected to reduce entropy by "
        f"{unc_reduction:.2f} bits, carries EVOI ${v:,.0f} and direct EMV ${m:,.0f}, "
        f"for an expected decision value of ${edv:,.0f}. "
        f"{'FEASIBLE' if feasible else 'INFEASIBLE'} under remaining budget of "
        f"${econ.budget_remaining_usd:,.0f}."
    )
    assumptions = [
        "Additive combination of EVOI and EMV into a single ranking score.",
        "Single-step-lookahead VOI (not a full sequential POMDP optimum).",
        f"Action cost provenance: {action.cost.provenance.value}.",
    ]
    evidence_provenance = [f"{e.id} ({e.provenance.value}, source: {e.source})" for e in evidence_used]

    return ActionEvaluation(
        action=action,
        feasible=feasible,
        evoi_usd=v,
        emv_usd=m,
        expected_decision_value_usd=edv,
        uncertainty_reduction_bits=unc_reduction,
        rationale=rationale,
        assumptions=assumptions,
        evidence_provenance=evidence_provenance,
    )


def rank_actions(
    belief: BeliefState,
    candidate_actions: list[CandidateAction],
    econ: EconomicModel,
    evidence_used: list[EvidenceItem],
) -> list[ActionEvaluation]:
    evaluations = [evaluate_action(belief, a, econ, evidence_used) for a in candidate_actions]
    # Infeasible actions are still reported (transparency) but sorted after feasible ones.
    return sorted(
        evaluations,
        key=lambda ev: (not ev.feasible, -ev.expected_decision_value_usd),
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
