"""Environment along 2026 tropical-cyclone tracks (IBTrACS 6-hourly fixes, NA/EP/WP storms reaching 64 kt).
SST: NOAA OISST v2.1 daily (PSL), value and anomaly (1991-2020) at the fix 3 days before arrival (pre-storm) and the change from 3 days
before to 3 days after (cold wake). Shear: NCEP/NCAR R1 daily, 200-850 hPa vector difference of winds averaged over a 200-800 km annulus.
Mid-level humidity: R1 600 hPa relative humidity over the same annulus. Writes raw/papers/tc_env/env_2026.csv and log."""
import csv, datetime as dt, math, os, urllib.request
import numpy as np, xarray as xr
OUT = 'raw/papers/tc_env'; os.makedirs(OUT, exist_ok=True)
PSL = 'https://downloads.psl.noaa.gov/Datasets/'
FILES = {'sst': 'noaa.oisst.v2.highres/sst.day.mean.2026.nc', 'ssta': 'noaa.oisst.v2.highres/sst.day.anom.2026.nc',
         'u': 'ncep.reanalysis.dailyavgs/pressure/uwnd.2026.nc', 'v': 'ncep.reanalysis.dailyavgs/pressure/vwnd.2026.nc',
         'rh': 'ncep.reanalysis.dailyavgs/pressure/rhum.2026.nc'}
log = []
for k, f in FILES.items():
    dst = f'/tmp/{k}.nc'
    urllib.request.urlretrieve(PSL + f, dst); log.append(f'{k} {f} {os.path.getsize(dst)} bytes')
ds = {k: xr.open_dataset(f'/tmp/{k}.nc') for k in FILES}
for k, d in ds.items():
    log.append(f'{k}: time {str(d.time.values[0])[:10]} to {str(d.time.values[-1])[:10]} ({d.time.size} days)'); print(log[-1], flush=True)
U850, U200 = ds['u']['uwnd'].sel(level=850), ds['u']['uwnd'].sel(level=200)
V850, V200 = ds['v']['vwnd'].sel(level=850), ds['v']['vwnd'].sel(level=200)
RH600 = ds['rh']['rhum'].sel(level=600)
LAT, LON = ds['u'].lat.values, ds['u'].lon.values
LA2, LO2 = np.meshgrid(LAT, LON, indexing='ij')


def ring(lat, lon):
    la1, lo1, la2, lo2 = map(np.radians, (lat, lon, LA2, LO2))
    d = 6371 * 2 * np.arcsin(np.sqrt(np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2))
    return (d >= 200) & (d <= 800)


def amean(da, day, m):
    try:
        x = da.sel(time=str(day)).values
    except KeyError:
        return float('nan')
    w = np.cos(np.radians(LA2)) * m
    return float((x * w).sum() / w.sum())


def sst_at(var, day, lat, lon):
    try:
        x = ds[var][var if var == 'sst' else 'anom'].sel(time=str(day)).sel(lat=lat, lon=lon % 360, method='nearest').values
        return float(x)
    except KeyError:
        return float('nan')


rows = list(csv.DictReader(open('raw/papers/ibtracs/tc_2026_all.csv')))
mx = {}
for r in rows:
    if r['wind_kt'].strip().isdigit():
        mx[r['sid']] = max(mx.get(r['sid'], 0), int(r['wind_kt']))
keep = {s for s, m in mx.items() if m >= 64}
out = []
for r in rows:
    if r['sid'] not in keep or r['basin'] not in ('NA', 'EP', 'WP') or r['time'][11:13] not in ('00', '06', '12', '18'):
        continue
    t = dt.datetime.fromisoformat(r['time']); day = t.date(); lat, lon = float(r['lat']), float(r['lon']) % 360
    m = ring(lat, lon)
    u = amean(U200, day, m) - amean(U850, day, m); v = amean(V200, day, m) - amean(V850, day, m)
    pre, post = day - dt.timedelta(3), day + dt.timedelta(3)
    out.append([r['sid'], r['name'], r['basin'], r['time'], lat, round(lon, 2), r['wind_kt'], r['pres_mb'],
                round(math.hypot(u, v) * 1.944, 1), (round(math.degrees(math.atan2(-u, -v)) % 360) if u == u and v == v else ''), round(amean(RH600, day, m), 1),
                round(sst_at('sst', pre, lat, lon), 2), round(sst_at('ssta', pre, lat, lon), 2),
                round(sst_at('sst', post, lat, lon) - sst_at('sst', pre, lat, lon), 2), r['dist2land_km'], r['landfall_km']])
with open(f'{OUT}/env_2026.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['sid', 'name', 'basin', 'time', 'lat', 'lon', 'wind_kt', 'pres_mb', 'shear_kt', 'shear_from_deg', 'rh600_pct', 'sst_pre_c', 'ssta_pre_c', 'sst_wake_c', 'dist2land_km', 'landfall_km'])
    w.writerows(out)
open(f'{OUT}/log.txt', 'w').write('\n'.join(log) + f'\nfixes {len(out)}\n')
print('\n'.join(log), len(out))
