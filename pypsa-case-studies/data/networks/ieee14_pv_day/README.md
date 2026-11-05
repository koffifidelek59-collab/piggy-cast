# Dataset `ieee14_pv_day`

IEEE 14-bus (as in `ieee14`) over 24 hours of 2023-03-16, the clearest day of Q1 2023 in Niamey.
IEEE loads are taken as the evening peak and scaled by the modelled daily shape.
A 100 MW PV plant (real capacity factor) and a 50 MW / 200 MWh battery are connected at bus 14,
the weakest node of the system.

Snapshots: 24 (2023-03-16 00:00:00 to 2023-03-16 23:00:00)

| component | rows |
|---|---|
| buses | 14 |
| carriers | 3 |
| generators | 6 |
| loads | 11 |
| lines | 17 |
| transformers | 3 |
| storage_units | 1 |
| shunt_impedances | 1 |

Time-series files: `generators-p_max_pu.csv`, `generators-p_set.csv`, `loads-p_set.csv`, `loads-q_set.csv`

Load with: `n = pypsa.Network("data/networks/ieee14_pv_day")`
