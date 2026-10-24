"""IBTrACS v04r01 subset for the El Nino papers: 6-hourly fixes within 30S-30N, 90E-160W for event years.
Writes raw/papers/ibtracs/tc_fixes_tropwp.csv (sid, name, basin, time, lat, lon, wind_kt) and a log."""
import csv, io, os, urllib.request
B = 'https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/'
OUT = 'raw/papers/ibtracs'; os.makedirs(OUT, exist_ok=True)
YEARS = {1981, 1982, 1983, 1996, 1997, 1998, 2014, 2015, 2016, 2025, 2026}
rows, seen, log = [], set(), []
for f in ('ibtracs.since1980.list.v04r01.csv', 'ibtracs.last3years.list.v04r01.csv'):
    raw = urllib.request.urlopen(urllib.request.Request(B + f, headers={'User-Agent': 'GlobalWeatherWatch/1.0'}), timeout=600).read().decode('utf-8', 'replace')
    r = csv.reader(io.StringIO(raw)); hdr = next(r); next(r)
    ix = {k: hdr.index(k) for k in ('SID', 'NAME', 'BASIN', 'ISO_TIME', 'LAT', 'LON', 'WMO_WIND', 'USA_WIND', 'TRACK_TYPE')}
    last = ''
    for x in r:
        t = x[ix['ISO_TIME']]; last = max(last, t)
        if int(t[:4]) not in YEARS or t[11:13] not in ('00', '06', '12', '18'):
            continue
        lat, lon = float(x[ix['LAT']]), float(x[ix['LON']]) % 360
        if not (-30 <= lat <= 30 and 90 <= lon <= 200):
            continue
        key = (x[ix['SID']], t)
        if key in seen:
            continue
        seen.add(key)
        w = x[ix['USA_WIND']].strip() or x[ix['WMO_WIND']].strip()
        rows.append([x[ix['SID']], x[ix['NAME']], x[ix['BASIN']], t[:16], lat, lon, w, x[ix['TRACK_TYPE']]])
    log.append(f'{f}: last time {last}')
rows.sort(key=lambda z: (z[3], z[0]))
with open(f'{OUT}/tc_fixes_tropwp.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['sid', 'name', 'basin', 'time', 'lat', 'lon', 'wind_kt', 'track_type']); w.writerows(rows)
open(f'{OUT}/log.txt', 'w').write('\n'.join(log) + f'\nrows {len(rows)}\n')
print('\n'.join(log), len(rows))
