"""Chapter 2 (Lesson 1): phasors, three-phase power, bus admittance matrix.

Solves Exercise 1, questions 1 and 2, and the Ybus example of Lesson 1 (slide 37).
Question 1 is solved twice: by hand with numpy, and with the Ybus that PyPSA builds.

Run: python3 01_three_phase_and_ybus.py
"""
import cmath
import math
import warnings

import numpy as np
import pypsa

warnings.filterwarnings("ignore")


def polar(z, unit=""):
    """Format a complex number as magnitude/angle in degrees."""
    return f"{abs(z):.4f}{unit} /{math.degrees(cmath.phase(z)):+.2f} deg"


# ----------------------------------------------------------------------------------------
# Exercise 1, question 1: build Ybus and solve I = Y V
# ----------------------------------------------------------------------------------------
# Branch ADMITTANCES given on the diagram (per unit). Node 0 is the neutral (reference).
y10 = -0.05j     # inductor between node 1 and the neutral
y20 = -0.10j     # inductor between node 2 and the neutral
y12 = -2.00j
y13 = -4.00j
y23 = -5.00j
I = np.array([0.010 + 0.052j, 0.10j, 0.0])   # current sources injected at nodes 1, 2, 3

# Rule: Y_ii = sum of admittances connected to bus i ; Y_ij = - admittance between i and j
Y = np.array([
    [y10 + y12 + y13, -y12, -y13],
    [-y12, y20 + y12 + y23, -y23],
    [-y13, -y23, y13 + y23],
])
V = np.linalg.solve(Y, I)          # never invert Y explicitly on large systems: solve instead

print("=" * 72)
print("Exercise 1, question 1: bus admittance matrix (per unit)")
print(np.array2string(Y, precision=3, suppress_small=True))
for k, v in enumerate(V, start=1):
    print(f"  V{k} = {v.real:+.4f} {v.imag:+.4f}j  =  {polar(v)}")
print("  check  Y @ V - I =", np.round(Y @ V - I, 12))

# ---- Same network in PyPSA ---------------------------------------------------------------
# PyPSA works with impedances in ohm and a 1 MVA power base: with v_nom = 1 kV, the base
# impedance is 1 ohm, so ohm values equal per-unit values.
n = pypsa.Network()
for b in ("1", "2", "3"):
    n.add("Bus", b, v_nom=1.0)
for name, (b0, b1, y) in {"L12": ("1", "2", y12), "L13": ("1", "3", y13),
                          "L23": ("2", "3", y23)}.items():
    z = 1 / y                      # admittance -j2 -> impedance +j0.5 (an inductor)
    n.add("Line", name, bus0=b0, bus1=b1, r=z.real, x=z.imag)
# shunt elements to the neutral: g + jb in siemens (b < 0 = inductive)
n.add("ShuntImpedance", "Sh1", bus="1", g=y10.real, b=y10.imag)
n.add("ShuntImpedance", "Sh2", bus="2", g=y20.real, b=y20.imag)

n.determine_network_topology()
sub = n.sub_networks.obj.iloc[0]
sub.calculate_Y()
Y_pypsa = sub.Y.toarray()
order = [int(b) - 1 for b in sub.buses_o]           # PyPSA's internal bus order
Y_pypsa_sorted = np.empty_like(Y_pypsa)
Y_pypsa_sorted[np.ix_(order, order)] = Y_pypsa
print("\nYbus built by PyPSA equals the hand-built Ybus:",
      np.allclose(Y_pypsa_sorted, Y))
print("Solution with PyPSA's Ybus:", np.round(np.linalg.solve(Y_pypsa_sorted, I), 4))

# ----------------------------------------------------------------------------------------
# Lesson 1, slide 37: three-bus example given with branch IMPEDANCES
# ----------------------------------------------------------------------------------------
Ys = np.array([
    [1 / 1.0j + 1 / 0.4j + 1 / 0.2j, -1 / 0.4j, -1 / 0.2j],
    [-1 / 0.4j, 1 / 0.8j + 1 / 0.4j + 1 / 0.2j, -1 / 0.2j],
    [-1 / 0.2j, -1 / 0.2j, 1 / 0.08j + 1 / 0.2j + 1 / 0.2j],
])
print("\nLesson 1, slide 37: Ybus =\n", np.array2string(Ys, precision=3))

# ----------------------------------------------------------------------------------------
# Exercise 1, question 2: line and phase quantities, power factor
# ----------------------------------------------------------------------------------------
V_ll, I_line, pf = 480.0, 112.0, 0.85
V_an = V_ll / math.sqrt(3)                       # |Van| = |Vab| / sqrt(3)
phi = math.acos(pf)                              # lagging: current lags voltage
Van = cmath.rect(V_an, 0)
Vab = math.sqrt(3) * cmath.rect(1, math.radians(30)) * Van   # Vab leads Van by 30 deg (abc)
Ia = cmath.rect(I_line, -phi)
S3 = 3 * Van * Ia.conjugate()

print("\n" + "=" * 72)
print("Exercise 1, question 2")
print(f"  |Van| = 480/sqrt(3) = {V_an:.1f} V")
print(f"  Van = {polar(Van, ' V')}")
print(f"  Vab = {polar(Vab, ' V')}   (leads Van by 30 deg)")
print(f"  Ia  = {polar(Ia, ' A')}   (lags Van by acos(0.85) = {math.degrees(phi):.2f} deg)")
print(f"  S3phase = {S3.real/1e3:.1f} kW + j{S3.imag/1e3:.1f} kvar, |S| = {abs(S3)/1e3:.1f} kVA")
