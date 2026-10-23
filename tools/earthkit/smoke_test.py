"""Smoke test for the earthkit setup in GitHub Actions: imports, a known calculation, an ECMWF open-data read and a map."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.earthkit.ek import ekd, meteo, plots  # noqa: E402

td = meteo.thermo.dewpoint_from_relative_humidity(np.array([293.15]), np.array([50.0]))[0] - 273.15
assert abs(td - 9.27) < 0.05, td
print(f'earthkit-meteo dewpoint(20 °C, 50%) = {td:.2f} °C')
ds = ekd.from_source('ecmwf-open-data', param='2t', levtype='sfc', step=0)
f = ds[0]; v = f.to_numpy()
print('ecmwf-open-data 2t:', f.metadata('date'), f.metadata('time'), v.shape, f'{v.min() - 273.15:.1f} to {v.max() - 273.15:.1f} °C')
out = Path('earthkit_smoke.png')
plots.quickplot(ds[0]).save(str(out))
print('earthkit-plots map:', out, out.stat().st_size, 'bytes')
assert out.stat().st_size > 20000
