"""AC load-flow helpers and the operational indicators reported in every case study.

Indicators (one value per snapshot)
-----------------------------------
v_min, v_max        : lowest / highest bus voltage (p.u.)
n_under, n_over     : number of buses outside [v_low, v_high]
max_loading_pct     : highest branch loading = max(|S_from|, |S_to|) / s_nom
losses_mw           : active losses = sum over branches of (P_from + P_to)
slack_p, slack_q    : power delivered by the slack generator
gen_q_mvar          : total reactive power produced by all generators
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pypsa


def one_snapshot(n: pypsa.Network, sn) -> pypsa.Network:
    """Copy of the network restricted to a single snapshot (keeps its time-series values)."""
    m = n.copy()
    m.set_snapshots([sn])
    return m


def run_pf(n: pypsa.Network, snapshots=None) -> dict:
    """Run PyPSA's Newton-Raphson AC load flow and fail loudly if it diverges."""
    out = n.pf(snapshots=snapshots)
    conv = out["converged"]
    ok = bool(np.asarray(conv.values if hasattr(conv, "values") else conv).all())
    if not ok:
        raise RuntimeError("AC load flow did not converge")
    return out


def bus_table(n: pypsa.Network, sn=None) -> pd.DataFrame:
    sn = n.snapshots[0] if sn is None else sn
    return pd.DataFrame({
        "v_nom (kV)": n.buses.v_nom,
        "|V| (p.u.)": n.buses_t.v_mag_pu.loc[sn],
        "angle (deg)": np.degrees(n.buses_t.v_ang.loc[sn]),
        "P inj (MW)": n.buses_t.p.loc[sn],
        "Q inj (MVAr)": n.buses_t.q.loc[sn],
    })


def branch_table(n: pypsa.Network, sn=None) -> pd.DataFrame:
    """Flows, losses and loading of lines and transformers for one snapshot."""
    sn = n.snapshots[0] if sn is None else sn
    frames = []
    for c, df, dft in (("Line", n.lines, n.lines_t), ("Transformer", n.transformers, n.transformers_t)):
        if df.empty:
            continue
        p0, q0 = dft.p0.loc[sn], dft.q0.loc[sn]
        p1, q1 = dft.p1.loc[sn], dft.q1.loc[sn]
        s = np.maximum(np.hypot(p0, q0), np.hypot(p1, q1))
        s_nom = df.s_nom.replace(0, np.nan)
        frames.append(pd.DataFrame({
            "type": c, "from": df.bus0, "to": df.bus1,
            "P_from (MW)": p0, "Q_from (MVAr)": q0, "P_to (MW)": p1,
            "loss (MW)": p0 + p1, "|S| (MVA)": s, "rating (MVA)": df.s_nom,
            "loading (%)": 100 * s / s_nom,
        }))
    return pd.concat(frames)


def kpis(n: pypsa.Network, sn=None, v_low=0.95, v_high=1.05) -> dict:
    sn = n.snapshots[0] if sn is None else sn
    v = n.buses_t.v_mag_pu.loc[sn]
    br = branch_table(n, sn)
    slack = n.generators.index[n.generators.control == "Slack"]
    return {
        "v_min (p.u.)": v.min(), "bus v_min": v.idxmin(),
        "v_max (p.u.)": v.max(),
        "buses < %.2f" % v_low: int((v < v_low - 1e-9).sum()),
        "buses > %.2f" % v_high: int((v > v_high + 1e-9).sum()),
        "max loading (%)": br["loading (%)"].max(),
        "most loaded": br["loading (%)"].idxmax() if br["loading (%)"].notna().any() else None,
        "losses (MW)": br["loss (MW)"].sum(),
        "slack P (MW)": n.generators_t.p.loc[sn, slack].sum(),
        "slack Q (MVAr)": n.generators_t.q.loc[sn, slack].sum(),
        "gen Q total (MVAr)": n.generators_t.q.loc[sn].sum(),
    }


def enforce_q_limits(n: pypsa.Network, qlims: pd.DataFrame, max_iter: int = 10) -> list:
    """PV -> PQ switching: the standard way to respect generator reactive limits.

    PyPSA holds PV-bus voltages whatever reactive power it takes. Real machines
    cannot: when a generator hits Q_max (or Q_min) it loses voltage control and
    behaves as a PQ injection fixed at that limit. We repeat the load flow until
    no PV generator violates its limit. Works on the first snapshot.
    Returns the list of (generator, limit hit, Q fixed in MVAr).
    """
    sn = n.snapshots[0]
    switched = []
    for _ in range(max_iter):
        run_pf(n, sn)
        q = n.generators_t.q.loc[sn]
        pv = n.generators.index[n.generators.control == "PV"]
        new = []
        for g in pv.intersection(qlims.index):
            if q[g] > qlims.at[g, "q_max"] + 1e-6:
                new.append((g, "Q_max", qlims.at[g, "q_max"]))
            elif q[g] < qlims.at[g, "q_min"] - 1e-6:
                new.append((g, "Q_min", qlims.at[g, "q_min"]))
        if not new:
            return switched
        for g, lim, val in new:
            n.generators.loc[g, "control"] = "PQ"
            n.generators.loc[g, "q_set"] = val
        switched += new
    raise RuntimeError("Q-limit enforcement did not settle")
