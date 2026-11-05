# Dataset `ex5_3bus`

Exercise 5 (Power System Modeling, Simulation and Control), assignment 2.
Bus 1 slack (|U1| = 1.00, theta1 = 0), bus 2 PV (P_G2 = 0.50 p.u., |U2| = 1.05),
bus 3 load (P_D3 = 2.50, Q_D3 = 1.00 p.u.). S_base = 100 MVA, U_base = 110 kV.
Each line: series admittance -j8 p.u., total shunt admittance j0.1 p.u. (j0.05 at each end).

Snapshots: 1 (now to now)

| component | rows |
|---|---|
| buses | 3 |
| carriers | 2 |
| generators | 2 |
| loads | 1 |
| lines | 3 |

Time-series files: none

Load with: `n = pypsa.Network("data/networks/ex5_3bus")`
