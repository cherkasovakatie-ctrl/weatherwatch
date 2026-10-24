"""Shared GPCP rainfall and NOAA STAR tropospheric-temperature comparison for Papers 1–4.
Data: data/papers/climate/gpcp_regions_monthly.csv (GPCP v2.3, NOAA PSL; regional means, mm/day) and
data/papers/climate/msu_monthly.csv (NOAA STAR MSU/AMSU v5 TLT and TMT, K). Base period 1991–2020.
add_rain(paper, year) appends one section to a paper dict; table_all() gives the cross-event table for Paper 4.
"""
import csv
import statistics
from pathlib import Path

D = Path(__file__).resolve().parents[2] / 'data/papers/climate'
EVENTS = (1982, 1997, 2015)
LAB = {1982: '1982–83', 1997: '1997–98', 2015: '2015–16', 2026: '2026'}
# region, label, months relative to onset year (0 = onset year, 1 = following year), expected El Niño sign
SEASONS = [
    ('central_eq_pacific', 'Central equatorial Pacific (5°S–5°N, 170°E–140°W)', [(0, m) for m in (9, 10, 11)], 'SON', +1),
    ('peru_ecuador_coast', 'Coastal Peru and Ecuador (12.5°S–2.5°N, 85°–77.5°W)', [(0, 12)] + [(1, m) for m in (1, 2, 3, 4)], 'Dec–Apr', +1),
    ('indonesia', 'Indonesia (10°S–5°N, 95°–145°E)', [(0, m) for m in (7, 8, 9, 10)], 'Jul–Oct', -1),
    ('eastern_australia', 'Eastern Australia (40°–10°S, 140°–155°E)', [(0, m) for m in (6, 7, 8, 9, 10, 11)], 'Jun–Nov', -1),
    ('india', 'India (8°–30°N, 70°–90°E)', [(0, m) for m in (6, 7, 8, 9)], 'Jun–Sep', -1),
    ('east_africa', 'Equatorial East Africa (5°S–5°N, 35°–50°E)', [(0, m) for m in (10, 11, 12)], 'Oct–Dec', +1),
    ('southern_africa', 'Southern Africa (35°–15°S, 15°–40°E)', [(0, 12)] + [(1, m) for m in (1, 2, 3)], 'Dec–Mar', -1),
    ('california', 'California (32.5°–42.5°N, 125°–115°W)', [(0, m) for m in (11, 12)] + [(1, m) for m in (1, 2, 3)], 'Nov–Mar', +1),
]

with open(D / 'gpcp_regions_monthly.csv', encoding='utf-8') as fh:
    G = {r['month']: {k: float(v) for k, v in r.items() if k != 'month'} for r in csv.DictReader(fh)}
with open(D / 'msu_monthly.csv', encoding='utf-8') as fh:
    M = {r['month']: {k: (float(v) if v else None) for k, v in r.items() if k != 'month'} for r in csv.DictReader(fh)}
GLAST = max(G)


def season_total(region, y, months):
    keys = [f'{y + dy}-{m:02d}' for dy, m in months]
    if any(k not in G for k in keys):
        return None
    return sum(G[k][region] for k in keys) / len(keys)


def season_stats(region, months, y):
    """Mean rate (mm/day), % of the 1991–2020 mean, and rank (1 = wettest) among 1979–2025 seasons."""
    v = season_total(region, y, months)
    if v is None:
        return None
    base = [season_total(region, yy, months) for yy in range(1991, 2021)]
    allv = {yy: season_total(region, yy, months) for yy in range(1979, 2026)}
    allv = {k: x for k, x in allv.items() if x is not None}
    clim = statistics.mean(base)
    wet_rank = sorted(allv.values(), reverse=True).index(v) + 1 if y in allv else None
    return {'mm': v, 'pct': 100 * v / clim, 'wet_rank': wet_rank, 'dry_rank': (len(allv) + 1 - wet_rank) if wet_rank else None, 'n': len(allv)}


def cell(s, sign):
    if s is None:
        return '—'
    r = s['wet_rank'] if sign > 0 else s['dry_rank']
    word = 'wettest' if sign > 0 else 'driest'
    return f"{s['pct']:.0f}%<br><span class=\"note\">{_ord(r)} {word} of {s['n']}</span>"


def _ord(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def msu_anom(key):
    clim = {m: statistics.mean(M[f'{y}-{m:02d}'][key] for y in range(1991, 2021)) for m in range(1, 13)}
    return {k: v[key] - clim[int(k[5:])] for k, v in M.items() if v.get(key) is not None}


TLT_T, TLT_G = msu_anom('tlt_tropics'), msu_anom('tlt_global')


def tlt_peak(y, key=None):
    a = TLT_T if key is None else key
    win = [k for k in a if f'{y}-07' <= k <= f'{y + 1}-12']
    pk = max(win, key=lambda k: a[k])
    return pk, a[pk]


MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


def mlab(k):
    return f'{MON[int(k[5:]) - 1]} {k[:4]}'


NOTE = ("GPCP v2.3 monthly precipitation (NOAA PSL), box means over land and ocean on the 2.5° grid; percentage of the 1991–2020 mean for the same months; "
        f"rank among the {{n}} seasons 1979–2025 (wettest for regions that usually turn wet in El Niño, driest for those that usually turn dry). Data to {mlab(GLAST)}. "
        "Seasons are the usual El Niño impact seasons, counted from the onset year (Dec–Apr = December of the onset year to April of the next).")


def table_all(extra_year=None):
    cols = ['Region (season)', 'Usual El Niño signal'] + [LAB[y] for y in EVENTS] + ([LAB[extra_year]] if extra_year else [])
    rows = []
    for reg, lab, months, sl, sign in SEASONS:
        r = [f'{lab} ({sl})', 'wetter' if sign > 0 else 'drier'] + [cell(season_stats(reg, months, y), sign) for y in EVENTS]
        if extra_year:
            r.append(cell(season_stats(reg, months, extra_year), sign))
        rows.append(r)
    return cols, rows


def tlt_rows(years):
    out = []
    for y in years:
        pk, v = tlt_peak(y)
        pg, vg = tlt_peak(y, TLT_G)
        out.append([LAB[y], f'{v:+.2f} °C ({mlab(pk)})'.replace('-', '−', 1) if v < 0 else f'{v:+.2f} °C ({mlab(pk)})', f'{vg:+.2f} °C ({mlab(pg)})'])
    return out


REF = {"key": "gpcp", "text": "GPCP v2.3 monthly precipitation (Adler et al. 2018, <i>Atmosphere</i> 9, 138), via NOAA PSL; NOAA STAR MSU/AMSU-A/ATMS Mean Layer Temperature CDR v5 (TLT, TMT), via NOAA NCEI. Regional means computed with tools/papers/gpcp_regions.py (outputs in data/papers/climate/).",
       "doi": "10.3390/atmos9040138", "url": None, "check": "data read and processed"}


def add_rain(paper, year):
    cols, rows = table_all()
    i = EVENTS.index(year)
    hits = []
    for (reg, lab, months, sl, sign), row in zip(SEASONS, rows):
        s = season_stats(reg, months, year)
        if s is None:
            continue
        typical = (s['pct'] > 100) == (sign > 0)
        hits.append((lab.split(' (')[0], sl, s, typical, sign))
    n_typ = sum(h[3] for h in hits)
    ext = [h for h in hits if (h[2]['wet_rank'] if h[4] > 0 else h[2]['dry_rank']) <= 3]
    pk, v = tlt_peak(year)
    html = (f"<p>Rainfall in the usual El Niño impact regions, from GPCP v2.3 against 1991–2020. In {LAB[year]}, {n_typ} of the {len(hits)} regions had the usual El Niño sign. "
            + ("The most extreme seasons (top three since 1979) were: " + '; '.join(f"{h[0]} ({h[1]}, {h[2]['pct']:.0f}% of normal, {_ord(h[2]['wet_rank'] if h[4] > 0 else h[2]['dry_rank'])} {'wettest' if h[4] > 0 else 'driest'})" for h in ext) + ". " if ext else "")
            + f"The same comparison across all four events is in Paper 4.</p>"
            f"<p>The tropical lower troposphere (NOAA STAR TLT, 20°S–20°N) warmed to {v:+.2f} °C above 1991–2020 by {mlab(pk)}, the usual lag of a few months behind the sea surface.</p>")
    sec = {"id": "rainfall", "title": "Rainfall and tropospheric temperature (GPCP, NOAA STAR)", "html": html,
           "table": {"cols": ['Region (season)', 'Usual El Niño signal', LAB[year]], "rows": [[r[0], r[1], r[2 + i]] for r in rows], "note": NOTE.format(n=47)}}
    paper.setdefault("post_sections", [])
    paper["post_sections"] = [s for s in paper["post_sections"] if s.get("id") != "rainfall"]
    k = next((j for j, s in enumerate(paper["post_sections"]) if s.get("id") == "verification"), len(paper["post_sections"]))
    paper["post_sections"].insert(k, sec)
    toc = [t for t in paper.get("toc", []) if t[0] != "rainfall"]
    j = next((j for j, t in enumerate(toc) if t[0] in ("verification", "references")), len(toc))
    toc.insert(j, ("rainfall", "Rainfall and tropospheric temperature"))
    paper["toc"] = toc
    refs = [r for r in paper.get("references", []) if r.get("key") != "gpcp"]
    refs.append(REF)
    paper["references"] = refs
    return paper
