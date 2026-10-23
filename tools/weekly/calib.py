"""One-off: Greenland south-dome and east point calibration grids (one Open-Meteo call per point). Delete after use."""
import itertools, json, time, urllib.parse, urllib.request, datetime as dt
from pathlib import Path
OUT = Path('raw') / (dt.date.today().isoformat() + '-calib'); OUT.mkdir(parents=True, exist_ok=True)
for tag, lats, lons in (('south', [61.0, 61.5, 62.0, 62.5, 63.0, 63.5, 64.0, 64.5, 65.0], [-48.0, -47.0, -46.0, -45.0, -44.0, -43.0, -42.0]),
                        ('east', [66.0, 67.0, 68.0, 69.0, 70.0, 71.0, 72.0, 73.0], [-40.0, -36.0, -32.0, -28.0, -25.0, -22.0])):
    res = []
    for la, lo in itertools.product(lats, lons):
        q = urllib.parse.urlencode(dict(latitude=la, longitude=lo, daily='temperature_2m_max', past_days=30, forecast_days=1, timezone='UTC'))
        try:
            res.append(json.loads(urllib.request.urlopen('https://api.open-meteo.com/v1/forecast?' + q, timeout=60).read()))
        except Exception as e:
            res.append({'latitude': la, 'longitude': lo, 'error': str(e)})
        time.sleep(0.3)
    (OUT / f'om_glgrid_{tag}.json').write_text(json.dumps(res)); print(tag, len(res), sum('error' in r for r in res), 'errors')
