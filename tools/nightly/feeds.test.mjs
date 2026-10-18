// Run with: node --test tools/nightly/feeds.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import * as F from './feeds.mjs';

test('pyFloat writes floats like the existing files', () => {
  assert.equal(F.pyFloat(97), '97.0');
  assert.equal(F.pyFloat('3.33'), '3.33');
  assert.equal(F.pyFloat(''), '');
});

test('swpcDaily: DSD flux/SSN/flares and DGD planetary Kp/Ap, incomplete day leaves Ap blank', () => {
  const dsd = '#  Date\n2026 10 16  131     81      700      0    -999      *  13  1  0  2  1  0  0\n';
  const dgd = [
    '2026 10 16    10  3 2 2 2 2 3 3 2    15  2 1 3 3 2 5 3 2    12   3.33  2.00  1.67  2.33  1.67  3.33  3.67  2.33',
    '2026 10 17    -1  1 1 0 1 2 2 2-1    -1  1 1 0 1 1 4 2-1     7   2.00  1.00  0.67  0.67  0.67  2.67  3.00 -1.00',
  ].join('\n');
  const rows = F.swpcDaily(dsd, dgd);
  assert.deepEqual(rows.find((r) => r.date === '2026-10-16'), { date: '2026-10-16', f107: '131.0', ssn: '81.0', flares_m: '1', flares_x: '0', kp_max: '3.67', ap: '12.0' });
  assert.deepEqual(rows.find((r) => r.date === '2026-10-17'), { date: '2026-10-17', kp_max: '3.0', ap: '' });
});

test('mergeRows patches overlaps, appends accepted keys only, keeps the last N', () => {
  const old = 'month,a,b\n2026-01,1,x\n2026-02,2,\n';
  const m = F.mergeRows(old, ['month', 'a', 'b'], 'month', [{ month: '2026-02', a: '2', b: 'y' }, { month: '2026-03', a: '3', b: '' }], { accept: (o) => o.b !== '' });
  assert.deepEqual(m.rows, [['2026-01', '1', 'x'], ['2026-02', '2', 'y']]);
  assert.equal(m.changed, 1);
  const k = F.mergeRows(old, ['month', 'a', 'b'], 'month', [{ month: '2026-03', a: '3', b: 'z' }], { keep: 2 });
  assert.deepEqual(k.rows.map((r) => r[0]), ['2026-02', '2026-03']);
});

test('overlapCheck flags a misread column', () => {
  const m = F.mergeRows('d,v\n1,1.0\n2,2.0\n', ['d', 'v'], 'd', []);
  assert.equal(F.overlapCheck(m.old, [{ d: '1', v: '1.01' }, { d: '2', v: '2.0' }], 'd', ['v'], 0.05), null);
  assert.match(F.overlapCheck(m.old, [{ d: '1', v: '9' }], 'd', ['v'], 0.05), /differ/);
});

test('calfire: local start date, rounded acres, largest first', () => {
  const rows = F.calfire([
    { Name: 'Land Fire ', County: 'Tulare', Started: '2026-10-10T20:00:00Z', AcresBurned: 11, PercentContained: 100, IsActive: true, Type: 'Wildfire' },
    { Name: 'Timber Fire ', County: 'Monterey', Started: '2026-08-09T03:35:00Z', AcresBurned: 25351.9, PercentContained: 97, IsActive: true, Type: 'Wildfire' },
  ], (d) => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Los_Angeles' }).format(d));
  assert.deepEqual(rows[0], { incident: 'Timber Fire', county: 'Monterey', started: '2026-08-08', acres: '25352', containment_pct: '97' });
});

test('coral: DHW column, real HotSpot column, alert names, 2026 peak', () => {
  const txt = 'YYYY MM DD SST_MIN SST_MAX SST@90th_HS SSTA@90th_HS 90th_HS>0 DHW_from_90th_HS>1 BAA_7day_max\n' +
    '2026 05 15 26.0 28.0 28.1 4.0 2.9 24.6 4\n2026 10 15 26.73 28.61 27.53 6.6 1.58 12.0614 4\n';
  const s = { galapagos: F.crwSeries(txt) };
  assert.deepEqual(F.coralDhw(s)[1], { date: '2026-10-15', galapagos: '12.0614' });
  assert.deepEqual(F.coralNow(s, { galapagos: 'Galápagos' }, '2026')[0], { reef: 'Galápagos', date: '2026-10-15', sst: '27.5', hotspot: '1.6', dhw: '12.1', alert: 'Alert 2', dhw_peak_2026: '24.6', peak_date: '2026-05-15' });
});

test('ozone tables: missing days blank, column names from the header', () => {
  const area = F.ozoneTable('Date            Data   Minimum     10%     30%    Mean     70%     90% Maximum\n2026-10-06     24.87      0.73    9.13    1    19.06    1   25.44   28.17\n2026-10-07   -9999.0      0.00    8.13    1   18.34    1   24.84   28.02\n');
  const rows = F.ozoneRows(area, F.ozoneTable('Date Data Minimum 10% Mean\n2026-10-06 120.0 100 110 124.14\n'));
  assert.deepEqual(rows[0], { date: '2026-10-06', hole_area: '24.87', area_min: '0.73', area_p10: '9.13', area_mean: '19.06', area_p90: '25.44', area_max: '28.17', min_ozone: '120.0', minoz_mean: '124.14' });
  assert.equal(rows[1].hole_area, '');
});

test('fiveDayMean needs all five days', () => {
  const daily = F.nsidcDaily('2026, 10, 06, 5.0, 0, x\n2026, 10, 07, 6.0, 0, x\n2026, 10, 08, 7.0, 0, x\n2026, 10, 09, 8.0, 0, x\n2026, 10, 10, 9.0, 0, x\n');
  const m = F.fiveDayMean(daily, '2026');
  assert.equal(m.get('10-10'), '7');
  assert.equal(m.has('10-09'), false);
});

test('ONI seasons map to centre months; RONI joined by season', () => {
  const rows = F.oniRows(' SEAS  YR   TOTAL   ANOM\n  DJF 1950  25.01  -1.32\n  JAS 2026  29.12   2.16\n', 'SEAS   YR  ANOM\nJAS  2026  1.69\n');
  assert.deepEqual(rows, [{ centre_month: '1950-01', season: 'DJF 1950', oni: '-1.32', roni: '' }, { centre_month: '2026-08', season: 'JAS 2026', oni: '2.16', roni: '1.69' }]);
});

test('planet: GISTEMP, Mauna Loa and Rutgers snow with 1991–2020 anomaly', () => {
  const gis = 'Land-Ocean: Global Means\nYear,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec\n2026,1.08,1.23,1.30,1.16,1.13,1.17,1.24,1.42,1.38,***,***,***\n';
  const co2 = 'year,month,decimal date,average,deseasonalized,ndays,sdev,unc\n2026,9,2026.7083,426.07,429.55,18,0.51,0.23\n';
  let snow = '';
  for (let y = 1991; y <= 2020; y++) snow += `${y}  09  5000000\n`;
  snow += '2026  09  5029058\n';
  const sep = F.planetMonthly(gis, co2, snow).find((r) => r.month === '2026-09');
  assert.deepEqual(sep, { month: '2026-09', gistemp: '1.38', co2: '426.07', co2_trend: '429.55', snow_nh: '5.029', snow_nh_anom: '0.029' });
});

test('silso: 13-month smoothed mean with half-weight ends', () => {
  const txt = Array.from({ length: 13 }, (_, i) => `2025;${String(i + 1).padStart(2, '0')};x; ${i === 6 ? 120 : 100}.0; 1; 1;0`).join('\n');
  const rows = F.silso(txt);
  assert.equal(rows[6].ssn_smooth, '101.7');
  assert.equal(rows[5].ssn_smooth, '');
});
