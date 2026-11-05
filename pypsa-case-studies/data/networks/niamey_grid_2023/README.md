# Dataset `niamey_grid_2023`

Hourly year 2023 (8760 local hours, UTC+1) on the five-bus Niamey-area network (FICTITIOUS
grid parameters), with the 15 MVAr capacitor bank chosen in CS03.
Supply at bus 1: thermal plant (200 MW, HFO/diesel) and an import interconnector (80 MW).
PV (bus 3) and a 4-hour battery (bus 3) are extendable: PyPSA chooses their size.
Real weather: NASA POWER hourly irradiance and temperature for Niamey (13.51 N, 2.11 E);
PV capacity factor from pvlib (or Renewables.ninja when its CSV is present).
Demand: temperature-driven model (see src/pscs/demand.py), peak 105 MW.

Snapshots: 8760 (2023-01-01 00:00:00 to 2023-12-31 23:00:00)

| component | rows |
|---|---|
| buses | 5 |
| carriers | 5 |
| generators | 3 |
| loads | 3 |
| lines | 5 |
| storage_units | 1 |
| shunt_impedances | 1 |

Time-series files: `generators-p_max_pu.csv`, `loads-p_set.csv`, `loads-q_set.csv`

Load with: `n = pypsa.Network("data/networks/niamey_grid_2023")`
