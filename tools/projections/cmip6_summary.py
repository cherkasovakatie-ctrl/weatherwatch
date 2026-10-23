"""Summarise the CMIP6 table: per-model anomalies vs each model's 1850-1900 mean, ensemble percentiles, and warming in
2081-2100 against the IPCC AR6 assessed ranges (SPM Table SPM.1). Models need historical + the scenario to count.
Writes data/projections/cmip6_global_summary.csv and cmip6_warming_2081_2100.csv. Run locally or in Actions."""
import csv
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parents[2] / 'data' / 'projections'
rows = list(csv.DictReader(open(D / 'cmip6_tas_global_annual.csv')))
S = {}
for r in rows: S.setdefault((r['model'], r['experiment']), {})[int(r['year'])] = float(r['tas_c'])
models = sorted({m for m, e in S if e == 'historical' and len(S[(m, e)]) >= 150})
AR6 = {'ssp126': (1.8, 1.3, 2.4), 'ssp245': (2.7, 2.1, 3.5), 'ssp585': (4.4, 3.3, 5.7)}
out, warm = [], []
for exp in ('historical', 'ssp126', 'ssp245', 'ssp585'):
    ms = [m for m in models if (m, exp) in S]
    years = range(1850, 2015) if exp == 'historical' else range(2015, 2101)
    for y in years:
        v = []
        for m in ms:
            base = np.mean([S[(m, 'historical')][k] for k in range(1850, 1901) if k in S[(m, 'historical')]])
            if y in S[(m, exp)]: v.append(S[(m, exp)][y] - base)
        if len(v) >= 3:
            out.append(dict(experiment=exp, year=y, n_models=len(v), p10=round(np.percentile(v, 10), 3), p50=round(np.percentile(v, 50), 3),
                            p90=round(np.percentile(v, 90), 3), min=round(min(v), 3), max=round(max(v), 3)))
    if exp != 'historical':
        per = []
        for m in ms:
            base = np.mean([S[(m, 'historical')][k] for k in range(1850, 1901)])
            fut = [S[(m, exp)][k] for k in range(2081, 2101) if k in S[(m, exp)]]
            if len(fut) == 20: per.append((m, np.mean(fut) - base))
        vals = [v for _, v in per]
        c, lo, hi = AR6[exp]
        warm.append(dict(experiment=exp, n_models=len(vals), cmip6_p10=round(np.percentile(vals, 10), 2), cmip6_median=round(np.median(vals), 2),
                         cmip6_p90=round(np.percentile(vals, 90), 2), ar6_best=c, ar6_very_likely_low=lo, ar6_very_likely_high=hi,
                         models_above_ar6_range=';'.join(m for m, v in per if v > hi), models_below_ar6_range=';'.join(m for m, v in per if v < lo)))
for name, data in (('cmip6_global_summary.csv', out), ('cmip6_warming_2081_2100.csv', warm)):
    with open(D / name, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(data[0].keys()), lineterminator='\n'); w.writeheader(); w.writerows(data)
print('models with historical:', len(models)); [print(x) for x in warm]
