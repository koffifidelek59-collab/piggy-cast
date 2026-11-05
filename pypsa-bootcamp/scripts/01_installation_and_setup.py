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
# # Chapter 1 - Installation, setup and the Bohol dataset
#
# Welcome to the **PyPSA bootcamp**. The whole course is built around one real
# system: the electricity island of **Bohol** (Philippines). Every chapter adds
# one new modelling idea on top of the same data, exactly the way you would learn
# a programming language one concept at a time.
#
# PyPSA (*Python for Power System Analysis*) is a free library that lets you:
#
# - build a power network (buses, lines, generators, loads, storage) as a set of tables,
# - run a **power flow** (how the current actually distributes in the grid),
# - run an **optimisation** (how to operate or invest in the system at least cost).
#
# **Goals of this chapter**
# - Check that PyPSA and a linear solver (HiGHS) are installed and working.
# - Load the Bohol dataset and look at what is inside it.
# - Understand the eight component types we will use for the rest of the bootcamp.

# %% [markdown]
# ### 1.1 Check the installation
#
# If the imports below run without error, you are ready. `pypsa.__version__`
# should be 1.x. We also silence a few harmless warnings so the output stays clean.

# %%
import warnings, logging
warnings.filterwarnings("ignore")
for _n in ("pypsa", "linopy", "pypsa.consistency"):
    logging.getLogger(_n).setLevel(logging.ERROR)

from pathlib import Path
import numpy as np
import pandas as pd
import pypsa

print("PyPSA   :", pypsa.__version__)
print("pandas  :", pd.__version__)
print("numpy   :", np.__version__)

# %% [markdown]
# ### 1.2 Check the solver
#
# Optimisation chapters (4 to 8) need a Linear Programming solver. PyPSA ships
# with **HiGHS**, which is open source and needs no license. We test it on a
# trivial one-line problem: one 100 MW generator feeding one 80 MW load. The
# only possible answer is "produce 80 MW", at a cost of 80 x 10 = 800.

# %%
test = pypsa.Network()
test.add("Bus", "b")
test.add("Generator", "g", bus="b", p_nom=100, marginal_cost=10)
test.add("Load", "d", bus="b", p_set=80)

status, condition = test.optimize(solver_name="highs",
                                  solver_options={"output_flag": False},
                                  log_to_console=False)
print("solver status :", status, "/", condition)
print("generator output :", round(test.generators_t.p.iloc[0, 0], 1), "MW")
print("total cost       :", round(float(test.objective), 1), "currency units")
assert status == "ok", "HiGHS is not available - check the installation"
print("\nSolver works. You are ready for the whole bootcamp.")

# %% [markdown]
# ### 1.3 Locate the Bohol dataset
#
# The dataset is a single Excel file with seven sheets. We find it whether the
# notebook is run from the project root or from the `notebooks/` folder.

# %%
DATA = next(p for p in [Path("data"), Path("../data"), Path("pypsa-bootcamp/data")]
            if (p / "PyPSA_Dataset_Bohol.xlsx").exists())
XLS = DATA / "PyPSA_Dataset_Bohol.xlsx"
sheets = pd.ExcelFile(XLS).sheet_names
print("dataset folder :", DATA.resolve())
print("sheets         :", sheets)

# %% [markdown]
# ### 1.4 What is in each sheet
#
# The seven sheets map one-to-one onto PyPSA components. This is the vocabulary
# of the whole bootcamp, so take a minute here.
#
# | Sheet | PyPSA component | Meaning |
# | --- | --- | --- |
# | `buses` | **Bus** | an electrical node (a substation), at a voltage level |
# | `lines` | **Line** | an AC transmission line joining two buses |
# | `loads` | **Load** | electricity demand connected to a bus |
# | `generators` | **Generator** | a power plant (diesel, hydro, grid import) |
# | `carriers` | **Carrier** | a technology/fuel, with its cost and CO2 content |
# | `loads_t` | time series | hourly demand for one day (the `_t` means "time dependent") |
# | `generators_t` | time series | hourly availability of solar and wind |
#
# Let us look at the static sheets.

# %%
buses = pd.read_excel(XLS, "buses")
print("BUSES - the three nodes of the Bohol grid")
print(buses.to_string(index=False))

# %% [markdown]
# Three buses: **07CORELLA** and **07UBAY** at 138 kV (the transmission backbone)
# and **07TAPAL** at 13.8 kV (a distribution pocket). The `x` and `y` columns are
# the real longitude/latitude, which we will use to draw the network on a map.

# %%
lines = pd.read_excel(XLS, "lines")
print("LINES - the AC corridors")
print(lines.to_string(index=False))
print("\nGENERATORS - the power plants")
print(pd.read_excel(XLS, "generators").to_string(index=False))

# %% [markdown]
# Thirteen generators: four diesel units at Tapal, four older diesel units and
# four small hydro units at Corella, plus one "Grid" generator at Ubay that stands
# for the submarine cable importing power from the neighbouring island of Leyte.
#
# ### 1.5 Carriers: where the economics live
#
# A **Carrier** is a fuel or technology. PyPSA uses it to attach two things to
# every plant of that type: its **CO2 content** and the raw numbers we turn into
# a **marginal cost** (currency per MWh produced) and a **capital cost** (currency
# per MW of capacity). We will compute those in Chapter 4; for now just read them.

# %%
carriers = pd.read_excel(XLS, "carriers")
print("CARRIERS")
print(carriers.to_string(index=False))

# %% [markdown]
# Reading the economics the way the rest of the bootcamp will:
#
# - **marginal cost** = `VOM + fuel / efficiency` (variable O&M plus the fuel
#   burned per MWh of electricity). Diesel burns expensive fuel at 35 % efficiency,
#   so it will be costly; hydro and the grid import are cheap.
# - **capital cost** = `(1 + FOM) * investment / (lifetime * 365.25)`, i.e. the
#   build cost spread over the plant's life and expressed **per day** (our
#   optimisation horizon is one day).

# %%
econ = carriers.assign(
    marginal_cost=lambda d: (d.VOM + d.fuel / d.efficiency).round(2),
    capital_cost_per_day=lambda d: ((1 + d.FOM) * d.investment / (d.lifetime * 365.25)).round(1),
)[["name", "co2_emissions", "marginal_cost", "capital_cost_per_day"]]
print(econ.to_string(index=False))

# %% [markdown]
# Already a result worth noting: **diesel costs about 157 /MWh, the grid import
# about 43 /MWh, and hydro is almost free.** Any least-cost model will lean on
# hydro and the cable first and keep diesel for the peak. We will prove it in
# Chapter 4.
#
# ### 1.6 The time series
#
# The `_t` sheets hold one winter day (2 January 2023) at hourly resolution.

# %%
loads_t = pd.read_excel(XLS, "loads_t", index_col=0)
gens_t = pd.read_excel(XLS, "generators_t", index_col=0)
print("Demand (MW) - first hours:")
print(loads_t.head(3).round(2).to_string())
print("\nRenewable availability (fraction of capacity) - midday hours:")
print(gens_t.iloc[9:13].round(3).to_string())
print("\nDaily peak demand:", round(loads_t.sum(axis=1).max(), 1), "MW",
      "| daily energy:", round(loads_t.sum(axis=1).sum(), 0), "MWh")

# %% [markdown]
# Solar peaks at noon (~0.67 of its capacity) and is zero at night; wind is
# strong all day on this date (0.4 to 0.85). The island peaks near 84 MW.
#
# ## Summary of Chapter 1
#
# - PyPSA and the HiGHS solver are installed and solve a trivial problem correctly.
# - The Bohol dataset has **3 buses, 3 lines, 13 generators, 6 carriers** and a
#   24-hour demand and renewable profile.
# - Economics come from the carriers: **diesel ~157, grid ~43, hydro ~0** per MWh.
# - Next chapter we build our very first network by hand and read its tables.
