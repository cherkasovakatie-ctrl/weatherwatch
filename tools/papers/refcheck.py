"""Bibliographic check for a list of references (tools/papers/refs_<tag>.tsv: key<TAB>doi-or-search-query).
For each: Crossref record (title, journal, volume, issue, pages, year, authors) and OpenAlex (abstract, OA status,
best open copy). Output JSON in raw/papers/<tag>/refs.json. Nothing is interpreted here."""
import json, os, sys, time, urllib.parse, urllib.request
TAG = sys.argv[1]
OUT = f'raw/papers/{TAG}'; os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'GlobalWeatherWatch/1.0 (research; https://github.com/cherkasovakatie-ctrl/weatherwatch)'}
def getj(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: return json.load(r)
        except Exception as e:
            err = str(e); time.sleep(3 * (i + 1))
    return {'error': err}
def abstract(inv):
    if not inv: return None
    pos = sorted((p, w) for w, ps in inv.items() for p in ps); return ' '.join(w for _, w in pos)
res = {}
for line in open(f'tools/papers/refs_{TAG}.tsv', encoding='utf-8'):
    if not line.strip() or line.startswith('#'): continue
    key, q = line.rstrip('\n').split('\t', 1)
    if q.startswith('10.'):
        cr = getj('https://api.crossref.org/works/' + urllib.parse.quote(q, safe='/()<>;:.'))
        m = cr.get('message', {}) if 'message' in cr else {}
        cands = [m] if m else []
    else:
        cr = getj('https://api.crossref.org/works?rows=3&query.bibliographic=' + urllib.parse.quote(q))
        cands = cr.get('message', {}).get('items', []) if 'message' in cr else []
    out = []
    for m in cands:
        doi = m.get('DOI')
        oa = getj('https://api.openalex.org/works/doi:' + urllib.parse.quote(doi, safe='/()<>;:.')) if doi else {}
        out.append({'doi': doi, 'title': (m.get('title') or [''])[0], 'journal': (m.get('container-title') or [''])[0],
                    'volume': m.get('volume'), 'issue': m.get('issue'), 'page': m.get('page'),
                    'year': (m.get('issued', {}).get('date-parts') or [[None]])[0][0],
                    'authors': [f"{a.get('family', '')}, {a.get('given', '')}" for a in m.get('author', [])],
                    'abstract_crossref': m.get('abstract'), 'abstract_openalex': abstract(oa.get('abstract_inverted_index')),
                    'oa_status': (oa.get('open_access') or {}).get('oa_status'), 'oa_url': (oa.get('open_access') or {}).get('oa_url'),
                    'cited_by': oa.get('cited_by_count')})
        time.sleep(0.5)
    res[key] = {'query': q, 'error': cr.get('error'), 'results': out}
json.dump(res, open(f'{OUT}/refs.json', 'w'), indent=1, ensure_ascii=False)
print(len(res), 'refs;', sum(1 for v in res.values() if not v['results']), 'without match')
