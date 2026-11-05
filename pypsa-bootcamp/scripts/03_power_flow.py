# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Chapter 3 - Power flow: how the current really distributes
#
# Chapter 2 used a single bus, so the grid could carry anything. Real grids have
# lines with resistance and reactance: current splits between parallel paths, the
# voltage sags far from the source, and a few percent of the energy is lost as
# heat. **Power flow** is the calculation that reveals all of this.
#
# We now build the **real 3-bus Bohol network** from the dataset and solve it two
# ways:
#
# - `n.pf()` - the full **AC** (non-linear) power flow: voltages, angles, reactive
#   power, losses. The physical truth.
# - `n.lpf()` - the **linear/DC** approximation: fast, no losses, voltages assumed
#   flat at 1.0 pu. The workhorse of large planning studies.
#
# **Goals of this chapter**
# - Build buses and lines from the dataset, in SI units (ohm, kV, MVA).
# - Understand the per-unit system that links ohm to the "pu" voltages PyPSA reports.
# - Run and compare `n.pf()` and `n.lpf()`.
# - Diagnose an undervoltage and fix it with a shunt capacitor.

# %%
import warnings, logging
warnings.filterwarnings("ignore")
for _n in ("pypsa", "linopy"):
    logging.getLogger(_n).setLevel(logging.ERROR)

from pathlib import Path
import numpy as np
import pandas as pd
import pypsa

DATA = next(p for p in [Path("data"), Path("../data"), Path("pypsa-bootcamp/data")]
            if (p / "PyPSA_Dataset_Bohol.xlsx").exists())
XLS = DATA / "PyPSA_Dataset_Bohol.xlsx"

# %% [markdown]
# ### 3.1 Build the network from the dataset
#
# We loop over the `buses` and `lines` sheets. Lines in PyPSA are given in **SI
# units**: resistance `r` and reactance `x` in **ohm**, nominal apparent power
# `s_nom` in **MVA**. Those are exactly the columns in the sheet.

# %%
buses = pd.read_excel(XLS, "buses")
lines = pd.read_excel(XLS, "lines")

n = pypsa.Network()
for b in buses.itertuples():
    # v_nom in kV; x,y are real longitude/latitude for the map later
    n.add("Bus", b.name, v_nom=b.v_nom, x=b.x, y=b.y)

for l in lines.itertuples():
    n.add("Line", l.name, bus0=l.bus0, bus1=l.bus1,
          r=l.r, x=l.x, s_nom=l.s_nom)   # ohm, ohm, MVA

print(n.buses[["v_nom"]].to_string())
print()
print(n.lines[["bus0", "bus1", "r", "x", "s_nom"]].to_string())

# %% [markdown]
# The island has a **138 kV backbone** (Corella and Ubay, joined by two parallel
# lines) and a weak **13.8 kV spur** to Tapal. Ubay is where the submarine cable
# from Leyte lands, so it is our natural slack (reference) bus.
#
# ### 3.2 The per-unit system (why PyPSA talks in "pu")
#
# Power engineers rarely quote voltage in kV during a study; they use **per-unit**:
# the actual value divided by a nominal base. The base impedance of a bus is
#
# > Z_base = V_nom^2 / S_base      (ohm, with V_nom in kV and S_base in MVA)
#
# A line's impedance in per-unit is then `x_pu = x_ohm / Z_base`. PyPSA stores ohm
# but converts internally, which is why `n.buses_t.v_mag_pu` comes back around 1.0.
# Let us compute the base for the 138 kV corridor so the numbers feel concrete.

# %%
S_BASE = 100.0  # MVA, the usual reference
for v in [138.0, 13.8]:
    z = v ** 2 / S_BASE
    print(f"V_nom = {v:6.1f} kV  ->  Z_base = {z:8.2f} ohm  (on a {S_BASE:.0f} MVA base)")

xpu = lines.loc[lines.name == "138_07UBAY_07CORELLA", "x"].iloc[0] / (138 ** 2 / S_BASE)
print(f"\nExample: the 138 kV line reactance 12.09 ohm = {xpu:.4f} pu on 100 MVA")

# %% [markdown]
# ### 3.3 Attach generation and demand, then run the AC power flow
#
# For a power flow we need:
# - a **slack** generator (here the Grid/cable at Ubay) that balances the system
#   and fixes the reference voltage and angle,
# - **loads** with both active power `p_set` (MW) and reactive power `q_set`
#   (MVAr). We assume a 0.95 power factor, so `Q = P * tan(acos(0.95))`.
#
# We take the evening peak hour, when demand is highest and the voltage problem
# is worst.

# %%
loads_t = pd.read_excel(XLS, "loads_t", index_col=0)
peak_hour = loads_t.sum(axis=1).idxmax()
pf_tan = np.tan(np.arccos(0.95))
print("peak hour:", peak_hour)

n.add("Generator", "Grid", bus="07UBAY", control="Slack", p_set=0.0)
for bus, col, name in [("07CORELLA", "07CORELLA_LOAD", "Load_Corella"),
                       ("07UBAY", "07UBAY_LOAD", "Load_Ubay")]:
    p = float(loads_t.loc[peak_hour, col])
    n.add("Load", name, bus=bus, p_set=p, q_set=p * pf_tan)

n.pf()   # Newton-Raphson AC power flow
print("\nDemand served (MW):", round(n.loads.p_set.sum(), 1))
print("\nBus voltages (per unit):")
print(n.buses_t.v_mag_pu.iloc[0].round(4).to_string())

# %% [markdown]
# **Read the result.** Ubay is the slack, pinned at 1.000 pu. Corella sits at
# about **0.977 pu**: the current drawn by its 53 MW load drops ~2 % of the voltage
# across the resistance and reactance of the 138 kV lines. That is the voltage
# drop a single bus could never show you.
#
# ### 3.4 Line flows and losses
#
# `p0` is the power entering a line at `bus0`, `p1` what leaves at `bus1`. Their
# sum is the **loss** (positive = power dissipated as heat in the resistance).

# %%
flows = pd.DataFrame({
    "P0 (MW)": n.lines_t.p0.iloc[0],
    "P1 (MW)": n.lines_t.p1.iloc[0],
    "loss (MW)": n.lines_t.p0.iloc[0] + n.lines_t.p1.iloc[0],
    "loading (%)": 100 * np.hypot(n.lines_t.p0, n.lines_t.q0).iloc[0] / n.lines.s_nom,
}).round(3)
print(flows.to_string())
print("\nTotal network losses:", round((n.lines_t.p0.iloc[0] + n.lines_t.p1.iloc[0]).sum(), 3), "MW")

# %% [markdown]
# The current splits between the two parallel Ubay-Corella lines in inverse
# proportion to their impedance: the stronger 138 kV line (lower reactance) takes
# the larger share. Nobody dispatched that split - it is pure physics, and only an
# AC/DC power flow reveals it.
#
# ### 3.5 AC vs DC: what the linear approximation drops
#
# `n.lpf()` solves the **linearised** problem. It assumes every voltage is exactly
# 1.0 pu and ignores resistance, so it reports **no losses** and a slightly
# different flow split. It is far faster and always converges, which is why it is
# used for large markets and planning. Compare the two.

# %%
ac = n.lines_t.p0.iloc[0].copy()
n.lpf()
dc = n.lines_t.p0.iloc[0]
cmp = pd.DataFrame({"AC p0 (MW)": ac, "DC p0 (MW)": dc, "diff (MW)": ac - dc}).round(3)
print(cmp.to_string())
print("\nDC voltages are all exactly 1.0 pu:",
      bool((n.buses_t.v_mag_pu.iloc[0] == 1.0).all()))
print("=> DC is quick and robust, but blind to voltage and losses.")

# %% [markdown]
# ### 3.6 Fix the undervoltage with a capacitor
#
# 0.977 pu is acceptable, but on a heavier day Corella could fall below the 0.95 pu
# limit. The classic remedy is a **shunt capacitor bank** that injects reactive
# power locally, so less has to travel over the lines. We add 10 MVAr at Corella
# (as a `ShuntImpedance`, whose susceptance is `b = Q / V_nom^2`) and re-run.

# %%
def ac_voltages(cap_mvar=0.0):
    m = pypsa.Network()
    for b in buses.itertuples():
        m.add("Bus", b.name, v_nom=b.v_nom, x=b.x, y=b.y)
    for l in lines.itertuples():
        m.add("Line", l.name, bus0=l.bus0, bus1=l.bus1, r=l.r, x=l.x, s_nom=l.s_nom)
    m.add("Generator", "Grid", bus="07UBAY", control="Slack", p_set=0.0)
    for bus, col, name in [("07CORELLA", "07CORELLA_LOAD", "Load_Corella"),
                           ("07UBAY", "07UBAY_LOAD", "Load_Ubay")]:
        p = float(loads_t.loc[peak_hour, col])
        m.add("Load", name, bus=bus, p_set=p, q_set=p * pf_tan)
    if cap_mvar:
        m.add("ShuntImpedance", "cap_Corella", bus="07CORELLA", b=cap_mvar / 138 ** 2)
    m.pf()
    return m.buses_t.v_mag_pu.iloc[0]

before = ac_voltages(0.0)
after = ac_voltages(10.0)
print(pd.DataFrame({"without cap": before, "with 10 MVAr": after}).round(4).to_string())
print(f"\nCorella voltage raised from {before['07CORELLA']:.3f} to {after['07CORELLA']:.3f} pu.")

# %% [markdown]
# ## Summary of Chapter 3
#
# - A power flow turns a list of injections into **voltages, angles, flows and
#   losses**. A single bus cannot do this.
# - Per-unit (`Z_base = V_nom^2 / S_base`) links the ohm we type to the ~1.0 pu
#   voltages PyPSA reports.
# - `n.pf()` is the exact AC truth (Corella at 0.977 pu, ~0.8 MW lost);
#   `n.lpf()` is the fast linear approximation (flat voltages, no losses).
# - Current splits between parallel lines by impedance, and a local **capacitor**
#   lifts a sagging voltage. These are the everyday diagnostics of grid operation.
# - Next chapter we stop fixing the dispatch by hand and let PyPSA **optimise** it.
