"""Official NOAA CPC ENSO probabilities from CPC's strength-probability page (numeric table, RONI-based).

Input:  <raw_dir>/cpc_strengths.html (cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths/)
        <raw_dir>/cpc_ensodisc.html  (for the exact issue date of the ENSO Diagnostic Discussion)
Output: CPC rows of data/enso_probs.csv (tools/weekly/enso_probs_io.py)
The table gives nine bins per season: four La Niña strengths, Neutral, four El Niño strengths (weak +0.5, moderate
+1.0, strong +1.5, very strong +2.0 °C RONI). Category totals are the sums of the bins; each row must sum to 100 ± 1.
Usage: python3 tools/weekly/cpc_probs.py <raw_dir>
"""
from __future__ import annotations

import datetime as dt
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import enso_probs_io as io


def _cells(tr: str) -> list[str]:
    return [html.unescape(re.sub(r'<[^>]+>', ' ', c)).split() for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', tr, flags=re.DOTALL)]


def parse(raw: Path) -> list[dict]:
    page = (raw / 'cpc_strengths.html').read_text(errors='replace')
    issued_month = re.findall(r'Issued ([A-Z][a-z]+ 20\d\d)', page)[-1]
    ym = dt.datetime.strptime(issued_month + ' +0000', '%B %Y %z').strftime('%Y-%m')
    issued = ym
    disc = raw / 'cpc_ensodisc.html'
    if disc.exists():
        t = html.unescape(re.sub(r'<[^>]+>', ' ', disc.read_text(errors='replace')))
        m = re.search(r'NCEP/NWS\s+(?:and the International Research Institute for Climate and Society\s+)?(\d{1,2} [A-Z][a-z]+ 20\d\d)', t)
        if m:
            d = dt.datetime.strptime(m.group(1) + ' +0000', '%d %B %Y %z').date()
            if d.strftime('%Y-%m') == ym:
                issued = d.isoformat()
    table = next(tb for tb in re.findall(r'<table.*?</table>', page, flags=re.DOTALL) if 'Season' in tb and 'Index' in tb)
    out = []
    for tr in re.findall(r'<tr.*?</tr>', table, flags=re.DOTALL)[1:]:
        c = _cells(tr)
        if len(c) != 10 or not c[0]:
            continue
        season = c[0][0]
        v = [int(x[0]) for x in c[1:]]
        assert 99 <= sum(v) <= 101, (season, v)
        out.append({'source': 'CPC', 'issued': issued, 'index': 'RONI (relative Niño 3.4)', 'season': season,
                    'target_start': io.target_start(season, ym), 'la_nina': sum(v[:4]), 'neutral': v[4], 'el_nino': sum(v[5:]),
                    'en_weak': v[5], 'en_moderate': v[6], 'en_strong': v[7], 'en_very_strong': v[8]})
    assert len(out) >= 6, 'CPC table not found or too short'
    return out


def main(raw: Path) -> int:
    rows = parse(raw)
    io.write('CPC', rows)
    print(f"  cpc_probs: issued {rows[0]['issued']}, {len(rows)} seasons {rows[0]['season']}..{rows[-1]['season']}")
    print('  (LN/N/EN):', ', '.join(f"{r['season']} {r['la_nina']}/{r['neutral']}/{r['el_nino']}" for r in rows))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1])))
