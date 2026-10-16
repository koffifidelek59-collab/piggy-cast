"""Chapter 6 (Lesson 5) with PyPSA: the five-bus system of Glover Example 6.9.

Shows how the textbook per-unit data are entered in PyPSA, solves the AC power flow
(Newton-Raphson, n.pf()) and the linear "DC" power flow (n.lpf()), and compares with
Tables 6.6 to 6.8 of the book and with our own solver (04_power_flow_newton_raphson.py).

PyPSA units: power in MW / Mvar, voltages in kV, line impedances in ohm and susceptances
in siemens; transformer r and x in per unit on the transformer's own s_nom.

Run: python3 05_power_flow_pypsa.py
"""
import math
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore")
pd.set_option("display.precision", 3)

S_BASE = 100.0                      # MVA


def build_network():
    n = pypsa.Network()
    v_nom = {"1": 15.0, "2": 345.0, "3": 15.0, "4": 345.0, "5": 345.0}
    for b, v in v_nom.items():
        n.add("Bus", b, v_nom=v)

    # lines: per-unit data converted to ohm and siemens with Zbase = V^2 / Sbase
    z_base = 345.0**2 / S_BASE
    for name, (b0, b1, r, x, b_tot) in {
        "2-4": ("2", "4", 0.0090, 0.100, 1.72),
        "2-5": ("2", "5", 0.0045, 0.050, 0.88),
        "4-5": ("4", "5", 0.00225, 0.025, 0.44),
    }.items():
        n.add("Line", name, bus0=b0, bus1=b1, r=r * z_base, x=x * z_base,
              b=b_tot / z_base, s_nom=1200)

    # transformers: per unit on s_nom, so use s_nom = system base (100 MVA)
    n.add("Transformer", "T1-5", bus0="1", bus1="5", r=0.0015, x=0.02, s_nom=S_BASE)
    n.add("Transformer", "T3-4", bus0="3", bus1="4", r=0.00075, x=0.01, s_nom=S_BASE)

    # generators: slack at bus 1 (|V| = 1.0), PV at bus 3 (P = 520 MW, |V| = 1.05)
    n.add("Generator", "G1", bus="1", control="Slack", p_set=0)   # p_set must be set (not NaN)
    n.add("Generator", "G3", bus="3", control="PV", p_set=520)
    n.buses.loc["1", "v_mag_pu_set"] = 1.00
    n.buses.loc["3", "v_mag_pu_set"] = 1.05

    n.add("Load", "L2", bus="2", p_set=800, q_set=280)
    n.add("Load", "L3", bus="3", p_set=80, q_set=40)
    return n


if __name__ == "__main__":
    n = build_network()
    info = n.pf()
    print("=" * 72)
    print("AC power flow with PyPSA (Newton-Raphson):",
          "converged" if bool(np.all(info["converged"])) else "NOT converged",
          f"in {int(np.max(info['n_iter'].values))} iterations")

    res = pd.DataFrame({
        "|V| pu": n.buses_t.v_mag_pu.iloc[0],
        "angle deg": np.degrees(n.buses_t.v_ang.iloc[0]),
    })
    res["book |V|"] = [1.000, 0.834, 1.050, 1.019, 0.974]
    res["book angle"] = [0.0, -22.407, -0.597, -2.834, -4.548]
    print(res.round(3))

    g = n.generators_t
    print(f"\nG1 (slack): P = {g.p.iloc[0]['G1']:.1f} MW, Q = {g.q.iloc[0]['G1']:.1f} Mvar"
          "   (book: 394.8 MW, 114.4 Mvar)")
    print(f"G3 (PV):    P = {g.p.iloc[0]['G3']:.1f} MW, Q = {g.q.iloc[0]['G3']:.1f} Mvar"
          "   (book: 520 MW, 337.6 Mvar)")

    flows = pd.DataFrame({
        "P0 MW": n.lines_t.p0.iloc[0], "Q0 Mvar": n.lines_t.q0.iloc[0],
        "P1 MW": n.lines_t.p1.iloc[0], "Q1 Mvar": n.lines_t.q1.iloc[0],
    })
    print("\nLine flows (P0, Q0 leave bus0; P1, Q1 leave bus1):")
    print(flows.round(1))
    print("Book Table 6.7: 2-4: -292.0/-139.2 and 303.6/121.6 ; 2-5: -508.0/-140.8 and"
          " 525.6/263.2 ; 4-5: 134.4/150.4 and -133.2/-182.4")
    losses = n.generators_t.p.iloc[0].sum() - n.loads.p_set.sum()   # book: 914.8 - 880 = 34.8 MW
    print(f"\nTotal losses = {losses:.1f} MW")

    # ---------------- PyPSA's Ybus equals our hand-built Ybus ----------------
    n.determine_network_topology()
    sub = n.sub_networks.obj.iloc[0]
    sub.calculate_Y()
    order = [int(b) - 1 for b in sub.buses_o]
    Y = np.empty((5, 5), dtype=complex)
    Y[np.ix_(order, order)] = sub.Y.toarray()
    print("\nPyPSA Ybus converted to per unit on the 100 MVA base (PyPSA works on 1 MVA):")
    print(np.round(Y / S_BASE, 4))

    # ---------------- linear ("DC") power flow ----------------
    n_dc = build_network()
    n_dc.lpf()
    dc = pd.DataFrame({
        "AC angle deg": res["angle deg"],
        "DC angle deg": np.degrees(n_dc.buses_t.v_ang.iloc[0]),
    })
    print("\nDC power flow: |V| = 1, no losses, P depends only on angles:")
    print(dc.round(2))
    print("DC line flows (MW):", n_dc.lines_t.p0.iloc[0].round(1).to_dict(),
          "\nAC line flows (MW):", n.lines_t.p0.iloc[0].round(1).to_dict())
    print("The DC approximation is good for active power but ignores Q, |V| and losses;"
          " here bus 2 is heavily loaded (|V| = 0.83 pu), so errors are larger than usual.")
    _ = math
