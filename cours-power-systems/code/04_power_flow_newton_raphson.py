"""Chapter 6 (Lesson 5): power flow solved from scratch.

Five-bus system of Glover Example 6.9 (Sbase = 100 MVA). Builds Ybus, then solves
the power flow with three methods taught in Lesson 5:
  * Newton-Raphson with the Jacobian formulas of the slides (J11, J12, J21, J22)
  * Fast decoupled (constant B' and B'' matrices)
  * Gauss-Seidel (to show its slow convergence)
and compares the result with Table 6.6 of the book.

Run: python3 04_power_flow_newton_raphson.py
"""
import math

import numpy as np

np.set_printoptions(precision=4, suppress=True, linewidth=110)

# ---------------------------------------------------------------- data (Tables 6.1-6.3)
n_bus = 5
# branches: (from, to, R, X, B_total) in per unit, buses numbered 1..5
branches = [
    (2, 4, 0.0090, 0.100, 1.72),     # lines
    (2, 5, 0.0045, 0.050, 0.88),
    (4, 5, 0.00225, 0.025, 0.44),
    (1, 5, 0.00150, 0.020, 0.0),     # transformers (nominal tap)
    (3, 4, 0.00075, 0.010, 0.0),
]
# bus types: 0 = slack, 1 = PV, 2 = PQ
bus_type = np.array([0, 2, 1, 2, 2])
P_spec = np.array([0.0, -8.0, 5.2 - 0.8, 0.0, 0.0])      # P = PG - PL
Q_spec = np.array([0.0, -2.8, 0.0, 0.0, 0.0])             # Q = QG - QL (PQ buses only)
V_set = np.array([1.0, 1.0, 1.05, 1.0, 1.0])              # flat start, |V| fixed at slack/PV


def build_ybus():
    Y = np.zeros((n_bus, n_bus), dtype=complex)
    for f, t, r, x, b in branches:
        i, k = f - 1, t - 1
        y = 1 / complex(r, x)
        Y[i, i] += y + 1j * b / 2
        Y[k, k] += y + 1j * b / 2
        Y[i, k] -= y
        Y[k, i] -= y
    return Y


Y = build_ybus()
G, B = Y.real, Y.imag
pv_pq = np.where(bus_type != 0)[0]          # unknown angles
pq = np.where(bus_type == 2)[0]             # unknown magnitudes


def injections(V, d):
    """P_i = sum_k |Vi||Vk| [Gik cos(dik) + Bik sin(dik)], Q_i likewise (slides)."""
    dd = d[:, None] - d[None, :]
    P = V * ((G * np.cos(dd) + B * np.sin(dd)) @ V)
    Q = V * ((G * np.sin(dd) - B * np.cos(dd)) @ V)
    return P, Q


def jacobian(V, d):
    """Exact Jacobian with the four blocks given in Lesson 5."""
    P, Q = injections(V, d)
    n = n_bus
    dP_dd = np.zeros((n, n)); dP_dV = np.zeros((n, n))
    dQ_dd = np.zeros((n, n)); dQ_dV = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dij = d[i] - d[j]
            if i != j:
                dP_dd[i, j] = V[i] * V[j] * (G[i, j] * math.sin(dij) - B[i, j] * math.cos(dij))
                dP_dV[i, j] = V[i] * (G[i, j] * math.cos(dij) + B[i, j] * math.sin(dij))
                dQ_dd[i, j] = -V[i] * V[j] * (G[i, j] * math.cos(dij) + B[i, j] * math.sin(dij))
                dQ_dV[i, j] = V[i] * (G[i, j] * math.sin(dij) - B[i, j] * math.cos(dij))
        dP_dd[i, i] = -Q[i] - B[i, i] * V[i] ** 2
        dP_dV[i, i] = P[i] / V[i] + G[i, i] * V[i]
        dQ_dd[i, i] = P[i] - G[i, i] * V[i] ** 2
        dQ_dV[i, i] = Q[i] / V[i] - B[i, i] * V[i]
    J11 = dP_dd[np.ix_(pv_pq, pv_pq)]
    J12 = dP_dV[np.ix_(pv_pq, pq)]
    J21 = dQ_dd[np.ix_(pq, pv_pq)]
    J22 = dQ_dV[np.ix_(pq, pq)]
    return np.block([[J11, J12], [J21, J22]])


def mismatch(V, d):
    P, Q = injections(V, d)
    return np.concatenate([P_spec[pv_pq] - P[pv_pq], Q_spec[pq] - Q[pq]])


def newton_raphson(tol=1e-8, max_iter=20, verbose=True):
    V, d = V_set.copy(), np.zeros(n_bus)
    for it in range(max_iter):
        f = mismatch(V, d)
        if verbose:
            print(f"  iter {it}: max |mismatch| = {np.max(np.abs(f)):.2e} pu")
        if np.max(np.abs(f)) < tol:
            return V, d, it
        dx = np.linalg.solve(jacobian(V, d), f)
        d[pv_pq] += dx[: len(pv_pq)]
        V[pq] += dx[len(pv_pq):]
    raise RuntimeError("Newton-Raphson did not converge")


def fast_decoupled(tol=1e-8, max_iter=100):
    """-B' dd = dP/|V| and -B'' d|V| = dQ/|V| with constant matrices (Lesson 5)."""
    Bp = -B[np.ix_(pv_pq, pv_pq)]          # B'  (here simply -Bbus, as on the slide)
    Bpp = -B[np.ix_(pq, pq)]               # B''
    V, d = V_set.copy(), np.zeros(n_bus)
    for it in range(max_iter):
        P, Q = injections(V, d)
        dP = (P_spec - P)[pv_pq]
        dQ = (Q_spec - Q)[pq]
        if max(np.max(np.abs(dP)), np.max(np.abs(dQ))) < tol:
            return V, d, it
        d[pv_pq] += np.linalg.solve(Bp, dP / V[pv_pq])
        P, Q = injections(V, d)
        V[pq] += np.linalg.solve(Bpp, (Q_spec - Q)[pq] / V[pq])
    raise RuntimeError("fast decoupled did not converge")


def gauss_seidel(tol=1e-6, max_iter=500):
    Vc = V_set.astype(complex)
    for it in range(max_iter):
        V_old = Vc.copy()
        for i in range(1, n_bus):
            if bus_type[i] == 1:                       # PV: compute Q from current state
                Q_i = -np.imag(np.conj(Vc[i]) * (Y[i] @ Vc))
                S_i = P_spec[i] + 1j * Q_i
            else:
                S_i = P_spec[i] + 1j * Q_spec[i]
            Vi = (np.conj(S_i / Vc[i]) - (Y[i] @ Vc - Y[i, i] * Vc[i])) / Y[i, i]
            Vc[i] = V_set[i] * Vi / abs(Vi) if bus_type[i] == 1 else Vi
        if np.max(np.abs(Vc - V_old)) < tol:
            return Vc, it + 1
    return Vc, max_iter


if __name__ == "__main__":
    print("=" * 72)
    print("Glover Example 6.9: Ybus (per unit)")
    print(Y)
    print(f"  Y24 = {Y[1,3]:.5f}  (book: -0.89276 + j9.91964)")

    # first iteration checks of Example 6.11
    V0, d0 = V_set.copy(), np.zeros(n_bus)
    P0, _ = injections(V0, d0)
    print(f"\nExample 6.11: dP2(0) = {P_spec[1] - P0[1]:.5f}  (book: -7.99972; exact value is -8 at flat start,\n"
          "  the book's 2.9e-4 comes from rounded angles)")
    J0 = jacobian(V0, d0)
    print(f"  Jacobian size {J0.shape} (book: 7 x 7 once the PV bus equation is removed)")
    print(f"  J1_24(0) = {J0[0, 2]:.5f}  (book: -9.91964)")

    print("\nNewton-Raphson")
    V, d, it = newton_raphson()
    P, Q = injections(V, d)
    print(f"  converged in {it} iterations (quadratic convergence)")
    print("\n  bus   |V| pu   angle deg     P pu      Q pu")
    for i in range(n_bus):
        print(f"  {i+1:3d}  {V[i]:7.4f}  {math.degrees(d[i]):9.3f}  {P[i]:8.3f}  {Q[i]:8.3f}")
    print("  Book Table 6.6: |V| = 1.000 0.834 1.050 1.019 0.974;"
          " angles 0 -22.407 -0.597 -2.834 -4.548;\n"
          "                  PG1 = 3.948, QG1 = 1.144, QG3 = 3.376")
    print(f"  here: PG1 = {P[0]:.3f}, QG1 = {Q[0]:.3f}, QG3 = QL3 + Q3 = {0.4 + Q[2]:.3f}")
    losses = P.sum()
    print(f"  system losses = {losses*100:.1f} MW")

    Vf, df, itf = fast_decoupled()
    print(f"\nFast decoupled: {itf} iterations, max |V| difference with NR "
          f"= {np.max(np.abs(Vf - V)):.1e} pu (same exact solution, more iterations)")
    Vgs, itgs = gauss_seidel()
    print(f"Gauss-Seidel: {itgs} iterations to 1e-6, max |V| difference with NR "
          f"= {np.max(np.abs(np.abs(Vgs) - V)):.1e} pu (slow convergence)")
