"""TP case 3 - IEEE 9-bus system: congestion, N-1 security, redispatch and nodal prices.

Official data of MATPOWER case9.m (100 MVA base, 345 kV), written out below.
Scenario: hot-season ratings (-15 %) and evening peak (+15 % demand).
Run from the repository root:  python solutions/s05_tp3_congestion_ieee9.py
"""
import logging
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
S_B, V_N = 100.0, 345.0
Z_B = V_N**2 / S_B
# MATPOWER case9 branch data: from, to, r, x, b (p.u.), rateA (MVA)
BRANCH = [(1, 4, 0.0, 0.0576, 0.0, 250), (4, 5, 0.017, 0.092, 0.158, 250),
          (5, 6, 0.039, 0.17, 0.358, 150), (3, 6, 0.0, 0.0586, 0.0, 300),
          (6, 7, 0.0119, 0.1008, 0.209, 150), (7, 8, 0.0085, 0.072, 0.149, 250),
          (8, 2, 0.0, 0.0625, 0.0, 250), (8, 9, 0.032, 0.161, 0.306, 250),
          (9, 4, 0.01, 0.085, 0.176, 250)]
# generators: bus, P (MW), V set point, cost c2 ($/MW^2h), c1 ($/MWh), c0 ($/h), Pmax
GEN = [(1, 72.3, 1.04, 0.11, 5.0, 150, 250), (2, 163.0, 1.025, 0.085, 1.2, 600, 300),
       (3, 85.0, 1.025, 0.1225, 1.0, 335, 270)]
LOAD = [(5, 90, 30), (7, 100, 35), (9, 125, 50)]           # bus, P (MW), Q (MVAr)
DERATE, GROWTH = 0.85, 1.15
RADIAL = ["L1-4", "L3-6", "L8-2"]                           # generator connections


def network(dispatch=None, outage=None, cap9=0.0, rating_56=None):
    n = pypsa.Network()
    for b in range(1, 10):
        n.add("Bus", str(b), v_nom=V_N)
    for f, t, r, x, b, rate in BRANCH:                      # p.u. -> ohm and siemens
        n.add("Line", f"L{f}-{t}", bus0=str(f), bus1=str(t), r=r * Z_B, x=x * Z_B, b=b / Z_B,
              s_nom=rate * DERATE)
    if rating_56:
        n.lines.loc["L5-6", "s_nom"] = rating_56
    for k, (b, p, vset, c2, c1, c0, pmax) in enumerate(GEN):
        n.buses.loc[str(b), "v_mag_pu_set"] = vset
        n.add("Generator", f"G{b}", bus=str(b), control="Slack" if k == 0 else "PV",
              p_nom=pmax, p_min_pu=10 / pmax, marginal_cost=c1, marginal_cost_quadratic=c2,
              p_set=np.nan if dispatch is None else dispatch[f"G{b}"])
    for b, p, q in LOAD:
        n.add("Load", f"D{b}", bus=str(b), p_set=p * GROWTH, q_set=q * GROWTH)
    if outage:
        n.lines.loc[outage, "active"] = False
    if cap9:
        n.add("ShuntImpedance", "cap9", bus="9", b=cap9 / V_N**2)
    return n


def loading(n):
    s = np.maximum(np.hypot(n.lines_t.p0, n.lines_t.q0), np.hypot(n.lines_t.p1, n.lines_t.q1)).iloc[0]
    return 100 * s / n.lines.s_nom


C0 = sum(g[5] for g in GEN)
opts = dict(solver_name="highs", solver_options={"output_flag": False})
# ---------------------------------------------------------- 1. economic dispatch (DC-OPF)
n = network(); n.optimize(**opts)                       # p_set = NaN: dispatch is free
ed = n.generators_t.p.iloc[0]
print("1. Economic dispatch (MW):", ed.round(1).to_dict(), "| cost %.0f $/h" % (n.objective + C0))
print("   LMP %.2f $/MWh at every bus" % n.buses_t.marginal_price.iloc[0].mean())
cost_ed = n.objective + C0

# ---------------------------------------------------------- 2. AC check, intact grid
m = network(ed); m.pf()
print("2. Intact grid: max loading %.1f %%, min |V| %.3f p.u." % (loading(m).max(), m.buses_t.v_mag_pu.iloc[0].min()))

# ---------------------------------------------------------- 3. N-1 screening (AC)
def n1(dispatch, **kw):
    rows = []
    for out in [l for l in network().lines.index if l not in RADIAL]:
        m = network(dispatch, outage=out, **kw); m.pf()
        L = loading(m).drop(out)
        rows.append({"outage": out, "worst line": L.idxmax(), "loading (%)": L.max(),
                     "min |V|": m.buses_t.v_mag_pu.iloc[0].min()})
    return pd.DataFrame(rows).set_index("outage").round(3)

print("3. N-1 screening of the economic dispatch\n", n1(ed).to_string())

# ---------------------------------------------------------- 4. security-constrained OPF
n = network()
n.optimize.optimize_security_constrained(branch_outages=[l for l in n.lines.index if l not in RADIAL], **opts)
sc = n.generators_t.p.iloc[0]
lmp = n.buses_t.marginal_price.iloc[0]
print("4. Secure dispatch (MW):", sc.round(1).to_dict(), "| extra cost %.1f $/h" % (n.objective + C0 - cost_ed))
print("   LMP %.2f-%.2f $/MWh" % (lmp.min(), lmp.max()))
print("   N-1 screening of the secure dispatch\n", n1(sc).to_string())

# ---------------------------------------------------------- 5. voltage support at bus 9
lo, hi = 0.0, 300.0                     # bisection on the post-outage voltage of bus 9
for _ in range(30):
    mid = (lo + hi) / 2
    m = network(sc, outage="L9-4", cap9=mid); m.pf()
    lo, hi = (mid, hi) if m.buses_t.v_mag_pu.iloc[0]["9"] < 0.95 else (lo, mid)
m = network(sc, outage="L9-4", cap9=hi); m.pf()
print("5. Loss of 9-4: %.0f MVAr at bus 9 restores %.3f p.u.; worst loading %.1f %%"
      % (hi, m.buses_t.v_mag_pu.iloc[0]["9"], loading(m).drop("L9-4").max()))

# ---------------------------------------------------------- 6. reinforcement option
print("6. Line 5-6 uprated to 200 MVA, economic dispatch: worst N-1 loading %.1f %%"
      % n1(ed, rating_56=200)["loading (%)"].max())
