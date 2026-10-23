"""Derive the 1997–98 numbers quoted in Paper 2 from the diagnostics in data/papers/1997/ (no hand-typed values).

Inputs: mjo_summary.json and mjo_index.csv (tools/papers/event_diag.py, run in Actions for Jul 1995 – Dec 1998 on the
same definitions as Paper 1), omi_1995_98.csv (NOAA PSL OMI, extracted from omi.1x.webpage.7921.txt), tao_summary.json
(tools/papers/tao_1997.py). Usage: python3 tools/papers/diag_1997.py [raw_omi_file]  -> writes data/papers/1997/diag_1997.json
"""
import csv
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[2] / 'data' / 'papers' / '1997'
if len(sys.argv) > 1:  # refresh the OMI extract from the PSL file saved by event_diag.py
    rows = [ln.split() for ln in open(sys.argv[1]) if len(ln.split()) == 7 and ln.split()[0].isdigit() and len(ln.split()[0]) == 4]
    seen = {}
    for p in rows:
        seen[dt.date(int(p[0]), int(p[1]), int(p[2]))] = (p[4], p[5], p[6])
    with open(D / 'omi_1995_98.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['date', 'pc1', 'pc2', 'amplitude'])
        for k in sorted(seen):
            if dt.date(1995, 7, 1) <= k <= dt.date(1998, 12, 31):
                w.writerow([k.isoformat(), *seen[k]])
omi = {r['date']: float(r['amplitude']) for r in csv.DictReader(open(D / 'omi_1995_98.csv'))}
S = json.load(open(D / 'mjo_summary.json'))
T = json.load(open(D / 'tao_summary.json'))

wwb = [w for w in S['wwb'] if '1996-12-01' <= w['start'] <= '1997-06-30']
counts = {y['year']: y['wwb_count'] for y in S['wwb_yearly']}
mean = statistics.mean(counts.values())
seasons = {s['season']: s for s in S['seasons']}


def rank(key, season='1996-97'):
    order = sorted(S['seasons'], key=lambda s: -s[key])
    return [s['season'] for s in order].index(season) + 1, len(order), round(statistics.mean(s[key] for s in S['seasons']), 1)


def episodes(lo, hi, thr=1.0, min_len=15):
    keys = sorted(omi)
    out, cur = [], []
    for k in keys:
        if omi[k] >= thr:
            cur.append(k)
        else:
            if len(cur) >= min_len and lo <= cur[0] <= hi:
                out.append({'start': cur[0], 'end': cur[-1], 'days': len(cur), 'max': round(max(omi[x] for x in cur), 2)})
            cur = []
    return out


res = {
    'wwb_dec96_jun97': [{'start': w['start'], 'end': w['end'], 'peak': w['peak'], 'peak_anom_ms': w['peak_anom'], 'peak_lon_E': w['peak_lon'],
                         'lon_w': w['lon_w'], 'lon_e': w['lon_e'], 'omi_amp_at_peak': omi.get(w['peak']), 'wh_like_amp_at_peak': w['wh_like_amp']} for w in wwb],
    'wwb_count_1997': counts[1997], 'wwb_count_1996': counts[1996], 'wwb_count_1995': counts[1995], 'wwb_count_1982': counts[1982],
    'wwb_mean_1979_2001': round(mean, 1), 'wwb_max_year': max(counts, key=counts.get),
    'mjo_days_rank_1996_97': rank('wh_like_days_amp_ge1'), 'olr_io_wp_var_rank_1996_97': rank('olr_20_100_var_60E_150E'),
    'mjo_days_1996_97': seasons['1996-97']['wh_like_days_amp_ge1'], 'mjo_days_1981_82': seasons['1981-82']['wh_like_days_amp_ge1'],
    'olr_io_wp_var_1997_98': seasons['1997-98']['olr_20_100_var_60E_150E'],
    'omi_episodes_onset': episodes('1996-09-01', '1997-06-30'), 'omi_episodes_termination': episodes('1998-03-01', '1998-06-30'),
    'tao_kelvin_waves': T['kelvin_waves'], 'tao_westerly_episodes': T['westerly_episodes_Nov1996_Jun1997'],
}
json.dump(res, open(D / 'diag_1997.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if not k.startswith('tao_')}, indent=1)[:3000])
