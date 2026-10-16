"""Lesson 5, "exemplary PtX scenario": where should electrolysers be connected?

Small illustrative network (data invented for teaching, 380 kV):
  North : large wind farm (renewable surplus)
  Centre: transit node
  South : load centre with gas-fired plants
A 300 MW electrolyser is connected either in the SOUTH (next to industrial users) or in
the NORTH (next to the wind). Two PyPSA studies:
  1. linear ("DC") power flow for one windy hour  -> line loading in each case
  2. 24-hour optimal dispatch with HiGHS (generators, electrolyser, hydrogen storage,
     line limits)                                     -> cost, curtailment, congestion

Run: python3 08_pypsa_ptx_electrolysers.py
"""
import logging
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

X_PER_KM = 0.25          # ohm/km, typical 380 kV overhead line
LINES = {"N-C": ("North", "Centre", 150, 600),       # name: bus0, bus1, km, MVA
         "C-S": ("Centre", "South", 150, 600),
         "N-S": ("North", "South", 300, 400)}


def base_network(snapshots, electrolyser_bus):
    n = pypsa.Network()
    n.set_snapshots(snapshots)
    for b in ("North", "Centre", "South"):
        n.add("Bus", b, v_nom=380, carrier="AC")
    for name, (b0, b1, km, s_nom) in LINES.items():
        n.add("Line", name, bus0=b0, bus1=b1, x=X_PER_KM * km, r=0.03 * km, s_nom=s_nom)

    # hydrogen side: H2 bus, storage tank, constant industrial H2 demand
    n.add("Bus", "H2", carrier="H2")
    n.add("Link", "electrolyser", bus0=electrolyser_bus, bus1="H2",
          p_nom=300, efficiency=0.65, marginal_cost=0)
    n.add("Store", "H2 tank", bus="H2", e_nom=3000, e_cyclic=True)
    n.add("Load", "H2 demand", bus="H2", p_set=120)            # MW of hydrogen (LHV)
    return n


# ------------------------------------------------------------------ 1. one windy hour
def dc_power_flow(electrolyser_bus):
    n = base_network(["windy hour"], electrolyser_bus)
    n.add("Generator", "wind", bus="North", p_set=900)
    n.add("Generator", "gas", bus="South", p_set=0)
    n.add("Load", "demand", bus="South", p_set=600)
    # in a power flow the electrolyser is just a 300 MW load at its bus
    n.links.loc["electrolyser", "p_set"] = 300
    n.add("Generator", "slack", bus="South", control="Slack", p_set=0)
    n.lpf()
    flows = n.lines_t.p0.iloc[0]
    return (flows.abs() / n.lines.s_nom * 100).round(0), flows.round(0)


print("=" * 72)
print("1. Linear power flow, one windy hour: wind 900 MW (North), demand 600 MW (South),")
print("   electrolyser 300 MW. Line loading in % of the thermal rating:")
for where in ("South", "North"):
    load_pct, flows = dc_power_flow(where)
    flag = "  <-- OVERLOADED" if (load_pct > 100).any() else ""
    print(f"   electrolyser in the {where:5s}: " +
          ", ".join(f"{k} {v:.0f} %" for k, v in load_pct.items()) + flag)

# ------------------------------------------------------------------ 2. 24-hour optimisation
hours = pd.date_range("2030-06-01", periods=24, freq="h")
t = np.arange(24)
wind_cf = 0.55 + 0.35 * np.cos((t - 3) / 24 * 2 * np.pi)        # windier at night
demand = 500 + 150 * np.sin((t - 6) / 24 * 2 * np.pi).clip(0)   # daytime peak


def optimise(electrolyser_bus):
    n = base_network(hours, electrolyser_bus)
    n.add("Carrier", "AC")
    n.add("Carrier", "H2")
    n.add("Generator", "wind", bus="North", p_nom=1200, p_max_pu=wind_cf, marginal_cost=0)
    n.add("Generator", "gas", bus="South", p_nom=800, marginal_cost=80)       # EUR/MWh
    n.add("Load", "demand", bus="South", p_set=demand)
    status, condition = n.optimize(solver_name="highs", solver_options={"output_flag": False})
    assert status == "ok", condition
    wind_avail = (n.generators.p_nom["wind"] * n.generators_t.p_max_pu["wind"]).sum()
    curtailed = wind_avail - n.generators_t.p["wind"].sum()
    congested = (n.lines_t.p0.abs().ge(n.lines.s_nom * 0.999)).sum()
    return {
        "total cost (kEUR/day)": n.objective / 1e3,
        "gas used (MWh)": n.generators_t.p["gas"].sum(),
        "wind curtailed (MWh)": curtailed,
        "hours with a congested line": int(congested.max()),
    }


print("\n" + "=" * 72)
print("2. 24-hour optimal dispatch with HiGHS (wind 1200 MW, gas 800 MW at 80 EUR/MWh,")
print("   electrolyser 300 MW feeding a 3000 MWh hydrogen tank and a 120 MW H2 demand):")
results = pd.DataFrame({f"electrolyser in {w}": optimise(w) for w in ("South", "North")})
print(results.round(0).to_string())
print("\nReading: placing the electrolyser next to the wind lets it absorb the surplus")
print("locally, relieving the North-South corridor. This is the message of the Lesson 5")
print("PtX scenario (relocation of electrolysers in the German target grid).")
