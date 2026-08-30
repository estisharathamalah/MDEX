# MDEX Model Card

## 1. Model Details

**Model Name:** MDEX (Mineral Exploration Decision Engine)

**Model Type:** Sequential decision-support system with Bayesian belief updating and Value-of-Information (VOI) analysis

**Version:** TRL 3 Proof-of-Concept

**Developer:** [Your organization]

**Date Created:** 2024-2026

**Model Card Version:** 1.0

---

## 2. Intended Use

### Primary Use Case
Research demonstration of a computational system that:
- Maintains an explicit probabilistic belief over competing geological hypotheses
- Values information actions by their expected impact on the best available subsequent terminal decision, net of cost
- Produces traceable, reproducible exploration recommendations with full provenance documentation

### Intended Users
- Deep-tech investors and technical reviewers evaluating mineral exploration decision-support concepts
- Geotechnical researchers studying decision frameworks for capital-intensive exploration
- Development teams adapting this architecture for specific mining or exploration contexts

### Decision Context
Single-point-in-time evaluation of mineral exploration options under geological uncertainty, where:
- A fixed set of geological hypotheses are defined
- Available evidence is characterized by provenance and temporal availability
- A constrained exploration budget must be allocated
- The decision is evaluated against a small set of alternative baseline strategies

---

## 3. NOT Intended For

- **Operational drilling decisions:** Do not use this model directly to decide whether to drill real boreholes without expert geologist review and domain-specific calibration
- **Production systems:** This is not a production-ready exploration platform; it is a research artifact
- **Unvalidated hypothesis sets:** Do not assume the four geological hypotheses (H1–H4) are sufficient for any real deposit
- **Real economic valuation:** Payoff figures are illustrative [ASSUMPTION] defaults, not discounted cashflow valuations or real project economics
- **Multi-year campaign optimization:** The model uses single-step-lookahead VOI, not a full sequential (POMDP) solution for multi-period campaigns
- **Predictions of discovery:** The model does not claim to predict whether a given site will be discovered or become economic

---

## 4. Model Inputs

### Evidence
- **Provenance-tagged facts:** Historical geological, geochemical, and geophysical observations, each marked [FACT], [ASSUMPTION], [SYNTHETIC], or [MODEL OUTPUT]
- **Temporal metadata:** Each evidence item carries `date_observed` and `date_available`, enforced by a structurally mandatory temporal firewall
- **Confidence scores:** Analyst-assigned confidence [0, 1] per item, used to soften likelihood functions (not a posterior probability)

### Belief State
- Discrete probability distribution over four competing geological hypotheses
- Initialized as a uniform prior or prior belief from upstream analysis
- Updated via discrete Bayes rule as evidence is introduced

### Action Set
- Information actions (drill sites, geophysical surveys, sampling) and terminal economic decisions (for example develop, farm-out, abandon, or hold)
- Each action specifies: cost (with provenance), outcome scenarios (enumerated, with likelihoods per hypothesis), and an explicit or legacy-derived action role
- Outcome scenarios are [ASSUMPTION] discretizations of continuous real-world assay/geophysical results

### Economic Model
- Hypothesis-conditional payoff table (USD): expected economic value if that hypothesis proves true
- Exploration budget and budget constraints
- All payoff and cost figures are [ASSUMPTION] illustrative defaults, not real project valuations

---

## 5. Model Outputs

### Primary Output: Action Ranking
For each candidate action:
- **Total value (USD):** Either VOI (for information-gathering actions) or EMV − cost (for terminal actions)
- **Feasibility:** Whether cost is within remaining budget (hard constraint)
- **Decomposition:** VOI and EMV components, uncertainty reduction (bits), rationale, assumptions, evidence provenance

### Secondary Outputs
- **Belief posterior:** Updated probability distribution over hypotheses
- **Entropy (bits):** Shannon entropy of posterior (uncertainty measure)
- **Recommendation:** Single top-ranked feasible action
- **Evaluation:** Comparison against historical decision and baseline heuristics (if evaluation mode is invoked)

---

## 6. Model Architecture

```
Evidence Store (with temporal firewall)
    ↓
Temporal Filter (at decision time T)
    ↓
Bayesian Belief Engine (discrete update over H1..H4)
    ↓
    Information Actions -> outcomes -> posterior -> best Terminal Decision
    ↓
    Information Value Engine (pre-posterior VOI calculation)
    ↓
Economic Engine (cost, budget, payoffs)
    ↓
Decision Engine (ranking by value, accounting for feasibility)
    ↓
Replay Engine (sequential replay for validation)
    ↓
Evaluation Engine (comparison with history and baselines)
```

**Key Constraint:** The temporal firewall prevents any evidence dated after decision time T from influencing the decision. This is enforced structurally and tested.

---

## 7. Known Limitations

### Data & Calibration
- **Hypothesis set:** Four hypotheses (H1–H4) are illustrative; no evidence that this discretization is geologically sufficient or appropriate for real deposits
- **Likelihood tables:** Hand-authored [ASSUMPTION] conditional probability tables, not fitted to a large historical corpus or expert-elicited via formal methods
- **Payoff estimates:** Order-of-magnitude [ASSUMPTION] illustrative figures; no real discounted cashflow or economic feasibility modeling
- **Single case validation:** Only one historical scenario (Oyu Tolgoi, pre-OTD-150, July 2001) reconstructed with cited macro-facts; per-site discriminating evidence is synthetic

### Algorithmic Simplifications
- **Belief update:** Assumes evidence likelihoods can be authored per evidence type and per hypothesis; does not learn from data
- **VOI calculation:** Single-step-lookahead discrete pre-posterior VOI; does not solve a full multi-period sequential (POMDP) optimization
- **Action roles:** Information actions are not terminal payoff actions. VOI is `E[best terminal value after outcome] - best terminal value now - information cost`; `hold` is always the zero-valued outside option.
- **Oyu Tolgoi terminal set:** The replay currently has only `hold` as a post-information terminal action, so it cannot establish an economic benefit from information until calibrated terminal decisions are supplied.
- **No geophysical/economic data pipeline:** Ingestion is via structured JSON; no live integration with assay databases, geophysical sensors, or market data

### Validation & Testing
- **Test coverage:** 13 automated tests covering core modules, including an analytical information-outcome-to-terminal-decision integration path; no multi-case historical or domain-expert blind backtest
- **Baseline strategies:** Four simple heuristics compared; does not benchmark against published exploration decision frameworks or industry best practices
- **Regret analysis:** No regret or opportunity-cost quantification against a true optimal policy (which is unknown)

---

## 8. Failure Modes & Mitigation

| Failure Mode | Cause | Impact | Mitigation |
|---|---|---|---|
| Wrong hypothesis set | Hypotheses do not span true system state | Recommendation biased toward wrong targets | Elicit hypothesis set from domain experts; validate on multiple cases |
| Miscalibrated likelihoods | Hand-authored probabilities do not reflect reality | Belief updates inaccurate; poor action ranking | Fit likelihoods to historical assay/geophysical data; conduct sensitivity analysis |
| Unrealistic payoffs | Payoff table does not reflect real economics | Actions ranked by incorrect economic value | Source real cost & commodity price data; model time value of money & optionality |
| Incomplete evidence | Critical geological information absent at decision time | Posterior belief false; recommendation misled | Ensure evidence selection covers all decision-relevant geological layers |
| Model misspecification | VOI, EMV, or ranking formula does not match decision maker's actual preferences | Recommendation incoherent with true utility | Validate decision framework against expert judgment; elicit utility function |
| Outcome scenario errors | Discretized scenarios do not cover true outcomes; outcome probabilities wrong | VOI calculation inaccurate | Refine scenarios via Monte Carlo or continuous-outcome approximation |

---

## 9. Validation Status & Evidence

### TRL 3 (Demonstrated)
- ✅ Core algorithms (Bayesian belief, VOI, economics, ranking, replay) implemented in code
- ✅ 13 automated tests pass, including mandatory temporal firewall proof and an analytical decision-switch VOI integration test
- ✅ End-to-end pipeline runs on one historically-grounded scenario (Oyu Tolgoi, pre-OTD-150)
- ✅ Output is documented, reproducible, and disagreement with history is reported honestly

### Partial TRL 4 Evidence
- ✅ Integrated pipeline (not just unit-tested modules)
- ✅ Reproducibility proven by test suite
- ⚠️ Only one historical case validated
- ❌ No multi-case blind backtest or external expert review

### TRL 5+ (Not Claimed)
- ❌ No market engagement or customer signals
- ❌ No production deployment or field trials
- ❌ No regulatory validation or industry certification

---

## 10. Recommended Next Steps for TRL 4+

1. **Multi-case historical validation:** Add 2–3 additional documented historical exploration campaigns (ideally with diverse deposit types and at least one documented non-discovery) to test whether MDEX correctly ranks them retrospectively

2. **Likelihood calibration:** Elicit geological probability estimates from domain experts via formal methods (e.g., SHELF), or fit likelihoods to a large historical corpus of assay & geophysical results

3. **Economic refinement:** Source real circa-2001 Gobi Desert drilling costs, commodity prices, and discounted cashflow methods; replace illustrative payoffs with realistic project economics

4. **Hypothesis validation:** Conduct expert review of the four-hypothesis set; consider whether additional hypotheses or hierarchical hypothesis structures are needed

5. **Sequential optimization:** Prototype a multi-step lookahead or POMDP formulation to optimize across an entire exploration campaign, not just a single decision point

6. **Sensitivity & robustness analysis:** Systematic testing of how recommendations change with perturbations in likelihoods, payoffs, costs, and budget

---

## 11. Ethical Considerations

- **Transparency:** All data and assumptions are provenance-tagged. No synthetic data is silently merged with historical data
- **Reproducibility:** Full source code, test suite, and historical reconstruction are provided. All outputs can be traced back to inputs
- **Honest evaluation:** Disagreement between MDEX and historical decisions is reported, not suppressed
- **Appropriate humility:** The model does not claim to beat experienced geologists. Its purpose is to provide a decision framework for research and validation

---

## 12. Maintenance & Contact

**Current Status:** TRL 3 research artifact. Not actively maintained for production use.

**For inquiries:** [Contact information / project repository]

**Version History:**
- v1.0 (2024–2026): Initial TRL 3 proof-of-concept

---

## References

- Howard, R. A. (1966). *Information Value Theory.* IEEE Transactions on Systems Science and Cybernetics.
- Raiffa, H., Winter, R. F. (1997). *Decision Analysis: Introductory Lectures on Choices under Uncertainty.* Cambridge University Press.
- [Other relevant citations on VOI, exploration decision-making, Bayesian updating, etc.]

---

**Model Card Reviewed:** [Date]  
**Reviewed By:** [Name, Title]
