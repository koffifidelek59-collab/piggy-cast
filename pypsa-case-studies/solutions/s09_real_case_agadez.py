"""Real case B - Off-grid mini-grid in the Agadez region: least-cost PV + battery + diesel.

Dataset data/networks/agadez_minigrid_2023: one bus, 8760 hourly snapshots of 2023, real
NASA POWER weather, demand peak 2 MW, existing 2.5 MW diesel genset; PV and a 4-hour battery
are extendable. Run:  python solutions/s09_real_case_agadez.py
"""
import logging
import warnings

import pandas as pd
import pypsa

warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
PATH = "data/networks/agadez_minigrid_2023"
SFC, VOM, CO2 = 0.28, 20.0, 0.74                  # l/kWh, $/MWh, tCO2/MWh of diesel


def solve(diesel_price=1.0, hybrid=True):
    n = pypsa.Network(PATH)
    n.generators.loc["diesel", "marginal_cost"] = diesel_price * SFC * 1000 + VOM   # $/MWh
    if not hybrid:
        n.generators.loc["pv", ["p_nom_extendable", "p_nom"]] = [False, 0]
        n.storage_units.loc["battery", ["p_nom_extendable", "p_nom"]] = [False, 0]
    n.optimize(solver_name="highs", solver_options={"output_flag": False})
    E = n.loads_t.p_set.sum().sum()
    d = n.generators_t.p["diesel"]
    capex = (n.generators.p_nom_opt["pv"] * n.generators.at["pv", "capital_cost"]
             + n.storage_units.p_nom_opt["battery"] * n.storage_units.at["battery", "capital_cost"])
    fuel = (d * n.generators.at["diesel", "marginal_cost"]).sum()
    return {"PV MW": n.generators.p_nom_opt["pv"], "battery MWh": 4 * n.storage_units.p_nom_opt["battery"],
            "renewable %": 100 * (1 - d.sum() / E), "diesel Ml": d.sum() * SFC / 1e3,
            "CO2 t": d.sum() * CO2, "$/kWh": (capex + fuel) / E / 1000}

print(pd.DataFrame({"diesel only": solve(hybrid=False), "optimal hybrid": solve()}).T.round(3).to_string())
print("\nSensitivity to the diesel price ($/litre)")
print(pd.DataFrame({p: solve(p) | {"$/kWh diesel only": solve(p, False)["$/kWh"]} for p in [0.8, 1.0, 1.2, 1.4]}).T.round(3).to_string())
