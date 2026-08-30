"""
Geological Belief Engine.

Represents belief as a discrete probability distribution over a fixed set of
competing geological hypotheses, and updates it via Bayes' rule as evidence
(already filtered by the temporal firewall) is introduced.

Likelihood tables are hand-authored, explicit, and defined within evidence item definitions
and outcome scenarios. They are [ASSUMPTION]s, not fitted parameters —
this is a documented TRL-3 simplification (see docs/OPEN_ISSUES.md).
"""
import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .evidence import EvidenceItem


class Hypothesis(str, Enum):
    H1_SHALLOW_SUPERGENE = "H1_shallow_supergene"
    H2_DEEP_HYPOGENE_PORPHYRY = "H2_deep_hypogene_porphyry"
    H3_LOCALIZED_NONECONOMIC = "H3_localized_noneconomic"
    H4_INSUFFICIENT_EVIDENCE = "H4_insufficient_evidence"


HYPOTHESES = list(Hypothesis)


def uniform_prior() -> dict[Hypothesis, float]:
    n = len(HYPOTHESES)
    return {h: 1.0 / n for h in HYPOTHESES}


@dataclass
class BeliefState:
    posterior: dict[Hypothesis, float]

    def entropy(self) -> float:
        """Shannon entropy of the posterior, in bits. Used as the
        uncertainty measure throughout the system."""
        h = 0.0
        for p in self.posterior.values():
            if p > 0:
                h -= p * math.log2(p)
        return h

    def most_likely(self) -> tuple[Hypothesis, float]:
        h, p = max(self.posterior.items(), key=lambda kv: kv[1])
        return h, p

    def as_dict(self) -> dict[str, float]:
        return {h.value: p for h, p in self.posterior.items()}


# A likelihood function maps (evidence_item) -> {Hypothesis: P(evidence | H)}
LikelihoodFn = Callable[[EvidenceItem], dict[Hypothesis, float]]


def bayes_update(prior: dict[Hypothesis, float], likelihood: dict[Hypothesis, float]) -> dict[Hypothesis, float]:
    """Standard discrete Bayes rule: posterior ∝ prior * likelihood, normalized."""
    unnorm = {h: prior[h] * likelihood.get(h, 1e-9) for h in HYPOTHESES}
    z = sum(unnorm.values())
    if z <= 0:
        raise ValueError("Degenerate posterior: likelihoods incompatible with prior")
    return {h: v / z for h, v in unnorm.items()}


def update_belief(
    prior_state: BeliefState,
    evidence_items: list[EvidenceItem],
    likelihood_fn: LikelihoodFn,
) -> BeliefState:
    """Sequentially fold a batch of evidence into the prior belief.

    Evidence items must already be temporally filtered by the caller
    (EvidenceStore.as_of(t)) before being passed in here. This module does
    not know about dates and must not be given a way to peek at the future.
    """
    posterior = dict(prior_state.posterior)
    for item in evidence_items:
        likelihood = likelihood_fn(item)
        # confidence-weighted likelihood: low-confidence evidence is
        # softened toward uninformative (all-hypotheses-equal) likelihood
        c = item.confidence
        softened = {h: c * likelihood.get(h, 1e-9) + (1 - c) * 1.0 for h in HYPOTHESES}
        posterior = bayes_update(posterior, softened)
    return BeliefState(posterior=posterior)
