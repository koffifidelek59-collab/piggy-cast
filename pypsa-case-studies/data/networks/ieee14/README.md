# Dataset `ieee14`

IEEE 14-bus system from the official MATPOWER file case14.m (load flow data, 100 MVA base;
nominal voltages are not given in the file, 132 kV is used, results are in p.u.).
Thermal ratings from PGLib-OPF v23.07 (pglib_opf_case14_ieee.m, IEEE PES benchmark library).
Generator reactive limits stored as custom columns q_min, q_max (MVAr).

Snapshots: 1 (now to now)

| component | rows |
|---|---|
| buses | 14 |
| carriers | 1 |
| generators | 5 |
| loads | 11 |
| lines | 17 |
| transformers | 3 |
| shunt_impedances | 1 |

Time-series files: none

Load with: `n = pypsa.Network("data/networks/ieee14")`
