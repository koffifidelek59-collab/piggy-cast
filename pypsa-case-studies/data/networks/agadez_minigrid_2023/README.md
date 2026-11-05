# Dataset `agadez_minigrid_2023`

Off-grid mini-grid for a town in the Agadez region (single bus, 0.4 kV), hourly year 2023.
Peak demand 2 MW (temperature-driven model with real Agadez temperatures).
Existing diesel genset 2.5 MW; PV and a 4-hour battery are extendable.
Real weather: NASA POWER hourly data for Agadez (16.97 N, 7.99 E).

Snapshots: 8760 (2023-01-01 00:00:00 to 2023-12-31 23:00:00)

| component | rows |
|---|---|
| buses | 1 |
| carriers | 4 |
| generators | 2 |
| loads | 1 |
| storage_units | 1 |

Time-series files: `generators-p_max_pu.csv`, `loads-p_set.csv`

Load with: `n = pypsa.Network("data/networks/agadez_minigrid_2023")`
