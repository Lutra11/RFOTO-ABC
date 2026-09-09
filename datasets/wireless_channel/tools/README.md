# Channel generation and loading

`generate_wireless_dataset.py` defines the scenario configurations, user/server topology, path-loss/blockage/fading calculations and success-probability grids. This source file is a frozen revision input and is intentionally unchanged.

`wireless_dataset.py` loads generated arrays and interpolates finite-transmission reliability. A portable usage example is in `../generated_v1/README.md`.

Inspect generator options with:

```bash
python datasets/wireless_channel/tools/generate_wireless_dataset.py --help
```

Use a new output directory when generating a different dataset. Do not silently overwrite the archived inputs or call newly generated data an exact replay without checking array equality and seeds.
