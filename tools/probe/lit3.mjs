// Indian-Pacific literature for 1982: metadata/abstracts (committed) and full texts (workflow artifact only, not committed).
import { writeFile, mkdir } from 'node:fs/promises';
import { execSync } from 'node:child_process';
await mkdir('probe', { recursive: true }); await mkdir('fulltext', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:weatherwatch@users.noreply.github.com)' };
const get = (u) => fetch(u, { headers: UA, signal: AbortSignal.timeout(120000), redirect: 'follow' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const inv = (x) => { if (!x) return ''; const p = []; for (const [w, ix] of Object.entries(x)) for (const i of ix) p[i] = w; return p.join(' '); };
const pick = (j) => ({ doi: j.doi, title: j.title, year: j.publication_year, authors: (j.authorships || []).map((a) => a.author.display_name).slice(0, 8), venue: j.primary_location?.source?.display_name, biblio: j.biblio, oa: j.open_access?.oa_url, lic: j.primary_location?.license, abstract: inv(j.abstract_inverted_index), cited_by: j.cited_by_count });
const SEARCH = {
  annamalai2005: 'Annamalai Xie McCreary Murtugudde 2005 Impact of Indian Ocean sea surface temperature on developing El Nino',
  izumo2010: 'Izumo 2010 Influence of the state of the Indian Ocean Dipole on the following year El Nino',
  kug_kang2006: 'Kug Kang 2006 Interactive feedback between ENSO and the Indian Ocean',
  ohba_ueda2007: 'Ohba Ueda 2007 An impact of SST anomalies in the Indian Ocean in acceleration of the El Nino to La Nina transition',
  luo2010: 'Luo Zhang Behera Masumoto Jin Lukas Yamagata 2010 Interaction between El Nino and extreme Indian Ocean dipole',
  wu_kirtman2004: 'Wu Kirtman 2004 Understanding the impacts of the Indian Ocean on ENSO variability in a coupled GCM',
  yu2002: 'Yu Mechoso McWilliams Arakawa 2002 Impacts of the Indian Ocean on the ENSO cycle',
  behera2006: 'Behera Luo Yamagata 2006 A CGCM study on the interaction between IOD and ENSO',
  saji1999: 'Saji Goswami Vinayachandran Yamagata 1999 A dipole mode in the tropical Indian Ocean',
  webster1999: 'Webster Moore Loschnigg Leben 1999 Coupled ocean-atmosphere dynamics in the Indian Ocean during 1997-98',
  annamalai2003: 'Annamalai Murtugudde Potemra Xie Liu Wang 2003 Coupled dynamics over the Indian Ocean spring initiation of the Zonal Mode',
  xie2009: 'Xie Hu Huang Du 2009 Indian Ocean capacitor effect on Indo-western Pacific climate during the summer following El Nino',
  klein1999: 'Klein Soden Lau 1999 Remote sea surface temperature variations during ENSO evidence for a tropical atmospheric bridge',
  diverse_iod_enso: 'Diverse impacts of the Indian Ocean Dipole on El Nino-Southern Oscillation',
  super_coupling: 'Coupling is key for the tropical Indian and Atlantic oceans to boost super El Nino',
  cai2019: 'Cai 2019 Pantropical climate interactions Science',
  wang2019iod: 'Indian Ocean dipole 1982 El Nino positive IOD co-occurrence event',
  fischer2005: 'Fischer Terray Guilyardi Gualdi Delecluse 2005 Two independent triggers for the Indian Ocean dipole zonal mode in a coupled GCM',
  meyers2007: 'Meyers McIntosh Pigot Pook 2007 The years of El Nino La Nina and interactions with the tropical Indian Ocean',
  kajtar2017: 'Kajtar Santoso England Cai 2017 Tropical climate variability interactions across the Pacific Indian and Atlantic Oceans',
  santoso2012: 'Santoso England Cai 2012 Impact of Indo-Pacific feedback interactions on ENSO dynamics diagnosed using ensemble climate simulations',
  zhang2021: 'Zhang Wang Jin Indian Ocean dipole ENSO interaction review 2021',
  ummenhofer_1982: 'Indian Ocean 1982 positive dipole Java upwelling El Nino onset observations',
  stuecker2017: 'Stuecker Timmermann Jin Chikamoto Zhang Wittenberg Widiasih Zhao 2017 Revisiting ENSO Indian Ocean Dipole phase relationships',
  dommenget2011: 'Dommenget Semenov Latif 2006 Impacts of the tropical Indian and Atlantic Oceans on ENSO',
  luo2010pnas: 'Luo Behera Masumoto Sakuma Yamagata 2008 Successful prediction of the consecutive IOD in 2006 and 2007',
};
const out = {};
for (const [k, q] of Object.entries(SEARCH)) {
  try { const j = await (await get('https://api.openalex.org/works?per-page=4&search=' + encodeURIComponent(q))).json(); out[k] = (j.results || []).map(pick); } catch (e) { out[k] = { err: e.message }; }
  await sleep(400);
}
await writeFile('probe/lit3.json', JSON.stringify(out, null, 1));
const FT = {
  super_coupling_pmc: 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11397419/fullTextXML',
  diverse_iod_noaa: 'https://repository.library.noaa.gov/view/noaa/61748/noaa_61748_DS1.pdf',
  luo2010_jamstec: 'https://www.jamstec.go.jp/aplinfo/sintexf/2007/forecast/Luoetal.ENSO-IOD.JCLI09.pdf',
  izumo2010_hal: 'https://hal.science/hal-00455457/document',
};
const log = [];
for (const [k, u] of Object.entries(FT)) {
  try { const r = await get(u); const b = Buffer.from(await r.arrayBuffer()); const ct = r.headers.get('content-type') || ''; log.push(`${k} ${r.status} ${ct} ${b.length}`);
    if (!r.ok) continue;
    if (ct.includes('pdf')) { await writeFile(`/tmp/${k}.pdf`, b); execSync(`pdftotext -layout /tmp/${k}.pdf fulltext/${k}.txt`); }
    else await writeFile(`fulltext/${k}.${ct.includes('xml') ? 'xml' : 'html'}`, b);
  } catch (e) { log.push(`${k} ERR ${e.message}`); }
}
await writeFile('probe/lit3_log.txt', log.join('\n'));
