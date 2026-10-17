// Nightly refresh of datasets that come from stable, keyless public APIs.
// Each dataset is fetched, transformed, validated against the existing file, and only then written.
// A failed or suspicious fetch leaves the existing file untouched. Usage: node tools/nightly/run.mjs
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as T from './transforms.mjs';

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
    run: async () => T.tidesHourly(
      await getJson(coops(`product=predictions&interval=h&begin_date=${ymd(begin)}&end_date=${ymd(end)}`)),
      await getJson(coops('product=water_level&date=recent')).catch(() => ({ data: [] })),
    ),
  },
  local_hilo: { min: 20, time: 'max', run: async () => T.tidesHiLo(await getJson(coops(`product=predictions&interval=hilo&begin_date=${ymd(begin)}&end_date=${ymd(end)}`))) },
  local_watertemp: { min: 24, time: 'max', run: async () => T.waterTemp(await getJson(coops('product=water_temperature&interval=h&date=recent'))) },
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
      const out = await job.run();
      const problem = check(id, job, out, oldTxt);
      if (problem) throw new Error(problem);
      const csv = T.toCsv(out.header, out.rows);
      await writeFile(file, csv);
      ds.updated = today;
      ds.bytes = Buffer.byteLength(csv);
      results.push({ id, ok: true, rows: out.rows.length, newest: out.rows.map((r) => String(r[0])).sort().at(-1) });
    } catch (e) {
      results.push({ id, ok: false, error: e.message });
    }
  }
  await writeFile(mPath, JSON.stringify(manifest, null, 1) + '\n');
  const status = { run_utc: now.toISOString(), run_local: T.localStamp(now), results };
  await writeFile(path.join(DATA, 'nightly_status.json'), JSON.stringify(status, null, 1) + '\n');
  for (const r of results) console.log(r.ok ? `ok    ${r.id}: ${r.rows} rows, newest ${r.newest}` : `FAIL  ${r.id}: ${r.error}`);
  if (!results.some((r) => r.ok)) process.exit(1);
}

main().catch((e) => { console.error(e); process.exit(1); });
