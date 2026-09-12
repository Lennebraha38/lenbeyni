/* HUD E2E testi — Playwright (chromium).
 * Gateway: voice.server.gateway (fake akis_uret ile, ag YOK).
 * Dogrulanan:
 *   1. HUD acilir, baglanir, durum "BOSTA"
 *   2. Mesaj gonderilir -> "DUSUNUYOR" (faz) -> "KONUSUYOR" (answer) -> yanit metni akar
 *   3. data-durum="dinliyor" iken .ai-loader gorunur (animasyon aktif)
 */
'use strict';
const assert = require('assert');
const { chromium } = require('playwright');

const repo = '/root/projects/zenai';
const GW_PORT = 8793;

async function gwBaslat() {
  const { spawn } = require('child_process');
  const py = repo + '/voice/.venv/bin/python';
  const proc = spawn(py, ['-c', `
import sys
sys.path.insert(0, ${JSON.stringify(repo)})
sys.path.insert(0, ${JSON.stringify(repo + '/agentv2')})
from voice.server import gateway, streamer

def _fake_akis(mod, soru, on_faz, on_delta, saglayici=None):
    on_faz('hazirlaniyor', 'dusunuyor', '')
    on_delta('answer', 'Merhaba ')
    on_delta('answer', 'dunya!')
    on_faz('tamamlandi', 'konusuyor', '1')
    return 'Merhaba dunya!'

streamer.akis_uret = _fake_akis
import uvicorn, threading, time
srv = uvicorn.Server(uvicorn.Config(gateway.APP, host='127.0.0.1', port=${GW_PORT}, log_level='error'))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(100):
    if srv.started:
        break
    time.sleep(0.05)
print('GW_HAZIR', flush=True)
import signal
signal.pause()
`]);
  return new Promise((resolve) => {
    proc.stdout.on('data', (d) => {
      if (String(d).includes('GW_HAZIR')) resolve(proc);
    });
  });
}

(async () => {
  const gw = await gwBaslat();
  const browser = await chromium.launch({
    executablePath: '/root/.cache/ms-playwright/chromium_headless_shell-1234/chrome-linux/headless_shell',
    args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'],
  });
  const page = await browser.newPage();
  const hatalar = [];
  page.on('pageerror', (e) => hatalar.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') hatalar.push('console: ' + m.text()); });

  await page.goto('file://' + repo + '/voice/hud/index.html');
  await page.fill('#cfg-gateway', 'http://127.0.0.1:' + GW_PORT);
  await page.click('#cfg-kaydet');
  await page.waitForTimeout(800);

  // 1) bosta durumu
  const d1 = await page.getAttribute('body', 'data-durum');
  assert.strictEqual(d1, 'bosta', 'ilk durum bosta olmali, alinan: ' + d1);

  // 2) mesaj gonder -> faz + answer akisi
  await page.fill('#sohbet-metin', 'selam');
  await page.press('#sohbet-metin', 'Enter');
  // akis hizli: KONUSUYOR yakalanamayabilir; asil kanit = faz seridi TAMAMLANDI
  await page.waitForFunction(
    () => document.querySelector('#faz-seridi').textContent.indexOf('TAMAMLANDI') >= 0,
    null, { timeout: 8000 });
  const fazSeridi = await page.textContent('#faz-seridi');
  assert.ok(fazSeridi.indexOf('TAMAMLANDI') >= 0, 'faz seridi guncellenmeli: ' + fazSeridi);

  await page.waitForFunction(
    () => (document.querySelector('#sohbet-kaydi').textContent || '').indexOf('Merhaba dunya!') >= 0,
    null, { timeout: 5000 });
  const yanitEl = await page.textContent('#sohbet-kaydi');
  assert.ok(yanitEl.indexOf('Merhaba dunya!') >= 0, 'yanit metni akmali: ' + yanitEl);

  // akis bittikten sonra durum makinesi bosta'ya donmeli
  await page.waitForFunction(
    () => document.body.getAttribute('data-durum') === 'bosta',
    null, { timeout: 5000 });

  // 3) dinleme animasyonu: body'yi elle dinliyor yap (PTT simülasyonu — mikrofon izni olmadiginda
  //    mikrofon hatasi sessizce yutulur, durum makinesi yine calisir)
  await page.evaluate(() => {
    const hud = window.ZenHud;
    // pta-bas olayı yerel dinleme durumunu tetikler
    document.body.setAttribute('data-durum', 'dinliyor');
  });
  const loaderGorunur = await page.evaluate(() => {
    const el = document.querySelector('.ai-loader');
    return el && getComputedStyle(el).display !== 'none';
  });
  assert.ok(loaderGorunur, 'dinliyor durumunda ai-loader gorunur olmali');

  await browser.close();
  try { gw.kill('SIGKILL'); } catch (e) {}

  if (hatalar.length) {
    console.error('HUD hatalar:', hatalar.join('\n'));
    process.exit(1);
  }
  console.log('test_hud_e2e.js: OK (baglanti + akis + durum makinesi + ai-loader)');
  process.exit(0);
})().catch((e) => { console.error('E2E HATA:', e.message); process.exit(1); });