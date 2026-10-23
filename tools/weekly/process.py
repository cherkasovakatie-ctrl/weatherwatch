"""Turn the raw weekly fetch (raw/<date>/ from tools/weekly/fetch_raw.py) into the weekly datasets in data/.

Each builder merges new rows into the existing file, keeps its column layout, prints an overlap check against the
old values, and refuses to write if the newest row would be older than the current file's.
Usage: python3 tools/weekly/process.py <raw_dir> [dataset ...]
"""
import csv
import datetime as dt
import json
import math
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data'
RAW = Path(sys.argv[1])
ONLY = set(sys.argv[2:])
LA = ZoneInfo('America/Los_Angeles')
NOW_LA = dt.datetime.now(LA)
TODAY_LA = NOW_LA.date().isoformat()
TODAY_UTC = dt.datetime.now(dt.timezone.utc).date().isoformat()


def rcsv(name):
    with open(D / name, newline='', encoding='utf-8') as fh:
        r = csv.reader(fh); hdr = next(r); return hdr, [dict(zip(hdr, row)) for row in r]


def wcsv(name, hdr, rows, key):
    old_hdr, old = rcsv(name)
    assert hdr == old_hdr, (name, hdr, old_hdr)
    if old and rows and max(r[key] for r in rows) < max(r[key] for r in old):
        print(f'  REFUSED {name}: newest row older than current file'); return False
    with open(D / name, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n'); w.writerow(hdr)
        for r in rows: w.writerow([r.get(h, '') for h in hdr])
    print(f'  wrote {name}: {len(rows)} rows, {rows[0][key]} .. {rows[-1][key]}'); return True


def j(name): return json.load(open(RAW / name))


def fmt(x, nd=1):
    return '' if x is None else (f'{x:.{nd}f}'.rstrip('0').rstrip('.') if nd else str(round(x)))


def overlap(label, pairs):
    pairs = [(a, b) for a, b in pairs if a not in ('', None) and b not in ('', None)]
    if pairs:
        d = [abs(float(a) - float(b)) for a, b in pairs]
        print(f'  overlap {label}: n={len(d)} mean |diff|={sum(d) / len(d):.3f} max={max(d):.3f}')


def want(k): return not ONLY or k in ONLY


# ---------------- mjo_daily: PSL real-time OMI (CPC OLR), last 150 days
if want('mjo_daily'):
    print('mjo_daily')
    hdr, old = rcsv('mjo_daily.csv'); oldd = {r['date']: r for r in old}
    rows = []
    for line in open(RAW / 'psl_romi.cpcolr.1x.txt'):
        p = line.split()
        if len(p) == 7 and p[0].isdigit():
            d = f'{p[0]}-{int(p[1]):02d}-{int(p[2]):02d}'; pc1, pc2, amp = float(p[4]), float(p[5]), float(p[6])
            r1, r2 = pc2, -pc1
            ph = int(((math.degrees(math.atan2(r2, r1)) + 180) // 45) % 8) + 1
            rows.append({'date': d, 'rmm1': f'{r1:.3f}', 'rmm2': f'{r2:.3f}', 'amplitude': f'{amp:.3f}', 'phase': str(ph)})
    rows = rows[-150:]
    overlap('amplitude', [(r['amplitude'], oldd[r['date']]['amplitude']) for r in rows if r['date'] in oldd])
    overlap('phase', [(r['phase'], oldd[r['date']]['phase']) for r in rows if r['date'] in oldd])
    wcsv('mjo_daily.csv', hdr, rows, 'date')

# ---------------- enso_subsurface: WWV column from PMEL
if want('wwv'):
    print('enso_subsurface (WWV)')
    hdr, old = rcsv('enso_subsurface.csv'); wwv = {}
    for line in open(RAW / 'pmel_wwv.dat'):
        p = line.split()
        if len(p) == 3 and p[0].isdigit() and len(p[0]) == 6: wwv[f'{p[0][:4]}-{p[0][4:]}'] = float(p[2]) / 1e14
    overlap('wwv', [(f"{wwv[r['month']]:.3f}", r['wwv_anom']) for r in old if r['month'] in wwv])
    for r in old:
        if r['month'] in wwv and r['month'] >= '1980-01': r['wwv_anom'] = f"{wwv[r['month']]:.3f}".rstrip('0').rstrip('.')
    wcsv('enso_subsurface.csv', hdr, old, 'month')

# ---------------- poles_daily: CPC AO, GFS 10 hPa 60N zonal-mean u, Greenland daily max T
GL_POINTS = {'gl_summit': 'summit', 'gl_kanger': 'kanger_b', 'gl_nw': 'nw_b', 'gl_south': 'south', 'gl_east': 'east'}  # points in fetch_raw.py
if want('poles_daily'):
    print('poles_daily')
    hdr, old = rcsv('poles_daily.csv'); rows = {r['date']: r for r in old}
    for line in open(RAW / 'cpc_ao_daily.csv'):
        p = line.strip().split(',')
        if len(p) == 4 and p[0].isdigit() and p[3] not in ('', 'NaN'):
            d = f'{p[0]}-{int(p[1]):02d}-{int(p[2]):02d}'
            if d in rows or d >= min(rows):
                rows.setdefault(d, {'date': d})['ao'] = f'{float(p[3]):.2f}'
    U = {}
    for lo in range(-180, 180, 45):
        h = j(f'om_u10hpa_{lo}.json')['hourly']
        for t, s, di in zip(h['time'], h['wind_speed_10hPa'], h['wind_direction_10hPa']):
            if s is not None and di is not None: U.setdefault(t[:10], []).append(-s / 3.6 * math.sin(math.radians(di)))
    new_u = {d: sum(v) / len(v) for d, v in U.items() if len(v) >= 8 * 20}
    overlap('u60 (old analysis)', [(f'{new_u[d]:.1f}', rows[d]['u60']) for d in new_u if d in rows])
    for d, v in new_u.items():
        r = rows.setdefault(d, {'date': d})
        if d < TODAY_UTC: r['u60'], r['u60_fc'] = f'{v:.1f}', ''
        else: r['u60'], r['u60_fc'] = '', f'{v:.1f}'
    gl_extra = {}
    for col, key in list(GL_POINTS.items()) + list(gl_extra.items()):
        dd = j(f'om_gl_{key}.json')['daily'] if not key.startswith('grid:') else None
        if dd is None:
            tag, idx = key.split(':')[1], int(key.split(':')[2]); dd = j(f'om_glgrid_{tag}.json')[idx]['daily']
        overlap(col, [(fmt(v), rows[d][col]) for d, v in zip(dd['time'], dd['temperature_2m_max']) if d in rows and d < '2026-10-15'])
        for d, v in zip(dd['time'], dd['temperature_2m_max']):
            if v is not None: rows.setdefault(d, {'date': d})[col] = fmt(v)
    out = [rows[d] for d in sorted(rows)]
    wcsv('poles_daily.csv', hdr, out, 'date')

# ---------------- ar_watch: daily max IWV and rain, past 7 days + 16-day forecast
AR_OFF = 'off_a'
if want('ar_watch'):
    print('ar_watch')
    hdr, old = rcsv('ar_watch.csv'); rows = {r['date']: r for r in old}
    for k, pre in (('vv', 'vv'), (AR_OFF, 'off'), ('sf', 'sf')):
        jj = j(f'om_ar_{k}.json'); mx = {}
        for t, v in zip(jj['hourly']['time'], jj['hourly']['total_column_integrated_water_vapour']):
            if v is not None: mx[t[:10]] = max(mx.get(t[:10], -1e9), v)
        for d, p in zip(jj['daily']['time'], jj['daily']['precipitation_sum']):
            if d in mx and p is not None:
                r = rows.setdefault(d, {'date': d}); r[f'{pre}_iwv'] = f'{mx[d]:.1f}'; r[f'{pre}_precip'] = f'{p:.1f}'
    for d, r in rows.items(): r['kind'] = 'observed' if d < TODAY_LA else 'forecast'
    keep = sorted(rows)[-30:]
    wcsv('ar_watch.csv', hdr, [rows[d] for d in keep], 'date')

# ---------------- ridge_watch: 500 hPa height anomalies vs 2021-2025 historical forecasts (+-7 days)
if want('ridge_watch'):
    print('ridge_watch')
    hdr, old = rcsv('ridge_watch.csv'); rows = {r['date']: r for r in old}
    for k in ('coast40', 'coast33', 'alaska50'):
        def daily(fn):
            h = j(fn)['hourly']; acc = {}
            for t, v in zip(h['time'], h['geopotential_height_500hPa']):
                if v is not None: acc.setdefault(t[:10], []).append(v)
            return {d: sum(v) / len(v) for d, v in acc.items() if len(v) >= 20}
        cur = daily(f'om_ridge_{k}.json'); hist = {}
        for y in range(2021, 2026): hist.update(daily(f'om_ridge_{k}_{y}.json'))
        def normal(d):
            dd = dt.date.fromisoformat(d); vals = []
            for y in range(2021, 2026):
                c = dd.replace(year=y)
                vals += [hist[(c + dt.timedelta(o)).isoformat()] for o in range(-7, 8) if (c + dt.timedelta(o)).isoformat() in hist]
            return sum(vals) / len(vals)
        overlap(f'{k} normal (old z-anom)', [(f'{normal(d):.0f}', float(rows[d][f'{k}_z']) - float(rows[d][f'{k}_anom'])) for d in cur if d in rows and rows[d].get(f'{k}_z')])
        for d, z in cur.items():
            r = rows.setdefault(d, {'date': d}); r[f'{k}_z'] = f'{z:.0f}'; r[f'{k}_anom'] = f'{z - normal(d):.0f}'
    for d, r in rows.items(): r['kind'] = 'observed' if d < TODAY_UTC else 'forecast'
    keep = sorted(rows)[-30:]
    wcsv('ridge_watch.csv', hdr, [rows[d] for d in keep], 'date')

# ---------------- coast_hourly: CO-OPS 9410660 water level (half-hourly) + Santa Ana gauge (hourly)
if want('coast_hourly'):
    print('coast_hourly')
    hdr, old = rcsv('coast_hourly.csv'); oldd = {r['time']: r for r in old}
    rows = {}
    for x in j('coops_obs6.json').get('data', []):
        t = x['t'].replace(' ', 'T')
        if t[14:16] in ('00', '30') and x['v']: rows.setdefault(t, {'time': t})['observed'] = x['v'].rstrip('0').rstrip('.') if '.' in x['v'] else x['v']
    for x in j('coops_pred.json').get('predictions', []):
        t = x['t'].replace(' ', 'T'); rows.setdefault(t, {'time': t})['predicted'] = f"{float(x['v']):.3f}".rstrip('0').rstrip('.')
    for r in rows.values():
        if r.get('observed') and r.get('predicted'): r['residual'] = f"{float(r['observed']) - float(r['predicted']):.2f}".rstrip('0').rstrip('.')
    lax, ton = j('om_coast_lax.json')['hourly'], j('om_coast_tonopah.json')['hourly']
    tp = dict(zip(ton['time'], ton['pressure_msl']))
    now = NOW_LA.strftime('%Y-%m-%dT%H:%M')
    for t, p, g, rh in zip(lax['time'], lax['pressure_msl'], lax['wind_gusts_10m'], lax['relative_humidity_2m']):
        if p is None or tp.get(t) is None: continue
        r = rows.setdefault(t, {'time': t}); r['gradient'] = f'{p - tp[t]:.1f}'; r['gust_lax'] = f'{g:.1f}' if g is not None else ''
        r['rh_lax'] = f'{rh:.0f}' if rh is not None else ''; r['forecast'] = '1' if t > now else '0'
    overlap('observed', [(r.get('observed'), oldd[t]['observed']) for t, r in rows.items() if t in oldd])
    overlap('gradient', [(r.get('gradient'), oldd[t]['gradient']) for t, r in rows.items() if t in oldd and oldd[t].get('forecast') == '0'])
    start = (NOW_LA - dt.timedelta(days=9)).strftime('%Y-%m-%dT%H:%M')
    out = [rows[t] for t in sorted(rows) if t >= start]
    wcsv('coast_hourly.csv', hdr, out, 'time')

# ---------------- polar_stations: now, today's mean, 1991-2020 same-week normal
if want('polar_stations'):
    print('polar_stations')
    hdr, old = rcsv('polar_stations.csv'); out = []
    doy = dt.date.fromisoformat(TODAY_UTC)
    for i, r in enumerate(old):
        now = j(f'om_polar_{i}_now.json'); clim = j(f'om_polar_{i}_clim.json')['daily']
        assert abs(now['latitude'] - float(r['lat'])) < 0.2, (r['station'], now['latitude'])
        vals = [v for t, v in zip(clim['time'], clim['temperature_2m_mean']) if v is not None and
                abs((dt.date.fromisoformat(t) - dt.date.fromisoformat(t).replace(month=doy.month, day=doy.day)).days) <= 3]
        nrm = sum(vals) / len(vals); cur = now['current']; mean = now['daily']['temperature_2m_mean'][0]
        out.append({**r, 'temp_now_c': fmt(cur['temperature_2m']), 'wind_kmh': fmt(cur['wind_speed_10m']), 'today_mean_c': fmt(mean),
                    'normal_c': fmt(nrm), 'anomaly_c': fmt(mean - nrm), 'obs_time_utc': cur['time'].replace('T', ' ')})
        print(f"  {r['station']}: now {cur['temperature_2m']} mean {mean} normal {nrm:.1f} (n={len(vals)})")
    wcsv('polar_stations.csv', hdr, out, 'obs_time_utc')

# ---------------- cdec_reservoirs: CDEC daily reservoir report (RES): storage, % of capacity, % of historical average
if want('cdec_reservoirs'):
    print('cdec_reservoirs')
    import html as _h, re as _re
    hdr, old = rcsv('cdec_reservoirs.csv')
    t = _h.unescape(_re.sub(r'<[^>]+>', ' | ', open(RAW / 'cdec_res.html', encoding='utf-8', errors='replace').read()))
    cells = [c.strip() for c in _re.split(r'\s*\|\s*', t) if c.strip()]
    m = _re.search(r'(\d{2}/\d{2}/\d{4})', t); print('  report date:', m.group(1) if m else 'not found')
    num = lambda x: int(x.replace(',', ''))
    out = []
    for r in old:
        k = cells.index(r['station'])  # ID cell; then capacity, elevation, storage, change, %cap, avg storage, %avg
        cap = num(cells[k + 1]); assert str(cap) == r['capacity_af'], (r['station'], cap)
        if '---' in (cells[k + 3], cells[k + 5], cells[k + 7]):
            print(f"  {r['station']}: not reported in RES today; row kept unchanged"); out.append(r); continue
        st, pcap, pavg = num(cells[k + 3]), cells[k + 5], cells[k + 7]
        print(f"  {r['station']}: {r['storage_af']} -> {st} ({pcap}% cap, {pavg}% avg)")
        out.append({**r, 'storage_af': str(st), 'pct_capacity': pcap, 'pct_average': pavg})
    with open(D / 'cdec_reservoirs.csv', 'w', newline='') as fh:
        w = csv.writer(fh, lineterminator='\n'); w.writerow(hdr); [w.writerow([o[h] for h in hdr]) for o in out]

# ---------------- polar_motion: USNO finals2000A monthly means (x, y arcsec), forecast flag
if want('polar_motion'):
    print('polar_motion')
    hdr, old = rcsv('polar_motion.csv'); rows = {r['month']: r for r in old}; acc = {}
    for line in open(RAW / 'usno_finals2000A.data'):
        if len(line) < 68 or not line[18:27].strip(): continue
        yy, mm = int(line[0:2]), int(line[2:4]); y = 2000 + yy if yy < 70 else 1900 + yy
        flag = line[16]; x, yv = float(line[18:27]), float(line[37:46])
        acc.setdefault(f'{y}-{mm:02d}', []).append((x, yv, flag == 'P'))
    new = {m: v for m, v in acc.items() if m >= '2026-07'}
    overlap('x', [(f'{sum(a for a, _, _ in v) / len(v):.4f}', rows[m]['x_arcsec']) for m, v in new.items() if m in rows and not any(p for *_, p in v)])
    for m, v in new.items():
        rows[m] = {'month': m, 'x_arcsec': f'{sum(a for a, _, _ in v) / len(v):.4f}'.rstrip('0'), 'y_arcsec': f'{sum(b for _, b, _ in v) / len(v):.4f}'.rstrip('0'),
                   'forecast': '1' if any(p for *_, p in v) else ''}
    wcsv('polar_motion.csv', hdr, [rows[m] for m in sorted(rows)], 'month')

# ---------------- enso_plume / enso_probs: IRI/CCSR monthly plume and objective probabilities (SVG geometry)
if want('enso_plume') and (RAW / 'iri_figure4.svg').exists():
    print('enso_plume')
    sys.path.insert(0, str(Path(__file__).parent))
    import enso_plume
    enso_plume.main(RAW)
