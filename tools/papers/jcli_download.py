"""Download openly licensed J Climate 2026 articles: CC BY publisher versions (AMS) and CC-licensed repository/preprint copies.
Writes raw/papers/jcli2026/pdf/<doi-suffix>[_preprint].pdf and download_log.csv (doi, version, licence, url tried, status, bytes)."""
import csv, json, os, time, urllib.request
OUT = 'raw/papers/jcli2026/pdf'; os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) GlobalWeatherWatch/1.0 research-library', 'Accept': 'application/pdf,*/*'}
rows = list(csv.DictReader(open('raw/papers/jcli2026/articles.csv')))
log = []
def fetch(url, dst):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
            b = r.read()
        if b[:5] != b'%PDF-':
            return f'not pdf ({b[:30]!r})', 0
        open(dst, 'wb').write(b); return 'ok', len(b)
    except Exception as e:
        return str(e)[:120], 0
for r in rows:
    pub_cc = 'creativecommons' in r['crossref_license']
    locs = json.loads(r['openalex_locations'])
    suf = r['doi'].split('/')[-1]
    if pub_cc:
        cands = [u for u in r['crossref_pdf_links'].split('|') if u] + [f"https://journals.ametsoc.org/downloadpdf/view/journals/clim/39/{r['issue']}/{suf.upper().replace('JCLI-D', 'JCLI-D')}.pdf"]
        for u in cands:
            st, n = fetch(u, f'{OUT}/{suf}.pdf'); log.append([r['doi'], 'publisher', 'cc-by-4.0', u, st, n])
            if st == 'ok': break
            time.sleep(2)
    elif r['oa_license'].startswith('cc-'):
        for u, lic, src in locs:
            if u and lic.startswith('cc-'):
                st, n = fetch(u, f'{OUT}/{suf}_preprint.pdf'); log.append([r['doi'], f'repository ({src})', lic, u, st, n])
                if st == 'ok': break
                time.sleep(2)
        else:
            if not any(u and lic.startswith('cc-') for u, lic, src in locs):
                log.append([r['doi'], 'none', r['oa_license'], '', 'no licensed copy with a PDF URL', 0])
with open('raw/papers/jcli2026/download_log.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['doi', 'version', 'licence', 'url', 'status', 'bytes']); w.writerows(log)
print(sum(1 for x in log if x[4] == 'ok'), 'downloaded;', len(log), 'attempts')
