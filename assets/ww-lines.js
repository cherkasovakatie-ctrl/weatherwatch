/* WW line-panels helper (pilot, TASK-005). Needs d3 v7 (7.9.0, loaded with an integrity hash).
   Progressive enhancement: the static <img> stays as the fallback; it is hidden only after the chart has rendered.
   Pattern: crosshair + tooltip + keyboard cursor + series toggle + CSV link. Missing values are shown as gaps and "no data", never as zero. */
(function () {
  'use strict';
  var CONFIGS = {
    analogs: { // Figure 1 of enso-2026.html; same series, colours, panels and units as tools/papers/fig_2026.py
      csv: 'data/papers/2026/analog_monthly.csv',
      series: [
        { key: '1982', label: '1982–83', color: '#7a8aa0' }, { key: '1997', label: '1997–98', color: '#d1495b' },
        { key: '2015', label: '2015–16', color: '#edae49' }, { key: '2026', label: '2026', color: '#00798c', bold: true }],
      panels: [
        { v: 'roni', title: 'RONI (°C), 3-month, by centre month', unit: '°C' },
        { v: 'nino12', title: 'Niño 1+2 SST anomaly (°C, OISST)', unit: '°C' },
        { v: 'heat', title: 'Upper-300 m heat content, 180°–100°W (°C)', unit: '°C' },
        { v: 'wwv', title: 'Warm water volume anomaly (10¹⁴ m³)', unit: '10¹⁴ m³' }],
      refLag: 'Sep', refNote: 'dotted line = September of year 0',
      label: 'Four panels comparing 1982–83, 1997–98, 2015–16 and 2026, aligned on the onset year.'
    }
  };
  var CSS = '.wl-root{margin:0 0 8px;position:relative;font:13px/1.4 var(--font-sans,system-ui,sans-serif);color:var(--color-fg,#1d1f22)}' +
    '.wl-legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px}' +
    '.wl-legend button{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:4px 12px;font:inherit;color:inherit;background:var(--color-panel,#fff);border:1px solid var(--color-border-line,#ccc);border-radius:6px;cursor:pointer}' +
    '.wl-legend button[aria-pressed="false"]{opacity:.55;text-decoration:line-through}' +
    '.wl-legend i{width:18px;height:4px;border-radius:2px;display:inline-block}' +
    '.wl-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}@media(max-width:640px){.wl-grid{grid-template-columns:minmax(0,1fr)}}' +
    '.wl-ptitle{font-weight:600;margin:0 0 2px}.wl-panel svg{display:block;width:100%;touch-action:pan-y;overflow:visible}' +
    '.wl-panel svg:focus-visible{outline:2px solid var(--color-fg,#1d1f22);outline-offset:2px}' +
    '.wl-tip{position:absolute;z-index:5;pointer-events:none;background:var(--color-panel,#fff);color:var(--color-fg,#1d1f22);border:1px solid var(--color-border-line,#999);border-radius:6px;padding:6px 8px;box-shadow:0 2px 8px rgba(0,0,0,.18);white-space:nowrap;font-size:12px}' +
    '.wl-tip b{display:block;margin-bottom:2px}.wl-tip i{display:inline-block;width:10px;height:3px;margin-right:6px;vertical-align:middle}.wl-tip .wl-nd{color:var(--color-fg-muted,#5c6370)}' +
    '.wl-note{margin:6px 0 0;color:var(--color-fg-muted,#5c6370);font-size:12px}.wl-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}';

  function num(s) { return s === '' || s == null ? null : +s; }
  function fmt(v, unit) { return v == null ? null : (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(2) + ' ' + unit; }

  function build(fig, cfg, rows) {
    var img = fig.querySelector('img'); if (!img || fig.querySelector('.wl-root')) return;
    var lags = []; rows.forEach(function (r) { if (r['var'] === cfg.panels[0].v && lags.indexOf(r.lag) < 0) lags.push(r.lag); });
    var data = {}; cfg.panels.forEach(function (p) {
      data[p.v] = lags.map(function (lag) { var r = rows.filter(function (x) { return x['var'] === p.v && x.lag === lag; })[0] || {}; var o = { lag: lag }; cfg.series.forEach(function (s) { o[s.key] = num(r[s.key]); }); return o; });
    });
    if (!document.getElementById('ww-lines-css')) { var st = document.createElement('style'); st.id = 'ww-lines-css'; st.textContent = CSS; document.head.appendChild(st); }
    var root = document.createElement('div'); root.className = 'wl-root';
    var legend = document.createElement('div'); legend.className = 'wl-legend'; legend.setAttribute('role', 'group'); legend.setAttribute('aria-label', 'Show or hide events');
    var grid = document.createElement('div'); grid.className = 'wl-grid';
    var tip = document.createElement('div'); tip.className = 'wl-tip'; tip.hidden = true;
    var live = document.createElement('div'); live.className = 'wl-sr'; live.setAttribute('aria-live', 'polite');
    var note = document.createElement('p'); note.className = 'wl-note';
    note.innerHTML = 'Hover, touch or use the arrow keys on a panel to read values; ' + cfg.refNote + '. Gaps mean no data. <a href="' + cfg.csv + '" download>Download the data (CSV)</a>.';
    var hidden = {}, cursor = null, active = null, panels = [];

    cfg.series.forEach(function (s) {
      var b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-pressed', 'true');
      b.innerHTML = '<i style="background:' + s.color + '"></i>' + s.label;
      b.addEventListener('click', function () {
        var on = b.getAttribute('aria-pressed') === 'true';
        if (on && cfg.series.filter(function (x) { return !hidden[x.key]; }).length === 1) return; // keep one series visible
        hidden[s.key] = on; b.setAttribute('aria-pressed', on ? 'false' : 'true'); drawAll();
      });
      legend.appendChild(b);
    });

    cfg.panels.forEach(function (p) {
      var wrap = document.createElement('div'); wrap.className = 'wl-panel';
      var t = document.createElement('div'); t.className = 'wl-ptitle'; t.textContent = p.title;
      var svg = d3.create('svg').attr('tabindex', 0).attr('role', 'group')
        .attr('aria-label', p.title + '. ' + cfg.label + ' Use the left and right arrow keys to read values.');
      wrap.appendChild(t); wrap.appendChild(svg.node()); grid.appendChild(wrap);
      var P = { cfg: p, svg: svg, wrap: wrap, x: null, y: null, m: { t: 8, r: 10, b: 24, l: 42 } };
      svg.on('keydown', function (e) {
        var i = cursor == null ? lags.indexOf(cfg.refLag) : cursor, k = e.key;
        if (k === 'ArrowRight') i = Math.min(lags.length - 1, i + 1); else if (k === 'ArrowLeft') i = Math.max(0, i - 1);
        else if (k === 'Home') i = 0; else if (k === 'End') i = lags.length - 1;
        else if (k === 'Escape') { setCursor(null, null); return; } else return;
        e.preventDefault(); setCursor(i, P, true);
      });
      svg.on('focus', function () { if (cursor == null) setCursor(lags.indexOf(cfg.refLag), P, true); });
      svg.on('blur', function () { setCursor(null, null); });
      svg.on('pointermove pointerdown', function (e) {
        var px = d3.pointer(e, svg.node())[0]; var i = Math.round(P.x.invert(px));
        setCursor(Math.max(0, Math.min(lags.length - 1, i)), P, false);
      });
      svg.on('pointerleave', function (e) { if (e.pointerType !== 'touch') setCursor(null, null); });
      panels.push(P);
    });
    document.addEventListener('pointerdown', function (e) { if (!root.contains(e.target)) setCursor(null, null); });

    function draw(P, w) {
      var m = P.m, h = 230, iw = w - m.l - m.r, ih = h - m.t - m.b, d = data[P.cfg.v];
      var all = []; d.forEach(function (r) { cfg.series.forEach(function (s) { if (r[s.key] != null) all.push(r[s.key]); }); });
      var ext = d3.extent(all.concat([0])); P.x = d3.scaleLinear([0, lags.length - 1], [m.l, m.l + iw]); P.y = d3.scaleLinear(ext, [m.t + ih, m.t]).nice();
      var s = P.svg; s.attr('width', w).attr('height', h).attr('viewBox', '0 0 ' + w + ' ' + h); s.selectAll('*').remove();
      var ticks = P.y.ticks(5);
      s.append('g').selectAll('line').data(ticks).join('line').attr('x1', m.l).attr('x2', m.l + iw).attr('y1', P.y).attr('y2', P.y).attr('stroke', 'var(--color-border-line,#ddd)').attr('stroke-width', 1);
      s.append('line').attr('x1', m.l).attr('x2', m.l + iw).attr('y1', P.y(0)).attr('y2', P.y(0)).attr('stroke', 'var(--color-fg-muted,#888)').attr('stroke-width', 1);
      s.append('g').selectAll('text').data(ticks).join('text').attr('x', m.l - 6).attr('y', P.y).attr('dy', '0.32em').attr('text-anchor', 'end').attr('font-size', 11).attr('fill', 'var(--color-fg-muted,#5c6370)').text(function (v) { return v; });
      var xt = d3.range(0, lags.length, w < 400 ? 6 : 3); // fewer labels on narrow panels so they do not overlap
      s.append('g').selectAll('text').data(xt).join('text').attr('x', function (i) { return P.x(i); }).attr('y', h - 6).attr('text-anchor', 'middle').attr('font-size', 10).attr('fill', 'var(--color-fg-muted,#5c6370)').text(function (i) { return lags[i]; });
      var ri = lags.indexOf(cfg.refLag); if (ri >= 0) s.append('line').attr('x1', P.x(ri)).attr('x2', P.x(ri)).attr('y1', m.t).attr('y2', m.t + ih).attr('stroke', 'var(--color-fg-muted,#999)').attr('stroke-dasharray', '2 3');
      cfg.series.forEach(function (ser) {
        if (hidden[ser.key]) return;
        var ln = d3.line().defined(function (r) { return r[ser.key] != null; }).x(function (r, i) { return P.x(i); }).y(function (r) { return P.y(r[ser.key]); });
        s.append('path').datum(d).attr('d', ln).attr('fill', 'none').attr('stroke', ser.color).attr('stroke-width', ser.bold ? 2.8 : 1.7).attr('stroke-linejoin', 'round');
      });
      P.cross = s.append('g').attr('pointer-events', 'none').attr('display', 'none');
      P.cross.append('line').attr('y1', m.t).attr('y2', m.t + ih).attr('stroke', 'var(--color-fg,#222)').attr('stroke-width', 1);
      P.dots = P.cross.append('g');
    }
    function drawAll() { var w = Math.max(240, Math.floor(panels[0].wrap.clientWidth)); panels.forEach(function (P) { draw(P, w); }); if (cursor != null) setCursor(cursor, active, false); }

    function setCursor(i, P, speak) {
      cursor = i; active = P;
      panels.forEach(function (Q) {
        if (i == null) { Q.cross.attr('display', 'none'); return; }
        var x = Q.x(i), d = data[Q.cfg.v][i];
        Q.cross.attr('display', null).select('line').attr('x1', x).attr('x2', x);
        var vis = cfg.series.filter(function (s) { return !hidden[s.key] && d[s.key] != null; });
        Q.dots.selectAll('circle').data(vis, function (s) { return s.key; }).join('circle').attr('cx', x).attr('cy', function (s) { return Q.y(d[s.key]); }).attr('r', 3.5).attr('fill', function (s) { return s.color; }).attr('stroke', 'var(--color-panel,#fff)');
      });
      if (i == null) { tip.hidden = true; return; }
      var d2 = data[P.cfg.v][i], html = '<b>' + P.cfg.title.split(' (')[0] + ' · ' + d2.lag + '</b>', text = P.cfg.title.split(' (')[0] + ', ' + d2.lag + ': ';
      cfg.series.forEach(function (s) {
        if (hidden[s.key]) return; var f = fmt(d2[s.key], P.cfg.unit);
        html += '<div><i style="background:' + s.color + '"></i>' + s.label + ': ' + (f ? f : '<span class="wl-nd">no data</span>') + '</div>'; text += s.label + ' ' + (f || 'no data') + '; ';
      });
      tip.innerHTML = html; tip.hidden = false;
      var rr = root.getBoundingClientRect(), pr = P.svg.node().getBoundingClientRect();
      var left = pr.left - rr.left + P.x(i) + 12, top = pr.top - rr.top + 8;
      if (left + tip.offsetWidth > rr.width) left = pr.left - rr.left + P.x(i) - tip.offsetWidth - 12;
      tip.style.left = Math.max(0, left) + 'px'; tip.style.top = top + 'px';
      if (speak) live.textContent = text;
    }

    root.appendChild(legend); root.appendChild(grid); root.appendChild(tip); root.appendChild(live); root.appendChild(note);
    img.parentNode.insertBefore(root, img);
    drawAll(); img.hidden = true;
    if (window.ResizeObserver) { var last = 0, tm; new ResizeObserver(function () { var w = Math.floor(panels[0].wrap.clientWidth); if (w === last) return; last = w; clearTimeout(tm); tm = setTimeout(drawAll, 80); }).observe(root); }
  }

  function init() {
    if (!window.d3) return;
    Array.prototype.forEach.call(document.querySelectorAll('figure[data-ww-chart]'), function (fig) {
      var cfg = CONFIGS[fig.getAttribute('data-ww-chart')]; if (!cfg) return;
      d3.csv(cfg.csv).then(function (rows) { build(fig, cfg, rows); }).catch(function () { /* the static image stays */ });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
