"""Paper 4: burst counts for the four events from the event_diag outputs (Papers 1–3 runs and the 2026 run).
Usage: python3 tools/papers/diag_2026.py RAWDIR   (RAWDIR = raw/papers/2026 from the weekly-raw branch)
Writes data/papers/2026/diag_2026.json and copies the 2026 burst list and Hovmöller file.
"""
import json
import shutil
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data/papers'
raw = Path(sys.argv[1])
S26 = json.load(open(raw / 'mjo_summary.json'))
shutil.copy(raw / 'mjo_summary.json', D / '2026/mjo_summary.json')
if (raw / 'hov_u1000_anom_5S5N.csv').exists():
    shutil.copy(raw / 'hov_u1000_anom_5S5N.csv', D / '2026/hov_u1000_anom_5S5N.csv')
lists = {y: json.load(open(D / f'{y}/mjo_summary.json'))['wwb'] for y in (1982, 1997, 2015)}
lists[2026] = S26['wwb']
jan_sep = {str(y): sum(f'{y}-01-01' <= w['start'] <= f'{y}-09-30' for w in L) for y, L in lists.items()}
yearly = {y['year']: y['wwb_count'] for y in S26['wwb_yearly']}
w26 = [w for w in S26['wwb'] if w['start'] >= '2026-01-01']
big = max(w26, key=lambda w: w['peak_anom']) if w26 else None
past = [v for k, v in yearly.items() if k <= 2025]
rank_whole = sorted(past, reverse=True)
res = {
    'bursts_jan_sep': jan_sep,
    'bursts_year': {str(y): yearly[y] for y in (1982, 1997, 2015, 2026)},
    'mean_year_1979_2025': round(statistics.mean(past), 1),
    'max_year_1979_2025': [max(past), [k for k, v in yearly.items() if k <= 2025 and v == max(past)]],
    'years_with_more_than_2026_to_date': [k for k, v in yearly.items() if k <= 2025 and v > yearly[2026]],
    'bursts_2026': w26,
    'largest_2026': big,
    'data_end': S26.get('log', [])[-5:],
}
json.dump(res, open(D / '2026/diag_2026.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'bursts_2026'}, indent=1))
