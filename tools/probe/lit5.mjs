import { writeFile, mkdir } from 'node:fs/promises';
await mkdir('fulltext', { recursive: true }); await mkdir('probe', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:weatherwatch@users.noreply.github.com)' };
const get = (u) => fetch(u, { headers: UA, signal: AbortSignal.timeout(120000), redirect: 'follow' });
const out = {}; const log = [];
const DOIS = { chu_frederick1990: '10.2151/jmsj1965.68.5_523', chu1988: '10.2151/jmsj1965.66.4_549', love1985a: '10.1175/1520-0493(1985)113<1487:ciowhs>2.0.co;2', harrison_giese1991: '10.1029/90jc01775', giese_harrison1991: '10.1029/90jc01760', hartten1996: '10.1029/96jd00030', ohba_ueda2007: '10.2151/jmsj.85.335' };
for (const [k, d] of Object.entries(DOIS)) {
  try { const r = await get('https://api.crossref.org/works/' + encodeURIComponent(d)); log.push(`${k} crossref ${r.status}`);
    if (r.ok) { const m = (await r.json()).message; out[k] = { doi: m.DOI, title: m.title?.[0], authors: (m.author || []).map((a) => a.family).join(', '), journal: m['container-title']?.[0], vol: m.volume, issue: m.issue, page: m.page, year: m.issued?.['date-parts']?.[0]?.[0], links: (m.link || []).map((l) => l.URL), abstract: m.abstract }; }
    else { const q = await (await get('https://api.crossref.org/works?rows=2&query.bibliographic=' + encodeURIComponent(k.replace(/_/g, ' ')) + '&select=DOI,title,volume,page,issued,author,container-title')).json(); out[k] = { search: q.message?.items }; }
  } catch (e) { log.push(`${k} ${e.message}`); }
}
for (const [k, q] of [['io_hameed2018', 'TITLE:"A model for super El Niños"'], ['io_hameed2018b', 'Hameed super El Nino Indian Ocean Dipole']]) {
  try { const j = await (await get('https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=core&pageSize=3&query=' + encodeURIComponent(q))).json();
    out[k] = (j.resultList?.result || []).map((r) => ({ title: r.title, authors: r.authorString, journal: r.journalInfo?.journal?.title, year: r.pubYear, vol: r.journalInfo?.volume, doi: r.doi, pmcid: r.pmcid, license: r.license, abstract: r.abstractText }));
    const pmc = out[k].find((r) => r.pmcid)?.pmcid; if (pmc) { const t = await (await get(`https://www.ebi.ac.uk/europepmc/webservices/rest/${pmc}/fullTextXML`)).text(); await writeFile(`fulltext/${k}.xml`, t); log.push(`${k} ${pmc} ${t.length}`); }
  } catch (e) { log.push(`${k} ${e.message}`); }
}
const PDF = { wwb_chu_frederick1990: 'https://www.jstage.jst.go.jp/article/jmsj1965/68/5/68_5_523/_pdf', wwb_chu1988: 'https://www.jstage.jst.go.jp/article/jmsj1965/66/4/66_4_549/_pdf', io_ohba_ueda2007: 'https://www.jstage.jst.go.jp/article/jmsj/85/3/85_3_335/_pdf',
  io_super_coupling_pmc: 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11397419/fullTextXML', io_diverse_iod_noaa: 'https://repository.library.noaa.gov/view/noaa/61748/noaa_61748_DS1.pdf', io_luo2010_jamstec: 'https://www.jamstec.go.jp/aplinfo/sintexf/2007/forecast/Luoetal.ENSO-IOD.JCLI09.pdf',
  wwb_vecchi_harrison_pmel109: 'https://www.pmel.noaa.gov/pubs/PDF/vecc1810/vecc1810.pdf' };
for (const [k, u] of Object.entries(PDF)) {
  try { const r = await get(u); const b = Buffer.from(await r.arrayBuffer()); const ct = r.headers.get('content-type') || ''; log.push(`${k} ${r.status} ${ct} ${b.length}`);
    if (r.ok) await writeFile(`fulltext/${k}.${ct.includes('pdf') ? 'pdf' : ct.includes('xml') ? 'xml' : 'html'}`, b);
  } catch (e) { log.push(`${k} ERR ${e.message}`); }
}
await writeFile('probe/lit5.json', JSON.stringify(out, null, 1)); await writeFile('probe/lit5_log.txt', log.join('\n'));
