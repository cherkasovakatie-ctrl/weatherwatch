"""Direct ERA5 vs R1 check of the 1982 westerly-wind-burst list (pre-registered rule: >= 9 of 13 R1 bursts matched).
ERA5: Kate's CDS downloads for 1981 and 1982 (u at 1000 hPa, 6-hourly, 2.5 deg), reduced to daily 5S-5N means in data/papers/1982/era5_years/.
Without ERA5 baseline years, ERA5 anomalies use the R1 seasonal cycle plus a fitted ERA5-R1 offset: for each longitude,
d = u_ERA5 - anom_R1 is fitted with a mean and three annual harmonics over 1981-82, and anom_ERA5 = u_ERA5 - fit(d).
Slow (seasonal) anomalies are therefore tied to R1; day-to-day bursts are ERA5's own. Burst rule as in Papers 1-3.
Writes data/papers/1982/era5_wwb_direct.json. Run: python3 tools/papers/wwb_era5_1982_direct.py
"""
import csv
import datetime as dt
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

D = Path(__file__).resolve().parents[2] / 'data/papers/1982'
E = np.concatenate([np.load(D / f'era5_years/era5_{y}_pl.npz')['u1000_eq'] for y in (1981, 1982)]).astype(float) / 10
dates = np.array([dt.date(1981, 1, 1) + dt.timedelta(i) for i in range(len(E))])
lon = np.arange(144) * 2.5
with open(D / 'hov_u1000_anom_5S5N.csv', encoding='utf-8') as fh:
    rows = {r['date']: r for r in csv.DictReader(fh)}
l5 = np.arange(0, 360, 5.0)
A = np.array([np.interp(lon, np.r_[l5, 360], np.r_[[float(rows[str(d)][f'{x:g}']) for x in l5], float(rows[str(d)]['0'])]) for d in dates])
t = np.arange(len(E))
X = np.column_stack([np.ones(len(E))] + [g(2 * np.pi * h * t / 365.25) for h in (1, 2, 3) for g in (np.sin, np.cos)])
dd = E - A
anomE = E - X @ np.linalg.lstsq(X, dd, rcond=None)[0]
reg = (lon >= 120) & (lon <= 210)


def bursts(a):
    lab, k = ndimage.label((a >= 5) & reg[None, :]); ev = []
    for e in range(1, k + 1):
        ti, li = np.where(lab == e)
        if ti.max() - ti.min() + 1 < 3 or lon[li].max() - lon[li].min() < 10:
            continue
        pk = np.argmax(a[ti, li])
        ev.append(dict(start=str(dates[ti.min()]), end=str(dates[ti.max()]), lon_w=float(lon[li].min()), lon_e=float(lon[li].max()),
                       peak_anom=round(float(a[ti[pk], li[pk]]), 1)))
    return ev


R1 = [w for w in json.load(open(D / 'mjo_summary.json'))['wwb'] if w['start'][:4] == '1982']
EV = [w for w in bursts(anomE) if w['start'][:4] == '1982' or w['end'][:4] == '1982']


def match(r, e):
    f = dt.date.fromisoformat
    t_ok = f(e['start']) <= f(r['end']) + dt.timedelta(3) and f(e['end']) >= f(r['start']) - dt.timedelta(3)
    return t_ok and e['lon_w'] <= r['lon_e'] and e['lon_e'] >= r['lon_w']


res = []
for r in R1:
    m = [e for e in EV if match(r, e)]
    res.append(dict(r1=r, matched=bool(m), era5=m))
extra = [e for e in EV if not any(match(r, e) for r in R1)]
n_m = sum(x['matched'] for x in res)
corr = float(np.corrcoef(anomE[:, reg].ravel(), A[:, reg].ravel())[0, 1])
out = dict(rule='R1 burst matched if an ERA5 burst overlaps its dates within +/-3 days and its longitude span; pass if >= 9 of 13',
           n_r1=len(R1), n_matched=n_m, passed=n_m >= 9, n_era5_1982=len(EV), extra_era5=extra, results=res,
           corr_daily_anom_120E_150W=round(corr, 3), method=__doc__.strip().splitlines()[2:5])
json.dump(out, open(D / 'era5_wwb_direct.json', 'w'), indent=1)
print(f'matched {n_m}/{len(R1)} passed={n_m >= 9}; ERA5 bursts {len(EV)}; extra {len(extra)}; corr {corr:.3f}')
for x in res:
    r = x['r1']; e = x['era5']
    print(r['start'], r['end'], r['lon_w'], r['lon_e'], r['peak_anom'], '->', [(w['start'], w['end'], w['lon_w'], w['lon_e'], w['peak_anom']) for w in e])
print('extra', [(w['start'], w['end'], w['lon_w'], w['lon_e'], w['peak_anom']) for w in extra])
