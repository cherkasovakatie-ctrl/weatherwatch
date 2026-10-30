/* WW storm-figure helper (TASK-009 package 8). Needs d3 v7 (7.9.0, loaded with an integrity hash).
   Rebuilds the three-panel storm figure of tools/tc2026/fig_storm.py from the same inputs it reads
   (data/tc2026/track_stats.json, env_2026.csv, era5_shear.csv), with the pilot's pattern: linked crosshair, tooltip with
   exact values, keyboard cursor, series toggle, CSV download. The static <img> stays as the fallback and is hidden only
   after the chart has rendered. A missing value is shown as "no data" and left as a gap, never as zero. */
(function () {
  'use strict';
  var C = { wind: '#d1495b', pres: '#30638e', sst: '#00798c', ssta: '#edae49', shear: '#6b4c9a' };
  var SERIES = [ // key, label, unit, colour, panel
    { key: 'wind', label: 'Max wind (kt, 1-min)', unit: 'kt', color: C.wind, panel: 0, dp: 0 },
    { key: 'pres', label: 'Min pressure (mb)', unit: 'mb', color: C.pres, panel: 0, dp: 0, dash: '5 3' },
    { key: 'sst', label: 'SST 3 days before arrival (°C)', unit: '°C', color: C.sst, panel: 1, dp: 2 },
    { key: 'ssta', label: 'SST anomaly vs 1991–2020 (°C)', unit: '°C', color: C.ssta, panel: 1, dp: 2, signed: true },
    { key: 'shear', label: 'ERA5 200–850 hPa shear (kt)', unit: 'kt', color: C.shear, panel: 2, dp: 1 }];
  var PANELS = [
    { title: 'Intensity and pressure', h: 230, unit: 'kt' },
    { title: 'Sea-surface temperature under the track', h: 170, unit: '°C' },
    { title: 'Vertical wind shear', h: 140, unit: 'kt' }];
  var CSS = '.ws-root{margin:0 0 8px;position:relative;font:13px/1.4 var(--font-sans,system-ui,sans-serif);color:var(--color-fg,#1d1f22)}' +
    '.ws-legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px}' +
    '.ws-legend button{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:4px 12px;font:inherit;color:inherit;background:var(--color-panel,#fff);border:1px solid var(--color-border-line,#c8c6bd);border-radius:999px;cursor:pointer}' +
    '.ws-legend button[aria-pressed="false"]{opacity:.55;text-decoration:line-through}.ws-legend button:focus-visible{outline:2px solid var(--color-fg,#1d1f22);outline-offset:2px}' +
    '.ws-legend i{width:18px;height:4px;border-radius:2px;display:inline-block}' +
    '.ws-ptitle{font-weight:600;margin:8px 0 2px}.ws-panel svg{display:block;width:100%;touch-action:pan-y;overflow:visible}' +
    '.ws-panel svg:focus-visible{outline:2px solid var(--color-fg,#1d1f22);outline-offset:2px}' +
    '.ws-tip{position:absolute;z-index:5;pointer-events:none;background:var(--color-panel,#fff);color:var(--color-fg,#1d1f22);border:1px solid var(--color-border-line,#999);border-radius:6px;padding:6px 8px;box-shadow:0 4px 14px rgba(0,0,0,.18);font-size:12px;min-width:12rem}' +
    '.ws-tip b{display:block;margin-bottom:2px}.ws-tip i{display:inline-block;width:10px;height:3px;margin-right:6px;vertical-align:middle}.ws-tip .ws-nd{color:var(--color-fg-muted,#5c6370)}' +
    '.ws-note{margin:6px 0 0;color:var(--color-fg-muted,#5c6370);font-size:12px}.ws-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}';

  var cache = null;
  function load() {
    if (!cache) cache = Promise.all([d3.json('data/tc2026/track_stats.json'), d3.csv('data/tc2026/env_2026.csv'), d3.csv('data/tc2026/era5_shear.csv')]);
    return cache;
  }
  var utc = function (s) { return Date.parse(s.replace(' ', 'T') + ':00Z'); };
  var isInt = function (s) { return /^\d+$/.test(String(s).trim()); };

  // Same selection rules as fig_storm.py: wind and pressure from the fixes when the field is an integer; SST rows unless 'nan' or blank; shear rows unless blank.
  function series(name, T, E, SH) {
    var o = T[name], rows = {}, put = function (t, k, v) { (rows[t] = rows[t] || { t: t })[k] = v; };
    o.fixes.forEach(function (f) { var t = utc(f[0]); if (isInt(f[3])) put(t, 'wind', +f[3]); if (isInt(f[4])) put(t, 'pres', +f[4]); });
    E.forEach(function (r) { if (r.name === name && r.sst_pre_c !== 'nan' && r.sst_pre_c !== '') { var t = utc(r.time); put(t, 'sst', +r.sst_pre_c); put(t, 'ssta', +r.ssta_pre_c); } });
    SH.forEach(function (r) { if (r.name === name && r.shear_kt !== '') put(utc(r.time), 'shear', +r.shear_kt); });
    var list = Object.keys(rows).map(function (k) { return rows[k]; }).sort(function (a, b) { return a.t - b.t; });
    return { rows: list, ri: o.ri_episodes.map(function (e) { return [utc(e.start), utc(e.end)]; }) };
  }
  function fmtVal(s, v) {
    if (v == null) return null;
    var a = Math.abs(v).toFixed(s.dp), sign = s.signed ? (v > 0 ? '+' : v < 0 ? '−' : '') : (v < 0 ? '−' : '');
    return sign + a + ' ' + s.unit;
  }

  function build(fig, name, T, E, SH) {
    var img = fig.querySelector('img'); if (!img || fig.querySelector('.ws-root') || !T[name]) return;
    var D = series(name, T, E, SH), rows = D.rows; if (!rows.length) return;
    var fmtDay = d3.utcFormat('%d %b'), fmtFull = d3.utcFormat('%d %b %Y %H:%M UTC');
    if (!document.getElementById('ww-storm-css')) { var st = document.createElement('style'); st.id = 'ww-storm-css'; st.textContent = CSS; document.head.appendChild(st); }
    var root = document.createElement('div'); root.className = 'ws-root';
    var legend = document.createElement('div'); legend.className = 'ws-legend'; legend.setAttribute('role', 'group'); legend.setAttribute('aria-label', 'Show or hide series');
    var tip = document.createElement('div'); tip.className = 'ws-tip'; tip.hidden = true;
    var live = document.createElement('div'); live.className = 'ws-sr'; live.setAttribute('aria-live', 'polite');
    var note = document.createElement('p'); note.className = 'ws-note';
    var hidden = {}, cursor = null, panels = [];
    var alt = img.getAttribute('alt') || (name + ' 2026');
    var csv = (function () {
      var head = 'time_utc,wind_kt,pressure_mb,sst_pre_c,ssta_pre_c,shear_kt', cols = ['wind', 'pres', 'sst', 'ssta', 'shear'];
      var body = rows.map(function (r) { return d3.utcFormat('%Y-%m-%d %H:%M')(new Date(r.t)) + ',' + cols.map(function (k) { return r[k] == null ? '' : r[k]; }).join(','); });
      return head + '\n' + body.join('\n') + '\n';
    })();
    var a = document.createElement('a'); a.textContent = 'Download the plotted data (CSV)'; a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = 'tc2026_' + name.toLowerCase() + '_figure.csv';
    note.textContent = 'Hover, touch or use the arrow keys on a panel to read values. Shaded bands mark rapid intensification. Gaps mean no data. ';
    note.appendChild(a); note.appendChild(document.createTextNode('.'));

    SERIES.forEach(function (s) {
      if (!rows.some(function (r) { return r[s.key] != null; })) return;
      var b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-pressed', 'true'); b.innerHTML = '<i style="background:' + s.color + '"></i>' + s.label;
      b.addEventListener('click', function () {
        var on = b.getAttribute('aria-pressed') === 'true';
        var visible = SERIES.filter(function (x) { return !hidden[x.key] && rows.some(function (r) { return r[x.key] != null; }); }).length;
        if (on && visible === 1) return; // keep one series visible
        hidden[s.key] = on; b.setAttribute('aria-pressed', on ? 'false' : 'true'); drawAll();
      });
      legend.appendChild(b);
    });

    var t0 = rows[0].t, t1 = rows[rows.length - 1].t; // matplotlib sharex: one time axis for the three panels
    PANELS.forEach(function (p, pi) {
      var wrap = document.createElement('div'); wrap.className = 'ws-panel';
      var t = document.createElement('div'); t.className = 'ws-ptitle'; t.textContent = p.title;
      var svg = d3.create('svg').attr('tabindex', 0).attr('role', 'group').attr('aria-label', alt + ' ' + p.title + '. Use the left and right arrow keys to read values.');
      wrap.appendChild(t); wrap.appendChild(svg.node()); root.appendChild(wrap);
      var P = { i: pi, p: p, svg: svg, wrap: wrap, x: null, ys: {}, m: { t: 8, r: 46, b: 24, l: 46 } };
      svg.on('keydown', function (e) {
        var i = cursor == null ? rows.length - 1 : cursor, k = e.key;
        if (k === 'ArrowRight') i = Math.min(rows.length - 1, i + 1); else if (k === 'ArrowLeft') i = Math.max(0, i - 1);
        else if (k === 'Home') i = 0; else if (k === 'End') i = rows.length - 1;
        else if (k === 'Escape') { setCursor(null, false); return; } else return;
        e.preventDefault(); setCursor(i, true);
      });
      svg.on('focus', function () { if (cursor == null) setCursor(rows.length - 1, true); });
      svg.on('blur', function () { setCursor(null, false); });
      svg.on('pointermove pointerdown', function (e) {
        var px = d3.pointer(e, svg.node())[0], tm = P.x.invert(px), j = d3.bisector(function (r) { return r.t; }).center(rows, tm);
        setCursor(j, false, P);
      });
      svg.on('pointerleave', function (e) { if (e.pointerType !== 'touch') setCursor(null, false); });
      panels.push(P);
    });
    document.addEventListener('pointerdown', function (e) { if (!root.contains(e.target)) setCursor(null, false); });

    function ext(keys, pad) {
      var all = []; rows.forEach(function (r) { keys.forEach(function (k) { if (r[k] != null) all.push(r[k]); }); });
      return all.length ? d3.extent(all) : [0, 1];
    }
    function axisRight(s, P, scale, ticks, fmt) {
      var m = P.m, iw = P.iw;
      s.append('g').selectAll('text').data(ticks).join('text').attr('x', m.l + iw + 6).attr('y', function (v) { return scale(v); }).attr('dy', '0.32em').attr('font-size', 11).attr('fill', 'var(--color-fg-muted,#5c6370)').text(fmt);
    }
    function draw(P, w) {
      var m = P.m, h = P.p.h, iw = w - m.l - m.r, ih = h - m.t - m.b; P.iw = iw; P.ih = ih;
      var s = P.svg; s.attr('width', w).attr('height', h).attr('viewBox', '0 0 ' + w + ' ' + h); s.selectAll('*').remove();
      P.x = d3.scaleUtc([t0, t1], [m.l, m.l + iw]);
      var grid = function (y, ticks) { s.append('g').selectAll('line').data(ticks).join('line').attr('x1', m.l).attr('x2', m.l + iw).attr('y1', y).attr('y2', y).attr('stroke', 'var(--color-border-line,#ddd)'); };
      var left = function (y, ticks, fmt) { s.append('g').selectAll('text').data(ticks).join('text').attr('x', m.l - 6).attr('y', y).attr('dy', '0.32em').attr('text-anchor', 'end').attr('font-size', 11).attr('fill', 'var(--color-fg-muted,#5c6370)').text(fmt); };
      var ref = function (y, v, label) { s.append('line').attr('x1', m.l).attr('x2', m.l + iw).attr('y1', y(v)).attr('y2', y(v)).attr('stroke', 'var(--color-fg-muted,#999)').attr('stroke-dasharray', '1 3'); if (label) s.append('text').attr('x', m.l + 3).attr('y', y(v) - 2).attr('font-size', 9).attr('fill', 'var(--color-fg-muted,#777)').text(label); };
      var line = function (key, y, ser) {
        if (hidden[key]) return;
        var ln = d3.line().defined(function (r) { return r[key] != null; }).x(function (r) { return P.x(r.t); }).y(function (r) { return y(r[key]); });
        s.append('path').datum(rows).attr('d', ln).attr('fill', 'none').attr('stroke', ser.color).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-dasharray', ser.dash || null);
      };
      var se = function (k) { return SERIES.filter(function (x) { return x.key === k; })[0]; };
      if (P.i === 0) {
        var we = ext(['wind']), top = Math.max(we[1], 40) * 1.08; var y = d3.scaleLinear([0, top], [m.t + ih, m.t]); P.ys.wind = y;
        D.ri.forEach(function (e) { s.append('rect').attr('x', P.x(e[0])).attr('width', Math.max(1, P.x(e[1]) - P.x(e[0]))).attr('y', m.t).attr('height', ih).attr('fill', C.wind).attr('opacity', 0.12); });
        var tk = y.ticks(5); grid(y, tk); left(y, tk, function (v) { return v; });
        [[34, 'TS'], [64, 'Cat 1'], [96, 'Cat 3'], [113, 'Cat 4'], [137, 'Cat 5']].forEach(function (c) { if (c[0] < top) ref(y, c[0], c[1]); });
        var pe = ext(['pres']); var yp = d3.scaleLinear([pe[1] + 4, pe[0] - 4], [m.t + ih, m.t]); P.ys.pres = yp; // inverted: lower pressure plots higher
        axisRight(s, P, yp, yp.ticks(5), function (v) { return v; });
        line('wind', y, se('wind')); line('pres', yp, se('pres'));
      } else if (P.i === 1) {
        var ee = ext(['sst']), y2 = d3.scaleLinear([Math.min(ee[0], 26) - 0.5, ee[1] + 0.5], [m.t + ih, m.t]); P.ys.sst = y2;
        var tk2 = y2.ticks(5); grid(y2, tk2); left(y2, tk2, function (v) { return v; }); if (26 > y2.domain()[0]) ref(y2, 26, '26 °C');
        var ae = ext(['ssta']), amax = Math.max(Math.abs(ae[0]), Math.abs(ae[1]), 0.5) * 1.15; var ya = d3.scaleLinear([-amax, amax], [m.t + ih, m.t]); P.ys.ssta = ya;
        axisRight(s, P, ya, ya.ticks(4), function (v) { return v > 0 ? '+' + v : v; });
        s.append('line').attr('x1', m.l).attr('x2', m.l + iw).attr('y1', ya(0)).attr('y2', ya(0)).attr('stroke', 'var(--color-fg-muted,#999)').attr('stroke-width', 0.8);
        if (!hidden.ssta) rows.forEach(function (r) { if (r.ssta == null) return; s.append('rect').attr('x', P.x(r.t) - 1.5).attr('width', 3).attr('y', Math.min(ya(0), ya(r.ssta))).attr('height', Math.abs(ya(r.ssta) - ya(0))).attr('fill', C.ssta).attr('opacity', 0.65); });
        line('sst', y2, se('sst'));
      } else {
        var he = ext(['shear']), y3 = d3.scaleLinear([0, Math.max(he[1], 22) * 1.08], [m.t + ih, m.t]); P.ys.shear = y3;
        var tk3 = y3.ticks(4); grid(y3, tk3); left(y3, tk3, function (v) { return v; }); ref(y3, 10); ref(y3, 20);
        line('shear', y3, se('shear'));
      }
      var xt = P.x.ticks(Math.max(2, Math.floor(iw / 80)));
      s.append('g').selectAll('text').data(xt).join('text').attr('x', function (d) { return P.x(d); }).attr('y', h - 6).attr('text-anchor', 'middle').attr('font-size', 10).attr('fill', 'var(--color-fg-muted,#5c6370)').text(fmtDay);
      P.cross = s.append('g').attr('pointer-events', 'none').attr('display', 'none');
      P.cross.append('line').attr('y1', m.t).attr('y2', m.t + ih).attr('stroke', 'var(--color-fg,#222)');
      P.dots = P.cross.append('g');
    }
    function drawAll() { var w = Math.max(280, Math.floor(panels[0].wrap.clientWidth)); panels.forEach(function (P) { draw(P, w); }); if (cursor != null) setCursor(cursor, false); }

    var active = null;
    function setCursor(i, speak, P) {
      cursor = i; if (P) active = P; else if (!active) active = panels[0];
      panels.forEach(function (Q) {
        if (i == null) { Q.cross.attr('display', 'none'); return; }
        var r = rows[i], x = Q.x(r.t); Q.cross.attr('display', null).select('line').attr('x1', x).attr('x2', x);
        var vis = SERIES.filter(function (s) { return s.panel === Q.i && !hidden[s.key] && r[s.key] != null; });
        Q.dots.selectAll('circle').data(vis, function (s) { return s.key; }).join('circle').attr('cx', x).attr('cy', function (s) { return Q.ys[s.key](r[s.key]); }).attr('r', 3.5).attr('fill', function (s) { return s.color; }).attr('stroke', 'var(--color-panel,#fff)');
      });
      if (i == null) { tip.hidden = true; return; }
      var r2 = rows[i], html = '<b>' + fmtFull(new Date(r2.t)) + '</b>', text = fmtFull(new Date(r2.t)) + ': ';
      SERIES.forEach(function (s) {
        if (hidden[s.key] || !rows.some(function (r) { return r[s.key] != null; })) return;
        var f = fmtVal(s, r2[s.key]);
        html += '<div><i style="background:' + s.color + '"></i>' + s.label + ': ' + (f ? f : '<span class="ws-nd">no data</span>') + '</div>'; text += s.label + ' ' + (f || 'no data') + '; ';
      });
      tip.innerHTML = html; tip.hidden = false;
      var A = active, rr = root.getBoundingClientRect(), pr = A.svg.node().getBoundingClientRect();
      var left = pr.left - rr.left + A.x(r2.t) + 12, top = pr.top - rr.top + 8;
      if (left + tip.offsetWidth > rr.width) left = pr.left - rr.left + A.x(r2.t) - tip.offsetWidth - 12;
      tip.style.left = Math.max(0, left) + 'px'; tip.style.top = top + 'px';
      if (speak) live.textContent = text;
    }

    root.insertBefore(legend, root.firstChild); root.appendChild(tip); root.appendChild(live); root.appendChild(note);
    img.parentNode.insertBefore(root, img);
    drawAll(); img.hidden = true;
    fig.setAttribute('data-ww-ready', '1');
    if (window.ResizeObserver) { var last = 0, tm; new ResizeObserver(function () { var w = Math.floor(panels[0].wrap.clientWidth); if (w === last) return; last = w; clearTimeout(tm); tm = setTimeout(drawAll, 80); }).observe(root); }
  }

  function init() {
    if (!window.d3) return;
    var figs = document.querySelectorAll('figure[data-ww-chart="storm"]'); if (!figs.length) return;
    load().then(function (a) { Array.prototype.forEach.call(figs, function (f) { build(f, f.getAttribute('data-storm'), a[0], a[1], a[2]); }); }).catch(function () { /* the static image stays */ });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
