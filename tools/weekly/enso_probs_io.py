"""Shared writer for data/enso_probs.csv: ENSO category probabilities from several sources, keyed by target season.

Each source rewrites only its own rows. Rows carry the target season's first month (target_start, YYYY-MM) so that
products that start on different seasons can be matched by season rather than by row position.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / 'data' / 'enso_probs.csv'
HDR = ['source', 'issued', 'index', 'season', 'target_start', 'la_nina', 'neutral', 'el_nino',
       'en_weak', 'en_moderate', 'en_strong', 'en_very_strong']
MONTHS = 'JFMAMJJASONDJF'


def target_start(season: str, issue_ym: str) -> str:
    """First month (YYYY-MM) of a 3-letter season such as 'NDJ', taking the first occurrence that begins no
    earlier than two months before the issue month (CPC's first season starts the month before issue)."""
    y, m = int(issue_ym[:4]), int(issue_ym[5:7])
    starts = [i + 1 for i in range(12) if MONTHS[i:i + 3] == season]
    assert len(starts) == 1, season
    s = starts[0]
    base = y * 12 + (m - 1) - 2
    k = base + ((s - 1) - base) % 12
    return f'{k // 12}-{k % 12 + 1:02d}'


def write(source: str, rows: list[dict]) -> None:
    keep = []
    if FILE.exists():
        with open(FILE, newline='', encoding='utf-8') as fh:
            r = csv.DictReader(fh)
            if r.fieldnames == HDR:
                keep = [x for x in r if x['source'] != source]
    allr = keep + rows
    allr.sort(key=lambda x: (x['source'], x['target_start']))
    with open(FILE, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(HDR)
        for x in allr:
            w.writerow([x.get(h, '') for h in HDR])
