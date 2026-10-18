// MJO follow-up: Kate's sheet tab, AGU/AMS papers (metadata, abstracts, OA copies -> fulltext/ for excerpting, never committed whole).
import { writeFile, mkdir } from 'node:fs/promises';
await mkdir('probe', { recursive: true }); await mkdir('fulltext', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:weatherwatch@users.noreply.github.com)' };
const get = (u) => fetch(u, { headers: UA, signal: AbortSignal.timeout(120000), redirect: 'follow' });
const inv = (x) => { if (!x) return ''; const p = []; for (const [w, ix] of Object.entries(x)) for (const i of ix) p[i] = w; return p.join(' '); };
const log = []; const out = {};
// 1. Sheet tab
try { const u = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSDsjlfm3r3JwgBbm40qXK9d5lsjAwwVjyKs_hh963NuwS3_91QCmndBdqfD7ni1hyVcuNuCgxwlRJg/pub?single=true&output=csv&gid=2125758773';
  const r = await get(u); const t = await r.text(); const L = t.split('\n'); log.push(`sheet ${r.status} ${t.length} lines ${L.length}`);
  await writeFile('probe/sheet_2125758773.txt', [...L.slice(0, 40), '...', ...L.filter((l) => /^"?1982|^"?1981|^"?1983|,1982,|1982-|\/1982/.test(l)).slice(0, 400), '...', ...L.slice(-5)].join('\n'));
} catch (e) { log.push('sheet ' + e.message); }
// 2. Papers
const DOI = { zhang2005: '10.1029/2004RG000158', agu2020: '10.1029/2020GL088894', agu2012: '10.1029/2012GL053144', agu2015: '10.1002/2015GL064547', agu2019: '10.1029/2019JD031416',
  wh2004: '10.1175/1520-0493(2004)132<1917:AARMMI>2.0.CO;2', rk2006: '10.1175/jcli3893.1', li2023: '10.3389/feart.2022.1021953', chen2016: '10.1175/jcli-d-15-0486.1', chen2015: '10.1007/s11802-015-2381-y',
  ventrice2013: '10.1175/mwr-d-12-00327.1', kessler1995: '10.1029/95jc00382', kessler_kleeman2000: '10.1175/1520-0442(2000)013<3560:rotmjo>2.0.co;2', mcphaden1999: '10.1126/science.283.5404.950' };
const SEARCH = { rk2007: 'Roundy Kiladis Analysis of a reconstructed oceanic Kelvin wave dynamic height dataset for the period 1974-2005', marsico2025: 'Marsico linear inverse model ENSO filter MJO RMM index 2025',
  liebmann_smith1996: 'Liebmann Smith 1996 Description of a complete interpolated outgoing longwave radiation dataset', rk_conf: 'Roundy Kiladis Roles of the MJO in the development of oceanic Kelvin waves and ENSO',
  mjo_enso_review: 'Madden-Julian oscillation ENSO two-way interaction review' };
const meta = (j) => ({ doi: j.doi, title: j.title, year: j.publication_year, authors: (j.authorships || []).map((a) => a.author.display_name).slice(0, 8), venue: j.primary_location?.source?.display_name, biblio: j.biblio, oa: j.open_access, best: j.best_oa_location?.pdf_url || j.best_oa_location?.landing_page_url, lic: j.best_oa_location?.license, abstract: inv(j.abstract_inverted_index) });
for (const [k, d] of Object.entries(DOI)) {
  try { const r = await get('https://api.openalex.org/works/https://doi.org/' + encodeURIComponent(d)); out[k] = r.ok ? meta(await r.json()) : { status: r.status, doi: d }; } catch (e) { out[k] = { err: e.message }; }
  try { const r = await get(`https://api.unpaywall.org/v2/${encodeURIComponent(d)}?email=weatherwatch@users.noreply.github.com`); if (r.ok) { const u = await r.json(); out[k].upw = (u.oa_locations || []).map((l) => ({ pdf: l.url_for_pdf, url: l.url, host: l.host_type, ver: l.version, lic: l.license })); } } catch (e) {}
  const cands = [out[k].best, ...(out[k].upw || []).map((l) => l.pdf)].filter((x) => x && /pdf|download/i.test(x));
  for (const p of [...new Set(cands)]) { try { const q = await get(p); const ct = q.headers.get('content-type') || ''; log.push(`${k} ${p} ${q.status} ${ct}`); if (q.ok && ct.includes('pdf')) { await writeFile(`fulltext/mjo_${k}.pdf`, Buffer.from(await q.arrayBuffer())); break; } } catch (e) { log.push(`${k} ${p} ${e.message}`); } }
}
for (const [k, q] of Object.entries(SEARCH)) {
  try { const j = await (await get('https://api.openalex.org/works?per-page=4&search=' + encodeURIComponent(q))).json(); out[k] = (j.results || []).map(meta); } catch (e) { out[k] = { err: e.message }; }
}
await writeFile('probe/lit7.json', JSON.stringify(out, null, 1)); await writeFile('probe/lit7_log.txt', log.join('\n'));
