// Charts for warming-since-1976.html. Data: data/planet_monthly.csv and data/report1976/*.csv.
(() => {
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const S = (i) => `var(--s${i})`;
  const fmt1 = d3.format('.1f'), fmt2 = d3.format('.2f'), fmt3 = d3.format('.3f');
  const signed = (f) => (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + f(Math.abs(v));
  const tip = document.createElement('div'); tip.className = 'viz-tip'; tip.hidden = true; document.body.append(tip);
  const showTip = (ev, html) => {
    tip.innerHTML = html; tip.hidden = false;
    const r = tip.getBoundingClientRect(), pad = 12;
    let x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - pad;
    if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - pad;
    tip.style.left = `${Math.max(8, x)}px`; tip.style.top = `${Math.max(8, y)}px`;
  };
  const hideTip = () => { tip.hidden = true; };
  const row = (color, label, val) => `<div class="tr"><i style="background:${color}"></i><span>${label}</span><b>${val}</b></div>`;

  function legend(fig, items) {
    const l = fig.querySelector('.legend'); if (!l) return; l.replaceChildren();
    items.forEach((it) => { const s = document.createElement('span'); s.innerHTML = `<i style="background:${it.color}${it.dash ? ';height:2px;border-top:2px dashed ' + it.color + ';background:none' : ''}"></i>${it.label}`; l.append(s); });
  }
  function table(fig, head, rows) {
    let d = fig.querySelector('details.dt');
    if (!d) { d = document.createElement('details'); d.className = 'dt'; d.innerHTML = '<summary>Data table</summary><div class="tw"></div>'; fig.append(d); }
    const t = document.createElement('table');
    const ft = fig.querySelector('.ft');
    const cap = ft ? `<caption style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap">${ft.innerHTML}</caption>` : '';
    t.innerHTML = `${cap}<thead><tr>${head.map((h) => `<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody>`;
    d.querySelector('.tw').replaceChildren(t);
  }
  function frame(el, H, mlExtra = 0) {
    el.replaceChildren();
    const W = Math.max(280, el.clientWidth);
    const m = { t: 12, r: 14, b: 26, l: 40 + mlExtra };
    const svg = d3.select(el).append('svg').attr('viewBox', `0 0 ${W} ${H}`).attr('width', '100%').attr('role', 'img');
    return { svg, W, H, m, iw: W - m.l - m.r, ih: H - m.t - m.b };
  }
  function axes(f, x, y, { xTicks, xFmt = d3.format('d'), yFmt = fmt1, yTicks = 5, yLabel }) {
    const g = f.svg.append('g');
    g.selectAll('line.grid').data(y.ticks(yTicks)).join('line').attr('class', 'grid')
      .attr('x1', f.m.l).attr('x2', f.m.l + f.iw).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
    g.selectAll('text.yt').data(y.ticks(yTicks)).join('text').attr('class', 'tk').attr('x', f.m.l - 6).attr('y', (d) => y(d)).attr('dy', '0.32em').attr('text-anchor', 'end').text(yFmt);
    const xt = xTicks || x.ticks(Math.max(3, Math.floor(f.iw / 80)));
    g.selectAll('text.xt').data(xt).join('text').attr('class', 'tk').attr('x', (d) => x(d)).attr('y', f.H - 8).attr('text-anchor', 'middle').text(xFmt);
    if (yLabel) g.append('text').attr('class', 'tk').attr('x', f.m.l).attr('y', 9).text(yLabel);
    if (y.domain()[0] < 0 && y.domain()[1] > 0) g.append('line').attr('class', 'zero').attr('x1', f.m.l).attr('x2', f.m.l + f.iw).attr('y1', y(0)).attr('y2', y(0));
  }
  function marks(f, x, list) {
    (list || []).forEach((mk, i) => {
      const px = x(mk.x); if (px < f.m.l || px > f.m.l + f.iw) return;
      f.svg.append('line').attr('class', 'mark').attr('x1', px).attr('x2', px).attr('y1', f.m.t).attr('y2', f.m.t + f.ih);
      const near = px > f.m.l + f.iw * 0.8;
      f.svg.append('text').attr('class', 'mlbl').attr('x', near ? px - 4 : px + 4).attr('text-anchor', near ? 'end' : 'start').attr('y', f.m.t + 10 + (i % 3) * 12).text(mk.label);
    });
  }
  // Line chart with crosshair tooltip. series: [{key,label,color,width,dash}]
  function lines(el, o) {
    const f = frame(el, o.height || 260);
    const x = d3.scaleLinear(d3.extent(o.data, (d) => d.x), [f.m.l, f.m.l + f.iw]);
    const vals = o.data.flatMap((d) => o.series.map((s) => d[s.key])).filter((v) => v != null);
    const y = d3.scaleLinear(d3.extent(o.zero ? [...vals, 0] : vals), [f.m.t + f.ih, f.m.t]).nice();
    axes(f, x, y, o); marks(f, x, o.marks);
    o.series.forEach((s) => {
      f.svg.append('path').datum(o.data.filter((d) => d[s.key] != null)).attr('fill', 'none').attr('stroke', s.color)
        .attr('stroke-width', s.width || 2).attr('stroke-dasharray', s.dash ? '5 4' : null).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round')
        .attr('d', d3.line().x((d) => x(d.x)).y((d) => y(d[s.key])));
    });
    hover(f, x, o.data, (d) => o.series.filter((s) => d[s.key] != null).map((s) => ({ color: s.color, label: s.label, v: d[s.key], y: y(d[s.key]) })), o);
  }
  // Stacked area; keys in stack order bottom-up.
  function stack(el, o) {
    const f = frame(el, o.height || 280);
    const st = d3.stack().keys(o.keys)(o.data);
    const x = d3.scaleLinear(d3.extent(o.data, (d) => d.x), [f.m.l, f.m.l + f.iw]);
    const y = d3.scaleLinear([Math.min(0, d3.min(st, (l) => d3.min(l, (p) => p[0]))), d3.max(st, (l) => d3.max(l, (p) => p[1]))], [f.m.t + f.ih, f.m.t]).nice();
    axes(f, x, y, o);
    const area = d3.area().x((p) => x(p.data.x)).y0((p) => y(p[0])).y1((p) => y(p[1]));
    st.forEach((l, i) => f.svg.append('path').datum(l).attr('fill', o.colors[i]).attr('stroke', 'var(--color-panel)').attr('stroke-width', 1).attr('d', area));
    marks(f, x, o.marks);
    hover(f, x, o.data, (d) => o.keys.map((k, i) => ({ color: o.colors[i], label: o.labels[i], v: d[k] })).reverse(), o, (d) => (o.totalLabel ? `<div class="tr tot"><span>${o.totalLabel}</span><b>${o.valFmt(d3.sum(o.keys, (k) => d[k]))}</b></div>` : ''));
  }
  function hover(f, x, data, pick, o, extra = () => '') {
    const rule = f.svg.append('line').attr('class', 'rule').attr('y1', f.m.t).attr('y2', f.m.t + f.ih).style('opacity', 0);
    const dots = f.svg.append('g');
    const bis = d3.bisector((d) => d.x).center;
    f.svg.append('rect').attr('x', f.m.l).attr('y', 0).attr('width', f.iw).attr('height', f.H).attr('fill', 'transparent')
      .on('pointermove', (ev) => {
        const d = data[bis(data, x.invert(d3.pointer(ev)[0]))]; if (!d) return;
        rule.attr('x1', x(d.x)).attr('x2', x(d.x)).style('opacity', 1);
        const items = pick(d); dots.selectAll('*').remove();
        items.forEach((it) => { if (it.y != null) dots.append('circle').attr('cx', x(d.x)).attr('cy', it.y).attr('r', 4).attr('fill', it.color).attr('stroke', 'var(--color-panel)').attr('stroke-width', 2); });
        showTip(ev, `<div class="th">${o.tipTitle ? o.tipTitle(d) : d.x}</div>${items.map((it) => row(it.color, it.label, o.valFmt(it.v))).join('')}${extra(d)}`);
      })
      .on('pointerleave', () => { rule.style('opacity', 0); dots.selectAll('*').remove(); hideTip(); });
  }
  // Horizontal bars. rows: [{label, parts:[{v,color,label}]}]; parts stack (may be negative for diverging).
  function hbars(el, o) {
    const lw = Math.min(o.labelWidth || 170, Math.max(96, el.clientWidth * 0.36));
    const rh = 26, H = o.rows.length * rh + 34;
    const f = frame(el, H, lw - 40);
    const lo = Math.min(0, d3.min(o.rows, (r) => d3.sum(r.parts.filter((p) => p.v < 0), (p) => p.v)));
    const hi = Math.max(0, d3.max(o.rows, (r) => d3.sum(r.parts.filter((p) => p.v > 0), (p) => p.v)));
    const x = d3.scaleLinear([lo, hi], [f.m.l, f.m.l + f.iw - (o.endLabel ? (o.endW || 44) : 0)]).nice();
    const nt = f.iw < 260 ? 2 : 4;
    f.svg.selectAll('line.grid').data(x.ticks(nt)).join('line').attr('class', 'grid').attr('y1', f.m.t).attr('y2', f.m.t + f.ih).attr('x1', (d) => x(d)).attr('x2', (d) => x(d));
    f.svg.selectAll('text.xt').data(x.ticks(nt)).join('text').attr('class', 'tk').attr('x', (d) => x(d)).attr('y', f.H - 8).attr('text-anchor', 'middle').text(o.tickFmt || o.valFmt);
    f.svg.append('line').attr('class', 'zero').attr('x1', x(0)).attr('x2', x(0)).attr('y1', f.m.t).attr('y2', f.m.t + f.ih);
    o.rows.forEach((r, i) => {
      const cy = f.m.t + i * rh, bh = rh - 8;
      f.svg.append('text').attr('class', 'blbl').attr('x', f.m.l - 8).attr('y', cy + bh / 2).attr('dy', '0.32em').attr('text-anchor', 'end').text(r.label);
      let pos = 0, neg = 0;
      r.parts.forEach((p) => {
        const a = p.v >= 0 ? pos : neg + p.v, b = p.v >= 0 ? pos + p.v : neg;
        if (p.v >= 0) pos += p.v; else neg += p.v;
        f.svg.append('rect').attr('x', x(a)).attr('y', cy).attr('width', Math.max(1, x(b) - x(a) - 1)).attr('height', bh).attr('rx', 2).attr('fill', p.color);
      });
      const total = r.total != null ? r.total : d3.sum(r.parts, (p) => p.v);
      if (o.endLabel) f.svg.append('text').attr('class', 'bval').attr('x', x(Math.max(0, pos)) + 5).attr('y', cy + bh / 2).attr('dy', '0.32em').text(o.endLabel(r, total));
      f.svg.append('rect').attr('x', 0).attr('y', cy - 3).attr('width', f.W).attr('height', rh).attr('fill', 'transparent')
        .on('pointermove', (ev) => showTip(ev, `<div class="th">${r.label}</div>${r.parts.map((p) => row(p.color, p.label, o.valFmt(p.v))).join('')}${r.parts.length > 1 ? `<div class="tr tot"><span>Total</span><b>${o.valFmt(total)}</b></div>` : ''}${r.note ? `<div class="tn">${r.note}</div>` : ''}`))
        .on('pointerleave', hideTip);
    });
  }

  const num = (v) => (v === '' || v == null ? null : +v);
  const drawers = [];
  const redraw = () => drawers.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });
  const fig = (id) => document.getElementById(id);

  Promise.all([
    d3.csv('data/planet_monthly.csv'),
    d3.csv('data/report1976/forcing_by_agent.csv'),
    d3.csv('data/report1976/co2_by_fuel_world.csv'),
    d3.csv('data/report1976/so2_by_sector.csv'),
    d3.csv('data/report1976/ch4_by_sector.csv'),
    d3.csv('data/report1976/ghg_warming_world.csv'),
    d3.csv('data/report1976/country_ghg_warming_1976_2024.csv'),
  ]).then(([pm, erf, fuel, so2, ch4, ghgw, ctry]) => {
    // 1. Temperature with trends
    const byYear = d3.rollups(pm.filter((r) => r.gistemp !== ''), (v) => ({ n: v.length, t: d3.mean(v, (r) => +r.gistemp) }), (r) => +r.month.slice(0, 4))
      .filter(([, o]) => o.n === 12).map(([x, o]) => ({ x, t: o.t })).sort((a, b) => a.x - b.x);
    const lastY = byYear[byYear.length - 1].x;
    const fit = (a, b) => { const p = byYear.filter((d) => d.x >= a && d.x <= b); const mx = d3.mean(p, (d) => d.x), my = d3.mean(p, (d) => d.t); const k = d3.sum(p, (d) => (d.x - mx) * (d.t - my)) / d3.sum(p, (d) => (d.x - mx) ** 2); return (x) => my + k * (x - mx); };
    const f1 = fit(1880, 1975), f2 = fit(1976, lastY);
    byYear.forEach((d) => { d.a = d.x <= 1975 ? f1(d.x) : null; d.b = d.x >= 1976 ? f2(d.x) : null; });
    drawers.push(() => {
      const s = [{ key: 't', label: 'Annual mean', color: 'var(--color-fg-muted)', width: 1.5 }, { key: 'a', label: 'Trend 1880–1975 (+0.04 °C/decade)', color: S(1), width: 2.5, dash: true }, { key: 'b', label: `Trend 1976–${lastY} (+0.21 °C/decade)`, color: S(2), width: 2.5, dash: true }];
      legend(fig('f-temp'), s);
      lines(fig('f-temp').querySelector('.chart'), { data: byYear, series: s, zero: true, yFmt: signed(fmt1), valFmt: (v) => `${signed(fmt2)(v)} °C`, yLabel: '°C vs 1951–1980', marks: [{ x: 1941, label: '1940–42 El Niño' }, { x: 1976, label: '1976' }, { x: 1991, label: 'Pinatubo' }], height: 280 });
    });
    table(fig('f-temp'), ['Year', 'Annual mean (°C vs 1951–1980)'], byYear.filter((d) => d.x % 5 === 0 || d.x === lastY).map((d) => [d.x, signed(fmt2)(d.t)]));

    // 2a. CO2 by fuel
    const F = fuel.map((r) => ({ x: +r.year, coal: +r.coal, oil: +r.oil, gas: +r.gas, ind: +r.cement + +r.flaring + +r.other_industry, luc: +r.land_use_change }));
    const fk = ['coal', 'oil', 'gas', 'ind', 'luc'], fl = ['Coal', 'Oil', 'Gas', 'Cement, flaring and other industry', 'Land-use change (mainly deforestation)'];
    const fc = [S(2), S(1), S(3), S(5), S(6)];
    drawers.push(() => {
      legend(fig('f-fuel'), fk.map((k, i) => ({ label: fl[i], color: fc[i] })));
      stack(fig('f-fuel').querySelector('.chart'), { data: F, keys: fk, labels: fl, colors: fc, yFmt: d3.format('d'), valFmt: (v) => `${fmt1(v)} Gt`, yLabel: 'billion tonnes CO₂ per year', totalLabel: 'Total', marks: [{ x: 1976, label: '1976' }] });
    });
    table(fig('f-fuel'), ['Year', ...fl, 'Total'], F.filter((d) => d.x % 5 === 0 || d.x === F[F.length - 1].x).map((d) => [d.x, ...fk.map((k) => fmt1(d[k])), fmt1(d3.sum(fk, (k) => d[k]))]));

    // 2b. Forcing by greenhouse gas
    const E = erf.map((r) => ({ x: +r.year, CO2: +r.CO2, CH4: +r.CH4, N2O: +r.N2O, halogen: +r.halogen, O3: +r.O3, aerosol: +r.aerosol, solar: +r.solar, volcanic: +r.volcanic, anthro: +r.anthro, total: +r.total })).filter((d) => d.x >= 1900);
    drawers.push(() => {
      const s = [{ key: 'CO2', label: 'Carbon dioxide', color: S(1) }, { key: 'CH4', label: 'Methane', color: S(2) }, { key: 'halogen', label: 'CFCs, HCFCs and HFCs', color: S(7) }, { key: 'N2O', label: 'Nitrous oxide', color: S(3) }];
      legend(fig('f-ghg'), s);
      lines(fig('f-ghg').querySelector('.chart'), { data: E, series: s, zero: true, yFmt: fmt1, valFmt: (v) => `${fmt2(v)} W/m²`, yLabel: 'W/m² since 1750', marks: [{ x: 1976, label: '1976' }, { x: 1987, label: 'Montreal Protocol' }] });
    });
    table(fig('f-ghg'), ['Year', 'CO₂', 'Methane', 'Halogenated', 'N₂O'], E.filter((d) => d.x % 10 === 0 || d.x === 2024).map((d) => [d.x, fmt2(d.CO2), fmt2(d.CH4), fmt2(d.halogen), fmt2(d.N2O)]));

    // 3. SO2 by sector
    const sk = Object.keys(so2[0]).filter((k) => k !== 'year');
    const SO = so2.map((r) => { const o = { x: +r.year }; sk.forEach((k) => { o[k] = +r[k]; }); return o; });
    const sc = [S(1), S(2), S(3), S(4), S(5), S(6), S(7)];
    drawers.push(() => {
      legend(fig('f-so2'), sk.map((k, i) => ({ label: k, color: sc[i] })));
      stack(fig('f-so2').querySelector('.chart'), { data: SO, keys: sk, labels: sk, colors: sc, yFmt: d3.format('d'), valFmt: (v) => `${fmt1(v)} Mt`, yLabel: 'million tonnes SO₂ per year', totalLabel: 'Total', marks: [{ x: 1979, label: 'Global peak 1979' }, { x: 2020, label: 'Ship-fuel rule' }] });
    });
    table(fig('f-so2'), ['Year', ...sk, 'Total'], SO.filter((d) => d.x % 5 === 0 || d.x >= 2019).map((d) => [d.x, ...sk.map((k) => fmt1(d[k])), fmt1(d3.sum(sk, (k) => d[k]))]));

    // 5. Natural vs human forcing
    const N = E.filter((d) => d.x >= 1950);
    drawers.push(() => {
      const s = [{ key: 'anthro', label: 'All human causes', color: S(8) }, { key: 'solar', label: 'Sun', color: S(4), width: 2 }, { key: 'volcanic', label: 'Volcanoes', color: S(1), width: 2 }];
      legend(fig('f-natural'), s);
      lines(fig('f-natural').querySelector('.chart'), { data: N, series: s, zero: true, yFmt: fmt1, valFmt: (v) => `${signed(fmt2)(v)} W/m²`, yLabel: 'W/m² since 1750', marks: [{ x: 1963, label: 'Agung' }, { x: 1982, label: 'El Chichón' }, { x: 1991, label: 'Pinatubo' }] });
    });
    table(fig('f-natural'), ['Year', 'Human', 'Sun', 'Volcanoes'], N.filter((d) => d.x % 5 === 0 || d.x === 2024 || d.x === 1991 || d.x === 1992).map((d) => [d.x, signed(fmt2)(d.anthro), signed(fmt2)(d.solar), signed(fmt2)(d.volcanic)]));

    // 9.2 Push since the 1970s (decade means)
    const R = erf.map((r) => { const o = { x: +r.year }; Object.keys(r).forEach((k) => { if (k !== 'year') o[k] = +r[k]; }); return o; });
    const dm = (k, a, b) => d3.mean(R.filter((d) => d.x >= a && d.x <= b), (d) => d[k]);
    const agents = [['CO2', 'Carbon dioxide'], ['aerosol', 'Less aerosol haze (cleaner air)'], ['halogen', 'CFCs, HCFCs and HFCs'], ['CH4', 'Methane'], ['O3', 'Low-level ozone (smog)'], ['N2O', 'Nitrous oxide'], ['contrails', 'Aircraft contrails'], ['H2O_stratospheric', 'Stratospheric water vapour'], ['BC_on_snow', 'Soot on snow'], ['land_use', 'Land-use albedo'], ['volcanic', 'Volcanoes (natural)'], ['solar', 'Sun (natural)']];
    const push = agents.map(([k, l]) => ({ k, l, v: dm(k, 2015, 2024) - dm(k, 1971, 1980) }));
    const human = dm('anthro', 2015, 2024) - dm('anthro', 1971, 1980);
    drawers.push(() => {
      hbars(fig('f-push').querySelector('.chart'), { rows: push.map((p) => ({ label: p.l, parts: [{ v: p.v, color: p.v >= 0 ? S(8) : S(1), label: p.v >= 0 ? 'Warming push' : 'Cooling push' }], note: p.k === 'volcanic' || p.k === 'solar' ? 'Natural factor' : `${fmt1((p.v / human) * 100)}% of the human total` })), valFmt: (v) => `${signed(fmt2)(v)} W/m²`, tickFmt: signed(fmt1), endLabel: (r, t) => signed(fmt2)(t), labelWidth: 200 });
    });
    table(fig('f-push'), ['Agent', '1971–80 mean', '2015–24 mean', 'Change (W/m²)', 'Share of human change'], push.map((p) => [p.l, signed(fmt3)(dm(p.k, 1971, 1980)), signed(fmt3)(dm(p.k, 2015, 2024)), signed(fmt3)(p.v), p.k === 'volcanic' || p.k === 'solar' ? '—' : `${fmt1((p.v / human) * 100)}%`]));

    // 9.3 GHG warming over time (Jones et al.)
    const G = ghgw.map((r) => ({ x: +r.year, co2: num(r.co2), ch4: num(r.ch4), n2o: num(r.n2o) }));
    drawers.push(() => {
      const keys = ['co2', 'ch4', 'n2o'], labels = ['Carbon dioxide', 'Methane', 'Nitrous oxide'], colors = [S(1), S(2), S(3)];
      legend(fig('f-ghgwarm'), keys.map((k, i) => ({ label: labels[i], color: colors[i] })));
      stack(fig('f-ghgwarm').querySelector('.chart'), { data: G, keys, labels, colors, yFmt: fmt1, valFmt: (v) => `${fmt2(v)} °C`, yLabel: '°C of warming since 1850', totalLabel: 'Three gases together', marks: [{ x: 1976, label: '1976' }] });
    });
    table(fig('f-ghgwarm'), ['Year', 'CO₂', 'Methane', 'N₂O', 'Total'], G.filter((d) => d.x % 10 === 0 || d.x === 1976 || d.x === 2024).map((d) => [d.x, fmt3(d.co2), fmt3(d.ch4), fmt3(d.n2o), fmt3(d.co2 + d.ch4 + d.n2o)]));

    // 9.4a CO2 by source, cumulative 1976–2024
    const cum = (k) => d3.sum(fuel.filter((r) => +r.year >= 1976 && +r.year <= 2024), (r) => +r[k]);
    const src = [['coal', 'Coal'], ['oil', 'Oil'], ['land_use_change', 'Land-use change'], ['gas', 'Natural gas'], ['cement', 'Cement'], ['flaring', 'Gas flaring'], ['other_industry', 'Other industry']].map(([k, l]) => ({ l, v: cum(k) }));
    const tot = d3.sum(src, (s) => s.v);
    drawers.push(() => {
      hbars(fig('f-co2src').querySelector('.chart'), { rows: src.map((s) => ({ label: s.l, parts: [{ v: s.v, color: S(1), label: 'CO₂ emitted 1976–2024' }], note: `${fmt1((s.v / tot) * 100)}% of all CO₂ since 1976` })), valFmt: (v) => `${d3.format(',.0f')(v)} Gt`, tickFmt: d3.format(',d'), endLabel: (r, t) => `${d3.format(',.0f')(t)} Gt · ${d3.format('.0f')((t / tot) * 100)}%`, endW: 86, labelWidth: 170 });
    });
    table(fig('f-co2src'), ['Source', 'CO₂ 1976–2024 (Gt)', 'Share'], src.map((s) => [s.l, d3.format(',.1f')(s.v), `${fmt1((s.v / tot) * 100)}%`]).concat([['Total', d3.format(',.1f')(tot), '100%']]));

    // 9.4b Methane by source
    const mk = Object.keys(ch4[0]).filter((k) => k !== 'year');
    const M = ch4.map((r) => { const o = { x: +r.year }; mk.forEach((k) => { o[k] = +r[k]; }); return o; });
    const mc = [S(1), S(2), S(3), S(4), S(5), S(6)];
    drawers.push(() => {
      legend(fig('f-ch4'), mk.map((k, i) => ({ label: k, color: mc[i] })));
      stack(fig('f-ch4').querySelector('.chart'), { data: M, keys: mk, labels: mk, colors: mc, yFmt: d3.format('d'), valFmt: (v) => `${fmt1(v)} Mt`, yLabel: 'million tonnes methane per year', totalLabel: 'Total (human sources)', marks: [{ x: 1976, label: '1976' }] });
    });
    table(fig('f-ch4'), ['Year', ...mk, 'Total'], M.filter((d) => d.x % 5 === 0 || d.x === 1976 || d.x === M[M.length - 1].x).map((d) => [d.x, ...mk.map((k) => fmt1(d[k])), fmt1(d3.sum(mk, (k) => d[k]))]));

    // 9.5 Countries
    const C = ctry.map((r) => ({ c: r.country, co2: +r.dT_co2, ch4: +r.dT_ch4, n2o: +r.dT_n2o, ghg: +r.dT_ghg, fos: +r.fossil_co2_gt_1976_2024, luc: +r.landuse_co2_gt_1976_2024, pc: num(r.co2_per_capita_t_2024), pop: +r.population_m_2024 }));
    const world = d3.sum(C, (d) => d.ghg);
    drawers.push(() => {
      legend(fig('f-country'), [{ label: 'Carbon dioxide', color: S(1) }, { label: 'Methane', color: S(2) }, { label: 'Nitrous oxide', color: S(3) }]);
      hbars(fig('f-country').querySelector('.chart'), { rows: C.map((d) => ({ label: d.c.replace(/^All other countries \((\d+)\)$/, '$1 other countries'), total: d.ghg, parts: [{ v: d.co2, color: S(1), label: 'Carbon dioxide' }, { v: d.ch4, color: S(2), label: 'Methane' }, { v: d.n2o, color: S(3), label: 'Nitrous oxide' }], note: `${fmt1((d.ghg / world) * 100)}% of the ${fmt2(world)} °C · ${d3.format(',.0f')(d.pop)} million people${d.pc != null ? ` · ${fmt1(d.pc)} t CO₂ per person in 2024` : ''}` })), valFmt: (v) => `${signed(fmt3)(v)} °C`, tickFmt: fmt2, endLabel: (r, t) => `${fmt1((t / world) * 100)}%`, endW: 46, labelWidth: 150 });
    });
    table(fig('f-country'), ['Country', 'Warming added 1976–2024 (°C)', 'Share', 'of which CO₂', 'Methane', 'N₂O', 'Fossil CO₂ 1976–2024 (Gt)', 'Land-use CO₂ (Gt)', 't CO₂ per person 2024', 'Population 2024 (m)'],
      C.map((d) => [d.c, fmt3(d.ghg), `${fmt1((d.ghg / world) * 100)}%`, fmt3(d.co2), fmt3(d.ch4), fmt3(d.n2o), fmt1(d.fos), fmt1(d.luc), d.pc != null ? fmt1(d.pc) : '—', d3.format(',')(d.pop)]));

    redraw();
    let t; addEventListener('resize', () => { clearTimeout(t); t = setTimeout(redraw, 150); });
  }).catch((e) => { console.error(e); document.querySelectorAll('.fig .chart').forEach((c) => { c.textContent = 'Chart data could not be loaded.'; }); });
})();
