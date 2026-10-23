"""Stage-5 check for Paper 2: recompute every data-derived number quoted in the 1997–98 paper from the source files.
Prints CLAIM | QUOTED | RECOMPUTED | OK/CHECK and exits non-zero if any check fails. Run: python3 tools/papers/verify_1997.py
"""
import csv
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[2] / 'data'


def load(f, key):
    with open(R / f, encoding='utf-8') as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


oni, sm, at, sub, dr = (load('oni.csv', 'centre_month'), load('sst_monthly.csv', 'month'), load('atmosphere_monthly.csv', 'month'),
                        load('enso_subsurface.csv', 'month'), load('drivers_monthly.csv', 'month'))
tao = load('papers/1997/tao_d20_monthly.csv', 'time')
DG = json.load(open(R / 'papers/1997/diag_1997.json'))
MS = json.load(open(R / 'papers/1997/mjo_summary.json'))
TS = json.load(open(R / 'papers/1997/tao_summary.json'))
omi = {r['date']: float(r['amplitude']) for r in csv.DictReader(open(R / 'papers/1997/omi_1995_98.csv'))}
rows = []


def v(d, k, c):
    x = d.get(k, {}).get(c)
    return float(x) if x not in (None, '') else float('nan')


def months(a, b):
    out, (y, m) = [], map(int, a.split('-'))
    while f'{y}-{m:02d}' <= b:
        out.append(f'{y}-{m:02d}')
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def chk(claim, quoted, val, tol=0.051, ok=None):
    if ok is None:
        ok = abs(float(quoted) - float(val)) < tol
    rows.append((claim, quoted, val, 'OK' if ok else 'CHECK'))


def rng(claim, lo, hi, vals, tol=0.051):
    a, b = min(vals), max(vals)
    rows.append((claim, f'{lo}..{hi}', f'{a}..{b}', 'OK' if abs(a - lo) < tol and abs(b - hi) < tol else 'CHECK'))


# ENSO indices
chk('RONI OND 1995 minimum', -1.02, min(v(oni, k, 'roni') for k in months('1995-07', '1996-06')))
chk('RONI JJA 1995', -0.41, v(oni, '1995-07', 'roni'))
chk('RONI FMA 1996', -0.58, v(oni, '1996-03', 'roni'))
rng('RONI MAM 1996 – DJF 1997', -0.37, -0.20, [v(oni, k, 'roni') for k in months('1996-04', '1997-01')])
rng('Niño 1+2 Apr 1996 – Jan 1997 (stated −1.6..−0.7)', -1.64, -0.73, [v(sm, k, 'nino12') for k in months('1996-04', '1997-01')])
for k, q in (('1997-05', 0.83), ('1997-06', 1.20), ('1997-07', 1.50), ('1997-10', 2.22), ('1997-12', 2.28), ('1998-06', -0.46), ('1998-07', -1.05)):
    chk(f'RONI {oni[k]["season"]}', q, v(oni, k, 'roni'))
chk('ONI NDJ 1997', 2.37, v(oni, '1997-12', 'oni'))
peak = max(months('1997-01', '1998-06'), key=lambda k: v(oni, k, 'roni'))
chk('RONI peak season is NDJ 1997', 'NDJ 1997', oni[peak]['season'], ok=oni[peak]['season'] == 'NDJ 1997')
chk('RONI − ONI at peak (0.09)', 0.09, round(v(oni, '1997-12', 'oni') - v(oni, '1997-12', 'roni'), 2), tol=0.006)
# subsurface
chk('WWV Dec 1995', 0.05, v(sub, '1995-12', 'wwv_anom'))
w96 = [v(sub, k, 'wwv_anom') for k in months('1996-01', '1996-12')]
rng('WWV 1996 range', 0.26, 0.85, w96)
chk('WWV 1996 all positive', 'all > 0', min(w96), ok=min(w96) > 0)
rng('Heat content 1996 range', -0.47, 0.17, [v(sub, k, 'heat_180_100w') for k in months('1996-01', '1996-12')])
chk('Heat Jan 1997', 0.56, v(sub, '1997-01', 'heat_180_100w'))
chk('Heat Feb 1997', 1.00, v(sub, '1997-02', 'heat_180_100w'))
chk('WWV Jan 1997', 1.64, v(sub, '1997-01', 'wwv_anom'))
chk('WWV Feb 1997', 2.14, v(sub, '1997-02', 'wwv_anom'))
pk = max(months('1995-07', '1998-12'), key=lambda k: v(sub, k, 'wwv_anom'))
chk('WWV peak month Apr 1997', '1997-04', pk, ok=pk == '1997-04')
chk('WWV Apr 1997', 3.12, v(sub, '1997-04', 'wwv_anom'))
chk('Heat Apr 1997', 2.17, v(sub, '1997-04', 'heat_180_100w'))
chk('WWV Nov 1997', 0.66, v(sub, '1997-11', 'wwv_anom'))
chk('WWV Dec 1997', -0.77, v(sub, '1997-12', 'wwv_anom'))
chk('WWV first negative month Dec 1997', '1997-12', next(k for k in months('1997-05', '1998-12') if v(sub, k, 'wwv_anom') < 0),
    ok=next(k for k in months('1997-05', '1998-12') if v(sub, k, 'wwv_anom') < 0) == '1997-12')
# atmosphere and SST
chk('W Pac trades Mar 1997', -3.1, v(at, '1997-03', 'trades_west'))
for k, q in (('1997-02', -0.45), ('1997-03', 0.23), ('1997-04', 0.80), ('1997-05', 1.83), ('1997-06', 2.79)):
    chk(f'Niño 1+2 {k}', q, v(sm, k, 'nino12'))
chk('SOI May 1997', -1.3, v(at, '1997-05', 'soi'))
chk('SOI Jun 1997', -1.4, v(at, '1997-06', 'soi'))
chk('C Pac OLR May 1997', -25.7, v(at, '1997-05', 'olr_central_pac'))
chk('C Pac OLR Jun 1997', -26.8, v(at, '1997-06', 'olr_central_pac'))
chk('C Pac trades Oct 1997', -4.1, v(at, '1997-10', 'trades_central'))
chk('C Pac OLR Oct 1997', -49.8, v(at, '1997-10', 'olr_central_pac'))
chk('DMI (CPC) Jul 1997', 0.55, v(dr, '1997-07', 'dmi_cpc'))
chk('DMI (CPC) Nov 1997', 1.39, v(dr, '1997-11', 'dmi_cpc'))
dmax = max(months('1997-01', '1998-06'), key=lambda k: v(dr, k, 'dmi_cpc'))
chk('DMI peak month Nov 1997', '1997-11', dmax, ok=dmax == '1997-11')
rng('PDO May–Jun 1997 (stated +1.6..+2.6)', 1.59, 2.55, [v(dr, k, 'pdo') for k in ('1997-05', '1997-06')])
chk('TNA Mar 1997', -0.37, v(dr, '1997-03', 'tna'))
chk('TNA May 1998', 0.51, v(dr, '1998-05', 'tna'))
# TAO
rng('TAO D20 110°W Oct–Dec 1997 (about 130 m)', 129, 131, [v(tao, k, 'd20_250E') for k in months('1997-10', '1997-12')], tol=0.6)
rng('TAO D20 110°W Dec 1996 – Jan 1997 (29–46 m)', 29, 46, [v(tao, k, 'd20_250E') for k in ('1996-12', '1997-01')], tol=0.6)
chk('TAO D20 140°W Nov 1997 (about 135 m)', 135, v(tao, '1997-11', 'd20_220E'), tol=0.6)
chk('TAO D20 140°W May 1998 (about 62 m)', 62, v(tao, '1998-05', 'd20_220E'), tol=0.6)
kw = TS['kelvin_waves']
chk('Kelvin wave 1: 52 days, 2.1 m/s', 2.1, kw[0]['speed_ms'], tol=0.051)
chk('Kelvin wave 2: 38 days, 2.9 m/s', 2.9, kw[1]['speed_ms'], tol=0.051)
ep = {e['start']: e for e in TS['westerly_episodes_Nov1996_Jun1997']}
chk('TAO 21–26 Dec max 8.7 m/s at 156E', 8.7, ep['1996-12-24']['max_u_ms'])
chk('TAO 27 Feb – 6 Mar max 9.9 m/s at 147E', 9.9, ep['1997-02-27']['max_u_ms'])
chk('TAO 11–16 Mar max 8.6 m/s at 165E', 8.6, ep['1997-03-11']['max_u_ms'])
chk('TAO 13–20 Apr max 11.0 m/s at 165E', 11.0, ep['1997-04-13']['max_u_ms'])
chk('TAO 22–26 May max 10.2 m/s at 165E', 10.2, ep['1997-05-22']['max_u_ms'])
chk('TAO coverage 147E 37%, 156E 64%', '37/64', f"{TS['wind_coverage_pct_Jul1995_Dec1998']['147']}/{TS['wind_coverage_pct_Jul1995_Dec1998']['156']}",
    ok=(TS['wind_coverage_pct_Jul1995_Dec1998']['147'], TS['wind_coverage_pct_Jul1995_Dec1998']['156']) == (37, 64))
# reanalysis bursts and MJO
counts = {y['year']: y['wwb_count'] for y in MS['wwb_yearly']}
chk('Bursts 1997 = 16, most of 1979–2001', 16, counts[1997], ok=counts[1997] == 16 and counts[1997] == max(counts.values()))
chk('Bursts 1982 = 13', 13, counts[1982], ok=counts[1982] == 13)
chk('Bursts 1995 = 0, 1996 = 3', '0/3', f'{counts[1995]}/{counts[1996]}', ok=(counts[1995], counts[1996]) == (0, 3))
chk('Mean bursts 1979–2001 = 4.2', 4.2, sum(counts.values()) / len(counts))
chk('Bursts Dec 1996 – Jun 1997 = 10', 10, len(DG['wwb_dec96_jun97']), ok=len(DG['wwb_dec96_jun97']) == 10)
late = [w for w in MS['wwb'] if '1997-08-01' <= w['start'] <= '1997-12-31']
chk('Seven bursts Aug–Dec 1997', 7, len(late), ok=len(late) == 7)
chk('Aug–Dec 1997 bursts mostly east of 160°E', '>= 4 of 7', sum(w['peak_lon'] >= 160 for w in late), ok=sum(w['peak_lon'] >= 160 for w in late) >= 4)
for d, q in (('1996-12-25', 2.7), ('1997-03-13', 2.75), ('1997-03-28', 3.31)):
    chk(f'OMI on {d} (2.7–3.3)', q, omi[d], tol=0.06)
chk('OMI 13 Apr 1997 = 2.0', 2.0, omi['1997-04-13'], tol=0.06)
eo = DG['omi_episodes_onset']
chk('OMI ≥1 episodes Oct 1996 – Jun 1997 (3, max 2.8/3.39/3.03)', '3', len(eo), ok=len(eo) == 3)
et = DG['omi_episodes_termination'][0]
chk('OMI ≥1 30 Apr – 31 May 1998, max 2.24', 2.24, et['max'], ok=et['start'] == '1998-04-30' and et['end'] == '1998-05-31' and abs(et['max'] - 2.24) < 0.01)
r = DG['olr_io_wp_var_rank_1996_97']
chk('Intraseasonal OLR variance 60E–150E, 1996–97 rank 1 of 22', '1/22', f'{r[0]}/{r[1]}', ok=r[:2] == [1, 22])
chk('22-season mean of that variance 233', 233, r[2], tol=0.6)
chk('Days circulation index ≥1: 1996–97 vs 1981–82', '137/77', f"{DG['mjo_days_1996_97']}/{DG['mjo_days_1981_82']}", ok=(DG['mjo_days_1996_97'], DG['mjo_days_1981_82']) == (137, 77))

w = max(len(r_[0]) for r_ in rows)
bad = 0
for c_, q, val, st in rows:
    print(f'{c_:<{w}} | {q} | {val} | {st}')
    bad += st == 'CHECK'
print(f'\n{len(rows)} checks, {bad} to check')
sys.exit(1 if bad else 0)
