"""Download hourly PV capacity factors from Renewables.ninja for the case-study sites.

Renewables.ninja (https://www.renewables.ninja) is free for research and teaching but needs
an API token: create an account, open your profile page, copy the token, then run

    python scripts/fetch_renewables_ninja.py --token YOUR_TOKEN
    python scripts/run_all.py            # every notebook now uses the ninja profiles

The files are saved as data/raw/renewables_ninja/<site>_pv_<year>.csv. `pscs.solar.pv_profile`
uses them automatically instead of the NASA POWER + pvlib series. The PV settings match those
used with NASA POWER: fixed array, tilt = latitude, facing south, 10 % system losses.
"""
import argparse
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pscs.solar import SITES                                               # noqa: E402

API = "https://www.renewables.ninja/api/data/pv"


def fetch(site: str, year: int, token: str) -> Path:
    lat, lon, _, _ = SITES[site]
    params = {
        "lat": lat, "lon": lon,
        "date_from": f"{year}-01-01", "date_to": f"{year}-12-31",
        "dataset": "merra2", "capacity": 1.0, "system_loss": 0.1,
        "tracking": 0, "tilt": round(abs(lat)), "azim": 180,
        "format": "csv", "header": "true", "local_time": "true",
    }
    r = requests.get(API, params=params, headers={"Authorization": f"Token {token}"}, timeout=120)
    r.raise_for_status()
    out = ROOT / "data" / "raw" / "renewables_ninja" / f"{site}_pv_{year}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(r.text)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--token", required=True, help="your Renewables.ninja API token")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--sites", nargs="+", default=list(SITES))
    a = ap.parse_args()
    for s in a.sites:
        print("saved", fetch(s, a.year, a.token))
        time.sleep(2)                      # stay well below the API rate limit
