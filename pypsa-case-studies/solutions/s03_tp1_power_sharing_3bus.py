"""TP case 1 - Three-bus network (Niamey context): thermal plant, city, solar plant.

Questions: voltages, effect of solar on the thermal output, reactive power, line loading,
losses. Part A: design point built explicitly in PyPSA. Part B: the real day of 4 May 2023
(24 snapshots, real solar profile) from the dataset data/networks/niamey_3bus.
Run from the repository root:  python solutions/s03_tp1_power_sharing_3bus.py
"""
import logging
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

# 132 kV overhead line, ACSR 240/40 mm2 (per-km values) and hot-season rating
R_KM, X_KM, B_KM, S_NOM = 0.12, 0.39, 2.9e-6, 100.0     # ohm/km, ohm/km, S/km, MVA


def network(pv_mw, pv_mode="PQ"):
    n = pypsa.Network()
    n.add("Bus", "1", v_nom=132, v_mag_pu_set=1.02)        # thermal plant (slack)
    n.add("Bus", "2", v_nom=132)                           # city substation
    n.add("Bus", "3", v_nom=132, v_mag_pu_set=1.02)        # solar plant
    for name, a, b, km in [("L1-2", "1", "2", 25), ("L1-3", "1", "3", 20), ("L2-3", "2", "3", 15)]:
        n.add("Line", name, bus0=a, bus1=b, r=R_KM * km, x=X_KM * km, b=B_KM * km, s_nom=S_NOM)
    n.add("Generator", "thermal", bus="1", control="Slack", p_set=0.0)
    n.add("Generator", "pv", bus="3", control=pv_mode, p_set=pv_mw, q_set=0.0)
    n.add("Load", "city", bus="2", p_set=50.0, q_set=20.0)
    n.pf()
    return n


def report(n):
    flows = n.lines_t
    s = np.maximum(np.hypot(flows.p0, flows.q0), np.hypot(flows.p1, flows.q1)).iloc[0]
    return {"|V2|": n.buses_t.v_mag_pu.iloc[0]["2"], "|V3|": n.buses_t.v_mag_pu.iloc[0]["3"],
            "P_th MW": n.generators_t.p.iloc[0]["thermal"],
            "Q_th MVAr": n.generators_t.q.iloc[0]["thermal"],
            "Q_pv MVAr": n.generators_t.q.iloc[0]["pv"],
            "max load %": 100 * (s / n.lines.s_nom).max(),
            "loss MW": (flows.p0 + flows.p1).iloc[0].sum()}

# ---------------------------------------------------------------- Part A: design point
cases = {"no PV": network(0.0), "PV 30, unity PF": network(30.0),
         "PV 30, voltage ctrl": network(30.0, "PV")}
print("Part A - design point (city 50 MW + 20 MVAr, PV at 30 MW)")
print(pd.DataFrame({k: report(n) for k, n in cases.items()}).T.round(3).to_string())
n = cases["PV 30, unity PF"]
print("\nLine flows with 30 MW of PV (MW, MVAr):")
print(pd.DataFrame({"P0": n.lines_t.p0.iloc[0], "Q0": n.lines_t.q0.iloc[0],
                    "P1": n.lines_t.p1.iloc[0], "loss": n.lines_t.p0.iloc[0] + n.lines_t.p1.iloc[0]}).round(3))
print("Inverter capability at full output (33 MVA rating): Q_max = %.1f MVAr" % np.sqrt(33**2 - 30**2))

# ---------------------------------------------------------------- Part B: the real day
d = pypsa.Network("data/networks/niamey_3bus")         # same network + 24 h time series
d.pf()                                                  # one AC load flow per hour
day = pd.DataFrame({"demand": d.loads_t.p["city"], "PV": d.generators_t.p["pv"],
                    "thermal": d.generators_t.p["thermal"],
                    "losses": (d.lines_t.p0 + d.lines_t.p1).sum(axis=1),
                    "|V2|": d.buses_t.v_mag_pu["2"]})
day.index = day.index.hour
print("\nPart B - 4 May 2023, hourly (MW, p.u.)")
print(day.iloc[::3].round(2).to_string())
e = day[["demand", "PV", "thermal", "losses"]].sum()
print("Daily energy (MWh):", e.round(1).to_dict(), "| solar share %.1f %%" % (100 * e.PV / e.demand))
