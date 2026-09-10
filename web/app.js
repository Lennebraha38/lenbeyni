const OPENROUTER = "https://openrouter.ai/api/v1/chat/completions";
const CORS_PROXY = "https://api.allorigins.win/raw?url=";

let mod = "tek";
let gecmis = [];
let sunucuModu = null; // null: bilinmiyor, true: /api/chat aktif (zero-config), false: degil

const $ = (id) => document.getElementById(id);

async function sunucuKontrol() {
  try {
    const r = await fetch(window.location.origin + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model: "ping", messages: [] }) });
    const j = await r.json();
    sunucuModu = true;
    return true;
  } catch (e) {
    sunucuModu = false;
    return false;
  }
}

function durum(goster, metin) {
  if (goster) { $("durum").classList.remove("hidden"); $("durum").textContent = metin; }
  else $("durum").classList.add("hidden");
}

function mesajEkle(role, icerik) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = icerik;
  $("chat").appendChild(div);
  $("chat").scrollTop = $("chat").scrollHeight;
  return div;
}

async function megaBeyin(mesajlar, model, key) {
  if (sunucuModu !== false) {
    try {
      const r = await fetch(window.location.origin + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
body: JSON.stringify({ model, messages: mesajlar, temperature: 0.7, max_tokens: 65536 }),
      });
      const j = await r.json();
      if (r.ok && j.content !== undefined) return j.content;
      if (j.error && String(j.error).includes("OPENROUTER_KEY")) { sunucuModu = false; }
    } catch (e) {
      if (sunucuModu === true) throw e;
      sunucuModu = false;
    }
  }
  if (!key) throw new Error("Sunucu rölesi çalışmıyor ve API key girilmedi.");
  const r = await fetch(OPENROUTER, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + key },
    body: JSON.stringify({ model, messages: mesajlar, temperature: 0.7, max_tokens: 4096 }),
  });
  if (!r.ok) {
    const hata = await r.text();
    throw new Error("HTTP " + r.status + ": " + hata.slice(0, 200));
  }
  return (await r.json()).choices[0].message.content;
}

async function siteCek(url) {
  try {
    const r = await fetch(CORS_PROXY + encodeURIComponent(url));
    const html = await r.text();
    const metin = html
      .replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<nav[\s\S]*?<\/nav>|<footer[\s\S]*?<\/footer>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/&[a-z]+;/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return metin.slice(0, 4000);
  } catch (e) {
    return "[Site okunamadi: " + e.message + "]";
  }
}

async function aramaNet(sorgu) {
  try {
    const r = await fetch(CORS_PROXY + encodeURIComponent("https://html.duckduckgo.com/html/?q=" + encodeURIComponent(sorgu)));
    const html = await r.text();
    const sonuclar = [...html.matchAll(/result__a[^>]*href="([^"]+)"[^>]*>(.*?)<\/a>/g)]
      .slice(0, 5)
      .map((m) => {
        let link = m[1];
        const uddg = link.match(/uddg=([^&]+)/);
        if (uddg) link = decodeURIComponent(uddg[1]);
        const baslik = m[2].replace(/<[^>]+>/g, "").trim();
        return baslik + " | " + link;
      });
    return sonuclar.join("\n") || "[Arama sonucu yok]";
  } catch (e) {
    return "[Arama hatasi: " + e.message + "]";
  }
}

function sorudakiUrl(soru) {
  const m = soru.match(/\b(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,6})+(?:\/[^\s]*)?/);
  return m ? m[0] : null;
}

async function ajanMod(mesajlar, tools) {
  const son = mesajlar[mesajlar.length - 1].content;
  let baglam = "";
  const url = sorudakiUrl(son);
  if (url && tools.site) {
    const adres = url.startsWith("http") ? url : "https://" + url;
    durum(true, "Site okunuyor: " + adres + "...");
    baglam += "\nSITE: " + await siteCek(adres);
  } else if (tools.arama) {
    const q = son.replace(/\b(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,6})+(?:\/[^\s]*)?/g, "").trim();
    if (q && q.split(" ").length >= 3) {
      durum(true, "Web aranıyor: " + q.slice(0, 60) + "...");
      baglam += "\nARAMA: " + await aramaNet(q);
    }
  }
  if (baglam) {
    mesajlar.push({ role: "system", content: "Web araç sonuçları (gerçek veri):" + baglam + "\nKullanıcının sorusuna bu verilerle Türkçe cevap ver." });
  }
}

async function tekMod(soru, key, model) {
  const kullaniciIc = soru;
  mesajEkle("user", kullaniciIc);
  const mesajlar = [
    { role: "system", content: "Sen LenBeyni'sin. Türkçe, net ve detaylı cevap ver. Kullanıcıdan gelen site/link varsa siteyi incele, sonra cevapla." },
    ...gecmis,
    { role: "user", content: kullaniciIc },
  ];
  await ajanMod(mesajlar, { arama: $("toolArama").checked, site: $("toolSite").checked });
  durum(true, model + " düşünüyor...");
  const div = mesajEkle("ai", "…");
  try {
    const yanit = await megaBeyin(mesajlar, model, key);
    div.textContent = yanit;
    gecmis.push({ role: "user", content: kullaniciIc }, { role: "assistant", content: yanit });
    gecmis = gecmis.slice(-20);
  } catch (e) {
    div.className = "msg hata";
    div.textContent = "Hata: " + e.message;
  }
  durum(false);
  $("chat").scrollTop = $("chat").scrollHeight;
}

async function meclisMod(soru, key) {
  const secilen = [...document.querySelectorAll('#meclisModel input:checked')].map((i) => i.value);
  if (secilen.length < 2) { alert("Meclis için en az 2 model seç."); return; }
  mesajEkle("user", soru);
  const wrap = document.createElement("div");
  wrap.className = "meclis-wrap";
  wrap.innerHTML = '<h3 style="color:#34d399;margin-bottom:8px;font-size:15px;">⚖ AI Meclisi</h3><div class="meclis-grid"></div>';
  $("chat").appendChild(wrap);
  const grid = wrap.querySelector(".meclis-grid");

  const sözler = await Promise.all(secilen.map(async (model) => {
    const kart = document.createElement("div");
    kart.className = "meclis-card";
    kart.innerHTML = `<h4>${model}</h4><div class="content">…</div>`;
    grid.appendChild(kart);
    const icerik = kart.querySelector(".content");
    try {
      const yanit = await megaBeyin([
        { role: "system", content: "Sen LenBeyni meclisinin bir üyesisin. Türkçe, net cevap ver." },
        { role: "user", content: soru },
      ], model, key);
      icerik.textContent = yanit;
      return { model, yanit };
    } catch (e) {
      icerik.textContent = "Hata: " + e.message;
      return { model, yanit: null };
    }
  }));

  const gecerliler = sözler.filter((s) => s.yanit);
  if (gecerliler.length >= 2) {
    durum(true, "Meclis en iyi cevabı seçiyor (hakim model oyluyor)...");
    const liste = sözler.map((s, i) => `--- MOD${i + 1} (${s.model}) ---\n${s.yanit}`).join("\n\n");
    try {
      const gerekce = await megaBeyin([
        { role: "system", content: "Sen AI meclisinin hakimisin. MOD1..MODN cevaplarını oku, en iyisini seç ve 1-2 cümle gerekçe ver. Format: 'MOD3 kazandı: <gerekçe>'" },
        { role: "user", content: "Soru: " + soru + "\n\n" + liste },
      ], "nvidia/nemotron-3-ultra-550b-a55b:free", key);
      const m = gerekce.match(/MOD(\d+)/);
      const kazananIdx = m ? parseInt(m[1]) - 1 : 0;
      if (kazananIdx >= 0 && kazananIdx < sözler.length) {
        const kart = grid.querySelectorAll(".meclis-card")[kazananIdx];
        const el = document.createElement("div");
        el.className = "kazanan";
        el.textContent = "🏆 " + gerekce.trim().slice(0, 400);
        kart.appendChild(el);
        kart.style.borderColor = "#34d399";
      }
    } catch (e) {
      mesajEkle("system", "Meclis kararı alınamadı: " + e.message);
    }
    durum(false);
  }
  gecmis.push({ role: "user", content: soru });
  gecmis = gecmis.slice(-20);
}

async function gonder() {
  const soru = $("giris").value.trim();
  const key = $("apiKey").value.trim();
  if (!soru) return;
  if (!key) {
    if (sunucuModu === null) await sunucuKontrol();
    if (sunucuModu === false) { alert("Sunucu rölesi yok ve API key girilmedi."); return; }
  }
  $("giris").value = "";
  $("btnGonder").disabled = true;
  try {
    if (mod === "tek") await tekMod(soru, key, $("modelSec").value);
    else if (mod === "meclis") await meclisMod(soru, key);
    else if (mod === "ajan") await tekMod(soru, key, $("modelSec").value);
  } finally {
    $("btnGonder").disabled = false;
    $("giris").focus();
  }
}

document.querySelectorAll(".mode-btn").forEach((b) => {
  b.addEventListener("click", () => {
    mod = b.dataset.mode;
    document.querySelectorAll(".mode-btn").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    $("tekModel").classList.toggle("hidden", mod !== "tek");
    $("meclisModel").classList.toggle("hidden", mod !== "meclis");
  });
});

$("btnGonder").addEventListener("click", gonder);
$("giris").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); gonder(); } });
$("btnTemizle").addEventListener("click", () => { $("chat").innerHTML = ""; gecmis = []; });
$("btnKopyala").addEventListener("click", () => {
  const son = $("chat").querySelector(".msg.ai:last-child, .kopya");
  if (!son) return;
  navigator.clipboard.writeText(son.textContent.replace(/^…/, "").trim());
});

try {
  (async () => {
    if (await sunucuKontrol()) {
      // zero-config: key kutusu gizle, rozet göster
      const kutu = $("keyBox");
      if (kutu) {
        kutu.classList.add("hidden");
        const rozet = document.createElement("div");
        rozet.className = "zero-rozet";
        rozet.textContent = "⚡ Hazır — key gerekmez";
        kutu.insertAdjacentElement("beforebegin", rozet);
      }
    }
  })();
  $("apiKey").value = localStorage.getItem("lb_key") || "";
  $("apiKey").addEventListener("input", () => localStorage.setItem("lb_key", $("apiKey").value));
} catch (e) {}