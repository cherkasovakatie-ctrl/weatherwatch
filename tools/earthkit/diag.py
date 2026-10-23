"""earthkit diagnostics: each stage reported separately into raw/<date>-earthkit/log.txt."""
import sys, traceback, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
OUT = Path('raw') / (dt.date.today().isoformat() + '-earthkit'); OUT.mkdir(parents=True, exist_ok=True)
log = []
def stage(name, fn):
    try:
        r = fn(); log.append(f'OK   {name}: {r}')
    except Exception:
        log.append(f'FAIL {name}:\n' + traceback.format_exc()[-2500:])
import numpy as np
stage('import', lambda: __import__('tools.earthkit.ek', fromlist=['ekd']).__name__)
from tools.earthkit.ek import ekd, meteo, plots
stage('meteo', lambda: float(meteo.thermo.dewpoint_from_relative_humidity(np.array([293.15]), np.array([50.0]))[0] - 273.15))
box = {}
def od():
    ds = ekd.from_source('ecmwf-open-data', param='2t', levtype='sfc', step=0); box['ds'] = ds
    f = ds[0]; return f"{f.metadata('date')} {f.metadata('time')} shape={f.to_numpy().shape}"
stage('open-data', od)
def qp():
    plots.quickplot(box['ds'][0]).save(str(OUT / 'map.png')); return (OUT / 'map.png').stat().st_size
stage('plots', qp)
def cds():
    import os; return 'cdsapirc present' if os.path.exists(os.path.expanduser('~/.cdsapirc')) else 'no cdsapirc (expected here)'
stage('cds-config', cds)
(OUT / 'log.txt').write_text('\n'.join(log) + '\n'); print('\n'.join(log))
