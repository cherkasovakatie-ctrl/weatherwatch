import { writeFile, mkdir } from 'node:fs/promises';
await mkdir('probe', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:weatherwatch@users.noreply.github.com)' };
const get = (u) => fetch(u, { headers: UA, signal: AbortSignal.timeout(120000), redirect: 'follow' });
const log = [];
try { const r = await get('https://docs.google.com/spreadsheets/d/e/2PACX-1vSDsjlfm3r3JwgBbm40qXK9d5lsjAwwVjyKs_hh963NuwS3_91QCmndBdqfD7ni1hyVcuNuCgxwlRJg/pub?single=true&output=csv&gid=2125758773');
  const L = (await r.text()).split('\n'); const keep = L.filter((l) => /^,,,\s*198[123]\s/.test(l)).map((l) => l.replace(/^,,,/, '').trim().replace(/\s+/g, ' '));
  await writeFile('probe/bom_rmm_1981_83.txt', ['# BoM RMM via published sheet tab gid=2125758773 (source URL in sheet: https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt)', '# ' + L[1].slice(0, 300), 'year month day rmm1 rmm2 phase amp method', ...keep].join('\n')); log.push(`sheet ${r.status} rows ${keep.length}`);
} catch (e) { log.push('sheet ' + e.message); }
const out = {};
for (const [k, d] of Object.entries({ rk2007: '10.1175/jcli4249.1', zhang2005: '10.1029/2004rg000158', li2023: '10.3389/feart.2022.1021953', rk2006: '10.1175/jcli3893.1', ventrice2013: '10.1175/mwr-d-12-00327.1' })) {
  try { const r = await get('https://api.crossref.org/works/' + encodeURIComponent(d)); if (!r.ok) { out[k] = r.status; continue; } const m = (await r.json()).message;
    out[k] = { doi: m.DOI, title: m.title?.[0], authors: (m.author || []).map((a) => a.family).join(', '), journal: m['container-title']?.[0], vol: m.volume, issue: m.issue, page: m.page, art: m['article-number'], year: m.issued?.['date-parts']?.[0]?.[0] }; } catch (e) { out[k] = e.message; }
}
try { const j = await (await get('https://api.crossref.org/works?rows=3&query.bibliographic=' + encodeURIComponent('Roundy Kiladis 2007 Analysis of a reconstructed oceanic Kelvin wave dynamic height dataset for the period 1974-2005') + '&select=DOI,title,volume,page,issued,author,container-title')).json(); out.rk2007_q = j.message?.items; } catch (e) { out.rk2007_q = e.message; }
await writeFile('probe/lit8.json', JSON.stringify(out, null, 1)); await writeFile('probe/lit8_log.txt', log.join('\n'));
