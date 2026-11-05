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
# # Chapter 2 - Your first PyPSA network
#
# Everything in PyPSA lives inside one `Network` object. The components (buses,
# loads, generators, lines) are stored as **pandas tables** that you fill with
# `n.add(...)`. In this chapter we build the smallest useful model by hand - a
# single bus with the demand of Corella and two plants - so you can see exactly
# what those tables look like before we scale up to the real island.
#
# **Goals of this chapter**
# - Use `n.add()` to create carriers, a bus, a load and generators.
# - Read the component tables `n.buses`, `n.loads`, `n.generators`.
# - Run `n.statistics()` for a first automatic summary.
# - Understand the "copper plate" assumption (one bus = no grid limits).

# %%
import warnings, logging
warnings.filterwarnings("ignore")
for _n in ("pypsa", "linopy", "pypsa.consistency"):
    logging.getLogger(_n).setLevel(logging.ERROR)

import numpy as np
import pandas as pd
import pypsa

print("PyPSA version:", pypsa.__version__)

# %% [markdown]
# ### 2.1 Create the network and add components
#
# The pattern is always `n.add("ComponentType", "name", **parameters)`. Good
# habit: declare the **Carrier** first, so every plant can point at a known fuel
# and PyPSA never warns about an undefined carrier.

# %%
n = pypsa.Network()

# 1) carriers (fuels / technologies) - cost and CO2 attached later
n.add("Carrier", "Diesel", co2_emissions=0.2571)   # tonnes CO2 per MWh thermal
n.add("Carrier", "Grid", co2_emissions=0.1100)      # imported electricity

# 2) one bus: the 138 kV node at Corella. With a single bus, every plant and the
#    load sit at the same place: this is the "copper plate" - no line can limit
#    anything. We relax that in Chapter 3.
n.add("Bus", "Corella", v_nom=138)

# 3) the demand at Corella (its daytime value, held constant for now)
n.add("Load", "Corella_load", bus="Corella", p_set=42.0)   # MW

# 4) two ways to serve it: cheap imported grid power, expensive local diesel
n.add("Generator", "Grid_import", bus="Corella", carrier="Grid",
      p_nom=138, marginal_cost=43.0)      # large cable, cheap
n.add("Generator", "Diesel_local", bus="Corella", carrier="Diesel",
      p_nom=30, marginal_cost=157.0)      # small, expensive

print("buses:", len(n.buses), "| loads:", len(n.loads),
      "| generators:", len(n.generators), "| carriers:", len(n.carriers))

# %% [markdown]
# ### 2.2 Look at the component tables
#
# Each component type is a DataFrame indexed by the name you gave. PyPSA fills in
# every attribute you did not set with its default value, so the tables are wider
# than what we typed.

# %%
print("n.buses")
print(n.buses[["v_nom"]].to_string())
print("\nn.loads")
print(n.loads[["bus", "p_set"]].to_string())
print("\nn.generators")
print(n.generators[["bus", "carrier", "p_nom", "marginal_cost"]].to_string())

# %% [markdown]
# ### 2.3 A first dispatch by hand, then by PyPSA
#
# With 42 MW of demand and a 138 MW cheap cable, the obvious least-cost answer is:
# **import all 42 MW, run no diesel.** Let us ask the optimiser and check it agrees.

# %%
status, cond = n.optimize(solver_name="highs",
                          solver_options={"output_flag": False},
                          log_to_console=False)
print("status:", status)
print("\nDispatch (MW):")
print(n.generators_t.p.iloc[0].round(2).to_string())
print("\nTotal cost:", round(float(n.objective), 1),
      "= 42 MW x 43 =", 42 * 43)

# %% [markdown]
# As expected the diesel stays off. The grid carries the whole load because it is
# cheaper and big enough. This is the **merit order** in miniature; Chapter 4
# makes it the central idea.
#
# ### 2.4 `n.statistics()` - the automatic summary
#
# Once a network is solved, `n.statistics()` aggregates the result per carrier:
# installed capacity, energy supplied, cost, CO2. It is the fastest way to read a
# result and we will use it in every later chapter.

# %%
stats = n.statistics()
cols = [c for c in ["Optimal Capacity", "Supply", "Operational Expenditure"] if c in stats.columns]
print(stats[cols].round(1).to_string())

# %% [markdown]
# ### 2.5 What one bus cannot tell you
#
# A single bus assumes the grid is a perfect copper plate: infinite line capacity,
# no voltage drop, no losses. That is fine for a first economic look, but a real
# island has a 138 kV backbone and a weak 13.8 kV pocket, and the lines **do**
# limit the flows and drop the voltage. To see that, we need more than one bus and
# a real power flow - which is exactly Chapter 3.
#
# To make the point concrete, add the second real bus (Ubay) and the cable between
# them, then look at the (still trivial) line flow.

# %%
n.add("Bus", "Ubay", v_nom=138)
# move the cheap grid import to Ubay, where the submarine cable actually lands
n.generators.loc["Grid_import", "bus"] = "Ubay"
# a line from Ubay to Corella (per-unit impedance converted to ohm in Chapter 3)
n.add("Line", "Ubay-Corella", bus0="Ubay", bus1="Corella", x=12.09, r=8.51, s_nom=138)

n.optimize(solver_name="highs", solver_options={"output_flag": False}, log_to_console=False)
print("Power now flows Ubay -> Corella over the cable:")
print(n.lines_t.p0.iloc[0].round(2).to_string(), "MW")

# %% [markdown]
# ## Summary of Chapter 2
#
# - A PyPSA model is a `Network` of component **tables** filled with `n.add()`.
# - With a single bus the grid is a copper plate: the cheapest generator that is
#   big enough serves the whole load. Here the 43 /MWh grid import beats the
#   157 /MWh diesel and diesel stays off.
# - `n.statistics()` gives a one-line summary per carrier.
# - A single bus hides the grid. Chapter 3 introduces buses, lines and the two
#   kinds of power flow that reveal voltages, flows and losses.
