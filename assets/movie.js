/* Storm "mini movie": animated track over a sea-surface-temperature map, a story panel,
   live conditions and time-linked charts. Global Weather Watch. */
window.stormMovie = async function (host, mv) {
  const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  const land = await (await fetch('data/world_land.json')).json();
  const T = (s) => Date.parse(s), H = 3600e3;
  const fixes = mv.fixes.map((f) => ({ ...f, ms: T(f.t) }));
  const t0 = fixes[0].ms, t1 = fixes[fixes.length - 1].ms, now = T(mv.now);
  const cat = (kt) => kt < 34 ? ['TD', '#5aa9f0'] : kt < 64 ? ['TS', '#19c3c3'] : kt < 83 ? ['Cat 1', '#f6e7a1'] : kt < 96 ? ['Cat 2', '#f8cf4d'] : kt < 113 ? ['Cat 3', '#f7a227'] : kt < 137 ? ['Cat 4', '#ef4f23'] : ['Cat 5', '#c2185b'];
  const label = (kt) => kt < 34 ? 'Tropical depression' : kt < 64 ? 'Tropical storm' : kt >= 130 ? 'Super typhoon' : 'Typhoon';
  const at = (ms) => { const i = fixes.findIndex((f) => f.ms >= ms); if (i <= 0) return { ...fixes[Math.max(0, i)] }; const a = fixes[i - 1], b = fixes[i], w = (ms - a.ms) / (b.ms - a.ms);
    return { lat: a.lat + (b.lat - a.lat) * w, lon: a.lon + (b.lon - a.lon) * w, kt: Math.round(a.kt + (b.kt - a.kt) * w), mb: Math.abs(ms - a.ms) < 2 * H ? a.mb : Math.abs(ms - b.ms) < 2 * H ? b.mb : null,
      kind: ms > now ? 'forecast' : (a.kind === 'estimated' || b.kind === 'estimated') ? 'estimated' : 'observed' }; };
  const envAt = (ms) => mv.env.filter((e) => T(e.t) <= ms).slice(-1)[0] || mv.env[0];
  // sea surface temperature grid (daily)
  const G = mv.sst_grid;
  const sstAt = (lat, lon, ms) => { if (!G) return null; const d = Math.max(0, Math.min(G.days.length - 1, Math.floor((ms - T(G.days[0] + 'T00:00Z')) / (24 * H))));
    const fi = (lat - G.lats[0]) / (G.lats[1] - G.lats[0]), fj = (lon - G.lons[0]) / (G.lons[1] - G.lons[0]);
    const i0 = Math.max(0, Math.min(G.lats.length - 2, Math.floor(fi))), j0 = Math.max(0, Math.min(G.lons.length - 2, Math.floor(fj))), wi = fi - i0, wj = fj - j0;
    const val = (i, j) => { const v = G.v[i * G.lons.length + j][d]; return v == null ? null : G.base + v / G.scale; };
    const q = [[val(i0, j0), (1 - wi) * (1 - wj)], [val(i0, j0 + 1), (1 - wi) * wj], [val(i0 + 1, j0), wi * (1 - wj)], [val(i0 + 1, j0 + 1), wi * wj]].filter(([v]) => v != null);
    const sw = q.reduce((s, [, w]) => s + w, 0); return sw ? q.reduce((s, [v, w]) => s + v * w, 0) / sw : null; };
  const guam = (mv.places || [])[0];
  const km = (a, b) => { const r = Math.PI / 180, dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r; const h = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2; return 12742 * Math.asin(Math.sqrt(h)); };
  // per-hour series for the charts
  const series = []; for (let ms = t0; ms <= t1; ms += H) { const p = at(ms), e = envAt(ms); const q = at(ms + 3 * H), r0 = at(ms - 3 * H);
    series.push({ ms, kt: p.kt, sst: sstAt(p.lat, p.lon, ms), shlo: e.shear_kt ? e.shear_kt[0] : null, shhi: e.shear_kt ? e.shear_kt[1] : null, dist: guam ? km(p, guam) : null, spd: km(r0, q) / 6 / 1.609, kind: p.kind }); }

  // ---------- layout ----------
  const wrap = el('section', 'card mv'); wrap.append(el('h2', null, mv.title || 'Storm timeline'));
  wrap.append(el('p', 'mvnote', 'Press play and choose a speed. The sea is shaded by surface temperature for each day; the track is solid where observed, dotted where estimated before the first official fix and dashed where it is the official forecast. Dots every 6 hours are coloured by intensity. The charts below follow the same clock — click any chart to jump to that moment.'));
  const ctr = el('div', 'mvctl'); const btn = el('button', 'mvplay', 'Play');
  const spd = el('select', 'mvspd'); [['0.5', '½×'], ['1', '1×'], ['2', '2×'], ['4', '4×'], ['8', '8×']].forEach(([v, t]) => { const o = el('option', null, t); o.value = v; if (v === '2') o.selected = true; spd.append(o); });
  const sl = el('input'); sl.type = 'range'; sl.min = 0; sl.max = Math.round((t1 - t0) / H); sl.value = 0; sl.setAttribute('aria-label', 'Time');
  const clock = el('span', 'mvclock'); ctr.append(btn, spd, sl, clock);
  const legend = el('div', 'mvleg'); ['TD', 'TS', 'Cat 1', 'Cat 2', 'Cat 3', 'Cat 4', 'Cat 5'].forEach((k, i) => { const s = el('span'); const d = el('i'); d.style.background = cat([20, 40, 70, 90, 100, 120, 140][i])[1]; s.append(d, document.createTextNode(k)); legend.append(s); });
  const sstLeg = el('span', 'mvsstleg'); legend.append(sstLeg);
  const grid = el('div', 'mvgrid'); const left = el('div', 'mvleft'); const mapBox = el('div', 'mvmap'); const side = el('div', 'mvside');
  const cap = el('div', 'mvcap'); const charts = el('div', 'mvcharts');
  left.append(mapBox, cap); grid.append(left, side); wrap.append(ctr, legend, grid, charts); host.append(wrap);
  const g = {}; [['date', 'Date and time'], ['status', 'Status'], ['wind', 'Max sustained wind'], ['pres', 'Central pressure'], ['sst', 'Sea surface under the storm'], ['ohc', 'Warm-water layer (ocean heat content)'], ['shear', 'Vertical wind shear'], ['outflow', 'Outflow aloft'], ['move', 'Forward speed'], ['dist', 'Distance to Guam'], ['pos', 'Position']].forEach(([k, l]) => { const d = el('div', 'mvg'); d.append(el('div', 'l', l)); g[k] = el('div', 'v'); d.append(g[k]); side.append(d); });

  // ---------- map ----------
  const W = mapBox.clientWidth || 800, Hh = Math.round(W * 0.5);
  const [x0, y0, x1, y1] = mv.bbox;
  const x = d3.scaleLinear([x0, x1], [0, W]), y = d3.scaleLinear([y0, y1], [Hh, 0]);
  const svg = d3.select(mapBox).append('svg').attr('viewBox', `0 0 ${W} ${Hh}`).attr('width', '100%').attr('class', 'mvsvg');
  svg.append('rect').attr('width', W).attr('height', Hh).attr('class', 'mvsea');
  const sstCol = d3.scaleSequential(d3.interpolateRgbBasis(['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c'])).domain([26.5, 31]);
  const sstLayer = svg.append('g').attr('class', 'mvsstl');
  const g0 = svg.append('g');
  land.forEach((r) => { const pts = r.path.split(',').map((p) => p.trim().split(/\s+/).map(Number)); if (!pts.some(([lo, la]) => lo >= x0 - 5 && lo <= x1 + 5 && la >= y0 - 5 && la <= y1 + 5)) return;
    g0.append('path').attr('class', 'mvland').attr('d', 'M' + pts.map(([lo, la]) => `${x(lo)},${y(la)}`).join('L') + 'Z'); });
  for (let lo = Math.ceil(x0 / 5) * 5; lo <= x1; lo += 5) { g0.append('line').attr('class', 'mvgrat').attr('x1', x(lo)).attr('x2', x(lo)).attr('y1', 0).attr('y2', Hh); g0.append('text').attr('class', 'mvtick').attr('x', x(lo) + 3).attr('y', Hh - 4).text(lo + '°E'); }
  for (let la = Math.ceil((y0 + 1) / 5) * 5; la <= y1; la += 5) { g0.append('line').attr('class', 'mvgrat').attr('x1', 0).attr('x2', W).attr('y1', y(la)).attr('y2', y(la)); g0.append('text').attr('class', 'mvtick').attr('x', 3).attr('y', y(la) - 3).text(la + '°N'); }
  (mv.places || []).forEach((p) => { g0.append('circle').attr('cx', x(p.lon)).attr('cy', y(p.lat)).attr('r', 3).attr('class', 'mvplace'); g0.append('text').attr('class', 'mvplbl').attr('x', x(p.lon) + 6).attr('y', y(p.lat) + 4).text(p.name); });
  const dateTag = svg.append('text').attr('class', 'mvdate').attr('x', W - 10).attr('y', 24).attr('text-anchor', 'end');
  const fcPath = svg.append('path').attr('class', 'mvfc');
  const trail = svg.append('g'), dots = svg.append('g'), head = svg.append('g');
  if (G) { const s = el('span'); s.textContent = 'Sea surface °C: '; sstLeg.append(s); [27, 28, 29, 30, 31].forEach((v) => { const b = el('b', 'mvsw', String(v)); b.style.background = sstCol(v); sstLeg.append(b); }); }
  let drawnDay = -1;
  const drawSST = (ms) => { if (!G) return; const d = Math.max(0, Math.min(G.days.length - 1, Math.floor((ms - T(G.days[0] + 'T00:00Z')) / (24 * H)))); if (d === drawnDay) return; drawnDay = d; sstLayer.selectAll('*').remove();
    const dla = G.lats[1] - G.lats[0], dlo = G.lons[1] - G.lons[0];
    G.lats.forEach((la, i) => G.lons.forEach((lo, j) => { const v = G.v[i * G.lons.length + j][d]; if (v == null) return; const t = G.base + v / G.scale;
      sstLayer.append('rect').attr('x', x(lo - dlo / 2)).attr('y', y(la + dla / 2)).attr('width', x(lo + dlo / 2) - x(lo - dlo / 2) + 0.5).attr('height', y(la - dla / 2) - y(la + dla / 2) + 0.5).attr('fill', sstCol(t)); })); };
  const six = []; for (let ms = Math.ceil(t0 / (6 * H)) * 6 * H; ms <= t1; ms += 6 * H) six.push(ms);
  const dFmt = (ms) => new Date(ms).toLocaleString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + ' UTC';
  const chst = (ms) => new Date(ms).toLocaleString('en-US', { weekday: 'short', hour: 'numeric', timeZone: 'Pacific/Guam' }) + ' Guam time';
  const scenes = mv.scenes.map((s) => ({ ...s, ms: T(s.t) }));

  // ---------- charts ----------
  const CH = [
    { k: 'kt', t: 'Max sustained wind (kt)', fmt: (v) => `${v} kt`, refs: [[64, 'typhoon'], [130, 'super typhoon']], col: '#ef4f23' },
    { k: 'sst', t: 'Sea surface temperature under the storm (°C)', fmt: (v) => `${v.toFixed(1)} °C`, refs: [[26.5, 'minimum for a tropical cyclone']], col: '#d7191c' },
    { k: 'sh', t: 'Vertical wind shear (kt, JTWC range)', fmt: (v) => `${v} kt`, refs: [[10, 'low']], col: '#7a8a99', band: true },
    { k: 'dist', t: 'Distance from Guam (km)', fmt: (v) => `${Math.round(v)} km`, refs: [], col: '#2b6cb0' }];
  const cw = charts.clientWidth || 900, chH = 92, ml = 36, mr = 10;
  const cx = d3.scaleUtc([t0, t1], [ml, cw - mr]);
  const cursors = [];
  CH.forEach((c) => { const box = el('div', 'mvch'); box.append(el('div', 'mvcht', c.t)); const val = el('span', 'mvchv'); box.firstChild.append(val); c.val = val; charts.append(box);
    const s2 = d3.select(box).append('svg').attr('viewBox', `0 0 ${cw} ${chH}`).attr('width', '100%');
    const vals = c.band ? series.flatMap((r) => [r.shlo, r.shhi]) : series.map((r) => r[c.k]); const ext = d3.extent(vals.filter((v) => v != null).concat(c.refs.map((r) => r[0])));
    const cy = d3.scaleLinear(ext, [chH - 18, 6]).nice(3);
    cy.ticks(3).forEach((tk) => { s2.append('line').attr('x1', ml).attr('x2', cw - mr).attr('y1', cy(tk)).attr('y2', cy(tk)).attr('class', 'mvcgrid'); s2.append('text').attr('x', ml - 4).attr('y', cy(tk) + 3).attr('text-anchor', 'end').attr('class', 'mvtick').text(tk); });
    d3.utcDay.range(new Date(t0), new Date(t1 + 1)).forEach((d) => { s2.append('line').attr('x1', cx(d)).attr('x2', cx(d)).attr('y1', 4).attr('y2', chH - 16).attr('class', 'mvcgrid'); s2.append('text').attr('x', cx(d) + 3).attr('y', chH - 4).attr('class', 'mvtick').text(d3.utcFormat('%-d %b')(d)); });
    s2.append('rect').attr('x', cx(now)).attr('y', 4).attr('width', Math.max(0, cw - mr - cx(now))).attr('height', chH - 20).attr('class', 'mvfcband');
    c.refs.forEach(([v, l]) => { if (v < cy.domain()[0] || v > cy.domain()[1]) return; s2.append('line').attr('x1', ml).attr('x2', cw - mr).attr('y1', cy(v)).attr('y2', cy(v)).attr('class', 'mvcref'); s2.append('text').attr('x', cw - mr - 2).attr('y', cy(v) - 3).attr('text-anchor', 'end').attr('class', 'mvtick').text(l); });
    if (c.band) s2.append('path').attr('d', d3.area().x((r) => cx(r.ms)).y0((r) => cy(r.shlo)).y1((r) => cy(r.shhi)).curve(d3.curveStepAfter)(series)).attr('fill', c.col).attr('fill-opacity', 0.35);
    else { const ln = d3.line().defined((r) => r[c.k] != null).x((r) => cx(r.ms)).y((r) => cy(r[c.k]));
      s2.append('path').attr('d', ln(series.filter((r) => r.ms <= now))).attr('class', 'mvcl').attr('stroke', c.col);
      s2.append('path').attr('d', ln(series.filter((r) => r.ms >= now))).attr('class', 'mvcl fc').attr('stroke', c.col); }
    cursors.push(s2.append('line').attr('y1', 4).attr('y2', chH - 16).attr('class', 'mvcur'));
    s2.style('cursor', 'pointer').on('click', (ev) => { const [px] = d3.pointer(ev); seek(Math.round((cx.invert(px) - t0) / H)); });
  });
  charts.append(el('p', 'mvnote', 'Shaded right-hand part of each chart = forecast. Sea temperatures: Open-Meteo Marine (daily model analysis; 17–21 October are model forecasts, which already show the storm cooling the sea along its path). Shear ranges are from the Joint Typhoon Warning Center discussions. Positions between official fixes are interpolated.'));

  // ---------- render ----------
  let lastScene = null, live = null;
  function render(ms) {
    const p = at(ms); const [cn, cc] = cat(p.kt); const r = series[Math.round((ms - t0) / H)] || {};
    drawSST(ms);
    trail.selectAll('*').remove(); dots.selectAll('*').remove(); head.selectAll('*').remove();
    let prev = at(t0); for (let m = t0 + H; m <= ms; m += H) { const q = at(m); trail.append('line').attr('x1', x(prev.lon)).attr('y1', y(prev.lat)).attr('x2', x(q.lon)).attr('y2', y(q.lat)).attr('class', 'mvtrail ' + q.kind); prev = q; }
    six.filter((m) => m <= ms).forEach((m) => { const q = at(m); dots.append('circle').attr('cx', x(q.lon)).attr('cy', y(q.lat)).attr('r', 4.5).attr('fill', cat(q.kt)[1]).attr('class', 'mvdot ' + q.kind); });
    const fc = []; for (let m = Math.max(ms, now); m <= t1; m += 3 * H) fc.push(at(m));
    fcPath.attr('d', fc.length > 1 ? 'M' + fc.map((q) => `${x(q.lon)},${y(q.lat)}`).join('L') : null);
    const r0 = 7 + Math.min(10, p.kt / 14);
    if (p.kt >= 64) head.append('circle').attr('cx', x(p.lon)).attr('cy', y(p.lat)).attr('r', r0 + 6).attr('class', 'mvhalo').attr('stroke', cc);
    head.append('circle').attr('cx', x(p.lon)).attr('cy', y(p.lat)).attr('r', r0).attr('fill', cc).attr('class', 'mvhead');
    const lft = x(p.lon) > W * 0.62;
    head.append('text').attr('class', 'mvhl').attr('text-anchor', lft ? 'end' : 'start').attr('x', x(p.lon) + (lft ? -(r0 + 8) : r0 + 8)).attr('y', y(p.lat) - r0 - 2)
      .text(`${label(p.kt)} · ${p.kt} kt${r.sst ? ` · sea ${r.sst.toFixed(1)} °C` : ''}${p.kind === 'forecast' ? ' (forecast)' : ''}`);
    dateTag.text(dFmt(ms));
    const e = envAt(ms);
    g.date.textContent = `${dFmt(ms)} · ${chst(ms)}${ms > now ? ' · forecast' : ''}`;
    g.status.textContent = `${label(p.kt)} (${cn})${p.kind === 'forecast' ? ' — forecast' : p.kind === 'estimated' ? ' — estimated' : ''}`;
    g.wind.textContent = `${p.kt} kt · ${Math.round(p.kt * 1.151)} mph · ${Math.round(p.kt * 1.852)} km/h`;
    g.pres.textContent = p.mb ? `${p.mb} mb` : 'not reported for this time';
    g.sst.textContent = r.sst ? `${r.sst.toFixed(1)} °C (needs ≥ 26.5 °C)` : e.sst;
    g.ohc.textContent = e.ohc; g.shear.textContent = e.shear; g.outflow.textContent = e.outflow;
    g.move.textContent = r.spd ? `${Math.round(r.spd)} mph` : '—';
    g.dist.textContent = r.dist ? `${Math.round(r.dist)} km (${Math.round(r.dist / 1.609)} mi)` : '—';
    g.pos.textContent = `${p.lat.toFixed(1)}°N ${p.lon.toFixed(1)}°E`;
    clock.textContent = dFmt(ms) + (ms > now ? ' · forecast' : '');
    cursors.forEach((c) => c.attr('x1', cx(ms)).attr('x2', cx(ms)));
    CH.forEach((c) => { const v = c.k === 'sh' ? (r.shlo != null ? `${r.shlo}–${r.shhi} kt` : '') : r[c.k] != null ? c.fmt(r[c.k]) : ''; c.val.textContent = v ? ` · ${v}` : ''; });
    const s = scenes.filter((q) => q.ms <= ms).slice(-1)[0] || scenes[0];
    if (s !== lastScene) { lastScene = s; cap.replaceChildren(el('div', 'mvcapd', dFmt(s.ms) + (s.ms > now ? ' · forecast' : '')), el('b', null, s.title), el('p', null, s.text), (live = el('p', 'mvlive'))); cap.classList.remove('mvfade'); void cap.offsetWidth; cap.classList.add('mvfade'); }
    const above = r.sst ? r.sst - 26.5 : null;
    live.textContent = `${ms > now ? 'Forecast for' : 'At'} ${dFmt(ms)}: ${label(p.kt).toLowerCase()} with ${p.kt} kt winds over ${r.sst ? `${r.sst.toFixed(1)} °C water, ${above.toFixed(1)} °C warmer than a tropical cyclone needs` : 'warm water'}; shear ${e.shear}${r.dist ? `; ${Math.round(r.dist).toLocaleString('en-GB')} km from Guam, moving at about ${Math.round(r.spd)} mph` : ''}.`;
  }
  let i = 0, timer = null;
  const speed = () => 140 / +spd.value;
  const seek = (k) => { i = Math.max(0, Math.min(+sl.max, k)); sl.value = i; render(t0 + i * H); };
  const stop = () => { clearInterval(timer); timer = null; btn.textContent = i >= +sl.max ? 'Replay' : 'Play'; };
  const start = () => { clearInterval(timer); btn.textContent = 'Pause'; timer = setInterval(() => { if (i >= +sl.max) return stop(); seek(i + 1); }, speed()); };
  btn.onclick = () => { if (timer) return stop(); if (i >= +sl.max) seek(0); start(); };
  spd.onchange = () => { if (timer) start(); };
  sl.oninput = () => { stop(); seek(+sl.value); };
  render(t0);
};
