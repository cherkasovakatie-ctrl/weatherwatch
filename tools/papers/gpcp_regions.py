"""GPCP v2.3 monthly precipitation (NOAA PSL), area-weighted regional means 1979-present, mm/day.
Writes raw/papers/gpcp/regions_monthly.csv and a short log. Regions are boxes on the 2.5-degree grid (land and ocean)."""
import os, urllib.request, numpy as np, xarray as xr, cftime

def months(ds, tname='time'):
    t = ds[tname]; d = cftime.num2date(t.values, t.attrs['units'], t.attrs.get('calendar', 'standard'))
    return [f'{x.year}-{x.month:02d}' for x in d]

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
ds = xr.open_dataset('/tmp/gpcp.nc', decode_times=False); p = ds['precip']
w = np.cos(np.deg2rad(p['lat']))
cols = {}
for k, (s, n, a, b) in REG.items():
    sub = p.sel(lat=slice(min(s, n), max(s, n)) if p.lat[0] < p.lat[-1] else slice(max(s, n), min(s, n)), lon=slice(a, b))
    cols[k] = sub.weighted(w.sel(lat=sub.lat)).mean(('lat', 'lon')).values
t = months(ds)
with open(f'{OUT}/regions_monthly.csv', 'w') as f:
    f.write('month,' + ','.join(REG) + '\n')
    for i, tt in enumerate(t):
        f.write(tt + ',' + ','.join(f'{cols[k][i]:.3f}' for k in REG) + '\n')
open(f'{OUT}/log.txt', 'w').write(f'{URL}\n{ds.attrs.get("title", "")}\n{ds.attrs.get("version", "")}\nfirst {t[0]} last {t[-1]}\nboxes {REG}\n')
print('gpcp ok', t[-1])

# NOAA STAR mean layer temperature v5 (TLT, TMT): global (82.5S-82.5N) and tropical (20S-20N) area-weighted means, K anomalies as stored
MLT = 'https://www.ncei.noaa.gov/data/mean-layer-temperature-noaa/access/'
import re
idx = urllib.request.urlopen(urllib.request.Request(MLT, headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=120).read().decode()
rows = {}; info = []
for layer in ('TLT', 'TMT'):
    name = sorted(set(re.findall(r'Mean-Layer-Temperature-NOAA_v05r00_%s_S\d{6}_E\d{6}_C\d{8}\.nc' % layer, idx)))[-1]
    urllib.request.urlretrieve(MLT + name, f'/tmp/{layer}.nc')
    d = xr.open_dataset(f'/tmp/{layer}.nc', decode_times=False)
    v = [k for k, x in d.data_vars.items() if x.ndim == 3][0]; x = d[v]
    lat = [c for c in x.dims if 'lat' in c.lower()][0]; lon = [c for c in x.dims if 'lon' in c.lower()][0]; tn = x.dims[0]
    wl = np.cos(np.deg2rad(d[lat]))
    for tag, (a, b) in {'global': (-82.5, 82.5), 'tropics': (-20, 20)}.items():
        sub = x.where((d[lat] >= a) & (d[lat] <= b))
        ser = sub.weighted(wl.fillna(0)).mean((lat, lon)).values
        for m, val in zip(months(d, tn), ser):
            rows.setdefault(m, {})[f'{layer.lower()}_{tag}'] = val
    info.append(f'{name} var={v} units={x.attrs.get("units")} long_name={x.attrs.get("long_name")} dims={x.dims}')
keys = ['tlt_global', 'tlt_tropics', 'tmt_global', 'tmt_tropics']
with open(f'{OUT}/msu_monthly.csv', 'w') as f:
    f.write('month,' + ','.join(keys) + '\n')
    for m in sorted(rows):
        f.write(m + ',' + ','.join('' if rows[m].get(k) is None or np.isnan(rows[m][k]) else f'{rows[m][k]:.3f}' for k in keys) + '\n')
open(f'{OUT}/msu_log.txt', 'w').write('\n'.join(info) + '\n')
print('msu ok', max(rows))
