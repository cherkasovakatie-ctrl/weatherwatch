// Trace early-1982 westerly wind burst literature: reference lists (Crossref, OpenAlex) of key papers; searches; OA copies.
import { writeFile, mkdir } from 'node:fs/promises';
import { execSync } from 'node:child_process';
await mkdir('probe', { recursive: true }); await mkdir('fulltext', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:weatherwatch@users.noreply.github.com)' };
const get = (u) => fetch(u, { headers: UA, signal: AbortSignal.timeout(120000), redirect: 'follow' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const inv = (x) => { if (!x) return ''; const p = []; for (const [w, ix] of Object.entries(x)) for (const i of ix) p[i] = w; return p.join(' '); };
const out = { refs: {}, search: {}, verify: {}, oa: {} };
const SRC = { harrison_vecchi1997: '10.1175/1520-0442(1997)010<3131:wweitt>2.0.co;2', harrison1984: '10.1126/science.224.4653.1099', weickmann1991: '10.1029/90jd01832',
  lukas1984: null, harrison_giese1991: null, schreck2009: '10.1175/2008mwr2541.1', seiki2007a: '10.1175/mwr3477.1', vecchi_harrison2000: '10.1175/1520-0442(2000)013<1814:tpssta>2.0.co;2' };
const SEARCH = {
  lukas1984: 'Lukas Hayes Wyrtki 1984 Equatorial sea level response during the 1982-1983 El Nino',
  harrison_giese1991: 'Harrison Giese 1991 Episodes of surface westerly winds as observed from islands in the western tropical Pacific',
  wwb_may1982: 'westerly wind burst May 1982 western equatorial Pacific',
  wwb_1982_kelvin: 'westerly wind event 1982 equatorial Kelvin wave western Pacific observations',
  meyers_donguy1984: 'Meyers Donguy 1984 The North Equatorial Countercurrent and heat storage in the western Pacific Ocean during 1982-83',
  sadler_kilonsky: 'Sadler Kilonsky 1983 meteorological events central Pacific 1982 El Nino',
  keen1987: 'Keen 1987 Equatorial westerlies and the Southern Oscillation',
  hartten1996: 'Hartten 1996 Synoptic settings of westerly wind bursts',
  giese_harrison1990: 'Giese Harrison 1990 Aspects of the Kelvin wave response to episodic wind forcing',
  harrison_giese1988: 'Harrison Giese 1988 Remote westerly wind forcing of the eastern equatorial Pacific some model results',
  eriksen1983: 'Eriksen 1983 equatorial Kelvin waves 1982 Line Islands',
  lau_chan1986: 'Lau Chan 1986 40-50 day oscillation El Nino Southern Oscillation new perspective',
  lau_chan1988: 'Lau Chan 1988 Intraseasonal and interannual variations of tropical convection possible link 40-50 day oscillation ENSO',
  nakazawa1988: 'Nakazawa 1988 Tropical super clusters within intraseasonal variations over the western Pacific',
  murakami_1982: 'Murakami 1984 1982 El Nino intraseasonal 40-50 day monsoon',
  arkin1983: 'Arkin Kopman Reynolds 1983 1982-1983 El Nino Southern Oscillation event quick look atlas',
  bjerknes1969: 'Bjerknes 1969 Atmospheric teleconnections from the equatorial Pacific',
  robock1995: 'Robock Taylor Stenchikov Liu 1995 GCM evaluation of a mechanism for El Nino triggering by the El Chichon ash cloud',
  gill_rasmusson_cited: 'Gill Rasmusson 1983 1982-83 climate anomaly equatorial Pacific Nature',
};
async function work(doi) {
  const r = await get('https://api.openalex.org/works/https://doi.org/' + encodeURIComponent(doi)); return r.ok ? r.json() : null;
}
for (const [k, d] of Object.entries(SRC)) {
  if (!d) continue;
  try {
    const cr = await (await get('https://api.crossref.org/works/' + encodeURIComponent(d))).json();
    out.refs[k] = { title: cr.message?.title?.[0], crossref_refs: (cr.message?.reference || []).map((x) => x.unstructured || [x.author, x.year, x['article-title'] || x['journal-title'] || x['volume-title'], x.volume, x['first-page'], x.DOI].filter(Boolean).join(' | ')) };
    const w = await work(d);
    if (w) { const ids = (w.referenced_works || []).map((u) => u.split('/').pop()); const titles = [];
      for (let i = 0; i < ids.length; i += 40) { const j = await (await get(`https://api.openalex.org/works?per-page=50&filter=openalex:${ids.slice(i, i + 40).join('|')}&select=id,doi,title,publication_year,authorships,biblio,primary_location`)).json();
        for (const x of j.results || []) titles.push(`${x.publication_year} | ${(x.authorships || []).map((a) => a.author.display_name).slice(0, 4).join(', ')} | ${x.title} | ${x.primary_location?.source?.display_name} ${x.biblio?.volume}:${x.biblio?.first_page} | ${x.doi}`); }
      out.refs[k].openalex_refs = titles.sort(); out.refs[k].cited_by_api = w.cited_by_api_url; }
  } catch (e) { out.refs[k] = { err: e.message }; }
  await sleep(500);
}
for (const [k, q] of Object.entries(SEARCH)) {
  try { const j = await (await get('https://api.openalex.org/works?per-page=5&search=' + encodeURIComponent(q))).json();
    out.search[k] = (j.results || []).map((x) => ({ doi: x.doi, title: x.title, year: x.publication_year, authors: (x.authorships || []).map((a) => a.author.display_name).slice(0, 6), venue: x.primary_location?.source?.display_name, biblio: x.biblio, oa: x.open_access?.oa_url, abstract: inv(x.abstract_inverted_index) })); } catch (e) { out.search[k] = { err: e.message }; }
  await sleep(400);
}
// Works citing Harrison 1984 or Weickmann 1991 that mention 1982 in the title
for (const [k, d] of [['citing_harrison1984', '10.1126/science.224.4653.1099'], ['citing_weickmann1991', '10.1029/90jd01832']]) {
  try { const w = await work(d); const id = w.id.split('/').pop();
    const j = await (await get(`https://api.openalex.org/works?per-page=100&filter=cites:${id}&select=doi,title,publication_year,authorships,primary_location`)).json();
    out.search[k] = (j.results || []).map((x) => `${x.publication_year} | ${(x.authorships || []).map((a) => a.author.display_name).slice(0, 3).join(', ')} | ${x.title} | ${x.primary_location?.source?.display_name} | ${x.doi}`).sort(); } catch (e) { out.search[k] = e.message; }
}
await writeFile('probe/lit4.json', JSON.stringify(out, null, 1));
// Full texts to the workflow artifact only (not committed)
const FT = { hv1997_unpaywall: 'https://api.unpaywall.org/v2/10.1175/1520-0442(1997)010%3C3131:WWEITT%3E2.0.CO;2?email=weatherwatch@users.noreply.github.com',
  cane1983_columbia: 'https://academiccommons.columbia.edu/doi/10.7916/D8X06HPV/download' };
const log = [];
for (const [k, u] of Object.entries(FT)) {
  try { const r = await get(u); const b = Buffer.from(await r.arrayBuffer()); const ct = r.headers.get('content-type') || ''; log.push(`${k} ${r.status} ${ct} ${b.length}`);
    if (k.endsWith('unpaywall') && r.ok) { const j = JSON.parse(b.toString()); log.push(JSON.stringify(j.oa_locations)); for (const l of j.oa_locations || []) { const p = l.url_for_pdf; if (!p) continue; const q = await get(p); log.push(`  pdf ${p} ${q.status} ${q.headers.get('content-type')}`); if (q.ok && (q.headers.get('content-type') || '').includes('pdf')) { await writeFile('/tmp/hv.pdf', Buffer.from(await q.arrayBuffer())); execSync('pdftotext -layout /tmp/hv.pdf fulltext/hv1997.txt'); break; } } }
    else if (r.ok && ct.includes('pdf')) { await writeFile(`/tmp/${k}.pdf`, b); execSync(`pdftotext -layout /tmp/${k}.pdf fulltext/${k}.txt`); }
  } catch (e) { log.push(`${k} ERR ${e.message}`); }
}
await writeFile('probe/lit4_log.txt', log.join('\n'));
