"""GPCP v2.3 monthly precipitation (NOAA PSL), area-weighted regional means 1979-present, mm/day.
Writes raw/papers/gpcp/regions_monthly.csv and a short log. Regions are boxes on the 2.5-degree grid (land and ocean)."""
import os, urllib.request, numpy as np, xarray as xr
URL = 'https://downloads.psl.noaa.gov/Datasets/gpcp/precip.mon.mean.nc'
OUT = 'raw/papers/gpcp'; os.makedirs(OUT, exist_ok=True)
REG = {  # name: (lat S, lat N, lon W, lon E) in degrees east
    'indonesia': (-10, 5, 95, 145),
    'peru_ecuador_coast': (-12.5, 2.5, 275, 282.5),
    'california': (32.5, 42.5, 235, 245),
    'central_eq_pacific': (-5, 5, 170, 220),
    'southern_africa': (-35, -15, 15, 40),
    'eastern_australia': (-40, -10, 140, 155),
    'east_africa': (-5, 5, 35, 50),
    'india': (8, 30, 70, 90),
}
urllib.request.urlretrieve(URL, '/tmp/gpcp.nc')
ds = xr.open_dataset('/tmp/gpcp.nc'); p = ds['precip']
w = np.cos(np.deg2rad(p['lat']))
cols = {}
for k, (s, n, a, b) in REG.items():
    sub = p.sel(lat=slice(min(s, n), max(s, n)) if p.lat[0] < p.lat[-1] else slice(max(s, n), min(s, n)), lon=slice(a, b))
    cols[k] = sub.weighted(w.sel(lat=sub.lat)).mean(('lat', 'lon')).values
t = p['time'].values
with open(f'{OUT}/regions_monthly.csv', 'w') as f:
    f.write('month,' + ','.join(REG) + '\n')
    for i, tt in enumerate(t):
        f.write(str(tt)[:7] + ',' + ','.join(f'{cols[k][i]:.3f}' for k in REG) + '\n')
open(f'{OUT}/log.txt', 'w').write(f'{URL}\n{ds.attrs.get("title", "")}\n{ds.attrs.get("version", "")}\nfirst {str(t[0])[:10]} last {str(t[-1])[:10]}\nboxes {REG}\n')
print('ok', str(t[-1])[:10])
