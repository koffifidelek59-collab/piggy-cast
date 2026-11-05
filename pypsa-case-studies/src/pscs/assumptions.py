"""Techno-economic assumptions shared by the case studies (USD 2023).

Every number here is an ASSUMPTION for teaching and screening purposes, chosen
within ranges published by the sources quoted. Change them here and re-run the
notebooks: nothing else needs editing.

Sources used to choose the ranges
---------------------------------
- IRENA (2024), Renewable Power Generation Costs in 2023: utility-scale PV
  global weighted-average installed cost about USD 758/kW in 2023; costs in
  Africa are usually higher (logistics, risk premium).
- NREL Annual Technology Baseline (ATB) and BNEF battery price surveys:
  utility-scale 4-hour Li-ion systems in the range USD 250-400/kWh installed.
- Diesel / HFO generation: fuel use 0.25-0.30 l/kWh; emission factors
  0.65-0.75 tCO2/MWh (IPCC 2006 default fuel factors).
"""

WACC = 0.08                      # real weighted average cost of capital


def annuity(lifetime: float, rate: float = WACC) -> float:
    """Capital recovery factor: converts an investment into an equal yearly payment."""
    return rate / (1 - (1 + rate) ** -lifetime)


# ---------------------------------------------------------------- Niamey grid (CS07)
PV_CAPEX = 800.0                 # USD/kW (AC), utility scale, West Africa
PV_FOM = 0.015                   # share of CAPEX per year
PV_LIFE = 25
BAT_HOURS = 4.0                  # energy-to-power ratio of the battery (h)
BAT_CAPEX_E = 250.0              # USD/kWh of storage capacity
BAT_CAPEX_P = 150.0              # USD/kW of converter capacity
BAT_FOM = 0.02
BAT_LIFE = 15
BAT_EFF = 0.95                   # one-way efficiency (round trip about 90 %)
THERMAL_MC = 180.0               # USD/MWh, HFO/diesel engines (fuel + variable O&M)
THERMAL_CO2 = 0.70               # tCO2/MWh
IMPORT_MC = 70.0                 # USD/MWh, interconnector import tariff (illustrative)


def pv_capital_cost(capex=PV_CAPEX, fom=PV_FOM, life=PV_LIFE) -> float:
    """Annualised PV cost in USD per MW per year (what PyPSA calls capital_cost)."""
    return 1000 * capex * (annuity(life) + fom)


def battery_capital_cost(hours=BAT_HOURS, e=BAT_CAPEX_E, p=BAT_CAPEX_P,
                         fom=BAT_FOM, life=BAT_LIFE) -> float:
    """Annualised cost of 1 MW of battery with `hours` of storage (USD/MW/year)."""
    capex_per_kw = hours * e + p
    return 1000 * capex_per_kw * (annuity(life) + fom)


# --------------------------------------------------------- Agadez mini-grid (CS08)
MG_PV_CAPEX = 1000.0             # USD/kW, small remote system (transport, smaller scale)
MG_BAT_CAPEX_E = 350.0           # USD/kWh
MG_BAT_CAPEX_P = 200.0           # USD/kW
DIESEL_PRICE = 1.00              # USD/litre delivered to site (sensitivity 0.8-1.4)
DIESEL_SFC = 0.28                # litre/kWh, specific fuel consumption at typical load
DIESEL_VOM = 20.0                # USD/MWh variable O&M
DIESEL_CO2 = 0.74                # tCO2/MWh (2.64 kgCO2/litre x 0.28 l/kWh)


def diesel_marginal_cost(price=DIESEL_PRICE) -> float:
    return price * DIESEL_SFC * 1000 + DIESEL_VOM
