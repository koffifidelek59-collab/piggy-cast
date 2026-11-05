"""Read MATPOWER case files (.m) and convert them to PyPSA networks.

MATPOWER stores a power system in per unit on a system base (baseMVA, usually
100 MVA). PyPSA stores line impedances in ohm and admittances in siemens, with
powers in MW / MVA and voltages in kV. The conversion is therefore:

    Z_base = V_nom^2 / S_base        (ohm,   with V_nom in kV and S_base in MVA)
    r_ohm  = r_pu * Z_base,   x_ohm = x_pu * Z_base,   b_S = b_pu / Z_base

Transformers keep per-unit impedances in PyPSA, but on their own rating s_nom:

    x_pu(s_nom) = x_pu(baseMVA) * s_nom / baseMVA

Bus shunts given in MW / MVAr at 1 p.u. become siemens:  b_S = B_MVAr / V_nom^2.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import pypsa

BUS_COLS = ["bus_i", "type", "Pd", "Qd", "Gs", "Bs", "area", "Vm", "Va",
            "baseKV", "zone", "Vmax", "Vmin"]
GEN_COLS = ["bus", "Pg", "Qg", "Qmax", "Qmin", "Vg", "mBase", "status", "Pmax", "Pmin"]
BRANCH_COLS = ["fbus", "tbus", "r", "x", "b", "rateA", "rateB", "rateC",
               "ratio", "angle", "status", "angmin", "angmax"]
GENCOST_COLS = ["model", "startup", "shutdown", "ncost", "c2", "c1", "c0"]


def _block(text: str, name: str, cols: list[str]) -> pd.DataFrame | None:
    """Return the numeric matrix `mpc.<name> = [ ... ];` as a DataFrame."""
    m = re.search(rf"mpc\.{name}\s*=\s*\[(.*?)\];", text, re.S)
    if m is None:
        return None
    rows = []
    for line in m.group(1).splitlines():
        line = line.split("%")[0].strip().rstrip(";").strip()
        if line:
            rows.append([float(v) for v in line.split()])
    arr = np.array(rows)
    return pd.DataFrame(arr[:, : len(cols)], columns=cols[: arr.shape[1]])


def read_matpower(path) -> dict:
    """Parse a MATPOWER version-2 case file into a dict of DataFrames."""
    text = open(path, encoding="utf-8").read()
    base = float(re.search(r"mpc\.baseMVA\s*=\s*([\d.]+)", text).group(1))
    return {
        "baseMVA": base,
        "bus": _block(text, "bus", BUS_COLS),
        "gen": _block(text, "gen", GEN_COLS),
        "branch": _block(text, "branch", BRANCH_COLS),
        "gencost": _block(text, "gencost", GENCOST_COLS),
    }


def matpower_to_pypsa(mpc: dict, name: str = "matpower case",
                      v_nom_default: float = 132.0) -> tuple[pypsa.Network, pd.DataFrame]:
    """Build a PyPSA network from a parsed MATPOWER case.

    Returns
    -------
    n      : the PyPSA network (one snapshot, 'now')
    qlims  : DataFrame indexed by generator name with columns q_min, q_max (MVAr).
             PyPSA's AC load flow does not enforce reactive limits; we keep them
             so that `pscs.kpi.enforce_q_limits` can apply PV->PQ switching.
    """
    base = mpc["baseMVA"]
    bus, gen, br = mpc["bus"], mpc["gen"], mpc["branch"]
    n = pypsa.Network(name=name)
    n.add("Carrier", "AC")

    # ------------------------------------------------------------------ buses
    v_nom = {}
    for _, b in bus.iterrows():
        bid = str(int(b.bus_i))
        v_nom[bid] = b.baseKV if b.baseKV > 0 else v_nom_default
        n.add("Bus", bid, v_nom=v_nom[bid], carrier="AC",
              v_mag_pu_set=b.Vm, v_mag_pu_min=b.Vmin, v_mag_pu_max=b.Vmax)
        if b.Pd != 0 or b.Qd != 0:
            n.add("Load", f"load_{bid}", bus=bid, p_set=b.Pd, q_set=b.Qd)
        if b.Gs != 0 or b.Bs != 0:
            vn2 = v_nom[bid] ** 2
            n.add("ShuntImpedance", f"shunt_{bid}", bus=bid, g=b.Gs / vn2, b=b.Bs / vn2)

    # ------------------------------------------------------------ generators
    cost = mpc.get("gencost")
    qlims = {}
    for k, g in gen.iterrows():
        if g.status <= 0:
            continue
        bid = str(int(g.bus))
        btype = int(bus.loc[bus.bus_i == g.bus, "type"].iloc[0])
        control = {3: "Slack", 2: "PV"}.get(btype, "PQ")
        gname = f"G{bid}"
        mc = mcq = 0.0
        if cost is not None and len(cost) > k and int(cost.loc[k, "model"]) == 2:
            mc, mcq = cost.loc[k, "c1"], cost.loc[k, "c2"]
        n.add("Generator", gname, bus=bid, control=control, carrier="AC",
              p_set=g.Pg, q_set=g.Qg, p_nom=max(g.Pmax, g.Pg, 1.0),
              p_min_pu=g.Pmin / max(g.Pmax, 1.0) if g.Pmax > 0 else 0.0,
              marginal_cost=mc, marginal_cost_quadratic=mcq)
        n.buses.loc[bid, "v_mag_pu_set"] = g.Vg            # voltage set point of PV/slack bus
        qlims[gname] = {"q_min": g.Qmin, "q_max": g.Qmax}

    # -------------------------------------------------------------- branches
    for k, r in br.iterrows():
        if r.status <= 0:
            continue
        f, t = str(int(r.fbus)), str(int(r.tbus))
        if r.ratio != 0:                                   # off-nominal tap: transformer
            s_nom = r.rateA if r.rateA > 0 else base
            n.add("Transformer", f"T{f}-{t}", bus0=f, bus1=t, s_nom=s_nom,
                  r=r.r * s_nom / base, x=r.x * s_nom / base, b=r.b * s_nom / base,
                  tap_ratio=r.ratio, tap_side=0, phase_shift=r.angle, model="pi")
        else:                                              # line: convert p.u. to ohm/siemens
            zb = v_nom[f] ** 2 / base
            n.add("Line", f"L{f}-{t}", bus0=f, bus1=t, r=r.r * zb, x=r.x * zb,
                  b=r.b / zb, s_nom=r.rateA if r.rateA > 0 else 0.0)
    return n, pd.DataFrame(qlims).T
