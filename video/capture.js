// Съемка шагов ролика в прототипе Ordo: node capture.js <id>
// Открывает собранный ../index.html как файл. Результат: build/<id>/16x9/sNN.jpg + meta.json
const puppeteer = require('/Users/kate/Documents/Проекты/frontpupirka/maker/tutorials/node_modules/puppeteer-core');
const fs = require('fs');
const V = require('./steps.js')[process.argv[2]];
const id = process.argv[2], F = { w: 1600, h: 900, dsf: 1.2 };
if (!V) { console.error('нет ролика', id); process.exit(1); }

(async () => {
  const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--hide-scrollbars', '--force-color-profile=srgb'] });
  const dir = `build/${id}/16x9`;
  fs.mkdirSync(dir, { recursive: true });
  const p = await b.newPage();
  p.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await p.setViewport({ width: F.w, height: F.h, deviceScaleFactor: F.dsf });
  await p.goto('file://' + require('path').resolve(__dirname, '../index.html'), { waitUntil: 'networkidle0', timeout: 120000 });
  await p.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 800));
  await p.addStyleTag({ content: '.toast{display:none!important}' });
  await p.evaluate(() => {
    window.$ = s => [...document.querySelectorAll(s)].find(e => e.offsetParent || e.getClientRects().length) || null;
    window.$$ = s => [...document.querySelectorAll(s)];
  });
  const meta = { id, fmt: '16x9', w: Math.round(F.w * F.dsf), h: Math.round(F.h * F.dsf), title: V.title, group: V.group, outro: V.outro || '', outroSub: V.outroSub || '', intro: V.intro, steps: [] };
  for (let i = 0; i < V.steps.length; i++) {
    const S = V.steps[i];
    if (S.do) { try { await p.evaluate(S.do); } catch (e) { console.error('step', i, 'do:', e.message); } }
    await new Promise(r => setTimeout(r, S.wait || 700));
    let rect = null;
    if (S.t) {
      rect = await p.evaluate(t => {
        let el; try { el = eval(t); } catch (e) { return null; }
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: r.left, y: r.top, w: r.width, h: Math.min(r.height, innerHeight - r.top - 12) };
      }, S.t);
      if (!rect) console.error('step', i, 'цель не найдена:', S.t);
    }
    const file = `s${String(i).padStart(2, '0')}.jpg`;
    await p.screenshot({ path: `${dir}/${file}`, type: 'jpeg', quality: 90 });
    const k = F.dsf;
    meta.steps.push({ img: file, say: S.say, label: S.label || '', click: !!S.click, rect: rect && { x: rect.x * k, y: rect.y * k, w: rect.w * k, h: rect.h * k } });
    console.log('шаг', i, rect ? 'ok' : '—');
  }
  fs.writeFileSync(`${dir}/meta.json`, JSON.stringify(meta, null, 1));
  await b.close();
})();
