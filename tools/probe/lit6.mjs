import { writeFile, mkdir } from 'node:fs/promises';
await mkdir('probe', { recursive: true });
const UA = { 'User-Agent': 'GlobalWeatherWatch/1.0 (mailto:weatherwatch@users.noreply.github.com)' };
const get = (u) => fetch(u, { headers: UA, signal: AbortSignal.timeout(60000) });
const DOI = { hameed2018: '10.1038/s41467-018-04803-7', kim2025: '10.1038/s41467-025-56692-2', izumo2010: '10.1038/ngeo760', huang2017: '10.1175/jcli-d-16-0836.1', schreck2009: '10.1175/2008mwr2541.1', fan2024: '10.1126/sciadv.adp2281', bjerknes1969: '10.1175/1520-0493(1969)097<0163:atftep>2.3.co;2', zhang2021: '10.1175/jcli-d-21-0074.1', luo2010: '10.1175/2009jcli3104.1', liebmann1996: '10.1175/1520-0477(1996)077<1275:dociol>2.0.co;2', robock1995: '10.1029/95gl02180', chai2020: '10.1007/s00382-020-05453-6', zuo2018: '10.1175/jcli-d-17-0571.1', khodri2017: '10.1038/s41467-017-00755-6', worsfold2024: '10.3390/rs16183358', weickmann1991: '10.1029/90jd01832', kiladis2014: '10.1175/mwr-d-13-00301.1', annamalai2005: '10.1175/jcli-3268.1', kug2006: '10.1175/jcli3587.1' };
const out = {};
for (const [k, d] of Object.entries(DOI)) {
  try { const r = await get('https://api.crossref.org/works/' + encodeURIComponent(d)); if (!r.ok) { out[k] = { status: r.status, doi: d }; continue; }
    const m = (await r.json()).message; out[k] = { doi: m.DOI, title: m.title?.[0], first: (m.author || []).slice(0, 6).map((a) => `${a.family} ${a.given?.[0] || ''}`).join(', '), n_auth: (m.author || []).length, journal: m['container-title']?.[0], vol: m.volume, issue: m.issue, page: m.page, art: m['article-number'], year: m.issued?.['date-parts']?.[0]?.[0] };
  } catch (e) { out[k] = { err: e.message }; }
}
for (const [k, q] of [['luo2010_q', 'Luo Zhang Behera Masumoto Jin Lukas Yamagata Interaction between El Nino and extreme Indian Ocean dipole Journal of Climate 2010'], ['zhang2021_q', 'Zhang Han Meehl Diverse impacts of the Indian Ocean dipole on El Nino Southern Oscillation 2021'], ['robock1995_q', 'Robock Taylor Stenchikov Liu GCM evaluation of a mechanism for El Nino triggering by the El Chichon ash cloud'], ['liebmann_q', 'Liebmann Smith 1996 Description of a complete interpolated outgoing longwave radiation dataset'], ['annamalai2005_q', 'Annamalai Xie McCreary Murtugudde Impact of Indian Ocean sea surface temperature on developing El Nino'], ['kug2006_q', 'Kug Kang Interactive feedback between ENSO and the Indian Ocean']]) {
  try { const j = await (await get('https://api.crossref.org/works?rows=2&query.bibliographic=' + encodeURIComponent(q) + '&select=DOI,title,volume,page,issued,author,container-title,article-number')).json();
    out[k] = (j.message?.items || []).map((m) => ({ doi: m.DOI, title: m.title?.[0], first: (m.author || []).slice(0, 3).map((a) => a.family).join(', '), journal: m['container-title']?.[0], vol: m.volume, page: m.page, art: m['article-number'], year: m.issued?.['date-parts']?.[0]?.[0] })); } catch (e) { out[k] = e.message; }
}
await writeFile('probe/lit6.json', JSON.stringify(out, null, 1));
