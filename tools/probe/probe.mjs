import { writeFile, mkdir } from 'node:fs/promises';
import { execSync } from 'node:child_process';
await mkdir('probe', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:noreply@github.com)' };
const log = [];
async function get(u, opt = {}) { const r = await fetch(u, { headers: UA, signal: AbortSignal.timeout(120000), redirect: 'follow', ...opt }); return r; }
// 1. El Chichón paper (CC-BY): OpenAlex metadata + PDF text
try {
  const j = await (await get('https://api.openalex.org/works/https://doi.org/10.1038/s43247-020-0013-y')).json();
  const ab = j.abstract_inverted_index ? (() => { const p = []; for (const [w, ix] of Object.entries(j.abstract_inverted_index)) for (const i of ix) p[i] = w; return p.join(' '); })() : '';
  await writeFile('probe/elchichon_meta.json', JSON.stringify({ title: j.title, authors: j.authorships?.map((a) => a.author.display_name), year: j.publication_year, venue: j.primary_location?.source?.display_name, license: j.primary_location?.license, oa: j.open_access, pdf: j.primary_location?.pdf_url, cited_by: j.cited_by_count, abstract: ab }, null, 1));
  for (const u of [j.primary_location?.pdf_url, 'https://www.nature.com/articles/s43247-020-0013-y.pdf'].filter(Boolean)) {
    const r = await get(u); log.push(`pdf ${u} ${r.status} ${r.headers.get('content-type')}`);
    if (r.ok && (r.headers.get('content-type') || '').includes('pdf')) { await writeFile('/tmp/ec.pdf', Buffer.from(await r.arrayBuffer())); execSync('pdftotext -layout /tmp/ec.pdf probe/elchichon_2020_CC-BY.txt'); break; }
  }
} catch (e) { log.push('elchichon ' + e.message); }
// 2. Literature: Crossref
const Q = {
  lau_chan_1986: 'Lau Chan 1986 The 40-50 day oscillation and the El Nino Southern Oscillation a new perspective',
  lau_chan_1988: 'Lau Chan 1988 Intraseasonal and interannual variations of tropical convection a possible link between the 40-50 day oscillation and ENSO',
  weickmann1991: 'Weickmann 1991 El Nino Southern Oscillation and Madden Julian 30-60 day oscillations during 1981-1982',
  mjo_1982: 'Madden-Julian oscillation 1982 El Nino onset intraseasonal',
  wheeler_hendon2004: 'Wheeler Hendon 2004 An all-season real-time multivariate MJO index development of an index for monitoring and prediction',
  kiladis2014: 'Kiladis 2014 A comparison of OLR and circulation-based indices for tracking the MJO',
  hendon2007: 'Hendon Zhang Glick 2007 Interannual variation of the Madden-Julian oscillation during austral summer',
  zhang_gottschalck2002: 'Zhang Gottschalck 2002 SST anomalies of ENSO and the Madden-Julian oscillation in the equatorial Pacific',
  kessler2001: 'Kessler 2001 EOF representations of the Madden-Julian oscillation and its connection with ENSO',
  seiki2007: 'Seiki Takayabu 2007 Westerly wind bursts and their relationship with intraseasonal variations and ENSO',
  harrison_vecchi1997: 'Harrison Vecchi 1997 Westerly wind events in the tropical Pacific 1986-95',
  ohba2013: 'Ohba Shiogama Yokohata Watanabe 2013 Impact of strong tropical volcanic eruptions on ENSO simulated in a coupled GCM',
  predybaylo2017: 'Predybaylo 2017 Impacts of a Pinatubo-size volcanic eruption on ENSO',
  mcgregor_timmermann2011: 'McGregor Timmermann 2011 The effect of explosive tropical volcanism on ENSO',
  stevenson2016: 'Stevenson 2016 El Nino like hydroclimate responses to last millennium volcanic eruptions',
  dee2020: 'Dee Cobb Emile-Geay 2020 No consistent ENSO response to volcanic forcing over the last millennium Science',
  elchichon_mjo: 'El Chichon eruption Maritime Continent MJO westerly wind bursts 1982 El Nino model',
  robock_elchichon_enso: 'El Chichon 1982 El Nino volcanic eruption coincidence',
  slingo1999: 'Slingo 1999 On the predictability of the interannual behaviour of the Madden-Julian Oscillation and its relationship with El Nino',
  liebmann1996: 'Liebmann Smith 1996 Description of a complete interpolated outgoing longwave radiation dataset',
  kalnay1996: 'Kalnay 1996 The NCEP/NCAR 40-year reanalysis project',
};
const out = {};
for (const [k, q] of Object.entries(Q)) {
  try { const j = await (await get(`https://api.crossref.org/works?rows=3&query.bibliographic=${encodeURIComponent(q)}&select=DOI,title,author,container-title,volume,page,issued`)).json();
    out[k] = (j.message?.items || []).map((i) => ({ doi: i.DOI, title: (i.title || [''])[0], authors: (i.author || []).slice(0, 6).map((a) => a.family).join(', '), journal: (i['container-title'] || [''])[0], vol: i.volume, page: i.page, year: i.issued?.['date-parts']?.[0]?.[0] })); } catch (e) { out[k] = e.message; }
  await new Promise((r) => setTimeout(r, 600));
}
await writeFile('probe/lit.json', JSON.stringify(out, null, 1));
// 3. Data access tests
const D = {
  rmm_bom: 'http://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt',
  omi_psl: 'https://psl.noaa.gov/mjo/mjoindex/omi.1x.txt',
  omi_era5: 'https://psl.noaa.gov/mjo/mjoindex/omi.era5.1x.webpage.4023.txt',
  u850_dods: 'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/uwnd.1982.nc.ascii?level[0:1:16]',
  u850_sub: 'https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/uwnd.1982.nc.ascii?uwnd[0:1:1][2:1:2][36:1:36][0:1:3]',
  olr_dods: 'https://psl.noaa.gov/thredds/dodsC/Datasets/interp_OLR/olr.day.mean.nc.ascii?time[0:1:3]',
  olr_sub: 'https://psl.noaa.gov/thredds/dodsC/Datasets/interp_OLR/olr.day.mean.nc.ascii?olr[2900:1:2901][36:1:36][0:1:3]',
};
for (const [k, u] of Object.entries(D)) {
  try { const r = await get(u); const t = await r.text(); const L = t.split('\n'); await writeFile(`probe/data_${k}.txt`, `${u}\nHTTP ${r.status} ${t.length}\n` + [...L.slice(0, 12), '...', ...L.slice(-4)].join('\n')); log.push(`${k} ${r.status} ${t.length}`); }
  catch (e) { log.push(`${k} ERR ${e.message}`); }
}
await writeFile('probe/_log.txt', log.join('\n') + '\n');
