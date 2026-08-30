"""
MANDATORY test: proves information dated after decision time T cannot
affect the recommendation generated at T.

Method: build two evidence stores that are IDENTICAL up to time T, but
differ arbitrarily after T (one has a strongly positive future assay, the
other a strongly negative one). Confirm the belief update and resulting
recommendation at T are byte-for-byte identical regardless of what happens
after T.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mdex.belief import BeliefState, Hypothesis, uniform_prior, update_belief
from mdex.evidence import EvidenceItem, EvidenceKind, EvidenceStore, ProvenanceTag


def make_item(item_id, date_avail, kind=EvidenceKind.GEOCHEMICAL_OBSERVATION):
    return EvidenceItem(
        id=item_id,
        kind=kind,
        description=f"test evidence {item_id}",
        date_observed=date_avail,
        date_available=date_avail,
        source="synthetic/test",
        provenance=ProvenanceTag.SYNTHETIC,
        confidence=0.9,
        values={"strength": 0.9},
    )


def flat_likelihood(evidence):
    return {h: 1.0 for h in Hypothesis}


def strong_h2_likelihood(evidence):
    return {
        Hypothesis.H1_SHALLOW_SUPERGENE: 0.1,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 5.0,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.1,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.1,
    }


def weak_h2_likelihood(evidence):
    return {
        Hypothesis.H1_SHALLOW_SUPERGENE: 5.0,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.1,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 5.0,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 5.0,
    }


def test_future_evidence_never_reaches_decision_at_T():
    T = date(2001, 7, 1)
    future_date = date(2001, 8, 1)

    shared_pre_T = [make_item("E1", date(2001, 6, 1)), make_item("E2", date(2001, 6, 20))]

    store_a = EvidenceStore(shared_pre_T + [make_item("FUTURE_POSITIVE", future_date)])
    store_b = EvidenceStore(shared_pre_T + [make_item("FUTURE_NEGATIVE", future_date)])

    evidence_a_at_T = store_a.as_of(T)
    evidence_b_at_T = store_b.as_of(T)

    # The firewall must exclude the future item entirely from both.
    ids_a = {e.id for e in evidence_a_at_T}
    ids_b = {e.id for e in evidence_b_at_T}
    assert "FUTURE_POSITIVE" not in ids_a
    assert "FUTURE_NEGATIVE" not in ids_b
    assert ids_a == ids_b == {"E1", "E2"}

    prior = BeliefState(posterior=uniform_prior())
    belief_a = update_belief(prior, evidence_a_at_T, flat_likelihood)
    belief_b = update_belief(prior, evidence_b_at_T, flat_likelihood)

    # Because the visible evidence sets are identical, posteriors must match exactly.
    assert belief_a.as_dict() == belief_b.as_dict()


def test_firewall_excludes_future_even_with_informative_likelihoods():
    """Stronger check: even when the (excluded) future evidence WOULD have
    swung the posterior dramatically under an informative likelihood
    function, the at-T belief must be unaffected because the evidence never
    reaches update_belief in the first place."""
    T = date(2001, 7, 1)
    future_date = date(2001, 8, 1)

    pre_T = [make_item("E1", date(2001, 6, 1))]
    future_bullish = make_item("FUTURE_BULLISH", future_date)

    store = EvidenceStore(pre_T + [future_bullish])
    evidence_at_T = store.as_of(T)
    assert [e.id for e in evidence_at_T] == ["E1"]

    prior = BeliefState(posterior=uniform_prior())
    belief_at_T = update_belief(prior, evidence_at_T, strong_h2_likelihood)

    # Now simulate what WOULD happen if the firewall were bypassed (for comparison only).
    evidence_leaked = store.all_items_UNSAFE_FOR_EVALUATION_ONLY()
    belief_leaked = update_belief(prior, evidence_leaked, strong_h2_likelihood)

    # The legitimate at-T belief must differ from the "leaked" belief,
    # proving the future item is influential (a meaningful test) and that
    # the firewall path correctly withholds it.
    assert belief_at_T.as_dict() != belief_leaked.as_dict()


def test_as_of_is_monotonic_non_decreasing_in_evidence_count():
    dates = [date(2001, 1, 1), date(2001, 3, 1), date(2001, 6, 1), date(2001, 9, 1)]
    store = EvidenceStore([make_item(f"E{i}", d) for i, d in enumerate(dates)])
    counts = [len(store.as_of(d)) for d in sorted(dates)]
    assert counts == sorted(counts)
    assert len(store.as_of(date(2001, 12, 31))) == 4
    assert len(store.as_of(date(2000, 1, 1))) == 0


if __name__ == "__main__":
    test_future_evidence_never_reaches_decision_at_T()
    test_firewall_excludes_future_even_with_informative_likelihoods()
    test_as_of_is_monotonic_non_decreasing_in_evidence_count()
    print("All temporal firewall tests passed.")
