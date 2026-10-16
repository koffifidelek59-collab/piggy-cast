"""Chapters 11 and 12: transient stability (swing equation) and frequency control.

  * Glover Examples 11.4 and 11.5: generator on an infinite bus, temporary bolted
    three-phase fault at the generator terminals (p_e = 0 during the fault).
    Critical clearing angle from the equal-area criterion, critical clearing time,
    then a numerical simulation of the swing equation to check stability.
  * Glover Example 12.3: turbine-governor droop.
  * Area frequency response characteristic beta = D + sum(1/R).

Run: python3 09_stability_and_frequency.py
"""
import math

from scipy.integrate import solve_ivp
from scipy.optimize import brentq

# ----------------------------------------------------------------------------------------
# Swing equation:  (2H / w_syn) d2(delta)/dt2 = p_m - p_e     (per unit, D = 0)
# ----------------------------------------------------------------------------------------
H, f = 3.0, 60.0
w_syn = 2 * math.pi * f
p_m, P_max = 1.0, 2.4638          # pre- and post-fault p_e = P_max sin(delta)
d0 = math.asin(p_m / P_max)       # initial angle, 0.4179 rad
d3 = math.pi - d0                 # maximum angle allowed after clearing


def area_balance(d_cr):
    """A1 (accelerating) - A2 (decelerating)."""
    a1 = p_m * (d_cr - d0)
    a2 = P_max * (math.cos(d_cr) - math.cos(d3)) - p_m * (d3 - d_cr)
    return a1 - a2


d_cr = brentq(area_balance, d0 + 1e-6, d3 - 1e-6)
t_cr = math.sqrt(4 * H / (w_syn * p_m) * (d_cr - d0))   # p_e = 0 during the fault

print("=" * 72)
print("Examples 11.4 and 11.5: equal-area criterion")
print(f"  delta0 = {d0:.4f} rad, delta_cr = {d_cr:.4f} rad = {math.degrees(d_cr):.2f} deg, "
      f"t_cr = {t_cr:.4f} s = {t_cr*f:.2f} cycles")
print("  book: delta0 = 0.4179 rad, delta_cr = 1.5489 rad = 88.74 deg, t_cr = 0.1897 s = 11.38 cycles")


def simulate(t_clear, t_end=2.0):
    """Integrate the swing equation; return the maximum rotor angle reached (deg)."""
    def rhs(t, x):
        delta, dw = x
        p_e = 0.0 if t < t_clear else P_max * math.sin(delta)
        return [dw, w_syn / (2 * H) * (p_m - p_e)]
    sol = solve_ivp(rhs, (0, t_end), [d0, 0.0], max_step=1e-3, rtol=1e-8)
    return math.degrees(max(sol.y[0]))


for tc in (0.15, 0.18, 0.20):
    dmax = simulate(tc)
    verdict = "stable (angle swings back)" if dmax < 180 else "UNSTABLE (loses synchronism)"
    print(f"  clearing at {tc:.2f} s -> max angle {min(dmax, 999):6.1f} deg : {verdict}")

# ----------------------------------------------------------------------------------------
# Frequency control
# ----------------------------------------------------------------------------------------
R, S_unit, df = 0.05, 500.0, 0.01                      # Example 12.3
dp = -(1 / R) * (df / f) * S_unit
print("\n" + "=" * 72)
print("Example 12.3: droop  dp_m = dp_ref - (1/R) df")
print(f"  frequency +0.01 Hz, R = 0.05 pu on 500 MVA -> dp_m = {dp:.3f} MW (book: -1.67 MW)")

# Area of two units after a load increase (illustrative data)
units = {"unit A (1000 MVA, R = 5 %)": (0.05, 1000), "unit B (500 MVA, R = 4 %)": (0.04, 500)}
S_base, D, dP_load = 1000.0, 0.0, 60.0               # MVA, load damping, MW
beta = D + sum((s / S_base) / r for r, s in units.values())    # 1/R converted to 1000 MVA
df_pu = -(dP_load / S_base) / beta
print("\nArea frequency response: two units, load increase of 60 MW, no AGC")
print(f"  beta = sum(1/R) on 1000 MVA = {beta:.1f} pu, steady-state df = {df_pu*f*1000:.1f} mHz")
for name, (r, s) in units.items():
    print(f"  {name}: picks up {-(s / S_base) / r * df_pu * S_base:.1f} MW")
print("  Units share the load in proportion to (rating / R). The secondary control (AGC)")
print("  then drives the area control error ACE = (p_tie - p_tie,sched) + B_f (f - 60) to zero.")
