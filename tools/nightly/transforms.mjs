// Pure transforms: API JSON -> CSV rows matching the existing files in data/ column for column.
// No network or file access here, so every function can be unit-tested offline.

export const TZ = 'America/Los_Angeles';

const parts = (d, tz = TZ) =>
  Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', {
      timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
    }).formatToParts(d).map((p) => [p.type, p.value]),
  );

/** 'YYYY-MM-DD HH:MM' in the given time zone. */
export function localStamp(date, tz = TZ) {
  const p = parts(date, tz);
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}`;
}

/** 'YYYY-MM-DD' in the given time zone. */
export const localDate = (date, tz = TZ) => localStamp(date, tz).slice(0, 10);

/** Round to n decimals and drop trailing zeros, as the existing files do ("155.7", not "155.70"). */
export function num(v, n = 1) {
  if (v === null || v === undefined || v === '' || Number.isNaN(Number(v))) return '';
  return String(Number(Number(v).toFixed(n)));
}

/** Fixed decimals ("0.0"), used where the existing file keeps them. */
export function fixed(v, n = 1) {
  if (v === null || v === undefined || v === '' || Number.isNaN(Number(v))) return '';
  return Number(v).toFixed(n);
}

export const cToF = (c) => (c === null || c === undefined ? null : (c * 9) / 5 + 32);
export const kmhToMph = (k) => (k === null || k === undefined ? null : k / 1.609344);

export function toCsv(header, rows) {
  const q = (v) => {
    const s = v === null || v === undefined ? '' : String(v);
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [header, ...rows].map((r) => r.map(q).join(',')).join('\n') + '\n';
}

// ---------- USGS earthquakes (4.5_month.geojson) ----------
export function earthquakes(geo) {
  const rows = geo.features
    .filter((f) => f.properties && f.properties.time && f.geometry)
    .sort((a, b) => b.properties.time - a.properties.time)
    .map((f) => {
      const p = f.properties, [lon, lat, depth] = f.geometry.coordinates;
      return [
        new Date(p.time).toISOString().slice(0, 16).replace('T', ' '),
        p.mag, num(lat, 2), num(lon, 2), depth == null ? '' : Math.round(depth),
        p.place || '', p.tsunami ?? 0, p.alert || '', p.sig ?? '', f.id,
      ];
    });
  return { header: ['time_utc', 'magnitude', 'lat', 'lon', 'depth_km', 'place', 'tsunami_flag', 'pager_alert', 'significance', 'id'], rows };
}

// ---------- NWS KBUR observations ----------
// One row per local clock hour (the observation with the most fields filled; latest wins ties).
export function nwsObservations(json, now = new Date(), hours = 36) {
  const cutoff = now.getTime() - hours * 3600e3;
  const byHour = new Map();
  for (const f of json.features || []) {
    const p = f.properties, t = new Date(p.timestamp);
    if (Number.isNaN(t.getTime()) || t.getTime() < cutoff) continue;
    const filled = ['temperature', 'dewpoint', 'relativeHumidity', 'windSpeed', 'windDirection', 'barometricPressure']
      .filter((k) => p[k] && p[k].value !== null).length + (p.textDescription ? 1 : 0);
    const key = localStamp(t).slice(0, 13);
    const prev = byHour.get(key);
    if (!prev || filled > prev.filled || (filled === prev.filled && t > prev.t)) byHour.set(key, { t, p, filled });
  }
  const rows = [...byHour.values()].sort((a, b) => a.t - b.t).map(({ t, p }) => [
    localStamp(t), num(cToF(p.temperature?.value), 1), num(cToF(p.dewpoint?.value), 1),
    p.relativeHumidity?.value == null ? '' : Math.round(p.relativeHumidity.value),
    fixed(kmhToMph(p.windSpeed?.value), 1), fixed(kmhToMph(p.windGust?.value), 1),
    p.windDirection?.value ?? '', fixed(p.barometricPressure?.value == null ? null : p.barometricPressure.value / 100, 1),
    p.textDescription || '',
  ]);
  return { header: ['time', 'temp_f', 'dewpoint_f', 'rh', 'wind_mph', 'gust_mph', 'wind_dir', 'pressure_hpa', 'text'], rows };
}

// ---------- NWS point forecast periods ----------
export function nwsPeriods(json) {
  const rows = (json.properties?.periods || []).map((p) => [
    p.name, localStamp(new Date(p.startTime)), p.temperature,
    p.probabilityOfPrecipitation?.value ?? 0, `${p.windSpeed} ${p.windDirection}`.trim(), p.shortForecast,
    p.isDaytime ? 'True' : 'False',
  ]);
  return { header: ['period', 'start', 'temp_f', 'precip_chance', 'wind', 'forecast', 'is_day'], rows };
}

// ---------- Open-Meteo hourly forecast + air quality ----------
export function openMeteoHourly(fc, aq) {
  const h = fc.hourly, a = aq?.hourly || { time: [] };
  const aqAt = new Map(a.time.map((t, i) => [t, i]));
  const rows = h.time.map((t, i) => {
    const j = aqAt.get(t);
    const g = (k) => (j === undefined || a[k] == null ? '' : a[k][j] ?? '');
    return [
      t.replace('T', ' '), h.temperature_2m[i] ?? '', h.relative_humidity_2m[i] ?? '', h.dew_point_2m[i] ?? '',
      h.precipitation_probability[i] ?? '', h.precipitation[i] ?? '', h.pressure_msl[i] ?? '', h.wind_speed_10m[i] ?? '',
      h.wind_gusts_10m[i] ?? '', h.wind_direction_10m[i] ?? '', h.uv_index[i] ?? '', g('us_aqi'), g('pm2_5'), g('ozone'),
    ];
  });
  return { header: ['time', 'temp_f', 'rh', 'dewpoint_f', 'precip_prob', 'precip_in', 'pressure_hpa', 'wind_mph', 'gust_mph', 'wind_dir', 'uv', 'us_aqi', 'pm2_5', 'ozone'], rows };
}

// ---------- NOAA CO-OPS ----------
export function tidesHourly(pred, obs) {
  const o = new Map((obs?.data || []).filter((d) => d.t.endsWith(':00') && d.v !== '').map((d) => [d.t, Number(d.v)]));
  const rows = (pred.predictions || []).map((p) => {
    const v = Number(p.v), ob = o.get(p.t);
    return [p.t, num(v, 3), ob === undefined ? '' : num(ob, 3), ob === undefined ? '' : num(ob - v, 3)];
  });
  return { header: ['time', 'predicted_ft', 'observed_ft', 'anomaly_ft'], rows };
}

export function tidesHiLo(pred) {
  const rows = (pred.predictions || []).map((p) => [p.t, num(p.v, 3), p.type]);
  return { header: ['time', 'predicted_ft', 'type'], rows };
}

export function waterTemp(json) {
  const rows = (json.data || []).filter((d) => d.t.endsWith(':00') && d.v !== '').map((d) => [d.t, num(d.v, 1)]);
  return { header: ['time', 'water_temp_f'], rows };
}

// ---------- USGS HANS elevated volcanoes ----------
export function volcanoAlerts(list, coords) {
  const rows = list.map((v) => {
    const c = coords[v.vnum] || coords[v.volcano_name] || {};
    return [v.volcano_name, v.obs_fullname, v.alert_level, v.color_code, c.lat ?? '', c.lon ?? '', (v.sent_utc || '').slice(0, 10)];
  });
  return { header: ['volcano', 'observatory', 'alert_level', 'aviation_color', 'lat', 'lon', 'notice_date'], rows };
}

// ---------- NASA FIRMS VIIRS (area API CSV) ----------
export function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const head = lines.shift().split(',');
  return lines.filter(Boolean).map((l) => Object.fromEntries(l.split(',').map((v, i) => [head[i], v])));
}

const CONF = { l: 'low', n: 'nominal', h: 'high', low: 'low', nominal: 'nominal', high: 'high' };
const hhmm = (t) => String(t).padStart(4, '0');

/** Global 1° grid: low-confidence detections dropped; count, total and max FRP, latest pass (UTC). */
export function firmsGrid(detections) {
  const cells = new Map();
  for (const d of detections) {
    if (CONF[d.confidence] === 'low') continue;
    const lat = Math.floor(Number(d.latitude)) + 0.5, lon = Math.floor(Number(d.longitude)) + 0.5;
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
    const k = `${lat},${lon}`, frp = Number(d.frp) || 0, t = `${d.acq_date} ${hhmm(d.acq_time)}`;
    const c = cells.get(k) || { lat, lon, n: 0, sum: 0, max: 0, latest: '' };
    c.n += 1; c.sum += frp; c.max = Math.max(c.max, frp); if (t > c.latest) c.latest = t;
    cells.set(k, c);
  }
  const rows = [...cells.values()].sort((a, b) => b.sum - a.sum).map((c) => [c.lat, c.lon, c.n, fixed(c.sum, 1), fixed(c.max, 1), c.latest]);
  return { header: ['lat', 'lon', 'detections', 'frp_sum_mw', 'frp_max_mw', 'latest_utc'], rows };
}

function km(a, b, c, d) {
  const r = Math.PI / 180, x = Math.sin(((c - a) * r) / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin(((d - b) * r) / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(x));
}

/** Southern California detections with distance from home and a persistent-heat-source tag.
 *  Site = 0.02° cell (~2 km). Seen on 4+ days with max FRP under 15 MW => likely industrial. */
export function firmsSocal(detections, home) {
  const site = (d) => `${Math.floor(Number(d.latitude) / 0.02)},${Math.floor(Number(d.longitude) / 0.02)}`;
  const days = new Map(), maxFrp = new Map();
  for (const d of detections) {
    const s = site(d);
    if (!days.has(s)) days.set(s, new Set());
    days.get(s).add(d.acq_date);
    maxFrp.set(s, Math.max(maxFrp.get(s) || 0, Number(d.frp) || 0));
  }
  const rows = detections
    .map((d) => {
      const s = site(d), n = days.get(s).size, t = hhmm(d.acq_time);
      const persistent = n >= 4 && maxFrp.get(s) < 15;
      return [d.acq_date, `${t.slice(0, 2)}:${t.slice(2)}`, Number(d.latitude).toFixed(4), Number(d.longitude).toFixed(4), fixed(d.frp, 2),
        CONF[d.confidence] || d.confidence, d.satellite, d.daynight, fixed(km(home.lat, home.lon, Number(d.latitude), Number(d.longitude)), 1), n,
        persistent ? 'Persistent heat source (likely industrial)' : 'Possible fire'];
    })
    .sort((a, b) => (a[0] + a[1]).localeCompare(b[0] + b[1]));
  return { header: ['date', 'time_utc', 'lat', 'lon', 'frp_mw', 'confidence', 'satellite', 'day_night', 'km_from_home', 'days_at_site', 'kind'], rows };
}
