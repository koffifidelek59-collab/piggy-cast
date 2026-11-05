"""Newton's method and a Newton-Raphson AC load flow written from scratch.

The goal is transparency: every quantity that PyPSA computes internally
(admittance matrix, mismatches, Jacobian, iterations) is visible here, so the
PyPSA result can be checked against an independent implementation.

Power-flow equations (polar form), for every bus i:

    P_i = |V_i| sum_k |V_k| (G_ik cos t_ik + B_ik sin t_ik)
    Q_i = |V_i| sum_k |V_k| (G_ik sin t_ik - B_ik cos t_ik),   t_ik = theta_i - theta_k

Unknowns: theta at PV and PQ buses, |V| at PQ buses.
Newton step: J [d_theta; d_V] = [P_spec - P_calc; Q_spec - Q_calc].
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ------------------------------------------------------------------ scalar Newton
def newton_scalar(f, df, x0: float, n_iter: int = 5) -> pd.DataFrame:
    """Run `n_iter` Newton iterations x_{k+1} = x_k - f(x_k)/f'(x_k).

    Returns one row per iteration with x_k, f(x_k), f'(x_k), dx and x_{k+1}.
    """
    rows, x = [], float(x0)
    for k in range(n_iter):
        fx, dfx = f(x), df(x)
        dx = -fx / dfx
        rows.append({"k": k, "x_k": x, "f(x_k)": fx, "f'(x_k)": dfx,
                     "dx": dx, "x_k+1": x + dx})
        x += dx
    return pd.DataFrame(rows).set_index("k")


# --------------------------------------------------------------- admittance matrix
def make_ybus(n_bus: int, branches: list[dict], bus_shunt: np.ndarray | None = None) -> np.ndarray:
    """Admittance matrix from a branch list (pi model, optional off-nominal tap).

    Each branch dict holds: f, t (0-based bus indices), y (series admittance),
    ysh (TOTAL shunt admittance of the pi model, split half at each end),
    tap (ratio at the 'from' side, 1 if none), shift (rad, 0 if none).
    """
    Y = np.zeros((n_bus, n_bus), dtype=complex)
    for b in branches:
        i, k = b["f"], b["t"]
        y, ysh = b["y"], b.get("ysh", 0.0)
        a = b.get("tap", 1.0) * np.exp(1j * b.get("shift", 0.0))
        Y[i, i] += (y + ysh / 2) / abs(a) ** 2
        Y[k, k] += y + ysh / 2
        Y[i, k] += -y / np.conj(a)
        Y[k, i] += -y / a
    if bus_shunt is not None:
        Y[np.diag_indices(n_bus)] += bus_shunt
    return Y


def injections(Y: np.ndarray, V: np.ndarray, th: np.ndarray):
    """Complex power injections S = V (Y V)* for every bus, returned as (P, Q)."""
    U = V * np.exp(1j * th)
    S = U * np.conj(Y @ U)
    return S.real, S.imag


def jacobian(Y, V, th, pvpq, pq):
    """Full polar Jacobian [[dP/dth, dP/dV],[dQ/dth, dQ/dV]] (rows/cols reduced)."""
    U = V * np.exp(1j * th)
    I = Y @ U
    diagU, diagI = np.diag(U), np.diag(I)
    diagUn = np.diag(U / np.abs(U))
    dS_dth = 1j * diagU @ np.conj(diagI - Y @ diagU)
    dS_dV = diagU @ np.conj(Y @ diagUn) + np.conj(diagI) @ diagUn
    J11 = dS_dth.real[np.ix_(pvpq, pvpq)]
    J12 = dS_dV.real[np.ix_(pvpq, pq)]
    J21 = dS_dth.imag[np.ix_(pq, pvpq)]
    J22 = dS_dV.imag[np.ix_(pq, pq)]
    return np.block([[J11, J12], [J21, J22]])


def nr_load_flow(Y, bus_type, P_spec, Q_spec, V0, th0, tol=1e-10, max_iter=20):
    """Newton-Raphson load flow.

    bus_type: array with 'slack', 'PV' or 'PQ' for each bus.
    P_spec, Q_spec: specified net injections (generation - load) in p.u.
    Returns dict with V, th, the iteration log and the first Jacobian.
    """
    bus_type = np.asarray(bus_type)
    pvpq = np.where(bus_type != "slack")[0]
    pq = np.where(bus_type == "PQ")[0]
    V, th = np.array(V0, float), np.array(th0, float)
    log, J0 = [], None
    for it in range(max_iter + 1):
        P, Q = injections(Y, V, th)
        mis = np.r_[P_spec[pvpq] - P[pvpq], Q_spec[pq] - Q[pq]]
        log.append({"iteration": it, "max |mismatch| (p.u.)": np.abs(mis).max(),
                    **{f"theta_{i+1} (deg)": np.degrees(th[i]) for i in pvpq},
                    **{f"|V_{i+1}| (p.u.)": V[i] for i in pq}})
        if np.abs(mis).max() < tol:
            break
        J = jacobian(Y, V, th, pvpq, pq)
        if J0 is None:
            J0 = J.copy()
        dx = np.linalg.solve(J, mis)
        th[pvpq] += dx[: len(pvpq)]
        V[pq] += dx[len(pvpq):]
    P, Q = injections(Y, V, th)
    return {"V": V, "th": th, "P": P, "Q": Q, "log": pd.DataFrame(log).set_index("iteration"),
            "J0": J0, "converged": np.abs(mis).max() < tol}


def branch_flows(branches, V, th, names=None) -> pd.DataFrame:
    """Sending- and receiving-end complex powers and series+shunt losses of each branch."""
    U = V * np.exp(1j * th)
    rows = []
    for idx, b in enumerate(branches):
        i, k = b["f"], b["t"]
        y, ysh = b["y"], b.get("ysh", 0.0)
        a = b.get("tap", 1.0) * np.exp(1j * b.get("shift", 0.0))
        Ii = ((y + ysh / 2) / abs(a) ** 2) * U[i] - (y / np.conj(a)) * U[k]
        Ik = -(y / a) * U[i] + (y + ysh / 2) * U[k]
        Sik, Ski = U[i] * np.conj(Ii), U[k] * np.conj(Ik)
        rows.append({"branch": names[idx] if names else f"{i+1}-{k+1}",
                     "P_ik": Sik.real, "Q_ik": Sik.imag, "P_ki": Ski.real, "Q_ki": Ski.imag,
                     "P_loss": (Sik + Ski).real, "Q_loss": (Sik + Ski).imag})
    return pd.DataFrame(rows).set_index("branch")
