"""Objective propagation test and Hovmöller figures for candidate MJO episodes, Nov 1981 – Dec 1982.

Inputs (data/papers/1982/, produced by tools/papers/mjo_1982_diag.py from NCEP/NCAR R1 and NOAA interpolated OLR):
  hov_olr_20_100.csv, hov_u850_20_100.csv, hov_u200_20_100.csv  20–100-day band-passed anomalies, 10°S–10°N mean, 5° longitude
  hov_u1000_anom_5S5N.csv                                       unfiltered 1000 hPa zonal-wind anomaly, 5°S–5°N mean
  psl_mjo_indices_1981_83.csv                                   NOAA PSL OMI, FMO, VPM (NCEP/NCAR R1 version), RMM*

Propagation test (version 2). Version 1 tracked the single daily OLR minimum and required day-to-day continuity; it failed every
window because the minimum jumps between separate convective systems and convection weakens over the Maritime Continent.
It was replaced, before results were interpreted, by a two-box sequence test plus a lag-correlation speed check:
  T1 Indian Ocean convection: filtered OLR over 70°E–100°E reaches ≤ −15 W m⁻² on day t1 (the earliest such minimum in the window).
  T2 western Pacific convection: filtered OLR over 140°E–180° reaches ≤ −15 W m⁻² on day t2 with 8 ≤ t2 − t1 ≤ 35 days
     (≈ 2.4–10.4 m s⁻¹ over the ~65° between box centres).
  T3 lag-correlation speed: for each longitude 60°E–180°, the lag (−5…+35 days) of maximum correlation of filtered OLR with the
     70°–100°E mean; a least-squares fit over longitudes with r ≥ 0.4 must give an eastward speed of 2–10 m s⁻¹ (reported, not required).
  T4 circulation: on day t2 ± 2 days, filtered u850 averaged over the 30° west of the western-Pacific convective centre is > 0
     and filtered u200 there is < 0 on at least 3 of the 5 days (first-baroclinic MJO structure).
  PASS = T1 and T2 and T4.  Passing makes an episode "MJO-like intraseasonal activity"; it says nothing about cause.
Run: python3 tools/papers/mjo_1982_tests.py   (writes data/papers/1982/propagation_tests.json and papers/img/*.png)
"""
import csv
import datetime as dt
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data' / 'papers' / '1982'


def load(name):
    with open(D / name) as fh:
        rows = list(csv.reader(fh))
    lon = np.array([float(x) for x in rows[0][1:]])
    dates = [dt.date.fromisoformat(r[0]) for r in rows[1:]]
    return dates, lon, np.array([[float(x) for x in r[1:]] for r in rows[1:]])


dates, lon, olr = load('hov_olr_20_100.csv')
_, _, u850 = load('hov_u850_20_100.csv')
_, _, u200 = load('hov_u200_20_100.csv')
_, _, usfc = load('hov_u1000_anom_5S5N.csv')
idx = {r['date']: r for r in csv.DictReader(open(D / 'psl_mjo_indices_1981_83.csv'))}

WINDOWS = {
    'Nov 1981 – Jan 1982': ('1981-11-10', '1982-01-10'),
    'Mar – Apr 1982': ('1982-03-05', '1982-04-15'),
    'Apr – May 1982': ('1982-04-10', '1982-05-25'),
    'Jun – Jul 1982': ('1982-06-05', '1982-07-25'),
    'Aug – Sep 1982': ('1982-07-25', '1982-09-10'),
    'Oct – Nov 1982': ('1982-10-15', '1982-11-30'),
    'Dec 1982': ('1982-11-25', '1982-12-31'),
}
SEL = (lon >= 60) & (lon <= 210)
DEG_M = 111e3


def test(a, b):
    ii = [i for i, d in enumerate(dates) if a <= d.isoformat() <= b]
    io = (lon >= 70) & (lon <= 100); wp = (lon >= 140) & (lon <= 180)
    o_io = olr[ii][:, io].min(1); o_wp = olr[ii][:, wp].min(1)
    out = {'window': f'{a} to {b}'}
    t1s = [k for k in range(len(ii)) if o_io[k] <= -15]
    if not t1s:
        return out | {'T1': False, 'T2': False, 'T3': None, 'T4': False, 'PASS': False}
    # earliest IO minimum: the deepest day within the first active IO spell
    k0 = t1s[0]; k1 = k0
    while k1 + 1 < len(ii) and o_io[k1 + 1] <= -15: k1 += 1
    t1 = k0 + int(np.argmin(o_io[k0:k1 + 1]))
    t2c = [k for k in range(len(ii)) if 8 <= k - t1 <= 35 and o_wp[k] <= -15]
    out |= {'T1': True, 'io_date': dates[ii[t1]].isoformat(), 'io_min': round(float(o_io[t1]), 1)}
    # lag-correlation speed (T3)
    ref = olr[ii][:, io].mean(1); lags, lons = [], []
    for j, L in enumerate(lon):
        if not (60 <= L <= 180): continue
        best = (-1, None)
        for lag in range(-5, 36):
            x = ref[max(0, -lag):len(ref) - max(0, lag)]; y = olr[ii][max(0, lag):len(ref) - max(0, -lag), j]
            if len(x) > 15:
                r = np.corrcoef(x, y)[0, 1]
                if r > best[0]: best = (r, lag)
        if best[0] >= 0.4: lags.append(best[1]); lons.append(L)
    if len(lons) >= 5 and np.ptp(lags) > 0:
        sl = np.polyfit(lags, lons, 1)[0]; spd = sl * DEG_M / 86400
        out |= {'lagcorr_speed_ms': round(float(spd), 1), 'lagcorr_n_lon': len(lons)}; T3 = bool(2 <= spd <= 10)
    else:
        T3 = False; out |= {'lagcorr_speed_ms': None, 'lagcorr_n_lon': len(lons)}
    if not t2c:
        return out | {'T2': False, 'T3': T3, 'T4': False, 'PASS': False}
    # deepest WP minimum within the first qualifying WP spell
    k0 = t2c[0]; k1 = k0
    while k1 + 1 < len(ii) and o_wp[k1 + 1] <= -15: k1 += 1
    t2 = k0 + int(np.argmin(o_wp[k0:k1 + 1]))
    cen = lon[wp][olr[ii[t2]][wp].argmin()]
    span = (lon >= cen - 30) & (lon < cen)
    good = sum(1 for k in range(max(0, t2 - 2), min(len(ii), t2 + 3)) if u850[ii[k]][span].mean() > 0 and u200[ii[k]][span].mean() < 0)
    T4 = good >= 3
    return out | {'T2': True, 'wp_date': dates[ii[t2]].isoformat(), 'wp_min': round(float(o_wp[t2]), 1), 'wp_centre_E': float(cen), 'lag_days': t2 - t1,
                  'T3': T3, 'baroclinic_days_of_5': good, 'T4': bool(T4), 'PASS': bool(T4)}


def avail(a, b):
    """Which published indices have values in the window, and their maximum amplitude."""
    res = {}
    for k in ('omi', 'fmo', 'vpm', 'rmmstar'):
        v = [float(r[f'{k}_amp']) for d, r in idx.items() if a <= d <= b and r[f'{k}_amp'] != '']
        res[k] = round(max(v), 2) if v else None
    return res


results = {n: test(a, b) | {'index_max_amp': avail(a, b)} for n, (a, b) in WINDOWS.items()}
json.dump({'method': __doc__.split('Run:')[0].strip(), 'results': results}, open(D / 'propagation_tests.json', 'w'), indent=1, ensure_ascii=False)
for n, r in results.items():
    print(n, {k: v for k, v in r.items() if k not in ('window', 'index_max_amp')}, r['index_max_amp'])

# Figures: daily Hovmöllers (OLR shading, u850 contours, burst days marked)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

PANELS = [('1981-11-01', '1982-02-15', 'mjo1982_hov_a.png', 'Nov 1981 – mid-Feb 1982'),
          ('1982-03-01', '1982-07-31', 'mjo1982_hov_b.png', 'Mar – Jul 1982'),
          ('1982-08-01', '1982-12-31', 'mjo1982_hov_c.png', 'Aug – Dec 1982')]
x = lon <= 270
for a, b, fn, title in PANELS:
    ii = [i for i, d in enumerate(dates) if a <= d.isoformat() <= b]
    tt = np.array([dates[i].toordinal() for i in ii])
    fig, ax = plt.subplots(figsize=(6.2, 7.2), dpi=130)
    pc = ax.pcolormesh(lon[x], tt, olr[ii][:, x], cmap='RdBu_r', norm=TwoSlopeNorm(0, -40, 40), shading='nearest')
    cs = ax.contour(lon[x], tt, u850[ii][:, x], levels=[-4, -2, 2, 4], colors=['#555', '#555', 'k', 'k'], linewidths=[.6, .6, .9, 1.4], linestyles=['dashed', 'dashed', 'solid', 'solid'])
    burst = (usfc[ii][:, x] >= 5) & (lon[x] >= 120) & (lon[x] <= 210)
    yy, xx = np.where(burst)
    ax.scatter(lon[x][xx], tt[yy], s=4, c='#e0a000', marker='s', linewidths=0, label='1000 hPa anomaly ≥ 5 m s⁻¹ (120°E–150°W)')
    ticks = [dt.date(y, m, 1) for y in (1981, 1982, 1983) for m in range(1, 13) if a <= dt.date(y, m, 1).isoformat() <= b]
    ax.set_yticks([d.toordinal() for d in ticks]); ax.set_yticklabels([d.strftime('%b %Y') for d in ticks], fontsize=8)
    ax.set_xticks([60, 90, 120, 150, 180, 210, 240, 270]); ax.set_xticklabels(['60°E', '90°E', '120°E', '150°E', '180°', '150°W', '120°W', '90°W'], fontsize=8)
    ax.set_xlim(40, 270)
    ax.set_title(f'{title}: 20–100-day OLR (shading, W m⁻²) and u850 (contours ±2, ±4 m s⁻¹)\n10°S–10°N; NOAA interpolated OLR, NCEP/NCAR R1', fontsize=8)
    cb = fig.colorbar(pc, ax=ax, orientation='horizontal', fraction=.04, pad=.06); cb.set_label('OLR anomaly (W m⁻²); red = suppressed, blue = enhanced convection', fontsize=8); cb.ax.tick_params(labelsize=7)
    ax.legend(loc='upper right', fontsize=7, framealpha=.85)
    fig.tight_layout(); fig.savefig(ROOT / 'papers' / 'img' / fn); plt.close(fig)
print('figures written')
