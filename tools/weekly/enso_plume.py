"""Recover the IRI/CCSR ENSO forecast plume and objective probabilities from IRI's matplotlib SVG figures.

IRI publishes the monthly plume only as figures (the data/table endpoints return 403). The SVGs keep exact geometry:
tick marks give the axis mapping, legend glyphs give model names, and the legend swatches list the line colours in
the same order as the data lines, which is checked before anything is written.

Inputs:  <raw_dir>/iri_figure4.svg (plume), iri_figure3.svg (probabilities), iri_issue.txt (YYYY-MM)
Outputs: data/enso_plume.csv  one row per season; observed, three averages, model min/max/count, one column per model
         data/enso_probs.csv  IRI objective probabilities (%) of La Niña / Neutral / El Niño per season
Usage:   python3 tools/weekly/enso_plume.py <raw_dir>
Values are traditional Niño 3.4 anomalies (°C, OISST v2.1, 1991–2020 base) as plotted by IRI, read to ±0.01 °C.
"""
from __future__ import annotations

import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SV = '{http://www.w3.org/2000/svg}'
XL = '{http://www.w3.org/1999/xlink}href'
ROOT = Path(__file__).resolve().parents[2]
AVERAGES = {'COMBINED AVG': 'combined_avg', 'DYN Average': 'dyn_avg', 'STAT Average': 'stat_avg'}


def _glyph_text(g: ET.Element) -> str:
    """matplotlib glyph ids end in DejaVuSans-<hex>; IRI's font subset is offset by 29 code points."""
    out = []
    for u in g.iter(SV + 'use'):
        code = u.get(XL, '')[1:].split('-')[-1]
        if len(code) < 2:
            out.append(' ')
            continue
        c = chr(int(code, 16))
        out.append('−' if c == 'ಜ' else chr(ord(c) + 29) if ord(c) < 0x80 else c)
    return ''.join(out).strip()


def _translate(g: ET.Element) -> tuple[float, float] | None:
    inner = g.find(SV + 'g')
    m = re.match(r'translate\(([\d.\-]+) ([\d.\-]+)', inner.get('transform', '')) if inner is not None else None
    return (float(m.group(1)), float(m.group(2))) if m else None


def _ticks(root: ET.Element, axis: str) -> list[tuple[float, str]]:
    out = []
    for g in root.iter(SV + 'g'):
        if not re.fullmatch(rf'{axis}tick_\d+', g.get('id', '')):
            continue
        mark = [u for u in g.iter(SV + 'use') if u.get(axis) and u.get(XL, '').startswith('#m')]
        lab = [t for t in g.iter(SV + 'g') if t.get('id', '').startswith('text_')]
        if mark and lab:
            out.append((float(mark[0].get(axis)), _glyph_text(lab[0])))
    return out


def _yscale(root: ET.Element):
    yt = [(p, float(s.replace('−', '-'))) for p, s in _ticks(root, 'y')]
    (p1, v1), (p2, v2) = yt[0], yt[-1]
    k = (v2 - v1) / (p2 - p1)
    return lambda y: v1 + (y - p1) * k


def _lines(root: ET.Element) -> list[dict]:
    out = []
    for g in root.iter(SV + 'g'):
        if not g.get('id', '').startswith('line2d_'):
            continue
        p = g.find(SV + 'path')
        if p is None:
            continue
        style = p.get('style', '')
        col = re.search(r'stroke: ?(#[0-9a-f]{6})', style)
        xy = [(float(a), float(b)) for a, b in re.findall(r'([\d.\-]+) ([\d.\-]+)', p.get('d', ''))]
        out.append({'color': col[1] if col else None, 'xy': xy})
    return out


def plume(svg: Path) -> tuple[list[str], dict, list[str], list[str]]:
    root = ET.parse(svg).getroot()
    val = _yscale(root)
    xt = _ticks(root, 'x')
    seasons = [s for _, s in xt]
    col_of = {round(x): s for x, s in xt}
    texts = [(t, _translate(g)) for g in root.iter(SV + 'g') if g.get('id', '').startswith('text_') for t in [_glyph_text(g)]]
    legend_x = min(p[0] for t, p in texts if p and t == 'COMBINED AVG')
    legend_txt = sorted(((p[1], t) for t, p in texts if p and abs(p[0] - legend_x) < 1), key=lambda a: a[0])
    lines = [ln for ln in _lines(root) if ln['color'] and len(ln['xy']) >= 2]
    swatch = [ln for ln in lines if min(x for x, _ in ln['xy']) > legend_x - 60]
    data = [ln for ln in lines if ln not in swatch and len({round(x) for x, _ in ln['xy']}) > 1]  # drop vertical gridlines
    # name each legend swatch by the nearest legend label (same row)
    named = []
    for ln in swatch:
        y = ln['xy'][0][1]
        dy, name = min((abs(ty - y), t) for ty, t in legend_txt)
        assert dy < 8, ('legend label not found', y)
        named.append((name, ln['color']))
    models = [(n, c) for n, c in named if n not in AVERAGES]
    avgs = [(n, c) for n, c in named if n in AVERAGES]
    # data lines: all-forecast lines starting at the first forecast season; observed = black line through *-OBS ticks
    fc = [ln for ln in data if all(round(x) in col_of and not col_of[round(x)].endswith('-OBS') for x, _ in ln['xy'])]
    fc_models, fc_avgs = fc[:len(models)], fc[len(models):]
    assert [ln['color'] for ln in fc_models] == [c for _, c in models], 'model colour order mismatch'
    assert [ln['color'] for ln in fc_avgs] == [c for _, c in avgs], 'average colour order mismatch'
    obs = [ln for ln in data if ln['color'] == '#000000' and all(col_of.get(round(x), '').endswith('-OBS') for x, _ in ln['xy'])]
    rows = {s: {} for s in seasons}
    for (name, _), ln in zip(models + avgs, fc_models + fc_avgs):
        key = AVERAGES.get(name, name)
        for x, y in ln['xy']:
            rows[col_of[round(x)]][key] = round(val(y), 2)
    for ln in obs[:1]:
        for x, y in ln['xy']:
            rows[col_of[round(x)]]['observed'] = round(val(y), 2)
    title = next((t for t, _ in texts if 'Model Predictions of ENSO from' in t), '')
    return seasons, rows, [n for n, _ in models], [title]


def probs(svg: Path) -> list[dict]:
    root = ET.parse(svg).getroot()
    val = _yscale(root)
    xt = _ticks(root, 'x')
    kinds = {'#0000ff': 'la_nina', '#aaaaaa': 'neutral', '#ff0000': 'el_nino'}
    out = {s: {'season': s} for _, s in xt}
    centres = [x for x, _ in xt]
    for g in root.iter(SV + 'g'):
        if not g.get('id', '').startswith('patch_'):
            continue
        p = g.find(SV + 'path')
        col = re.search(r'fill: ?(#[0-9a-f]{6})', p.get('style', '') if p is not None else '')
        if not col or col[1] not in kinds:
            continue
        n = [float(v) for v in re.findall(r'[\d.\-]+', p.get('d', ''))]
        xs, ys = n[0::2], n[1::2]
        cx = (min(xs) + max(xs)) / 2
        i = min(range(len(centres)), key=lambda k: abs(centres[k] - cx))
        if abs(centres[i] - cx) > 30:
            continue  # legend swatch
        out[xt[i][1]][kinds[col[1]]] = round(val(min(ys)) - val(max(ys)))
    rows = list(out.values())
    for r in rows:
        tot = sum(r.get(k, 0) for k in kinds.values())
        assert 98 <= tot <= 102, ('probabilities do not sum to 100', r)
    return rows


def main(raw: Path) -> int:
    issue = (raw / 'iri_issue.txt').read_text().strip() if (raw / 'iri_issue.txt').exists() else ''
    seasons, rows, models, (title,) = plume(raw / 'iri_figure4.svg')
    hdr = ['issue', 'season', 'order', 'kind', 'observed', 'combined_avg', 'dyn_avg', 'stat_avg', 'model_min', 'model_max', 'model_n'] + models
    with open(ROOT / 'data' / 'enso_plume.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(hdr)
        for i, s in enumerate(seasons):
            r = rows[s]
            if not r:
                continue  # tick with no plotted value (e.g. the season that overlaps the observations)
            mv = [r[m] for m in models if m in r]
            if 'combined_avg' in r:  # cross-check: IRI's plotted average must equal the mean of the plotted models
                assert abs(sum(mv) / len(mv) - r['combined_avg']) <= 0.015, (s, sum(mv) / len(mv), r['combined_avg'])
            r.update(issue=issue, season=s.replace('-OBS', ''), order=i, kind='observed' if s.endswith('-OBS') else 'forecast',
                     model_min=min(mv) if mv else '', model_max=max(mv) if mv else '', model_n=len(mv) or '')
            w.writerow([r.get(h, '') for h in hdr])
    pr = probs(raw / 'iri_figure3.svg')
    with open(ROOT / 'data' / 'enso_probs.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(['issue', 'season', 'la_nina', 'neutral', 'el_nino'])
        for r in pr:
            w.writerow([issue, r['season'], r.get('la_nina', 0), r.get('neutral', 0), r.get('el_nino', 0)])
    print(f'  enso_plume: {title} | {len(models)} models, seasons {seasons[0]}..{seasons[-1]}')
    print('  combined avg:', ', '.join(f"{s} {rows[s].get('combined_avg', '')}" for s in seasons if 'combined_avg' in rows[s]))
    print('  probs (LN/N/EN):', ', '.join(f"{r['season']} {r.get('la_nina', 0)}/{r.get('neutral', 0)}/{r.get('el_nino', 0)}" for r in pr))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1])))
