# Technology Brief — MDEX

## Problem
Exploration companies commit tens of millions of dollars per campaign to sequential decisions (drill here, survey there, hold, stop) made under deep geological uncertainty, using largely tacit, non-quantified, non-auditable judgment. No standard tool makes the value of the *next* piece of information explicit against its cost, or lets that judgment be replayed and scored against what history actually showed.

## Technology
MDEX is a decision-architecture system, not a geological predictor. It maintains an explicit, updatable probability distribution over competing geological hypotheses, values each candidate exploration action by its expected reduction in decision-relevant uncertainty (Value of Information) net of cost, enforces a hard budget, and produces a ranked, fully-reasoned recommendation with all assumptions and evidence provenance attached. It is built to be replayed chronologically against historical campaigns under a strict temporal information firewall — the recommendation at time T can never see information that only became available after T.

## Technical novelty
Not the individual mathematics (Bayesian updating and VOI are established techniques). The novelty asserted here is the **integration**: a single computational loop that couples geological belief, information valuation, exploration economics, and sequential replay, together with a provenance/temporal-firewall data model and an evaluation methodology that scores agreement/disagreement with real historical decisions rather than assuming superiority.

## Critical technical function
Given a historical exploration state and a constrained budget, rank candidate actions by expected decision value, with full rationale and evidence provenance. Implemented in `src/mdex/decision_engine.py`.

## Architecture
Evidence Store (temporal firewall) → Belief Engine (Bayesian) → Information Value Engine (VOI) + Economic Engine (EMV/budget) → Decision Engine (ranking) → Replay Engine (sequential) → Evaluation Engine. Full detail: `docs/architecture.md`.

## Why this is deep-tech
It requires genuine integration of probabilistic reasoning, decision theory, domain-specific exploration economics, and a temporally rigorous historical-evaluation methodology — none of which is captured by an LLM, a dashboard, or a CRUD application, and none of which is available today as an off-the-shelf, exploration-specific, historically-validated decision engine.

## Mining application
Supports exploration geologists and technical management in prioritizing next actions (drill targets, surveys, hold/stop decisions) under budget constraints, with an auditable rationale trail suitable for board- and investor-level review.

## Current maturity
TRL 3: critical functions implemented and demonstrated on one reconstructed historical decision point, with automated tests including the temporal-firewall proof. See `docs/dtv/02_trl_evidence.md`.

## Next technical milestones
1. Multi-case historical validation (2–3 additional deposits, including at least one documented non-discovery, to test whether MDEX correctly down-ranks poor targets).
2. Elicit or fit likelihood tables with domain-expert geologists rather than hand-authored placeholders.
3. Extend the decision rule from single-step-lookahead to a multi-step sequential (POMDP-style) optimization.
4. Pilot with a real active exploration program (with the operator's own data) under the same temporal-firewall discipline, evaluated prospectively rather than retrospectively.
