# DTV Evidence & Claims Matrix

**Purpose:** Map every technical, commercial, geological, TRL, and IP claim in MDEX to its supporting evidence, assess confidence level, identify gaps, and determine positioning strategy for DTV submission.

**Note:** This is an internal strategic document. Not all items appear in the pitch; some are Technical Appendix territory. The matrix helps us know which claims we can defend and which need caveats or omission.

---

## A. MATHEMATICAL & ALGORITHMIC CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Bayesian belief update is correctly implemented | Technical | Unit test + code review | `tests/test_core_engine.py::test_bayesian_update_shifts_posterior_toward_favored_hypothesis` | PROVEN | FACT | "How is normalization handled?" | None | ✅ Brief |
| A2 | Posterior probabilities remain normalized (sum=1) | Technical | Unit test | `tests/test_core_engine.py::test_posterior_normalizes_and_entropy_bounds` | PROVEN | FACT | "What if numerical rounding breaks normalization?" | Should add tolerance bounds test | ⚠️ Appendix |
| A3 | VOI formula is decision-theoretically correct | Technical | Analytical $5 ground-truth test + Howard (1966) citation | `tests/test_voi_correctness.py::test_voi_positive_with_decision_change_ground_truth` + `docs/01_technology_definition.md` | PROVEN | FACT | "Why not just use uncertainty reduction?" | Need to explain why EMV-weighted VOI is better | ✅ Core |
| A4 | VOI = -cost when information has no decision value | Technical | Analytical test | `tests/test_voi_correctness.py::test_voi_is_negative_when_information_has_no_decision_value` | PROVEN | FACT | "Doesn't cost-only harm exploration?" | Explain that "don't drill" is a valid recommendation | ✅ Core |
| A5 | VOI respects budget constraints | Technical | Unit test | `tests/test_voi_correctness.py::test_voi_respects_budget_constraint` | PROVEN | FACT | "What if budget increases?" | Single-budget scenario only; multi-period is TRL 4 | ⚠️ Appendix |
| A6 | Temporal firewall prevents future information leakage | Technical | 3 unit tests + structural design | `tests/test_temporal_firewall.py` | PROVEN | FACT | "Can the firewall be bypassed?" | Explain architecture: `EvidenceStore.as_of(T)` is only entry point | ✅ Core |
| A7 | Deterministic replay: identical inputs → identical outputs | Technical | Unit test | `tests/test_core_engine.py::test_sequential_replay_is_reproducible` | PROVEN | FACT | "What about floating-point rounding?" | Acceptable tolerance; not claimed bit-for-bit | ⚠️ Appendix |
| A8 | Action ranking by value is correctly ordered | Technical | Unit test | `tests/test_core_engine.py::test_action_ranking_respects_budget_feasibility` | PROVEN | FACT | "What if values are within noise margin?" | Explain precision limits | ⚠️ Appendix |
| A9 | Terminal actions are separated from information actions | Technical | Architectural assertion + code review | `src/mdex/information_value.py` (assertion at line ~130) | PROVEN | FACT | "Why this separation?" | Prevents double-counting: info shouldn't receive terminal payoffs | ✅ Core |

---

## B. HISTORICAL VALIDATION CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| B1 | Oyu Tolgoi pre-OTD-150 decision can be reconstructed | Historical | Macro-level facts from Turquoise Hill / Ivanhoe press release + SEC filings | `data/historical/oyu_tolgoi_facts.json` + `experiments/run_oyu_tolgoi_experiment.py` + `docs/DATA_PROVENANCE.md` | PARTIALLY PROVEN | FACT (macro context), SYNTHETIC (site-level evidence) | "Is your 2001 data public or proprietary?" | Macro context is public; per-site discriminating evidence is synthetic (clearly tagged) | ✅ With caveat |
| B2 | OTD-150 was drilled to 590m and intersected economic-grade mineralization | Historical | News release 2001-07-17 | `experiments/run_oyu_tolgoi_experiment.py` (stdout) | PROVEN | FACT | "Any doubt about this outcome?" | None; outcome is documented | ✅ Context |
| B3 | MDEX recommendation (hold) differs from historical (drill_Southwest) | Experimental | Direct pipeline output | `results/oyu_tolgoi_experiment_result.json` + `experiments/run_oyu_tolgoi_experiment.py` | PROVEN | MODEL OUTPUT | "Why does MDEX disagree?" | Explain: belief + assumed payoffs + VOI calculation lead to different ranking | ✅ Core |
| B4 | Disagreement is reported honestly, not suppressed | Design | Code review: `evaluation.py` always reports baseline comparison | `src/mdex/evaluation.py::build_report()` | PROVEN | FACT | "Don't you want to hide bad results?" | Explain: transparency is core to defensibility | ✅ Differentiator |
| B5 | Oyu Tolgoi case generalizes beyond this one site | Design | **NOT TESTED** | None | UNPROVEN | ASSUMPTION | "How do you know this works elsewhere?" | This is TRL 4 work: need 2-3 additional historical cases | ❌ Do not claim |

---

## C. GEOLOGICAL & DOMAIN CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| C1 | Four geological hypotheses are relevant for deep-mineral exploration decisions | Domain | Domain knowledge + literature | `src/mdex/belief.py` + `docs/01_technology_definition.md` | SUPPORTED | ASSUMPTION | "Why four? Why these four?" | Not empirically validated; selected for POC illustrousness | ⚠️ Appendix |
| C2 | Evidence likelihoods P(evidence \| hypothesis) are geologically sound | Domain | Hand-authored, cited in geoscience reasoning | `src/mdex/information_value.py` (outcome scenarios) + `data/synthetic/candidate_site_indications.json` | PARTIALLY PROVEN | ASSUMPTION | "Who certified these likelihoods?" | They are plausible but not fitted to real data; TRL 4 requires expert elicitation or corpus fitting | ⚠️ Appendix |
| C3 | Hypothesis payoffs reflect real economic incentives | Domain | Order-of-magnitude defaults from mining economics literature | `configs/economics.yaml` | PARTIALLY PROVEN | ASSUMPTION | "Are these real 2001 costs?" | Illustrative; real data required for TRL 4 | ⚠️ Appendix |
| C4 | MDEX recommendations align with geologist intuition | Domain | **NOT TESTED** | None | UNPROVEN | UNKNOWN | "Did you ask any geologists?" | Not in scope for TRL 3; recommendation for TRL 4 | ❌ Do not claim |
| C5 | MDEX would improve exploration ROI | Business | **NOT MEASURED** | None | UNPROVEN | HYPOTHESIS | "Do you have case studies showing upside?" | No; this is the ultimate validation goal, not a claim | ❌ Do not claim |

---

## D. ARCHITECTURE & DESIGN CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Temporal firewall is structurally enforced, not procedural | Architecture | Code architecture: `EvidenceStore.as_of(T)` is only entry point to historical evidence | `src/mdex/evidence.py` + `tests/test_temporal_firewall.py` | PROVEN | FACT | "Could someone bypass the firewall?" | Explain: no other code path reads raw store; firewall is mandatory | ✅ Core differentiator |
| D2 | Provenance metadata is attached to all inputs | Design | Code review: every `EvidenceItem`, `ActionCost`, parameter carries `provenance: {FACT, ASSUMPTION, SYNTHETIC}` tag | `src/mdex/evidence.py` + `src/mdex/economics.py` + entire codebase | PROVEN | FACT | "How do users know what to trust?" | Transparency-first design: every datum is labeled | ✅ Core |
| D3 | Single-step-lookahead VOI is appropriate for TRL 3 | Design | Documented limitation + roadmap for POMDP as TRL 4 work | `docs/OPEN_ISSUES.md` + `docs/dtv/02_trl_evidence.md` | SUPPORTED | ASSUMPTION | "Isn't single-step myopic?" | Yes; acknowledged; multi-step is TRL 4+ | ✅ Honest limitation |
| D4 | Sequential replay architecture supports future multi-case validation | Design | Code review: `ReplayEngine` chains decision points | `src/mdex/replay.py` | PROVEN | FACT | "Can this scale to 100 decision points?" | Structurally yes; tested on single point; untested at scale | ⚠️ Appendix |
| D5 | All outputs are machine-readable JSON | Design | Code review + output file | `results/oyu_tolgoi_experiment_result.json` | PROVEN | FACT | "Why JSON?" | Standards compliance; enables downstream integration | ✅ Brief |

---

## E. TRL CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| E1 | TRL 3 is demonstrated: all critical functions integrated | TRL | Full pipeline runs end-to-end; 12 tests pass | `experiments/run_oyu_tolgoi_experiment.py` + all test files | PROVEN | FACT | "What makes this TRL 3 not TRL 2?" | Integration + reproducibility + analytical validation | ✅ Core |
| E2 | TRL 4 is NOT claimed as fully met | TRL | Honest caveat in `docs/dtv/02_trl_evidence.md` | `docs/dtv/02_trl_evidence.md` section "Partial TRL 4 Evidence" | PROVEN | FACT | "Why aren't you at TRL 4?" | Only one case; expert/calibration validation absent; roadmap clear | ✅ Transparency |
| E3 | Multi-case validation is the principal TRL 4 gateway | TRL | Roadmap + analysis | `docs/OPEN_ISSUES.md` + `docs/dtv/02_trl_evidence.md` | SUPPORTED | FACT | "How many cases do you need?" | Recommend 3-5 to begin claiming robustness; 1 is TRL 3 sufficient | ✅ Roadmap |
| E4 | TRL 5 (market engagement) is out of scope | TRL | Explicit non-claim | `docs/dtv/04_market.md` | PROVEN | FACT | "Will mining companies use this?" | Unknown; market validation is TRL 5 future work | ✅ Honest |

---

## F. IP & DEFENSIBILITY CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| F1 | Temporal firewall + provenance metadata are novel in mining tech stack | IP | Patent landscape is not analyzed; based on domain knowledge | `docs/dtv/03_ip_defensibility.md` | SUPPORTED | ASSUMPTION | "Has anyone patented this before?" | Honest caveat: no formal prior-art search conducted | ⚠️ Appendix with caveat |
| F2 | Bayesian belief + VOI ranking is standard, not novel | IP | Reference Howard (1966) + literature | `docs/01_technology_definition.md` | PROVEN | FACT | "So the math is boring?" | Correct; novelty is in architecture + temporal integrity, not algorithm | ✅ Reframe |
| F3 | Code is open-source (MIT/Apache) for transparency | IP | License choice (to be finalized) | TBD | PLANNED | ASSUMPTION | "Will you open-source this?" | Yes; transparency builds trust; recommend MIT or Apache 2.0 | ✅ Advantage |
| F4 | No major dependencies conflict with mining/defense sectors | IP | Code review: Python stdlib + scientific stack only | `requirements.txt` / setup.py | PLANNED | ASSUMPTION | "Will defense/export control restrict this?" | Standard Python stack; no specialized crypto or ML models; low risk | ⚠️ Verify |

---

## G. VALIDATION & TESTING CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| G1 | 12 automated tests cover critical functions | Validation | Test suite + CI readiness | `tests/*.py` + commit log | PROVEN | FACT | "What about edge cases?" | List edge cases; some untested (e.g., zero budget) | ✅ With scope |
| G2 | Test coverage includes mathematical correctness proofs | Validation | Ground-truth VOI tests with known analytical answers | `tests/test_voi_correctness.py` | PROVEN | FACT | "Why test with synthetic values?" | Explain: ground-truth testing validates the formula itself | ✅ Strength |
| G3 | Temporal firewall is tested structurally and functionally | Validation | 3 tests in `test_temporal_firewall.py` | `tests/test_temporal_firewall.py` | PROVEN | FACT | "Could bugs hide in the firewall logic?" | Explain: boolean logic tested; future work: fuzzing, property-based testing | ⚠️ Appendix |
| G4 | No external AI/ML model is used (all symbolic logic) | Design | Code review: all logic hand-written, no neural networks or sklearn | Entire `src/mdex/` | PROVEN | FACT | "Doesn't ML solve this better?" | Explain: symbolic logic is interpretable; ML would obscure provenance | ✅ Advantage |

---

## H. COMMERCIAL & MARKET CLAIMS

| # | Claim | Type | Current Evidence | Location | Confidence | Provenance | Likely Q&A | Gap | Pitch? |
|---|---|---|---|---|---|---|---|---|---|
| H1 | Exploration decision-making is capital-intensive and uncertain | Market | Industry knowledge + public data | `docs/dtv/04_market.md` | SUPPORTED | FACT | "How big is the market?" | List TAM/SAM estimates; cite analyst reports | ✅ Context |
| H2 | Exploration teams need decision-support tools | Market | Industry interviews (or lack thereof) | `docs/dtv/04_market.md` | SUPPORTED | ASSUMPTION | "Did you talk to geologists?" | **GAP**: No customer discovery conducted yet | ❌ Do not claim ownership; frame as hypothesis |
| H3 | Customers will pay for MDEX | Market | **NO EVIDENCE** | None | UNPROVEN | HYPOTHESIS | "What's your go-to-market strategy?" | Unknown; this is TRL 5 validation | ❌ Do not claim |
| H4 | Competitors (commercial software, consultants) can be differentiated | Competitive | Not analyzed | `docs/dtv/04_market.md` | UNPROVEN | ASSUMPTION | "Who are your competitors?" | Honest answer: don't know; temporal firewall + provenance are differentiators if novel | ⚠️ Appendix |
| H5 | $10M+ TAM in mineral exploration software | Market | Industry estimates | `docs/dtv/04_market.md` | PARTIALLY PROVEN | ASSUMPTION | "Citation?" | Cite: Frost & Sullivan mining software market; breakout numbers unclear | ✅ Context |

---

## I. RISK & MITIGATION

| # | Risk | Likelihood | Impact | Current Mitigation | Residual Risk |
|---|---|---|---|---|---|
| R1 | Geological likelihoods are off → MDEX recommendations are wrong | Medium | High | Clearly tag as [ASSUMPTION]; roadmap: expert elicitation + corpus fitting for TRL 4 | Medium |
| R2 | One historical case is insufficient to generalize | High | Medium | Acknowledge TRL 3 limitation; plan 2-3 additional cases for TRL 4 | Medium |
| R3 | Economic payoff table doesn't reflect real mining capital structures | Medium | High | Tag as [ASSUMPTION]; roadmap: source real 2001 drilling costs and commodity prices | Medium |
| R4 | Temporal firewall is bypassed by future developers | Low | Critical | Structural enforcement + 3 unit tests; add comment warnings to code; document violation as violation | Low |
| R5 | LLM reviewer asks "Why isn't this just supervised learning?" | Medium | Low | Explain: provenance + temporal integrity are interpretability requirements; ML obscures these | Low |
| R6 | Patent office rejects application; "Bayesian inference + VOI is prior art" | Medium | Medium | Honest: likely true; differentiation is architecture + temporal firewall, not algorithm | Medium |
| R7 | Geologist consultant says "this is too simplified" | High | Low | Agree: it's TRL 3; explicitly list geological simplifications (4 hypotheses, hand-authored likelihoods, etc.) | Low |
| R8 | Customer asks "Will you integrate with our data lake?" | Medium | Medium | Roadmap item; not in TRL 3 scope; highlight JSON output + modularity | Low |

---

## J. STRATEGIC POSITIONING MATRIX

**For each claim, decide:**

| Claim Category | Should appear in Pitch? | Should appear in Technical Appendix? | Should be public caveat? | Strategy |
|---|---|---|---|---|
| A1-A9 (Math & Algorithms) | A1, A3, A4, A6, A9 → YES | A2, A5, A7, A8 → YES | All math is correct, but TRL 3 scope | Lead with: "decision-theoretically correct VOI with temporal integrity" |
| B1-B5 (Historical) | B1, B2, B3, B4 → YES (with caveat) | B5 → NO | "One case illustrative, not definitive" | Frame: "Historically grounded proof-of-concept, not backtested across portfolio" |
| C1-C5 (Geological) | None → NO | C1, C2, C3 → YES | "Geological hypotheses are illustrative; likelihoods are ASSUMPTION" | Say: "Computational architecture + decision method are validated; geological inputs require domain expertise" |
| D1-D5 (Architecture) | D1, D2 → YES | D3, D4, D5 → YES | "Single-step lookahead is TRL 3 limitation" | Lead with: "Temporal firewall + provenance are architecturally novel and auditable" |
| E1-E4 (TRL) | E1, E2 → YES | E3, E4 → YES | "TRL 3 claimed; TRL 4+ roadmap clear" | Frame: "Proved critical functions; transparent about limitations" |
| F1-F4 (IP) | F2, F3 → Maybe | F1, F4 → YES | "No formal IP search; Bayesian inference is standard" | Caveat: transparency > aggressive IP claims |
| G1-G4 (Testing) | G1, G2, G4 → YES | G3 → YES | "Test scope is documented" | Showcase: "Mathematical correctness proven with ground-truth tests" |
| H1-H5 (Market) | H1 → Maybe | H2, H3, H4, H5 → YES | "Market validation not conducted; hypothesis phase" | Say: "If market hypothesis holds, TAM is substantial; DTV can help prove it" |

---

## K. RECOMMENDED PITCH NARRATIVE

**Opening:**
> MDEX is a provenance-controlled, temporally-auditable decision-intelligence engine for mineral exploration under uncertainty. It maintains explicit geological beliefs, values information by its decision-theoretic impact, prevents future-information leakage into historical decisions, and ranks exploration actions under economic constraints.

**Strengths to emphasize:**
1. **Temporal Integrity**: Structural firewall + 3 unit tests prove no future data pollutes historical decisions. Differentiator vs. other mining AI.
2. **Interpretability**: Every input is provenance-tagged (FACT, ASSUMPTION, SYNTHETIC). Every output is traceable to evidence. No black-box ML.
3. **Mathematical Correctness**: VOI formula is proven correct via ground-truth $5 test. Separates information-gathering value from terminal payoff.
4. **Honest Disagreement**: Oyu Tolgoi case shows MDEX can disagree with history — and we report it honestly instead of gaming the output.

**Honest Limitations:**
1. Single historical case (TRL 3); multi-case validation is TRL 4 roadmap.
2. Geological likelihoods are hand-authored [ASSUMPTION]s; expert elicitation / corpus fitting required for TRL 4.
3. Economic parameters are illustrative; real mining cost/price data required.
4. Single-step-lookahead VOI; full POMDP is TRL 4+ work.

**Why this matters for DTV:**
- Temporal firewall + provenance are novel in mining decision support (if not patented elsewhere).
- One fully-integrated, reproducible proof-of-concept with automated tests.
- Clear roadmap to TRL 4: 2-3 more cases + expert geological calibration + real economics.
- Defensible technical foundation for customer engagement (DTV can help fund validation).

---

## L. NEXT ACTIONS (Pre-Submission)

- [ ] Verify no factual errors in Evidence column
- [ ] Confirm test locations are accurate
- [ ] Add customer discovery stub (interviews with geologists, exploration teams)
- [ ] Identify 2 additional historical cases for TRL 4 roadmap (one success, one failure/non-discovery)
- [ ] Map gaps to DTV funding scope (which gaps could DTV help close?)
- [ ] Review with technical advisor (geologist or mining engineer) to catch domain errors
- [ ] Prepare Technical Appendix section-by-section from "Appendix" items in matrix
- [ ] Draft pitch narrative using K section
- [ ] Prepare Q&A sheet from "Likely Q&A" column with prepared answers
