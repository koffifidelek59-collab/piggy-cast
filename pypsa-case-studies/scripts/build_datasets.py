"""Build every PyPSA dataset used by the case studies and export it as CSV folders.

A PyPSA CSV folder is the standard, tool-independent way to share a network:

    buses.csv            one row per node (nominal voltage, voltage set point, limits)
    carriers.csv         energy carriers (AC, solar, gas, battery ...) with CO2 factors
    generators.csv       static generator data (bus, control type, capacity, costs)
    loads.csv            static load data
    lines.csv            series r, x (ohm), shunt b (S), thermal rating s_nom (MVA)
    transformers.csv     per-unit impedances on s_nom, tap ratio
    storage_units.csv    batteries (power, hours of storage, efficiencies)
    snapshots.csv        the time steps studied
    loads-p_set.csv      loads_t.p_set : time series of active demand (MW)
    loads-q_set.csv      loads_t.q_set : time series of reactive demand (MVAr)
    generators-p_set.csv      generators_t.p_set : dispatch used by the AC load flow
    generators-p_max_pu.csv   generators_t.p_max_pu : availability (PV capacity factor)

Load any dataset with   n = pypsa.Network("data/networks/<name>")

Run:  python scripts/build_datasets.py
"""
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pscs import DATA                                                    # noqa: E402
from pscs import assumptions as A                                        # noqa: E402
from pscs.demand import city_load                                        # noqa: E402
from pscs.matpower import matpower_to_pypsa, read_matpower                # noqa: E402
from pscs.solar import pv_profile, to_local, weather                      # noqa: E402

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
OUT = DATA / "networks"

# 132 kV overhead line, ACSR 240/40 mm2 (typical per-km values)
R_KM, X_KM, B_KM = 0.12, 0.39, 2.9e-6       # ohm/km, ohm/km, S/km
HOT_RATING = 100.0                          # MVA, rating at 45 degC ambient (assumption)

CARRIERS = {   # name: (nice name, colour, tCO2/MWh_el)
    "AC": ("AC grid", "#898781", 0.0),
    "thermal": ("Thermal (HFO/diesel)", "#eb6834", A.THERMAL_CO2),
    "import": ("Import interconnector", "#6250d6", 0.0),
    "solar": ("Solar PV", "#eda100", 0.0),
    "battery": ("Battery", "#1baf7a", 0.0),
    "diesel": ("Diesel genset", "#eb6834", A.DIESEL_CO2),
    "gas": ("Conventional", "#52514e", 0.0),
}


def add_carriers(n, names):
    for c in names:
        nice, color, co2 = CARRIERS[c]
        n.add("Carrier", c, nice_name=nice, color=color, co2_emissions=co2)


def export(n: pypsa.Network, name: str, description: str):
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    for f in folder.glob("*.csv"):
        f.unlink()
    n.export_to_csv_folder(folder)
    comps = {c: len(getattr(n, ln)) for c, ln in
             [("buses", "buses"), ("carriers", "carriers"), ("generators", "generators"),
              ("loads", "loads"), ("lines", "lines"), ("transformers", "transformers"),
              ("storage_units", "storage_units"), ("shunt_impedances", "shunt_impedances")]}
    ts = sorted(p.name for p in folder.glob("*-*.csv"))
    readme = [f"# Dataset `{name}`", "", description.strip(), "",
              f"Snapshots: {len(n.snapshots)} ({n.snapshots[0]} to {n.snapshots[-1]})", "",
              "| component | rows |", "|---|---|"]
    readme += [f"| {k} | {v} |" for k, v in comps.items() if v]
    readme += ["", "Time-series files: " + (", ".join(f"`{t}`" for t in ts) if ts else "none"),
               "", "Load with: `n = pypsa.Network(\"data/networks/%s\")`" % name]
    (folder / "README.md").write_text("\n".join(readme) + "\n")
    print(f"  {name:28s} {comps}  snapshots={len(n.snapshots)}")


def line(n, name, b0, b1, km, s_nom=HOT_RATING):
    n.add("Line", name, bus0=b0, bus1=b1, r=R_KM * km, x=X_KM * km, b=B_KM * km,
          s_nom=s_nom, length=km, carrier="AC")


def day_profiles(date: str):
    """Real PV capacity factor and modelled city demand shape (peak = 1) for one local day."""
    cf = to_local(pv_profile("niamey"), "niamey").loc[date]
    d = to_local(city_load(weather("niamey").temp_air, 1.0), "niamey").loc[date]
    return cf, d / d.max()


# ============================================================================ CS01
def build_ex5():
    """Exercise 5, assignment 2: three buses, three identical lossless pi lines."""
    vn, sb = 110.0, 100.0                       # kV and MVA bases (the exercise is in p.u.)
    zb = vn ** 2 / sb
    n = pypsa.Network(name="Exercise 5 three-bus system")
    add_carriers(n, ["AC", "gas"])
    for b, v in [("1", 1.00), ("2", 1.05), ("3", 1.00)]:
        n.add("Bus", b, v_nom=vn, v_mag_pu_set=v, carrier="AC")
    y_series, y_shunt_total = -8j, 0.1j            # p.u. (see the note on the data in CS01)
    z = 1 / y_series
    for a, b in [("1", "2"), ("1", "3"), ("2", "3")]:
        n.add("Line", f"L{a}-{b}", bus0=a, bus1=b, r=z.real * zb, x=z.imag * zb,
              b=y_shunt_total.imag / zb, s_nom=500, carrier="AC")
    n.add("Generator", "G1", bus="1", control="Slack", p_nom=500, p_set=0.0, carrier="gas")
    n.add("Generator", "G2", bus="2", control="PV", p_set=0.50 * sb, p_nom=200, carrier="gas")
    n.add("Load", "D3", bus="3", p_set=2.50 * sb, q_set=1.00 * sb)
    export(n, "ex5_3bus", """
Exercise 5 (Power System Modeling, Simulation and Control), assignment 2.
Bus 1 slack (|U1| = 1.00, theta1 = 0), bus 2 PV (P_G2 = 0.50 p.u., |U2| = 1.05),
bus 3 load (P_D3 = 2.50, Q_D3 = 1.00 p.u.). S_base = 100 MVA, U_base = 110 kV.
Each line: series admittance -j8 p.u., total shunt admittance j0.1 p.u. (j0.05 at each end).""")


# ============================================================================ CS02
def build_niamey_3bus(date="2023-05-04"):
    cf, shape = day_profiles(date)
    n = pypsa.Network(name="Niamey area, 3-bus teaching network")
    n.set_snapshots(cf.index)
    add_carriers(n, ["AC", "thermal", "solar"])
    for b, desc, x, y in [("1", "Thermal power station (slack)", 0, 1),
                          ("2", "City substation", 2, 0), ("3", "Solar PV plant", 2, 2)]:
        n.add("Bus", b, v_nom=132, v_mag_pu_set=1.02 if b == "1" else 1.0, x=x, y=y,
              carrier="AC", v_mag_pu_min=0.95, v_mag_pu_max=1.05)
        n.buses.loc[b, "description"] = desc
    line(n, "L1-2", "1", "2", 25); line(n, "L1-3", "1", "3", 20); line(n, "L2-3", "2", "3", 15)
    n.add("Generator", "thermal", bus="1", control="Slack", p_nom=150, carrier="thermal",
          p_set=0.0, marginal_cost=A.THERMAL_MC)    # slack: p_set must be numeric for n.pf()
    n.add("Generator", "pv", bus="3", control="PQ", p_nom=30, carrier="solar",
          p_set=30 * cf, q_set=0.0, p_max_pu=cf, marginal_cost=0)
    n.add("Load", "city", bus="2", p_set=50 * shape, q_set=20 * shape)
    export(n, "niamey_3bus", f"""
Teaching network inspired by the Niamey context (FICTITIOUS parameters, not NIGELEC data).
132 kV lines (ACSR 240/40: 0.12 + j0.39 ohm/km, 2.9 uS/km), hot-season rating 100 MVA.
24 hourly snapshots of {date} (local time, UTC+1), the day of the annual demand peak:
PV output = 30 MW x real capacity factor (NASA POWER + pvlib),
city demand = 50 MW + 20 MVAr x modelled daily shape (peak = design value).""")


# ============================================================================ CS03
def build_niamey_5bus(date="2023-05-04"):
    cf, shape = day_profiles(date)
    flat = 0.85 + 0.15 * shape / shape.max()          # industry: flatter daily profile
    n = pypsa.Network(name="Niamey area, 5-bus teaching network")
    n.set_snapshots(cf.index)
    add_carriers(n, ["AC", "thermal", "solar"])
    for b, desc, x, y in [("1", "Thermal power station (slack)", 0, 1), ("2", "Substation", 1.5, 2),
                          ("3", "Solar PV plant", 1.5, 0), ("4", "Urban area", 3, 1),
                          ("5", "Remote industrial zone", 5.5, 1)]:
        n.add("Bus", b, v_nom=132, v_mag_pu_set=1.02 if b == "1" else 1.0, x=x, y=y,
              carrier="AC", v_mag_pu_min=0.95, v_mag_pu_max=1.05)
        n.buses.loc[b, "description"] = desc
    for nm, (a, b, km) in {"L1-2": ("1", "2", 30), "L1-3": ("1", "3", 25), "L2-4": ("2", "4", 35),
                           "L3-4": ("3", "4", 30), "L4-5": ("4", "5", 85)}.items():
        line(n, nm, a, b, km)
    n.add("Generator", "thermal", bus="1", control="Slack", p_nom=250, carrier="thermal",
          p_set=0.0, marginal_cost=A.THERMAL_MC)
    n.add("Generator", "pv", bus="3", control="PQ", p_nom=40, carrier="solar",
          p_set=40 * cf, q_set=0.0, p_max_pu=cf)
    n.add("Load", "substation", bus="2", p_set=25 * shape, q_set=8 * shape)
    n.add("Load", "urban", bus="4", p_set=45 * shape, q_set=15 * shape)
    n.add("Load", "industry", bus="5", p_set=35 * flat, q_set=18 * flat)
    export(n, "niamey_5bus", f"""
Five-bus teaching network (FICTITIOUS parameters). Bus 5 is a remote industrial zone at the
end of an 85 km, 132 kV line. Design values (daily peak): substation 25 MW + 8 MVAr,
urban 45 + 15, industry 35 + 18; PV plant 40 MW at bus 3.
24 hourly snapshots of {date} (local time); real PV capacity factor, modelled demand shape
(industrial load flatter: 85 % + 15 % x shape).""")


# ============================================================================ CS04
def build_ieee9():
    n, q = matpower_to_pypsa(read_matpower(DATA / "raw/matpower/case9.m"), "IEEE 9-bus (WSCC)", 345)
    n.generators[["q_min", "q_max"]] = q[["q_min", "q_max"]]
    export(n, "ieee9", """
IEEE / WSCC 9-bus system from the official MATPOWER file case9.m (345 kV, 100 MVA base),
with MATPOWER thermal ratings (rateA) and quadratic generator costs (gencost: c2, c1).
Generator reactive limits stored as custom columns q_min, q_max (MVAr).""")


def ieee14_network():
    mp = read_matpower(DATA / "raw/matpower/case14.m")
    pg = read_matpower(DATA / "raw/matpower/pglib_opf_case14_ieee.m")
    n, q = matpower_to_pypsa(mp, "IEEE 14-bus", 132)
    rate = {f"{int(r.fbus)}-{int(r.tbus)}": r.rateA for _, r in pg["branch"].iterrows()}
    for nm in n.lines.index:
        n.lines.loc[nm, "s_nom"] = rate[nm[1:]]
    for nm in n.transformers.index:                 # re-express p.u. impedance on the new rating
        s_old, s_new = n.transformers.loc[nm, "s_nom"], rate[nm[1:]]
        n.transformers.loc[nm, ["r", "x", "b"]] *= s_new / s_old
        n.transformers.loc[nm, "s_nom"] = s_new
    n.generators[["q_min", "q_max"]] = q[["q_min", "q_max"]]
    n.buses["v_mag_pu_min"], n.buses["v_mag_pu_max"] = 0.94, 1.06
    return n


def build_ieee14():
    export(ieee14_network(), "ieee14", """
IEEE 14-bus system from the official MATPOWER file case14.m (load flow data, 100 MVA base;
nominal voltages are not given in the file, 132 kV is used, results are in p.u.).
Thermal ratings from PGLib-OPF v23.07 (pglib_opf_case14_ieee.m, IEEE PES benchmark library).
Generator reactive limits stored as custom columns q_min, q_max (MVAr).""")


# ============================================================================ CS06
def build_ieee14_pv_day(date="2023-03-16"):
    cf, shape = day_profiles(date)
    n = ieee14_network()
    base_p, base_q = n.loads.p_set.copy(), n.loads.q_set.copy()
    n.set_snapshots(cf.index)
    add_carriers(n, ["solar", "battery"])
    for ld in n.loads.index:                      # IEEE loads = evening peak, scaled by the daily shape
        n.loads_t.p_set[ld] = base_p[ld] * shape.values
        n.loads_t.q_set[ld] = base_q[ld] * shape.values
    n.add("Generator", "pv14", bus="14", control="PQ", p_nom=100, carrier="solar",
          p_set=100 * cf, q_set=0.0, p_max_pu=cf)
    n.add("StorageUnit", "battery14", bus="14", p_nom=50, max_hours=4, carrier="battery",
          efficiency_store=A.BAT_EFF, efficiency_dispatch=A.BAT_EFF, p_set=0.0)
    export(n, "ieee14_pv_day", f"""
IEEE 14-bus (as in `ieee14`) over 24 hours of {date}, the clearest day of Q1 2023 in Niamey.
IEEE loads are taken as the evening peak and scaled by the modelled daily shape.
A 100 MW PV plant (real capacity factor) and a 50 MW / 200 MWh battery are connected at bus 14,
the weakest node of the system.""")


# ============================================================================ CS07
def annual_local(series_utc: pd.Series) -> pd.Series:
    """UTC year -> the same 8760 values on local (UTC+1) timestamps of the same year.
    The first local hour (00:00, 1 Jan) takes the last UTC hour (wrap-around, at night)."""
    idx = pd.date_range("2023-01-01", periods=len(series_utc), freq="h")
    return pd.Series(np.roll(series_utc.values, 1), index=idx, name=series_utc.name)


def build_niamey_grid_2023():
    cf = annual_local(pv_profile("niamey"))
    shape = annual_local(city_load(weather("niamey").temp_air, 1.0))
    flat = 0.85 + 0.15 * shape
    n = pypsa.Network(name="Niamey area grid, hourly year 2023")
    n.set_snapshots(cf.index)
    add_carriers(n, ["AC", "thermal", "import", "solar", "battery"])
    for b, desc, x, y in [("1", "Power station and interconnector", 0, 1), ("2", "Substation", 1.5, 2),
                          ("3", "Solar PV site", 1.5, 0), ("4", "Urban area", 3, 1),
                          ("5", "Remote industrial zone", 5.5, 1)]:
        n.add("Bus", b, v_nom=132, x=x, y=y, carrier="AC", v_mag_pu_set=1.02 if b == "1" else 1.0)
        n.buses.loc[b, "description"] = desc
    for nm, (a, b, km) in {"L1-2": ("1", "2", 30), "L1-3": ("1", "3", 25), "L2-4": ("2", "4", 35),
                           "L3-4": ("3", "4", 30), "L4-5": ("4", "5", 85)}.items():
        line(n, nm, a, b, km)
    n.lines["s_max_pu"] = 0.9                       # keep 10 % of the rating for reactive flows
    n.add("ShuntImpedance", "cap5", bus="5", b=15 / 132 ** 2)   # 15 MVAr bank decided in CS03
    n.add("Generator", "thermal", bus="1", p_nom=200, carrier="thermal", marginal_cost=A.THERMAL_MC)
    n.add("Generator", "import", bus="1", p_nom=80, carrier="import", marginal_cost=A.IMPORT_MC)
    n.add("Generator", "pv", bus="3", p_nom_extendable=True, carrier="solar",
          p_max_pu=cf, capital_cost=A.pv_capital_cost(), marginal_cost=0.0)
    n.add("StorageUnit", "battery", bus="3", p_nom_extendable=True, max_hours=A.BAT_HOURS,
          carrier="battery", capital_cost=A.battery_capital_cost(), cyclic_state_of_charge=True,
          efficiency_store=A.BAT_EFF, efficiency_dispatch=A.BAT_EFF)
    n.add("Load", "substation", bus="2", p_set=25 * shape, q_set=8 * shape)
    n.add("Load", "urban", bus="4", p_set=45 * shape, q_set=15 * shape)
    n.add("Load", "industry", bus="5", p_set=35 * flat, q_set=18 * flat)
    export(n, "niamey_grid_2023", """
Hourly year 2023 (8760 local hours, UTC+1) on the five-bus Niamey-area network (FICTITIOUS
grid parameters), with the 15 MVAr capacitor bank chosen in CS03.
Supply at bus 1: thermal plant (200 MW, HFO/diesel) and an import interconnector (80 MW).
PV (bus 3) and a 4-hour battery (bus 3) are extendable: PyPSA chooses their size.
Real weather: NASA POWER hourly irradiance and temperature for Niamey (13.51 N, 2.11 E);
PV capacity factor from pvlib (or Renewables.ninja when its CSV is present).
Demand: temperature-driven model (see src/pscs/demand.py), peak 105 MW.""")


# ============================================================================ CS08
def build_agadez_2023():
    cf = annual_local(pv_profile("agadez"))
    load = annual_local(city_load(weather("agadez").temp_air, 2.0))
    n = pypsa.Network(name="Agadez region off-grid mini-grid, hourly year 2023")
    n.set_snapshots(cf.index)
    add_carriers(n, ["AC", "diesel", "solar", "battery"])
    n.add("Bus", "minigrid", v_nom=0.4, carrier="AC")
    n.add("Load", "town", bus="minigrid", p_set=load)
    n.add("Generator", "diesel", bus="minigrid", p_nom=2.5, carrier="diesel",
          marginal_cost=A.diesel_marginal_cost())
    pv_cc = A.pv_capital_cost(capex=A.MG_PV_CAPEX)
    bat_cc = A.battery_capital_cost(e=A.MG_BAT_CAPEX_E, p=A.MG_BAT_CAPEX_P)
    n.add("Generator", "pv", bus="minigrid", p_nom_extendable=True, carrier="solar",
          p_max_pu=cf, capital_cost=pv_cc)
    n.add("StorageUnit", "battery", bus="minigrid", p_nom_extendable=True, max_hours=A.BAT_HOURS,
          carrier="battery", capital_cost=bat_cc, cyclic_state_of_charge=True,
          efficiency_store=A.BAT_EFF, efficiency_dispatch=A.BAT_EFF)
    export(n, "agadez_minigrid_2023", """
Off-grid mini-grid for a town in the Agadez region (single bus, 0.4 kV), hourly year 2023.
Peak demand 2 MW (temperature-driven model with real Agadez temperatures).
Existing diesel genset 2.5 MW; PV and a 4-hour battery are extendable.
Real weather: NASA POWER hourly data for Agadez (16.97 N, 7.99 E).""")


if __name__ == "__main__":
    print("Building PyPSA datasets in", OUT)
    build_ex5()
    build_niamey_3bus()
    build_niamey_5bus()
    build_ieee9()
    build_ieee14()
    build_ieee14_pv_day()
    build_niamey_grid_2023()
    build_agadez_2023()
