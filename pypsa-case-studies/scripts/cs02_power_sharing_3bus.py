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
# # CS02 - Power sharing between a thermal plant and a solar plant (3-bus, Niamey context)
#
# **Problem type:** power balance - who supplies the load, the role of the slack bus,
# reactive power and losses.
# **Source:** Travaux pratiques, case 1. Grid parameters are **fictitious and educational**
# (not NIGELEC data); the solar profile is **real** (NASA POWER, Niamey, 4 May 2023).
#
# ## 1. Context
# | Bus | Equipment | Power |
# |---|---|---|
# | 1 | Thermal power station (HFO/diesel) | slack, $|V| = 1.02$ p.u. |
# | 2 | City substation | 50 MW + 20 MVAr at the evening peak |
# | 3 | Solar PV plant | 30 MW peak |
#
# Three 132 kV lines (ACSR 240/40: $0.12 + j0.39$ ohm/km, 2.9 uS/km), 15 to 25 km long,
# hot-season rating 100 MVA.
#
# ## 2. Exercise
# 1. Are the voltages at buses 2 and 3 close to nominal?
# 2. Does the solar plant reduce the output of the thermal plant? By how much?
# 3. Is there enough reactive power? Who provides it?
# 4. Are the lines adequately sized?
# 5. What are the total active losses?
# 6. *(Real profile)* Over the 24 hours of the peak-demand day, how much energy does the PV
#    plant supply and how does the thermal plant follow the residual demand?
#
# ## 3. Theory in three lines
# * The **slack bus** fixes the angle reference and closes the power balance:
#   $P_{slack} = \sum P_{load} - \sum P_{gen,other} + P_{losses}$.
#   First estimate (no losses): $P_{slack} = 50 - 30 = 20$ MW.
# * A **PQ** injection (PV plant at unity power factor) fixes $P$ and $Q = 0$; a **PV**
#   injection (plant in voltage-control mode) fixes $P$ and $|V|$, and $Q$ follows.
# * Voltage drop along a line: $\Delta V \approx (RP + XQ)/V$. On 132 kV lines $X \gg R$, so
#   **reactive** flows dominate voltage drop, **active** flows dominate angles.

# %%
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "src" / "pscs").exists())
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
import pypsa
import matplotlib.pyplot as plt

import pscs
from pscs.kpi import run_pf, kpis, bus_table, branch_table, one_snapshot
from pscs.plotting import ENTITY, SERIES, CRITICAL, INK2, MUTED, save, limit_line

DATA, FIG, TAB = pscs.setup()

# %% [markdown]
# ## 4. Load the PyPSA dataset
# The dataset is a standard PyPSA CSV folder: `buses.csv`, `carriers.csv`, `generators.csv`,
# `loads.csv`, `lines.csv`, plus the time series `loads-p_set.csv`, `loads-q_set.csv`,
# `generators-p_set.csv` and `generators-p_max_pu.csv` (= `loads_t`, `generators_t`).

# %%
n = pypsa.Network(DATA / "networks" / "niamey_3bus")
print(n)
n.buses[["v_nom", "v_mag_pu_set", "description"]]

# %%
n.lines[["bus0", "bus1", "length", "r", "x", "b", "s_nom"]]

# %%
pd.concat({"PV output (MW)": n.generators_t.p_set["pv"],
           "city demand (MW)": n.loads_t.p_set["city"]}, axis=1).T.round(1)

# %% [markdown]
# ## 5. Design-point study (questions 1 to 5)
# We take the evening-peak demand (50 MW + 20 MVAr) and assume the PV plant at full output
# (30 MW), as in the exercise. Three variants of the solar plant:
# * **No PV** - reference;
# * **PV, unity power factor** - the default grid-code setting for small plants;
# * **PV, voltage control** - the inverters hold 1.02 p.u. at bus 3 (they become a PV bus).

# %%
def design_point(pv_mw, mode="pq"):
    m = one_snapshot(n, n.snapshots[19])                 # 19:00, the peak hour
    m.loads_t.p_set.iloc[0, 0], m.loads_t.q_set.iloc[0, 0] = 50.0, 20.0
    m.generators_t.p_set.loc[:, "pv"] = pv_mw
    if mode == "pv":
        m.generators.loc["pv", "control"] = "PV"
        m.buses.loc["3", "v_mag_pu_set"] = 1.02
    run_pf(m)
    return m

variants = {"No PV": design_point(0), "PV 30 MW, unity PF": design_point(30),
            "PV 30 MW, voltage control": design_point(30, "pv")}
rows = {}
for name, m in variants.items():
    k = kpis(m)
    v = m.buses_t.v_mag_pu.iloc[0]
    rows[name] = {"|V2| (p.u.)": v["2"], "|V3| (p.u.)": v["3"],
                  "thermal P (MW)": m.generators_t.p.iloc[0]["thermal"],
                  "thermal Q (MVAr)": m.generators_t.q.iloc[0]["thermal"],
                  "PV Q (MVAr)": m.generators_t.q.iloc[0]["pv"],
                  "max loading (%)": k["max loading (%)"], "losses (MW)": k["losses (MW)"]}
design = pd.DataFrame(rows).T
design.to_csv(TAB / "cs02_design_point.csv")
design.round(3)

# %%
branch_table(variants["PV 30 MW, unity PF"])[["from", "to", "P_from (MW)", "Q_from (MVAr)",
                                              "loss (MW)", "|S| (MVA)", "loading (%)"]].round(2)

# %% [markdown]
# **Answers** (the numbers are printed from the results above)

# %%
d = design
print(f"""1. Voltages: |V2| = {d.loc['No PV','|V2| (p.u.)']:.3f} p.u. without PV and {d.loc['PV 30 MW, unity PF','|V2| (p.u.)']:.3f} with PV
   (slack at 1.02): close to nominal, inside 0.95-1.05. The city bus is the lowest point.
2. Thermal output: {d.loc['No PV','thermal P (MW)']:.2f} MW without PV, {d.loc['PV 30 MW, unity PF','thermal P (MW)']:.2f} MW with 30 MW of PV.
   The estimate 50 - 30 = 20 MW is right; the difference is the losses.
3. Reactive power: at unity PF the thermal plant gives {d.loc['PV 30 MW, unity PF','thermal Q (MVAr)']:.1f} MVAr (city 20 MVAr minus the
   net line charging). In voltage-control mode the PV inverters give {d.loc['PV 30 MW, voltage control','PV Q (MVAr)']:.1f} MVAr and the
   thermal plant only {d.loc['PV 30 MW, voltage control','thermal Q (MVAr)']:.1f} MVAr. A 30 MW plant with ~33 MVA of inverters can
   supply sqrt(33^2-30^2) = {np.sqrt(33**2-30**2):.1f} MVAr at full output: the request is feasible.
4. Lines: maximum loading {d['max loading (%)'].max():.0f} % of the 100 MVA hot-season rating: adequate.
5. Active losses: {d.loc['No PV','losses (MW)']:.2f} MW without PV ({100*d.loc['No PV','losses (MW)']/50:.1f} % of demand),
   {d.loc['PV 30 MW, unity PF','losses (MW)']:.2f} MW with PV: generation closer to the load means less transport.""")

# %% [markdown]
# ## 6. A real day: 24 AC load flows with the measured solar profile (question 6)
# PyPSA runs one Newton-Raphson load flow per snapshot: `n.pf()` solves the 24 hours at once.

# %%
run_pf(n)
day = pd.DataFrame({
    "demand (MW)": n.loads_t.p.sum(axis=1),
    "PV (MW)": n.generators_t.p["pv"],
    "thermal (MW)": n.generators_t.p["thermal"],
    "losses (MW)": (n.lines_t.p0 + n.lines_t.p1).sum(axis=1),
    "|V2| (p.u.)": n.buses_t.v_mag_pu["2"],
    "|V3| (p.u.)": n.buses_t.v_mag_pu["3"],
})
day.index = day.index.hour
day.to_csv(TAB / "cs02_day.csv")
energy = day[["demand (MW)", "PV (MW)", "thermal (MW)", "losses (MW)"]].sum()
print("Daily energy (MWh):"); print(energy.round(1))
print("PV share of demand: %.1f %%" % (100 * energy["PV (MW)"] / energy["demand (MW)"]))
day.round(3)

# %%
fig, ax = plt.subplots(figsize=(7.2, 4.0))
ax.plot(day.index, day["demand (MW)"], color=ENTITY["demand"], label="city demand")
ax.plot(day.index, day["thermal (MW)"], color=ENTITY["thermal"], label="thermal plant (slack)")
ax.fill_between(day.index, 0, day["PV (MW)"], color=ENTITY["solar"], alpha=0.35, lw=0)
ax.plot(day.index, day["PV (MW)"], color=ENTITY["solar"], label="solar PV (real profile)")
for col, y, txt in [(ENTITY["demand"], day["demand (MW)"].max(), "evening peak"),
                    (ENTITY["thermal"], day["thermal (MW)"].min(), "thermal minimum at midday")]:
    h = (day["demand (MW)"] if txt == "evening peak" else day["thermal (MW)"]).idxmax() \
        if txt == "evening peak" else day["thermal (MW)"].idxmin()
    ax.annotate(f"{txt}: {y:.0f} MW", (h, y), xytext=(6, 6 if txt == 'evening peak' else -14),
                textcoords="offset points", fontsize=8.5, color=INK2)
ax.set_xlabel("hour of 4 May 2023 (local time)"); ax.set_ylabel("MW")
ax.set_xticks(range(0, 24, 3)); ax.set_ylim(0, 60)
ax.set_title("The thermal plant follows the demand minus the solar output")
ax.legend(loc="upper left", ncol=3)
save(fig, FIG / "cs02_day_balance.png")
fig

# %%
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.plot(day.index, day["|V2| (p.u.)"], color=SERIES[0], label="bus 2, city")
ax.plot(day.index, day["|V3| (p.u.)"], color=SERIES[1], label="bus 3, PV plant")
limit_line(ax, 0.95, "lower limit 0.95", color=CRITICAL)
ax.set_ylim(0.94, 1.03); ax.set_xticks(range(0, 24, 3))
ax.set_xlabel("hour (local time)"); ax.set_ylabel("|V| (p.u.)")
ax.set_title("Voltages stay within limits all day; the lowest point is the evening peak")
ax.legend(loc="lower left", ncol=2)
save(fig, FIG / "cs02_day_voltages.png")
fig

# %% [markdown]
# ## 7. Interpretation
# * On this hot, hazy peak day the PV plant (30 MW) produces at most about 20 MW and covers
#   about 15 % of the daily energy. It covers part of the **day-time** demand, but the **peak is in the evening**
#   (19:00-21:00), when the sun has set: the thermal plant must still be sized for the full
#   peak. PV saves fuel (energy) but, without storage, does not reduce the capacity needed.
# * The thermal plant must **ramp** down at midday and up in the late afternoon (a steep ramp
#   between 16:00 and 19:00). This "duck curve" shape grows with more solar.
# * Voltages and line loadings are comfortable in this small, short network: the problem
#   here is **energy and flexibility**, not the grid. The next cases add distance (CS03) and
#   meshing (CS04-CS06), where the grid becomes the constraint.
#
# **What to say:** "In this first case I study a three-bus grid to understand how the load is
# shared between conventional and solar generation. The load flow gives the nodal voltages,
# the line flows and the losses. Solar reduces the thermal output by up to 30 MW (20 MW on the
# real peak day) and reduces the losses, but the evening peak remains entirely on the thermal plant."

# %%
pscs.save_summary("cs02", {
    "thermal_noPV": design.loc["No PV", "thermal P (MW)"],
    "thermal_PV": design.loc["PV 30 MW, unity PF", "thermal P (MW)"],
    "loss_noPV": design.loc["No PV", "losses (MW)"],
    "loss_PV": design.loc["PV 30 MW, unity PF", "losses (MW)"],
    "V2_noPV": design.loc["No PV", "|V2| (p.u.)"], "V2_PV": design.loc["PV 30 MW, unity PF", "|V2| (p.u.)"],
    "Q_pv_voltage_control": design.loc["PV 30 MW, voltage control", "PV Q (MVAr)"],
    "max_loading": design["max loading (%)"].max(),
    "day_demand_MWh": energy["demand (MW)"], "day_pv_MWh": energy["PV (MW)"],
    "day_thermal_MWh": energy["thermal (MW)"], "pv_share": energy["PV (MW)"] / energy["demand (MW)"],
    "thermal_min_MW": day["thermal (MW)"].min(), "thermal_max_MW": day["thermal (MW)"].max(),
})
