"""Figure 1 for Paper 4: four El Niño events aligned on the onset year (Dec of year −1 to Dec of year +1)."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / 'data/papers/2026/analog_monthly.csv', encoding='utf-8')))
YEARS = ('1982', '1997', '2015', '2026')
COL = {'1982': '#7a8aa0', '1997': '#d1495b', '2015': '#edae49', '2026': '#00798c'}
PANELS = [('roni', 'RONI (°C), 3-month, by centre month'), ('nino12', 'Niño 1+2 SST anomaly (°C, OISST)'),
          ('heat', 'Upper-300 m heat content, 180°–100°W (°C)'), ('wwv', 'Warm water volume anomaly (10¹⁴ m³)')]
lags = list(dict.fromkeys(r['lag'] for r in rows))
fig, axs = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
for ax, (v, title) in zip(axs.flat, PANELS):
    for y in YEARS:
        pts = [(i, float(r[y])) for i, r in enumerate(r for r in rows if r['var'] == v) if r[y] != '']
        ax.plot(*zip(*pts), color=COL[y], lw=2.6 if y == '2026' else 1.6, label=f'{y}–{str(int(y) + 1)[2:]}' if y != '2026' else '2026')
    ax.axhline(0, color='#888', lw=0.6); ax.axvline(lags.index('Sep'), color='#bbb', lw=0.8, ls=':')
    ax.set_title(title, fontsize=10); ax.grid(alpha=0.25)
for ax in axs[1]:
    ax.set_xticks(range(0, len(lags), 3)); ax.set_xticklabels([lags[i] for i in range(0, len(lags), 3)], fontsize=8)
axs[0, 0].legend(fontsize=9, frameon=False)
fig.suptitle('Onset year aligned (year 0 = 1982, 1997, 2015, 2026); dotted line = September of year 0', fontsize=10)
fig.tight_layout()
fig.savefig(ROOT / 'papers/img/enso2026_analogs.png', dpi=130)
print('saved')
