"""TP case 5 - Solar plant at bus 14 of the IEEE 14-bus system: hosting capacity, reverse
power flow, battery storage. Real solar profile of 16 March 2023 (Niamey).

Dataset data/networks/ieee14_pv_day: IEEE 14 + PV plant 'pv14' + battery 'battery14' at
bus 14, 24 hourly snapshots. Run:  python solutions/s07_tp5_solar_storage_ieee14.py
"""
import logging
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
DAY = pypsa.Network("data/networks/ieee14_pv_day")
CF = DAY.generators_t.p_max_pu["pv14"]                  # real hourly capacity factor
NOON = CF.idxmax()
MONITORED = ["4", "5", "9", "10", "11", "12", "13", "14"]  # customer buses + PV bus
V_MIN, V_MAX, TAN = 0.94, 1.06, np.tan(np.arccos(0.95))


def q_limited_pf(n):
    """AC load flow with generator reactive limits (PV -> PQ switching), first snapshot."""
    for _ in range(10):
        if not n.pf(snapshots=n.snapshots[:1])["converged"].all().all():
            raise RuntimeError("no load-flow solution")
        q = n.generators_t.q.iloc[0]
        pv = n.generators.index[(n.generators.control == "PV") & n.generators.q_max.notna()]
        hit = [g for g in pv if q[g] > n.generators.at[g, "q_max"] + 1e-6 or q[g] < n.generators.at[g, "q_min"] - 1e-6]
        if not hit:
            return
        for g in hit:
            lim = "q_max" if q[g] > n.generators.at[g, "q_max"] else "q_min"
            n.generators.loc[g, ["control", "q_set"]] = ["PQ", n.generators.at[g, lim]]


def lower_set_points(n, dv):
    buses = n.generators.bus[n.generators.control.isin(["PV", "Slack"])]
    n.buses.loc[buses, "v_mag_pu_set"] -= dv


def at_noon(pv_mw, absorb=False, dv=0.0):
    n = DAY.copy()
    n.set_snapshots([NOON])
    lower_set_points(n, dv)
    n.generators_t.p_set.loc[:, "pv14"] = pv_mw
    n.generators_t.q_set.loc[:, "pv14"] = -TAN * pv_mw if absorb else 0.0   # PF 0.95 absorbing
    n.storage_units_t.p_set.loc[:, "battery14"] = 0.0
    q_limited_pf(n)
    return n


def first_violation(n):
    v = n.buses_t.v_mag_pu.iloc[0][MONITORED]
    s = pd.concat([np.hypot(n.lines_t.p0, n.lines_t.q0).iloc[0] / n.lines.s_nom,
                   np.hypot(n.transformers_t.p0, n.transformers_t.q0).iloc[0] / n.transformers.s_nom])
    if v.max() > V_MAX + 1e-9:
        return "overvoltage"
    if v.min() < V_MIN - 1e-9:
        return "undervoltage"
    return "thermal" if s.max() > 1 else None


# ---------------------------------------------------------- 1. hosting capacity at noon
print("1. Hosting capacity of bus 14 at noon (1 MW steps)")
for name, absorb, dv in [("unity PF, original set points", False, 0.0),
                         ("unity PF, set points -0.03 p.u.", False, 0.03),
                         ("PF 0.95 absorbing, set points -0.03", True, 0.03)]:
    for p in range(0, 251):
        try:
            why = first_violation(at_noon(p, absorb, dv))
        except RuntimeError:
            why = "no solution"
        if why:
            print(f"   {name:38s}: {p - 1:4d} MW (limited by {why})")
            break

# ---------------------------------------------------------- 2. reverse power flow
print("\n2. Flow into bus 14 at noon (original set points, MW)")
for p in [0, 10, 14, 20, 50, 100]:
    n = at_noon(p)
    flow = n.lines_t.p0.iloc[0][["L9-14", "L13-14"]]
    print(f"   PV {p:3d} MW: 9->14 {flow['L9-14']:7.2f}, 13->14 {flow['L13-14']:7.2f}, total {flow.sum():7.2f}")

# ---------------------------------------------------------- 3. the five scenarios over 24 h
def battery(pv, p_max=50.0, e_max=200.0, eta=0.95):
    """Peak shaving: store the PV above the lowest threshold whose surplus fits in e_max,
    return the energy evenly from 18:00 to 22:00. Sign: + discharge, - charge (PyPSA)."""
    lo, hi = 0.0, float(pv.max())
    for _ in range(50):
        t = (lo + hi) / 2
        lo, hi = (t, hi) if (pv - t).clip(0, p_max).sum() * eta > e_max else (lo, t)
    charge = (pv - hi).clip(0, p_max)
    evening = (pv.index.hour >= 18) & (pv.index.hour < 22)
    out = -charge
    out[evening] = min(p_max, charge.sum() * eta * eta / evening.sum())
    return out


def day(pv_mw, bat=False, absorb=False, dv=0.0):
    n = DAY.copy()
    lower_set_points(n, dv)
    pv = pv_mw * CF
    n.generators_t.p_set["pv14"] = pv
    n.generators_t.q_set["pv14"] = -TAN * pv if absorb else 0 * pv
    n.storage_units_t.p_set["battery14"] = battery(pv) if bat else 0 * pv
    n.pf()
    vmon = n.buses_t.v_mag_pu[MONITORED].max(axis=1)
    inflow = n.lines_t.p0["L9-14"] + n.lines_t.p0["L13-14"]
    return {"max V14": n.buses_t.v_mag_pu["14"].max(), "overV h": int((vmon > V_MAX + 1e-9).sum()),
            "reverse h": int((inflow < 0).sum()), "export MW": max(0.0, -inflow.min()),
            "loss MWh": ((n.lines_t.p0 + n.lines_t.p1).sum(axis=1)
                             + (n.transformers_t.p0 + n.transformers_t.p1).sum(axis=1)).sum()}

rows = {"S0 no PV": day(0), "S1 PV 50": day(50), "S2 PV 100": day(100),
        "S3 PV 100 + battery": day(100, bat=True),
        "S4 S3 + PF0.95 + setpts": day(100, bat=True, absorb=True, dv=0.03)}
print("\n3. Scenarios over 16 March 2023")
print(pd.DataFrame(rows).T.round(3).to_string())
