"""Figure for each 2026 storm paper: intensity and pressure (IBTrACS) and the ocean under the track (OISST, 3 days before arrival).
Usage: python3 tools/tc2026/fig_storm.py TRUDY SIMON ...  -> papers/img/tc2026_<storm>.png"""
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
T = json.loads((ROOT / 'data/tc2026/track_stats.json').read_text())
E = [r for r in csv.DictReader(open(ROOT / 'data/tc2026/env_2026.csv', encoding='utf-8'))]
SH = [r for r in csv.DictReader(open(ROOT / 'data/tc2026/era5_shear.csv', encoding='utf-8'))]
for name in sys.argv[1:]:
    o = T[name]
    fx = [(dt.datetime.fromisoformat(t), w, p) for t, la, lo, w, p in o['fixes']]
    env = [r for r in E if r['name'] == name]
    sh = [(dt.datetime.fromisoformat(r['time']), float(r['shear_kt'])) for r in SH if r['name'] == name and r['shear_kt'] != '']
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True, gridspec_kw={'height_ratios': [1.3, 1, 0.8]})
    tw = [(t, int(w)) for t, w, p in fx if w.strip().isdigit()]
    a1.plot([t for t, _ in tw], [w for _, w in tw], color='#d1495b', lw=2, label='Max wind (kt, 1-min)')
    for th, lab in ((34, 'TS'), (64, 'Cat 1'), (96, 'Cat 3'), (113, 'Cat 4'), (137, 'Cat 5')):
        a1.axhline(th, color='#999', lw=0.6, ls=':'); a1.text(tw[0][0], th + 1, lab, fontsize=7, color='#777')
    for ep in o['ri_episodes']:
        a1.axvspan(dt.datetime.fromisoformat(ep['start']), dt.datetime.fromisoformat(ep['end']), color='#d1495b', alpha=0.12, lw=0)
    a1b = a1.twinx()
    tp = [(t, int(p)) for t, w, p in fx if p.strip().isdigit()]
    if tp:
        a1b.plot([t for t, _ in tp], [p for _, p in tp], color='#30638e', lw=1.2, ls='--', label='Min pressure (mb)')
        a1b.invert_yaxis(); a1b.set_ylabel('mb', fontsize=8)
    a1.set_ylabel('kt', fontsize=8); a1.set_title(f'{name.title()} (2026): intensity; shading = rapid intensification (≥30 kt in 24 h)', fontsize=10)
    h1, l1 = a1.get_legend_handles_labels(); h2, l2 = a1b.get_legend_handles_labels(); a1.legend(h1 + h2, l1 + l2, fontsize=8, frameon=False, loc='upper left')
    te = [(dt.datetime.fromisoformat(r['time']), r) for r in env if r['sst_pre_c'] not in ('nan', '')]
    a2.plot([t for t, _ in te], [float(r['sst_pre_c']) for _, r in te], color='#00798c', lw=2, label='SST 3 days before arrival (°C)')
    a2.axhline(26, color='#999', lw=0.6, ls=':'); a2.text(te[0][0], 26.1, '26 °C', fontsize=7, color='#777')
    a2b = a2.twinx()
    a2b.bar([t for t, _ in te], [float(r['ssta_pre_c']) for _, r in te], width=0.2, color='#edae49', alpha=0.6, label='SST anomaly vs 1991–2020 (°C)')
    a2b.axhline(0, color='#999', lw=0.6); a2b.set_ylabel('anomaly °C', fontsize=8)
    a2.set_ylabel('°C', fontsize=8)
    h1, l1 = a2.get_legend_handles_labels(); h2, l2 = a2b.get_legend_handles_labels(); a2.legend(h1 + h2, l1 + l2, fontsize=8, frameon=False, loc='upper right')
    a3.plot([t for t, _ in sh], [v for _, v in sh], color='#6b4c9a', lw=2, label='ERA5 200–850 hPa shear (kt)')
    for th in (10, 20):
        a3.axhline(th, color='#999', lw=0.6, ls=':')
    a3.set_ylabel('kt', fontsize=8); a3.legend(fontsize=8, frameon=False, loc='upper left')
    a3.xaxis.set_major_formatter(mdates.DateFormatter('%d %b')); a3.set_xlabel('UTC', fontsize=8)
    fig.text(0.01, 0.005, 'Data: IBTrACS v04r01 (provisional); NOAA OISST v2.1 daily; ERA5 (Copernicus C3S, to 18 Oct). Global Weather Watch.', fontsize=7, color='#666')
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(ROOT / f'papers/img/tc2026_{name.lower()}.png', dpi=120); plt.close(fig)
    print('saved', name)
