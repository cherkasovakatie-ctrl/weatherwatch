"""Rebuild data/reports.csv (the 'Research Papers and Reports' tab) from the ENSO papers, the 2026 storm papers and the fixed reports.
Run after adding a paper: python3 tools/reports_index.py, then node tools/make_pdfs.cjs (local server on :8765), then this script again to link the PDFs."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATES = {'18 October 2026': '2026-10-18', '23 October 2026': '2026-10-23', '24 October 2026': '2026-10-24'}
rows = [('2026-10-17', 'Why global temperature has risen since 1976 — and what made the 1940s bump', 'Climate report', '', 'warming-since-1976.html')]
for f in sorted((ROOT / 'papers').glob('*.json')):
    p = json.loads(f.read_text(encoding='utf-8'))
    rows.append((DATES.get(p['research_date'], p['research_date']), f"Paper {p['number']}: {p['title']}", 'Research paper · ENSO', '', p['file']))
tc = sorted((json.loads(f.read_text(encoding='utf-8')) for f in (ROOT / 'tc2026').glob('*.json') if f.name not in ('inventory.json', 'media.json')), key=lambda p: p['order'])
for p in tc:
    rows.append((DATES.get(p['research_date'], p['research_date']), p['title'], 'Research paper · 2026 storms', '', p['file']))
if tc:
    rows.append((max(DATES.get(p['research_date'], p['research_date']) for p in tc), '2026 hurricanes and typhoons: index of storm papers', 'Index · 2026 storms', '', 'tc-2026.html'))
rows = [(d, t, k, (f'reports/pdf/{doc[:-5]}.pdf' if (ROOT / f'reports/pdf/{doc[:-5]}.pdf').exists() else pdf), doc) for d, t, k, pdf, doc in rows]
with open(ROOT / 'data/reports.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['date', 'title', 'kind', 'pdf', 'doc']); w.writerows(rows)
print(len(rows), 'rows')
