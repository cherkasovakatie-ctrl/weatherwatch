"""TAO/TRITON equatorial moorings, Jul 2013 – Dec 2016: data return by quarter (the 2012–14 decline), westerly
episodes and intraseasonal Kelvin-wave peaks in 20 °C isotherm depth. Same definitions as tools/papers/tao_1997.py.
Usage: python3 tools/papers/tao_2015.py <raw_dir>   (raw PMEL ERDDAP files from the weekly-raw branch, raw/papers/2015/)
"""
import json
import sys
from pathlib import Path

import pandas as pd
from scipy.signal import find_peaks

RAW = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[2] / 'data' / 'papers' / '2015'
OUT.mkdir(parents=True, exist_ok=True)
SITES = [147.0, 156.0, 165.0, 180.0, 190.0, 205.0, 220.0, 235.0, 250.0, 265.0]


def load(name, var):
    d = pd.read_csv(RAW / name, skiprows=[1], parse_dates=['time'])
    d['time'] = d.time.dt.tz_localize(None).dt.normalize()
    t = d.pivot_table(index='time', columns='longitude', values=var).reindex(pd.date_range('2013-07-01', '2016-12-31'))
    return t[[c for c in SITES if c in t.columns]]


U = load('tao_pmel_pmelTaoDyW.csv', 'WU_422')
D = load('tao_pmel_pmelTaoDyIso.csv', 'ISO_6')
cov = pd.DataFrame({'wind_pct': U.notna().resample('QS').mean().mean(axis=1) * 100,
                    'd20_pct': D.notna().resample('QS').mean().mean(axis=1) * 100}).round(0)
cov.index = cov.index.strftime('%Y-%m')
cov.to_csv(OUT / 'tao_data_return_quarterly.csv', index_label='quarter_start')

w = U[[147.0, 156.0, 165.0, 180.0]]
on = w.max(axis=1) >= 5
lab = (on != on.shift()).cumsum()
ep = []
for _, g in on[on].groupby(lab[on]):
    if len(g) < 2:
        continue
    seg = w.loc[g.index[0]:g.index[-1]]
    ep.append({'start': str(g.index[0].date()), 'end': str(g.index[-1].date()), 'days': len(g), 'max_u_ms': round(float(seg.max().max()), 1),
               'max_lon_E': float(seg.max().idxmax())})
pd.DataFrame(ep).to_csv(OUT / 'tao_westerly_episodes.csv', index=False)

lons = [165.0, 180.0, 190.0, 205.0, 220.0, 235.0, 250.0]
X = D[lons].interpolate(limit=10, limit_area='inside')
hp = (X - X.rolling(91, center=True, min_periods=60).mean()).rolling(7, center=True, min_periods=4).mean()
peaks = []
for lon in lons:
    s = hp[lon].dropna()
    pk, _ = find_peaks(s.values, height=8, distance=20)
    peaks += [{'lon_E': lon, 'date': str(s.index[p].date()), 'd20_anom_m': round(float(s.values[p]), 1)} for p in pk]
pd.DataFrame(peaks).to_csv(OUT / 'tao_kelvin_peaks.csv', index=False)
m = D.resample('MS').mean().round(0)
m.index = m.index.strftime('%Y-%m')
m.columns = [f'd20_{c:g}E' for c in m.columns]
m.to_csv(OUT / 'tao_d20_monthly.csv', index_label='month')
json.dump({'data_return_quarterly': cov.to_dict(orient='index'), 'westerly_episodes': ep}, open(OUT / 'tao_summary.json', 'w'), indent=1)
print(cov.to_string()); print(pd.DataFrame(ep).to_string()); print(pd.DataFrame(peaks).sort_values(['date']).to_string())
