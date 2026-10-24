"""ERA5 200-850 hPa vertical wind shear along 2026 storm tracks: vector difference of the winds averaged over a 200-800 km annulus
around each 6-hourly position (daily-mean ERA5 at 2.5 deg, 00 and 12 UTC; data to 18 Oct 2026). Writes data/tc2026/era5_shear.csv.
Run: python3 tools/tc2026/era5_shear.py"""
import csv
import datetime as dt
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
z = np.load(ROOT / 'data/era5_2026/era5_2026_uv_daily.npz')
lat, lon = z['lat'], z['lon']; s0 = dt.date.fromisoformat(str(z['start'])); nd = z['u200'].shape[0]
U = {k: z[k].astype(np.float32) / 10 for k in ('u200', 'u850', 'v200', 'v850')}
LA, LO = np.meshgrid(lat, lon, indexing='ij'); W = np.cos(np.radians(LA))


def ring(la, lo):
    a1, o1, a2, o2 = map(np.radians, (la, lo, LA, LO))
    h = np.clip(np.sin((a2 - a1) / 2) ** 2 + np.cos(a1) * np.cos(a2) * np.sin((o2 - o1) / 2) ** 2, 0, 1)
    d = 6371 * 2 * np.arcsin(np.sqrt(h)); return (d >= 200) & (d <= 800)


out = []
for r in csv.DictReader(open(ROOT / 'data/tc2026/env_2026.csv', encoding='utf-8')):
    t = dt.datetime.fromisoformat(r['time']); i = (t.date() - s0).days
    la, lo = float(r['lat']), float(r['lon']) % 360
    if not (0 <= i < nd) or not (-27.5 <= la <= 47.5):
        out.append([r['sid'], r['name'], r['time'], '', '']); continue
    m = ring(la, lo); w = W * m
    mean = lambda k: float((U[k][i] * w).sum() / w.sum())  # noqa: E731
    du, dv = mean('u200') - mean('u850'), mean('v200') - mean('v850')
    out.append([r['sid'], r['name'], r['time'], round(math.hypot(du, dv) * 1.944, 1), round(math.degrees(math.atan2(-du, -dv)) % 360)])
with open(ROOT / 'data/tc2026/era5_shear.csv', 'w', newline='', encoding='utf-8') as fh:
    wr = csv.writer(fh); wr.writerow(['sid', 'name', 'time', 'shear_kt', 'shear_from_deg']); wr.writerows(out)
print(len(out), 'rows; with shear', sum(1 for x in out if x[3] != ''))
