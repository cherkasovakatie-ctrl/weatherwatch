"""Cache NOAA daily OLR CDR v02r00 on the R1 2.5-degree grid, 10N-10S, one compressed file per year: raw/olr_cdr/olr_YYYY.npz.
Usage: python3 tools/papers/olr_cache.py 1979 1980 ...  (skips years already cached, except the current year)."""
import datetime as dt, os, sys, time, urllib.request
import numpy as np, xarray as xr
CDR = 'https://archive.data.noaa.gov/climatedatarecords/UMD_ESSIC/OLR_CDR/Daily/OLR-D-CDR_01B-21/'
LAT25, LON25 = np.arange(10, -10.1, -2.5), np.arange(0, 360, 2.5)
os.makedirs('raw/olr_cdr', exist_ok=True)
UA = {'User-Agent': 'GlobalWeatherWatch/1.0'}

def name(y):
    if y < dt.date.today().year:
        return f'OLR-Daily_v02r00_s{y}0101_e{y}1231.nc'
    for back in range(21):
        d = dt.date.today() - dt.timedelta(back); n = f'OLR-Daily_v02r00-preliminary_s{y}0101_e{d:%Y%m%d}.nc'
        try:
            with urllib.request.urlopen(urllib.request.Request(CDR + n, method='HEAD', headers=UA), timeout=60) as r:
                if r.status == 200: return n
        except Exception: pass
    return None

for y in map(int, sys.argv[1:]):
    out = f'raw/olr_cdr/olr_{y}.npz'
    if os.path.exists(out) and y < dt.date.today().year:
        print(y, 'cached'); continue
    n = name(y); t0 = time.time()
    if not n: print(y, 'no file'); continue
    f = f'/tmp/olr_{y}.nc'
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(CDR + n, headers=UA), timeout=900) as r, open(f, 'wb') as fh:
                while True:
                    b = r.read(1 << 20)
                    if not b: break
                    fh.write(b)
            break
        except Exception as e:
            print(y, 'retry', i, e); time.sleep(30 * (i + 1))
    ds = xr.open_dataset(f)
    v = [k for k, d in ds.data_vars.items() if d.ndim == 3][0]; da = ds[v]
    lat = [c for c in da.dims if 'lat' in c][0]; lon = [c for c in da.dims if 'lon' in c][0]
    da = da.sortby(lat).sel({lat: slice(-11.5, 11.5)})
    lo = da[lon].values; da = da.assign_coords({lon: np.where(lo < 0, lo + 360, lo)}).sortby(lon)
    g = da.interp({lat: LAT25, lon: LON25}, kwargs={'fill_value': None}).transpose(da.dims[0], lat, lon).values.astype(np.float32)
    t = ds[da.dims[0]].values
    np.savez_compressed(out, olr=g.astype(np.float16), first=str(t[0])[:10], last=str(t[-1])[:10], src=n, var=v)
    ds.close(); os.remove(f)
    print(y, n, g.shape, str(t[-1])[:10], f'{time.time() - t0:.0f}s')
