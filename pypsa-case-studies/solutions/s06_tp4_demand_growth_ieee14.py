"""TP case 4 - IEEE 14-bus system: demand growth S0-S3 (and beyond), with reactive limits.

The network is the PyPSA dataset data/networks/ieee14 (MATPOWER case14.m, PGLib ratings).
Generator reactive limits are stored in the custom columns q_min, q_max.
Run from the repository root:  python solutions/s06_tp4_demand_growth_ieee14.py
"""
import logging
import warnings

import numpy as np
import pandas as pd
import pypsa

warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
BASE = pypsa.Network("data/networks/ieee14")
print(BASE.generators[["bus", "control", "p_set", "q_min", "q_max"]].to_string())


def solve_with_q_limits(n, max_iter=10):
    """AC load flow with PV -> PQ switching: a generator that hits a reactive limit loses
    its voltage control and is fixed at that limit; repeat until no limit is violated."""
    at_limit = []
    for _ in range(max_iter):
        if not n.pf()["converged"].all().all():         # no solution: beyond the nose point
            raise RuntimeError("load flow did not converge")
        q = n.generators_t.q.iloc[0]
        new = [(g, n.generators.at[g, "q_max"]) for g in n.generators.index[n.generators.control == "PV"]
               if q[g] > n.generators.at[g, "q_max"] + 1e-6]
        new += [(g, n.generators.at[g, "q_min"]) for g in n.generators.index[n.generators.control == "PV"]
                if q[g] < n.generators.at[g, "q_min"] - 1e-6]
        if not new:
            return at_limit
        for g, q_lim in new:
            n.generators.loc[g, ["control", "q_set"]] = ["PQ", q_lim]
            at_limit.append(g)
    raise RuntimeError("reactive limits did not settle")


def scenario(lam, q_limits=True):
    n = BASE.copy()
    n.loads[["p_set", "q_set"]] *= lam                  # every load grows by the same factor
    n.generators.loc["G2", "p_set"] *= lam              # G2 follows; the slack takes the rest
    at_limit = solve_with_q_limits(n) if q_limits else (n.pf() and [])
    v = n.buses_t.v_mag_pu.iloc[0]
    s = pd.concat([np.maximum(np.hypot(n.lines_t.p0, n.lines_t.q0), np.hypot(n.lines_t.p1, n.lines_t.q1)).iloc[0] / n.lines.s_nom,
                   np.hypot(n.transformers_t.p0, n.transformers_t.q0).iloc[0] / n.transformers.s_nom])
    loss = (n.lines_t.p0 + n.lines_t.p1).iloc[0].sum() + (n.transformers_t.p0 + n.transformers_t.p1).iloc[0].sum()
    return {"min|V|": round(v.min(), 3), "bus": v.idxmin(), "n<0.95": int((v < 0.95).sum()),
            "max%": round(100 * s.max(), 1), "line": s.idxmax(), "loss MW": round(loss, 2),
            "Q MVAr": round(n.generators_t.q.iloc[0].sum(), 1), "at Q limit": ",".join(at_limit) or "-"}

rows = {f"S{k} ({int(100*l)} %)": scenario(l) for k, l in enumerate([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])}
print("\nScenarios with reactive limits enforced")
print(pd.DataFrame(rows).T.round(3).to_string())
print("\nSame scenarios if reactive limits are ignored (PyPSA default): min |V| =")
print({k.split()[0]: scenario(l, False)["min|V|"] for k, l in zip(rows, [1.0, 1.1, 1.2, 1.3, 1.4, 1.5])})

lam = 1.0                                              # maximum loadability (step 0.01)
while True:
    try:
        r = scenario(round(lam + 0.01, 2))
        if r["min |V|"] < 0.5:
            break
        lam = round(lam + 0.01, 2)
    except Exception:
        break
print(f"\nMaximum loadability with reactive limits: lambda = {lam:.2f} "
      f"({BASE.loads.p_set.sum() * lam:.0f} MW, margin +{100 * (lam - 1):.0f} %)")
