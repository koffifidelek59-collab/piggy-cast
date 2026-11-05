# Renewables.ninja PV profiles

Place Renewables.ninja PV files here as `<site>_pv_<year>.csv` (sites: `niamey`, `agadez`),
or download them with:

```bash
python scripts/fetch_renewables_ninja.py --token YOUR_TOKEN
```

When a file is present, `pscs.solar.pv_profile()` uses it instead of the NASA POWER + pvlib
series, and every notebook reports the data source it used. Re-run `python scripts/run_all.py`
to regenerate datasets, notebooks, figures and tables with the ninja profiles.

Settings expected (same as the NASA POWER series): capacity 1 kW, system loss 0.1, no tracking,
tilt = latitude (14 degrees for Niamey, 17 for Agadez), azimuth 180 (south), dataset MERRA-2.

Why the folder is empty: the Renewables.ninja API was not reachable from the environment in
which this study was computed (network policy), so the PV profiles were computed from NASA
POWER hourly irradiance with pvlib, using the same model chain as Renewables.ninja.
