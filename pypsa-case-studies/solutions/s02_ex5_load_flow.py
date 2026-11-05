"""Exercise 5, Assignment 2 - Newton-Raphson load flow of the three-bus system.

Part A: the method written by hand (admittance matrix, mismatches, Jacobian, iterations,
        flows and losses).  Part B: the same network in PyPSA, solved with n.pf().
Data in p.u. on S_base = 100 MVA. Run:  python solutions/s02_ex5_load_flow.py
"""
import numpy as np
import pandas as pd
import pypsa

np.set_printoptions(precision=4, suppress=True)

# ------------------------------------------------------------------ data (p.u.)
y_line = -8j          # series admittance of each line   (X = 0.125 p.u.)
y0_line = 0.1j        # total shunt admittance of each line (y0/2 at each end)
lines = [(0, 1), (0, 2), (1, 2)]                     # lines 1-2, 1-3, 2-3 (0-based)
V = np.array([1.00, 1.05, 1.00])                     # |U1|, |U2| fixed; |U3| flat start
th = np.zeros(3)                                     # theta1 = 0 (reference); flat start
P_spec = np.array([0.0, +0.50, -2.50])               # P_G2 = 0.5 ; P_D3 = 2.5
Q_spec = np.array([0.0, 0.0, -1.00])                 # Q_D3 = 1.0
pvpq, pq = [1, 2], [2]                               # unknown angles, unknown magnitudes

# ------------------------------------------------------------ step 1: admittance matrix
Y = np.zeros((3, 3), dtype=complex)
for i, k in lines:
    Y[i, i] += y_line + y0_line / 2
    Y[k, k] += y_line + y0_line / 2
    Y[i, k] -= y_line
    Y[k, i] -= y_line
print("Step 1 - admittance matrix Y (p.u.):\n", Y)


def injections(V, th):
    """S_i = U_i * conj(sum_k Y_ik U_k)  ->  P_i + jQ_i."""
    U = V * np.exp(1j * th)
    return U * np.conj(Y @ U)


def jacobian(V, th):
    """Polar Jacobian [[dP/dtheta, dP/dV], [dQ/dtheta, dQ/dV]] for the unknowns."""
    U = V * np.exp(1j * th)
    I = Y @ U
    dS_dth = 1j * np.diag(U) @ np.conj(np.diag(I) - Y @ np.diag(U))
    dS_dV = np.diag(U) @ np.conj(Y @ np.diag(U / V)) + np.conj(np.diag(I)) @ np.diag(U / V)
    return np.block([[dS_dth.real[np.ix_(pvpq, pvpq)], dS_dV.real[np.ix_(pvpq, pq)]],
                     [dS_dth.imag[np.ix_(pq, pvpq)], dS_dV.imag[np.ix_(pq, pq)]]])

# ------------------------------------------------------------ step 2: Newton-Raphson
print("\nStep 2 - Newton-Raphson iterations")
print(f"{'it':>2} {'max|dF|':>10} {'theta2(deg)':>12} {'theta3(deg)':>12} {'|U3|':>9}")
for it in range(10):
    S = injections(V, th)
    dF = np.r_[P_spec[pvpq] - S.real[pvpq], Q_spec[pq] - S.imag[pq]]   # mismatches
    print(f"{it:>2} {abs(dF).max():10.2e} {np.degrees(th[1]):12.4f} {np.degrees(th[2]):12.4f} {V[2]:9.5f}")
    if abs(dF).max() < 1e-10:
        break
    J = jacobian(V, th)
    if it == 0:
        print("   Jacobian at the flat start:\n", J)
    dx = np.linalg.solve(J, dF)                      # J [dtheta2, dtheta3, d|U3|] = dF
    th[pvpq] += dx[:2]
    V[pq] += dx[2:]

S = injections(V, th)
print(f"\nResult: |U3| = {V[2]:.4f} p.u., theta2 = {np.degrees(th[1]):.3f} deg, theta3 = {np.degrees(th[2]):.3f} deg")
print(f"        P_G1 = {S[0].real:.4f}, Q_G1 = {S[0].imag:.4f}, Q_G2 = {S[1].imag:.4f} p.u.")

# ------------------------------------------------------------ step 3: flows and losses
U = V * np.exp(1j * th)
rows = []
for i, k in lines:
    I_ik = (y_line + y0_line / 2) * U[i] - y_line * U[k]     # current leaving bus i
    I_ki = (y_line + y0_line / 2) * U[k] - y_line * U[i]
    S_ik, S_ki = U[i] * np.conj(I_ik), U[k] * np.conj(I_ki)
    rows.append({"line": f"{i+1}-{k+1}", "S_ik": np.round(S_ik, 4), "S_ki": np.round(S_ki, 4),
                 "S_ik,v (loss)": np.round(S_ik + S_ki, 4)})
flows = pd.DataFrame(rows).set_index("line")
print("\nStep 3 - line flows and losses (p.u.)\n", flows)
print("Total losses S_v,ges =", np.round(sum(r["S_ik,v (loss)"] for r in rows), 4), "p.u.")

# ------------------------------------------------------------ Part B: PyPSA
S_base, V_nom = 100.0, 110.0              # MVA, kV (any V_nom gives the same p.u. result)
Z_base = V_nom**2 / S_base                # ohm
n = pypsa.Network()
for bus, v_set in [("1", 1.00), ("2", 1.05), ("3", 1.00)]:
    n.add("Bus", bus, v_nom=V_nom, v_mag_pu_set=v_set)
for a, b in [("1", "2"), ("1", "3"), ("2", "3")]:
    z = 1 / y_line                                        # j0.125 p.u.
    n.add("Line", f"L{a}-{b}", bus0=a, bus1=b, r=z.real * Z_base, x=z.imag * Z_base,
          b=y0_line.imag / Z_base, s_nom=500)             # ohm, ohm, siemens
n.add("Generator", "G1", bus="1", control="Slack", p_set=0.0)   # slack: numeric p_set
n.add("Generator", "G2", bus="2", control="PV", p_set=0.50 * S_base)
n.add("Load", "D3", bus="3", p_set=2.50 * S_base, q_set=1.00 * S_base)
n.pf()
print("\nPart B - PyPSA results")
print(pd.DataFrame({"|U| (p.u.)": n.buses_t.v_mag_pu.iloc[0],
                    "theta (deg)": np.degrees(n.buses_t.v_ang.iloc[0])}).round(5))
print((n.generators_t.p.iloc[0] / S_base).round(5).rename("P (p.u.)").to_frame()
      .join((n.generators_t.q.iloc[0] / S_base).round(5).rename("Q (p.u.)")))
print("max |U3 own - U3 PyPSA| =", abs(V[2] - n.buses_t.v_mag_pu.iloc[0]["3"]))
