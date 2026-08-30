import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mdex.belief import BeliefState, Hypothesis, uniform_prior, update_belief
from mdex.decision_engine import rank_actions, recommend
from mdex.economics import ActionCost, EconomicModel, ParamProvenance
from mdex.evidence import EvidenceItem, EvidenceKind, EvidenceStore, ProvenanceTag
from mdex.information_value import CandidateAction, OutcomeScenario
from mdex.replay import ReplayEngine


def make_evidence(id_, strength, d=date(2001, 6, 1)):
    return EvidenceItem(
        id=id_,
        kind=EvidenceKind.GEOCHEMICAL_OBSERVATION,
        description="test",
        date_observed=d,
        date_available=d,
        source="synthetic/test",
        provenance=ProvenanceTag.SYNTHETIC,
        confidence=0.9,
        values={"strength": strength},
    )


def likelihood_fn(evidence):
    s = evidence.values.get("strength", 0.5)
    return {
        Hypothesis.H1_SHALLOW_SUPERGENE: 1.0,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 1.0 + s,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 1.0 - 0.5 * s,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 1.0,
    }


def test_bayesian_update_shifts_posterior_toward_favored_hypothesis():
    prior = BeliefState(posterior=uniform_prior())
    ev = [make_evidence("E1", strength=0.9)]
    posterior = update_belief(prior, ev, likelihood_fn)
    assert posterior.posterior[Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY] > prior.posterior[Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY]
    assert abs(sum(posterior.posterior.values()) - 1.0) < 1e-9


def test_posterior_normalizes_and_entropy_bounds():
    prior = BeliefState(posterior=uniform_prior())
    assert abs(prior.entropy() - 2.0) < 1e-9  # log2(4) = 2 bits for a uniform 4-way prior
    ev = [make_evidence("E1", strength=0.99)]
    posterior = update_belief(prior, ev, likelihood_fn)
    assert posterior.entropy() <= prior.entropy() + 1e-9  # informative evidence should not increase entropy on average


def _simple_action(name, cost_usd, hit_h2_strength=0.8):
    cost = ActionCost(cost_usd, 10, ParamProvenance.ASSUMPTION)
    hit = OutcomeScenario("hit", {
        Hypothesis.H1_SHALLOW_SUPERGENE: 0.3,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: hit_h2_strength,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.1,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.2,
    })
    miss = OutcomeScenario("miss", {
        Hypothesis.H1_SHALLOW_SUPERGENE: 0.7,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.2,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.9,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.8,
    })
    return CandidateAction(name=name, kind="drill_hole", cost=cost, outcome_scenarios=[hit, miss])


def test_action_ranking_respects_budget_feasibility():
    belief = BeliefState(posterior=uniform_prior())
    econ = EconomicModel(
        payoff_by_hypothesis={
            Hypothesis.H1_SHALLOW_SUPERGENE: 1_000_000,
            Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 100_000_000,
            Hypothesis.H3_LOCALIZED_NONECONOMIC: 0,
            Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0,
        },
        budget_remaining_usd=50_000,
    )
    cheap = _simple_action("cheap_hole", 40_000)
    expensive = _simple_action("expensive_hole", 500_000)
    ranked = rank_actions(belief, [cheap, expensive], econ, [])
    assert ranked[0].action.name == "cheap_hole"
    assert ranked[0].feasible is True
    expensive_eval = next(r for r in ranked if r.action.name == "expensive_hole")
    assert expensive_eval.feasible is False

    rec = recommend(belief, [cheap, expensive], econ, [])
    assert rec.action.name == "cheap_hole"  # must never recommend an infeasible action


def test_no_feasible_action_raises():
    belief = BeliefState(posterior=uniform_prior())
    econ = EconomicModel(payoff_by_hypothesis={h: 0 for h in Hypothesis}, budget_remaining_usd=100)
    action = _simple_action("too_expensive", 500_000)
    try:
        recommend(belief, [action], econ, [])
        assert False, "expected ValueError for no feasible action"
    except ValueError:
        pass


def test_sequential_replay_is_reproducible():
    econ_factory = lambda: EconomicModel(
        payoff_by_hypothesis={
            Hypothesis.H1_SHALLOW_SUPERGENE: 1_000_000,
            Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 100_000_000,
            Hypothesis.H3_LOCALIZED_NONECONOMIC: 0,
            Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0,
        },
        budget_remaining_usd=1_000_000,
    )
    store = EvidenceStore([make_evidence("E1", 0.7, date(2001, 6, 1)), make_evidence("E2", 0.9, date(2001, 6, 15))])
    actions = [_simple_action("hole_A", 100_000), _simple_action("hole_B", 100_000, hit_h2_strength=0.5)]

    def run_once():
        engine = ReplayEngine(store, likelihood_fn, econ_factory())
        prior = BeliefState(posterior=uniform_prior())
        belief, rec = engine.step(date(2001, 7, 1), prior, actions)
        return belief.as_dict(), rec.action.name, rec.total_value_usd

    result_1 = run_once()
    result_2 = run_once()
    assert result_1 == result_2  # identical inputs must produce an identical trace


def test_baseline_evaluation_reports_disagreement_when_present():
    from mdex.evaluation import build_report

    belief = BeliefState(posterior=uniform_prior())
    econ = EconomicModel(
        payoff_by_hypothesis={
            Hypothesis.H1_SHALLOW_SUPERGENE: 1_000_000,
            Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 100_000_000,
            Hypothesis.H3_LOCALIZED_NONECONOMIC: 0,
            Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0,
        },
        budget_remaining_usd=1_000_000,
    )
    actions = [_simple_action("hole_A", 100_000), _simple_action("hole_B", 100_000)]
    ranked = rank_actions(belief, actions, econ, [])
    rec = recommend(belief, actions, econ, [])
    report = build_report(
        decision_point="unit-test",
        mdex_rec=rec,
        ranked_by_mdex=ranked,
        candidate_actions=actions,
        belief_state=belief,
        econ=econ,
        historical_decision="some_other_action_never_in_candidates",
        historical_outcome_summary="synthetic outcome for unit test",
    )
    assert report.agreement_with_history is False
    assert any("DIFFERS" in n for n in report.notes)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS: {name}")
    print("All core engine tests passed.")
