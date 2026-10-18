"""Indian-Pacific diagnostics for 1982-83 (probe, test branch only).
SST: NOAA ERSSTv5 monthly via ERDDAP. Winds: NCEP/NCAR R1 monthly surface (sigma 0.995) u via PSL THREDDS.
OLR: NOAA interpolated monthly OLR via PSL THREDDS. Anomalies vs 1981-2010; correlations on linearly detrended data."""
import csv, io, json, re, time, urllib.request
import numpy as np

def fetch(u, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=300) as r:
                return r.read().decode()
        except Exception as e:
            print('retry', i, u[-90:], e); time.sleep(15 * (i + 1))
    raise RuntimeError(u)

HOSTS = ['https://coastwatch.pfeg.noaa.gov', 'https://upwell.pfeg.noaa.gov']
def ersst(lat0, lat1, lon0, lon1):
    for h in HOSTS:
        try:
            t = fetch(f'{h}/erddap/griddap/nceiErsstv5.csv?sst[(1950-01-01):1:(2025-12-01)][(0.0)][({lat0}):1:({lat1})][({lon0}):1:({lon1})]', tries=2); break
        except Exception as e: print(e)
    acc = {}
    for l in t.split('\n')[2:]:
        f = l.split(',')
        if len(f) < 5 or f[4] in ('', 'NaN'): continue
        m = f[0][:7]; w = np.cos(np.deg2rad(float(f[2]))); a = acc.setdefault(m, [0, 0]); a[0] += w * float(f[4]); a[1] += w
    ks = sorted(acc); return ks, np.array([acc[k][0] / acc[k][1] for k in ks])

def anom(ks, x):
    out = x.copy()
    for mo in range(12):
        ii = [i for i, k in enumerate(ks) if int(k[5:]) == mo + 1]; base = [i for i in ii if '1981' <= ks[i][:4] <= '2010']
        out[ii] = x[ii] - x[base].mean()
    return out

B = {'wtio': (-10, 10, 50, 70), 'setio': (-10, 0, 90, 110), 'nino34': (-5, 5, 190, 240), 'tio': (-20, 20, 40, 100), 'trop': (-20, 20, 0, 358)}
S = {}
for k, b in B.items():
    ks, x = ersst(*b); S[k] = anom(ks, x)
months = ks
S['dmi'] = S['wtio'] - S['setio']
S['rel_nino34'] = S['nino34'] - S['trop']

def dods(url, shape):
    t = fetch(url).split('---------------------------------------------', 1)[1]
    a = np.full(shape, np.nan)
    for line in t.splitlines():
        if not line.startswith('['):
            if line.strip() == '' and np.isfinite(a).any(): break
            continue
        m = re.match(r'^((?:\[\d+\])+), (.*)$', line); idx = tuple(int(v) for v in re.findall(r'\[(\d+)\]', m.group(1)))
        a[idx] = np.array(m.group(2).split(', '), float)
    return a
# R1 monthly surface u, 1950-01 (index 24) .. 2025-12 (index 935); lat 5N..5S = 34..38; lon 2.5 deg from 0E
n = 935 - 24 + 1
U = dods(f'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.derived/surface/uwnd.mon.mean.nc.ascii?uwnd[24:1:935][34:1:38][0:1:143]', (n, 5, 144))
lon = np.arange(144) * 2.5
def ubox(l0, l1): return U[:, :, (lon >= l0) & (lon <= l1)].mean((1, 2))
for k, (l0, l1) in {'u_eqio_70_90E': (70, 90), 'u_wpac_130_160E': (130, 160), 'u_cpac_160E_150W': (160, 210)}.items():
    S[k] = anom(months, ubox(l0, l1))
# OLR monthly from 1974-06 (index 0); 1975-01 = 7; lat 90..-90 2.5; SETIO 0..10S = 36..40 ; lon 90-110E = 36..44; MC 100-140E
tt = fetch('https://psl.noaa.gov/thredds/dodsC/Datasets/interp_OLR/olr.mon.mean.nc.ascii?time').split('---------------------------------------------', 1)[1].strip().split('\n', 1)[1]
nt = len(re.findall(r'[\d.]+', tt))
O = dods(f'https://psl.noaa.gov/thredds/dodsC/Datasets/interp_OLR/olr.mon.mean.nc.ascii?olr[0:1:{nt-1}][32:1:40][0:1:143]', (nt, 9, 144))
okeys = [f'{1974 + (5 + i) // 12}-{(5 + i) % 12 + 1:02d}' for i in range(nt)]
olr = {}
for k, (j0, j1, l0, l1) in {'olr_setio': (4, 9, 90, 110), 'olr_mc_100_140E': (0, 9, 100, 140), 'olr_cpac_170E_140W': (0, 9, 170, 220)}.items():
    s = O[:, j0:j1, (lon >= l0) & (lon <= l1)].mean((1, 2)); full = np.full(len(months), np.nan)
    for i, mk in enumerate(okeys):
        if mk in months and np.isfinite(s[i]) and s[i] < 1e3: full[months.index(mk)] = s[i]
    olr[k] = full
for k, v in olr.items():
    a = v.copy()
    for mo in range(12):
        ii = [i for i, m in enumerate(months) if int(m[5:]) == mo + 1]; base = [i for i in ii if '1981' <= months[i][:4] <= '2010']
        a[ii] = v[ii] - np.nanmean(v[base])
    S[k] = a
cols = list(S)
with open('probe/io_monthly.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['month'] + cols)
    for i, m in enumerate(months): w.writerow([m] + ['' if not np.isfinite(S[c][i]) else f'{S[c][i]:.2f}' for c in cols])
# Seasonal means and statistics, 1950-2025 (OLR from 1975)
def seas(x, yr, ms):
    ii = [months.index(f'{yr + (m > 12)}-{(m - 1) % 12 + 1:02d}') for m in ms if f'{yr + (m > 12)}-{(m - 1) % 12 + 1:02d}' in months]
    return np.nanmean(x[ii]) if len(ii) == len(ms) else np.nan
yrs = np.arange(1950, 2025)
def ser(k, ms): return np.array([seas(S[k], y, ms) for y in yrs])
def detr(x):
    m = np.isfinite(x); p = np.polyfit(yrs[m], x[m], 1); return x - np.polyval(p, yrs)
SON, JJA, NDJ, MAM, AMJ = [9, 10, 11], [6, 7, 8], [11, 12, 13], [3, 4, 5], [4, 5, 6]
D = {f'{k}_{n}': detr(ser(k, ms)) for k in ('dmi', 'nino34', 'rel_nino34', 'setio', 'wtio', 'u_eqio_70_90E', 'u_wpac_130_160E', 'tio') for n, ms in [('SON', SON), ('JJA', JJA), ('NDJ', NDJ), ('MAM', MAM), ('AMJ', AMJ)]}
D['nino34_NDJnext'] = detr(np.array([seas(S['nino34'], y + 1, NDJ) for y in yrs]))
D['dmi_SONprev'] = detr(np.array([seas(S['dmi'], y - 1, SON) for y in yrs]))
def corr(a, b, ex=()):
    m = np.isfinite(a) & np.isfinite(b) & ~np.isin(yrs, ex); return round(float(np.corrcoef(a[m], b[m])[0, 1]), 2), int(m.sum())
def partial(a, b, c, ex=()):
    m = np.isfinite(a) & np.isfinite(b) & np.isfinite(c) & ~np.isin(yrs, ex)
    ra = a[m] - np.polyval(np.polyfit(c[m], a[m], 1), c[m]); rb = b[m] - np.polyval(np.polyfit(c[m], b[m], 1), c[m])
    return round(float(np.corrcoef(ra, rb)[0, 1]), 2), int(m.sum())
i82 = list(yrs).index(1982)
# Expected DMI(SON) from Nino3.4(SON) by regression excluding 1982; residual for 1982
x, y = D['nino34_SON'], D['dmi_SON']; m = np.isfinite(x) & np.isfinite(y) & (yrs != 1982)
p = np.polyfit(x[m], y[m], 1); resid = y[m] - np.polyval(p, x[m])
stats = dict(
  corr_dmiSON_nino34SON=corr(D['dmi_SON'], D['nino34_SON']), corr_dmiJJA_nino34JJA=corr(D['dmi_JJA'], D['nino34_JJA']),
  corr_dmiJJA_nino34NDJ=corr(D['dmi_JJA'], D['nino34_NDJ']), partial_dmiJJA_nino34NDJ_given_nino34JJA=partial(D['dmi_JJA'], D['nino34_NDJ'], D['nino34_JJA']),
  partial_dmiSON_nino34NDJnext_given_nino34SON=partial(D['dmi_SON'], D['nino34_NDJnext'], D['nino34_SON']),
  corr_dmiSON_nino34NDJnext=corr(D['dmi_SON'], D['nino34_NDJnext']),
  regression_dmiSON_on_nino34SON=dict(slope=round(float(p[0]), 3), intercept=round(float(p[1]), 3), resid_sd=round(float(resid.std()), 3)),
  y1982=dict(dmi_SON=round(float(y[i82]), 2), nino34_SON=round(float(x[i82]), 2), dmi_expected=round(float(np.polyval(p, x[i82])), 2), residual=round(float(y[i82] - np.polyval(p, x[i82])), 2),
             residual_z=round(float((y[i82] - np.polyval(p, x[i82])) / resid.std()), 2), dmi_SON_rank_of_75=int((y[np.isfinite(y)] > y[i82]).sum() + 1),
             nino34_NDJnext=round(float(D['nino34_NDJnext'][i82]), 2)),
  pos_iod_years_dmiSON_gt_0_4=[int(v) for v in yrs[np.isfinite(ser('dmi', SON)) & (ser('dmi', SON) > 0.4)]],
  el_nino_years_nino34SON_gt_0_5=[int(v) for v in yrs[ser('nino34', SON) > 0.5]],
  note='seasonal series linearly detrended 1950-2024 for correlations; thresholds on undetrended anomalies vs 1981-2010')
win = [i for i, mm in enumerate(months) if '1981-01' <= mm <= '1984-06']
stats['monthly_1981_84'] = [{'month': months[i], **{c: (None if not np.isfinite(S[c][i]) else round(float(S[c][i]), 2)) for c in cols}} for i in win]
json.dump(stats, open('probe/io_summary.json', 'w'), indent=1)
print('io done')
