/* HUD saf mantık testleri (node, bağımlılıksız). */
'use strict';
const assert = require('assert');
const ZenHud = require('../hud/hud.js');

const Durum = ZenHud.Durum;

function test_durum_makinesi() {
  const d = new Durum();
  assert.strictEqual(d.aktif, 'bosta');

  d.uygula({ type: 'answer', content: 'Merhaba' });
  assert.strictEqual(d.aktif, 'konusuyor');

  d.uygula({ type: 'faz', faz: 'rapor', durum: 'dusunuyor', detay: 'kaynak taraması' });
  assert.strictEqual(d.aktif, 'arastiriyor');

  d.uygula({ type: 'faz', faz: 'plan', durum: 'dusunuyor', detay: 'akıl yürütme' });
  assert.strictEqual(d.aktif, 'dusunuyor');

  d.uygula({ type: 'faz', faz: 'yanit', durum: 'konusuyor', detay: '' });
  assert.strictEqual(d.aktif, 'konusuyor');

  d.uygula({ type: 'faz', faz: 'hata', detay: 'mega beyin yok' });
  assert.strictEqual(d.aktif, 'hata');

  d.sus();
  assert.strictEqual(d.aktif, 'bosta');

  // yerel ses olayları
  d.uygula({ yerel: 'pta-bas' });
  assert.strictEqual(d.aktif, 'dinliyor');
  d.uygula({ yerel: 'pta-son' });
  assert.strictEqual(d.aktif, 'dusunuyor');
  d.sus();
}

function test_sse_ayikla() {
  const ham = ['data: {"choices":[{"delta":{"type":"faz","faz":"yanit"}}]}',
               '', 'data: {"choices":[{"delta":{"type":"answer","content":"Merhaba "}}]}',
               '', 'data: [DONE]', ''].join('\n');
  const olaylar = ZenHud.durum_ayikla(ham);
  assert.strictEqual(olaylar.length, 2);
  assert.strictEqual(olaylar[0].choices[0].delta.type, 'faz');
  assert.strictEqual(olaylar[1].choices[0].delta.content, 'Merhaba ');
}

function test_sse_bos_ve_bozuk() {
  assert.deepStrictEqual(ZenHud.durum_ayikla(''), []);
  assert.deepStrictEqual(ZenHud.durum_ayikla('data: [DONE]'), []);
  assert.strictEqual(ZenHud.durum_ayikla('data: {bozuk').length, 0);
  assert.strictEqual(ZenHud.durum_ayikla('satır: x\nidle yazısı').length, 0);
}

test_durum_makinesi();
test_sse_ayikla();
test_sse_bos_ve_bozuk();
console.log('test_hud.js: 3/3 OK');