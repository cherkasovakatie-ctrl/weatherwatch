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
