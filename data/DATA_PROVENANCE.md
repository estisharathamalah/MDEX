# Data Provenance — Oyu Tolgoi Pre-Discovery Scenario

This POC reconstructs a single historical decision point: Ivanhoe Mines'
mid-2001 choice of where to commit a scarce deep diamond drill hole at the
Oyu Tolgoi (Turquoise Hill) licence in the South Gobi, Mongolia, in the
weeks before discovery hole OTD-150 was drilled in July 2001.

## FACT items (cited, dated on or before the July 2001 decision)

| Item | Detail | Date observed | Date available | Source |
|---|---|---|---|---|
| F1 | Ivanhoe Mines signed an option agreement with BHP Billiton to earn a 100% interest in the Oyu Tolgoi concession. | 2000-05 | 2000-05 | Turquoise Hill Resources, "History" (turquoisehill.com/turquoise-hill/history) |
| F2 | Ivanhoe completed approximately 109 reverse-circulation holes by September 2000, described as encouraging. | 2000-09 | 2000-09 | Mining South East Europe, "The story of the copper discovery at Oyu Tolgoi" |
| F3 | A total of 149 holes had been completed before the eventual discovery hole; the exploration budget was constrained, funding only three deep diamond holes. | 2001 (pre-July) | 2001 (pre-July) | IndraStra Global, "The Story of the Discovery of Oyu Tolgoi"; corroborated by Mining South East Europe |
| F4 | Three deep diamond holes were planned to test hypogene copper-gold potential at Southern Oyu, Southwest Oyu, and Central Oyu respectively; local geologist D. Garamjav was central to selecting the Southwest Oyu collar location. | 2001 (pre-July) | 2001 (pre-July) | Turquoise Hill Resources "History"; IndraStra Global |
| F5 (post-decision, used only for evaluation) | Hole OTD-150, collared at Southwest Oyu, was drilled to 590 m depth in July 2001 and intersected 508 m averaging >1 g/t Au and 0.81% Cu (70–578 m), including 278 m at >1.0% Cu and ~1.5 g/t Au (188–466 m). | 2001-07 | 2001-07-17 (public news release) | Turquoise Hill Resources "History"; Ivanhoe Mines news release of 2001-07-17 as reported in International Mining and GlobeNewswire retrospectives |
| F6 (post-decision) | Ivanhoe's first independent resource audit for the Southwest Oyu discovery zone (March 2002) estimated inferred resources of 588 Mt at 0.53 g/t Au and 0.41% Cu (~10 Moz Au, ~5.3 Blb Cu) at a 0.30% CuEq cutoff. | 2002-03 | 2002-03 | Turquoise Hill Resources "History" |

All figures above are paraphrased from the cited public sources; none are
verbatim reproductions. F5 and F6 postdate the decision point and are used
**only** by the Evaluation Engine after MDEX's recommendation has already
been generated from F1–F4 — this is the temporal firewall in practice.

## What is NOT reconstructed from primary data (and why)

The master prompt calls for full drill-hole-level assay tables, geophysical
survey grids, and geochemical sampling results with individual provenance.
Those primary datasets (original assay certificates, IP survey grids,
soil-geochemistry results for the 109–149 pre-discovery holes) are not
publicly available in machine-readable form; they exist in Ivanhoe/Turquoise
Hill's internal technical reports and NI 43-101 filings that were not
retrievable in this session (no verified public repository of the raw
pre-2001 dataset was located). Reconstructing them at hole-by-hole
resolution would require either licensed access to those filings or
further dedicated archival research.

**This POC does not fabricate that data.** Instead:

- The macro-level facts above (F1–F6) are used as the real, cited
  historical scaffold — dates, decision constraints, and the eventual
  outcome are FACT.
- The candidate-action set and the specific evidence-to-hypothesis
  likelihood values used to run the belief update in `experiments/`
  are `[SYNTHETIC]` — clearly labeled as illustrative test data
  constructed to exercise the computational pipeline against a
  historically-grounded scenario, not as a claim about the real
  underlying assay values at each of the 149 holes.
- `docs/OPEN_ISSUES.md` records this as the top data-availability gap and
  names the concrete next step (licensed/archival access to pre-2001
  Ivanhoe technical reports) required to replace the synthetic layer with
  a fully historical one.

## Synthetic data location

All synthetic data lives under `data/synthetic/` and every record includes
`"provenance": "SYNTHETIC"` in its schema field, matching `ProvenanceTag`
in `src/mdex/evidence.py`. It is never merged silently with `data/historical/`.
