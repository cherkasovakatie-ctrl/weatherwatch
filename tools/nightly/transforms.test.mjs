// Run with: node --test tools/nightly/
import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from './transforms.mjs';

test('localStamp converts UTC to Pacific, including the DST change', () => {
  assert.equal(T.localStamp(new Date('2026-10-11T18:00:00Z')), '2026-10-11 11:00'); // PDT, UTC-7
  assert.equal(T.localStamp(new Date('2026-11-02T18:00:00Z')), '2026-11-02 10:00'); // PST, UTC-8
});

test('num drops trailing zeros; fixed keeps them; blanks stay blank', () => {
  assert.equal(T.num(155.70, 2), '155.7');
  assert.equal(T.fixed(0, 1), '0.0');
  assert.equal(T.num(null), '');
  assert.equal(T.fixed(undefined), '');
});

test('toCsv quotes commas and quotes', () => {
  assert.equal(T.toCsv(['a', 'b'], [['x, y', 'say "hi"']]), 'a,b\n"x, y","say ""hi"""\n');
});

test('earthquakes: newest first, rounded like the existing file', () => {
  const geo = { features: [
    { id: 'old', properties: { time: Date.parse('2026-10-01T00:00:00Z'), mag: 4.5, place: 'A', tsunami: 0, alert: null, sig: 312 }, geometry: { coordinates: [143.214, 40.091, 23.4] } },
    { id: 'new', properties: { time: Date.parse('2026-10-11T14:07:30Z'), mag: 6.2, place: '79 km SSE of Panguna, Papua New Guinea', tsunami: 0, alert: 'green', sig: 591 }, geometry: { coordinates: [155.70, -7.012, 53.2] } },
  ] };
  const { header, rows } = T.earthquakes(geo);
  assert.equal(header[0], 'time_utc');
  assert.deepEqual(rows[0], ['2026-10-11 14:07', 6.2, '-7.01', '155.7', 53, '79 km SSE of Panguna, Papua New Guinea', 0, 'green', 591, 'new']);
  assert.equal(rows[1][9], 'old');
});

test('nwsObservations: one row per local hour, unit conversions', () => {
  const f = (ts, extra) => ({ properties: { timestamp: ts, temperature: { value: 21 }, dewpoint: { value: 16 }, relativeHumidity: { value: 73.1 }, windSpeed: { value: 25.92 }, windGust: { value: null }, windDirection: { value: 130 }, barometricPressure: { value: 100474.15 }, textDescription: 'Haze', ...extra } });
  const json = { features: [f('2026-10-11T18:05:00Z'), f('2026-10-11T18:00:00Z', { textDescription: '' }), f('2026-10-11T17:55:00Z')] };
  const { rows } = T.nwsObservations(json, new Date('2026-10-11T19:00:00Z'));
  assert.equal(rows.length, 2); // 10:xx and 11:xx PDT
  assert.deepEqual(rows[1], ['2026-10-11 11:05', '69.8', '60.8', 73, '16.1', '', 130, '1004.7', 'Haze']);
});

test('nwsPeriods: local start time and True/False flags', () => {
  const { rows } = T.nwsPeriods({ properties: { periods: [{ name: 'Tonight', startTime: '2026-10-16T18:00:00-07:00', temperature: 69, probabilityOfPrecipitation: { value: null }, windSpeed: '10 to 15 mph', windDirection: 'NE', shortForecast: 'Mostly Clear', isDaytime: false }] } });
  assert.deepEqual(rows[0], ['Tonight', '2026-10-16 18:00', 69, 0, '10 to 15 mph NE', 'Mostly Clear', 'False']);
});

test('openMeteoHourly merges air quality by time and leaves gaps blank', () => {
  const fc = { hourly: { time: ['2026-10-09T00:00', '2026-10-09T01:00'], temperature_2m: [71.2, 70.1], relative_humidity_2m: [73, 76], dew_point_2m: [62.1, 62.1], precipitation_probability: [0, 0], precipitation: [0, 0], pressure_msl: [1009.2, 1009], wind_speed_10m: [1.3, 0.5], wind_gusts_10m: [5.8, 3.8], wind_direction_10m: [122, 320], uv_index: [0, 0] } };
  const aq = { hourly: { time: ['2026-10-09T00:00'], us_aqi: [67], pm2_5: [13.6], ozone: [27] } };
  const { rows } = T.openMeteoHourly(fc, aq);
  assert.deepEqual(rows[0], ['2026-10-09 00:00', 71.2, 73, 62.1, 0, 0, 1009.2, 1.3, 5.8, 122, 0, 67, 13.6, 27]);
  assert.deepEqual(rows[1].slice(-3), ['', '', '']);
});

test('tidesHourly matches on-the-hour observations and computes the anomaly', () => {
  const { rows } = T.tidesHourly({ predictions: [{ t: '2026-10-17 00:00', v: '1.661' }, { t: '2026-10-17 01:00', v: '2.1' }] }, { data: [{ t: '2026-10-17 00:00', v: '1.900' }, { t: '2026-10-17 00:06', v: '1.95' }] });
  assert.deepEqual(rows[0], ['2026-10-17 00:00', '1.661', '1.9', '0.239']);
  assert.deepEqual(rows[1], ['2026-10-17 01:00', '2.1', '', '']);
});

test('volcanoAlerts uses known coordinates and the notice date', () => {
  const { rows } = T.volcanoAlerts([{ volcano_name: 'Great Sitkin', vnum: '311120', obs_fullname: 'Alaska Volcano Observatory', alert_level: 'WATCH', color_code: 'ORANGE', sent_utc: '2026-10-17 19:05:57' }], { 'Great Sitkin': { lat: '52.0765', lon: '-176.1109' } });
  assert.deepEqual(rows[0], ['Great Sitkin', 'Alaska Volcano Observatory', 'WATCH', 'ORANGE', '52.0765', '-176.1109', '2026-10-17']);
});

test('firmsGrid: 1-degree cells, low confidence dropped, sorted by total power', () => {
  const d = [
    { latitude: '46.9', longitude: '119.2', acq_date: '2026-10-11', acq_time: '548', confidence: 'n', frp: '10.5' },
    { latitude: '46.1', longitude: '119.8', acq_date: '2026-10-11', acq_time: '0530', confidence: 'h', frp: '4.5' },
    { latitude: '-7.2', longitude: '140.9', acq_date: '2026-10-11', acq_time: '0512', confidence: 'l', frp: '99' },
  ];
  const { rows } = T.firmsGrid(d);
  assert.deepEqual(rows, [[46.5, 119.5, 2, '15.0', '10.5', '2026-10-11 0548']]);
});

test('firmsSocal: distance from home and persistent-heat tag', () => {
  const det = (date, frp) => ({ latitude: '35.1211', longitude: '-118.3684', acq_date: date, acq_time: '949', confidence: 'n', frp, satellite: 'N', daynight: 'N' });
  const d = ['2026-10-04', '2026-10-05', '2026-10-06', '2026-10-07'].map((x) => det(x, '0.47'));
  const { rows } = T.firmsSocal(d, { lat: 34.165, lon: -118.395 });
  assert.equal(rows.length, 4);
  assert.deepEqual(rows[0], ['2026-10-04', '09:49', '35.1211', '-118.3684', '0.47', 'nominal', 'N', 'N', '106.3', 4, 'Persistent heat source (likely industrial)']);
  const hot = T.firmsSocal([...d, det('2026-10-08', '40')], { lat: 34.165, lon: -118.395 }).rows;
  assert.equal(hot[0][10], 'Possible fire');
});

test('firmsSocal: a site across a grid edge is one site; known sites carry over', () => {
  const det = (date, lat, lon) => ({ latitude: String(lat), longitude: String(lon), acq_date: date, acq_time: '943', confidence: 'n', frp: '0.5', satellite: 'N', daynight: 'N' });
  const home = { lat: 34.165, lon: -118.395 };
  // Sun Valley-style site: three nights, detections either side of the old 0.02° cell edge at -118.38
  const sv = [det('2026-10-14', 34.2435, -118.3792), det('2026-10-15', 34.2425, -118.3816), det('2026-10-16', 34.2436, -118.3837)];
  assert.ok(T.firmsSocal(sv, home).rows.every((r) => r[9] === 3 && r[10].startsWith('Persistent')));
  // one night only: possible fire, unless the previous run knew the site
  const one = [det('2026-10-17', 34.2430, -118.3800)];
  assert.equal(T.firmsSocal(one, home).rows[0][10], 'Possible fire');
  assert.ok(T.firmsSocal(one, home, [{ lat: 34.2432, lon: -118.3825 }]).rows[0][10].startsWith('Persistent'));
  // a detection 5 km away from the known site is not affected
  assert.equal(T.firmsSocal([det('2026-10-17', 34.2430, -118.3260)], home, [{ lat: 34.2432, lon: -118.3825 }]).rows[0][10], 'Possible fire');
});
