"""Exercise 5, Assignment 1 - Newton's method on f(x) = 10 x^2 - 2 x^3 = 0.

Run from the repository root:  python solutions/s01_newton_method.py
"""
import numpy as np


def f(x):
    return 10 * x**2 - 2 * x**3          # f(x) = 2x^2 (5 - x): roots 0 (double) and 5


def df(x):
    return 20 * x - 6 * x**2             # f'(x) = 2x (10 - 3x): zero at x = 0 and x = 10/3


def newton(x0, n_iter=5):
    """Five Newton steps x_{k+1} = x_k + dx with dx = -f(x_k) / f'(x_k)."""
    x = x0
    print(f"{'k':>2} {'x_k':>12} {'f(x_k)':>12} {'f`(x_k)':>12} {'dx':>12}")
    for k in range(n_iter):
        dx = -f(x) / df(x)
        print(f"{k:>2} {x:12.6f} {f(x):12.6f} {df(x):12.6f} {dx:12.6f}")
        x += dx
    print(f"{n_iter:>2} {x:12.8f}")
    return x


print("(a) start at x0 = 1")
xa = newton(1.0)
print("\n(b) start at x0 = 4")
xb = newton(4.0)

# Convergence rate: error ratio e_{k+1}/e_k (linear) or e_{k+1}/e_k^2 (quadratic)
print("\nConvergence check")
for x0, root in [(1.0, 0.0), (4.0, 5.0)]:
    x, e = x0, [abs(x0 - root)]
    for _ in range(5):
        x -= f(x) / df(x)
        e.append(abs(x - root))
    e = np.array(e)
    print(f"x0 = {x0}: e_k+1/e_k   = {np.round(e[1:] / e[:-1], 4)}")
    print(f"          e_k+1/e_k^2 = {np.round(e[1:] / e[:-1] ** 2, 4)}")
print("f'(10/3) =", df(10 / 3), "-> no Newton step is possible from x0 = 10/3")
