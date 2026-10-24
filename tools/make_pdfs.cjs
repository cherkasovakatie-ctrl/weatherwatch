// Print every page listed in data/reports.csv to reports/pdf/<page>.pdf (A4, print layout, site navigation hidden).
// Run from the repo root with a local server on :8765:  node tools/make_pdfs.cjs
const fs = require('fs');
const { chromium } = require('playwright');
(async () => {
  const rows = fs.readFileSync('data/reports.csv', 'utf8').trim().split('\n').slice(1);
  const pages = [...new Set(rows.map((l) => l.split(',').pop().trim()).filter((p) => p.endsWith('.html')))];
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage();
  for (const f of pages) {
    await p.goto('http://localhost:8765/' + f, { waitUntil: 'networkidle' });
    await p.addStyleTag({ content: '.site-nav, .papers { display: none !important; } body { background: #fff !important; } a { text-decoration: none; }' });
    await p.emulateMedia({ media: 'print', colorScheme: 'light' });
    await p.waitForTimeout(800);
    const out = 'reports/pdf/' + f.replace('.html', '.pdf');
    await p.pdf({ path: out, format: 'A4', printBackground: true, margin: { top: '14mm', bottom: '14mm', left: '12mm', right: '12mm' },
      displayHeaderFooter: true, headerTemplate: '<span></span>',
      footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#666">Global Weather Watch · <span class="pageNumber"></span> / <span class="totalPages"></span></div>' });
    console.log(out, fs.statSync(out).size);
  }
  await b.close();
})();
