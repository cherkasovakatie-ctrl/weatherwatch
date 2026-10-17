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
