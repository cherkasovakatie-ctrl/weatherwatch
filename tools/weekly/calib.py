"""One-off extra fetch: GDACS SEARCH lists per hazard type (last 60 days) and their TC geometries. Delete after use."""
import json, time, urllib.request, datetime as dt
from pathlib import Path
OUT = Path('raw') / (dt.date.today().isoformat() + '-more'); OUT.mkdir(parents=True, exist_ok=True)
T = dt.date.today(); F = T - dt.timedelta(60)
def get(name, url):
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=120).read()
        (OUT / name).write_bytes(b); print('OK', name, len(b)); return b
    except Exception as e:
        print('FAIL', name, e, url)
for ev in ('TC', 'FL', 'DR', 'VO', 'WF', 'EQ'):
    b = get(f'gdacs_search_{ev}.json', f'https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist={ev}&fromDate={F}&toDate={T}&alertlevel=green;orange;red')
    if ev == 'TC' and b:
        for f in json.loads(b)['features']:
            p = f['properties']
            if p.get('todate', '') >= str(T - dt.timedelta(14)):
                get(f"gdacs_tc_{p['eventid']}_{p['episodeid']}.json", f"https://www.gdacs.org/gdacsapi/api/polygons/getgeometry?eventtype=TC&eventid={p['eventid']}&episodeid={p['episodeid']}")
                time.sleep(1)
# Greenland south-dome and east calibration grids (one Open-Meteo call per point)
import itertools, urllib.parse
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
