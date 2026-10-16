"""Chapters 7 to 9 (week 2): symmetrical components and short-circuit calculations.

PyPSA does not compute short circuits, so this script uses numpy, with the same
Ybus / Zbus ideas as the power flow. All results are checked against Glover:
  * Example 7.4: Zbus and bolted three-phase faults at buses 1 and 2
  * Examples 8.x: Fortescue transformation (phase <-> sequence)
  * Examples 9.1 to 9.5: three-phase, single line-to-ground, line-to-line and
    double line-to-ground faults at bus 2, using the sequence networks

Run: python3 07_faults.py
"""
import cmath
import math

import numpy as np

a = cmath.exp(2j * math.pi / 3)
A = np.array([[1, 1, 1], [1, a**2, a], [1, a, a**2]])      # phase = A @ sequence
A_inv = np.linalg.inv(A)                                    # sequence = A_inv @ phase


def polar(z, unit=""):
    return f"{abs(z):.4f}{unit} /{math.degrees(cmath.phase(z)):+.2f} deg"


def to_phase(seq):
    """[I0, I1, I2] -> [Ia, Ib, Ic]"""
    return A @ np.asarray(seq)


# ----------------------------------------------------------------------------------------
# Example 7.4: Zbus and three-phase faults (system of Figure 7.3, 100 MVA base)
# ----------------------------------------------------------------------------------------
# Positive-sequence network: generator X'' = 0.15 at bus 1, motor X'' = 0.20 at bus 2,
# T1 + line + T2 = 0.10 + 0.105 + 0.10 = 0.305 between buses 1 and 2.
x_gen, x_mot, x_12 = 0.15, 0.20, 0.305
Ybus = -1j * np.array([[1 / x_gen + 1 / x_12, -1 / x_12],
                       [-1 / x_12, 1 / x_mot + 1 / x_12]])
Zbus = np.linalg.inv(Ybus)
VF = 1.05

print("=" * 72)
print("Example 7.4")
print("  Ybus = -j", np.round((Ybus / -1j).real, 4).tolist(), "  (book: 9.9454, 3.2787, 8.2787)")
print("  Zbus = j", np.round(Zbus.imag, 5).tolist(), "  (book: 0.11565, 0.04580, 0.13893)")
for k in range(2):
    IF = VF / Zbus[k, k]                                   # I_F = V_F / Z_kk
    E = [(1 - Zbus[i, k] / Zbus[k, k]) * VF for i in range(2)]   # bus voltages during fault
    I_line = (E[1 - k] - E[k]) / (1j * x_12)
    print(f"  fault at bus {k+1}: IF = {polar(IF, ' pu')}, voltages = "
          f"{[round(float(abs(e)), 4) for e in E]}, line contribution = {polar(I_line, ' pu')}")
print("  book: bus 1 -> IF = -j9.079, E2 = 0.6342, I21 = -j2.079 ;"
      " bus 2 -> IF = -j7.558, E1 = 0.7039, I12 = -j2.308")

# ----------------------------------------------------------------------------------------
# Example 8.x: sequence components of an unbalanced set
# ----------------------------------------------------------------------------------------
# Example 8.3 (book): Ia = 10/0, Ib = 0 (open phase), Ic = 10/120
Iabc = np.array([10, 0, cmath.rect(10, math.radians(120))])
seq = A_inv @ Iabc
print("\n" + "=" * 72)
print("Example 8.3: Ia = 10/0, Ib = 0, Ic = 10/120")
print("  I0, I1, I2 =", [polar(s, " A") for s in seq])
print("  book: I0 = 3.333 /60, I1 = 6.667 /0, I2 = 3.333 /-60")

# ----------------------------------------------------------------------------------------
# Examples 9.1 to 9.5: faults at bus 2 with sequence Thevenin impedances
# ----------------------------------------------------------------------------------------
par = lambda x, y: x * y / (x + y)
Z1 = 1j * par(0.20, 0.15 + 0.10 + 0.105 + 0.10)          # motor // (gen + T1 + line + T2)
Z2 = 1j * par(0.21, 0.17 + 0.10 + 0.105 + 0.10)
Z0 = 1j * (0.10 + 3 * 0.05)                              # motor X0 + 3 Xn ; delta of T2 opens left side
I_base = 100e6 / (math.sqrt(3) * 13.8e3) / 1e3          # kA at bus 2
ZF = 0.0                                                 # bolted faults

print("\n" + "=" * 72)
print(f"Example 9.1: Z0 = {Z0:.5f}, Z1 = {Z1:.5f}, Z2 = {Z2:.5f}  "
      "(book: j0.25, j0.13893, j0.14562)")


def report(name, I_seq, book):
    I_abc = to_phase(I_seq)
    print(f"  {name}")
    print("    I0, I1, I2 =", ", ".join(polar(i) for i in I_seq))
    print("    Ia, Ib, Ic =", ", ".join(f"{abs(i)*I_base:.2f} kA /{math.degrees(cmath.phase(i)):+.1f}"
                                         if abs(i) > 1e-9 else "0" for i in I_abc))
    print(f"    book: {book}")
    return I_abc


# 9.2 three-phase fault: only the positive-sequence network
report("9.2 three-phase fault", [0, VF / Z1, 0], "I1 = -j7.558 pu, |Ia| = |Ib| = |Ic| = 7.558 pu")

# 9.3 single line-to-ground (phase a): networks in SERIES, I0 = I1 = I2
I1 = VF / (Z0 + Z1 + Z2 + 3 * ZF)
report("9.3 single line-to-ground", [I1, I1, I1], "I0 = I1 = I2 = -j1.96427, Ia = 24.65 kA /-90")
V_seq = np.array([0, VF, 0]) - np.diag([Z0, Z1, Z2]) @ np.array([I1, I1, I1])
V_abc = to_phase(V_seq)
print("    Vag, Vbg, Vcg =", [polar(v, " pu") for v in V_abc],
      "\n    book: Vag = 0, Vbg = 1.179 /231.3, Vcg = 1.179 /128.7")

# 9.4 line-to-line (b-c): positive and negative networks in PARALLEL, I0 = 0, I2 = -I1
I1 = VF / (Z1 + Z2 + ZF)
report("9.4 line-to-line", [0, I1, -I1], "I1 = 3.690 /-90, Ib = 26.74 kA /180, Ic = 26.74 kA /0")

# 9.5 double line-to-ground: positive in series with (negative // (zero + 3ZF))
I1 = VF / (Z1 + par(Z2, Z0 + 3 * ZF))
I2 = -I1 * (Z0 + 3 * ZF) / (Z0 + 3 * ZF + Z2)
I0 = -I1 * Z2 / (Z0 + 3 * ZF + Z2)
I_abc = report("9.5 double line-to-ground", [I0, I1, I2],
               "I1 = -j4.5464, I2 = j2.8730, I0 = j1.6734, Ib = 28.86 kA /158.66, In = 21.00 kA")
print(f"    neutral current In = Ib + Ic = 3 I0 = {abs(3 * I0) * I_base:.2f} kA")
