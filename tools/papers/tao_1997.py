"""TAO/TRITON daily equatorial moorings, Jul 1995 – Dec 1998: westerly episodes, intraseasonal Kelvin-wave peaks in
20 °C isotherm depth, and monthly D20. Input: raw PMEL ERDDAP files (pmelTaoDyIso, pmelTaoDyW) from the weekly-raw
branch, raw/papers/1997/. Usage: python3 tools/papers/tao_1997.py <raw_dir>

Definitions (chosen before looking at the results, following Hartten 1996's surface-wind criterion of 5 m/s):
- westerly episode: daily TAO zonal wind >= 5 m/s at any of 147E, 156E, 165E, 180 on >= 2 consecutive days.
- Kelvin-wave peak: maximum of the 7-day-smoothed D20 after removing a centred 91-day mean, >= 8 m, >= 20 days apart.
- speed: great-circle distance along the equator between the 165E and 110W peaks of the same wave / time difference.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

RAW = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[2] / 'data' / 'papers' / '1997'
OUT.mkdir(parents=True, exist_ok=True)


def load(name, var):
    d = pd.read_csv(RAW / name, skiprows=[1], parse_dates=['time'])
    t = d.pivot_table(index='time', columns='longitude', values=var)
    t.index = t.index.tz_localize(None).normalize()
    return t


D = load('tao_pmel_pmelTaoDyIso.csv', 'ISO_6')
U = load('tao_pmel_pmelTaoDyW.csv', 'WU_422')
west = [147.0, 156.0, 165.0, 180.0]
cover = {f'{lon:g}': round(float(U[lon].notna().mean() * 100)) for lon in west}

w = U[west]
on = w.max(axis=1) >= 5
lab = (on != on.shift()).cumsum()
ep = []
for _, g in on[on].groupby(lab[on]):
    if len(g) < 2:
        continue
    seg = w.loc[g.index[0]:g.index[-1]]
    ep.append({'start': str(g.index[0].date()), 'end': str(g.index[-1].date()), 'days': len(g), 'max_u_ms': round(float(seg.max().max()), 1),
               'max_lon_E': float(seg.max().idxmax()), 'sites_ge5': ' '.join(f'{c:g}' for c in seg.columns if (seg[c] >= 5).any())})
pd.DataFrame(ep).to_csv(OUT / 'tao_westerly_episodes.csv', index=False)

lons = [165.0, 180.0, 190.0, 205.0, 220.0, 235.0, 250.0]
X = D[lons].interpolate(limit=10, limit_area='inside')
hp = (X - X.rolling(91, center=True, min_periods=60).mean()).rolling(7, center=True, min_periods=4).mean()
win = hp.loc['1996-11-01':'1997-08-31']
peaks = []
for lon in lons:
    s = win[lon].dropna()
    pk, _ = find_peaks(s.values, height=8, distance=20)
    peaks += [{'lon_E': lon, 'date': str(s.index[p].date()), 'd20_anom_m': round(float(s.values[p]), 1)} for p in pk]
pd.DataFrame(peaks).to_csv(OUT / 'tao_kelvin_peaks.csv', index=False)


def speed(d0, d1, lon0=165.0, lon1=250.0):
    km = (lon1 - lon0) * 111.2
    days = (pd.Timestamp(d1) - pd.Timestamp(d0)).days
    return round(km * 1000 / (days * 86400), 2), days, round(km)


P = pd.DataFrame(peaks)
waves = []
for a0, a1 in (('1996-12-20', '1997-01-20'), ('1997-03-01', '1997-04-01')):  # wave starts at 165E within these windows
    p0 = P[(P.lon_E == 165.0) & (P.date >= a0) & (P.date <= a1)].iloc[0]
    later = P[(P.lon_E == 250.0) & (P.date > p0.date)].iloc[0]
    sp, days, km = speed(p0.date, later.date)
    waves.append({'start_165E': p0.date, 'arrive_110W': later.date, 'days': days, 'distance_km': km, 'speed_ms': sp})
m = D.resample('MS').mean()[[156.0, 165.0, 180.0, 205.0, 220.0, 235.0, 250.0, 265.0]].round(0)
m.index = m.index.strftime('%Y-%m')
m.columns = [f'd20_{c:g}E' for c in m.columns]
m.loc['1996-01':'1998-12'].to_csv(OUT / 'tao_d20_monthly.csv')
summary = {'source': 'NOAA PMEL TAO/TRITON daily (ERDDAP pmelTaoDyIso, pmelTaoDyW), equator', 'wind_coverage_pct_Jul1995_Dec1998': cover,
           'westerly_episodes_Nov1996_Jun1997': [e for e in ep if '1996-11-01' <= e['start'] <= '1997-06-30'], 'kelvin_waves': waves}
json.dump(summary, open(OUT / 'tao_summary.json', 'w'), indent=1)
print(json.dumps(summary, indent=1))
