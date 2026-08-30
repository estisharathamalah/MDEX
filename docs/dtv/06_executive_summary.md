# Executive Summary — MDEX

**1. What is the problem?** Mineral exploration companies make sequential, high-stakes capital-allocation decisions (drill, survey, hold, stop) under deep geological uncertainty, largely via tacit, non-quantified, non-auditable judgment.

**2. What is the technology?** MDEX is a computational decision engine that maintains an explicit probabilistic belief over competing geological hypotheses, values candidate exploration actions by their expected information gain (Value of Information) net of cost, enforces budget constraints, and produces a ranked, fully-reasoned, provenance-tracked recommendation — replayable chronologically against history under a structurally enforced temporal information firewall.

**3. Why is it deep-tech?** It requires integrating probabilistic geological reasoning, decision theory, exploration economics, and a rigorous historical-evaluation methodology into one auditable computational loop — a combination not available as an off-the-shelf exploration-specific tool, and not reducible to an LLM, dashboard, or CRUD application.

**4. What has been demonstrated?** A working implementation of the full decision loop (evidence → belief → VOI → economics → ranking → sequential replay → evaluation), 9 passing automated tests including a mandatory proof that future information cannot leak into a historical decision, and one full end-to-end run against a historically-grounded Oyu Tolgoi decision scenario, producing a reproducible, machine-readable result that honestly reports where MDEX's recommendation disagreed with the historical decision.

**5. What is the current TRL?** TRL 3 demonstrated (critical functions implemented and experimentally exercised). TRL 4 roadmap defined; not yet claimed as met — see `docs/dtv/02_trl_evidence.md`.

**6. Why mining?** Exploration capital allocation is a large, high-variance, information-scarce decision problem where a quantified, auditable decision trail is structurally valuable and largely absent from current practice.

**7. Why Saudi Arabia?** Saudi Arabia's mineral-sector expansion under Vision 2030 and growth in exploration licensing activity create a plausible domestic customer base; this is a stated hypothesis pending direct validation with Saudi mineral-sector stakeholders, not yet tested.

**8. What is defensible?** The specific integration of a temporally-firewalled evidence/provenance data model with a VOI-driven sequential decision architecture and an honest-disagreement evaluation methodology — not the underlying mathematics, which is well established and not claimed as novel. See `docs/dtv/03_ip_defensibility.md` for what remains unproven.

**9. What is the commercial opportunity?** Unvalidated at this stage. No customer interviews, LOIs, or revenue figures exist; `docs/dtv/04_market.md` states hypotheses explicitly and names the validation work required before any commercial claim is made.

**10. What will DTV enable next?** Funding and access to (a) real, sourced historical exploration datasets for multi-case validation, (b) domain-expert geologists to elicit calibrated likelihood tables, and (c) introductions to Saudi mineral-sector stakeholders (e.g. Ma'aden, Saudi Geological Survey) for a real pilot — the concrete next steps needed to move from TRL 3 to TRL 4 and from technology hypothesis to a validated commercial opportunity.
