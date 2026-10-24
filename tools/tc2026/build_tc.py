"""Build the 2026 tropical-cyclone papers (tc2026/*.json -> tc-2026-<storm>.html) and their index page (tc-2026.html).
Reuses the style and table helpers of the ENSO papers. Run: python3 tools/tc2026/build_tc.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/papers'))
from build import NAV, STATUS_TAG, STYLE, conf, esc, ref_html, table  # noqa: E402

SRC = ROOT / 'tc2026'
MEDIA = json.loads((ROOT / 'tc2026/media.json').read_text(encoding='utf-8')) if (ROOT / 'tc2026/media.json').exists() else {}
HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Global Weather Watch</title>
<meta name="description" content="{desc}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%232b6cb0'/%3E%3C/svg%3E">
<style>{style}</style>
</head><body>
{nav}
<main>
"""
FOOT = """</main>
<footer class="site-foot">Data snapshot: <span data-asof>{asof}</span>. Independent, non-commercial analysis built from public sources (see <a href="about.html">About &amp; method</a>). Analysis prepared with Claude (Anthropic).</footer>
</body></html>
"""


def page(p: dict, allp: list) -> str:
    parts = [f'<p class="meta"><a href="tc-2026.html">2026 hurricanes and typhoons</a> · {esc(p["basin_name"])}</p>',
             f'<h1>{esc(p["title"])}</h1>',
             f'<p class="meta"><span class="tag {STATUS_TAG[p["status"]][0]}">{STATUS_TAG[p["status"]][1]}</span> Research date: {esc(p["research_date"])} · '
             f'Data cutoff: {esc(p["obs_cutoff"])} · Track data: {esc(p["track_source"])}</p>',
             f'<div class="card status"><b>Status.</b> {p["status_note"]}</div>']
    toc = list(p.get('toc', []))
    if MEDIA.get(p['storm']) and ('media', 'Media evidence (links)') not in toc:
        toc.insert(next((i for i, x in enumerate(toc) if x[0] == 'evidence'), len(toc)), ('media', 'Media evidence (links)'))
    if toc:
        parts.append('<div class="card"><b>Contents</b><div class="toc">' + ''.join(f'<div><a href="#{a}">{esc(t)}</a></div>' for a, t in toc) + '</div></div>')
    for s in p['sections']:
        parts.append(f'<h2 id="{s["id"]}">{esc(s["title"])}</h2><div class="prose">{s["html"]}</div>')
        if s.get('table'):
            t = s['table']; parts.append(table(t['cols'], t['rows'], t.get('cls', '')))
            if t.get('note'):
                parts.append(f'<p class="note">{t["note"]}</p>')
        if s.get('html_after'):
            parts.append(f'<div class="prose">{s["html_after"]}</div>')
    media = MEDIA.get(p['storm'], [])
    if media:
        parts.append('<h2 id="media">Media evidence (links)</h2><div class="prose"><p>Videos, photographs, satellite images and news reports that document the storm. They are supporting evidence only: the analysis above does not rely on them, and the material belongs to its publishers, so it is linked rather than copied. Press videos and social-media clips are not independently verified.</p></div>')
        parts.append(table(['Type', 'What it shows', 'Source', 'Link'], [[esc(m[0]), esc(m[1]), esc(m[2]), f'<a href="{esc(m[3])}">{esc(m[3].split("/")[2])}</a>'] for m in media]))
    if p.get('evidence'):
        parts.append('<h2 id="evidence">Evidence table</h2>')
        parts.append(table(['Factor', 'Observed conditions and timing', 'Proposed role', 'Evidence type', 'Confidence', 'Key sources'],
                           [[f'<b>{esc(e[0])}</b>', e[1], e[2], e[3], conf(e[4]), e[5]] for e in p['evidence']]))
    parts.append('<h2 id="references">References</h2><ol class="refs">' + ''.join(ref_html(r) for r in p['references']) + '</ol>')
    sib = ''.join(f'<a class="card" href="{q["file"]}"{" aria-current=\"page\"" if q["file"] == p["file"] else ""}><b>{esc(q["short"])}</b><br><span class="note">{esc(q["card_line"])}</span></a>' for q in allp)
    parts.append(f'<h2>Other 2026 storm papers</h2><div class="papers">{sib}</div>')
    return HEAD.format(title=esc(p['short']), desc=esc(p['description']), style=STYLE, nav=NAV) + '\n'.join(parts) + FOOT.format(asof=esc(p['research_date']))


def index(allp: list, inv: list) -> str:
    done = {q['storm'] for q in allp}
    rows = []
    for r in inv:
        link = next((q['file'] for q in allp if q['storm'] == r['name']), None)
        nm = f'<a href="{link}">{esc(r["name"].title())}</a>' if link else esc(r['name'].title())
        rows.append([nm, esc(r['basin']), esc(r['dates']), f'<span class="num">{r["peak_kt"]}</span>', esc(str(r['cat'])), 'Paper' if r['name'] in done else 'Planned'])
    body = ('<h1>2026 hurricanes and typhoons</h1>'
            '<p class="meta">One research paper per storm that reached hurricane or typhoon strength (64 kt, 1-minute winds in IBTrACS) in the North Atlantic, eastern and central North Pacific and western North Pacific. '
            'Written newest first, in batches. Track data are provisional until the official post-season reports.</p>'
            + table(['Storm', 'Basin', 'Dates (UTC, IBTrACS)', 'Peak (kt)', 'Category', 'Status'], rows)
            + '<p class="note">Peak = highest 1-minute sustained wind in IBTrACS v04r01 (NHC or JTWC values; JMA uses 10-minute winds, which are lower). Category on the Saffir–Simpson scale.</p>')
    return HEAD.format(title='2026 hurricanes and typhoons', desc='Research papers on every 2026 hurricane and typhoon.', style=STYLE, nav=NAV) + body + FOOT.format(asof=esc(allp[0]['research_date'] if allp else ''))


def main() -> int:
    allp = [json.loads(f.read_text(encoding='utf-8')) for f in sorted(SRC.glob('*.json')) if f.name not in ('inventory.json', 'media.json')]
    allp.sort(key=lambda q: q['order'])
    for p in allp:
        (ROOT / p['file']).write_text(page(p, allp), encoding='utf-8'); print('wrote', p['file'])
    inv = json.loads((SRC / 'inventory.json').read_text())
    (ROOT / 'tc-2026.html').write_text(index(allp, inv), encoding='utf-8'); print('wrote tc-2026.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
