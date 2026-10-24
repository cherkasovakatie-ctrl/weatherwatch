"""Derive the 2014–16 numbers quoted in Paper 3 from the diagnostics in data/papers/2015/ (no hand-typed values).

Inputs: mjo_summary.json and hov_u1000_anom_5S5N.csv (tools/papers/event_diag.py run for Jul 2013 – Dec 2016 with data
to 2016 but the climatology and EOF base kept at 1979–2000/2001, as in Papers 1 and 2), omi_2013_16.csv (NOAA PSL OMI),
tao_summary.json (tools/papers/tao_2015.py). Usage: python3 tools/papers/diag_2015.py [raw_omi_file]
"""
import csv
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[2] / 'data' / 'papers' / '2015'
if len(sys.argv) > 1:
    seen = {}
    for ln in open(sys.argv[1]):
        p = ln.split()
        if len(p) == 7 and p[0].isdigit() and len(p[0]) == 4:
            seen[dt.date(int(p[0]), int(p[1]), int(p[2]))] = (p[4], p[5], p[6])
    with open(D / 'omi_2013_16.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['date', 'pc1', 'pc2', 'amplitude'])
        for k in sorted(seen):
            if dt.date(2013, 7, 1) <= k <= dt.date(2016, 12, 31):
                w.writerow([k.isoformat(), *seen[k]])
omi = {r['date']: float(r['amplitude']) for r in csv.DictReader(open(D / 'omi_2013_16.csv'))}
S = json.load(open(D / 'mjo_summary.json'))
T = json.load(open(D / 'tao_summary.json'))
counts = {y['year']: y['wwb_count'] for y in S['wwb_yearly']}

# basin-mean 1000 hPa zonal-wind anomaly, 150°E–100°W (easterly bursts are broad, so a mean is used, not the burst rule)
rows = list(csv.DictReader(open(D / 'hov_u1000_anom_5S5N.csv')))
cols = [c for c in rows[0] if c != 'date' and 150 <= float(c) <= 260]
bm = {r['date']: statistics.mean(float(r[c]) for c in cols) for r in rows}
order = sorted(bm, key=bm.get)


def episodes(lo, hi, thr=1.0, min_len=15):
    out, cur = [], []
    for k in sorted(omi):
        if omi[k] >= thr:
            cur.append(k)
        else:
            if len(cur) >= min_len and lo <= cur[0] <= hi:
                out.append({'start': cur[0], 'end': cur[-1], 'days': len(cur), 'max': round(max(omi[x] for x in cur), 2)})
            cur = []
    return out


res = {
    'wwb': [{'start': w['start'], 'end': w['end'], 'peak': w['peak'], 'peak_anom_ms': w['peak_anom'], 'peak_lon_E': w['peak_lon'], 'lon_w': w['lon_w'],
             'lon_e': w['lon_e'], 'omi_amp_at_peak': omi.get(w['peak'])} for w in S['wwb'] if '2014-01-01' <= w['start'] <= '2016-01-31'],
    'wwb_count': {str(y): counts[y] for y in (1982, 1997, 2013, 2014, 2015, 2016)},
    'wwb_mean_1979_2001': round(statistics.mean(counts[y] for y in range(1979, 2002)), 1),
    'wwb_max_year_1979_2016': max(counts, key=counts.get),
    'basin_mean_min_jun_jul_2014': min(((d, round(v, 2)) for d, v in bm.items() if '2014-06-01' <= d <= '2014-07-31'), key=lambda x: x[1]),
    'basin_mean_rank_of_that_day': order.index(min((d for d in bm if '2014-06-01' <= d <= '2014-07-31'), key=bm.get)) + 1,
    'basin_mean_days_total': len(bm),
    'omi_episodes_2014': episodes('2013-10-01', '2014-12-31'), 'omi_episodes_2015': episodes('2015-01-01', '2016-06-30'),
    'seasons': {s['season']: s for s in S['seasons'] if s['season'] in ('1981-82', '1996-97', '2013-14', '2014-15', '2015-16')},
    'tao_data_return_quarterly': T['data_return_quarterly'],
}
json.dump(res, open(D / 'diag_2015.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('wwb', 'tao_data_return_quarterly')}, indent=1))
