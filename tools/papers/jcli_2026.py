"""List Journal of Climate volume 39 (2026) articles with licence and open-access status (Crossref + OpenAlex).
Writes raw/papers/jcli2026/articles.csv and summary.txt."""
import csv, json, os, time, urllib.parse, urllib.request
UA = {'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:cherkasovakatie@gmail.com)'}
OUT = 'raw/papers/jcli2026'; os.makedirs(OUT, exist_ok=True)
def get(u):
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120))
        except Exception as e:
            err = e; time.sleep(5 * (i + 1))
    raise err
items, cursor = [], '*'
while True:
    u = ('https://api.crossref.org/journals/0894-8755/works?filter=from-pub-date:2025-10-01,until-pub-date:2026-12-31&rows=500'
         '&select=DOI,title,author,volume,issue,page,license,link,published,type&cursor=' + urllib.parse.quote(cursor))
    m = get(u)['message']; items += m['items']; cursor = m.get('next-cursor')
    if not m['items'] or not cursor: break
items = [x for x in items if str(x.get('volume')) == '39']
rows = []
for k in range(0, len(items), 50):
    chunk = items[k:k + 50]
    oa = get('https://api.openalex.org/works?per-page=50&filter=doi:' + '|'.join(x['DOI'] for x in chunk) + '&select=doi,open_access,best_oa_location,locations')
    by = {w['doi'].lower().replace('https://doi.org/', ''): w for w in oa['results']}
    for x in chunk:
        w = by.get(x['DOI'].lower(), {})
        lic = sorted({l.get('URL', '') for l in x.get('license', [])})
        pdfs = [l.get('URL') for l in x.get('link', []) if 'pdf' in (l.get('content-type') or '')]
        locs = [(l.get('pdf_url') or '', (l.get('license') or ''), ((l.get('source') or {}).get('display_name') or '')) for l in w.get('locations', [])]
        rows.append([x['DOI'], (x.get('title') or [''])[0], '; '.join(f"{a.get('family','')}, {a.get('given','')}" for a in x.get('author', [])[:3]) + (' et al.' if len(x.get('author', [])) > 3 else ''),
                     x.get('issue', ''), x.get('page', ''), '|'.join(lic), (w.get('open_access') or {}).get('oa_status', ''),
                     ((w.get('best_oa_location') or {}).get('license') or ''), ((w.get('best_oa_location') or {}).get('pdf_url') or ''),
                     '|'.join(pdfs), json.dumps(locs)])
    time.sleep(1)
with open(f'{OUT}/articles.csv', 'w', newline='') as fh:
    wr = csv.writer(fh); wr.writerow(['doi', 'title', 'authors', 'issue', 'pages', 'crossref_license', 'oa_status', 'oa_license', 'oa_pdf_url', 'crossref_pdf_links', 'openalex_locations']); wr.writerows(rows)
from collections import Counter
s = [f'articles {len(rows)}', 'oa_status ' + str(Counter(r[6] for r in rows)), 'oa_license ' + str(Counter(r[7] for r in rows)),
     'crossref licence urls ' + str(Counter(u for r in rows for u in r[5].split('|') if u)), 'issues ' + str(sorted(Counter(r[3] for r in rows).items()))]
open(f'{OUT}/summary.txt', 'w').write('\n'.join(s) + '\n'); print('\n'.join(s))
