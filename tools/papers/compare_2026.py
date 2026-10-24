"""Paper 4 analog comparison: 2026 against 1982, 1997 and 2015 at the same calendar stage (onset year = year 0).
Reads the site's monthly files; writes data/papers/2026/analog_monthly.csv and analog_summary.json. Run: python3 tools/papers/compare_2026.py
"""
import csv
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2] / 'data'
OUT = R / 'papers/2026'
YEARS = (1982, 1997, 2015, 2026)
VARS = {  # file, key column, column
    'roni': ('oni.csv', 'centre_month', 'roni'), 'oni': ('oni.csv', 'centre_month', 'oni'),
    'nino12': ('sst_monthly.csv', 'month', 'nino12'), 'nino3': ('sst_monthly.csv', 'month', 'nino3'),
    'nino34': ('sst_monthly.csv', 'month', 'nino34'), 'nino4': ('sst_monthly.csv', 'month', 'nino4'),
    'rel_nino34': ('sst_monthly.csv', 'month', 'rel_nino34'), 'ersst_nino34': ('sst_monthly.csv', 'month', 'ersst_nino34'),
    'global_tropics': ('sst_monthly.csv', 'month', 'global_tropics'),
    'wwv': ('enso_subsurface.csv', 'month', 'wwv_anom'), 'heat': ('enso_subsurface.csv', 'month', 'heat_180_100w'),
    'soi': ('atmosphere_monthly.csv', 'month', 'soi'), 'olr_cp': ('atmosphere_monthly.csv', 'month', 'olr_central_pac'),
    'trades_w': ('atmosphere_monthly.csv', 'month', 'trades_west'), 'trades_c': ('atmosphere_monthly.csv', 'month', 'trades_central'),
    'pdo': ('drivers_monthly.csv', 'month', 'pdo'), 'dmi': ('drivers_monthly.csv', 'month', 'dmi_cpc'), 'tna': ('drivers_monthly.csv', 'month', 'tna'),
}
_cache = {}


def series(var):
    f, k, c = VARS[var]
    if f not in _cache:
        with open(R / f, encoding='utf-8') as fh:
            _cache[f] = {r[k]: r for r in csv.DictReader(fh)}
    return {m: float(r[c]) for m, r in _cache[f].items() if r.get(c) not in (None, '')}


def months(y0):  # Dec of year −1 to Dec of year +1
    out = [f'{y0 - 1}-12']
    for y in (y0, y0 + 1):
        out += [f'{y}-{m:02d}' for m in range(1, 13)]
    return out


S = {v: series(v) for v in VARS}
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / 'analog_monthly.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['lag', 'var', *YEARS])
    for i, lag in enumerate(['Dec-1'] + [f'{m}' for m in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')] + [f'{m}+1' for m in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')]):
        for v in VARS:
            w.writerow([lag, v, *[S[v].get(months(y)[i], '') for y in YEARS]])
summ = {}
for y in YEARS:
    ms = months(y)
    d = {}
    for v in VARS:
        vals = [(m, S[v][m]) for m in ms if m in S[v]]
        if vals:
            hi = max(vals, key=lambda t: t[1]); lo = min(vals, key=lambda t: t[1])
            d[v] = {'sep0': S[v].get(f'{y}-09'), 'max': hi, 'min': lo, 'last': vals[-1]}
    summ[y] = d
json.dump(summ, open(OUT / 'analog_summary.json', 'w'), indent=1)
