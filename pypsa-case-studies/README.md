# Power System Case Studies with PyPSA

Nine case studies, **one problem type each**, from the Newton-Raphson load flow to solar and
storage planning on real hourly weather for Niger. Every case states the exercise, uses a
PyPSA dataset (buses, carriers, generators, loads, lines, `loads_t`, `generators_t`), solves
it, checks it, and interprets the result as an expert would present it.

| Deliverable | File |
|---|---|
| **Case-study workbook** (35 pages, same layout as the per-unit method sheet): every exercise with its original diagram, the 8-step scientific approach, the full PyPSA code and its printed output | [`workbook/PyPSA_Case_Study_Workbook.pdf`](workbook/PyPSA_Case_Study_Workbook.pdf) |
| **Presentation** (21 slides, layout of the course slides) | [`slides/PyPSA_Case_Studies_Presentation.pptx`](slides/PyPSA_Case_Studies_Presentation.pptx) |
| Self-contained PyPSA solution scripts (one per exercise) and their outputs | [`solutions/`](solutions/) |
| Executed notebooks with extended analyses and figures | [`notebooks/`](notebooks/) |
| PyPSA datasets (CSV folders) | [`data/networks/`](data/networks/) |
| Figures and result tables | [`results/`](results/) |

## The case studies

| # | Problem type | Network and data | Headline result |
|---|---|---|---|
| CS00 | Solving non-linear equations | Exercise 5, assignment 1 | Quadratic vs linear convergence; failure where f'(x) = 0 |
| CS01 | Solving the AC load flow | Exercise 5, 3 buses | NR from scratch: \|U3\| = 0.951 p.u. in 4 iterations, = PyPSA to 1e-15 |
| CS02 | Power balance, slack, reactive power | 3 buses (Niamey context), real solar day | 30 MW PV: thermal 50.3 -> 20.2 MW; evening peak still thermal |
| CS03 | Undervoltage | 5 buses, 85 km feeder | 0.919 p.u. -> 0.959 p.u. with a 15 MVAr capacitor bank |
| CS04 | Congestion, N-1, nodal prices | IEEE 9-bus (MATPOWER) | 113 % N-1 overload removed by SC-OPF for 54 $/h; hidden voltage collapse found by AC check |
| CS05 | Demand growth, voltage stability | IEEE 14-bus (MATPOWER + PGLib ratings) | Reactive reserve gone at +30 %; loadability +77 % (not +145 %) |
| CS06 | Reverse flow, hosting capacity, storage | IEEE 14-bus + PV + battery, real solar day | Hosting capacity 3 -> 66 -> 129 MW with set points and inverter Q control |
| CS07 | Real case A: planning with solar and storage | Niamey area, 8760 h of 2023 | Islanded: 333 MW PV + 783 MWh battery, cost -22 %, fuel -68 % |
| CS08 | Real case B: off-grid sizing | Agadez region mini-grid, 8760 h of 2023 | 94 % renewable, 0.30 -> 0.16 $/kWh, robust to diesel price |

## Quick start

```bash
conda env create -f environment.yml      # or: pip install -r requirements.txt
conda activate pypsa-cases
python scripts/build_datasets.py         # rebuild the PyPSA CSV datasets
python scripts/run_all.py                # execute every case study -> notebooks/, results/
python scripts/run_all.py cs07           # re-run a single case study
python solutions/s02_ex5_load_flow.py    # run one exercise solution (from the repository root)
```

Open a dataset directly:

```python
import pypsa
n = pypsa.Network("data/networks/niamey_5bus")   # buses.csv, lines.csv, loads-p_set.csv ...
n.pf()                                           # 24 AC load flows (one per hour)
n.buses_t.v_mag_pu                               # voltages in p.u.
```

## Repository layout

```
src/pscs/            shared library
  matpower.py        MATPOWER .m reader and converter to PyPSA (p.u. -> ohm/siemens)
  newton.py          Newton's method and Newton-Raphson load flow written from scratch
  kpi.py             AC load-flow helpers, indicators, reactive-limit (PV-PQ) enforcement
  solar.py           NASA POWER / Renewables.ninja readers, pvlib PV model chain
  demand.py          temperature-driven demand model
  assumptions.py     cost assumptions (one place to change them)
  plotting.py        colour-blind-safe chart style
solutions/           s01 ... s09: one self-contained PyPSA script per exercise, outputs in solutions/output/
workbook/            LaTeX source and PDF of the workbook, original exercise figures, one-line diagrams
scripts/             cs00 ... cs08 case-study sources (jupytext percent format),
                     build_datasets.py, run_all.py, fetch_renewables_ninja.py
data/raw/            MATPOWER case9/case14, PGLib case14, NASA POWER 2023, reference results
data/networks/       ex5_3bus, niamey_3bus, niamey_5bus, ieee9, ieee14, ieee14_pv_day,
                     niamey_grid_2023 (8760 h), agadez_minigrid_2023 (8760 h)
notebooks/           executed notebooks
results/             figures/ (PNG) and tables/ (CSV, JSON summaries)
slides/              presentation generator (pptxgenjs) and the PowerPoint
```

## Data and honesty notes

- **IEEE systems**: official MATPOWER files; 14-bus thermal ratings from PGLib-OPF v23.07.
  PyPSA reproduces the published solutions and our own Newton-Raphson solver to machine precision.
- **Weather**: NASA POWER hourly data 2023 (CERES SYN1deg irradiance, MERRA-2 temperature)
  for Niamey and Agadez, converted to PV output with pvlib (Hay-Davies, Faiman, PVWatts,
  10 % losses), the same model chain as Renewables.ninja.
- **Renewables.ninja**: the API was not reachable from the computing environment (network
  policy). Run `python scripts/fetch_renewables_ninja.py --token YOUR_TOKEN`, then
  `python scripts/run_all.py`: every case automatically switches to the ninja profiles and
  reports the source it used. Narrative numbers in the report and slides refer to the
  NASA POWER run.
- **Niger grids and demand** (CS02, CS03, CS07, CS08): fictitious, educational parameters
  inspired by the Niamey and Agadez context; not NIGELEC data. Demand is a temperature-driven
  model, not measured load.
- **Costs**: assumptions within ranges published by IRENA (2024), NREL ATB and IPCC
  (`src/pscs/assumptions.py`).

## PyPSA 1.x lessons learned

- A generator with a numeric `p_set` is **fixed** in `n.optimize()`: set it to NaN before an OPF.
- The slack generator needs a numeric `p_set` (e.g. 0) for `n.pf()` to report its output.
- `n.pf()` does not enforce reactive limits: use `pscs.kpi.enforce_q_limits` for planning.
- A solved network cannot be copied while its solver model is attached:
  `n.model.solver_model = None` first.
- Lines are in ohm / siemens, transformers in p.u. on their own `s_nom`.

Author: KOUAME Koffi Fidèle - IMP-EGH Master, Track 6 System Analysis.
