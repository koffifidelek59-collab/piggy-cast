# Dataset `niamey_3bus`

Teaching network inspired by the Niamey context (FICTITIOUS parameters, not NIGELEC data).
132 kV lines (ACSR 240/40: 0.12 + j0.39 ohm/km, 2.9 uS/km), hot-season rating 100 MVA.
24 hourly snapshots of 2023-05-04 (local time, UTC+1), the day of the annual demand peak:
PV output = 30 MW x real capacity factor (NASA POWER + pvlib),
city demand = 50 MW + 20 MVAr x modelled daily shape (peak = design value).

Snapshots: 24 (2023-05-04 00:00:00 to 2023-05-04 23:00:00)

| component | rows |
|---|---|
| buses | 3 |
| carriers | 3 |
| generators | 2 |
| loads | 1 |
| lines | 3 |

Time-series files: `generators-p_max_pu.csv`, `generators-p_set.csv`, `loads-p_set.csv`, `loads-q_set.csv`

Load with: `n = pypsa.Network("data/networks/niamey_3bus")`
