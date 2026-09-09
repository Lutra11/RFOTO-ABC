# Generated wireless inputs

`generated_v1/` contains static S0–S6 inputs and S6 dynamic trajectories, a seed/configuration manifest and field codebook. `tools/` contains the generator and array loader. Generated channels combine documented 3GPP-inspired path loss, Rayleigh/Rician fading and finite-transmission reliability grids.

Read `generated_v1/README.md` for shapes and units. For the revision's separate fresh instances see `../../datas/revision_20260909/instances/`. Frozen-test and controlled instances share the same generation framework and workload pool; there is no external measured-channel test set.
