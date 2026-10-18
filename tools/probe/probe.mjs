import { writeFile, mkdir } from 'node:fs/promises';
await mkdir('probe', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:weatherwatch@users.noreply.github.com)' };
const log = [];
const get = (u, o = {}) => fetch(u, { headers: UA, signal: AbortSignal.timeout(120000), redirect: 'follow', ...o });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const inv = (x) => { if (!x) return ''; const p = []; for (const [w, ix] of Object.entries(x)) for (const i of ix) p[i] = w; return p.join(' '); };
if (process.env.SKIP_LIT) process.exit(0);
// 1. Europe PMC full text (Nature Communications 2025, PMC11802828)
try {
  const r = await get('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11802828/fullTextXML'); const t = await r.text();
  log.push(`epmc ${r.status} ${t.length}`);
  const lic = (t.match(/<license[\s\S]*?<\/license>/) || [''])[0].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
  const txt = t.replace(/<xref[^>]*>([^<]*)<\/xref>/g, '[$1]').replace(/<\/(p|title|sec|caption|ref)>/g, '\n').replace(/<[^>]+>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/\n\s*\n+/g, '\n\n');
  await writeFile('probe/mjo_volcano_2025.txt', 'LICENCE: ' + lic + '\n\n' + txt);
} catch (e) { log.push('epmc ' + e.message); }
// 2. Citation audit and literature: OpenAlex + Unpaywall + Semantic Scholar
const DOI = {
  gill1983: '10.1038/306229a0', rw1983: '10.1126/science.222.4629.1195', cane1983: '10.1126/science.222.4629.1189',
  firing1983: '10.1126/science.222.4628.1121', halpern1983: '10.1126/science.221.4616.1173', luther1983: '10.1126/science.222.4621.327',
  harrison1984: '10.1126/science.224.4653.1099', weickmann1991: '10.1029/90jd01832', predybaylo2020: '10.1038/s43247-020-0013-y',
  mjo_volcano_2025: '10.1038/s41467-025-56692-2', ohba2013: '10.1175/jcli-d-12-00471.1', predybaylo2017: '10.1002/2016jd025796',
  mcgregor2011: '10.1175/2010jcli3990.1', stevenson2016: '10.1175/jcli-d-15-0239.1', dee2020: '10.1126/science.aax2000',
  khodri2017: '10.1038/s41467-017-00755-6', hendon1999: '10.1175/1520-0442(1999)012<2538:ivotmj>2.0.co;2',
  kessler2001: '10.1175/1520-0442(2001)014<3055:erotmj>2.0.co;2', seiki2007a: '10.1175/mwr3477.1', harrison_vecchi1997: '10.1175/1520-0442(1997)010<3131:wweitt>2.0.co;2',
  zhang_gottschalck2002: '10.1175/1520-0442(2002)015<2429:saoeat>2.0.co;2', wheeler_hendon2004: '10.1175/1520-0493(2004)132<1917:aarmmi>2.0.co;2',
  kiladis2014: '10.1175/mwr-d-13-00301.1', slingo1999: '10.1002/qj.49712555411', kalnay1996: '10.1175/1520-0477(1996)077<0437:tnyrp>2.0.co;2',
};
const SEARCH = {
  lau_chan_1986: 'The 40-50 day oscillation and the El Nino/Southern Oscillation: A new perspective',
  lau_chan_1988: 'Intraseasonal and interannual variations of tropical convection: a possible link between the 40-50 day oscillation and ENSO',
  robock1995: 'GCM evaluation of a mechanism for El Nino triggering by the El Chichon ash cloud',
  lukas1984: 'Lukas Hayes Wyrtki 1984 Equatorial sea level response during the 1982-1983 El Nino',
  wyrtki1985a: 'Wyrtki 1985 Sea level fluctuations in the Pacific during the 1982-83 El Nino',
  liebmann_smith1996: 'Description of a complete (interpolated) outgoing longwave radiation dataset',
  gill_rasmusson_text: 'Gill Rasmusson The 1982-83 climate anomaly in the equatorial Pacific',
  mjo_1982_onset: 'Madden-Julian oscillation 1982-83 El Nino onset westerly wind',
  elchichon_mjo2: 'volcanic eruption Madden-Julian oscillation El Nino onset El Chichon',
};
const lit = {};
const pick = (j) => ({ id: j.id, doi: j.doi, title: j.title, year: j.publication_year, authors: (j.authorships || []).map((a) => a.author.display_name).slice(0, 8), venue: j.primary_location?.source?.display_name, biblio: j.biblio, oa: j.open_access, locations: (j.locations || []).map((l) => ({ src: l.source?.display_name, url: l.landing_page_url, pdf: l.pdf_url, lic: l.license, ver: l.version })), abstract: inv(j.abstract_inverted_index), cited_by: j.cited_by_count });
for (const [k, d] of Object.entries(DOI)) {
  try { const r = await get('https://api.openalex.org/works/https://doi.org/' + encodeURIComponent(d)); lit[k] = r.ok ? pick(await r.json()) : { err: r.status, doi: d }; } catch (e) { lit[k] = { err: e.message }; }
  try { const r = await get(`https://api.unpaywall.org/v2/${encodeURIComponent(d)}?email=weatherwatch@users.noreply.github.com`); if (r.ok) { const u = await r.json(); lit[k].unpaywall = { is_oa: u.is_oa, status: u.oa_status, locs: (u.oa_locations || []).map((l) => ({ url: l.url, pdf: l.url_for_pdf, host: l.host_type, ver: l.version, lic: l.license, repo: l.repository_institution })) }; } else lit[k].unpaywall = r.status; } catch (e) { lit[k].unpaywall = e.message; }
  try { const r = await get(`https://api.semanticscholar.org/graph/v1/paper/DOI:${encodeURIComponent(d)}?fields=title,abstract,openAccessPdf,tldr`); if (r.ok) { const s = await r.json(); lit[k].s2 = { abstract: s.abstract, pdf: s.openAccessPdf, tldr: s.tldr?.text }; } else lit[k].s2 = r.status; } catch (e) { lit[k].s2 = e.message; }
  await sleep(1200);
}
for (const [k, q] of Object.entries(SEARCH)) {
  try { const j = await (await get('https://api.openalex.org/works?per-page=5&search=' + encodeURIComponent(q))).json(); lit[k] = (j.results || []).map(pick); } catch (e) { lit[k] = { err: e.message }; }
  await sleep(500);
}
await writeFile('probe/lit2.json', JSON.stringify(lit, null, 1));
// 3. MJO index sources
const D = {
  psl_mjo_dir: 'https://psl.noaa.gov/mjo/mjoindex/',
  psl_mjo_page: 'https://psl.noaa.gov/mjo/',
  omi_1x_1979: 'https://psl.noaa.gov/mjo/mjoindex/omi.1x.1979.txt',
  iri_rmm: 'https://iridl.ldeo.columbia.edu/SOURCES/.BoM/.MJO/.RMM/',
  bom_ftp_list: 'http://www.bom.gov.au/catalogue/anon-ftp.shtml',
  sheet_mjo: 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSDsjlfm3r3JwgBbm40qXK9d5lsjAwwVjyKs_hh963NuwS3_91QCmndBdqfD7ni1hyVcuNuCgxwlRJg/pub?single=true&output=csv&gid=334938232',
};
for (const [k, u] of Object.entries(D)) {
  try { const r = await get(u); const t = await r.text(); const L = t.split('\n'); await writeFile(`probe/src_${k}.txt`, `${u}\nHTTP ${r.status} ${t.length}\n` + (t.length < 60000 ? t : [...L.slice(0, 40), '...', ...L.slice(-10)].join('\n'))); log.push(`${k} ${r.status} ${t.length}`); }
  catch (e) { log.push(`${k} ERR ${e.message}`); }
}
await writeFile('probe/log.txt', log.join('\n'));
