# Manuscript alignment

This release is aligned with the English LaTeX manuscript **“RFOTO-ABC: Reliability- and fairness-aware task offloading and resource allocation in wireless edge computing”**, revised on 10 September 2026.

The authoritative manuscript source is maintained outside this repository as `RFOTO-ABC_English_LaTeX`. The synchronized LaTeX entry point and its asset manifest have SHA-256:

```text
main.tex              ba136b7862d1082be0cd1c84b64c47adb4a8f04ed75d0ffb0c107803f39009fc
source_manifest.json  f972f09f8c8e93c9285e72a940f3d484dc3399709d838e3f9bc1b8a2f4fd7e78
```

The repository publishes the implementation, evidence, numeric tables, and exact figure assets rather than a duplicate manuscript build tree.

## Paper-to-repository map

| Manuscript content | Repository evidence |
|---|---|
| Methodology and Figure 1 | `algorithm/`, `experiments/`, `images/*/Framework.*` |
| Dataset construction and Figure 2 | `datasets/DATASET.md`, `tools/preprocess_alibaba.py`, Figure 2 assets |
| Overall comparison, Figures 3–5, Tables 5–7 | historical comparison CSVs and revision matched-initialization records |
| Components, Figures 6–7, Tables 8–9 | historical ablation CSV and controlled revision records |
| Sensitivity/capacity, Figures 8–10, Tables 10–11 | sensitivity, resource-scarcity, and frozen-temperature sources |
| Applicability/scale/dynamics, Figures 11–14, Tables 12–15 | transfer, new-instance, scaling, and dynamic records |

Tables 1–4 are literature, notation, scenario, and parameter tables. Experimental Tables 5–15 are consolidated in `datas/RFOTO_ABC_Results.xlsx`. The figure filename retains the historical experimental number, while `images/README.md` records the final manuscript number after the framework became Figure 1.

## Reporting boundaries

- Main-text evidence is presented in one Excel workbook, while raw records and frozen instances support validation and replay.
- Figure 4 uses the author-retained replacement for its first panel. Its relationship to the retained aggregate panels and Table 6 has not been recomputed from a newly supplied sequential record.
- The dynamic CSV label `Standard-ABC` is corrected to `Cold-RFOTO (alternative seed)` in Figure 14 and Table 15 because that series invoked RFOTO cold-start optimization with another seed. Static `Standard-ABC` results keep their original meaning.
- Temperature 1.6 is a prespecified RFOTO-ABC configuration test, not a common-decoder comparison across all optimizers.
- Negative ablations, rule-baseline advantages, and the absence of stable warm-start benefit remain visible.
- Funding, competing interests, and individual author contributions still require author confirmation.
