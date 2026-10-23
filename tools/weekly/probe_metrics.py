"""Probe CPC's official ENSO probability sources (figure01 bar chart and the RONI strength page)."""
import datetime as dt, urllib.request
from pathlib import Path
OUT = Path('raw') / (dt.date.today().isoformat() + '-cpcprob'); OUT.mkdir(parents=True, exist_ok=True)
urls = {
    'cpc_figure01.gif': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/figure01.gif',
    'cpc_strengths.html': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths/',
    'cpc_strengths_index.html': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths/index.php',
    'cpc_ensodisc.html': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml',
    'cpc_roni_dir.html': 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/',
}
log = []
for name, u in urls.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 GlobalWeatherWatch/1.0'}), timeout=60)
        b = r.read(); (OUT / name).write_bytes(b); log.append(f'OK   {name} {r.headers.get("Content-Type", "")} {len(b)}')
    except Exception as e:
        log.append(f'FAIL {name} {str(e)[:120]}')
(OUT / 'log.txt').write_text('\n'.join(log) + '\n'); print('\n'.join(log))
