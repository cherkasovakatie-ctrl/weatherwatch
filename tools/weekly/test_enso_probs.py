"""Tests for season alignment and the CPC/IRI probability parsers. Run: python3 -m pytest tools/weekly"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import enso_probs_io as io


def test_target_start_crosses_year():
    assert io.target_start('SON', '2026-10') == '2026-09'
    assert io.target_start('OND', '2026-10') == '2026-10'
    assert io.target_start('DJF', '2026-10') == '2026-12'
    assert io.target_start('JFM', '2026-10') == '2027-01'
    assert io.target_start('JJA', '2026-10') == '2027-06'
    assert io.target_start('NDJ', '2026-12') == '2026-11'


def test_cpc_and_iri_align_on_season():
    import csv
    with open(io.FILE, encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    by = {}
    for r in rows:
        by.setdefault(r['target_start'], {})[r['source']] = r['season']
    for ts, srcs in by.items():
        assert len(set(srcs.values())) == 1, (ts, srcs)  # same season code whatever the source
    for r in rows:
        assert 98 <= int(r['la_nina']) + int(r['neutral']) + int(r['el_nino']) <= 102, r
