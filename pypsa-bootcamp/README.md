# PyPSA Bootcamp - a progressive course built on the Bohol island dataset

A hands-on, chapter-by-chapter course in power-system modelling with
[PyPSA](https://pypsa.org). It follows the same shape as a programming bootcamp:
**one new idea per chapter**, each built on the real electricity island of
**Bohol (Philippines)**, with runnable code, heavy comments, printed results and
a short analysis at every step.

The structure mirrors the reference tutorial
[`pypsa-tutorial-zh`](https://github.com/koffifidelek59-collab/pypsa-tutorial-zh)
(installation -> first network -> power flow -> economic dispatch -> storage ->
case study) and uses the dataset and modelling conventions of the PyPSA Bohol
workshop.

## The eight chapters

| # | Chapter | What you learn | Headline result |
|---|---------|----------------|-----------------|
| 1 | Installation and the dataset | verify PyPSA + HiGHS; read the 7 dataset sheets | diesel ~157, grid ~43, hydro ~0 per MWh |
| 2 | Your first network | `n.add`, component tables, `n.statistics`, the copper plate | cheap import serves the load, diesel off |
| 3 | Power flow | `n.pf` vs `n.lpf`, per-unit, voltages, losses | Corella sags to 0.977 pu; a capacitor lifts it |
| 4 | Economic dispatch | merit order, `n.optimize`, marginal price | uniform 42.73/MWh; 157.52 when the cable is scarce |
| 5 | Renewables and storage | 24 h snapshots, `p_max_pu`, `StorageUnit` | a battery cuts curtailment 105->25 MWh, cost -18 % |
| 6 | Congestion and security | nodal prices, loop flow, N-1 screen | congestion splits price 157 vs 43; island is N-1 secure |
| 7 | Capacity expansion | `p_nom_extendable`, annualised cost, CO2 cap | cost-optimal build is mostly renewable; CO2 cap costs +8 % to 70 % |
| 8 | Capstone case study | four scenarios on the full island | renewables -68 % cost; island survives the cable loss |

## Quick start

```bash
pip install -r requirements.txt       # pypsa, highspy, jupytext, nbconvert, matplotlib, openpyxl
python scripts/run_all.py             # execute every chapter end to end
jupyter lab notebooks/                # or open the executed notebooks
```

Each chapter is a standalone script in `scripts/` (jupytext *percent* format) and
an executed notebook in `notebooks/`. Open either; they are the same content.

## Layout

```
data/        PyPSA_Dataset_Bohol.xlsx  (buses, loads, carriers, generators, lines, loads_t, generators_t)
scripts/     01..08 chapter sources (percent format) + run_all.py
notebooks/   01..08 executed notebooks (outputs and figures included)
figures/     PNG figures produced by the chapters
```

## The dataset

The real Bohol sub-system: three buses (two at 138 kV, one at 13.8 kV), three AC
lines, thirteen generators (diesel + small hydro + a submarine-cable import), six
carriers with cost and CO2 data, and a 24-hour demand and solar/wind profile for
2 January 2023. Economics follow the workshop convention:

- `marginal_cost = VOM + fuel / efficiency`
- `capital_cost  = (1 + FOM) * investment / (lifetime * 365.25)`  (per day)

## Honesty notes

- Results are reproducible: the solver is open-source **HiGHS**, no internet or
  token needed, and the printed numbers are exactly what the code computes.
- The CO2 cap is **slack in pure dispatch** (here the cheapest plants are also the
  cleanest) and only bites once capacity is extendable (Chapter 7) - the course
  says so plainly instead of hiding it.
- The single representative day favours renewables; Chapter 8 lists the steps to a
  full-year study.

Author: KOUAME Koffi Fidele - IMP-EGH Master, Track 6 System Analysis.
