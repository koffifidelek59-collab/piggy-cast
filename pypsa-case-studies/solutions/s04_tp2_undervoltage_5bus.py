"""TP case 2 - Five-bus network: undervoltage at a remote industrial zone, and its remedies.

Run from the repository root:  python solutions/s04_tp2_undervoltage_5bus.py
"""
import logging
import warnings

import pandas as pd
import pypsa

warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
R_KM, X_KM, B_KM = 0.12, 0.39, 2.9e-6                  # 132 kV ACSR 240/40, per km
LINES = [("L1-2", "1", "2", 30), ("L1-3", "1", "3", 25), ("L2-4", "2", "4", 35),
         ("L3-4", "3", "4", 30), ("L4-5", "4", "5", 85)]          # the 85 km feeder to bus 5
LOADS = [("substation", "2", 25, 8), ("urban", "4", 45, 15), ("industry", "5", 35, 18)]


def network(pv_mw=0.0, remedy=None):
    n = pypsa.Network()
    for b in "12345":
        n.add("Bus", b, v_nom=132, v_mag_pu_set=1.02 if b == "1" else 1.0)
    for name, a, b, km in LINES:
        n.add("Line", name, bus0=a, bus1=b, r=R_KM * km, x=X_KM * km, b=B_KM * km, s_nom=100)
    n.add("Generator", "thermal", bus="1", control="Slack", p_set=0.0)
    n.add("Generator", "pv", bus="3", control="PQ", p_set=pv_mw, q_set=0.0)
    for name, bus, p, q in LOADS:
        n.add("Load", name, bus=bus, p_set=p, q_set=q)
    if remedy:
        remedy(n)
    n.pf()
    return n


def v(n):
    return n.buses_t.v_mag_pu.iloc[0]


def losses(n):
    return (n.lines_t.p0 + n.lines_t.p1).iloc[0].sum()

# ---------------------------------------------------------- 1. voltage profile
A, B = network(pv_mw=40.0), network(pv_mw=0.0)
print("1. Voltage profile (p.u.)")
print(pd.DataFrame({"A: PV 40 MW": v(A), "B: evening peak, no PV": v(B)}).round(4).T.to_string())
print("losses A %.2f MW, B %.2f MW" % (losses(A), losses(B)))

# ---------------------------------------------------------- 2. remedies (worst case B)
def capacitor(q):                       # shunt capacitor bank of q MVAr at 1 p.u.
    return lambda n: n.add("ShuntImpedance", "cap5", bus="5", b=q / 132**2)


def setpoint(n):                        # raise the plant voltage set point
    n.buses.loc["1", "v_mag_pu_set"] = 1.05


def second_circuit(n):                  # double the 4-5 line: impedance / 2, charging x 2
    n.lines.loc["L4-5", ["r", "x"]] /= 2
    n.lines.loc["L4-5", "b"] *= 2


def pv_q_at_night(n):                   # PV inverters as a STATCOM holding 1.03 p.u. at bus 3
    n.generators.loc["pv", "control"] = "PV"
    n.buses.loc["3", "v_mag_pu_set"] = 1.03


def svc(n):                             # SVC/STATCOM at bus 5 holding 0.97 p.u.
    n.add("Generator", "svc5", bus="5", control="PV", p_set=0.0)
    n.buses.loc["5", "v_mag_pu_set"] = 0.97

rows = {}
for name, fn in [("none", None), ("capacitor 15 MVAr", capacitor(15)), ("set point 1.05", setpoint),
                 ("second circuit", second_circuit), ("PV Q-at-night", pv_q_at_night), ("SVC at bus 5", svc)]:
    n = network(0.0, fn)
    q_dev = n.generators_t.q.iloc[0].get("svc5", n.generators_t.q.iloc[0]["pv"])
    rows[name] = {"V5 (p.u.)": v(n)["5"], "V1 (p.u.)": v(n)["1"], "losses (MW)": losses(n),
                  "Q of device (MVAr)": q_dev if name in ("PV Q-at-night", "SVC at bus 5") else None}
print("\n2. Remedies at the evening peak")
print(pd.DataFrame(rows).T.round(4).to_string())

# ---------------------------------------------------------- 3. size the capacitor bank
lo, hi = 0.0, 30.0                       # bisection: smallest Q giving V5 >= 0.95 p.u.
for _ in range(30):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if v(network(0.0, capacitor(mid)))["5"] < 0.95 else (lo, mid)
print(f"\n3. Smallest capacitor bank: {hi:.1f} MVAr -> choose 15 MVAr (3 x 5 MVAr steps)")

# ---------------------------------------------------------- 4. the real day, with the bank
d0 = pypsa.Network("data/networks/niamey_5bus"); d0.pf()
d1 = pypsa.Network("data/networks/niamey_5bus")
d1.add("ShuntImpedance", "cap5", bus="5", b=15 / 132**2); d1.pf()
day = pd.DataFrame({"V5 no bank": d0.buses_t.v_mag_pu["5"], "V5 15 MVAr": d1.buses_t.v_mag_pu["5"]})
day.index = day.index.hour
print("\n4. Real day 4 May 2023 (every 3 h)\n", day.iloc[::3].round(3).T.to_string())
print("hours < 0.95 p.u.: no bank %d, with bank %d" % ((day.iloc[:, 0] < 0.95).sum(), (day.iloc[:, 1] < 0.95).sum()))
