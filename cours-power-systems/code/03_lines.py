"""Chapters 4 and 5 (Lessons 3 and 4): line parameters and line models.

Reproduces, and checks against the reference values:
  * Lesson 4 short-line example (10 mi distribution line, #1/0 ACSR)
  * Lesson 4 medium-line example (230 kV, 77.6 mi, 1272 kcmil ACSR)
  * Glover Examples 5.2 and 5.3 (765 kV, 300 km long line: exact ABCD, equivalent pi)
  * Lesson 4 surge impedance loading (SIL) and line loadability curve

Run: python3 03_lines.py
"""
import cmath
import math

import numpy as np

MU0_OVER_2PI = 2e-7          # H/m
EPS0 = 8.854e-12             # F/m
MILE = 1609.34               # m
FT = 0.3048                  # m


def polar(z, unit=""):
    return f"{abs(z):.4f}{unit} /{math.degrees(cmath.phase(z)):+.2f} deg"


def inductance_per_m(d_eq, d_s):
    """L = 2e-7 ln(Deq / Ds) [H/m]; Deq and Ds in the same unit."""
    return MU0_OVER_2PI * math.log(d_eq / d_s)


def capacitance_per_m(d_eq, r):
    """C = 2 pi eps0 / ln(Deq / r) [F/m] (line to neutral)."""
    return 2 * math.pi * EPS0 / math.log(d_eq / r)


def r_at_temperature(r1, t1, t2, T=228.1):
    """Aluminium: R(T2) = R(T1) (T2 + T) / (T1 + T)."""
    return r1 * (t2 + T) / (t1 + T)


def abcd_nominal_pi(Z, Y):
    A = 1 + Z * Y / 2
    return A, Z, Y * (1 + Z * Y / 4), A


def abcd_long_line(z, y, length):
    zc = cmath.sqrt(z / y)
    gl = cmath.sqrt(z * y) * length
    A = cmath.cosh(gl)
    return A, zc * cmath.sinh(gl), cmath.sinh(gl) / zc, A, zc, gl


# ----------------------------------------------------------------------------------------
# Short line (Lesson 4)
# ----------------------------------------------------------------------------------------
f = 60.0
w = 2 * math.pi * f
d_eq = (3.96 * 3.96 * 7.33) ** (1 / 3)                       # ft, geometric mean spacing
X = w * inductance_per_m(d_eq, 0.00446) * MILE               # ohm/mi
R = r_at_temperature(1.12, 50, 75)                           # ohm/mi at 75 C
Z = (R + 1j * X) * 10                                        # 10 miles
VR = 23e3 / math.sqrt(3)                                     # line-to-neutral
IR = cmath.rect(230, -math.acos(0.8))
VS = VR + Z * IR

print("=" * 72)
print("Short line (Lesson 4): 10 mi, #1/0 ACSR, 230 A, 23 kV, pf 0.8 lagging")
print(f"  Deq = {d_eq:.2f} ft, X = {X:.3f} ohm/mi, R(75 C) = {R:.2f} ohm/mi, Z = {Z:.2f} ohm")
print(f"  VS = {polar(VS / 1e3, ' kV')} (line-to-neutral) = {abs(VS)*math.sqrt(3)/1e3:.1f} kV LL "
      f"= {abs(VS)/VR:.2f} pu")
print(f"  losses = {3*abs(IR)**2*Z.real/1e6:.2f} MW for a load of {3*(VR*IR.conjugate()).real/1e6:.2f} MW")
print("  Slides: Deq = 4.86 ft, X = 0.849 ohm/mi, VS = 16.7 kV (28.9 kV LL, 1.26 pu), "
      "losses 1.94 MW / 7.33 MW")

# ----------------------------------------------------------------------------------------
# Medium line (Lesson 4)
# ----------------------------------------------------------------------------------------
d_eq = (18 * 18 * 36) ** (1 / 3)                              # ft
r_cond = 1.345 / 2 / 12                                       # ft (diameter 1.345 in)
x = w * inductance_per_m(d_eq, 0.0444) * MILE                 # ohm/mi
c = capacitance_per_m(d_eq * FT, r_cond * FT)                 # F/m
y = 1j * w * c * MILE                                         # S/mi
length = 77.6
Z, Y = (0.0832 + 1j * x) * length, y * length
A, B, C, D = abcd_nominal_pi(Z, Y)
VR = 230e3 / math.sqrt(3)
SR = 150e6 / 0.95
IR = cmath.rect(SR / (3 * VR), -math.acos(0.95))
VS = A * VR + B * IR
IS = C * VR + D * IR
SS = 3 * VS * IS.conjugate()

print("\n" + "=" * 72)
print("Medium line (Lesson 4): 230 kV, 77.6 mi, nominal pi, 150 MW at pf 0.95 lagging")
print(f"  x = {x:.3f} ohm/mi, C = {c*1e12:.2f} pF/m, y = j{y.imag*1e6:.2f} uS/mi")
print(f"  Z = {Z:.2f} ohm, Y = j{Y.imag*1e6:.0f} uS, A = {A:.4f}, C = {C*1e6:.3f} uS")
print(f"  VS = {polar(VS / 1e3, ' kV')} (LN), IS = {polar(IS, ' A')}")
print(f"  PS = {SS.real/1e6:.1f} MW, |SS| = {abs(SS)/1e6:.1f} MVA, pf_S = {SS.real/abs(SS):.3f}")
print("  Slides: x = 0.757, C = 9.27 pF/m, VS = 142.4 kV /8.68, IS = 377 A /-9.78, PS = 152.9 MW")

# ----------------------------------------------------------------------------------------
# Long line: Glover Examples 5.2 and 5.3
# ----------------------------------------------------------------------------------------
z = 0.0165 + 0.3306j           # ohm/km
y = 4.674e-6j                  # S/km
A, B, C, D, zc, gl = abcd_long_line(z, y, 300)
Zp = B                                         # equivalent pi: Z' = B
Yp_half = (A - 1) / B                          # Y'/2 = (A - 1) / B
print("\n" + "=" * 72)
print("Long line: Glover Examples 5.2 and 5.3 (765 kV, 300 km)")
print(f"  Zc = {polar(zc, ' ohm')}, gamma*l = {gl:.5f}")
print(f"  A = D = {polar(A)}, B = {polar(B, ' ohm')}, C = {polar(C*1e3, ' mS')}")
print(f"  nominal-pi B = Z = {polar(z*300, ' ohm')} ({abs(z*300)/abs(B)*100-100:.1f} % larger)")
print(f"  equivalent pi: Z' = {polar(Zp, ' ohm')}, Y'/2 = {polar(Yp_half*1e3, ' mS')}")
print("  Book: Zc = 266.1 /-1.43, A = 0.9313 /0.209, B = 97.0 /87.2, C = 1.37e-3 /90.06 S")

# ----------------------------------------------------------------------------------------
# Surge impedance loading and loadability (Lesson 4)
# ----------------------------------------------------------------------------------------
L, Cc = 2.093e-3, 14.27e-9     # per mile
zc = math.sqrt(L / Cc)
beta = w * math.sqrt(L * Cc)   # rad/mi
sil = (138e3) ** 2 / zc
print("\n" + "=" * 72)
print("Surge impedance loading (Lesson 4): 138 kV line")
print(f"  Zc = {zc:.0f} ohm, beta = {beta*1e3:.3f}e-3 rad/mi, SIL = {sil/1e6:.1f} MW")
print("  Slides: Zc = 383 ohm, beta = 2.06e-3 rad/mi, SIL = 49.7 MW")
print("  Loadability, P/SIL = sin(35 deg)/sin(beta*l), capped at 3 (thermal):")
for mi in (50, 100, 200, 300, 400, 600):
    p = min(math.sin(math.radians(35)) / math.sin(beta * mi), 3.0)
    print(f"    {mi:4d} mi -> {p:.2f} x SIL")
_ = np  # numpy kept for interactive use
