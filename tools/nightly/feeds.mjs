// Pure parsers for the second batch of daily feeds. Text in, plain objects out; no network or files.
// Each returns objects keyed by the target CSV's column names, so run.mjs can merge them into the
// existing file (patching overlaps, appending new keys) with mergeRows().

const MONTHS = { JAN: '01', FEB: '02', MAR: '03', APR: '04', MAY: '05', JUN: '06', JUL: '07', AUG: '08', SEP: '09', OCT: '10', NOV: '11', DEC: '12' };
const pad2 = (n) => String(n).padStart(2, '0');
const isNum = (s) => s !== undefined && s !== null && s !== '' && Number.isFinite(Number(s));

/** Python-style float text, as the existing files were written ("97.0", "3.33"). */
export function pyFloat(v) {
  if (!isNum(v)) return '';
  const n = Number(v);
  return Number.isInteger(n) ? n.toFixed(1) : String(n);
}
/** Round to n decimals, written like a Python float ("1.0", "2.16"), as the existing files are. */
export const round = (v, n) => (isNum(v) ? pyFloat(Number(Number(v).toFixed(n))) : '');

// ---------- generic merge ----------
/** Merge new objects into existing CSV rows by key. Existing values are overwritten only where the new value is
 *  non-empty; keys not yet in the file are appended only if `accept(obj)` is true. Rows are returned sorted by key. */
export function mergeRows(oldText, header, key, fresh, { accept = () => true, keep = null } = {}) {
  const lines = oldText.trim().split('\n');
  const cols = lines[0].split(',');
  const parseLine = (l) => {
    const out = []; let cur = '', q = false;
    for (let i = 0; i < l.length; i++) {
      const c = l[i];
      if (q) { if (c === '"' && l[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
      else if (c === '"') q = true; else if (c === ',') { out.push(cur); cur = ''; } else cur += c;
    }
    out.push(cur); return out;
  };
  const map = new Map();
  for (const l of lines.slice(1)) { const v = parseLine(l); map.set(v[cols.indexOf(key)], Object.fromEntries(cols.map((c, i) => [c, v[i] ?? '']))); }
  let added = 0, changed = 0;
  for (const o of fresh) {
    const k = o[key];
    if (!k) continue;
    if (map.has(k)) {
      const row = map.get(k);
      for (const c of header) if (c !== key && o[c] !== undefined && o[c] !== '' && row[c] !== String(o[c])) { row[c] = String(o[c]); changed++; }
    } else if (accept(o)) {
      map.set(k, Object.fromEntries(header.map((c) => [c, o[c] === undefined ? '' : String(o[c])]))); added++;
    }
  }
  let keys = [...map.keys()].sort();
  if (keep) keys = keys.slice(-keep);
  return { header, rows: keys.map((k) => header.map((c) => map.get(k)[c] ?? '')), added, changed, old: map };
}

/** Compare new values with the existing file on overlapping keys: returns a message if more than `maxBad` of the
 *  last `last` overlapping values differ by more than `tol` (catches a misread column before anything is written). */
export function overlapCheck(oldRowsMap, fresh, key, cols, tol, { last = 36, maxBad = 0 } = {}) {
  const pairs = [];
  for (const o of fresh) {
    const r = oldRowsMap.get(o[key]);
    if (!r) continue;
    for (const c of cols) if (isNum(r[c]) && isNum(o[c])) pairs.push([o[key], c, Number(r[c]), Number(o[c])]);
  }
  const recent = pairs.sort((a, b) => (a[0] < b[0] ? -1 : 1)).slice(-last * cols.length);
  const bad = recent.filter(([, , a, b]) => Math.abs(a - b) > tol + 1e-9);
  if (recent.length === 0) return 'no overlap with the existing file to check against';
  if (bad.length > maxBad) return `${bad.length} values differ from the existing file by more than ${tol} (e.g. ${bad[0][0]} ${bad[0][1]}: ${bad[0][2]} vs ${bad[0][3]})`;
  return null;
}

// ---------- NOAA SWPC daily solar and geomagnetic indices ----------
export function swpcDaily(dsd, dgd) {
  const out = new Map();
  const get = (d) => { if (!out.has(d)) out.set(d, { date: d }); return out.get(d); };
  for (const l of dsd.split('\n')) {
    const m = l.match(/^(\d{4}) (\d\d) (\d\d)\s+(.*)$/);
    if (!m) continue;
    const f = m[4].trim().split(/\s+/);
    // flux, ssn, area, new regions, field, xray bkgd, C, M, X, S, 1, 2, 3
    if (f.length < 13) continue;
    const o = get(`${m[1]}-${m[2]}-${m[3]}`);
    o.f107 = pyFloat(f[0]); o.ssn = pyFloat(f[1]); o.flares_m = String(Number(f[7])); o.flares_x = String(Number(f[8]));
  }
  for (const l of dgd.split('\n')) {
    const m = l.match(/^(\d{4}) (\d\d) (\d\d)\s+(.*)$/);
    if (!m) continue;
    // A, 8 K (Fredericksburg), A, 8 K (College), Ap, 8 planetary Kp; "-1" marks a missing value and can touch the
    // previous number ("2-1"), so split those first.
    const t = m[4].replace(/(\d)-1\b/g, '$1 -1').trim().split(/\s+/).map(Number);
    if (t.length !== 27 || t.some(Number.isNaN)) continue;
    const ap = t[18], pk = t.slice(19);
    const valid = pk.filter((k) => k >= 0);
    if (!valid.length) continue;
    const o = get(`${m[1]}-${m[2]}-${m[3]}`);
    o.kp_max = pyFloat(Math.max(...valid));
    o.ap = valid.length === 8 && ap >= 0 ? pyFloat(ap) : '';
  }
  return [...out.values()];
}

// ---------- CAL FIRE active incidents ----------
export function calfire(list, localDate) {
  return list
    .filter((i) => i.IsActive !== false && (i.Type || 'Wildfire') === 'Wildfire')
    .map((i) => ({
      incident: String(i.Name || '').trim(), county: String(i.County || '').split(/[,;]/)[0].trim(),
      started: i.Started ? localDate(new Date(i.Started)) : (i.StartedDateOnly || ''),
      acres: i.AcresBurned == null ? '' : String(Math.round(i.AcresBurned)),
      containment_pct: i.PercentContained == null ? '' : String(Math.round(i.PercentContained)),
    }))
    .sort((a, b) => Number(b.acres || 0) - Number(a.acres || 0));
}

// ---------- NOAA Coral Reef Watch virtual stations ----------
const BAA = ['No stress', 'Watch', 'Warning', 'Alert 1', 'Alert 2', 'Alert 3', 'Alert 4', 'Alert 5'];
export function crwSeries(text) {
  const rows = [];
  for (const l of text.split('\n')) {
    const f = l.trim().split(/\s+/);
    if (f.length < 10 || !/^\d{4}$/.test(f[0])) continue;
    rows.push({ date: `${f[0]}-${f[1]}-${f[2]}`, sst: Number(f[5]), ssta: Number(f[6]), hotspot: Number(f[7]), dhw: Number(f[8]), baa: Number(f[9]) });
  }
  return rows;
}
export function coralDhw(series, since = '2025-01-01') {
  const by = new Map();
  for (const [col, s] of Object.entries(series)) for (const r of s) {
    if (r.date < since) continue;
    if (!by.has(r.date)) by.set(r.date, { date: r.date });
    by.get(r.date)[col] = pyFloat(round(r.dhw, 4));
  }
  return [...by.values()];
}
export function coralNow(series, names, year) {
  return Object.entries(series).map(([col, s]) => {
    const last = s[s.length - 1];
    const yr = s.filter((r) => r.date.startsWith(year));
    const peak = yr.reduce((a, b) => (b.dhw > a.dhw ? b : a), yr[0] || last);
    return { reef: names[col], date: last.date, sst: pyFloat(round(last.sst, 1)), hotspot: pyFloat(round(last.hotspot, 1)), dhw: pyFloat(round(last.dhw, 1)), alert: BAA[last.baa] ?? String(last.baa), dhw_peak_2026: pyFloat(round(peak.dhw, 1)), peak_date: peak.date };
  });
}

// ---------- NASA Ozone Watch daily tables ----------
/** Generic: header line starting "Date", rows "YYYY-MM-DD v v v"; -9999 = missing. Returns [{date, <header>: value}]. */
export function ozoneTable(text) {
  const lines = text.split('\n');
  const h = lines.findIndex((l) => /^Date\s/.test(l));
  if (h < 0) return [];
  const cols = lines[h].trim().split(/\s+/);
  return lines.slice(h + 1).map((l) => l.trim().split(/\s+/)).filter((f) => /^\d{4}-\d\d-\d\d$/.test(f[0]))
    .map((f) => Object.fromEntries(cols.map((c, i) => [c, i === 0 ? f[0] : (Number(f[i]) <= -9999 ? '' : f[i])])));
}
export function ozoneRows(area, mins = []) {
  const mn = new Map(mins.map((r) => [r.Date, r]));
  return area.map((r) => {
    const m = mn.get(r.Date);
    const f2 = (v) => (v === '' || v === undefined ? '' : pyFloat(round(v, 2)));
    const o = { date: r.Date, hole_area: f2(r.Data), area_min: f2(r.Minimum), area_p10: f2(r['10%']), area_mean: f2(r.Mean), area_p90: f2(r['90%']), area_max: f2(r.Maximum) };
    if (m) { o.min_ozone = m.Data === '' ? '' : pyFloat(Number(m.Data)); o.minoz_mean = f2(m.Mean); }
    return o;
  });
}

// ---------- NSIDC Sea Ice Index v4 daily extent: 2026 five-day trailing means ----------
export function nsidcDaily(text) {
  const out = [];
  for (const l of text.split('\n')) {
    const f = l.split(',').map((s) => s.trim());
    if (!/^\d{4}$/.test(f[0]) || !isNum(f[3])) continue;
    out.push({ date: `${f[0]}-${pad2(f[1])}-${pad2(f[2])}`, extent: Number(f[3]) });
  }
  return out;
}
/** Five-day trailing mean of daily extent for each day of `year` (needs all five days present). Keyed by 'MM-DD'. */
export function fiveDayMean(daily, year) {
  const by = new Map(daily.map((d) => [d.date, d.extent]));
  const out = new Map();
  for (const d of daily) {
    if (!d.date.startsWith(year)) continue;
    const t = Date.parse(d.date + 'T00:00:00Z');
    const win = [0, 1, 2, 3, 4].map((k) => by.get(new Date(t - k * 864e5).toISOString().slice(0, 10)));
    if (win.every((v) => v !== undefined)) out.set(d.date.slice(5), round(win.reduce((a, b) => a + b, 0) / 5, 3));
  }
  return out;
}

// ---------- monthly indices ----------
const SEASONS = ['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ', 'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'];
export function oniRows(oni, roni) {
  const rd = new Map();
  for (const l of roni.split('\n')) { const f = l.trim().split(/\s+/); if (SEASONS.includes(f[0]) && isNum(f[2])) rd.set(`${f[0]} ${f[1]}`, f[2]); }
  const out = [];
  for (const l of oni.split('\n')) {
    const f = l.trim().split(/\s+/);
    if (!SEASONS.includes(f[0]) || !isNum(f[3])) continue;
    const season = `${f[0]} ${f[1]}`;
    out.push({ centre_month: `${f[1]}-${pad2(SEASONS.indexOf(f[0]) + 1)}`, season, oni: round(f[3], 2), roni: rd.has(season) ? round(rd.get(season), 2) : '' });
  }
  return out;
}

/** CPC "YYYY  M  value" monthly files. */
export function cpcMonthly(text) {
  const out = new Map();
  for (const l of text.split('\n')) {
    const f = l.trim().split(/\s+/);
    if (f.length === 3 && /^\d{4}$/.test(f[0]) && isNum(f[2]) && Number(f[2]) > -99) out.set(`${f[0]}-${pad2(f[1])}`, f[2]);
  }
  return out;
}
export function aoAao(aoText, aaoText) {
  const ao = cpcMonthly(aoText), aao = cpcMonthly(aaoText);
  return [...ao.keys()].map((m) => ({ month: m, ao: round(ao.get(m), 4), aao: aao.has(m) ? round(aao.get(m), 4) : '' }));
}

export function gistemp(csv) {
  const out = new Map();
  for (const l of csv.split('\n')) {
    const f = l.split(',');
    if (!/^\d{4}$/.test(f[0])) continue;
    for (let m = 1; m <= 12; m++) if (isNum(f[m])) out.set(`${f[0]}-${pad2(m)}`, round(f[m], 2));
  }
  return out;
}
export function maunaLoa(csv) {
  const out = new Map();
  for (const l of csv.split('\n')) {
    const f = l.split(',');
    if (!/^\d{4}$/.test(f[0]) || !isNum(f[3]) || Number(f[3]) < 0) continue;
    out.set(`${f[0]}-${pad2(f[1])}`, { co2: round(f[3], 2), co2_trend: round(f[4], 2) });
  }
  return out;
}
/** Rutgers NH land snow cover (km²) -> million km² and anomaly vs the 1991–2020 mean of the same month. */
export function rutgersSnow(text) {
  const raw = [];
  for (const l of text.split('\n')) { const f = l.trim().split(/\s+/); if (/^\d{4}$/.test(f[0]) && isNum(f[2])) raw.push({ month: `${f[0]}-${pad2(f[1])}`, v: Number(f[2]) / 1e6 }); }
  const norm = {};
  for (let m = 1; m <= 12; m++) {
    const vals = raw.filter((r) => r.month.endsWith('-' + pad2(m)) && r.month >= '1991' && r.month < '2021').map((r) => r.v);
    norm[pad2(m)] = vals.length === 30 ? vals.reduce((a, b) => a + b, 0) / 30 : null;
  }
  return new Map(raw.map((r) => [r.month, { snow_nh: round(r.v, 3), snow_nh_anom: norm[r.month.slice(5)] == null ? '' : round(r.v - norm[r.month.slice(5)], 3) }]));
}
export function planetMonthly(gisText, co2Text, snowText) {
  const g = gistemp(gisText), c = maunaLoa(co2Text), s = rutgersSnow(snowText);
  const months = new Set([...g.keys(), ...c.keys(), ...s.keys()]);
  return [...months].sort().map((m) => ({ month: m, gistemp: g.get(m) ?? '', ...(c.get(m) || {}), ...(s.get(m) || {}) }));
}

/** SILSO monthly mean total sunspot number with the standard 13-month smoothed mean (half weight at the ends). */
export function silso(text) {
  const rows = [];
  for (const l of text.split('\n')) { const f = l.split(';').map((s) => s.trim()); if (/^\d{4}$/.test(f[0]) && isNum(f[3]) && Number(f[3]) >= 0) rows.push({ month: `${f[0]}-${f[1]}`, v: Number(f[3]) }); }
  return rows.map((r, i) => {
    let smooth = '';
    if (i >= 6 && i + 6 < rows.length) {
      const w = rows.slice(i - 6, i + 7).map((x) => x.v);
      smooth = round((0.5 * w[0] + w.slice(1, 12).reduce((a, b) => a + b, 0) + 0.5 * w[12]) / 12, 1);
    }
    return { month: r.month, ssn: pyFloat(r.v), ssn_smooth: smooth };
  });
}

/** CPC upper-300 m heat content: the 180°W–100°W column. */
export function heatContent(text) {
  const out = [];
  for (const l of text.split('\n')) { const f = l.trim().split(/\s+/); if (/^\d{4}$/.test(f[0]) && f.length >= 5 && isNum(f[4])) out.push({ month: `${f[0]}-${pad2(f[1])}`, heat_180_100w: round(f[4], 2) }); }
  return out;
}

export { MONTHS };

// ---------- NOAA ERSSTv5 box means (ERDDAP griddap CSV) for the Blob watch ----------
/** Cos(latitude)-weighted mean SST per month from an ERDDAP griddap CSV (time,depth,latitude,longitude,sst). */
export function ersstBoxMean(csv) {
  const acc = new Map();
  for (const l of csv.split('\n').slice(2)) {
    const f = l.split(',');
    if (f.length < 5 || !isNum(f[4])) continue;
    const m = f[0].slice(0, 7), w = Math.cos((Number(f[2]) * Math.PI) / 180);
    const a = acc.get(m) || { s: 0, w: 0 };
    a.s += w * Number(f[4]); a.w += w; acc.set(m, a);
  }
  return new Map([...acc].map(([m, a]) => [m, a.s / a.w]));
}
/** Monthly anomalies vs the 1991–2020 mean of the same calendar month (needs all 30 years for that month). */
export function anomalies(series, from = '1991', to = '2020') {
  const clim = {};
  for (let k = 1; k <= 12; k++) {
    const v = [...series].filter(([m]) => m.slice(5) === pad2(k) && m.slice(0, 4) >= from && m.slice(0, 4) <= to).map(([, x]) => x);
    clim[pad2(k)] = v.length === 30 ? v.reduce((a, b) => a + b, 0) / 30 : null;
  }
  return new Map([...series].map(([m, x]) => [m, clim[m.slice(5)] == null ? null : x - clim[m.slice(5)]]));
}
export function blobRows(nepCsv, socalCsv, since = '2012-01') {
  const n = anomalies(ersstBoxMean(nepCsv)), s = anomalies(ersstBoxMean(socalCsv));
  return [...n.keys()].filter((m) => m >= since).sort().map((m) => ({ month: m, nep_anom: n.get(m) == null ? '' : round(n.get(m), 2), socal_anom: s.get(m) == null ? '' : round(s.get(m), 2) }));
}

// ---------- CPC Niño SST indices (weekly and monthly) ----------
const MON3 = { JAN: '01', FEB: '02', MAR: '03', APR: '04', MAY: '05', JUN: '06', JUL: '07', AUG: '08', SEP: '09', OCT: '10', NOV: '11', DEC: '12' };
const weekKey = (s) => { const m = s.match(/^(\d\d)([A-Z]{3})(\d{4})$/); return m ? `${m[3]}-${MON3[m[2]]}-${m[1]}` : null; };
const rows = (text) => text.split('\n').map((l) => l.trim().split(/\s+/));

/** wksst9120.for (SST, SSTA pairs) + rel_wksst9120.txt (relative SSTA) -> sst_weekly objects. */
export function sstWeekly(abs, rel) {
  const out = new Map();
  for (const f of rows(abs)) { const k = weekKey(f[0] || ''); if (k && f.length >= 9) out.set(k, { week: k, nino12: round(f[2], 1), nino3: round(f[4], 1), nino34: round(f[6], 1), nino4: round(f[8], 1) }); }
  for (const f of rows(rel)) { const k = weekKey(f[0] || ''); if (k && f.length >= 5 && out.has(k)) Object.assign(out.get(k), { rel_nino12: round(f[1], 1), rel_nino3: round(f[2], 1), rel_nino34: round(f[3], 1), rel_nino4: round(f[4], 1) }); }
  return [...out.values()];
}

/** Monthly table from five CPC files: sstoi.indices, rel_mthsst9120.txt, detrend.nino34.ascii.txt (ERSSTv6),
 *  Rnino34.ascii.txt (relative ERSSTv6) and sstoi.atl.indices. */
export function sstMonthly({ oi, rel, ersst, rersst, atl }) {
  const out = new Map();
  const get = (y, m) => { const k = `${y}-${pad2(m)}`; if (!out.has(k)) out.set(k, { month: k }); return out.get(k); };
  const ym = (f) => /^\d{4}$/.test(f[0]) && /^\d{1,2}$/.test(f[1]);
  for (const f of rows(oi)) if (ym(f) && f.length >= 10) Object.assign(get(f[0], f[1]), { nino12: round(f[3], 2), nino3: round(f[5], 2), nino4: round(f[7], 2), nino34: round(f[9], 2) });
  for (const f of rows(rel)) if (ym(f) && f.length >= 6) Object.assign(get(f[0], f[1]), { rel_nino12: round(f[2], 2), rel_nino3: round(f[3], 2), rel_nino4: round(f[4], 2), rel_nino34: round(f[5], 2) });
  for (const f of rows(ersst)) if (ym(f) && f.length >= 5) get(f[0], f[1]).ersst_nino34 = round(f[4], 2);
  for (const f of rows(rersst)) if (ym(f) && f.length >= 3) get(f[0], f[1]).rel_ersst_nino34 = round(f[2], 2);
  for (const f of rows(atl)) if (ym(f) && f.length >= 8) Object.assign(get(f[0], f[1]), { n_atlantic: round(f[3], 2), s_atlantic: round(f[5], 2), global_tropics: round(f[7], 2) });
  return [...out.values()];
}

// ---------- IBTrACS v04r01 ACTIVE (provisional best tracks) ----------
const POST = new Set(['EX', 'PT']); // extratropical / post-tropical
const LOW = new Set(['LO', 'DB', 'WV', 'MD']); // low, disturbance, wave, monsoon depression
const titleCase = (s) => s.toLowerCase().replace(/(^|[-\s])([a-z])/g, (m, a, b) => a + b.toUpperCase());
/** Saffir–Simpson category from the 1-minute wind (kt), or Post-tropical from the USA status code. */
export function sshs(windKt, status) {
  if (POST.has(status)) return 'Post-tropical';
  if (LOW.has(status)) return 'Low or disturbance';
  if (!isNum(windKt)) return '';
  const w = Number(windKt);
  return w < 34 ? 'TD' : w < 64 ? 'TS' : w < 83 ? 'Cat 1' : w < 96 ? 'Cat 2' : w < 113 ? 'Cat 3' : w < 137 ? 'Cat 4' : 'Cat 5';
}
/** Named storms' 6-hourly fixes (00/06/12/18 UTC) at or after `since` ('YYYY-MM-DD HH:MM'). */
export function ibtracsRows(csv, since) {
  const lines = csv.split('\n');
  const head = lines[0].split(',');
  const ix = Object.fromEntries(head.map((h, i) => [h.trim(), i]));
  const out = [];
  for (const l of lines.slice(2)) {
    const f = l.split(',').map((s) => s.trim());
    if (f.length < head.length / 2) continue;
    const name = f[ix.NAME], t = (f[ix.ISO_TIME] || '').slice(0, 16);
    if (!name || name === 'UNNAMED' || t < since || !/(00|06|12|18):00$/.test(t)) continue;
    const lat = isNum(f[ix.USA_LAT]) ? f[ix.USA_LAT] : f[ix.LAT];
    let lon = Number(isNum(f[ix.USA_LON]) ? f[ix.USA_LON] : f[ix.LON]);
    if (lon > 180) lon -= 360;
    const wind = f[ix.USA_WIND], pres = f[ix.USA_PRES];
    out.push({ storm: titleCase(name), basin: f[ix.BASIN], time_utc: t, lat: round(lat, 1), lon: round(lon, 1), wind_kt: isNum(wind) ? String(Math.round(Number(wind))) : '', pressure_mb: isNum(pres) ? String(Math.round(Number(pres))) : '', category: sshs(wind, f[ix.USA_STATUS]), source: 'IBTrACS v04r01 (provisional)' });
  }
  return out;
}
