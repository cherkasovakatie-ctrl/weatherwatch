"""Re-test the 1982 westerly-wind-burst list with ERA5 (independent of NCEP/NCAR R1).

Input: data/papers/1982/era5_band_1979_2001.npz (tools/era5/fetch_band.py) and the R1 list in mjo_summary.json.
Same definitions as tools/papers/mjo_1982_diag.py: anomaly = departure from the 1979–2000 mean plus three annual harmonics;
burst = anomaly >= 5 m/s for >= 3 days over >= 10° longitude within 120°E–150°W (5°S–5°N mean).
Run for two ERA5 fields: u1000 (like for like with R1) and 10 m u (closer to the true surface wind stress).
A burst matches an R1 burst when their date ranges overlap within ±3 days and their longitude spans overlap.
Writes data/papers/1982/era5_wwb.json.  Run: python3 tools/papers/wwb_era5_1982.py
"""
import datetime as dt
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

D = Path(__file__).resolve().parents[2] / 'data' / 'papers' / '1982'
z = np.load(D / 'era5_band_1979_2001.npz')
start = dt.date.fromisoformat(str(z['start'])); lon = z['lon']
n = len(z['u10_eq']); dates = np.array([start + dt.timedelta(i) for i in range(n)])
t = np.arange(n); base = np.array([d.year <= 2000 for d in dates])
X = np.column_stack([np.ones(n)] + [g(2 * np.pi * h * t / 365.25) for h in (1, 2, 3) for g in (np.sin, np.cos)])
reg = (lon >= 120) & (lon <= 210)
win = np.array([dt.date(1981, 1, 1) <= d <= dt.date(1983, 6, 30) for d in dates])
r1 = json.load(open(D / 'mjo_summary.json'))
R1 = [w for w in r1['wwb']]; R1Y = {r['year']: r['wwb_count'] for r in r1['wwb_yearly']}


def bursts(u):
    a = u - X @ np.linalg.lstsq(X[base], u[base], rcond=None)[0]
    lab, k = ndimage.label((a >= 5) & reg[None, :]); ev = []
    for e in range(1, k + 1):
        ti, li = np.where(lab == e)
        if ti.max() - ti.min() + 1 < 3 or lon[li].max() - lon[li].min() < 10: continue
        pk = np.argmax(a[ti, li])
        ev.append(dict(start=str(dates[ti.min()]), end=str(dates[ti.max()]), lon_w=float(lon[li].min()), lon_e=float(lon[li].max()),
                       peak=str(dates[ti[pk]]), peak_anom=round(float(a[ti[pk], li[pk]]), 1)))
    return ev


def overlap(a, b):
    a0, a1 = dt.date.fromisoformat(a['start']) - dt.timedelta(3), dt.date.fromisoformat(a['end']) + dt.timedelta(3)
    return a0 <= dt.date.fromisoformat(b['end']) and dt.date.fromisoformat(b['start']) <= a1 and a['lon_w'] <= b['lon_e'] and b['lon_w'] <= a['lon_e']


out = {'method': __doc__.split('Run:')[0].strip(), 'fields': {}}
for name in ('u1000_eq', 'u10_eq'):
    ev = bursts(z[name].astype(float) / 10)
    yearly = {y: sum(1 for e in ev if e['start'][:4] == str(y)) for y in range(1979, 2002)}
    w = [e for e in ev if '1981-01-01' <= e['start'] <= '1983-06-30']
    for e in w: e['matches_R1'] = any(overlap(e, r) for r in R1)
    r1m = [dict(start=r['start'], end=r['end'], found_in_era5=any(overlap(r, e) for e in w)) for r in R1]
    cnt = [yearly[y] for y in yearly]
    out['fields'][name] = dict(window_bursts=w, r1_bursts_confirmed=r1m, yearly=yearly,
                               count_1982=yearly[1982], mean_1979_2001=round(float(np.mean(cnt)), 1), max_other_year=max(v for y, v in yearly.items() if y != 1982),
                               rank_1982=1 + sum(v > yearly[1982] for v in cnt), r1_1982=R1Y[1982],
                               corr_yearly_with_R1=round(float(np.corrcoef(cnt, [R1Y[y] for y in yearly])[0, 1]), 2))
json.dump(out, open(D / 'era5_wwb.json', 'w'), indent=1)
for k, v in out['fields'].items():
    print(k, {x: v[x] for x in ('count_1982', 'mean_1979_2001', 'max_other_year', 'rank_1982', 'r1_1982', 'corr_yearly_with_R1')},
          'R1 confirmed', sum(r['found_in_era5'] for r in v['r1_bursts_confirmed']), '/', len(R1))
