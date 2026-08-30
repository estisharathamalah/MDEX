# Technology Brief - MDEX

## Mineral Exploration Decision Engine

**Submission scope:** DTV Deep-Tech Ventures Program - TRL 3 proof-of-concept
**Current maturity claim:** TRL 3 demonstrated; TRL 4 not claimed.

## Executive Technology Statement

MDEX is a decision-intelligence engine for mineral exploration under geological and economic uncertainty. It does not replace a geologist or predict an orebody directly. Given admissible evidence at a defined exploration decision point, competing geological hypotheses, candidate actions, costs, and a constrained budget, it ranks the next action by expected decision value.

The implemented TRL-3 chain is:

```
Evidence -> Belief State -> Information Action -> Possible Outcomes
-> Posterior Belief -> Best Terminal Decision -> VOI -> Economic Decision
```

MDEX combines Bayesian belief updating, decision-theoretic Value of Information (VOI), exploration economics, sequential replay, and a provenance-controlled temporal information firewall.

## Problem

Exploration teams must repeatedly choose whether to drill, acquire geophysical or geochemical information, continue, hold, or stop while geological knowledge is incomplete and capital is constrained. The challenge is the interaction between competing interpretations, heterogeneous evidence, costly information acquisition, asymmetric outcomes, finite budgets, and changing beliefs.

MDEX addresses the computational decision layer connecting evidence, uncertainty, information acquisition, economics, and the next action. It does not claim that conventional geological tools or expert judgment are inadequate.

## Decision Model

At decision time $t$, MDEX maintains a belief state over explicit hypotheses using only evidence available at that time. For an information action $I$ with possible outcome $y$, it computes:

$$
VOI(I) = E_y[BestTerminalDecisionValue(posterior \mid y)] - BestTerminalDecisionValue(prior) - Cost(I)
$$

Information actions purchase observations and are not evaluated as terminal economic decisions. After each possible outcome, MDEX updates the posterior and selects the best available terminal decision. `hold` is the zero-valued outside option. Terminal decisions are evaluated with hypothesis-conditional economic payoff and budget feasibility.

The current model is a discrete, single-step-lookahead computational framework. It is not a POMDP, a production-grade mineral-economic model, or an operational drilling authority.

## Architecture And Integrity

The architecture comprises an Evidence Store, Belief Engine, Information Value Engine, Economic Engine, Decision Engine, Replay Engine, and Evaluation Engine. Each input has provenance, and historical evidence enters downstream computation through `EvidenceStore.as_of(T)`. Automated tests verify that information unavailable at $T$ cannot affect a decision at $T$.

The implementation supports action-specific terminal payoff models. All likelihood and economic parameters in the Oyu Tolgoi proof-of-concept are explicitly marked `ASSUMPTION` where they are not sourced historical facts.

## TRL-3 Evidence

The current suite contains 13 automated tests:

- 3 analytical VOI tests, including a manually calculable $5 decision-switch case;
- 7 core and integration tests, including information outcome -> posterior -> best terminal decision; and
- 3 temporal-firewall tests.

These tests demonstrate the computational critical function: Bayesian update, action-role separation, decision-theoretic pre-posterior VOI, budget constraints, ranking, replay reproducibility, and honest disagreement reporting. They do not validate geological prediction or real-world economic performance.

## Historical Demonstration: Oyu Tolgoi

The Oyu Tolgoi experiment is a historically grounded computational replay immediately before the July 2001 deep-drilling decision associated with OTD-150. Historical macro-context and the eventual outcome are documented. The discriminating per-site evidence is clearly marked `SYNTHETIC`; it is not presented as fact.

The current replay recommends `hold`, differing from the historical decision to drill Southwest Oyu. This is reported as a diagnostic model output, not as evidence that the historical geologists were wrong. In the replay, drilling and surveying are information actions and `hold` is the only represented post-information terminal decision. Consequently, information actions have no calibrated terminal-decision upside in that scenario and retain cost-only VOI. The analytical integration test independently verifies the general pathway in which information changes the terminal decision.

Accordingly, the Oyu Tolgoi case demonstrates operation of the computational architecture, not geological predictive superiority or a historically validated backtest.

## What Is And Is Not Demonstrated

**Demonstrated at TRL 3:** an auditable computational pipeline that values information by its expected impact on subsequent terminal decisions under uncertainty and economic constraints; provenance labeling; temporal isolation of historical evidence; reproducible replay; analytical VOI validation; and machine-readable outputs.

**Not demonstrated:** calibrated geological likelihoods, calibrated mining economics, generalization across deposits, prospective exploration-economic improvement, agreement with expert geologists, production integration, patentability, or TRL 4.

## Differentiation Hypothesis

MDEX is not positioned as "AI that finds copper." Its proposed differentiation is a provenance-controlled decision layer that makes explicit which exploration action is worth taking next and why under uncertainty and capital constraints. Bayesian inference and VOI are established techniques; any claim of architectural novelty or patentability remains subject to formal competitive and prior-art analysis.

## Next Validation Stage

The path toward TRL 4 is controlled empirical validation rather than feature expansion:

1. Add multiple documented historical cases, including a non-discovery.
2. Obtain domain-expert review or empirical calibration of hypotheses and likelihoods.
3. Replace illustrative economic parameters with appropriately sourced data.
4. Define and calibrate terminal economic decisions for each replay before interpreting information-action VOI as an economic result.
5. Conduct a prospective evaluation with an active exploration program while retaining temporal-firewall discipline.

## Bottom Line

MDEX is a TRL-3 research proof-of-concept, not a demonstrated mining prediction product. Its evidence supports a computational decision-theoretic pipeline capable of valuing information through its expected impact on subsequent terminal decisions, while preserving provenance, temporal integrity, reproducibility, and honest reporting of disagreement.

## Related Evidence

- `docs/01_technology_definition.md` - technology definition.
- `docs/architecture.md` - system architecture and module contracts.
- `docs/dtv/EVIDENCE_CLAIMS_MATRIX.md` - claim-by-claim evidence matrix.
- `docs/dtv/02_trl_evidence.md` - TRL evidence and roadmap.
- `docs/dtv/05_validation_report.md` - experimental validation and limitations.
- `docs/dtv/10_model_card.md` - model scope, risks, and intended use.
