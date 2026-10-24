"""2026 westerly wind bursts from ERA5 (Jan-Sep 2026 now; October when part 2 arrives), Papers 1-4 burst rule.
No ERA5 1979-2000 baseline is held, so the climatology is the one implied by ERA5 1981-82 and the R1 anomalies of 1981-82
(d = u_ERA5 - anom_R1, fitted per longitude with a mean and three annual harmonics; see wwb_era5_1982_direct.py); this is the
R1 1979-2000 seasonal cycle plus the mean ERA5-R1 offset. 2026 anomaly = u_ERA5(2026) - fit(d) at the same day of year.
Writes data/papers/2026/era5_wwb_2026.json. Run: python3 tools/papers/wwb_era5_2026.py"""
import csv
import datetime as dt
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
D82 = ROOT / 'data/papers/1982'
lon = np.arange(144) * 2.5
E = np.concatenate([np.load(D82 / f'era5_years/era5_{y}_pl.npz')['u1000_eq'] for y in (1981, 1982)]).astype(float) / 10
d0 = dt.date(1981, 1, 1); dates = [d0 + dt.timedelta(i) for i in range(len(E))]
rows = {r['date']: r for r in csv.DictReader(open(D82 / 'hov_u1000_anom_5S5N.csv', encoding='utf-8'))}
l5 = np.arange(0, 360, 5.0)
A = np.array([np.interp(lon, np.r_[l5, 360], np.r_[[float(rows[str(x)][f'{v:g}']) for v in l5], float(rows[str(x)]['0'])]) for x in dates])


def basis(t):
    return np.column_stack([np.ones(len(t))] + [g(2 * np.pi * h * t / 365.25) for h in (1, 2, 3) for g in (np.sin, np.cos)])


coef = np.linalg.lstsq(basis(np.arange(len(E))), E - A, rcond=None)[0]
z = np.load(ROOT / 'data/era5_2026/era5_2026_uv_daily.npz')
lat = z['lat']; w = np.cos(np.radians(lat)); m = (lat >= -5) & (lat <= 5)
u = z['u1000'].astype(float) / 10
U = (u[:, m, :] * w[m][None, :, None]).sum(1) / w[m].sum()
s26 = dt.date.fromisoformat(str(z['start'])); t26 = np.array([(s26 + dt.timedelta(i) - d0).days for i in range(len(U))])
anom = U - basis(t26) @ coef
reg = (lon >= 120) & (lon <= 210)
lab, k = ndimage.label((anom >= 5) & reg[None, :]); ev = []
for e in range(1, k + 1):
    ti, li = np.where(lab == e)
    if ti.max() - ti.min() + 1 < 3 or lon[li].max() - lon[li].min() < 10:
        continue
    pk = np.argmax(anom[ti, li])
    ev.append(dict(start=str(s26 + dt.timedelta(int(ti.min()))), end=str(s26 + dt.timedelta(int(ti.max()))), lon_w=float(lon[li].min()), lon_e=float(lon[li].max()),
                   peak_lon=float(lon[li[pk]]), peak_anom=round(float(anom[ti[pk], li[pk]]), 1)))
ev.sort(key=lambda x: x['start'])
e82 = json.load(open(D82 / 'era5_wwb_direct.json'))
n82 = sum(1 for r in e82['results'] for _ in [0] if r['matched'] and r['r1']['start'] <= '1982-09-30') 
era82 = [x for x in json.load(open(D82 / 'era5_wwb_direct.json'))['extra_era5']]
out = dict(method=__doc__.strip().splitlines()[1:5], data_end=str(s26 + dt.timedelta(len(U) - 1)), n_2026=len(ev), bursts=ev,
           mean_anom_120E_150W_by_month={f'2026-{mm:02d}': round(float(anom[[(s26 + dt.timedelta(i)).month == mm for i in range(len(U))]][:, reg].mean()), 2) for mm in range(1, 13) if any((s26 + dt.timedelta(i)).month == mm for i in range(len(U)))})
json.dump(out, open(ROOT / 'data/papers/2026/era5_wwb_2026.json', 'w'), indent=1)
print('2026 bursts', len(ev), 'to', out['data_end']); [print(x) for x in ev]; print(out['mean_anom_120E_150W_by_month'])
