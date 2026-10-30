/* Global Weather Watch — static data runtime for GitHub Pages.
   Loads data/manifest.json and the CSV/JSON files it lists, then provides the small
   `dash` API the page code expects: data(id), calc(id, def), colors, onData(cb), setLink(page). */
window.dash = (() => {
  const store = {}, calcs = {}, cache = {}, cbs = [], early = [];
  let loaded = false;
  const colors = ['#2b6cb0', '#7a8a99', '#c2410c', '#0f766e', '#7c3aed', '#b45309'];
  const darkColors = ['#63a4ff', '#9aa8b5', '#fb923c', '#2dd4bf', '#a78bfa', '#fbbf24'];
  const isDark = () => document.documentElement.dataset.theme === 'dark' || (document.documentElement.dataset.theme !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
  function data(id) {
    if (store[id]) return store[id];
    if (calcs[id]) {
      if (cache[id]) return cache[id];
      const ins = calcs[id].inputs.map(data);
      const bad = ins.find((d) => d.status !== 'ok');
      if (bad) return { status: bad.status, data: null };
      try { cache[id] = { status: 'ok', data: calcs[id].fn(...ins.map((d) => d.data)) }; }
      catch (e) { console.error('calc', id, e); cache[id] = { status: 'error', data: null }; }
      return cache[id];
    }
    return { status: loaded ? 'missing' : 'loading', data: null };
  }
  const calc = (id, def) => { calcs[id] = def; };
  const onData = (cb) => { cbs.push(cb); if (loaded) cb(); };
  // onEarly(ids, cb): fetch these datasets first and call cb as soon as they are in, before the rest of the manifest has loaded.
  // Used for the headline block, which needs 4 small files and should not wait for all of them. cb must cope with other data still loading.
  const onEarly = (ids, cb) => { early.push({ ids, cb }); };
  const setLink = (p) => { try { history.replaceState(null, '', `#${p}`); } catch (e) { /* ignore */ } };
  const fmt = (field, v) => {
    if (v == null || v === '') return '—';
    const n = +v;
    if (Number.isNaN(n) || typeof v === 'string' && /[-:]/.test(v.slice(1)) && /^\d{4}-/.test(v)) return String(v);
    if (/_chg$/.test(field)) return (n > 0 ? '+' : n < 0 ? '−' : '±') + Math.abs(n).toFixed(2);
    return String(v);
  };
  function bind() {
    document.querySelectorAll('table[data-source]').forEach((t) => {
      const src = t.dataset.source; if (src.includes(' ')) return;
      const d = data(src); if (d.status !== 'ok') return;
      const fields = [...t.querySelectorAll('thead th')].map((th) => th.dataset.field);
      if (!fields.length || fields.some((f) => !f)) return;
      const tb = t.querySelector('tbody'); if (!tb) return;
      tb.replaceChildren();
      d.data.forEach((r) => {
        const tr = document.createElement('tr');
        fields.forEach((f) => { const td = document.createElement('td'); td.textContent = r[f] == null ? '' : String(r[f]); tr.append(td); });
        tb.append(tr);
      });
    });
    document.querySelectorAll('[data-source][data-field]:not(table):not(th)').forEach((el) => {
      const d = data(el.dataset.source); if (d.status !== 'ok' || !d.data.length) return;
      let row = d.data[+(el.dataset.row || 0)];
      if (el.dataset.where) { const [k, v] = el.dataset.where.split('='); row = d.data.find((r) => String(r[k]) === v); }
      if (!row) return;
      el.textContent = fmt(el.dataset.field, row[el.dataset.field]);
      el.classList.remove('dash-skeleton');
    });
  }
  async function load() {
    const m = await (await fetch('data/manifest.json', { cache: 'no-cache' })).json();
    document.querySelectorAll('[data-asof]').forEach((e) => { e.textContent = m.updated; });
    const loadOne = async (ds) => {
      if (store[ds.id]) return;
      try {
        const r = await fetch(`data/${ds.file}`, { cache: 'no-cache' });
        if (!r.ok) throw new Error(r.status);
        const txt = await r.text();
        store[ds.id] = { status: 'ok', data: ds.file.endsWith('.json') ? JSON.parse(txt) : d3.csvParse(txt).map((o) => { const x = {}; for (const k in o) x[k] = o[k]; return x; }) };
      } catch (e) { console.error('load', ds.id, e); store[ds.id] = { status: 'error', data: null }; }
    };
    for (const g of early) {
      const part = m.datasets.filter((d) => g.ids.includes(d.id));
      Promise.all(part.map(loadOne)).then(() => { try { g.cb(); } catch (e) { console.error(e); } });
    }
    await Promise.all(m.datasets.map(loadOne));
    loaded = true;
    bind();
    cbs.forEach((cb) => { try { cb(); } catch (e) { console.error(e); } });
  }
  const api = { data, calc, onData, onEarly, setLink, get colors() { return isDark() ? darkColors : colors; } };
  document.addEventListener('DOMContentLoaded', () => { load(); });
  let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => cbs.forEach((cb) => cb()), 200); });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => cbs.forEach((cb) => cb()));
  return api;
})();
