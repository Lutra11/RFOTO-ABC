# RFOTO ABC revision experiment protocol

Frozen before the supplementary runs on 9 September 2026. Historical data and the original algorithm files are read-only inputs. This is a local time-stamped protocol, not a public preregistration.

## Questions and decisions

1. Does the search improve over the same initial best solution, and over simpler search starting with exactly the same population? Compare RFOTO, a plain ABC adapter, DE/rand/1/bin and LSHADE-lite with population 14. Initialization is either the original 35% greedy scheme or entirely random. All search methods receive 320 or 1000 total objective evaluations, including initialization.
2. Do risk-biased task selection, fairness-based food-source selection and directed scouts individually help? Remove only the named operation, preserving objective weights, initial population and decoder. A separate uniform-allocation replacement intentionally changes the genotype-to-resource mapping, so its initial phenotype is not held constant.
3. Do fixed settings transfer to freshly generated instances? Compare the original temperature 0.8 and temperature 1.6 selected from the previous S4 sensitivity sweep, without choosing between them using new test results. Include plain ABC, LSHADE-lite and the Offload-then-Allocate rule. The rule uses one evaluation and is a cost reference, not an equal-budget optimizer.

## Design

- Controlled suite: S2, S4, S6; 20 independently generated instances per scene; 320 and 1000 evaluations. Greedy initialization: eight methods RFOTO-ABC, Plain-ABC, No-risk-sampling, No-fair-selection, Random-scout, Uniform-allocation, DE-RK, LSHADE-lite. Random initialization: RFOTO-ABC, Plain-ABC, DE-RK, LSHADE-lite. Total 1440 optimization runs.
- Frozen test suite: S1 through S6; 20 further instances per scene; 320 evaluations; RFOTO-ABC at 0.8, RFOTO-ABC at 1.6, Plain-ABC at 0.8, LSHADE-lite at 0.8, Offload-then-Allocate. Total 600 runs, including 120 one-evaluation rules.
- Wireless seed = 909000000 + suite_id * 1000000 + scenario_number * 10000 + instance; suite_id = 1 for controlled and 2 for frozen test. Task seed is wireless seed + 100000000. Initialization seed is wireless seed + 200000000. Optimization seed is wireless seed + 300000000, identical across paired algorithms; the same integer does not imply identical random event sequences across different algorithms.
- Wireless states are freshly generated with the original UMi-inspired generator and 256 Monte Carlo samples; no modulo reuse of old channel files. Geometry, shadowing, blockage, fading and link probabilities are newly sampled. Alibaba-derived profiles and mapping parameters remain frozen. This tests new instances from the same model, not a new real-world dataset or trace-row-disjoint validation.
- Default objective weights remain [0.25, 0.15, 0.20, 0.25, 0.15]. All methods observe the same channel/task state. Full RFOTO parameters are unchanged except the explicitly labeled temperature variant.
- No-risk-sampling sets the four task-risk weights to zero (epsilon-uniform task probabilities), while retaining the reliability candidate filter. No-fair-selection disables the fairness term in source selection only; the objective remains unchanged. Random-scout changes only the abandoned-source restart. Plain-ABC disables risk/candidate guidance, fairness guidance and directed scouting but retains the same basic neighborhood, decoder and greedy initialization when assigned. It is a task-adapted control, not a claim of canonical ABC equivalence.
- For continuous-key DE and LSHADE-lite, assignment keys use bin centers (assignment + 0.5)/(M + 1) to ensure an exact genotype round trip. Resource keys are identical to those passed to ABC. DE uses F = 0.65 and CR = 0.7, one forced crossover coordinate and distinct mutation parents. LSHADE-lite retains the existing success-history, jitter and population-reduction implementation, starting at 14 and reducing to 6. It is not the complete published L-SHADE.

## Analysis frozen in advance

- Primary metric: the common weighted objective, smaller is better. Secondary metrics: deadline-violation fraction, risk, Jain fairness, initialization-to-final improvement, resource/reliability feasibility and actual evaluation count.
- Independent analysis unit: a newly generated scene-instance. Compare algorithms within the same instance, initialization and budget. Do not treat the two budgets as independent replicas, or pool unlike scenes as if interchangeable observations.
- Report means and standard deviations, paired relative differences (100*(comparator - RFOTO)/comparator), 95% paired-instance bootstrap percentile intervals (10000 resamples; fixed seed 20260909), two-sided paired Wilcoxon signed-rank tests and Holm correction across all predeclared contrasts within each suite. For exact-zero paired differences report p=1. Statistical significance is distinct from practical size.
- Ties for best are counted separately from unique wins using absolute tolerance 1e-12 and zero relative tolerance. A method can be tied best without winning a unique first place. Never choose a winner by row order.
- A null or reversed result will narrow the corresponding component claim. No rerunning or retuning to obtain favorable test outcomes. Historical findings remain separately labeled with their original budgets and samples.
- Parallel worker timings are recorded for audit but will not be used as isolated deployment latency measurements.

## Verification

Check: original RFOTO replay equivalence when given its original population and RNG state; matched-population hashes; identical initial objective values for shared-decoder methods; exact integer assignment round trips; exact budget accounting; nonincreasing best-so-far objective; common objective decomposition; reliability/capacity constraints; fresh wireless hashes against all historical states; frozen-test and controlled-suite disjoint seeds; preservation of historical raw-data and manuscript hashes. Save raw run records, traces, instance NPZ files, protocol/config/code SHA256 hashes and full analysis outputs. Report failures instead of silently dropping runs.
