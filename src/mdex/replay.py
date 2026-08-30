"""
Historical Replay Engine.

Iterates a chronological sequence of decision points. At each point:
  1. filter evidence to what was available at that date (temporal firewall)
  2. update belief
  3. generate/receive candidate actions
  4. rank and recommend
  5. record a full decision trace (for reproducibility & evaluation)
  6. advance to the next decision date (the calling experiment script is
     responsible for supplying the next date and the candidate actions,
     since these are scenario-specific)

This module does not decide what the "next" historical evidence reveal is;
that is orchestrated by the experiment script so it stays inspectable and
cannot silently leak future information into an earlier step.
"""
from dataclasses import dataclass, field
from datetime import date

from .belief import BeliefState, update_belief, LikelihoodFn
from .decision_engine import ActionEvaluation, rank_actions
from .economics import EconomicModel
from .evidence import EvidenceStore
from .information_value import CandidateAction


@dataclass
class DecisionStep:
    decision_date: date
    evidence_ids_used: list[str]
    belief_before: dict
    belief_after: dict
    ranked_actions: list[ActionEvaluation]
    recommended_action_name: str


@dataclass
class ReplayTrace:
    steps: list[DecisionStep] = field(default_factory=list)


class ReplayEngine:
    def __init__(self, store: EvidenceStore, likelihood_fn: LikelihoodFn, econ: EconomicModel):
        self.store = store
        self.likelihood_fn = likelihood_fn
        self.econ = econ
        self.trace = ReplayTrace()

    def step(
        self,
        decision_date: date,
        prior_belief: BeliefState,
        candidate_actions: list[CandidateAction],
    ) -> tuple[BeliefState, ActionEvaluation]:
        evidence_now = self.store.as_of(decision_date)
        belief_after = update_belief(prior_belief, evidence_now, self.likelihood_fn)
        ranked = rank_actions(belief_after, candidate_actions, self.econ, evidence_now)
        feasible = [r for r in ranked if r.feasible]
        if not feasible:
            raise ValueError(f"No feasible action at {decision_date} within remaining budget")
        recommended = feasible[0]

        self.trace.steps.append(
            DecisionStep(
                decision_date=decision_date,
                evidence_ids_used=[e.id for e in evidence_now],
                belief_before=prior_belief.as_dict(),
                belief_after=belief_after.as_dict(),
                ranked_actions=ranked,
                recommended_action_name=recommended.action.name,
            )
        )
        return belief_after, recommended
