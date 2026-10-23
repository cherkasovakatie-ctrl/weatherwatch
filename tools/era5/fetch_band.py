"""Fetch ERA5 zonal wind for the equatorial band and reduce it to daily band means (runs in GitHub Actions).

Source: Copernicus Climate Data Store (CDS), ERA5 hourly data on pressure levels and on single levels
(Hersbach et al. 2020, doi:10.1002/qj.3803). Licence: Copernicus licence (free use with attribution).
Request per year: u at 1000/850/200 hPa and 10 m u, 00/06/12/18 UTC, 10°S–10°N, regridded by CDS to 2.5° (same grid as
NCEP/NCAR R1, so results compare like for like). Daily value = mean of the four synoptic times (UTC days).
Output: data/papers/1982/era5_band_1979_2001.npz with int16 arrays (m/s × 10), shape (days, 144), longitudes 0..357.5°E:
  u10_eq, u1000_eq  5°S–5°N cos-weighted mean;  u850, u200  10°S–10°N cos-weighted mean.
Needs the CDSAPI_KEY secret (personal access token from the CDS profile page) and accepted ERA5 licences.
Run: python3 tools/era5/fetch_band.py [first_year last_year]
"""
import datetime as dt
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cdsapi
import numpy as np
from netCDF4 import Dataset, num2date

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'era5_cache'; CACHE.mkdir(exist_ok=True)
Y0, Y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1979, 2001)
COMMON = dict(product_type=['reanalysis'], month=[f'{m:02d}' for m in range(1, 13)], day=[f'{d:02d}' for d in range(1, 32)],
              time=['00:00', '06:00', '12:00', '18:00'], area=[10, -180, -10, 180], grid=['2.5', '2.5'],
              data_format='netcdf', download_format='unarchived')
LAT = 10 - np.arange(9) * 2.5
W = np.cos(np.deg2rad(LAT))


def retrieve(kind, y):
    target = CACHE / f'{kind}_{y}.nc'
    if target.exists() and target.stat().st_size > 1e5:
        return target
    if kind == 'pl':
        ds, req = 'reanalysis-era5-pressure-levels', dict(COMMON, variable=['u_component_of_wind'], pressure_level=['200', '850', '1000'], year=[str(y)])
    else:
        ds, req = 'reanalysis-era5-single-levels', dict(COMMON, variable=['10m_u_component_of_wind'], year=[str(y)])
    for attempt in range(4):
        try:
            cdsapi.Client(quiet=True, progress=False).retrieve(ds, req, str(target)); print('got', target.name, flush=True); return target
        except Exception as e:  # queue hiccups: back off and retry
            print(f'retry {attempt} {kind} {y}: {str(e)[:300]}', flush=True); time.sleep(60 * (attempt + 1))
    raise RuntimeError(f'failed {kind} {y}')


def read(path, var):
    with Dataset(path) as nc:
        tname = 'valid_time' if 'valid_time' in nc.variables else 'time'
        t = num2date(nc[tname][:], nc[tname].units, only_use_cftime_datetimes=False)
        lat = np.round(nc['latitude'][:].astype(float), 2); lon = np.round(nc['longitude'][:].astype(float), 2) % 360
        a = np.asarray(nc[var][:], dtype=np.float32)
        plev = nc['pressure_level'][:].astype(int).tolist() if 'pressure_level' in nc.variables else None
    assert np.allclose(lat, LAT), lat
    order = np.argsort(lon); assert np.allclose(lon[order], np.arange(144) * 2.5), lon
    a = a[..., order]
    days = np.array([dt.date(x.year, x.month, x.day) for x in t])
    return days, a, plev


def daily(days, a):
    u = sorted(set(days)); return u, np.stack([a[days == d].mean(0) for d in u])


def band(a, j0, j1): return (a[:, j0:j1] * W[j0:j1, None]).sum(1) / W[j0:j1].sum()


def year(y):
    d, pl, lev = read(retrieve('pl', y), 'u'); dd, plm = daily(d, pl)
    d2, sl, _ = read(retrieve('sl', y), 'u10'); dd2, slm = daily(d2, sl)
    assert dd == dd2 and len(dd) == (dt.date(y + 1, 1, 1) - dt.date(y, 1, 1)).days, (y, len(dd))
    L = {p: lev.index(p) for p in (1000, 850, 200)}
    return dict(u10_eq=band(slm, 2, 7), u1000_eq=band(plm[:, L[1000]], 2, 7), u850=band(plm[:, L[850]], 0, 9), u200=band(plm[:, L[200]], 0, 9))


with ThreadPoolExecutor(3) as ex:
    R = list(ex.map(year, range(Y0, Y1 + 1)))
out = {k: np.round(np.concatenate([r[k] for r in R]) * 10).astype(np.int16) for k in R[0]}
out['start'] = np.array(f'{Y0}-01-01'); out['lon'] = np.arange(144) * 2.5
dest = ROOT / 'data' / 'papers' / '1982' / f'era5_band_{Y0}_{Y1}.npz'
np.savez_compressed(dest, **out)
print('wrote', dest, {k: v.shape for k, v in out.items()}, os.path.getsize(dest), 'bytes')
