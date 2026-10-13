// Renders After Dark frames with headless Chromium and encodes them with ffmpeg.
// usage: node render.mjs <out_dir> <width> <height> <fps> [text=1|0] [frames|still:t]
import { chromium } from 'playwright';
import { readFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const [out, w, h, fps, text = '1', mode = 'frames'] = process.argv.slice(2);
const threePath = process.env.THREE_JS;
mkdirSync(out, { recursive: true });

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +w / 2, height: +h / 2 }, deviceScaleFactor: 2 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[error]', e.message));
if (threePath) await page.route('**/three.min.js', r => r.fulfill({ body: readFileSync(threePath), contentType: 'text/javascript' }));
await page.goto('file://' + resolve(here, 'index.html') + `?capture=1&text=${text}`);
await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
await page.evaluate(() => document.fonts.ready);

const shoot = async (t, file) => { await page.evaluate(t => window.renderAt(t), t); await page.screenshot({ path: file, type: 'png' }); };
if (mode.startsWith('still:')) {
  for (const t of mode.slice(6).split(',')) await shoot(+t, `${out}/still_${t}.png`);
} else {
  const loop = await page.evaluate(() => window.LOOP);
  const n = Math.round(loop * fps);
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await shoot(i / fps, `${out}/f_${String(i).padStart(4, '0')}.png`);
    if (i % 10 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000 / (i + 1)).toFixed(2)}s/frame`);
  }
}
await browser.close();
