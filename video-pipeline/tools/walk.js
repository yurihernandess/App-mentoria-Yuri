const { chromium } = require('playwright');
const roots = JSON.parse(process.argv[2]);
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const out = {};
  async function walk(id, path, d, acc) {
    await p.goto(`https://drive.google.com/embeddedfolderview?id=${id}#list`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(1000);
    const items = await p.$$eval('a', as => as.map(a => [a.innerText.trim().split('\n')[0], a.href]));
    for (const [n, h] of items) {
      const f = h.match(/folders\/([^/?#]+)/), fi = h.match(/file\/d\/([^/]+)/);
      if (f && d > 0 && !/Lan[cç]amento|Apresenta|Materiais|Posts|Stories|E-MAIL|WEB/i.test(n)) await walk(f[1], path + '/' + n, d - 1, acc);
      else if (fi) acc.push([path + '/' + n, fi[1]]);
    }
  }
  for (const [k, id] of Object.entries(roots)) { out[k] = []; await walk(id, '', 4, out[k]); console.error(k, out[k].length); }
  console.log(JSON.stringify(out)); await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
