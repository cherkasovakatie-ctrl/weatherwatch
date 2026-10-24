"""Download NHC forecast discussions (TCD) and any Tropical Cyclone Report for 2026 Atlantic/eastern/central Pacific hurricanes.
Public-domain US Government text. Writes raw/papers/nhc/<STORM>/discus_NNN.txt and index.txt."""
import os, re, sys, time, urllib.request, html
UA = {'User-Agent': 'GlobalWeatherWatch/1.0 (research site)'}
def get(u):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read().decode('utf-8', 'replace')
        except Exception as e:
            err = e; time.sleep(5 * (i + 1))
    raise err
storms = sys.argv[1:]
for s in storms:
    d = f'raw/papers/nhc/{s}'; os.makedirs(d, exist_ok=True)
    page = get(f'https://www.nhc.noaa.gov/archive/2026/{s}.shtml?')
    links = sorted(set(re.findall(r'/archive/2026/[a-z]{2}\d{2}/[a-z]{2}\d{6}\.discus\.\d{3}\.shtml', page)))
    idx = []
    for l in links:
        t = get('https://www.nhc.noaa.gov' + l)
        m = re.search(r'<pre>(.*?)</pre>', t, re.S)
        txt = html.unescape(re.sub('<[^>]+>', '', m.group(1))) if m else ''
        n = l.split('.')[-2]
        open(f'{d}/discus_{n}.txt', 'w').write(txt); idx.append(l); time.sleep(0.5)
    open(f'{d}/index.txt', 'w').write('\n'.join(idx) + '\n')
    print(s, len(idx))
