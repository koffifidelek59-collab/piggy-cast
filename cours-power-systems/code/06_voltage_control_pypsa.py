"""Voltage control with reactive power (Day 3 paper: Mahmud et al., and Chapter 11).

Two-bus 11 kV distribution feeder with a distributed generator (DG). Illustrates the
key result of the paper, dV ~ (R P + X Q) / V:
  * a load alone causes a voltage DROP along the feeder,
  * a DG exporting active power causes a voltage RISE that can exceed the limit,
  * absorbing reactive power at the DG brings the voltage back within limits.
The approximation is compared with the exact AC power flow computed by PyPSA.

Illustrative data (not from the paper): 11 kV, 8 km of overhead line,
r = 0.30 ohm/km, x = 0.35 ohm/km, voltage limit 1.05 pu.

Run: python3 06_voltage_control_pypsa.py
"""
import warnings

import pypsa

warnings.filterwarnings("ignore")

V_NOM = 11.0                      # kV
R, X = 0.30 * 8, 0.35 * 8         # ohm, whole feeder
V_MIN, V_MAX = 0.95, 1.05


def feeder(p_load, q_load, p_dg=0.0, q_dg=0.0):
    """Return the exact |V| at the end of the feeder (pu) from a PyPSA AC power flow."""
    n = pypsa.Network()
    n.add("Bus", "substation", v_nom=V_NOM)
    n.add("Bus", "end", v_nom=V_NOM)
    n.add("Line", "feeder", bus0="substation", bus1="end", r=R, x=X)
    n.add("Generator", "grid", bus="substation", control="Slack", p_set=0)
    n.buses.loc["substation", "v_mag_pu_set"] = 1.0
    n.add("Load", "load", bus="end", p_set=p_load, q_set=q_load)
    # PQ generator: q_set < 0 means the DG absorbs reactive power
    n.add("Generator", "DG", bus="end", control="PQ", p_set=p_dg, q_set=q_dg)
    n.pf()
    return float(n.buses_t.v_mag_pu.iloc[0]["end"])


def approx_rise(p_net, q_net):
    """dV ~ (R P + X Q) / V^2 in pu, with P, Q the net injection at the feeder end (MW, Mvar)."""
    return (R * p_net + X * q_net) / V_NOM**2


cases = [
    ("Load 2 MW + 0.6 Mvar, no DG", 2.0, 0.6, 0.0, 0.0),
    ("Light load 0.5 MW, DG exports 5 MW at pf 1", 0.5, 0.15, 5.0, 0.0),
]
print("=" * 72)
print(f"11 kV feeder: R = {R:.1f} ohm, X = {X:.1f} ohm, R/X = {R/X:.2f}")
for label, pl, ql, pg, qg in cases:
    v = feeder(pl, ql, pg, qg)
    dv = approx_rise(pg - pl, qg - ql)
    status = ("OK" if V_MIN <= v <= V_MAX
              else f"ABOVE {V_MAX} pu" if v > V_MAX else f"BELOW {V_MIN} pu")
    print(f"  {label:45s}: |V_end| = {v:.4f} pu (approx 1 + RP + XQ = {1 + dv:.4f})  {status}")

# Reactive power the DG must absorb to bring the voltage back to the limit
pl, ql, pg = 0.5, 0.15, 5.0
q_needed = ((V_MAX - 1) * V_NOM**2 - R * (pg - pl)) / X + ql      # from the approximation
v = feeder(pl, ql, pg, q_needed)
print(f"\n  Approximation: absorb {-q_needed:.2f} Mvar -> exact |V_end| = {v:.4f} pu (overshoots)")

lo, hi = q_needed, 0.0                       # exact value by bisection on the AC power flow
for _ in range(30):
    mid = (lo + hi) / 2
    lo, hi = (lo, mid) if feeder(pl, ql, pg, mid) > V_MAX else (mid, hi)
q_exact = (lo + hi) / 2
print(f"  Exact (bisection on PyPSA power flow): absorb {-q_exact:.2f} Mvar "
      f"-> |V_end| = {feeder(pl, ql, pg, q_exact):.4f} pu")
print(f"  i.e. the DG runs at power factor {pg / (pg**2 + q_exact**2) ** 0.5:.3f} (absorbing)")

# Why reactive power is less effective in distribution grids: high R/X
print("\n  Voltage change per Mvar absorbed vs per MW curtailed:")
print(f"    1 Mvar absorbed -> {X / V_NOM**2:.4f} pu ;  1 MW curtailed -> {R / V_NOM**2:.4f} pu")
print("    In a transmission line (R/X ~ 0.1) reactive power dominates voltage control;")
print("    in a distribution feeder (R/X ~ 1) active power matters almost as much.")
