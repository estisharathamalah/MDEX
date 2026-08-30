# TRL Evidence — MDEX

## TRL 3 — Analytical and experimental critical function proof-of-concept

**Claim: MET.**

| Requirement | Evidence |
|---|---|
| Critical functions demonstrated | `src/mdex/{evidence,belief,information_value,economics,decision_engine,replay,evaluation}.py` implement the full loop described in `docs/architecture.md` |
| Experimental validation | `experiments/run_oyu_tolgoi_experiment.py` runs the full pipeline end-to-end against a historically-grounded decision point and produces a reproducible, machine-readable result (`results/oyu_tolgoi_experiment_result.json`) |
| Analytical results | Belief posterior, entropy, VOI, EMV, and total value are all computed and reported per candidate action, with rationale text |
| Test evidence | 12 automated tests pass: `tests/test_voi_correctness.py` (3 mathematical VOI ground-truth tests including positive/negative VOI scenarios), `tests/test_core_engine.py` (6 tests covering Bayesian update, budget constraints, action ranking, reproducibility), `tests/test_temporal_firewall.py` (3 tests enforcing temporal integrity). These cover the temporal firewall (mandatory), VOI mathematical correctness, Bayesian update correctness, budget-constraint enforcement, action ranking, sequential-replay reproducibility, and baseline/disagreement reporting |

## TRL 4 — Component validation in a laboratory environment

**Claim: PARTIALLY MET. TRL 3 fully demonstrated; TRL 4 roadmap defined below.**

What is already TRL-4-consistent:
- The modules are genuinely integrated, not just unit-tested in isolation — `run_oyu_tolgoi_experiment.py` exercises the belief, VOI, economics, decision, and evaluation modules together in one run, and `ReplayEngine` demonstrates the sequential state-transition architecture (`tests/test_core_engine.py::test_sequential_replay_is_reproducible`).
- Reproducibility is demonstrated (identical inputs produce identical outputs, verified by test).

What is missing for a full TRL 4 claim:
- Only one historical case and one decision point have been validated end-to-end. TRL 4 in this domain should mean the architecture holds up across multiple deposits/decision types, not one.
- The sequential replay is demonstrated structurally (the engine supports chaining decision points) but this experiment only exercises a single step; a multi-step chained replay across several decision dates for one campaign is the next concrete milestone.
- Likelihood tables and economic parameters are hand-authored `[ASSUMPTION]`s rather than expert-elicited or corpus-fitted values.

**Honest summary: TRL 3 demonstrated; TRL 4 roadmap defined.** We do not claim TRL 4 is fully met.
