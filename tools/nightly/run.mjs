// Nightly refresh of datasets that come from stable, keyless public APIs.
// Each dataset is fetched, transformed, validated against the existing file, and only then written.
// A failed or suspicious fetch leaves the existing file untouched. Usage: node tools/nightly/run.mjs
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as T from './transforms.mjs';
import * as F from './feeds.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const DATA = path.join(ROOT, 'data');
const UA = 'GlobalWeatherWatch/1.0 (https://github.com/cherkasovakatie-ctrl/weatherwatch)';
const BUR = { lat: 34.2, lon: -118.36 }; // Bob Hope Airport, Burbank
const TIDE = '9410840'; // Santa Monica

async function getJson(url, tries = 3) {
  let last;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'application/json,application/geo+json' }, signal: AbortSignal.timeout(45000) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      last = e;
      await new Promise((res) => setTimeout(res, 3000 * (i + 1)));
    }
  }
  throw new Error(`${url}: ${last.message}`);
}

const ymd = (d) => T.localDate(d).replace(/-/g, '');
const coops = (q) => `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station=${TIDE}&datum=MLLW&units=english&time_zone=lst_ldt&format=json&application=GlobalWeatherWatch&${q}`;

// FIRMS needs a free MAP_KEY (GitHub secret FIRMS_MAP_KEY). It is never printed: errors are redacted.
const FIRMS_KEY = process.env.FIRMS_MAP_KEY || '';
const HOME = { lat: 34.165, lon: -118.395 }; // Valley Village, San Fernando Valley
const redact = (s) => (FIRMS_KEY ? String(s).split(FIRMS_KEY).join('***') : String(s));

async function getText(url, tries = 3) {
  let last;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(120000) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const t = await r.text();
      if (!t.startsWith('latitude')) throw new Error(`unexpected response: ${t.slice(0, 80)}`);
      return t;
    } catch (e) {
      last = e;
      await new Promise((res) => setTimeout(res, 5000 * (i + 1)));
    }
  }
  throw new Error(redact(`${url}: ${last.message}`));
}

async function firms(area, days) {
  if (!FIRMS_KEY) throw new Error('FIRMS_MAP_KEY secret is not set');
  const out = [];
  for (const src of ['VIIRS_NOAA20_NRT', 'VIIRS_SNPP_NRT']) {
    out.push(...T.parseCsv(await getText(`https://firms.modaps.eosdis.nasa.gov/api/area/csv/${FIRMS_KEY}/${src}/${area}/${days}`)));
  }
  return out;
}

async function fetchText(url, { expect = null, tries = 3, timeout = 90000 } = {}) {
  let last;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(timeout) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const t = await r.text();
      if (expect && !expect.test(t)) throw new Error(`unexpected content: ${t.slice(0, 80).replace(/\s+/g, ' ')}`);
      return t;
    } catch (e) {
      last = e;
      await new Promise((res) => setTimeout(res, 3000 * (i + 1)));
    }
  }
  throw new Error(`${url}: ${last.message}`);
}

/** Merge fresh objects into the existing file after checking them against its overlapping values. */
function patch(oldTxt, key, fresh, { cols, tol, accept, keep, last } = {}) {
  const header = oldTxt.split('\n')[0].split(',');
  const m = F.mergeRows(oldTxt, header, key, fresh, { accept, keep });
  if (cols) { const bad = F.overlapCheck(m.old, fresh, key, cols, tol, { last }); if (bad) throw new Error(bad); }
  return { header, rows: m.rows, note: `${m.added} new, ${m.changed} values updated` };
}
const firstKey = (txt) => txt.split('\n')[1].split(',')[0];
const CPC = 'https://www.cpc.ncep.noaa.gov';
const CRW = { florida: ['florida_keys', 'Florida Keys'], puerto_rico: ['puerto_rico', 'Puerto Rico'], galapagos: ['galapagos', 'Galápagos'], hawaii: ['hawaii', 'Hawaii'] };
const crwAll = async () => Object.fromEntries(await Promise.all(Object.entries(CRW).map(async ([k, [f]]) => [k, F.crwSeries(await fetchText(`https://coralreefwatch.noaa.gov/product/vs/data/${f}.txt`, { expect: /DHW/ }))])));
let crwCache;
const OZ = 'https://ozonewatch.gsfc.nasa.gov/meteorology/figures/ozone';

const now = new Date();
const begin = new Date(now.getTime() - 3 * 86400e3), end = new Date(now.getTime() + 4 * 86400e3);

// id -> { fetch, min rows, time column for the freshness check ('first' | 'max' | null) }
const JOBS = {
  earthquakes: { min: 100, time: 'max', run: async () => T.earthquakes(await getJson('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson')) },
  local_obs: { min: 12, time: 'max', run: async () => T.nwsObservations(await getJson('https://api.weather.gov/stations/KBUR/observations?limit=500'), now) },
  local_periods: { min: 8, time: null, run: async () => T.nwsPeriods(await getJson('https://api.weather.gov/gridpoints/LOX/150,51/forecast')) },
  local_hourly: {
    min: 150, time: 'max',
    run: async () => {
      const q = `latitude=${BUR.lat}&longitude=${BUR.lon}&timezone=${encodeURIComponent(T.TZ)}&past_days=2`;
      const fc = await getJson(`https://api.open-meteo.com/v1/forecast?${q}&forecast_days=7&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,precipitation_probability,precipitation,pressure_msl,wind_speed_10m,wind_gusts_10m,wind_direction_10m,uv_index`);
      const aq = await getJson(`https://air-quality-api.open-meteo.com/v1/air-quality?${q}&forecast_days=5&hourly=us_aqi,pm2_5,ozone`);
      return T.openMeteoHourly(fc, aq);
    },
  },
  local_tides: {
    min: 150, time: 'max',
    run: async () => {
      const pred = await getJson(coops(`product=predictions&interval=h&begin_date=${ymd(begin)}&end_date=${ymd(end)}`));
      let obs = { data: [] }, warning;
      try { obs = await getJson(coops('product=water_level&date=recent')); } catch (e) { warning = `observed water level unavailable: ${e.message}`; }
      if (obs.error) warning = `observed water level unavailable: ${JSON.stringify(obs.error)}`;
      return { ...T.tidesHourly(pred, obs), warning };
    },
  },
  local_hilo: { min: 20, time: 'max', run: async () => T.tidesHiLo(await getJson(coops(`product=predictions&interval=hilo&begin_date=${ymd(begin)}&end_date=${ymd(end)}`))) },
  local_watertemp: { min: 24, time: 'max', run: async () => T.waterTemp(await getJson(coops('product=water_temperature&interval=h&date=recent'))) },
  fires_global_grid: { min: 500, time: null, run: async () => T.firmsGrid(await firms('world', 1)) },
  fires_socal: {
    min: 10, time: 'max',
    run: async () => {
      // Sites tagged persistent in the previous file stay known, so a landfill seen on only 1–2 of the 5 days is not flagged.
      const known = (await readCsv('fires_socal.csv')).filter((r) => r.kind?.startsWith('Persistent')).map((r) => ({ lat: Number(r.lat), lon: Number(r.lon) }));
      return T.firmsSocal(await firms('-121.2,32.3,-114.5,36', 5), HOME, known);
    },
  },
  // ---- batch 2: daily feeds ----
  space_daily: {
    min: 20, time: 'max',
    run: async (old) => patch(old, 'date', F.swpcDaily(
      await fetchText('https://services.swpc.noaa.gov/text/daily-solar-indices.txt', { expect: /Daily Solar Data/ }),
      await fetchText('https://services.swpc.noaa.gov/text/daily-geomagnetic-indices.txt', { expect: /Daily Geomagnetic Data/ })),
    { cols: ['ap', 'f107', 'ssn'], tol: 1, keep: 31 }),
  },
  calfire_active: {
    min: 0, time: null,
    run: async () => {
      const list = JSON.parse(await fetchText('https://www.fire.ca.gov/umbraco/api/IncidentApi/List?inactive=false', { expect: /^\s*\[/ }));
      const rows = F.calfire(list, T.localDate);
      return { header: ['incident', 'county', 'started', 'acres', 'containment_pct'], rows: rows.map((r) => [r.incident, r.county, r.started, r.acres, r.containment_pct]) };
    },
  },
  coral_dhw: {
    min: 600, time: 'max',
    run: async (old) => { crwCache ??= await crwAll(); return patch(old, 'date', F.coralDhw(crwCache), { cols: ['florida', 'puerto_rico', 'galapagos', 'hawaii'], tol: 0.05 }); },
  },
  coral_now: {
    min: 4, time: null,
    run: async () => {
      crwCache ??= await crwAll();
      const rows = F.coralNow(crwCache, Object.fromEntries(Object.entries(CRW).map(([k, [, n]]) => [k, n])), String(now.getUTCFullYear()));
      return { header: ['reef', 'date', 'sst', 'hotspot', 'dhw', 'alert', 'dhw_peak_2026', 'peak_date'], rows: rows.map((r) => [r.reef, r.date, r.sst, r.hotspot, r.dhw, r.alert, r.dhw_peak_2026, r.peak_date]) };
    },
  },
  ozone_2026: {
    min: 100, time: null,
    run: async (old) => {
      const area = F.ozoneTable(await fetchText(`${OZ}/to3areas_2026_toms+omi+omps.txt`, { expect: /Ozone Hole Area/ }));
      let mins = [], warning;
      try { mins = F.ozoneTable(await fetchText(`${OZ}/to3mins_2026_toms+omi+omps.txt`, { expect: /Date/ })); } catch (e) { warning = `minimum ozone not refreshed: ${e.message}`; }
      const start = firstKey(old);
      const out = patch(old, 'date', F.ozoneRows(area, mins).filter((r) => r.date >= start), { cols: ['area_mean', 'area_p10', 'area_p90'], tol: 0.02, accept: () => false });
      return { ...out, warning };
    },
  },
  seaice_clim: {
    min: 365, time: null,
    run: async (old) => {
      const yr = String(now.getUTCFullYear());
      const nsidc = (h) => fetchText(`https://noaadata.apps.nsidc.org/NOAA/G02135/${h === 'N' ? 'north' : 'south'}/daily/data/${h}_seaice_extent_daily_v4.0.csv`, { expect: /Extent/, timeout: 120000 });
      const n = F.fiveDayMean(F.nsidcDaily(await nsidc('N')), yr), s = F.fiveDayMean(F.nsidcDaily(await nsidc('S')), yr);
      const fresh = [...new Set([...n.keys(), ...s.keys()])].map((md) => ({ md, [`arctic_${yr}`]: n.get(md) ?? '', [`antarctic_${yr}`]: s.get(md) ?? '' }));
      return patch(old, 'md', fresh, { cols: [`arctic_${yr}`, `antarctic_${yr}`], tol: 0.03, accept: () => false, last: 60 });
    },
  },
  // ---- batch 2: monthly indices, checked daily; a new month is added only when every column has a value ----
  oni: {
    min: 900, time: 'max',
    run: async (old) => patch(old, 'centre_month', F.oniRows(
      await fetchText(`${CPC}/data/indices/oni.ascii.txt`, { expect: /SEAS/ }), await fetchText(`${CPC}/data/indices/RONI.ascii.txt`, { expect: /SEAS/ })),
    { cols: ['oni', 'roni'], tol: 0.05, accept: (o) => o.oni !== '' && o.roni !== '' }),
  },
  ao_aao: {
    min: 900, time: 'max',
    run: async (old) => patch(old, 'month', F.aoAao(
      await fetchText(`${CPC}/products/precip/CWlink/daily_ao_index/monthly.ao.index.b50.current.ascii`),
      await fetchText(`${CPC}/products/precip/CWlink/daily_ao_index/aao/monthly.aao.index.b79.current.ascii`)),
    { cols: ['ao', 'aao'], tol: 0.05, accept: (o) => o.ao !== '' && o.aao !== '' }),
  },
  planet_monthly: {
    min: 1700, time: 'max',
    run: async (old) => patch(old, 'month', F.planetMonthly(
      await fetchText('https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv', { expect: /Land-Ocean/ }),
      await fetchText('https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv', { expect: /year,month/ }),
      await fetchText('https://climate.rutgers.edu/snowcover/files/moncov.nhland.txt')),
    { cols: ['gistemp', 'co2', 'co2_trend', 'snow_nh', 'snow_nh_anom'], tol: 0.06, accept: (o) => ['gistemp', 'co2', 'co2_trend', 'snow_nh', 'snow_nh_anom'].every((c) => o[c] !== '' && o[c] !== undefined) }),
  },
  sunspots_monthly: {
    min: 1500, time: 'max',
    run: async (old) => patch(old, 'month', F.silso(await fetchText('https://www.sidc.be/SILSO/INFO/snmtotcsv.php')),
      { cols: ['ssn', 'ssn_smooth'], tol: 0.2, accept: (o) => o.ssn !== '' }),
  },
  enso_subsurface: {
    min: 500, time: 'max',
    run: async (old) => patch(old, 'month', F.heatContent(await fetchText(`${CPC}/products/analysis_monitoring/ocean/index/heat_content_index.txt`, { expect: /300m/ })),
      { cols: ['heat_180_100w'], tol: 0.05, accept: (o) => o.heat_180_100w !== '' }),
  },
  volcano_alerts_us: {
    min: 0, time: null,
    run: async () => {
      const list = await getJson('https://volcanoes.usgs.gov/hans-public/api/volcano/getElevatedVolcanoes');
      const coords = {};
      for (const r of await readCsv('volcano_alerts_us.csv')) coords[r.volcano] = { lat: r.lat, lon: r.lon };
      for (const v of list) {
        if (coords[v.volcano_name]?.lat) continue;
        try { const d = await getJson(`https://volcanoes.usgs.gov/hans-public/api/volcano/getVolcano/${v.vnum}`); coords[v.vnum] = { lat: d.latitude, lon: d.longitude }; } catch { /* leave blank */ }
      }
      return T.volcanoAlerts(list, coords);
    },
  },
};

async function readCsv(file) {
  const txt = await readFile(path.join(DATA, file), 'utf8').catch(() => '');
  const [head, ...lines] = txt.trim().split('\n');
  const cols = head ? head.split(',') : [];
  return lines.map((l) => Object.fromEntries(l.split(',').map((v, i) => [cols[i], v])));
}

function check(id, job, out, oldTxt) {
  const oldHeader = oldTxt.split('\n')[0];
  if (out.header.join(',') !== oldHeader) return `columns changed: "${out.header.join(',')}" vs "${oldHeader}"`;
  if (out.rows.length < job.min) return `only ${out.rows.length} rows (need ${job.min})`;
  if (job.time) {
    const newest = out.rows.map((r) => String(r[0])).sort().at(-1) || '';
    const oldNewest = oldTxt.trim().split('\n').slice(1).map((l) => l.split(',')[0]).sort().at(-1) || '';
    if (newest < oldNewest) return `newest row ${newest} is older than the existing ${oldNewest}`;
  }
  return null;
}

async function main() {
  const mPath = path.join(DATA, 'manifest.json');
  const manifest = JSON.parse(await readFile(mPath, 'utf8'));
  const today = T.localDate(now);
  const results = [];
  for (const [id, job] of Object.entries(JOBS)) {
    const ds = manifest.datasets.find((d) => d.id === id);
    if (!ds) { results.push({ id, ok: false, error: 'not in manifest' }); continue; }
    const file = path.join(DATA, ds.file);
    try {
      const oldTxt = await readFile(file, 'utf8');
      const out = await job.run(oldTxt);
      const problem = check(id, job, out, oldTxt);
      if (problem) throw new Error(problem);
      const csv = T.toCsv(out.header, out.rows);
      await writeFile(file, csv);
      ds.updated = today;
      ds.bytes = Buffer.byteLength(csv);
      results.push({ id, ok: true, rows: out.rows.length, newest: out.rows.map((r) => String(r[0])).sort().at(-1), ...(out.note ? { note: out.note } : {}), ...(out.warning ? { warning: out.warning } : {}) });
    } catch (e) {
      results.push({ id, ok: false, error: redact(e.message) });
    }
  }
  await writeFile(mPath, JSON.stringify(manifest, null, 1) + '\n');
  const status = { run_utc: now.toISOString(), run_local: T.localStamp(now), results };
  await writeFile(path.join(DATA, 'nightly_status.json'), JSON.stringify(status, null, 1) + '\n');
  for (const r of results) console.log(r.ok ? `ok    ${r.id}: ${r.rows} rows, newest ${r.newest}${r.warning ? ` (warning: ${r.warning})` : ''}` : `FAIL  ${r.id}: ${r.error}`);
  if (!results.some((r) => r.ok)) process.exit(1);
}

main().catch((e) => { console.error(e); process.exit(1); });
