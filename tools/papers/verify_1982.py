"""Stage-5 check for Paper 1: recompute every data-derived number quoted in the prose from the source files.
Prints CLAIM | QUOTED | RECOMPUTED | OK/CHECK.  Run: python3 tools/papers/verify_1982.py"""
import csv, json
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[2] / 'data'
def load(f, key):
    return {r[key]: r for r in csv.DictReader(open(R / f, encoding='utf-8'))}
oni, sm, at, sub, dr = load('oni.csv', 'centre_month'), load('sst_monthly.csv', 'month'), load('atmosphere_monthly.csv', 'month'), load('enso_subsurface.csv', 'month'), load('drivers_monthly.csv', 'month')
io = load('papers/1982/io_monthly.csv', 'month')
mj = json.load(open(R / 'papers/1982/mjo_summary.json')); pt = json.load(open(R / 'papers/1982/propagation_tests.json'))
f = lambda d, k, c: float(d[k][c]) if d.get(k, {}).get(c) not in (None, '') else np.nan
rows = []
def chk(claim, quoted, val, ok=None):
    ok = (abs(float(quoted) - float(val)) < 0.051 if ok is None else ok) if not isinstance(val, str) else ok
    rows.append((claim, quoted, val, 'OK' if ok else 'CHECK'))
ms = lambda y0, m0, y1, m1: [f'{y}-{m:02d}' for y in range(y0, y1 + 1) for m in range(1, 13) if (y, m) >= (y0, m0) and (y, m) <= (y1, m1)]
# ENSO indices
chk('RONI DJF 1983 peak', 2.40, f(oni, '1983-01', 'roni')); chk('ONI DJF 1983', 2.14, f(oni, '1983-01', 'oni'))
allr = {k: float(r['roni']) for k, r in oni.items() if r['roni']}
mx = max(allr, key=allr.get); chk('RONI record max is 1982-83', '1983-01', f'{mx} {allr[mx]}', mx == '1983-01')
top = sorted(((v, k) for k, v in allr.items()), reverse=True)[:6]; rows.append(('RONI top values', '', str(top), 'INFO'))
chk('RONI DJF 1982', 0.11, f(oni, '1982-01', 'roni')); chk('ONI DJF 1982', -0.05, f(oni, '1982-01', 'oni'))
r81 = [f(oni, k, 'roni') for k in ms(1981, 1, 1981, 12)]; chk('RONI 1981 range -0.3..0.0', '-0.3..0.0', f'{min(r81)}..{max(r81)}', min(r81) >= -0.35 and max(r81) <= 0.05)
chk('RONI FMA 1982', 0.23, f(oni, '1982-03', 'roni')); chk('RONI AMJ 1982', 0.74, f(oni, '1982-05', 'roni')); chk('RONI JAS 1982', 1.14, f(oni, '1982-08', 'roni'))
chk('RONI MAM 1982 (< +0.5 until MAM)', '<0.5 before MAM', f"JFM {f(oni,'1982-02','roni')} FMA {f(oni,'1982-03','roni')} MAM {f(oni,'1982-04','roni')}", f(oni, '1982-03', 'roni') < 0.5)
# subsurface
w81 = [f(sub, k, 'wwv_anom') for k in ms(1981, 1, 1981, 12)]; chk('WWV 1981 all positive, +0.6..+2.1', '0.6..2.1', f'{min(w81)}..{max(w81)}', min(w81) > 0 and abs(min(w81) - 0.6) < 0.06 and abs(max(w81) - 2.1) < 0.06)
chk('WWV Mar 1982', 2.15, f(sub, '1982-03', 'wwv_anom'))
w = np.array([f(sub, k, 'wwv_anom') for k in sub if '1980-01' <= k <= '2025-12' and sub[k]['wwv_anom']])
chk('WWV Mar 1982 percentile 1980-2025', 96, round(100 * (w < 2.15).mean(), 1), abs(100 * (w < 2.15).mean() - 96) < 1)
chk('WWV Mar 1982 z', 1.5, round((2.15 - w.mean()) / w.std(), 2), abs((2.15 - w.mean()) / w.std() - 1.5) < 0.1)
chk('Heat 180-100W Jan 1982', 0.2, f(sub, '1982-01', 'heat_180_100w'))
chk('Heat 180-100W Mar 1982', 0.9, f(sub, '1982-03', 'heat_180_100w'), abs(f(sub, '1982-03', 'heat_180_100w') - 0.9) < 0.06)
rows.append(('WWV Dec82/Jan83/Feb83 (fell to +1.4)', 1.4, [f(sub, k, 'wwv_anom') for k in ('1982-11', '1982-12', '1983-01', '1983-02')], 'INFO'))
# atmosphere and SST
tw = [f(at, k, 'trades_west') for k in ms(1982, 2, 1982, 4)]; chk('W Pac trades Feb-Apr 1982 -0.6..-1.3', '-1.3..-0.6', f'{min(tw)}..{max(tw)}', abs(min(tw) + 1.3) < 0.06 and abs(max(tw) + 0.6) < 0.06)
n12 = [f(sm, k, 'nino12') for k in ms(1982, 2, 1982, 4)]; chk('Nino1+2 Feb-Apr 1982 -1.4..-0.7', '-1.4..-0.7', f'{min(n12)}..{max(n12)}', abs(min(n12) + 1.4) < 0.06 and abs(max(n12) + 0.7) < 0.06)
chk('rel Nino3.4 ERSSTv6 Jun 1982', 1.12, f(sm, '1982-06', 'rel_ersst_nino34')); chk('SOI Jun 1982', -1.0, f(at, '1982-06', 'soi'))
chk('C Pac OLR Aug 1982', -21, f(at, '1982-08', 'olr_central_pac'), abs(f(at, '1982-08', 'olr_central_pac') + 21) < 0.6)
chk('C Pac trades Sep 1982', -2.0, f(at, '1982-09', 'trades_central'))
chk('SOI Jan 1983', -3.5, f(at, '1983-01', 'soi')); chk('C Pac OLR Jan 1983', -46, f(at, '1983-01', 'olr_central_pac'), abs(f(at, '1983-01', 'olr_central_pac') + 46) < 0.6)
chk('Nino1+2 Jun 1983', 4.0, f(sm, '1983-06', 'nino12'))
tna = [f(dr, k, 'tna') for k in ms(1982, 8, 1982, 12)]; rows.append(('TNA Aug-Dec 1982 (cooled 0.5-0.9)', '-0.9..-0.5', tna, 'INFO'))
# Indian Ocean
se = {k: float(io[k]['setio']) for k in ms(1982, 1, 1982, 8)}; rows.append(('SETIO Jan-Aug 1982 (0.3-0.5 cool from Feb)', '-0.5..-0.3', se, 'INFO'))
d = {k: float(io[k]['dmi']) for k in ms(1982, 8, 1982, 12)}; chk('DMI ERSSTv5 peak Oct 1982 +1.04', 1.04, max(d.values()), max(d, key=d.get) == '1982-10' and abs(max(d.values()) - 1.04) < 0.006)
dc = {k: f(dr, k, 'dmi_cpc') for k in ms(1982, 8, 1982, 12)}; rows.append(('DMI CPC Aug-Dec 1982 (peak +0.92)', 0.92, dc, 'INFO'))
ue = {k: float(io[k]['u_eqio_70_90E']) for k in ms(1982, 5, 1982, 12)}; rows.append(('Eq IO u Jul-Nov (easterlies Jul-Aug; -2.5..-3.1 Oct-Nov)', '', ue, 'INFO'))
ios = json.load(open(R / 'papers/1982/io_summary.json'))['y1982']; chk('SON DMI 1982', 0.58, ios['dmi_SON']); chk('SON DMI predicted', 0.61, ios['dmi_expected'])
# reanalysis diagnostics
idx = list(csv.DictReader(open(R / 'papers/1982/psl_mjo_indices_1981_83.csv'))); bom = list(csv.DictReader(open(R / 'papers/1982/bom_rmm_1981_83.csv')))
y = {r['year']: r['wwb_count'] for r in mj['wwb_yearly']}; c = list(y.values())
chk('WWB 1982 count', 13, y[1982]); chk('WWB 1979-2001 mean', 4.2, round(np.mean(c), 2), abs(np.mean(c) - 4.2) < 0.051); chk('WWB range 0-16, 1997=16', '0-16', f'{min(c)}-{max(c)} 1997={y[1997]}', min(c) == 0 and max(c) == 16 and y[1997] == 16)
ma = [b for b in mj['wwb'] if b['start'] == '1982-03-28'][0]; chk('Mar burst +12 at 147.5-165E, 28 Mar-3 Apr', 12.0, ma['peak_anom'], ma['peak_anom'] == 12.0 and ma['lon_w'] == 147.5 and ma['lon_e'] == 165 and ma['end'] == '1982-04-03')
aug = [(b['start'], b['end']) for b in mj['wwb'] if b['start'][:7] == '1982-08']; chk('Aug bursts 21-25 Aug and 27 Aug-3 Sep', '21-25 Aug; 27 Aug-3 Sep', aug, aug == [('1982-08-21', '1982-08-25'), ('1982-08-27', '1982-09-03')])
bm = {r['date']: float(r['amplitude']) for r in bom}; v = [bm[f'1982-05-{d:02d}'] for d in range(6, 15)]
chk('RMM 6-14 May 0.6-1.2, 1.8 on 16 May', '0.6-1.2; 1.8', f'{min(v):.2f}-{max(v):.2f}; {bm["1982-05-16"]:.2f}', round(min(v), 1) == 0.6 and round(max(v), 1) == 1.2 and round(bm['1982-05-16'], 1) == 1.8)
od = [b for b in mj['wwb'] if b['start'] >= '1982-10']; rows.append(('Oct-Dec bursts prev-60-day mean u (up to +5)', 5, [(b['start'], b['u1000_prev60d_mean']) for b in od], 'INFO'))
def mx(rows_, col, a, b): v = [float(r[col]) for r in rows_ if a <= r['date'] <= b and r.get(col) not in ('', None)]; return max(v) if v else None
rows.append(('BOM RMM columns', '', list(bom[0].keys()), 'INFO'))
chk('OMI max Nov-Dec 1981', 2.3, mx(idx, 'omi_amp', '1981-11-01', '1981-12-31'))
chk('OMI max during 6-16 May burst (up to 2.3)', 2.3, mx(idx, 'omi_amp', '1982-05-06', '1982-05-16'))
br = pt['base_rates_45d_windows_1981_1983']; chk('Base rates 53% / 20% of 837 windows', '53/20/837', f"{br['T1_T2_T4_pct']}/{br['all_four_pct']}/{br['windows']}", (br['T1_T2_T4_pct'], br['all_four_pct'], br['windows']) == (53.0, 20.0, 837))
sea = mj['seasons']; v = sorted((s['olr_20_100_var_60E_150E'], s['season']) for s in sea); rk = [i + 1 for i, x in enumerate(v) if x[1] == '1982-83'][0]; chk('IO-MC OLR var 1982-83 2nd lowest of 22', '2 of 22', f'{rk} of {len(v)}', (rk, len(v)) == (2, 22))
for r in rows: print(' | '.join(str(x) for x in r))
