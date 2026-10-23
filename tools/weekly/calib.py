"""One-off extra fetch: CSU real-time ACE-to-date vs climatology CSVs. Delete after use."""
import urllib.request, datetime as dt
from pathlib import Path
OUT = Path('raw') / (dt.date.today().isoformat() + '-csu'); OUT.mkdir(parents=True, exist_ok=True)
for loc in ('atlantic', 'northatlantic', 'northeastpacific', 'northwestpacific', 'northindian', 'southindian', 'southpacific', 'northernhemisphere'):
    url = f'https://tropical.atmos.colostate.edu/Includes/Documents/Realtime/{loc}acetodatevsclimo.csv'
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=60).read()
        (OUT / f'{loc}.csv').write_bytes(b); print('OK', loc, len(b))
    except Exception as e:
        print('FAIL', loc, e)
