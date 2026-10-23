"""Probe the IRI ensoforecast service for machine-readable plume data."""
import datetime as dt, urllib.request
from pathlib import Path
OUT = Path('raw') / (dt.date.today().isoformat() + '-plume3'); OUT.mkdir(parents=True, exist_ok=True)
B = 'https://ensoforecast.iri.columbia.edu'
paths = ['/', '/figure4_plot/2026/10', '/figure4_data/2026/10', '/figure4_table/2026/10', '/figure4_json/2026/10', '/figure4/2026/10',
         '/figure4_highchart/2026/10', '/figure9_plot/2026/10', '/figure3_plot/2026/10', '/figure7_plot/2026/10/22', '/strength_plot/2026/10',
         '/api', '/api/plume/2026/10', '/data/2026/10', '/plume/2026/10', '/table/2026/10', '/sst_table/2026/10', '/docs', '/openapi.json']
log = []
for p in paths:
    try:
        r = urllib.request.urlopen(urllib.request.Request(B + p, headers={'User-Agent': 'Mozilla/5.0 GlobalWeatherWatch/1.0'}), timeout=60)
        b = r.read(); ct = r.headers.get('Content-Type', '')
        name = p.strip('/').replace('/', '_') or 'root'
        (OUT / (name + ('.png' if 'image' in ct else '.txt'))).write_bytes(b); log.append(f'OK   {p} {ct} {len(b)}')
    except Exception as e:
        log.append(f'FAIL {p} {str(e)[:120]}')
(OUT / 'log.txt').write_text('\n'.join(log) + '\n'); print('\n'.join(log))
