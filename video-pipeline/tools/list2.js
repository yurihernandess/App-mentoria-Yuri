const { chromium } = require('playwright');
const root = process.argv[2], depth = +process.argv[3] || 2;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  async function walk(id, pre, d) {
    await p.goto(`https://drive.google.com/embeddedfolderview?id=${id}#list`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(1200);
    const items = await p.$$eval('a', as => as.map(a => [a.innerText.trim().split('\n')[0], a.href]));
    for (const [n, h] of items) {
      const f = h.match(/folders\/([^/?#]+)/), fi = h.match(/file\/d\/([^/]+)/);
      if (f) { console.log(pre + '[D] ' + n + ' ' + f[1]); if (d > 1) await walk(f[1], pre + '  ', d - 1); }
      else if (fi) console.log(pre + n + ' ' + fi[1]);
    }
  }
  await walk(root, '', depth); await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
