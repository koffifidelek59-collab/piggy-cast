# Dataset `ieee9`

IEEE / WSCC 9-bus system from the official MATPOWER file case9.m (345 kV, 100 MVA base),
with MATPOWER thermal ratings (rateA) and quadratic generator costs (gencost: c2, c1).
Generator reactive limits stored as custom columns q_min, q_max (MVAr).

Snapshots: 1 (now to now)

| component | rows |
|---|---|
| buses | 9 |
| carriers | 1 |
| generators | 3 |
| loads | 3 |
| lines | 9 |

Time-series files: none

Load with: `n = pypsa.Network("data/networks/ieee9")`
