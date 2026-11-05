# Dataset `niamey_5bus`

Five-bus teaching network (FICTITIOUS parameters). Bus 5 is a remote industrial zone at the
end of an 85 km, 132 kV line. Design values (daily peak): substation 25 MW + 8 MVAr,
urban 45 + 15, industry 35 + 18; PV plant 40 MW at bus 3.
24 hourly snapshots of 2023-05-04 (local time); real PV capacity factor, modelled demand shape
(industrial load flatter: 85 % + 15 % x shape).

Snapshots: 24 (2023-05-04 00:00:00 to 2023-05-04 23:00:00)

| component | rows |
|---|---|
| buses | 5 |
| carriers | 3 |
| generators | 2 |
| loads | 3 |
| lines | 5 |

Time-series files: `generators-p_max_pu.csv`, `generators-p_set.csv`, `loads-p_set.csv`, `loads-q_set.csv`

Load with: `n = pypsa.Network("data/networks/niamey_5bus")`
