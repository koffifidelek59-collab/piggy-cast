"""Temperature-driven hourly electricity demand for a Sahelian city.

No public hourly load series of the Niamey grid is available, so the demand
profile is MODELLED (an explicit assumption, stated in every result):

    D(t) = k * s(h) * [1 + beta * max(T24(t) - T_ref, 0)]

s(h)   : normalised daily shape in local time: low at dawn, daytime plateau
         (offices, commerce, cooling), evening peak 19:00-21:00 (lighting,
         households, cooling). Typical of West African urban systems.
T24(t) : 24-hour rolling mean of the real NASA POWER air temperature
         (buildings react to sustained heat, not to a single hour).
beta   : cooling sensitivity, 2.5 % per degC above T_ref = 25 degC.
k      : scaling so that the annual peak equals `peak_mw`.

The real temperature drives the seasonality: demand peaks in the hot season
(April-May) and is lowest in the cool, dry Harmattan months (December-January).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SHAPE = np.array([0.70, 0.66, 0.63, 0.61, 0.60, 0.62, 0.66, 0.72, 0.78, 0.83, 0.87, 0.90,
                  0.92, 0.93, 0.93, 0.92, 0.91, 0.92, 0.96, 1.00, 1.00, 0.97, 0.88, 0.78])


def city_load(temp_air_utc: pd.Series, peak_mw: float, utc_offset: int = 1,
              beta: float = 0.025, t_ref: float = 25.0) -> pd.Series:
    """Hourly demand in MW, indexed like the input temperature series (UTC)."""
    local_hour = (temp_air_utc.index + pd.Timedelta(hours=utc_offset)).hour
    t24 = temp_air_utc.rolling(24, min_periods=1).mean()
    raw = SHAPE[local_hour] * (1 + beta * (t24 - t_ref).clip(lower=0))
    return (peak_mw * raw / raw.max()).rename("demand (MW)")
