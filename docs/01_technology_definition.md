# MDEX — Technology Definition
### Mineral Exploration Decision Engine — TRL 3 Proof-of-Concept
DTV Deep-Tech Ventures application material — Dhahran Techno Valley / KFUPM

Status legend used throughout this document and the rest of the repository:
`[FACT]` historically documented, `[ASSUMPTION]` a modeling choice, `[SYNTHETIC]` fabricated-for-testing data, `[MODEL OUTPUT]` something MDEX computed, `[UNPROVEN]` a hypothesis not yet validated.

---

## 1. Technical Problem

Mineral exploration is a sequential, capital-constrained search process conducted under deep geological uncertainty. At any point in a campaign, a company holds an evidence set (drill results, geophysics, geochemistry, geological mapping) that is always incomplete relative to the true subsurface state. It must choose the next action — drill here, survey there, wait, stop — under a hard budget, knowing that the wrong choice can waste years and tens of millions of dollars, and that the right choice depends on information that does not yet exist.

In practice this decision is made by experienced geologists using judgment, heuristics ("drill the biggest anomaly," "follow the highest grade"), and internal company processes that are rarely made explicit, rarely quantify the value of the information being purchased by each dollar spent, and are essentially impossible to audit or replay after the fact.

## 2. Existing Approaches

- **Geostatistical / geological modeling** (kriging, implicit modeling, resource estimation software such as Leapfrog, Datamine, Micromine): estimates the spatial distribution of a variable (grade, lithology) from existing data. Does not by itself select the next action or value information.
- **Prospectivity mapping / mineral potential mapping** (weights-of-evidence, fuzzy logic, and increasingly ML classifiers trained on regional geoscience layers): ranks *where* mineralization is more likely at a regional scale. Typically a single-shot spatial prediction, not a sequential per-decision engine, and rarely tied to an explicit budget or action cost.
- **Value-of-Information (VOI) analysis in petroleum and mining economics**: a well-established decision-analysis technique (Howard 1966; widely used in oil & gas appraisal) for valuing an information-gathering action before committing capital. It is well known as a *technique* but is rarely implemented as an operational, repeatable engine coupled to a live geological belief model in hard-rock exploration; where it is used, it is typically a one-off spreadsheet exercise for a single decision, not a system that ingests evidence, updates belief, and re-evaluates repeatedly across a campaign.
- **Sequential decision-making / Bayesian optimization / bandit methods**: mature in other domains (drug discovery, engineering design, oilfield well placement research). Application to hard-rock mineral exploration decision support, integrated with exploration-specific economics and a temporally honest historical evaluation methodology, is not standard practice.

## 3. Technical Gap

No widely available system integrates, in one coherent computational loop and against a temporally honest historical record:

1. an explicit, updatable geological belief state over competing hypotheses,
2. a VOI-based valuation of candidate exploration actions,
3. exploration-specific economics (cost, budget, opportunity cost) applied to that valuation,
4. a sequential decision loop that can be replayed step-by-step against history, and
5. an evaluation methodology that compares the resulting recommendations against the actual historical decisions and against simple baselines, honestly reporting disagreement.

The gap is **integration and rigorous historical evaluation**, not the invention of Bayesian updating or VOI as mathematical objects.

## 4. MDEX Technical Hypothesis

`[UNPROVEN]` A computational system that (a) maintains an explicit probabilistic belief over competing geological hypotheses, (b) values candidate exploration actions by their expected reduction in decision-relevant uncertainty per unit cost, and (c) is evaluated exclusively against information that was actually available at each historical decision point, can produce exploration action recommendations that are *traceable, reproducible, and comparable* to historical human decisions and to simple baselines — and in some fraction of cases identify high-value actions that simple heuristics would not have prioritized.

MDEX does **not** claim to already out-perform experienced exploration geologists. The POC exists to generate the first honest evidence toward or against that hypothesis.

## 5. Critical Technical Function

> Given a historical exploration state (evidence available at time T, active geological hypotheses, and a constrained budget), rank the available exploration actions by expected decision value — combining hypothesis uncertainty, expected information gain, action cost, and expected economic consequence — and produce a recommended action together with its full rationale, assumptions, and evidence provenance.

This function is implemented in `src/mdex/decision_engine.py`, orchestrating the belief, information-value, and economic modules (Section 6).

## 6. System Architecture

See `docs/architecture.md` for the full diagram and module contracts. Summary of the loop:

```
Evidence (timestamped, provenance-tagged)
   -> Temporal Filter (firewall at decision time T)
   -> Belief Engine (posterior over H1..H4)
   -> Information Actions -> possible outcomes -> posterior beliefs
   -> Best available Terminal Decision (including hold = $0 outside option)
   -> Information Value Engine (decision-theoretic pre-posterior VOI)
   -> Economic Engine (cost, budget, terminal expected monetary value)
   -> Decision Engine (rank actions by expected decision value)
   -> Recommended Action + rationale
   -> [Replay] reveal next historical evidence -> new state T+1 -> repeat
```

## 7. Mathematical Concepts Used

- Discrete Bayesian updating over a finite hypothesis set (categorical posterior, likelihood functions authored per evidence type).
- Shannon entropy as the uncertainty measure over the hypothesis posterior.
- Value of Information (VOI): `VOI(I) = E_y[BestTerminalDecisionValue(posterior | y)] - BestTerminalDecisionValue(prior) - Cost(I)`, computed via discrete pre-posterior decision-theoretic calculation over enumerated evidence outcomes. Information actions purchase observations and are never evaluated as terminal payoff actions; `hold` is the zero-valued outside option.
- Expected monetary value (EMV) combining hypothesis-conditional economic payoff, probability, and cost.
- A simple single-step-lookahead ranking (VOI for information actions, direct EMV for terminal actions) used as the action-selection rule, explicitly `[ASSUMPTION]`-flagged as one reasonable rule among several (a full POMDP solve is out of scope for TRL 3 and is listed as TRL 4+ work).

## 8. Assumptions (global, POC-wide)

`[ASSUMPTION]` A 4-hypothesis discretization of geological system state is sufficient to demonstrate the decision architecture (Section 6.2 of the master prompt: H1 shallow/supergene, H2 deep hypogene/porphyry, H3 localized/non-economic, H4 insufficient evidence).
`[ASSUMPTION]` Evidence likelihoods (how strongly a given assay or geophysical result favors each hypothesis) are authored by the engineering team as illustrative conditional probability tables, not fitted to a large historical corpus — this is explicitly a TRL 3 simplification, documented per-instance in code and in `docs/OPEN_ISSUES.md`.
`[ASSUMPTION]` Economic parameters (drill cost per metre, assumed commodity price, discount rate) are configurable and, where a real historical figure is not documented, are marked as `[ASSUMPTION]` defaults in `configs/economics.yaml`, not presented as fact.

## 9. Limitations

- The belief-update likelihoods are hand-specified, not learned from a large labeled dataset — appropriate for demonstrating the architecture, not for production geological inference.
- Only one historical case (Oyu Tolgoi, one decision point) is reconstructed with real citations in this POC; broader validation requires more cases.
- The sequential decision rule is a myopic (one-step-lookahead) VOI/EMV ranking, not a full sequential (POMDP) optimum — sufficient to prove the loop, not to claim globally optimal sequencing.
- No live geophysical/geochemical data ingestion pipeline exists; ingestion is via structured files with a documented schema.
- The Oyu Tolgoi replay currently represents information actions and `hold`, but no calibrated post-information economic terminal decision beyond `hold`; its information-action VOI therefore remains cost-only. The analytical integration test validates the general terminal-decision pathway independently.

## 10. TRL 3 Target (this POC)

Analytical and experimental proof-of-concept: critical functions (belief update, VOI, economic evaluation, ranking, sequential replay) are implemented in code, exercised by automated tests, and run end-to-end on at least one reconstructed historical decision point with cited evidence, producing a documented, reproducible output.

## 11. TRL 4 Stretch Target

Component validation in a lab environment: the modules are integrated (not just unit-tested in isolation), validated against more than one historical case or scenario, and the sequential replay loop is demonstrated across multiple chained decision points with belief updates carried through. This POC provides partial TRL 4 evidence (see `docs/dtv/02_trl_evidence.md`) but does not claim TRL 4 is fully met — multi-case validation is listed as future work.

## 12. Proposed Validation Experiment

Reconstruct the exploration state immediately before Ivanhoe Mines' July 2001 decision to commit one of a small number of affordable deep diamond holes to the Southwest Oyu target (the historical antecedent of discovery hole OTD-150), using only publicly documented information dated on or before that decision point. Run MDEX, a historical-decision baseline, a "drill the best surface anomaly" baseline, and a random-feasible baseline, then reveal the real OTD-150 result to score all four retrospectively. Full design in `docs/dtv/05_validation_report.md` and `experiments/`.
