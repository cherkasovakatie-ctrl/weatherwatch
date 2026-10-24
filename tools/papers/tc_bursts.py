"""Tropical cyclones and westerly wind bursts: 1982, 1997, 2015 (with the R1 burst lists of Papers 1–3) and 2026 (cyclone side only
until the 2026 burst list exists). Input: data/papers/climate/ibtracs_tropwp.csv (IBTrACS v04r01 subset, 6-hourly, 30S–30N, 90E–160W).
A burst is 'cyclone-accompanied' if, on any day from 2 days before its start to its end, a tropical cyclone (any intensity in IBTrACS)
is centred 3–20 degrees from the equator (either hemisphere) within 10 degrees of longitude of the burst span.
'Twin' = cyclones on both sides of the equator at once under the same test. The base rate is the share of all days of the same year
(March–December) on which the same test is met somewhere in 140E–170W, the burst region's core.
Writes data/papers/2026/tc_bursts.json. Run: python3 tools/papers/tc_bursts.py
"""
import csv
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
F = ROOT / 'data/papers/climate/ibtracs_tropwp.csv'
fix = defaultdict(list)  # date -> [(lat, lon, sid, name)]
first = {}
with open(F, encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        d = dt.date.fromisoformat(r['time'][:10]); lat, lon = float(r['lat']), float(r['lon'])
        fix[d].append((lat, lon, r['sid'], r['name']))
        first.setdefault(r['sid'], (d, lat, lon, r['name'], r['basin']))


def near(d, lw, le):
    nh = {(s, n) for la, lo, s, n in fix.get(d, []) if 3 <= la <= 20 and lw - 10 <= lo <= le + 10}
    sh = {(s, n) for la, lo, s, n in fix.get(d, []) if -20 <= la <= -3 and lw - 10 <= lo <= le + 10}
    return nh, sh


def burst_test(w):
    s, e = dt.date.fromisoformat(w['start']), dt.date.fromisoformat(w['end'])
    NH, SH, twin = set(), set(), False
    d = s - dt.timedelta(2)
    while d <= e:
        nh, sh = near(d, w['lon_w'], w['lon_e']); NH |= nh; SH |= sh; twin |= bool(nh and sh); d += dt.timedelta(1)
    return NH, SH, twin


def base_rate(y):
    days = [dt.date(y, 3, 1) + dt.timedelta(i) for i in range((dt.date(y, 12, 31) - dt.date(y, 3, 1)).days + 1)]
    any_, tw = 0, 0
    for d in days:
        nh, sh = near(d, 150, 180)  # core 140E-170W after the +/-10 deg margin
        any_ += bool(nh or sh); tw += bool(nh and sh)
    return round(100 * any_ / len(days)), round(100 * tw / len(days))


out = {'events': {}, 'year2026': {}}
for y in (1982, 1997, 2015):
    W = [w for w in json.load(open(ROOT / f'data/papers/{y}/mjo_summary.json'))['wwb'] if w['start'][:4] == str(y) and w['start'][5:7] >= '03']
    res = []
    for w in W:
        NH, SH, twin = burst_test(w)
        res.append(dict(start=w['start'], end=w['end'], lon_w=w['lon_w'], lon_e=w['lon_e'], nh=sorted(n for _, n in NH), sh=sorted(n for _, n in SH), twin=twin))
    br = base_rate(y)
    # matched base rate: each burst's own window length and longitude span, slid over every start day of Mar-Dec of the same year
    probs, tprobs = [], []
    for w in W:
        L = (dt.date.fromisoformat(w['end']) - dt.date.fromisoformat(w['start'])).days + 3
        hits = tot = th = 0
        st = dt.date(y, 3, 1)
        while st + dt.timedelta(L) <= dt.date(y, 12, 31):
            nn = [near(st + dt.timedelta(k), w['lon_w'], w['lon_e']) for k in range(L)]
            hits += any(a or b for a, b in nn); th += any(a and b for a, b in nn); tot += 1; st += dt.timedelta(1)
        probs.append(hits / tot); tprobs.append(th / tot)
    out['events'][y] = dict(n=len(res), with_tc=sum(bool(r['nh'] or r['sh']) for r in res), twin=sum(r['twin'] for r in res),
                            base_any_pct=br[0], base_twin_pct=br[1], expected_with_tc=round(sum(probs), 1), expected_twin=round(sum(tprobs), 1), bursts=res)


def lowlat_genesis(y, m1=10):
    g = [(d, la, lo, n, b) for sid, (d, la, lo, n, b) in first.items() if d.year == y and d.month <= m1 and abs(la) <= 10 and 130 <= lo <= 200]
    return sorted(g)


for y in (1982, 1997, 2015, 2026):
    g = lowlat_genesis(y)
    out['year2026' if y == 2026 else 'events'].setdefault(y, {})
    tgt = out['year2026'][y] if y == 2026 else out['events'][y]
    tgt['lowlat_genesis_jan_oct'] = len(g)
    tgt['lowlat_genesis_list'] = [(str(d), la, lo, n) for d, la, lo, n, b in g]
# 2026 twin-cyclone days (Jan-Oct), 140E-170W core
tw = []
d = dt.date(2026, 1, 1)
while d <= dt.date(2026, 10, 31):
    nh, sh = near(d, 150, 180)
    if nh and sh:
        tw.append((str(d), sorted(n for _, n in nh), sorted(n for _, n in sh)))
    d += dt.timedelta(1)
out['year2026'][2026]['twin_days_jan_oct'] = tw
out['year2026'][2026]['last_fix'] = str(max(fix))
for y in (1982, 1997, 2015):
    dd, n = dt.date(y, 1, 1), 0
    while dd <= dt.date(y, 10, 31):
        nh, sh = near(dd, 150, 180); n += bool(nh and sh); dd += dt.timedelta(1)
    out['events'][y]['twin_days_jan_oct'] = n
json.dump(out, open(ROOT / 'data/papers/2026/tc_bursts.json', 'w'), indent=1, default=str)
for y, e in out['events'].items():
    print(y, 'bursts', e['n'], 'with TC', e['with_tc'], 'twin', e['twin'], 'expected by chance', e['expected_with_tc'], 'twin exp', e['expected_twin'], 'lowlat gen', e['lowlat_genesis_jan_oct'], 'twin days', e['twin_days_jan_oct'])
z = out['year2026'][2026]
print(2026, 'lowlat gen', z['lowlat_genesis_jan_oct'], z['lowlat_genesis_list'], 'twin days', len(z['twin_days_jan_oct']), z['twin_days_jan_oct'][:20], 'last fix', z['last_fix'])
