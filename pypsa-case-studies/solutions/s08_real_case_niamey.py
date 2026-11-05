"""Real case A - Niamey area: least-cost solar and storage, every hour of 2023.

Dataset data/networks/niamey_grid_2023: five-bus grid of TP case 2 (with the 15 MVAr bank),
8760 hourly snapshots; real NASA POWER weather (PV capacity factor in generators_t.p_max_pu),
temperature-driven demand (loads_t.p_set). PV and battery are extendable (capital costs set
from src/pscs/assumptions.py). Run:  python solutions/s08_real_case_niamey.py
"""
import logging
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
PATH = "data/networks/niamey_grid_2023"
FUEL, IMPORT, CO2 = 180.0, 70.0, 0.70          # $/MWh, $/MWh, tCO2/MWh
MUST_RUN = 20.0                                # MW of thermal online when islanded

n0 = pypsa.Network(PATH)
print(n0.generators[["bus", "p_nom", "p_nom_extendable", "marginal_cost", "capital_cost"]].round(0).to_string())
print(n0.storage_units[["bus", "max_hours", "capital_cost", "efficiency_store"]].round(2).to_string())
demand = n0.loads_t.p_set.sum(axis=1)
cf = n0.generators_t.p_max_pu["pv"]
print(f"demand {demand.sum()/1e3:.0f} GWh, peak {demand.max():.0f} MW; PV capacity factor {cf.mean():.1%}")


def build(imports, pv=None, battery=None):
    """pv / battery = None -> optimised by PyPSA; a number -> fixed capacity (MW)."""
    n = pypsa.Network(PATH)
    if not imports:
        n.generators.loc["import", "p_nom"] = 0.0
        n.generators.loc["thermal", "p_min_pu"] = MUST_RUN / n.generators.at["thermal", "p_nom"]
    if pv is not None:
        n.generators.loc["pv", ["p_nom_extendable", "p_nom"]] = [False, pv]
    if battery is not None:
        n.storage_units.loc["battery", ["p_nom_extendable", "p_nom"]] = [False, battery]
    return n


SCEN = {"A imports": (True, 0, 0), "B islanded": (False, 0, 0),           # islanded = no imports
        "C islanded+100PV": (False, 100, 0), "D0 islanded+optPV": (False, None, 0),
        "D islanded+opt": (False, None, None), "E imports+opt": (True, None, None)}
rows, nets = {}, {}
for name, args in SCEN.items():
    n = build(*args)
    n.optimize(solver_name="highs", solver_options={"output_flag": False})   # linear OPF, 8760 h
    p = n.generators_t.p
    pv_mw, bat_mw = n.generators.p_nom_opt["pv"], n.storage_units.p_nom_opt["battery"]
    capex = pv_mw * n.generators.at["pv", "capital_cost"] + bat_mw * n.storage_units.at["battery", "capital_cost"]
    opex = (p["thermal"] * FUEL + p["import"] * IMPORT).sum()
    avail = (pv_mw * cf).sum()
    rows[name] = {"PV MW": pv_mw, "bat MW": bat_mw, "bat MWh": 4 * bat_mw,
                  "solar %": 100 * p["pv"].sum() / demand.sum(),
                  "curtail %": 100 * (1 - p["pv"].sum() / avail) if avail else 0,
                  "CO2 kt": p["thermal"].sum() * CO2 / 1e3, "cost M$": (capex + opex) / 1e6,
                  "$/MWh": (capex + opex) / demand.sum(),
                  "max line %": 100 * (n.lines_t.p0.abs() / n.lines.s_nom).max().max()}
    nets[name] = n
print(pd.DataFrame(rows).T.round(1).to_string())

# ---------------------------------------------------------- AC check of scenario D
nD = nets["D islanded+opt"]
nD.model.solver_model = None                         # needed before copying a solved network
hours = pd.DatetimeIndex([demand.idxmax(), nD.generators_t.p["pv"].idxmax()])
m = nD.copy()
m.set_snapshots(hours)
m.generators_t.p_set = nD.generators_t.p.loc[hours]          # optimal dispatch -> set points
m.storage_units_t.p_set = nD.storage_units_t.p.loc[hours]
m.generators["control"] = "PQ"
m.generators.loc["thermal", "control"] = "Slack"             # the slack covers the AC losses
m.pf()
ac = pd.DataFrame({"min |V|": m.buses_t.v_mag_pu.min(axis=1), "max |V|": m.buses_t.v_mag_pu.max(axis=1),
                   "max loading %": 100 * (np.hypot(m.lines_t.p0, m.lines_t.q0) / m.lines.s_nom).max(axis=1),
                   "solar MW": m.generators_t.p["pv"]}, index=hours)
print("\nAC load flow of scenario D at the evening peak and at the solar peak\n", ac.round(3).to_string())
