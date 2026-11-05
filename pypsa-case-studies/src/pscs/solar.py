"""Hourly PV capacity factors from real weather data.

Two interchangeable sources, same output (kW of AC output per kWp installed):

1. Renewables.ninja  (preferred when available)
   Download CSVs with `scripts/fetch_renewables_ninja.py` (free API token) or from
   the website, and save them as data/raw/renewables_ninja/<site>_pv_<year>.csv.
   The ninja file is read as-is: `electricity` divided by the installed capacity.

2. NASA POWER + pvlib  (used when no ninja file is present)
   NASA POWER gives satellite-derived hourly irradiance (CERES SYN1deg: GHI, DNI,
   DHI) and MERRA-2 temperature / wind. We convert it to PV output with the same
   chain of physical models that Renewables.ninja (GSEE) applies:
     solar position -> plane-of-array irradiance (Hay-Davies transposition)
     -> cell temperature (Faiman) -> PVWatts DC model (-0.4 %/degC)
     -> system losses (10 %, the ninja default) -> AC capacity factor.

Every function returns a pandas Series indexed by UTC timestamps (hour start)
and named after its data source, so results always state where they came from.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pvlib

from . import DATA

SITES = {
    # name: (latitude, longitude, altitude m, UTC offset h)
    "niamey": (13.5137, 2.1098, 207.0, 1),
    "agadez": (16.9742, 7.9865, 520.0, 1),
}


def load_nasa_power(path) -> pd.DataFrame:
    """Read a NASA POWER hourly CSV (header block + YEAR,MO,DY,HR,...) into a tidy frame."""
    lines = Path(path).read_text().splitlines()
    start = lines.index("-END HEADER-") + 1
    df = pd.read_csv(path, skiprows=start)
    idx = pd.to_datetime(dict(year=df.YEAR, month=df.MO, day=df.DY, hour=df.HR), utc=True)
    out = pd.DataFrame({
        "ghi": df.ALLSKY_SFC_SW_DWN, "dni": df.ALLSKY_SFC_SW_DNI, "dhi": df.ALLSKY_SFC_SW_DIFF,
        "temp_air": df.T2M, "wind_speed": df.WS10M,
    }).set_axis(idx).replace(-999, np.nan)
    return out.interpolate(limit_direction="both")


def pv_from_weather(w: pd.DataFrame, lat: float, lon: float, alt: float = 0.0,
                    tilt: float | None = None, azimuth: float = 180.0,
                    system_loss: float = 0.10, gamma: float = -0.004) -> pd.Series:
    """AC capacity factor (kW per kWp) of a fixed, south-facing PV array."""
    tilt = round(abs(lat)) if tilt is None else tilt          # rule of thumb: tilt ~ latitude
    t_mid = w.index + pd.Timedelta(minutes=30)               # hourly values are hour averages
    sp = pvlib.solarposition.get_solarposition(t_mid, lat, lon, altitude=alt)
    dni_extra = pvlib.irradiance.get_extra_radiation(t_mid)
    poa = pvlib.irradiance.get_total_irradiance(
        tilt, azimuth, sp.apparent_zenith.values, sp.azimuth.values,
        w.dni.values, w.ghi.values, w.dhi.values, dni_extra=dni_extra.values,
        model="haydavies", albedo=0.25)
    g = np.nan_to_num(np.asarray(poa["poa_global"], float)).clip(min=0)
    t_cell = pvlib.temperature.faiman(g, w.temp_air.values, w.wind_speed.values)
    p_dc = pvlib.pvsystem.pvwatts_dc(g, t_cell, pdc0=1.0, gamma_pdc=gamma)
    cf = (np.asarray(p_dc) * (1 - system_loss)).clip(0, 1)
    return pd.Series(cf, index=w.index, name="NASA POWER + pvlib")


def load_renewables_ninja(path, capacity_kw: float = 1.0) -> pd.Series:
    """Read a Renewables.ninja PV CSV (comment lines start with '#')."""
    df = pd.read_csv(path, comment="#")
    idx = pd.to_datetime(df["time"], utc=True)
    return pd.Series(df["electricity"].values / capacity_kw, index=idx, name="Renewables.ninja")


def pv_profile(site: str, year: int = 2023) -> pd.Series:
    """Hourly PV capacity factor for a site: Renewables.ninja if downloaded, else NASA POWER."""
    ninja = DATA / "raw" / "renewables_ninja" / f"{site}_pv_{year}.csv"
    if ninja.exists():
        return load_renewables_ninja(ninja)
    lat, lon, alt, _ = SITES[site]
    w = load_nasa_power(DATA / "raw" / "nasa_power" / f"{site}_{year}_hourly.csv")
    return pv_from_weather(w, lat, lon, alt)


def weather(site: str, year: int = 2023) -> pd.DataFrame:
    return load_nasa_power(DATA / "raw" / "nasa_power" / f"{site}_{year}_hourly.csv")


def to_local(s, site: str):
    """Shift a UTC-indexed series/frame to local (naive) time, e.g. UTC+1 for Niger."""
    off = SITES[site][3]
    out = s.copy()
    out.index = (s.index + pd.Timedelta(hours=off)).tz_localize(None)
    return out
