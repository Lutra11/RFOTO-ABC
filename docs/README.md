# Manuscript alignment

This package corresponds to `RFOTO-ABC_Telecommunication_Systems_完整论文_中文版_全面修订版.docx`, the comprehensive revision dated 9 September 2026.

Manuscript SHA-256: `9bc623400af37ece8764b43747b8b4e4b44cbe3b5cb7cd179d5f6a9b0486861f`.

The working manuscript itself is maintained separately. This repository publishes its code, result tables, inputs and figures, not a claim of acceptance by Telecommunication Systems.

| Section | Tables | Figures | Core group |
|---|---|---|---|
| 4.1 Data and preprocessing | 3–4 (setup) | 1 | Dataset construction |
| 4.2 Environment and parameters | 5–6 (setup) | — | Shared protocol |
| 4.3.1 Overall performance | 7–9 | 2–4 | comparison |
| 4.3.2 Components and resource allocation | 10–11 | 5–6 | ablation |
| 4.3.3 Sensitivity and stability | 12–13 | 7–8 | sensitivity |
| 4.3.4 Applicability and scale | 14–16 | 9–10 | generalization |

Tables 7–16 are exported numerically to CSV/Excel, including SDs and unrounded data needed to audit rounded manuscript cells. Supplemental raw files retain dynamic and failure evidence. The file naming is standardized to current manuscript figure numbers rather than historical Section 4.7–4.23 numbering.

## Reporting limits retained in this release

The matched-initialization controls, negative ablations, uniform-allocation alternative, S2/S4 rule advantages, lack of stable warm-start superiority and the shared workload/generator boundary must remain visible when using these results. The 1.6 temperature test is not a cross-method common-decoder comparison. Historical sample sizes differ from the revision's 20-instance groups. No visually substituted display values enter the evidence package.

Author names/order and affiliation match author confirmation. Funding, conflicts, contribution roles and other unconfirmed declarations are not invented here. The software-assistance disclosure remains in the root README and manuscript.
