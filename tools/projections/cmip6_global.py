"""CMIP6 global mean near-surface air temperature, historical + SSP1-2.6/SSP2-4.5/SSP5-8.5 (runs in GitHub Actions).

Source: Copernicus CDS dataset 'projections-cmip6' (monthly 'near_surface_air_temperature', single levels), one request
per model and experiment, as in the C3S training notebook. Each file is reduced at once to an area-weighted (cos latitude)
global annual mean in °C and deleted, so only the small table is kept.
Output: data/projections/cmip6_tas_global_annual.csv (model, experiment, year, tas_c, member) and a run log.
Rules (Projections guide tab): models are compared as anomalies against each model's own 1850-1900 mean.
Run: python tools/projections/cmip6_global.py
"""
import csv
import datetime as dt
import shutil
import sys
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cdsapi
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data' / 'projections'; OUT.mkdir(parents=True, exist_ok=True)
CSV = OUT / 'cmip6_tas_global_annual.csv'; LOG = OUT / 'cmip6_run_log.txt'
MODELS = ['access_cm2', 'access_esm1_5', 'canesm5', 'cesm2', 'cmcc_esm2', 'cnrm_cm6_1', 'cnrm_esm2_1', 'ec_earth3',
          'ec_earth3_veg', 'fgoals_g3', 'gfdl_esm4', 'hadgem3_gc31_ll', 'inm_cm4_8', 'inm_cm5_0', 'ipsl_cm6a_lr',
          'kace_1_0_g', 'miroc6', 'miroc_es2l', 'mpi_esm1_2_lr', 'mri_esm2_0', 'nesm3', 'noresm2_lm', 'taiesm1', 'ukesm1_0_ll']
EXPS = {'historical': (1850, 2014), 'ssp126': (2015, 2100), 'ssp245': (2015, 2100), 'ssp585': (2015, 2100)}
done = set()
if CSV.exists():
    for r in csv.DictReader(open(CSV)): done.add((r['model'], r['experiment']))
lines = []


def log(msg):
    s = f'{dt.datetime.utcnow():%Y-%m-%d %H:%M} {msg}'; print(s, flush=True); lines.append(s)
    LOG.write_text('\n'.join(lines) + '\n')


def reduce(nc):
    ds = xr.open_dataset(nc, use_cftime=True)
    da = ds['tas']
    lat = next(c for c in ('lat', 'latitude') if c in da.dims); lon = next(c for c in ('lon', 'longitude') if c in da.dims)
    g = da.weighted(np.cos(np.deg2rad(da[lat]))).mean([lat, lon])
    yr = g.groupby('time.year').mean() - 273.15
    n = g.groupby('time.year').count()
    member = ds.attrs.get('variant_label', '')
    return [(int(y), float(v)) for y, v, k in zip(yr.year.values, yr.values, n.values) if k == 12], member


def one(model, exp):
    if (model, exp) in done: return model, exp, 'already done', []
    y0, y1 = EXPS[exp]
    req = {'temporal_resolution': 'monthly', 'experiment': exp, 'variable': 'near_surface_air_temperature', 'level': 'single_levels',
           'model': model, 'year': [str(y) for y in range(y0, y1 + 1)], 'month': [f'{m:02d}' for m in range(1, 13)]}
    tmp = Path(tempfile.mkdtemp())
    try:
        for attempt in range(3):
            try:
                cdsapi.Client(quiet=True, progress=False).retrieve('projections-cmip6', req, str(tmp / 'd.zip')); break
            except Exception as e:
                msg = str(e)
                if 'not available' in msg.lower() or 'no data' in msg.lower() or 'invalid' in msg.lower():
                    return model, exp, 'not available: ' + msg[:200], []
                if attempt == 2: return model, exp, 'failed: ' + msg[:200], []
                time.sleep(60 * (attempt + 1))
        with zipfile.ZipFile(tmp / 'd.zip') as z: z.extractall(tmp)
        rows, member = [], ''
        for nc in sorted(tmp.glob('tas*.nc')):
            r, member = reduce(nc); rows += r
        rows = sorted(dict(rows).items())
        return model, exp, f'ok {len(rows)} years {rows[0][0]}-{rows[-1][0]} member {member}', [(model, exp, y, round(v, 4), member) for y, v in rows]
    except Exception as e:
        return model, exp, 'error: ' + str(e)[:200], []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


new = not CSV.exists()
fh = open(CSV, 'a', newline=''); w = csv.writer(fh, lineterminator='\n')
if new: w.writerow(['model', 'experiment', 'year', 'tas_c', 'member'])
jobs = [(m, e) for m in MODELS for e in EXPS]
with ThreadPoolExecutor(4) as ex:
    for model, exp, status, rows in ex.map(lambda a: one(*a), jobs):
        log(f'{model} {exp}: {status}')
        for r in rows: w.writerow(r)
        fh.flush()
fh.close()
log('finished')
