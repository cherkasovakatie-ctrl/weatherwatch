"""Stage-5 check for Paper 3: recompute the data-derived numbers quoted in the 2015–16 paper from the source files.
Prints CLAIM | QUOTED | RECOMPUTED | OK/CHECK; exits non-zero if any fails. Run: python3 tools/papers/verify_2015.py"""
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
DG = json.load(open(R / 'papers/2015/diag_2015.json'))
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


chk('RONI JJA 2013', -0.48, v(oni, '2013-07', 'roni'))
rng('RONI ASO 2013 – DJF 2014 (−0.43..−0.22)', -0.43, -0.22, [v(oni, k, 'roni') for k in months('2013-10', '2014-01')])
rng('WWV Jul 2013 – Feb 2014', 0.78, 1.25, [v(sub, k, 'wwv_anom') for k in months('2013-07', '2014-02')], tol=0.01)
chk('Heat Jan 2014', -0.33, v(sub, '2014-01', 'heat_180_100w'))
chk('Heat Mar 2014', 1.60, v(sub, '2014-03', 'heat_180_100w'))
chk('WWV Mar 2014 peak 2.05', 2.05, v(sub, '2014-03', 'wwv_anom'))
chk('WWV Mar 2014 is max of 2014', '2014-03', max(months('2014-01', '2014-12'), key=lambda k: v(sub, k, 'wwv_anom')),
    ok=max(months('2014-01', '2014-12'), key=lambda k: v(sub, k, 'wwv_anom')) == '2014-03')
chk('RONI AMJ 2014', 0.15, v(oni, '2014-05', 'roni'))
chk('RONI JJA 2014', -0.14, v(oni, '2014-07', 'roni'))
chk('WWV Aug 2014', 1.49, v(sub, '2014-08', 'wwv_anom'))
chk('WWV Sep 2014', 1.57, v(sub, '2014-09', 'wwv_anom'))
chk('RONI NDJ 2014-15', 0.62, v(oni, '2014-12', 'roni'))
first_oni = next(k for k in months('2014-06', '2015-06') if v(oni, k, 'oni') >= 0.5)
chk('ONI ≥ 0.5 from SON 2014', 'SON 2014', oni[first_oni]['season'], ok=oni[first_oni]['season'] == 'SON 2014')
chk('PDO Dec 2014', 1.86, v(dr, '2014-12', 'pdo'))
chk('W Pac trades Mar 2015', -1.8, v(at, '2015-03', 'trades_west'))
chk('C Pac OLR Mar 2015', -18.8, v(at, '2015-03', 'olr_central_pac'))
rng('WWV Jan–May 2015', 0.31, 1.25, [v(sub, k, 'wwv_anom') for k in months('2015-01', '2015-05')], tol=0.01)
for k, q in (('2015-05', 0.89), ('2015-06', 1.02), ('2015-07', 1.27), ('2015-10', 2.03), ('2015-11', 2.18), ('2015-12', 2.25), ('2016-02', 1.81),
             ('2016-05', 0.08), ('2016-06', -0.43)):
    chk(f'RONI {oni[k]["season"]}', q, v(oni, k, 'roni'))
chk('ONI NDJ 2015-16', 2.59, v(oni, '2015-12', 'oni'))
chk('RONI peak season NDJ 2015', 'NDJ 2015', oni[max(months('2015-01', '2016-06'), key=lambda k: v(oni, k, 'roni'))]['season'],
    ok=max(months('2015-01', '2016-06'), key=lambda k: v(oni, k, 'roni')) == '2015-12')
chk('ONI − RONI at peak 0.34', 0.34, round(v(oni, '2015-12', 'oni') - v(oni, '2015-12', 'roni'), 2), tol=0.006)
rng('SOI May–Jul 2015', -1.1, -0.6, [v(at, k, 'soi') for k in months('2015-05', '2015-07')])
for k, q in (('2015-05', 1.34), ('2015-06', 1.91), ('2015-07', 2.48)):
    chk(f'Niño 1+2 {k}', q, v(sm, k, 'nino12'))
chk('Niño 4 Nov 2015 1.55 (record in table)', 1.55, v(sm, '2015-11', 'nino4'))
chk('C Pac OLR Dec 2015', -49.9, v(at, '2015-12', 'olr_central_pac'))
chk('WWV Dec 2015', -0.39, v(sub, '2015-12', 'wwv_anom'))
chk('WWV Apr 2016 (−3.36)', -3.36, v(sub, '2016-04', 'wwv_anom'))
rng('WWV Jan–May 2016 (−3.36..−1.26)', -3.36, -1.26, [v(sub, k, 'wwv_anom') for k in months('2016-01', '2016-05')])
mn = min(months('2016-06', '2016-12'), key=lambda k: v(oni, k, 'roni'))
chk('RONI 2016 La Niña minimum −0.96 (SON/OND)', -0.96, v(oni, mn, 'roni'))
chk('DMI Jul 2016', -0.89, v(dr, '2016-07', 'dmi_cpc'))
rng('DMI Aug–Oct 2015', 0.42, 0.47, [v(dr, k, 'dmi_cpc') for k in months('2015-08', '2015-10')])
# diagnostics
chk('Bursts 2015 = 17, most of 1979–2016', 17, DG['wwb_count']['2015'], ok=DG['wwb_count']['2015'] == 17 and DG['wwb_max_year_1979_2016'] == 2015)
chk('Bursts 2014 = 3', 3, DG['wwb_count']['2014'], ok=DG['wwb_count']['2014'] == 3)
chk('Bursts 1997 = 16 (same as Paper 2)', 16, DG['wwb_count']['1997'], ok=DG['wwb_count']['1997'] == 16)
b14 = [w for w in DG['wwb'] if w['start'][:4] == '2014']
chk('No bursts Apr–Jun 2014', 0, sum('2014-04' <= w['start'] < '2014-07' for w in b14), ok=sum('2014-04' <= w['start'] < '2014-07' for w in b14) == 0)
chk('Basin-mean minimum 11 Jun 2014 −1.94, 5th lowest', '-1.94/5', f"{DG['basin_mean_min_jun_jul_2014'][1]}/{DG['basin_mean_rank_of_that_day']}",
    ok=DG['basin_mean_min_jun_jul_2014'] == ['2014-06-11', -1.94] and DG['basin_mean_rank_of_that_day'] == 5)
s = DG['seasons']
chk('OLR var 160E–150W 2015-16 vs 1996-97 ratio ~1.8 ("nearly twice")', 1.83, round(s['2015-16']['olr_20_100_var_160E_150W'] / s['1996-97']['olr_20_100_var_160E_150W'], 2), tol=0.1)
kw = DG['tao_kelvin_waves_2015'][0]
chk('Mar 2015 Kelvin wave 32 days, 3.4 m/s', 3.4, kw['speed_ms'], tol=0.06)
w = max(len(r[0]) for r in rows)
bad = 0
for r in rows:
    print(f'{r[0]:<{w}} | {r[1]} | {r[2]} | {r[3]}')
    bad += r[3] == 'CHECK'
print(f'\n{len(rows)} checks, {bad} to check')
sys.exit(1 if bad else 0)
