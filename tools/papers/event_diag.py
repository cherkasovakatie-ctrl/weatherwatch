"""MJO and westerly-wind-burst diagnostics for an event window set by env W0/W1 (YYYY-MM-DD), output to env OUT.
Generalised from tools/papers/mjo_1982_diag.py (same definitions, so events can be compared).
Data: NCEP/NCAR Reanalysis 1 daily u (1000, 850, 200 hPa) and NOAA daily OLR Climate Data Record v02r00 (NCEI archive; regridded to 2.5 deg), via PSL THREDDS and NCEI.
Base period for climatology and EOFs: 1979-2001 (Wheeler & Hendon 2004 used 1979-2001)."""
import json, re, time, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import numpy as np, traceback, sys, os
W0 = dt.date.fromisoformat(os.environ.get('W0', '1996-01-01')); W1 = dt.date.fromisoformat(os.environ.get('W1', '1998-06-30'))
OUTD = os.environ.get('OUT', 'probe'); os.makedirs(OUTD, exist_ok=True)
from scipy import ndimage

Y0, Y1 = 1979, int(os.environ.get('YEND', '2001'))  # data years; climatology and EOF base stay 1979-2000/2001 as in Paper 1
LAT = slice(32, 41)  # 10N..10S on the 2.5 deg grid (index 36 = equator)
R1 = 'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/uwnd.{y}.nc.ascii?uwnd[0:1:{n}][{lev}][32:1:40][0:1:143]'
LOG = []

def fetch(u, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=600) as r:
                return r.read().decode()
        except Exception as e:
            LOG.append(f'retry {i} {u[-80:]} {e}'); time.sleep(20 * (i + 1))
    raise RuntimeError('failed ' + u)

def parse(txt, shape):
    a = np.full(shape, np.nan, dtype=np.float32)
    body = txt.split('---------------------------------------------', 1)[1]
    for line in body.splitlines():
        if not line.startswith('['):
            if line.strip() == '' and np.isfinite(a).any():
                break
            continue
        m = re.match(r'^((?:\[\d+\])+), (.*)$', line)
        idx = tuple(int(x) for x in re.findall(r'\[(\d+)\]', m.group(1)))
        a[idx] = np.array(m.group(2).split(', '), dtype=np.float32)
    return a

def days(y): return 366 if y % 4 == 0 else 365

def ulen(y):  # days in a (possibly partial) current-year file, from the DDS header
    t = fetch(f'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/uwnd.{y}.nc.dds')
    n = int(re.search(r'time = (\d+)', t).group(1)); LOG.append(f'R1 {y}: {n} days in file'); return n

def get_u(y):
    n = days(y) if y < dt.date.today().year else ulen(y)
    a = parse(fetch(R1.format(y=y, n=n - 1, lev='0:2:2')), (n, 2, 9, 144))
    b = parse(fetch(R1.format(y=y, n=n - 1, lev='9:1:9')), (n, 1, 9, 144))
    return np.concatenate([a, b], axis=1)  # levels 1000, 850, 200


for name in ('omi.1x.webpage.7921.txt', 'omi.1x.orig.txt', 'rmm_star_data.txt', 'vpm.1x.txt', 'fmo.1x.txt', 'REOMI.txt', 'Koopman_MJO.txt', 'format.html'):
    try:
        t = fetch('https://psl.noaa.gov/mjo/mjoindex/' + name, tries=2); L = t.splitlines()
        yr = lambda l: int(l.split()[0][:4]) if l.split() and l.split()[0][:4].isdigit() else 0
        keep = [l for l in L if W0.year <= yr(l) <= W1.year]
        open(OUTD + '/idx_' + name.replace('.', '_') + '.txt', 'w').write(f'{len(L)} lines\nHEAD\n' + '\n'.join(L[:15]) + '\nTAIL\n' + '\n'.join(L[-3:]) + '\nwindow\n' + '\n'.join(keep if name != 'format.html' else []) + ('\n' + t[:20000] if name == 'format.html' else ''))
    except Exception as e:
        LOG.append(f'{name} {e}')

CDR = 'https://archive.data.noaa.gov/climatedatarecords/UMD_ESSIC/OLR_CDR/Daily/OLR-D-CDR_01B-21/'
LAT25, LON25 = np.arange(10, -10.1, -2.5), np.arange(0, 360, 2.5)

def cdr_name(y):
    if y < dt.date.today().year:
        return f'OLR-Daily_v02r00_s{y}0101_e{y}1231.nc'
    for back in range(0, 21):  # current year: preliminary file whose end date changes; probe recent end dates
        d = dt.date.today() - dt.timedelta(back)
        name = f'OLR-Daily_v02r00-preliminary_s{y}0101_e{d:%Y%m%d}.nc'
        try:
            with urllib.request.urlopen(urllib.request.Request(CDR + name, method='HEAD', headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=60) as r:
                if r.status == 200 and 'html' not in r.headers.get('Content-Type', ''):
                    return name
        except Exception:
            pass
    return None

def get_olr(y):
    """Daily OLR CDR v02r00 (NOAA NCEI), bilinearly interpolated to the R1 2.5-degree grid, 10N-10S; NaN where missing."""
    import xarray as xr
    n = days(y); out = np.full((n, 9, 144), np.nan, dtype=np.float32)
    name = None
    try:
        name = cdr_name(y)
        if name is None: raise RuntimeError('no preliminary file name found in index')
        f = f'/tmp/olr_{y}.nc'
        for i in range(4):
            try:
                urllib.request.urlretrieve(CDR + name, f); break
            except Exception as e:
                LOG.append(f'OLR {y} retry {i} {e}'); time.sleep(20 * (i + 1))
        ds = xr.open_dataset(f)
        v = [k for k, d in ds.data_vars.items() if d.ndim == 3][0]
        da = ds[v]; lat = [c for c in da.dims if 'lat' in c][0]; lon = [c for c in da.dims if 'lon' in c][0]
        da = da.sortby(lat).sel({lat: slice(-11.5, 11.5)})
        lo = da[lon].values; da = da.assign_coords({lon: np.where(lo < 0, lo + 360, lo)}).sortby(lon)
        g = da.interp({lat: LAT25, lon: LON25}, kwargs={'fill_value': None}).transpose(da.dims[0], lat, lon).values.astype(np.float32)
        k = min(n, g.shape[0]); out[:k] = g[:k]
        if y == Y0: LOG.append(f'OLR CDR var {v} dims {da.dims} first {ds[da.dims[0]].values[0]}')
        LOG.append(f'OLR {y}: {g.shape[0]} days from {name}')
        ds.close(); os.remove(f)
    except Exception as e:
        LOG.append(f'OLR {y} failed ({name}): {e}')
    return out

years = list(range(Y0, Y1 + 1))
with ThreadPoolExecutor(4) as ex:
    U = list(ex.map(get_u, years)); O = list(ex.map(get_olr, years))
U = np.concatenate(U); O = np.concatenate(O)
NL = len(U); U, O = U[:NL], O[:NL]  # partial current year: U sets the length; OLR gaps are filled below and not used for bursts
LOG.append(f'days used {NL}')
O[(O > 500) | (O < 50)] = np.nan
dates = np.array([dt.date(Y0, 1, 1) + dt.timedelta(d) for d in range(len(U))])
nanO = int(np.isnan(O).sum())
if nanO:
    for j in range(9):
        for k in range(144):
            s = O[:, j, k]; m = np.isnan(s)
            if m.any(): s[m] = np.interp(np.where(m)[0], np.where(~m)[0], s[~m])
lon = np.arange(144) * 2.5
lat = 10 - np.arange(9) * 2.5
w = np.cos(np.deg2rad(lat))[:, None]

def band(a, j0, j1): return (a[:, j0:j1] * w[j0:j1]).sum(1) / w[j0:j1].sum()

f = {'olr': band(O, 0, 9), 'u850': band(U[:, 1], 0, 9), 'u200': band(U[:, 2], 0, 9), 'u1000_eq': band(U[:, 0], 2, 7)}  # 10S-10N; 5S-5N for surface proxy
t = np.arange(len(dates)); base = np.array([d.year <= 2000 for d in dates])
X = np.column_stack([np.ones_like(t, float)] + [g(2 * np.pi * h * t / 365.25) for h in (1, 2, 3) for g in (np.sin, np.cos)])
anom = {}
for k, v in f.items():
    c, *_ = np.linalg.lstsq(X[base], v[base], rcond=None); anom[k] = v - X @ c

def bandpass(x, lo=20, hi=100):
    F = np.fft.rfft(x - x.mean(0), axis=0); fr = np.fft.rfftfreq(len(x))
    F[(fr < 1 / hi) | (fr > 1 / lo)] = 0
    return np.fft.irfft(F, n=len(x), axis=0)

def prev120(x):
    c = np.cumsum(np.vstack([np.zeros((1, x.shape[1])), x]), 0); out = x.copy()
    for i in range(len(x)):
        a = max(0, i - 120); out[i] = x[i] - (c[i] - c[a]) / max(1, i - a) if i else x[i]
    return out

filt = {k: bandpass(anom[k]) for k in ('olr', 'u850', 'u200', 'u1000_eq')}
wh = {k: prev120(anom[k]) for k in ('olr', 'u850', 'u200')}

NB = int(sum(d.year <= 2001 for d in dates)); FIT = slice(120, NB)  # EOFs fitted on 1979-2001 only (Paper 1 base), applied to all days

def ceof(fields):
    Z = np.hstack([v / v[FIT].std() for v in fields]); Zc = Z - Z[FIT].mean(0)
    _, s, vt = np.linalg.svd(Zc[FIT], full_matrices=False)
    pc = Zc @ vt[:2].T; pc /= pc[FIT].std(0)
    eof = vt[:2]; var = (s[:2] ** 2 / (s ** 2).sum()).round(3).tolist()
    # orient: eastward propagation means the pattern of PC1 is followed by PC2's pattern shifted east; enforce PC1 leads PC2
    lagc = np.corrcoef(pc[FIT][:-10, 0], pc[FIT][10:, 1])[0, 1]
    if lagc < 0: pc[:, 1] *= -1; eof[1] *= -1
    olr_pat = eof[:, :144]
    amp = np.hypot(pc[:, 0], pc[:, 1]); ang = np.arctan2(pc[:, 1], pc[:, 0])
    recon = np.cos(ang)[:, None] * olr_pat[0] + np.sin(ang)[:, None] * olr_pat[1]
    centre = lon[np.argmin(recon, 1)]
    return dict(pc=pc, amp=amp, ang=ang, centre=centre, var=var, lag10=round(float(abs(lagc)), 3))

IDX = {'wh_like': ceof([wh['olr'], wh['u850'], wh['u200']]), 'bandpass_20_100': ceof([filt['olr'], filt['u850'], filt['u200']]), 'olr_only_20_100': ceof([filt['olr']])}
win = np.array([W0 <= d <= W1 for d in dates])

def episodes(ix, min_len=15):
    out = []; amp = ix['amp']; on = amp >= 1
    lab, n = ndimage.label(on)
    for e in range(1, n + 1):
        ii = np.where(lab == e)[0]
        if len(ii) < min_len or not win[ii].any(): continue
        un = np.unwrap(ix['ang'][ii]); prog = np.degrees(un[-1] - un[0])
        c = np.unwrap(np.deg2rad(ix['centre'][ii])); slope = np.polyfit(ii, np.degrees(c), 1)[0]
        out.append(dict(start=str(dates[ii[0]]), end=str(dates[ii[-1]]), days=len(ii), max_amp=round(float(amp[ii].max()), 2),
                        phase_progress_deg=round(float(prog), 0), centre_start=float(ix['centre'][ii[0]]), centre_end=float(ix['centre'][ii[-1]]),
                        centre_speed_ms=round(float(slope * 111e3 / 86400), 1)))
    return out

EP = {k: episodes(v) for k, v in IDX.items()}
# Westerly wind bursts: 5S-5N 1000 hPa anomaly >= 5 m/s, >= 3 days, >= 10 deg longitude, within 120E-150W
reg = (lon >= 120) & (lon <= 210)
mask = (anom['u1000_eq'] >= 5) & reg[None, :]
lab, n = ndimage.label(mask)
wwb = []
for e in range(1, n + 1):
    ti, li = np.where(lab == e)
    if ti.max() - ti.min() + 1 < 3 or (lon[li].max() - lon[li].min()) < 10 or not win[ti].any(): continue
    pk = np.argmax(anom['u1000_eq'][ti, li]); tp, lp = ti[pk], li[pk]
    o_f = float(filt['olr'][tp, lp]); u_lf = float(np.mean(anom['u1000_eq'][max(0, tp - 60):tp + 1, lp]))
    wwb.append(dict(start=str(dates[ti.min()]), end=str(dates[ti.max()]), lon_w=float(lon[li].min()), lon_e=float(lon[li].max()), peak=str(dates[tp]),
                    peak_lon=float(lon[lp]), peak_anom=round(float(anom['u1000_eq'][tp, lp]), 1), olr_20_100_at_peak=round(o_f, 1),
                    u1000_20_100_at_peak=round(float(filt['u1000_eq'][tp, lp]), 1), u1000_prev60d_mean=round(u_lf, 1),
                    **{f'{k}_amp': round(float(v['amp'][tp]), 2) for k, v in IDX.items()}, **{f'{k}_centre': float(v['centre'][tp]) for k, v in IDX.items()}))
# Base rates for WWBs and MJO activity by Oct-Mar season and by year, same definitions, 1979-2001
def season_stats():
    rows = []
    for y in range(1979, Y1):
        s = np.array([(d.year == y and d.month >= 10) or (d.year == y + 1 and d.month <= 3) for d in dates])
        rows.append(dict(season=f'{y}-{(y + 1) % 100:02d}', **{f'{k}_days_amp_ge1': int((v['amp'][s] >= 1).sum()) for k, v in IDX.items()},
                         olr_20_100_var_160E_150W=round(float(filt['olr'][s][:, (lon >= 160) & (lon <= 210)].var()), 1),
                         olr_20_100_var_60E_150E=round(float(filt['olr'][s][:, (lon >= 60) & (lon <= 150)].var()), 1)))
    return rows
yearly = []
for y in range(1979, Y1 + 1):
    s = np.array([d.year == y for d in dates]); cnt = 0
    for e in range(1, n + 1):
        ti, li = np.where(lab == e)
        if ti.max() - ti.min() + 1 >= 3 and (lon[li].max() - lon[li].min()) >= 10 and dates[ti.min()].year == y: cnt += 1
    yearly.append(dict(year=y, wwb_count=cnt))
# Hovmoller output for the window (5 deg spacing)
import csv
for k, src in [('olr_anom', anom['olr']), ('olr_20_100', filt['olr']), ('u850_anom', anom['u850']), ('u850_20_100', filt['u850']), ('u200_20_100', filt['u200']), ('u1000_anom_5S5N', anom['u1000_eq'])]:
    with open(f'{OUTD}/hov_{k}.csv', 'w', newline='') as fh:
        wr = csv.writer(fh); wr.writerow(['date'] + [f'{x:g}' for x in lon[::2]])
        for i in np.where(win)[0]: wr.writerow([str(dates[i])] + [f'{v:.1f}' for v in src[i, ::2]])
with open(OUTD + '/mjo_index.csv', 'w', newline='') as fh:
    wr = csv.writer(fh); wr.writerow(['date'] + [f'{k}_{c}' for k in IDX for c in ('pc1', 'pc2', 'amp', 'centre')])
    for i in np.where(win)[0]: wr.writerow([str(dates[i])] + [x for v in IDX.values() for x in (f"{v['pc'][i,0]:.2f}", f"{v['pc'][i,1]:.2f}", f"{v['amp'][i]:.2f}", f"{v['centre'][i]:g}")])
json.dump(dict(base=f'{Y0}-{Y1}', climatology='1979-2000 mean + 3 harmonics', nan_olr_filled=nanO, index_info={k: dict(var=v['var'], lag10_corr=v['lag10']) for k, v in IDX.items()},
               episodes=EP, wwb=wwb, wwb_yearly=yearly, seasons=season_stats(), log=LOG), open(OUTD + '/mjo_summary.json', 'w'), indent=1, default=float)
print('done', len(wwb), {k: len(v) for k, v in EP.items()})
