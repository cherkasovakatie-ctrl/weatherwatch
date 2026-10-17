/* Storm "mini movie": animated track with environment gauges and scene captions. */
window.stormMovie = async function (host, mv) {
  const el = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  const land = await (await fetch('data/world_land.json')).json();
  const T = (s) => Date.parse(s);
  const fixes = mv.fixes.map((f) => ({ ...f, ms: T(f.t) }));
  const t0 = fixes[0].ms, t1 = fixes[fixes.length - 1].ms, now = T(mv.now), H = 3600e3;
  const cat = (kt) => kt < 34 ? ['TD', '#5aa9f0'] : kt < 64 ? ['TS', '#19c3c3'] : kt < 83 ? ['Cat 1', '#f6e7a1'] : kt < 96 ? ['Cat 2', '#f8cf4d'] : kt < 113 ? ['Cat 3', '#f7a227'] : kt < 137 ? ['Cat 4', '#ef4f23'] : ['Cat 5', '#c2185b'];
  const label = (kt) => kt < 34 ? 'Tropical depression' : kt < 64 ? 'Tropical storm' : kt >= 130 ? 'Super typhoon' : 'Typhoon';
  const at = (ms) => { let i = fixes.findIndex((f) => f.ms >= ms); if (i <= 0) return { ...fixes[Math.max(0, i)] }; const a = fixes[i - 1], b = fixes[i], w = (ms - a.ms) / (b.ms - a.ms);
    return { lat: a.lat + (b.lat - a.lat) * w, lon: a.lon + (b.lon - a.lon) * w, kt: Math.round(a.kt + (b.kt - a.kt) * w), mb: w < .5 ? a.mb : b.mb, kind: ms > now ? 'forecast' : (a.kind === 'estimated' || b.kind === 'estimated') ? 'estimated' : 'observed' }; };
  const envAt = (ms) => mv.env.filter((e) => T(e.t) <= ms).slice(-1)[0] || mv.env[0];
  // layout
  const wrap = el('section', 'card mv'); wrap.append(el('h2', null, mv.title || 'Storm timeline'));
  wrap.append(el('p', 'mvnote', 'Press play to watch the storm form and move. Solid track = observed; dotted = estimated before the first official fix; dashed = official forecast. Dots every 6 hours, coloured by intensity. Captions pause the film at key moments.'));
  const ctr = el('div', 'mvctl'); const btn = el('button', 'mvplay', 'Play'); const sl = el('input'); sl.type = 'range'; sl.min = 0; sl.max = Math.round((t1 - t0) / H); sl.value = 0; const clock = el('span', 'mvclock'); ctr.append(btn, sl, clock);
  const legend = el('div', 'mvleg'); ['TD', 'TS', 'Cat 1', 'Cat 2', 'Cat 3', 'Cat 4', 'Cat 5'].forEach((k, i) => { const c = cat([20, 40, 70, 90, 100, 120, 140][i])[1]; const s = el('span'); const d = el('i'); d.style.background = c; s.append(d, document.createTextNode(k)); legend.append(s); });
  const grid = el('div', 'mvgrid'); const mapBox = el('div', 'mvmap'); const side = el('div', 'mvside');
  grid.append(mapBox, side); wrap.append(ctr, legend, grid); host.append(wrap);
  const cap = el('div', 'mvcap'); cap.hidden = true; mapBox.append(cap);
  // gauges
  const g = {}; [['status', 'Status'], ['wind', 'Max sustained wind'], ['pres', 'Central pressure'], ['sst', 'Sea surface temperature'], ['ohc', 'Warm-water layer (ocean heat content)'], ['shear', 'Vertical wind shear'], ['outflow', 'Outflow aloft'], ['pos', 'Position']].forEach(([k, l]) => { const d = el('div', 'mvg'); d.append(el('div', 'l', l)); g[k] = el('div', 'v'); d.append(g[k]); side.append(d); });
  // map
  const W = mapBox.clientWidth || 800, Hh = Math.round(W * 0.52);
  const [x0, y0, x1, y1] = mv.bbox;
  const x = d3.scaleLinear([x0, x1], [0, W]), y = d3.scaleLinear([y0, y1], [Hh, 0]);
  const svg = d3.select(mapBox).insert('svg', ':first-child').attr('viewBox', `0 0 ${W} ${Hh}`).attr('width', '100%').attr('class', 'mvsvg');
  svg.append('rect').attr('width', W).attr('height', Hh).attr('class', 'mvsea');
  const g0 = svg.append('g');
  land.forEach((r) => { const pts = r.path.split(',').map((p) => p.trim().split(/\s+/).map(Number)); if (!pts.some(([lo, la]) => lo >= x0 - 5 && lo <= x1 + 5 && la >= y0 - 5 && la <= y1 + 5)) return;
    g0.append('path').attr('class', 'mvland').attr('d', 'M' + pts.map(([lo, la]) => `${x(lo)},${y(la)}`).join('L') + 'Z'); });
  for (let lo = Math.ceil(x0 / 5) * 5; lo <= x1; lo += 5) { g0.append('line').attr('class', 'mvgrat').attr('x1', x(lo)).attr('x2', x(lo)).attr('y1', 0).attr('y2', Hh); g0.append('text').attr('class', 'mvtick').attr('x', x(lo) + 3).attr('y', Hh - 4).text(lo + '°E'); }
  for (let la = Math.ceil((y0 + 1) / 5) * 5; la <= y1; la += 5) { g0.append('line').attr('class', 'mvgrat').attr('x1', 0).attr('x2', W).attr('y1', y(la)).attr('y2', y(la)); g0.append('text').attr('class', 'mvtick').attr('x', 3).attr('y', y(la) - 3).text(la + '°N'); }
  (mv.places || []).forEach((p) => { g0.append('circle').attr('cx', x(p.lon)).attr('cy', y(p.lat)).attr('r', 3).attr('class', 'mvplace'); g0.append('text').attr('class', 'mvplbl').attr('x', x(p.lon) + 6).attr('y', y(p.lat) + 4).text(p.name); });
  const fcPath = svg.append('path').attr('class', 'mvfc');
  const trail = svg.append('g'), dots = svg.append('g'), head = svg.append('g');
  const six = []; for (let ms = Math.ceil(t0 / (6 * H)) * 6 * H; ms <= t1; ms += 6 * H) six.push(ms);
  const fmt = (ms) => new Date(ms).toUTCString().replace(':00 GMT', ' UTC').replace(/:00 UTC$/, ' UTC');
  const scenes = mv.scenes.map((s) => ({ ...s, ms: T(s.t), shown: false }));
  function render(ms) {
    const p = at(ms); const [cn, cc] = cat(p.kt);
    trail.selectAll('*').remove(); dots.selectAll('*').remove(); head.selectAll('*').remove();
    const pts = []; for (let m = t0; m <= ms; m += H) pts.push([m, at(m)]);
    for (let i = 1; i < pts.length; i++) { const [m, q] = pts[i], r = pts[i - 1][1]; trail.append('line').attr('x1', x(r.lon)).attr('y1', y(r.lat)).attr('x2', x(q.lon)).attr('y2', y(q.lat)).attr('class', 'mvtrail ' + q.kind); }
    six.filter((m) => m <= ms).forEach((m) => { const q = at(m); dots.append('circle').attr('cx', x(q.lon)).attr('cy', y(q.lat)).attr('r', 4.5).attr('fill', q.kt < 34 && q.kind === 'estimated' ? 'none' : cat(q.kt)[1]).attr('class', 'mvdot ' + q.kind); });
    const fc = []; for (let m = Math.max(ms, now); m <= t1; m += 3 * H) fc.push(at(m));
    fcPath.attr('d', fc.length > 1 ? 'M' + fc.map((q) => `${x(q.lon)},${y(q.lat)}`).join('L') : null);
    const r0 = 7 + Math.min(10, p.kt / 14);
    if (p.kt >= 64) head.append('circle').attr('cx', x(p.lon)).attr('cy', y(p.lat)).attr('r', r0 + 6).attr('class', 'mvhalo').attr('stroke', cc);
    head.append('circle').attr('cx', x(p.lon)).attr('cy', y(p.lat)).attr('r', r0).attr('fill', cc).attr('class', 'mvhead');
    const left = x(p.lon) > W * 0.62; head.append('text').attr('class', 'mvhl').attr('text-anchor', left ? 'end' : 'start').attr('x', x(p.lon) + (left ? -(r0 + 8) : r0 + 8)).attr('y', y(p.lat) - r0 - 2).text(`${label(p.kt)} · ${p.kt} kt${p.kind === 'forecast' ? ' (forecast)' : ''}`);
    const e = envAt(ms);
    g.status.textContent = `${label(p.kt)} (${cn})${p.kind === 'forecast' ? ' — forecast' : p.kind === 'estimated' ? ' — estimated' : ''}`;
    g.wind.textContent = `${p.kt} kt · ${Math.round(p.kt * 1.151)} mph · ${Math.round(p.kt * 1.852)} km/h`;
    g.pres.textContent = p.mb ? `${p.mb} mb` : '—';
    g.sst.textContent = e.sst; g.ohc.textContent = e.ohc; g.shear.textContent = e.shear; g.outflow.textContent = e.outflow;
    g.pos.textContent = `${p.lat.toFixed(1)}°N ${p.lon.toFixed(1)}°E`;
    clock.textContent = fmt(ms) + (ms > now ? ' · forecast' : '');
  }
  let i = 0, timer = null, hold = 0;
  const showCap = (s) => { cap.replaceChildren(el('b', null, s.title), el('p', null, s.text), (() => { const b = el('button', 'mvcont', timer ? 'Continue ▸' : 'Close'); b.onclick = () => { cap.hidden = true; hold = 0; }; return b; })()); cap.hidden = false; };
  const step = () => {
    if (hold > 0) { hold--; return; }
    if (!cap.hidden && hold === 0) cap.hidden = true;
    i++; if (i > +sl.max) { stop(); return; }
    sl.value = i; const ms = t0 + i * H; render(ms);
    const s = scenes.find((q) => q.ms <= ms && q.ms > ms - H); if (s) { showCap(s); hold = Math.round((3000 + s.text.length * 18) / 90); }
  };
  const stop = () => { clearInterval(timer); timer = null; btn.textContent = i >= +sl.max ? 'Replay' : 'Play'; };
  btn.onclick = () => { if (timer) return stop(); if (i >= +sl.max) i = -1; btn.textContent = 'Pause'; timer = setInterval(step, 90); if (i <= 0) { i = 0; render(t0); showCap(scenes[0]); hold = Math.round((3000 + scenes[0].text.length * 18) / 90); } };
  sl.oninput = () => { stop(); i = +sl.value; const ms = t0 + i * H; render(ms); const s = scenes.filter((q) => q.ms <= ms).slice(-1)[0]; if (s && ms - s.ms < 6 * H) showCap(s); else cap.hidden = true; };
  render(t0); showCap(scenes[0]);
};
