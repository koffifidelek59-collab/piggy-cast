"""pscs: shared tools for the PyPSA power-system case studies.

Modules
-------
matpower  : read MATPOWER case files and convert them to PyPSA networks
newton    : Newton's method and a Newton-Raphson load flow written from scratch
kpi       : AC load-flow helpers, operational indicators, reactive-limit enforcement
solar     : weather loading (NASA POWER / Renewables.ninja) and PV capacity factors
demand    : temperature-driven electricity demand profile
plotting  : one consistent, colour-blind-safe chart style for every figure
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repository folder pypsa-case-studies/
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIG = RESULTS / "figures"
TAB = RESULTS / "tables"
for _p in (FIG, TAB):
    _p.mkdir(parents=True, exist_ok=True)


def setup():
    """Quiet logs, apply the chart style, return (DATA, FIG, TAB)."""
    import logging
    import warnings

    import pandas as pd

    from .plotting import use_style
    warnings.filterwarnings("ignore")
    logging.disable(logging.CRITICAL)
    pd.set_option("display.precision", 4)
    pd.set_option("display.width", 120)
    use_style()
    return DATA, FIG, TAB


def save_summary(name: str, values: dict):
    """Store the headline numbers of a case study (read by the report and the slides)."""
    import json

    import numpy as np

    def conv(v):
        if isinstance(v, (np.floating, np.integer)):
            return v.item()
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [conv(x) for x in v]
        return v
    (TAB / f"{name}_summary.json").write_text(json.dumps(conv(values), indent=2))
