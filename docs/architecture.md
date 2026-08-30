# MDEX Architecture

## 1. Component Diagram

```
                         ┌─────────────────────────┐
                         │   Evidence Store         │
                         │  (evidence.py)           │
                         │  - drill/assay/geophys/  │
                         │    geochem/observation   │
                         │  - date, avail_date,     │
                         │    source, confidence    │
                         └────────────┬─────────────┘
                                      │  temporal filter (as_of=T)
                                      ▼
                         ┌─────────────────────────┐
                         │   Belief Engine          │
                         │  (belief.py)             │
                         │  discrete Bayesian       │
                         │  posterior over H1..H4   │
                         └────────────┬─────────────┘
                                      │ posterior, entropy
                                      ▼
              ┌───────────────────────┴────────────────────────┐
              ▼                                                 ▼
┌───────────────────────────┐                    ┌───────────────────────────┐
│ Information Value Engine  │                    │  Economic Engine          │
│ (information_value.py)    │                    │  (economics.py)           │
│ EVOI per candidate action │                    │  cost, budget, EMV        │
└──────────────┬─────────────┘                   └──────────────┬────────────┘
               └───────────────────────┬──────────────────────────┘
                                        ▼
                         ┌─────────────────────────┐
                         │   Decision Engine        │
                         │  (decision_engine.py)    │
                         │  rank actions by         │
                         │  expected decision value │
                         └────────────┬─────────────┘
                                      │ recommendation + rationale
                                      ▼
                         ┌─────────────────────────┐
                         │  Replay Engine           │
                         │  (replay.py)             │
                         │  T0 -> action -> reveal  │
                         │  evidence -> T1 -> ...   │
                         └────────────┬─────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  Evaluation Engine       │
                         │  (evaluation.py)         │
                         │  vs. historical decision │
                         │  vs. baselines, regret   │
                         └─────────────────────────┘
```

## 2. Module Contracts

### `evidence.py`
- `EvidenceItem`: dataclass with `id, kind, description, value(s), date_observed, date_available, source, confidence (FACT/ASSUMPTION/SYNTHETIC), spatial_ref`.
- `EvidenceStore.as_of(t)`: **the temporal firewall**. Returns only items with `date_available <= t`. This is the single choke point through which all downstream modules must receive evidence — no other code path may read the raw store.

### `belief.py`
- `Hypothesis` enum: H1_SHALLOW_SUPERGENE, H2_DEEP_HYPOGENE, H3_LOCALIZED_NONECONOMIC, H4_INSUFFICIENT_EVIDENCE.
- `BeliefState`: probability vector over the 4 hypotheses + entropy.
- `update(prior, evidence_item, likelihood_table) -> posterior`: standard discrete Bayes rule. Likelihood tables are explicit, inspectable, and versioned in `configs/likelihoods.yaml`, each entry tagged `[ASSUMPTION]`.

### `information_value.py`
- `enumerate_outcomes(action, belief)`: for a candidate action, enumerate plausible evidence outcomes and their probabilities under current belief (a discretized pre-posterior).
- `expected_uncertainty_reduction(action, belief) -> float`: expected drop in entropy.
- `evoi(action, belief, econ_model) -> float`: expected value of information in decision-value units (monetary, via the economic engine's payoff function), following the standard pre-posterior VOI construction.

### `economics.py`
- `ActionCost`: cost, duration, and a `provenance` tag (historical figure vs. `[ASSUMPTION]` default from `configs/economics.yaml`).
- `expected_monetary_value(belief, payoff_table, action_cost, budget) -> float`.
- `feasible(action_cost, remaining_budget) -> bool`: hard budget constraint enforcement.

### `decision_engine.py`
- `rank_actions(belief, candidate_actions, econ_model) -> List[ActionEvaluation]`, each item carrying: action, EVOI, cost, EMV, expected_decision_value (a documented combination rule), uncertainty, rationale (auto-generated text trace), assumptions used, evidence provenance list.
- `recommend(...) -> ActionEvaluation`: top of the ranked list subject to budget feasibility.

### `replay.py`
- `ReplayEngine.run(evidence_store, decision_dates, budget)`: iterates the historical decision points chronologically, at each step calling `as_of`, `update`, `rank_actions`, `recommend`, then revealing the next chronological evidence batch and advancing state. Produces a full, serializable decision trace for reproducibility.

### `evaluation.py`
- `compare(trace, historical_decisions, baselines) -> EvaluationReport`: computes regret, information efficiency, economic efficiency, and (if enough decision points exist) calibration, per Section 11 of the master prompt.

## 3. Why this satisfies the critical technical function

The critical function (Section 5 of `01_technology_definition.md`) requires ranking actions by expected decision value under uncertainty, cost, and budget, given only information available at T. The temporal firewall in `evidence.py` enforces the "at T" constraint structurally (not by convention), `belief.py` supplies the uncertainty term, `information_value.py` supplies the information-gain term, `economics.py` supplies cost/budget/economic terms, and `decision_engine.py` is the single point where all four are combined into a ranked, explainable output. This was checked against the master prompt's Section 5 requirements before implementation began, per the mandated internal-verification step.
