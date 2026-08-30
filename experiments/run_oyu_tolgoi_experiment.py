"""
Experiment: pre-OTD-150 decision replay (Oyu Tolgoi, July 2001).

Question: could MDEX identify a high-value exploration action using only
information available before the historical OTD-150 outcome?

Run:
    python3 experiments/run_oyu_tolgoi_experiment.py

Data honesty notice: the macro decision context (three-site choice, budget
constraint, which site was historically chosen, and the eventual outcome)
is FACT, cited in data/DATA_PROVENANCE.md. The per-site surface-indication
strengths used to construct evidence items and likelihoods are SYNTHETIC
placeholders (data/synthetic/candidate_site_indications.json) because the
real 2001 hole-by-hole/site-by-site geochemistry was not obtained in this
session. This experiment therefore demonstrates that the COMPUTATIONAL
PIPELINE correctly implements the temporal firewall, belief update, VOI,
economics, and ranking against a historically-grounded scenario — it does
NOT yet constitute a fully historically-validated backtest. See
docs/OPEN_ISSUES.md.
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

from mdex.belief import BeliefState, Hypothesis, uniform_prior, update_belief  # noqa: E402
from mdex.decision_engine import rank_actions, recommend  # noqa: E402
from mdex.economics import ActionCost, EconomicModel, ParamProvenance  # noqa: E402
from mdex.evaluation import build_report  # noqa: E402
from mdex.evidence import EvidenceItem, EvidenceKind, EvidenceStore, ProvenanceTag  # noqa: E402
from mdex.information_value import CandidateAction, OutcomeScenario  # noqa: E402

DECISION_DATE = date(2001, 7, 1)  # just before OTD-150 was collared


def load_evidence_store() -> EvidenceStore:
    store = EvidenceStore()
    facts = json.loads((ROOT / "data/historical/oyu_tolgoi_facts.json").read_text())
    for f in facts["facts"]:
        store.add(
            EvidenceItem(
                id=f["id"],
                kind=EvidenceKind(f["kind"]),
                description=f["description"],
                date_observed=date.fromisoformat(f["date_observed"]),
                date_available=date.fromisoformat(f["date_available"]),
                source=f["source"],
                provenance=ProvenanceTag(f["provenance"]),
                confidence=f["confidence"],
                values=f.get("values", {}),
            )
        )

    synth = json.loads((ROOT / "data/synthetic/candidate_site_indications.json").read_text())
    for site, vals in synth["sites"].items():
        store.add(
            EvidenceItem(
                id=f"SYN_{site}",
                kind=EvidenceKind.GEOCHEMICAL_OBSERVATION,
                description=f"Synthetic surface indication strength for {site}: {vals['note']}",
                date_observed=DECISION_DATE,
                date_available=DECISION_DATE,
                source="synthetic/candidate_site_indications.json",
                provenance=ProvenanceTag.SYNTHETIC,
                confidence=0.5,
                values=vals,
                spatial_ref=site,
            )
        )
    return store


def likelihood_fn(evidence: EvidenceItem) -> dict[Hypothesis, float]:
    """Hand-authored [ASSUMPTION] likelihoods. Southwest Oyu's synthetic
    indication is deliberately the strongest of the three (consistent with
    it being the historically chosen site) but this is illustrative, not a
    transcription of a real 2001 geochemistry likelihood model."""
    if evidence.provenance != ProvenanceTag.SYNTHETIC:
        # Historical scaffold facts (F1-F4) are treated as broadly informative
        # about "a porphyry system is plausible in this district" without
        # site-discriminating power on their own.
        return {
            Hypothesis.H1_SHALLOW_SUPERGENE: 1.0,
            Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 1.1,
            Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.9,
            Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.8,
        }
    strength = evidence.values.get("surface_alteration_strength", 0.5) + evidence.values.get(
        "surface_cu_geochem_anomaly", 0.5
    )
    return {
        Hypothesis.H1_SHALLOW_SUPERGENE: 0.5 + 0.3 * strength,
        Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.2 + 0.8 * strength,
        Hypothesis.H3_LOCALIZED_NONECONOMIC: 1.2 - 0.4 * strength,
        Hypothesis.H4_INSUFFICIENT_EVIDENCE: 1.0,
    }


def build_candidate_actions(econ_cfg: dict) -> list[CandidateAction]:
    def drill(site: str, base_cost_key: str = "deep_diamond_hole") -> CandidateAction:
        c = econ_cfg[base_cost_key]
        cost = ActionCost(c["cost_usd"], c["duration_days"], ParamProvenance(c["provenance"]), note=f"deep hole at {site}")
        hit = OutcomeScenario(
            "porphyry_hit",
            {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.3,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.85,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.05,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.2,
            },
        )
        miss = OutcomeScenario(
            "barren_or_low_grade",
            {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.7,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.15,
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.95,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.8,
            },
        )
        return CandidateAction(
            name=f"drill_{site}",
            kind="drill_hole",
            cost=cost,
            outcome_scenarios=[hit, miss],
            description=f"Commit one of the three affordable deep diamond holes to {site}.",
        )

    survey_cfg = econ_cfg["geophysical_survey"]
    survey = CandidateAction(
        name="additional_geophysical_survey",
        kind="geophysical_survey",
        cost=ActionCost(survey_cfg["cost_usd"], survey_cfg["duration_days"], ParamProvenance(survey_cfg["provenance"])),
        outcome_scenarios=[
            # If survey shows anomaly: favors H2 (porphyry) which is the economically valuable target
            OutcomeScenario("anomaly_confirmed", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.1,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.75,  # strongly favors porphyry
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.1,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.05,
            }),
            # If survey shows no anomaly: favors negative hypotheses (non-economic or insufficient)
            OutcomeScenario("no_anomaly", {
                Hypothesis.H1_SHALLOW_SUPERGENE: 0.4,
                Hypothesis.H2_DEEP_HYPOGENE_PORPHYRY: 0.1,  # low probability of porphyry
                Hypothesis.H3_LOCALIZED_NONECONOMIC: 0.4,
                Hypothesis.H4_INSUFFICIENT_EVIDENCE: 0.1,
            }),
        ],
        description="Run an additional IP/magnetic survey before committing a deep hole.",
    )

    hold_cfg = econ_cfg["hold"]
    hold = CandidateAction(
        name="hold",
        kind="hold",
        cost=ActionCost(hold_cfg["cost_usd"], hold_cfg["duration_days"], ParamProvenance(hold_cfg["provenance"])),
        outcome_scenarios=[],
        description="Take no further exploration action this period.",
    )

    return [drill("Southern_Oyu"), drill("Southwest_Oyu"), drill("Central_Oyu"), survey, hold]


def main():
    econ_cfg = yaml.safe_load((ROOT / "configs/economics.yaml").read_text())
    store = load_evidence_store()

    prior = BeliefState(posterior=uniform_prior())
    evidence_now = store.as_of(DECISION_DATE)
    belief = update_belief(prior, evidence_now, likelihood_fn)

    econ = EconomicModel(
        payoff_by_hypothesis={Hypothesis(k): v for k, v in econ_cfg["payoff_by_hypothesis_usd"].items()},
        budget_remaining_usd=econ_cfg["budget_available_usd"],
    )

    actions = build_candidate_actions(econ_cfg)
    ranked = rank_actions(belief, actions, econ, evidence_now)
    rec = recommend(belief, actions, econ, evidence_now)

    print("=" * 78)
    print("MDEX — Oyu Tolgoi pre-OTD-150 decision replay")
    print(f"Decision date: {DECISION_DATE}  |  Evidence items used: {len(evidence_now)}")
    print("=" * 78)
    print(f"\nBelief (posterior): {belief.as_dict()}")
    print(f"Entropy: {belief.entropy():.3f} bits\n")

    print("Ranked actions:")
    for ev in ranked:
        type_label = "info" if ev.is_information_action else "term"
        print(
            f"  [{'FEASIBLE' if ev.feasible else 'INFEASIBLE':10}] "
            f"{ev.action.name:28} ({type_label}) "
            f"Value=${ev.total_value_usd:>14,.0f}  "
            f"VOI=${ev.voi_usd:>13,.0f}  "
            f"dEntropy={ev.uncertainty_reduction_bits:.3f}"
        )

    print(f"\n>>> MDEX RECOMMENDATION: {rec.action.name}")
    print(f"\nRationale:\n{rec.rationale}")

    # ---- Evaluation against history and baselines ----
    historical_decision = "drill_Southwest_Oyu"  # FACT: F4 — Southwest Oyu was chosen historically
    facts = json.loads((ROOT / "data/historical/oyu_tolgoi_facts.json").read_text())
    f5 = next(f for f in facts["facts"] if f["id"] == "F5_FUTURE")
    outcome_summary = f5["description"] + " (Source: " + f5["source"] + ")"

    report = build_report(
        decision_point="Oyu Tolgoi pre-OTD-150, 2001-07-01",
        mdex_rec=rec,
        ranked_by_mdex=ranked,
        candidate_actions=actions,
        belief_state=belief,
        econ=econ,
        historical_decision=historical_decision,
        historical_outcome_summary=outcome_summary,
    )

    print("\n" + "=" * 78)
    print("EVALUATION")
    print("=" * 78)
    print(f"MDEX recommendation:      {report.mdex_recommendation}")
    print(f"Historical decision:      {report.historical_decision}")
    print(f"Agreement with history:   {report.agreement_with_history}")
    for b in report.baselines:
        print(f"Baseline [{b.strategy_name:28}]: {b.selected_action_name}  ({b.rationale})")
    print(f"\nHistorical outcome (revealed post-decision): {report.historical_outcome_summary}")
    for n in report.notes:
        print(f"NOTE: {n}")

    out_path = ROOT / "results" / "oyu_tolgoi_experiment_result.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "decision_date": str(DECISION_DATE),
                "belief_posterior": belief.as_dict(),
                "entropy_bits": belief.entropy(),
                "ranked_actions": [
                    {
                        "action": ev.action.name,
                        "action_type": "information" if ev.is_information_action else "terminal",
                        "feasible": ev.feasible,
                        "total_value_usd": ev.total_value_usd,
                        "voi_usd": ev.voi_usd,
                        "action_value_usd": ev.action_value_usd,
                        "uncertainty_reduction_bits": ev.uncertainty_reduction_bits,
                    }
                    for ev in ranked
                ],
                "mdex_recommendation": rec.action.name,
                "historical_decision": historical_decision,
                "agreement_with_history": report.agreement_with_history,
                "baselines": [b.__dict__ for b in report.baselines],
                "historical_outcome_summary": report.historical_outcome_summary,
                "notes": report.notes,
            },
            indent=2,
        )
    )
    print(f"\nFull machine-readable result written to: {out_path}")


if __name__ == "__main__":
    main()
