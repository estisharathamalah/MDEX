"""
Evaluation Engine.

Compares MDEX's recommendation at a decision point against:
  - the actual historical decision
  - simple baseline strategies
using future-revealed information (accessed here ONLY, never upstream, via
EvidenceStore.all_items_UNSAFE_FOR_EVALUATION_ONLY()).

MDEX is not assumed superior. This module reports what happened, including
disagreement between MDEX and history.
"""
from dataclasses import dataclass

from .decision_engine import ActionEvaluation
from .information_value import CandidateAction


@dataclass
class BaselineResult:
    strategy_name: str
    selected_action_name: str
    rationale: str


@dataclass
class EvaluationReport:
    decision_point: str
    mdex_recommendation: str
    mdex_expected_decision_value_usd: float
    historical_decision: str
    baselines: list[BaselineResult]
    historical_outcome_summary: str
    agreement_with_history: bool
    regret_usd: float | None
    notes: list[str]


def nearest_known_mineralization_baseline(candidate_actions: list[CandidateAction]) -> BaselineResult:
    """Baseline: pick whichever drill-type action is nearest to a known
    mineralized zone (as encoded in the action's description/metadata by the
    experiment script). This is a simple heuristic, not a claim of realism."""
    drills = [a for a in candidate_actions if a.kind == "drill_hole"]
    if not drills:
        return BaselineResult("nearest_known_mineralization", "hold", "No drill candidates available.")
    chosen = drills[0]  # experiment script is expected to order candidates by proximity if using this baseline
    return BaselineResult(
        "nearest_known_mineralization",
        chosen.name,
        "Heuristic: drill closest to previously known mineralized indications.",
    )


def highest_probability_target_baseline(
    ranked_by_mdex: list[ActionEvaluation],
) -> BaselineResult:
    """Baseline: pick the action with highest single-hypothesis-conditional
    probability of success, ignoring cost and information value entirely."""
    drill_only = [r for r in ranked_by_mdex if r.action.kind == "drill_hole"]
    if not drill_only:
        return BaselineResult("highest_probability_target", "hold", "No drill candidates ranked.")
    best = max(drill_only, key=lambda r: r.uncertainty_reduction_bits)
    return BaselineResult(
        "highest_probability_target",
        best.action.name,
        "Heuristic: pick the target most likely to confirm the leading hypothesis, ignoring EVOI/cost trade-off.",
    )


def lowest_cost_action_baseline(candidate_actions: list[CandidateAction]) -> BaselineResult:
    cheapest = min(candidate_actions, key=lambda a: a.cost.amount_usd)
    return BaselineResult("lowest_cost_action", cheapest.name, "Heuristic: always take the cheapest feasible action.")


def random_feasible_baseline(candidate_actions: list[CandidateAction], econ, seed: int = 0) -> BaselineResult:
    import random

    rng = random.Random(seed)
    feasible = [a for a in candidate_actions if econ.feasible(a.cost)]
    if not feasible:
        return BaselineResult("random_feasible", "hold", "No feasible actions under budget.")
    chosen = rng.choice(feasible)
    return BaselineResult("random_feasible", chosen.name, f"Uniform random draw (seed={seed}) over feasible actions.")


def build_report(
    decision_point: str,
    mdex_rec: ActionEvaluation,
    ranked_by_mdex: list[ActionEvaluation],
    candidate_actions: list[CandidateAction],
    econ,
    historical_decision: str,
    historical_outcome_summary: str,
    best_retrospective_value_usd: float | None = None,
) -> EvaluationReport:
    baselines = [
        nearest_known_mineralization_baseline(candidate_actions),
        highest_probability_target_baseline(ranked_by_mdex),
        lowest_cost_action_baseline(candidate_actions),
        random_feasible_baseline(candidate_actions, econ),
    ]
    agreement = mdex_rec.action.name == historical_decision
    regret = None
    if best_retrospective_value_usd is not None:
        regret = best_retrospective_value_usd - mdex_rec.expected_decision_value_usd

    notes = []
    if not agreement:
        notes.append(
            "MDEX's recommendation DIFFERS from the historical decision. "
            "This is reported, not suppressed or adjusted to force agreement."
        )
    return EvaluationReport(
        decision_point=decision_point,
        mdex_recommendation=mdex_rec.action.name,
        mdex_expected_decision_value_usd=mdex_rec.expected_decision_value_usd,
        historical_decision=historical_decision,
        baselines=baselines,
        historical_outcome_summary=historical_outcome_summary,
        agreement_with_history=agreement,
        regret_usd=regret,
        notes=notes,
    )
