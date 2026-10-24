"""Track and intensity statistics for 2026 storms from IBTrACS v04r01 (provisional), 6-hourly fixes.
Rapid intensification (RI): wind increase >= 30 kt in 24 h (Kaplan and DeMaria 2003); also >= 35 kt and >= 50 kt.
ACE: sum of (wind_kt)^2 / 1e4 over 6-hourly fixes with wind >= 34 kt (NOAA convention; includes subtropical/extratropical fixes as stored).
Writes data/tc2026/track_stats.json. Run: python3 tools/tc2026/track_stats.py
"""
import csv
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = defaultdict(list)
with open(ROOT / 'data/tc2026/ibtracs_2026_all.csv', encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        S[r['sid']].append(r)


def hav(a, b, c, d):
    a, b, c, d = map(math.radians, (a, b, c, d))
    return 6371 * 2 * math.asin(math.sqrt(math.sin((c - a) / 2) ** 2 + math.cos(a) * math.cos(c) * math.sin((d - b) / 2) ** 2))


def cat(v):
    return 5 if v >= 137 else 4 if v >= 113 else 3 if v >= 96 else 2 if v >= 83 else 1 if v >= 64 else 'TS' if v >= 34 else 'TD'


out = {}
for sid, L in S.items():
    L = [r for r in L if r['time'][11:13] in ('00', '06', '12', '18')]
    W = [(dt.datetime.fromisoformat(r['time']), int(r['wind_kt']) if r['wind_kt'].strip().isdigit() else None, r) for r in L]
    ws = [w for _, w, _ in W if w is not None]
    if not ws or max(ws) < 64 or L[0]['basin'] not in ('NA', 'EP', 'WP'):
        continue
    pk = max(W, key=lambda x: (x[1] or 0, -x[0].timestamp()))
    pres = [int(r['pres_mb']) for r in L if r['pres_mb'].strip().isdigit()]
    ri = []
    for i, (t, w, _) in enumerate(W):
        for t2, w2, _ in W[i:]:
            if t2 - t == dt.timedelta(hours=24) and w is not None and w2 is not None:
                ri.append((str(t)[:16], str(t2)[:16], w2 - w))
    best = max(ri, key=lambda x: x[2]) if ri else None
    ri30 = [x for x in ri if x[2] >= 30]
    # merge RI windows into episodes
    eps = []
    for a, b, d in ri30:
        if eps and a <= eps[-1]['end']:
            eps[-1]['end'] = max(eps[-1]['end'], b); eps[-1]['max24'] = max(eps[-1]['max24'], d)
        else:
            eps.append({'start': a, 'end': b, 'max24': d})
    ace = sum(w * w for _, w, _ in W if w is not None and w >= 34) / 1e4
    dist = sum(hav(float(L[i]['lat']), float(L[i]['lon']), float(L[i + 1]['lat']), float(L[i + 1]['lon'])) for i in range(len(L) - 1))
    hrs = (W[-1][0] - W[0][0]).total_seconds() / 3600
    ts = [t for t, w, _ in W if w is not None and w >= 34]
    hu = [t for t, w, _ in W if w is not None and w >= 64]
    mj = [t for t, w, _ in W if w is not None and w >= 96]
    land = [(r['time'][:16], r['lat'], r['lon'], r['wind_kt']) for r in L if r['landfall_km'].strip() == '0']
    out[L[0]['name']] = dict(
        sid=sid, basin=L[0]['basin'], subbasins=sorted({r['subbasin'] for r in L}), agency=L[0]['wmo_agency'], first=L[0]['time'], last=L[-1]['time'],
        genesis=(L[0]['lat'], L[0]['lon']), peak_kt=pk[1], peak_time=str(pk[0])[:16], peak_pos=(pk[2]['lat'], pk[2]['lon']), peak_cat=cat(pk[1]),
        min_pres=min(pres) if pres else None, ace=round(ace, 1), track_km=round(dist), duration_h=round(hrs), mean_speed_kmh=round(dist / hrs, 1) if hrs else None,
        hours_ts=6 * len(ts), hours_hu=6 * len(hu), hours_major=6 * len(mj), first_hu=str(hu[0])[:16] if hu else None,
        max_24h_change=best, ri_episodes=eps, landfall_fixes=land[:12], track_type=L[-1]['track_type'],
        fixes=[(r['time'][:16], float(r['lat']), float(r['lon']), r['wind_kt'], r['pres_mb']) for r in L])
(ROOT / 'data/tc2026/track_stats.json').write_text(json.dumps(out, indent=1))
for k in ('TRUDY', 'SIMON', 'KOGUMA', 'ISAIAS', 'RACHEL'):
    o = out[k]
    print(k, o['basin'], o['subbasins'], o['agency'], o['first'], '->', o['last'], 'peak', o['peak_kt'], o['peak_time'], o['peak_pos'], 'Cat', o['peak_cat'], o['min_pres'], 'ACE', o['ace'],
          'km', o['track_km'], 'h', o['duration_h'], 'spd', o['mean_speed_kmh'], 'TS/HU/MH h', o['hours_ts'], o['hours_hu'], o['hours_major'], 'max24', o['max_24h_change'], 'RI', o['ri_episodes'], 'landfall', o['landfall_fixes'][:3])
