"""Fetch the raw sources for the Friday weekly refresh into raw/<date>/ (runs in GitHub Actions on branch weekly-raw).

Only public, keyless endpoints. Every response is saved as-is with a log line (status, bytes, last line), so the
agent doing the weekly review can check the newest date in each file before using it. Nothing here edits data/.
Run: python3 tools/weekly/fetch_raw.py
"""
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

TODAY = dt.date.today()
OUT = Path('raw') / TODAY.isoformat(); OUT.mkdir(parents=True, exist_ok=True)
LOG = []
UA = 'GlobalWeatherWatch/1.0 (weekly refresh; github.com/cherkasovakatie-ctrl/weatherwatch)'


def get(name, url, tries=3, timeout=120):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout) as r:
                b = r.read()
            (OUT / name).write_bytes(b)
            tail = b.decode('utf-8', 'replace').strip().splitlines()[-1:] if b else ['']
            LOG.append(f'OK   {name} {len(b)} bytes | last: {tail[0][:160] if tail else ""} | {url}')
            return b
        except Exception as e:
            err = str(e)
            time.sleep(5 * (i + 1))
    LOG.append(f'FAIL {name} {err[:200]} | {url}')
    return None


def om(name, base, **params):
    return get(name, base + '?' + urllib.parse.urlencode(params, safe=',:'))


# ---- ENSO and drivers
get('psl_romi.cpcolr.1x.txt', 'https://psl.noaa.gov/mjo/mjoindex/romi.cpcolr.1x.txt')  # real-time OMI (CPC OLR)
get('pmel_wwv.dat', 'https://www.pmel.noaa.gov/tao/wwv/data/wwv.dat')
get('cpc_ao_daily.csv', 'https://ftp.cpc.ncep.noaa.gov/cwlinks/norm.daily.ao.cdas.z1000.19500101_current.csv')
# ---- hazards
get('nhc_currentstorms.json', 'https://www.nhc.noaa.gov/CurrentStorms.json')
F = TODAY - dt.timedelta(60)
for evt in ('TC', 'FL', 'DR', 'VO', 'WF', 'EQ'):
    b = get(f'gdacs_search_{evt}.json', f'https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist={evt}&fromDate={F}&toDate={TODAY}&alertlevel=green;orange;red')
try:
    feats = json.loads((OUT / 'gdacs_search_TC.json').read_bytes())['features']
    for f in feats:
        p = f['properties']
        if p.get('todate', '') >= str(TODAY - dt.timedelta(14)):
            get(f"gdacs_tc_{p['eventid']}_{p['episodeid']}.json",
                f"https://www.gdacs.org/gdacsapi/api/polygons/getgeometry?eventtype=TC&eventid={p['eventid']}&episodeid={p['episodeid']}", tries=2)
except Exception as e:
    LOG.append(f'FAIL gdacs TC geometry: {e}')
# Smithsonian weekly volcano report blocks automated requests (HTTP 403): read it by hand.
for loc in ('northatlantic', 'northeastpacific', 'northwestpacific', 'northindian', 'southindian', 'southpacific', 'northernhemisphere'):
    get(f'csu_{loc}.html', f'https://tropical.atmos.colostate.edu/Realtime/index.php?loc={loc}', tries=2)
for loc in ('atlantic', 'northeastpacific', 'northwestpacific', 'northindian', 'southindian', 'southpacific', 'northernhemisphere'):
    get(f'csu_climo_{loc}.csv', f'https://tropical.atmos.colostate.edu/Includes/Documents/Realtime/{loc}acetodatevsclimo.csv', tries=2)
# ---- Southern California and poles
stations = 'SHA,ORO,CLE,NML,SNL,BER,EXC,PNF,FOL,BUL,PYM,CAS,PRR'
get('cdec_res.html', 'https://cdec.water.ca.gov/reportapp/javareports?name=RES')
get('cdec_storage.csv', f'https://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={stations}&SensorNums=15&dur_code=D&Start={TODAY - dt.timedelta(10)}&End={TODAY}')
FC = 'https://api.open-meteo.com/v1/forecast'
PTS = {'vv': (34.165, -118.396), 'sf': (37.77, -122.42), 'off_a': (33.5, -119.5)}
for k, (la, lo) in PTS.items():
    om(f'om_ar_{k}.json', FC, latitude=la, longitude=lo, hourly='total_column_integrated_water_vapour', daily='precipitation_sum',
       past_days=7, forecast_days=16, timezone='America/Los_Angeles')
RIDGE = {'coast40': (40, -130), 'coast33': (33, -125), 'alaska50': (50, -140)}
for k, (la, lo) in RIDGE.items():
    om(f'om_ridge_{k}.json', FC, latitude=la, longitude=lo, hourly='geopotential_height_500hPa', past_days=7, forecast_days=16, timezone='UTC')
    for y in range(2021, 2026):
        om(f'om_ridge_{k}_{y}.json', 'https://historical-forecast-api.open-meteo.com/v1/forecast', latitude=la, longitude=lo,
           hourly='geopotential_height_500hPa', start_date=f'{y}-10-01', end_date=f'{y}-11-25', timezone='UTC')
om('om_coast_lax.json', FC, latitude=33.94, longitude=-118.41, hourly='pressure_msl,wind_gusts_10m,relative_humidity_2m', past_days=7, forecast_days=7,
   timezone='America/Los_Angeles', wind_speed_unit='mph')
om('om_coast_tonopah.json', FC, latitude=38.07, longitude=-117.09, hourly='pressure_msl', past_days=7, forecast_days=7, timezone='America/Los_Angeles')
co = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'
b, e = (TODAY - dt.timedelta(9)).strftime('%Y%m%d'), (TODAY + dt.timedelta(1)).strftime('%Y%m%d')
get('coops_obs.json', f'{co}?product=water_level&station=9410660&begin_date={b}&end_date={e}&datum=MLLW&units=english&time_zone=lst_ldt&format=json&interval=h')
get('coops_obs6.json', f'{co}?product=water_level&station=9410660&begin_date={b}&end_date={e}&datum=MLLW&units=english&time_zone=lst_ldt&format=json')
get('coops_pred.json', f'{co}?product=predictions&station=9410660&begin_date={b}&end_date={e}&datum=MLLW&units=english&time_zone=lst_ldt&format=json&interval=30')
POLAR = {'North Pole': (89.9, 0), 'Alert, Nunavut': (82.5, -62.35), 'Longyearbyen, Svalbard': (78.22, 15.63), 'Summit, Greenland': (72.58, -38.46),
         'Utqiagvik, Alaska': (71.29, -156.79), 'South Pole': (-89.9, 0), 'Vostok': (-78.46, 106.84), 'McMurdo': (-77.85, 166.67),
         'Rothera, Antarctic Peninsula': (-67.57, -68.13)}
for i, (k, (la, lo)) in enumerate(POLAR.items()):
    om(f'om_polar_{i}_now.json', FC, latitude=la, longitude=lo, current='temperature_2m,wind_speed_10m', daily='temperature_2m_mean', forecast_days=1, timezone='UTC')
    om(f'om_polar_{i}_clim.json', 'https://archive-api.open-meteo.com/v1/archive', latitude=la, longitude=lo, start_date='1991-01-01', end_date='2020-12-31',
       daily='temperature_2m_mean', timezone='UTC')
    time.sleep(2)
for lo in range(-180, 180, 45):
    om(f'om_u10hpa_{lo}.json', 'https://api.open-meteo.com/v1/gfs', latitude=60, longitude=lo, hourly='wind_speed_10hPa,wind_direction_10hPa',
       past_days=7, forecast_days=16, timezone='UTC')
# Greenland points used by poles_daily (see its manifest description)
GL = {'summit': (72.58, -38.46), 'kanger_b': (67.0, -47.0), 'south': (60.98, -44.03), 'nw_b': (77.0, -61.0), 'east': (72.93, -28.06)}
for k, (la, lo) in GL.items():
    om(f'om_gl_{k}.json', FC, latitude=la, longitude=lo, daily='temperature_2m_max', past_days=30, forecast_days=16, timezone='UTC')
# ---- monthly / other
get('usno_finals2000A.data', 'https://maia.usno.navy.mil/ser7/finals2000A.data', tries=1)
get('lsa_gmsl.csv', 'https://www.star.nesdis.noaa.gov/socd/lsa/SeaLevelRise/slr/slr_sla_gbl_free_ref_90.csv')
(OUT / 'fetch_log.txt').write_text('\n'.join(LOG) + '\n')
print('\n'.join(LOG))
