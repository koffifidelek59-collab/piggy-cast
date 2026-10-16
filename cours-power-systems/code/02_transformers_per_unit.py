"""Chapter 3 (Lesson 2): transformers and the per-unit system.

Solves Exercise 1, question 3 (13.8 kV delta / 480Y V transformer) and
Exercise 2 = Glover Example 3.4 (three-zone single-phase network).

Run: python3 02_transformers_per_unit.py
"""
import cmath
import math


def polar(z, unit=""):
    return f"{abs(z):.4f}{unit} /{math.degrees(cmath.phase(z)):+.2f} deg"


def change_base(z_pu_old, s_old, s_new, v_old, v_new):
    """Z_new = Z_old * (S_new / S_old) * (V_old / V_new)^2"""
    return z_pu_old * (s_new / s_old) * (v_old / v_new) ** 2


# ----------------------------------------------------------------------------------------
# Exercise 1, question 3
# ----------------------------------------------------------------------------------------
S_base = 500e3                      # VA, transformer rating
V_hv, V_lv = 13.8e3, 480.0          # line-to-line base voltages (same ratio as ratings)
I_base_hv = S_base / (math.sqrt(3) * V_hv)
I_base_lv = S_base / (math.sqrt(3) * V_lv)
Z_T = 0.0056 + 0.0355j              # per unit on the transformer rating

P_src, pf = 300e3, 0.87             # measured at the 13.8 kV source side, lagging
S_src = P_src / pf * cmath.exp(1j * math.acos(pf))          # complex power, VA
V1 = 1.0 + 0j                                                # rated voltage on HV side
S1 = S_src / S_base                                          # per unit
I1 = (S1 / V1).conjugate()                                   # I = (S / V)*
V2 = V1 - Z_T * I1                                           # per-phase, phase shift ignored
S2 = V2 * I1.conjugate()                                     # power delivered to the load

print("=" * 72)
print("Exercise 1, question 3  (base 500 kVA, 13.8 kV / 480 V)")
print(f"  base currents: HV {I_base_hv:.2f} A, LV {I_base_lv:.1f} A")
print(f"  (1) source apparent power  S1 = {polar(S1, ' pu')}  = {abs(S_src)/1e3:.1f} kVA")
print(f"  (2) source current         I1 = {polar(I1, ' pu')} = {abs(I1)*I_base_hv:.2f} A")
print(f"  (3) load current           I2 = I1 = {abs(I1):.4f} pu = {abs(I1)*I_base_lv:.1f} A")
print(f"  (4) load voltage           V2 = {polar(V2, ' pu')} = {abs(V2)*V_lv:.1f} V line-line")
print(f"  (5) load real power        P2 = {S2.real:.4f} pu = {S2.real*S_base/1e3:.1f} kW")
print(f"  (6) load reactive power    Q2 = {S2.imag:.4f} pu = {S2.imag*S_base/1e3:.1f} kvar")
print(f"  (7) load apparent power   |S2| = {abs(S2):.4f} pu = {abs(S2)*S_base/1e3:.1f} kVA")
print(f"  (8) load power factor     pf2 = {S2.real/abs(S2):.4f} lagging")
print(f"  losses in the transformer  = {(S1 - S2).real*S_base/1e3:.2f} kW, "
      f"{(S1 - S2).imag*S_base/1e3:.2f} kvar  (= |I|^2 Z_T)")
print("  Note: a delta-wye bank also shifts the LV voltage by 30 deg (ANSI: HV leads LV).")
print(f"        Including it, V2 = {polar(V2 * cmath.exp(-1j * math.pi / 6), ' pu')}")

# ----------------------------------------------------------------------------------------
# Exercise 2 = Glover Example 3.4
# ----------------------------------------------------------------------------------------
# Zone 1: source 220 V; T1: 30 kVA 240/480 V, X = 0.10 pu; zone 2: line X = 2 ohm;
# T2: 20 kVA 460/115 V, X = 0.10 pu; zone 3: load Z = 0.9 + j0.2 ohm.
S_b = 30e3
V_b1 = 240.0
V_b2 = V_b1 * 480 / 240            # bases follow the transformer ratios across each zone
V_b3 = V_b2 * 115 / 460
Z_b2, Z_b3 = V_b2**2 / S_b, V_b3**2 / S_b
I_b3 = S_b / V_b3

X_T1 = 0.10                                         # already on 30 kVA / 240 V
X_T2 = change_base(0.10, 20e3, S_b, 460, V_b2)      # nameplate 20 kVA / 460 V -> system base
X_line = 2.0 / Z_b2
Z_load = (0.9 + 0.2j) / Z_b3
V_s = 220 / V_b1

I_load = V_s / (1j * (X_T1 + X_line + X_T2) + Z_load)

print("\n" + "=" * 72)
print("Exercise 2 = Glover Example 3.4")
print(f"  base voltages: {V_b1:.0f} V, {V_b2:.0f} V, {V_b3:.0f} V; "
      f"Zbase2 = {Z_b2:.2f} ohm, Zbase3 = {Z_b3:.2f} ohm, Ibase3 = {I_b3:.0f} A")
print(f"  X_T1 = {X_T1:.4f}, X_T2 = {X_T2:.4f}, X_line = {X_line:.4f}, "
      f"Z_load = {Z_load.real:.4f} + j{Z_load.imag:.4f}  (pu)")
print(f"  V_source = {V_s:.4f} pu")
print(f"  I_load = {polar(I_load, ' pu')} = {abs(I_load)*I_b3:.1f} A")
print("  Book: X_T2 = 0.1378, X_line = 0.2604, Z_load = 1.875 + j0.4167, "
      "I_load = 0.4395 pu /-26.01 deg = 109.9 A (book rounds intermediate values)")
