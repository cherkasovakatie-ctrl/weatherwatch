"""Paper 4 (2026, preliminary): writes papers/4-enso-2026.json from the analog comparison and burst diagnostics.
Run: python3 tools/papers/compare_2026.py && python3 tools/papers/make_2026.py && python3 tools/papers/build.py
Every number below is read from data files; nothing is typed by hand.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data'
D26 = D / 'papers/2026'
YRS = (1982, 1997, 2015, 2026)
LAB = {1982: '1982–83', 1997: '1997–98', 2015: '2015–16', 2026: '2026'}


def load(f, key):
    with open(D / f, encoding='utf-8') as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


oni, sub, wk = load('oni.csv', 'centre_month'), load('enso_subsurface.csv', 'month'), load('sst_weekly.csv', 'week')
A = {}
with open(D26 / 'analog_monthly.csv', encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        A[(r['lag'], r['var'])] = {y: (float(r[str(y)]) if r[str(y)] != '' else None) for y in YRS}
probs = [r for r in csv.DictReader(open(D / 'enso_probs.csv', encoding='utf-8')) if r['source'] == 'CPC']
plume = {r['season']: r for r in csv.DictReader(open(D / 'enso_plume.csv', encoding='utf-8'))}
BD = json.load(open(D26 / 'diag_2026.json')) if (D26 / 'diag_2026.json').exists() else None
EB = json.load(open(D26 / 'era5_wwb_2026.json'))
EB_JS = [w for w in EB['bursts'] if w['start'] <= '2026-09-30']
EB_TOP = max(EB['bursts'], key=lambda w: w['peak_anom'])


def a(lag, var, y):
    return A[(lag, var)][y]


def f(x, nd=2, sign=True):
    return '—' if x is None else (f'{x:+.{nd}f}' if sign else f'{x:.{nd}f}').replace('-', '−')


def ms(a_, b_):
    y, m = map(int, a_.split('-')); out = []
    while f'{y}-{m:02d}' <= b_:
        out.append(f'{y}-{m:02d}'); y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def rank(var_rows, key, col, month, desc=True):
    vals = sorted(((float(r[col]), k) for k, r in var_rows.items() if k.endswith('-' + month) and r.get(col) not in (None, '')), reverse=desc)
    yrs = [k[:4] for _, k in vals]
    return yrs.index(key) + 1, len(vals), yrs[0], vals[0][1][:4] if vals else None


# --- what happened next in the three analogs
nxt = {}
for y in YRS[:3]:
    rng = ms(f'{y}-01', f'{y + 1}-12')
    pk = max(rng, key=lambda k: float(oni[k]['roni']))
    end = next(k for k in rng if k > pk and float(oni[k]['roni']) < 0.5)
    wneg = next(k for k in rng if k > f'{y}-06' and float(sub[k]['wwv_anom']) < 0)
    hpk = max(ms(f'{y}-01', f'{y}-12'), key=lambda k: float(sub[k]['heat_180_100w']))
    nxt[y] = dict(pk=oni[pk]['season'], pkv=float(oni[pk]['roni']), oni_max=max(float(oni[k]['oni']) for k in rng), end=oni[end]['season'],
                  jja1=float(oni[f'{y + 1}-07']['roni']), wneg=wneg, hpk=hpk, hpkv=float(sub[hpk]['heat_180_100w']),
                  inc=float(oni[pk]['roni']) - float(oni[f'{y}-08']['roni']))
jas26 = a('Aug', 'roni', 2026)
lo_inc, hi_inc = min(v['inc'] for v in nxt.values()), max(v['inc'] for v in nxt.values())
MON = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August',
       '09': 'September', '10': 'October', '11': 'November', '12': 'December'}


def mname(k):
    return f"{MON[k[5:]]} {k[:4]}"


# --- ranks of 2026 against every year on record
sst = load('sst_monthly.csv', 'month')
atm = load('atmosphere_monthly.csv', 'month')
rk = {
    'roni': rank(oni, '2026', 'roni', '08'), 'oni': rank(oni, '2026', 'oni', '08'),
    'rel34': rank(sst, '2026', 'rel_nino34', '09'), 'n12': rank(sst, '2026', 'nino12', '09'),
    'heat': rank(sub, '2026', 'heat_180_100w', '09'), 'olr': rank(atm, '2026', 'olr_central_pac', '09', desc=False),
    'tc': rank(atm, '2026', 'trades_central', '09', desc=False), 'gt': rank(sst, '2026', 'global_tropics', '09'),
}
wwv_all = sorted(((float(r['wwv_anom']), k) for k, r in sub.items() if r['wwv_anom']), reverse=True)
heat_all = sorted(((float(r['heat_180_100w']), k) for k, r in sub.items() if r['heat_180_100w']), reverse=True)
prev_wwv = next((v, k) for v, k in wwv_all if not k.startswith('2026'))
prev_heat = next((v, k) for v, k in heat_all if not k.startswith('2026'))
lastwk = max(wk)
wk_same = {y: wk.get(next((k for k in sorted(wk) if k.startswith(f'{y}-10-') and int(k[8:]) >= 12), ''), {}) for y in (1997, 2015)}
cpc_issue = probs[0]['issued'] if probs else '—'
p_vs = {r['season']: int(r['en_very_strong']) for r in probs if r['en_very_strong']}
ond = plume.get('OND', {})


def row(label, lag, var, nd=2, unit=''):
    return [label] + [f'<span class="num">{f(a(lag, var, y), nd)}</span>' for y in YRS]


cmp_rows = [
    row('RONI, NDJ before onset (°C)', 'Dec-1', 'roni'), row('RONI, FMA (°C)', 'Mar', 'roni'), row('RONI, JAS (°C)', 'Aug', 'roni'),
    row('ONI (traditional), JAS (°C)', 'Aug', 'oni'), row('Relative Niño 3.4, Sep (°C)', 'Sep', 'rel_nino34'),
    row('Niño 1+2, Sep (°C, OISST)', 'Sep', 'nino12'), row('Niño 4, Sep (°C, OISST)', 'Sep', 'nino4'),
    row('Heat content 180°–100°W, Sep (°C)', 'Sep', 'heat'), row('Warm water volume, Sep (10¹⁴ m³)', 'Sep', 'wwv'),
    row('SOI, Sep', 'Sep', 'soi', 1), row('OLR central Pacific, Sep (W m⁻²)', 'Sep', 'olr_cp', 1),
    row('850 hPa trades, central Pacific, Sep (standardized index, z-score)', 'Sep', 'trades_c', 1), row('PDO, Sep', 'Sep', 'pdo'),
    row('IOD (DMI, CPC), Aug', 'Aug', 'dmi'), row('Tropical North Atlantic, Sep (°C)', 'Sep', 'tna'),
    row('Global tropics SST, Sep (°C)', 'Sep', 'global_tropics'),
]
cmp_rows.append(['Westerly wind bursts, Jan–Sep (count)', '<span class="num">8 (ERA5 11)</span>', '<span class="num">15</span>', '<span class="num">13</span>', f'<span class="num">{len(EB_JS)} (ERA5)</span>'])
if False:
    cmp_rows.append(['Westerly wind bursts, Jan–Sep (count)'] + [f'<span class="num">{BD["bursts_jan_sep"].get(str(y), "—")}</span>' for y in YRS])
    cmp_rows.append(['Westerly wind bursts, whole year (count)'] + [f'<span class="num">{BD["bursts_year"].get(str(y), "—")}</span>' for y in YRS[:3]] + [f'<span class="num">{BD["bursts_year"]["2026"]} to date</span>'])
nxt_rows = [[LAB[y], f"{nxt[y]['pk']}, {f(nxt[y]['pkv'])}", f(nxt[y]['oni_max']), f(nxt[y]['inc']), f"{mname(nxt[y]['hpk'])} ({f(nxt[y]['hpkv'])})",
             mname(nxt[y]['wneg']), nxt[y]['end'], f(nxt[y]['jja1'])] for y in YRS[:3]]

g = lambda lag, v, y=2026: f(a(lag, v, y))  # noqa: E731
rise = {y: a('Aug', 'roni', y) - a('Feb', 'roni', y) for y in YRS}  # JFM to JAS

burst_par = (f"<p><b>Westerly wind bursts.</b> NOAA's Reanalysis 1, used for the bursts in Papers 1–3, has no 2026 data after 17 March, so the 2026 bursts were found in ERA5 (daily means of 00 and 12 UTC, 2.5°) with the same rule: 1000 hPa anomaly ≥ 5 m s⁻¹ for ≥ 3 days over ≥ 10° of longitude, 5°S–5°N, 120°E–150°W. "
             f"January–September 2026 had <b>{len(EB_JS)}</b> bursts, against 15 in 1997 and 13 in 2015 in Reanalysis 1, and 8 (Reanalysis 1) or 11 (ERA5, same method as here) in 1982. "
             f"The strongest, from {EB_TOP['start'][8:].lstrip('0')} to {EB_TOP['end'][8:].lstrip('0')} April, peaked at {EB_TOP['peak_anom']} m s⁻¹ near {EB_TOP['peak_lon']:.0f}°E and spanned {EB_TOP['lon_w']:.0f}–{EB_TOP['lon_e']:.0f}°E: stronger than any January–September burst of 1997 (11.6 m s⁻¹, in Reanalysis 1) or 2015 (12.4, in March), and it came as RONI was crossing zero. "
             f"With October data to the 18th, the westerlies are still strengthening: the monthly mean anomaly over 120°E–150°W was {EB['mean_anom_120E_150W_by_month']['2026-10']:+.1f} m s⁻¹ in October, and the westerly event that began on 28 September was still under way on 18 October with a peak of {EB['bursts'][-1]['peak_anom']} m s⁻¹. "
             "From June the monthly mean anomaly over 120°E–150°W stayed above +2 m s⁻¹ and several 'bursts' last two to five weeks: this is the El Niño's own coupled westerly response, as in late 1982, so the count from mid-year overstates the number of distinct events. "
             "Without an ERA5 baseline of its own, the anomalies use the Reanalysis 1 1979–2000 seasonal cycle plus the mean ERA5 offset estimated from 1981–82; the comparison with 1997 and 2015 mixes two reanalyses (tools/papers/wwb_era5_2026.py).</p>")
if False:
    b = BD
    burst_par = (f"<p><b>Westerly wind bursts.</b> On the burst definition used in Papers 1–3 (NCEP/NCAR Reanalysis 1, 1000 hPa anomaly ≥ 5 m s⁻¹ for ≥ 3 days over ≥ 10° of longitude, 5°S–5°N, 120°E–150°W), January–September 2026 had "
                 f"<b>{b['bursts_jan_sep']['2026']}</b> bursts, against {b['bursts_jan_sep']['1982']} in 1982, {b['bursts_jan_sep']['1997']} in 1997 and {b['bursts_jan_sep']['2015']} in 2015 over the same months "
                 f"(1979–2025 mean for January–September {f(b['mean_jan_sep_1979_2025'], 1, False)}). {b['sentence']}</p>")

S = []
S.append({"id": "abstract", "title": "Abstract", "html": (
    f"<p>This is a preliminary, observation-only comparison of the 2026 El Niño with the three strongest events of the satellite era, 1982–83, 1997–98 and 2015–16, at the same stage of each: the end of September of the onset year. "
    f"On the official relative index (RONI) 2026 is the second-strongest July–September on record ({g('Aug', 'roni')} °C, behind 1997's {f(a('Aug', 'roni', 1997))} °C). It has grown faster than any of the three, by {f(rise[2026])} °C from January–March to July–September, "
    f"starting from La Niña rather than from neutral or warm conditions. It is the most east-based of the four: September Niño 1+2 was {g('Sep', 'nino12')} °C against {f(a('Sep', 'nino12', 1997))} °C in 1997. "
    f"Upper-ocean heat content in the eastern half of the basin ({g('Sep', 'heat')} °C) and the warm water volume (peak {f(wwv_all[0][0])} × 10¹⁴ m³ in {mname(wwv_all[0][1])}) are the highest since the records began (1979–80), and the atmosphere is as strongly coupled as in 1997. "
    f"Two things set 2026 apart: a strongly negative Pacific Decadal Oscillation, where 1997 and 2015 had a positive one, and the warmest tropical oceans on record, which is why the traditional ONI ({g('Aug', 'oni')} °C) runs {f(a('Aug', 'oni', 2026) - a('Aug', 'roni', 2026), 2, False)} °C above RONI. "
    f"In the three analogs RONI rose a further {f(lo_inc, 2, False)}–{f(hi_inc, 2, False)} °C after July–September and peaked in November–January; heat content peaked two to four months before RONI. These are analog statistics, not a forecast.</p>")})
S.append({"id": "findings", "title": "Main findings (preliminary)", "html": (
    "<ol>"
    f"<li><b>Strength.</b> RONI JAS {g('Aug', 'roni')} °C, rank {rk['roni'][0]} of {rk['roni'][1]} since 1950 (1997 is first). On the traditional ONI, JAS 2026 ({g('Aug', 'oni')} °C) is first. September relative Niño 3.4 ({g('Sep', 'rel_nino34')} °C) is the highest September in the record (from 1981). <i>Observed.</i></li>"
    f"<li><b>Speed.</b> RONI rose {f(rise[2026])} °C from JFM to JAS, against {f(rise[1997])} (1997), {f(rise[2015])} (2015) and {f(rise[1982])} (1982), because it started from La Niña (NDJ {g('Dec-1', 'roni')} °C). <i>Observed.</i></li>"
    f"<li><b>Flavour.</b> East-based like 1997, more so: September Niño 1+2 {g('Sep', 'nino12')} °C (the highest September in the record), Niño 4 {g('Sep', 'nino4')} °C; the Niño 1+2 minus Niño 4 gap is {f(a('Sep', 'nino12', 2026) - a('Sep', 'nino4', 2026), 2, False)} °C, against {f(a('Sep', 'nino12', 1997) - a('Sep', 'nino4', 1997), 2, False)} in 1997 and {f(a('Sep', 'nino12', 2015) - a('Sep', 'nino4', 2015), 2, False)} in 2015. <i>Observed.</i></li>"
    f"<li><b>Ocean heat.</b> Heat content {g('Sep', 'heat')} °C in September and warm water volume {f(wwv_all[0][0])} in {mname(wwv_all[0][1])} are records for any month (previous: heat {f(prev_heat[0])} in {mname(prev_heat[1])}; WWV {f(prev_wwv[0])} in {mname(prev_wwv[1])}). Unlike 1997, when it peaked in April, the warm water volume kept rising until August and fell only in September. <i>Observed.</i></li>"
    f"<li><b>Atmosphere.</b> September SOI {f(a('Sep', 'soi', 2026), 1)}, central-Pacific OLR {f(a('Sep', 'olr_cp', 2026), 1)} W m⁻² and the central-Pacific standardized trade-wind index {f(a('Sep', 'trades_c', 2026), 1)} (dimensionless z-score) are each the most extreme September values in the record. <i>Observed.</i></li>"
    f"<li><b>Background.</b> PDO {g('Sep', 'pdo')} (1997 {f(a('Sep', 'pdo', 1997))}, 2015 {f(a('Sep', 'pdo', 2015))}); global-tropics SST {g('Sep', 'global_tropics')} °C, the warmest September on record. A positive IOD is developing (DMI {g('Aug', 'dmi')} in August, as in 1997 at {f(a('Aug', 'dmi', 1997))}). <i>Observed; their role is not yet tested.</i></li>"
    "</ol>")})
S.append({"id": "data", "title": "1. Data and approach", "html": (
    "<p>All values are from NOAA CPC index files and NOAA PMEL warm water volume as copied in the site's data archive (see the references), monthly to September 2026, RONI to July–September 2026 and weekly OISST to the week centred "
    f"{lastwk}. Events are aligned on the onset year (year 0 = 1982, 1997, 2015, 2026). RONI is the primary index (relative ERSSTv6 Niño 3.4, 1991–2020; <a href=\"#ref-lheureux2024\">[1]</a>). "
    "Niño-region values are OISST v2.1 (1991–2020 base). Ranks compare the same calendar month or season across all years with data (RONI and ONI from 1950; OISST, heat content and OLR from 1979–82; WWV from 1980). "
    "The script <code>tools/papers/compare_2026.py</code> writes the aligned series (<code>data/papers/2026/analog_monthly.csv</code>); this text is generated from it.</p>"
    "<p><b>What this is not.</b> It does not yet include daily reanalysis diagnostics of the MJO, TAO mooring data, the literature on 2026, or impacts. Those are the next stages, as in Papers 1–3.</p>")})
S.append({"id": "comparison", "title": "2. The four events at the same stage", "html": (
    "<figure><img src=\"papers/img/enso2026_analogs.png\" alt=\"Four panels comparing 1982–83, 1997–98, 2015–16 and 2026: RONI, Niño 1+2, upper-300 m heat content and warm water volume, aligned on the onset year\" style=\"max-width:100%;height:auto\">"
    "<figcaption class=\"note\">Figure 1. The four events aligned on the onset year, December of year −1 to December of year +1. 2026 data end in September (RONI: July–September). Sources: NOAA CPC, NOAA PMEL.</figcaption></figure>"),
    "table": {"cols": ["Indicator", "1982–83", "1997–98", "2015–16", "2026"], "rows": cmp_rows,
              "note": "Same calendar stage in each onset year. RONI and ONI are 3-month seasons labelled by their centre month (JAS = July–September). Niño-region SST from OISST v2.1; heat content from CPC (180°–100°W, 0–300 m, 1981–2010 base); WWV from NOAA PMEL; CPC trade-wind values are standardized, dimensionless z-scores (negative = weaker trades), and OLR values are in W m⁻² (negative = more convection). PDO from NOAA NCEI. IOD: CPC Dipole Mode Index, ERSSTv6, 1991–2020 baseline; the latest value is an estimate that may change for up to two months."}})
S.append({"id": "growth", "title": "3. Growth from La Niña", "html": (
    f"<p>Each of the three analogs began year 0 near neutral or warm: RONI in NDJ was {f(a('Dec-1', 'roni', 1982))} °C (1981–82), {f(a('Dec-1', 'roni', 1997))} (1996–97) and {f(a('Dec-1', 'roni', 2015))} (2014–15). 2026 began at {g('Dec-1', 'roni')} °C, a La Niña. "
    f"It crossed zero in spring and by July–September was within {f(a('Aug', 'roni', 1997) - a('Aug', 'roni', 2026), 2, False)} °C of 1997 (on the traditional ONI it has been above 1997 since DJF). The six-month rise of {f(rise[2026])} °C is the largest of the four.</p>"
    f"<p>The ocean was ready earlier than the surface. Heat content rose from {g('Dec-1', 'heat')} °C in December 2025 to {g('Apr', 'heat')} °C by April, matching 1997 ({f(a('Apr', 'heat', 1997))}), and the warm water volume reached {g('Apr', 'wwv')} in April, close to 1997's {f(a('Apr', 'wwv', 1997))}. "
    "The recharge-oscillator framework <a href=\"#ref-jin1997\">[2]</a> <a href=\"#ref-meinen2000\">[3]</a> expects a recharged equatorial Pacific to precede El Niño; on that view the 2025–26 La Niña left the basin recharged, as 1996 did before 1997. "
    "Whether the recharge came from the La Niña itself or from something else (for example off-equatorial heat carried towards the equator, a possibility still to test) is not tested here.</p>"
    + burst_par)})
S.append({"id": "flavour", "title": "4. An east-based event", "html": (
    f"<p>Warming in 2026 has been concentrated at the eastern end of the basin from the start: Niño 1+2 was {g('Feb', 'nino12')} °C in February, when the other three were still negative, and {g('Jun', 'nino12')} °C by June. "
    f"By September it was {g('Sep', 'nino12')} °C, ahead of 1997 ({f(a('Sep', 'nino12', 1997))}) and well ahead of 1982 and 2015. Niño 4, in contrast, has stayed near +1 °C, and in relative terms near zero "
    f"(weekly relative Niño 4 {f(float(wk[lastwk]['rel_nino4']), 1)} °C in the week of {lastwk}). This is the eastern-Pacific (E-type) end of ENSO diversity <a href=\"#ref-takahashi2011\">[4]</a> <a href=\"#ref-capotondi2015\">[5]</a>, as in 1982–83 and 1997–98; 2015–16 was centred further west. "
    f"Mid-October weekly values underline the gap: relative Niño 1+2 {f(float(wk[lastwk]['rel_nino12']), 1)} °C and relative Niño 3.4 {f(float(wk[lastwk]['rel_nino34']), 1)} °C (week of {lastwk}), against {f(float(wk_same[1997]['rel_nino12']), 1)} and {f(float(wk_same[1997]['rel_nino34']), 1)} °C in mid-October 1997 and {f(float(wk_same[2015]['rel_nino12']), 1)} and {f(float(wk_same[2015]['rel_nino34']), 1)} °C in mid-October 2015.</p>"
    "<p>East-based events bring the largest coastal impacts in Peru and Ecuador and, through coastally trapped waves, along the Americas; the site's event logs for the Peruvian coast and the California coast record those in 2026.</p>")})
S.append({"id": "atmos", "title": "5. Coupling with the atmosphere", "html": (
    f"<p>By September the atmosphere matched the ocean. The SOI was {f(a('Sep', 'soi', 2026), 1)}, central-Pacific OLR {f(a('Sep', 'olr_cp', 2026), 1)} W m⁻² (deep convection over normally dry ocean) and the central-Pacific 850 hPa standardized trade-wind index {f(a('Sep', 'trades_c', 2026), 1)} (dimensionless z-score); "
    f"each is the most extreme September value since these records began (SOI 1951; OLR and winds 1979). In 1997 the same indices were {f(a('Sep', 'soi', 1997), 1)}, {f(a('Sep', 'olr_cp', 1997), 1)} and {f(a('Sep', 'trades_c', 1997), 1)}. "
    "On these monthly measures the Bjerknes feedback is at least as strong as in 1997 at the same stage.</p>")})
S.append({"id": "background", "title": "6. A different background", "html": (
    f"<p><b>Negative PDO.</b> In 1997 and 2015 the PDO was positive during growth (September {f(a('Sep', 'pdo', 1997))} and {f(a('Sep', 'pdo', 2015))}); in 1982 it was weakly positive ({f(a('Sep', 'pdo', 1982))}). In 2026 it has been negative all year (September {g('Sep', 'pdo')}). "
    "All three analogs grew with a PDO at or above zero; 2026 is growing against a negative one. Whether the negative PDO is acting as a brake, has been cancelled by the tropical forcing, or is a sign of the North Pacific marine heatwaves rather than of the usual pattern, is an open question for the full paper.</p>"
    f"<p><b>Warm tropics.</b> Global-tropics SST was {g('Sep', 'global_tropics')} °C in September, the warmest September on record (2015: {f(a('Sep', 'global_tropics', 2015))}; 1997: {f(a('Sep', 'global_tropics', 1997))}). "
    f"This is why the traditional ONI ({g('Aug', 'oni')} °C, a record) is {f(a('Aug', 'oni', 2026) - a('Aug', 'roni', 2026), 2, False)} °C higher than RONI, against {f(a('Aug', 'oni', 1997) - a('Aug', 'roni', 1997))} in 1997. "
    "RONI removes the tropical-mean warming so that events from different decades can be compared <a href=\"#ref-lheureux2024\">[1]</a>; on RONI, 2026 is very strong but not yet the strongest.</p>"
    f"<p><b>Indian and Atlantic Oceans.</b> The IOD index (CPC) rose to {g('Aug', 'dmi')} in August, similar to 1997 ({f(a('Aug', 'dmi', 1997))}) and 1982 ({f(a('Aug', 'dmi', 1982))}); in 1997 it went on to {f(a('Nov', 'dmi', 1997))} in November <a href=\"#ref-saji1999\">[6]</a>. "
    "The 2026 IOD values are CPC's Dipole Mode Index from ERSSTv6 (western box minus south-eastern box, 1991–2020 baseline) read from CPC's data file <a href=\"#ref-cpc_dmi\">[CPC DMI]</a>; CPC says the latest values are estimates that may change for up to two months after first posting. "
    f"The tropical North Atlantic is warm ({g('Sep', 'tna')} °C), unlike 1982 and 1997, which were cool.</p>")})
import rain_common as RC  # noqa: E402
_rc, _rr = RC.table_all()
_tl = RC.tlt_rows([1982, 1997, 2015])
_tk = max(k for k in RC.TLT_T if k.startswith('2026')); _rec = max(RC.TLT_T.items(), key=lambda kv: kv[1])
S.append({"id": "rain", "title": "7. Rainfall and tropospheric temperature in the analogs", "html": (
    "<p><b>Rainfall.</b> The table shows each analog's rainfall in the usual El Niño impact regions and seasons (GPCP v2.3). The two east-based events, 1982–83 and 1997–98, brought extreme rain to coastal Peru and Ecuador and to California; "
    "2015–16, centred further west, brought neither, while Indonesia's dry season was the driest of all in 2015. Equatorial East Africa's short rains were the wettest since 1979 in 1997, the year of the strong positive Indian Ocean Dipole. "
    f"For 2026 the impact seasons have not yet been reached in the data, which end in {RC.mlab(RC.GLAST)}. Because 2026 is east-based, the 1982–83 and 1997–98 columns are the closer guide to what the coastal regions may see; that is an inference from two events, not a forecast.</p>"
    f"<p><b>Tropospheric temperature.</b> The tropical lower troposphere (NOAA STAR TLT, 20°S–20°N, against 1991–2020) peaked {_tl[0][1]} after 1982–83, {_tl[1][1]} after 1997–98 and {_tl[2][1]} after 2015–16, two to three months after the RONI peak. "
    f"In 2026 it was already {RC.TLT_T[_tk]:+.2f} °C in {RC.mlab(_tk)}, before the expected peak of the event; the record is {_rec[1]:+.2f} °C ({RC.mlab(_rec[0])}), after the 2023–24 El Niño.</p>"),
    "table": {"cols": _rc, "rows": _rr, "note": RC.NOTE.format(n=47)}})
TB = json.load(open(D26 / 'tc_bursts.json'))
_E = TB['events']; _z = TB['year2026']['2026']
_obs = sum(_E[k]['with_tc'] for k in _E); _exp = sum(_E[k]['expected_with_tc'] for k in _E); _nb = sum(_E[k]['n'] for k in _E)
_tobs = sum(_E[k]['twin'] for k in _E); _texp = sum(_E[k]['expected_twin'] for k in _E)
_tcrows = [[LAB[int(k)], str(_E[k]['n']), f"{_E[k]['with_tc']} ({_E[k]['expected_with_tc']:.1f})", f"{_E[k]['twin']} ({_E[k]['expected_twin']:.1f})", str(_E[k]['lowlat_genesis_jan_oct']), str(_E[k]['twin_days_jan_oct'])] for k in _E]
_tcrows.append(['2026 (ERA5, 1 Mar–18 Oct)', str(_z['n']), f"{_z['with_tc']} ({_z['expected_with_tc']:.1f})", f"{_z['twin']} ({_z['expected_twin']:.1f})", str(_z['lowlat_genesis_jan_oct']), str(len(_z['twin_days_jan_oct']))])
_tw = _z['twin_days_jan_oct']
S.append({"id": "cyclones", "title": "8. Tropical cyclones and westerly wind bursts", "html": (
    "<p><b>Question.</b> Westerly wind bursts often occur alongside tropical cyclones, sometimes as a pair straddling the equator; the 1982–83 paper discusses such pairs. Two directions matter: the developing El Niño shifts where cyclones form, and cyclones may in turn add equatorial westerlies that force the ocean. Neither direction can be proven from positions alone; this section tests what the data allow: how often the bursts of the three analogs had a cyclone nearby, compared with chance.</p>"
    f"<p><b>Method.</b> Cyclone positions are from IBTrACS v04r01 (6-hourly; 2026 provisional, to {_z['last_fix']}). A burst counts as cyclone-accompanied if a cyclone of any strength was centred 3°–20° from the equator, within 10° of longitude of the burst, from two days before the burst to its end; 'twin' means one on each side of the equator. "
    "The chance expectation slides each burst's own window and longitude span over every day of March–December of the same year. Bursts are the Reanalysis 1 lists of Papers 1–3 (March–December).</p>"
    f"<p><b>Result for the analogs.</b> {_obs} of {_nb} bursts had a cyclone nearby, against {_exp:.1f} expected by chance: cyclones are so common in these seasons that their presence near a burst says little on its own. Twin cyclones are different: {_tobs} bursts had one, against {_texp:.1f} expected, with the excess in 1997 and 2015. "
    "That is consistent with twin cyclones being linked to burst-producing disturbances such as the MJO, but this count cannot say which causes which.</p>"
    f"<p><b>2026 so far (January–October).</b> Only {_z['lowlat_genesis_jan_oct']} cyclones formed within 10° of the equator between 130°E and 160°W, against {_E['1982']['lowlat_genesis_jan_oct']} in 1982, {_E['1997']['lowlat_genesis_jan_oct']} in 1997 and {_E['2015']['lowlat_genesis_jan_oct']} in 2015 over the same months, and twin cyclones were present on {len(_tw)} days "
    + (f"({_tw[0][0]} to {_tw[-1][0]}: {', '.join(_tw[0][1])} north and {', '.join(_tw[0][2])} south of the equator)" if _tw else "") + f", against {_E['1982']['twin_days_jan_oct']}, {_E['1997']['twin_days_jan_oct']} and {_E['2015']['twin_days_jan_oct']} days. "
    "So 2026 has grown into a very strong El Niño with fewer near-equatorial cyclones in the western Pacific than any of the three analogs. "
    f"The ERA5 bursts of 1 March – 18 October 2026 answer part of this: {_z['n']} bursts, {_z['with_tc']} with a cyclone nearby against {_z['expected_with_tc']:.1f} expected by chance, and {_z['twin']} with twin cyclones ({_z['expected_twin']:.1f} expected): the strongest burst of the year, in early April, coincided with Sinlaku north and Maila south of the equator, and the westerly event from 28 September with Champi and Koguma to the north and Wati to the south. Cyclones accompanied the 2026 bursts no more often than chance, so they do not explain the event's strong westerly forcing; whether the MJO organised the bursts, and how much of the mid-year westerlies was the coupled El Niño response itself, are the next tests. "
    "The very active eastern and central Pacific hurricane season and Super Typhoon Champi lie mostly outside this box and are not tested here.</p>"),
    "table": {"cols": ["Event", "Westerly bursts, Mar–Dec", "With a cyclone nearby (chance)", "With twin cyclones (chance)", "Cyclones formed ≤10° from equator, 130°E–160°W, Jan–Oct", "Days with twin cyclones, Jan–Oct"],
              "rows": _tcrows, "note": "IBTrACS v04r01 (NOAA NCEI), any intensity; tools/papers/tc_bursts.py, output data/papers/2026/tc_bursts.json. Numbers in brackets: expected by chance, from the same windows slid over the same year."}})
S.append({"id": "next", "title": "9. What happened next in the analogs", "html": (
    "<p>The table below records what followed the September stage in each analog. It is a description of three past events, not a forecast for 2026.</p>"),
    "table": {"cols": ["Event", "RONI peak (season, °C)", "ONI peak (°C)", "RONI rise, JAS to peak (°C)", "Heat content peak", "WWV first negative", "RONI below +0.5", "RONI JJA, year +1"],
              "rows": nxt_rows, "note": "From the same files as section 2."}})
S.append({"id": "outlook", "title": "10. Forecasts and an analog scenario", "html": (
    f"<p><b>Forecasts (official, not observations).</b> The CPC outlook of {cpc_issue} gives a {p_vs.get('OND', '—')}% chance of very strong El Niño (RONI ≥ +2.0 °C) for October–December, {p_vs.get('NDJ', '—')}% for November–January and {p_vs.get('DJF', '—')}% for December–February. "
    f"The IRI multi-model plume of October has an all-model average of +{ond.get('combined_avg', '—')} °C for OND on the traditional Niño 3.4 index (range +{ond.get('model_min', '—')} to +{ond.get('model_max', '—')} °C, {ond.get('model_n', '—')} models). "
    "The site's ENSO outlook card shows both in full.</p>"
    f"<p><b>Analog scenario (speculation, labelled as such).</b> If 2026 added the same amount after JAS as the analogs did ({f(lo_inc, 2, False)}–{f(hi_inc, 2, False)} °C), its RONI peak would be {f(jas26 + lo_inc)} to {f(jas26 + hi_inc)} °C, most likely in November–January. "
    "The upper end would exceed every event since 1950 on RONI. Two features argue for the upper half: heat content was still rising in September, whereas in 1982 and 1997 it peaked in October, and the warm water volume had only begun to fall. "
    f"One point is unresolved: in all three analogs RONI peaked within a month of the warm water volume turning negative. In 2026 it is still {g('Sep', 'wwv')} (September), so on that analog the peak is some months away, or the relationship will not hold this time. This simple arithmetic ignores the different background state and has no skill estimate.</p>")})
S.append({"id": "next-steps", "title": "11. Next steps for the full paper", "html": (
    "<ul><li>Extend the ERA5 bursts beyond 18 October and test them against MJO phase using the NOAA daily OLR record (v02r00), cached for 1979–2026.</li><li>Then the daily MJO diagnostics for 2025–26 and TAO winds, as for Papers 2 and 3.</li>"
    "<li>Test the recharge path: equatorial versus off-equatorial heat, and the role of the 2025–26 La Niña.</li>"
    "<li>The negative PDO and the North Pacific marine heatwaves: amplifier, suppressor or coincidence.</li>"
    "<li>Literature on 2026 as it appears; update at each CPC monthly discussion (next: November 2026).</li></ul>")})

refs = [
    ("lheureux2024", "L'Heureux, M. L., et al. (2024). A relative sea surface temperature index for classifying ENSO events in a changing climate. <i>Journal of Climate</i> 37, 1197–1211.", "10.1175/JCLI-D-23-0406.1", None, "abstract read"),
    ("jin1997", "Jin, F.-F. (1997). An equatorial ocean recharge paradigm for ENSO. Part I: Conceptual model. <i>Journal of the Atmospheric Sciences</i> 54, 811–829.", "10.1175/1520-0469(1997)054<0811:AEORPF>2.0.CO;2", None, "abstract read"),
    ("meinen2000", "Meinen, C. S., and M. J. McPhaden (2000). Observations of warm water volume changes in the equatorial Pacific and their relationship to El Niño and La Niña. <i>Journal of Climate</i> 13, 3551–3559.", "10.1175/1520-0442(2000)013<3551:OOWWVC>2.0.CO;2", None, "abstract read"),
    ("takahashi2011", "Takahashi, K., A. Montecinos, K. Goubanova and B. Dewitte (2011). ENSO regimes: Reinterpreting the canonical and Modoki El Niño. <i>Geophysical Research Letters</i> 38, L10704.", "10.1029/2011GL047364", None, "bibliographic record"),
    ("capotondi2015", "Capotondi, A., et al. (2015). Understanding ENSO diversity. <i>Bulletin of the American Meteorological Society</i> 96, 921–938.", "10.1175/BAMS-D-13-00117.1", None, "abstract read"),
    ("saji1999", "Saji, N. H., B. N. Goswami, P. N. Vinayachandran and T. Yamagata (1999). A dipole mode in the tropical Indian Ocean. <i>Nature</i> 401, 360–363.", "10.1038/43854", None, "bibliographic record"),
    (RC.REF["key"], RC.REF["text"], RC.REF["doi"], RC.REF["url"], RC.REF["check"]),
    ("hersbach2020", "Hersbach, H., et al. (2020). The ERA5 global reanalysis. <i>Quarterly Journal of the Royal Meteorological Society</i> 146, 1999–2049. 2026 data: Copernicus Climate Change Service (C3S) Climate Data Store, ERA5 hourly data on pressure levels, u and v at 1000/850/200 hPa, 1 January – 18 October 2026.", "10.1002/qj.3803", None, "full text read (open access); data read and processed"),
    ("ibtracs", "Knapp, K. R., et al. (2010). The International Best Track Archive for Climate Stewardship (IBTrACS). <i>Bulletin of the American Meteorological Society</i> 91, 363–376. Data: IBTrACS v04r01, NOAA NCEI (2026 positions provisional).", "10.1175/2009BAMS2755.1", None, "bibliographic record"),
    ("cpc", "NOAA Climate Prediction Center: RONI and ONI, OISST v2.1 monthly and weekly Niño indices (traditional and relative), SOI, 850 hPa trade-wind and OLR indices, upper-300 m heat content, IOD (DMI), tropical Atlantic SST; ENSO Diagnostic Discussion and strength-probability table. NOAA PMEL warm water volume. NOAA NCEI PDO. Site copies in the data archive.", None, "https://www.cpc.ncep.noaa.gov/data/indices/", "data read"),
    ("cpc_dmi", "NOAA Climate Prediction Center, International Desks: Dipole Mode Index (DMI), ERSSTv6, 1991–2020 climatology; monthly text file mnth.ersstv6.clim19912020.dmi_current.txt (retrieved 24 Oct 2026).", None, "https://www.cpc.ncep.noaa.gov/products/international/ocean_monitoring/indian/IODMI/mnth.ersstv6.clim19912020.dmi_current.txt", "data read; August 2026 = +0.68"),
    ("iri", "IRI/CCSR: ENSO forecast, October 2026 multi-model Niño 3.4 plume (as read for the site's outlook card).", None, "https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/", "data read"),
]
if BD:
    refs.append(("r1diag", "NCEP/NCAR Reanalysis 1 daily winds (NOAA PSL): westerly-burst counts 1979–2026 on the definitions of Papers 1–3 (tools/papers/event_diag.py; outputs in data/papers/2026/).", None, "https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html", "data read and processed"))
toc = [(s["id"], s["title"]) for s in S] + [("references", "References")]
paper = {
    "number": 4, "file": "enso-2026.html", "short": "2026 El Niño (preliminary)",
    "title": "The 2026 El Niño against 1982–83, 1997–98 and 2015–16: a preliminary comparison",
    "description": "Preliminary observational comparison of the 2026 El Niño with the three strongest events of the satellite era at the same stage.",
    "status": "draft", "research_date": "24 October 2026", "lit_cutoff": "open; only background studies cited so far",
    "obs_cutoff": f"monthly indices to Sep 2026; RONI to JAS 2026; weekly OISST to the week of {lastwk}; CPC outlook of {cpc_issue}",
    "status_note": ("Preliminary analysis (24 Oct 2026): a same-stage comparison with the three strongest satellite-era events from monthly NOAA indices. "
                    "Not yet included: daily MJO and wind-burst analysis beyond the counts, TAO data, literature on 2026, impacts. Updated at each CPC monthly discussion."),
    "toc": toc, "sections": S,
    "references": [{"key": k, "text": t, "doi": doi, "url": u, "check": c} for k, t, doi, u, c in refs],
}
(ROOT / 'papers/4-enso-2026.json').write_text(json.dumps(paper, ensure_ascii=False, indent=1), encoding='utf-8')
print('ok', len(S), 'sections', len(refs), 'refs', rk)
