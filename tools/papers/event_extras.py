"""Extra observations for an event window (env W0/W1, OUT): TAO/TRITON daily moorings via ERDDAP, BoM RMM,
UHSLC daily island sea level. Saves raw responses with a log; nothing is interpreted here."""
import os, time, urllib.request, urllib.parse
W0, W1 = os.environ.get('W0', '1996-01-01'), os.environ.get('W1', '1998-06-30')
OUT = os.environ.get('OUT', 'probe'); os.makedirs(OUT, exist_ok=True)
LOG = []
def get(name, url, tries=3, timeout=300):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'GlobalWeatherWatch/1.0 (research; github.com/cherkasovakatie-ctrl/weatherwatch)'}), timeout=timeout) as r:
                b = r.read()
            open(f'{OUT}/{name}', 'wb').write(b); LOG.append(f'OK   {name} {len(b)} | {url}'); return b
        except Exception as e:
            err = str(e); time.sleep(8 * (i + 1))
    LOG.append(f'FAIL {name} {err[:160]} | {url}')
# TAO/TRITON daily: 20 C isotherm depth, winds, SST along the equator
for host in ('https://coastwatch.pfeg.noaa.gov/erddap', 'https://data.pmel.noaa.gov/pmel/erddap'):
    tag = 'cw' if 'coastwatch' in host else 'pmel'
    for ds, var in (('pmelTaoDyIso', 'ISO_6'), ('pmelTaoDyW', 'WU_422,WV_423'), ('pmelTaoDySst', 'T_25'), ('pmelTaoDyD', 'D_3')):
        q = f'time,latitude,longitude,{var}&latitude>=-0.5&latitude<=0.5&time>={W0}&time<={W1}T23:59:59Z'
        get(f'tao_{tag}_{ds}.csv', f'{host}/tabledap/{ds}.csv?{urllib.parse.quote(q, safe="=&,><:")}')
    get(f'tao_{tag}_index.csv', f'{host}/search/index.csv?searchFor=pmelTao%20daily&page=1&itemsPerPage=200')
# BoM RMM (Wheeler-Hendon 2004)
get('bom_rmm.txt', 'http://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt')
get('psl_rmm.txt', 'https://psl.noaa.gov/mjo/mjoindex/rmm.74toRealtime.txt')
# UHSLC daily fast-delivery/research quality sea level: Nauru (1), Christmas (?), Santa Cruz (30), Kanton, Tarawa, Kapingamarangi
for sid in ('001', '002', '003', '004', '005', '007', '008', '029', '030', '031', '113', '114', '109'):
    get(f'uhslc_d{sid}.csv', f'https://uhslc.soest.hawaii.edu/data/csv/rqds/pacific/daily/d{sid}a.csv', tries=1)
open(f'{OUT}/log.txt', 'w').write('\n'.join(LOG) + '\n'); print('\n'.join(LOG))
