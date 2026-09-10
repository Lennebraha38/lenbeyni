/* ═══════════════════════════════════════════════════════════
   LenBeyni Web — Gemini/Claude seviyesi arayüz
   Özellikler: konu→model yönlendirme, Akıl Motoru, Skills ekleme,
   MCP bağlama (JSON-RPC over HTTP rölesi), AI Meclisi, streaming,
   web arama + site okuma, sohbet geçmişi, konuşma listesi.
   ═══════════════════════════════════════════════════════════ */
const OPENROUTER = "https://openrouter.ai/api/v1/chat/completions";
const CORS_YON = "https://api.allorigins.win/raw?url=";
const $ = (id) => document.getElementById(id);

// ── Durum ─────────────────────────────────────────────
let mod = "tek";
let gecmis = [];
let sunucuModu = null;
let aktifSohbet = null;
let kullanicilar = 1;
let mcpSk = new Map();        // key name -> (durdum + tools listesi)
let tekrarAkis = false;

// ── Konu → Model yönlendirme (agentv2/model_routing.py ile aynı) ──
const KONU_MODELLERI = {
  kod:        ["cohere/north-mini-code:free", 32768],
  matematik:  ["nvidia/nemotron-3-ultra-550b-a55b:free", 65536],
  mantik:     ["nvidia/nemotron-3-ultra-550b-a55b:free", 65536],
  bilim:      ["dots-studio/dots-3-note-preview:free", 48000],
  tarih:      ["dots-studio/dots-3-note-preview:free", 48000],
  dil:        ["dots-studio/dots-3-note-preview:free", 24000],
  yaratici:   ["dots-studio/dots-3-note-preview:free", 40000],
  kultur:     ["dots-studio/dots-3-note-preview:free", 24000],
  pratik:     ["dots-studio/dots-3-note-preview:free", 16000],
  teknoloji:  ["dots-studio/dots-3-note-preview:free", 48000],
};
const KONU_YONTEM = {
  matematik: "Problemi parçala, adım adım çöz (adımları yaz). Son adımda sonucu **büyük ve net** yaz.",
  mantik: "Önermeleri ayır, kısa zincirlerle çöz, her adımı gerekçelendir.",
  kod: "Önce ne istendiğini analiz et. Kodu sözdizimi + mantık uyumlu yaz. Çalıştırılabilir örnek ver.",
  dil: "Cümleyi parçala, kuralı hatırla, örnekle pekiştir.",
  bilim: "Temel prensibi hatırla, sonra detaylandır, sonra kısa örnek ver.",
  tarih: "Dönemi hatırla, neden-sonuç zincirini kur.",
  yaratici: "Temayı kur (kim/neden/hangi ortam), sonra ton ve kategori.",
  kultur: "Bilgiyi hatırla, pratik cevap al, örnekle aç.",
  pratik: "Kısa, net, uygulanabilir. Üç adımlı cevap.",
  teknoloji: "Önce temel prensip, sonra nasıl çalıştığı, sonra neden önemli.",
};

const KONU_ANAHTAR = [
  ["kod", /\b(?:python|kod|sql|regex|fonksiyon|siralama|algoritma|javascript|react)\b/i],
  ["matematik", /\b(?:matematik|toplam|pi\b|asal|olasilik|acilar|carpım|denklem|hesapla|kactir|kacar)\b|\d+\s*[\+\-×÷*\/]\s*\d/i],
  ["mantik", /\b(?:mantik|onerme|bilmece|sudoku|kuzgun|deduksiyon)\b/i],
  ["bilim", /\b(?:bilim|fizik|kimya|dna|kuantum|foton|bio)\b/i],
  ["tarih", /\b(?:tarih|osmanli|ronesans|savas|cumhuriyet|imper)\b/i],
  ["yaratici", /\b(?:hikaye|masal|logo|manifesto|hikaye yaz|resim|slogan)\b/i],
  ["kultur", /\b(?:kahve|istanbul|sehir|bayrak|maskot|kultur)\b/i],
  ["teknoloji", /\b(?:teknoloji|context|veritabani|blockchain|gpu|yapay zeka|urun)\b/i],
];

function konuBul(soru) {
  for (const [k, re] of KONU_ANAHTAR) if (re.test(soru)) return k;
  return "pratik";
}

// ── Depolama helpers ──────────────────────────────────
const depo = {
  get(k, d) { try { return JSON.parse(localStorage.getItem("lb_" + k) || "null") ?? d; } catch (e) { return d; } },
  set(k, v) { localStorage.setItem("lb_" + k, JSON.stringify(v)); },
};

// ── Skills ────────────────────────────────────────────
let skills = depo.get("skills", [
  { ad: "Araştırmacı", ikon: "🔎", icerik: "Sen metodik bir araştırmacısın. Konuyu alt başlıklara ayır, güncel bilgiye dayalı kanıtlar sun, kaynaklardan bahset. Bulguları özetiyle kapat." },
  { ad: "Kod Uzmanı", ikon: "👨‍💻", icerik: "Sen kıdemli bir yazılım mühendisisin. İstediğin kodu önce analiz et, çalışan bir örnek ver, hata risklerini kısaca belirt. Kod bloklarını ``` ile işaretle." },
  { ad: "Matematikçi", ikon: "📐", icerik: "Sen titiz bir matematikçisin. Her adımı göster, mantığını açıkla, sonucu net ver." },
  { ad: "Yaratıcı Yazar", ikon: "✍️", icerik: "Sen hikâye anlatıcısısın. Canlı betimleme, gerçekçi diyalog ve akıcı kurgu kur. Amaç okuyucuyu içine çekmek." },
]);
let aktifSkilller = depo.get("aktifSkilller", [0, 1]);

function skillKaydet() {
  depo.set("skills", skills);
  depo.set("aktifSkilller", aktifSkilller);
  skillListesiCiz();
}

function skillListesiCiz() {
  const kutu = $("skillListesi");
  if (!kutu) return;
  kutu.innerHTML = skills.length === 0
    ? '<p class="panel-aciklama">Henüz skill yok. "＋ Ekle" ile ilkini oluşturun.</p>'
    : "";
  skills.forEach((s, i) => {
    const open = aktifSkilller.includes(i);
    const div = document.createElement("div");
    div.className = "skill-kayit" + (open ? " open" : "");
    div.innerHTML = `<span class="skill-ikon">${s.ikon}</span><span class="skill-ad">${s.ad}</span>
      <span class="mcp-durum ${open ? "bagli" : "kapali"}" style="border:none;padding:0">${open ? "on" : "off"}</span>
      <button class="skill-kaldir" title="Kaldır">✕</button>`;
    div.querySelector(".skill-ad").onclick = () => {
      if (aktifSkilller.includes(i)) aktifSkilller = aktifSkilller.filter((x) => x !== i);
      else aktifSkilller.push(i);
      skillKaydet();
    };
    div.querySelector(".skill-kaldir").onclick = (e) => {
      e.stopPropagation();
      skills.splice(i, 1);
      aktifSkilller = aktifSkilller.map((x) => (x > i ? x - 1 : x)).filter((x, j) => x !== -1);
      skillKaydet();
    };
    kutu.appendChild(div);
  });
}

function skillIcerikleri() {
  return aktifSkilller
    .map((i) => skills[i])
    .filter(Boolean)
    .map((s) => `[SKILL:${s.ad}] ${s.icerik}`);
}

// ── MCP ───────────────────────────────────────────────
let mcpListesi = depo.get("mcpListesi", []);

async function mcpIstem(action, body) {
  // Sunucu rölesi /api/mcp varsa oradan, yoksa CORS köprüsü dene.
  const denemeler = [
    window.location.origin + "/api/mcp",
    null,
  ];
  const ilk = denemeler[0];
  try {
    const r = await fetch(ilk, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, ...body }) });
    if (r.ok) return await r.json();
    return { hata: "HTTP " + r.status };
  } catch (e) {
    return { hata: "Röle yok: " + e.message };
  }
}

async function mcpAletleriGetir(girdi) {
  const sonuc = await mcpIstem("tools", { uc: girdi.uc, proto: girdi.proto || "http" });
  if (sonuc.hata) return { durum: "hata", mesaj: sonuc.hata, aletler: [] };
  const aletler = (sonuc.tools || []).map((t) => ({
    ad: t.name, aciklama: t.description || "", parametre: (t.inputSchema && t.inputSchema.properties) || {},
  }));
  return { durum: "bagli", mesaj: aletler.length + " alet bağlandı", aletler };
}

async function mcpYenile(girdi) {
  const sonuc = await mcpAletleriGetir(girdi);
  girdi.durum = sonuc.durum;
  girdi.mesaj = sonuc.mesaj;
  girdi.aletler = sonuc.aletler;
  mcpKaydet();
  mcpListesiCiz();
}

function mcpKaydet() {
  depo.set("mcpListesi", mcpListesi);
  depo.set("mcpSk", Object.fromEntries([...mcpSk].map(([k, v]) => [k, v])));
  mcpListesiCiz();
}

function mcpListesiCiz() {
  const kutu = $("mcpListesi");
  if (!kutu) return;
  kutu.innerHTML = mcpListesi.length === 0
    ? '<p class="panel-aciklama">Henüz bağlantı yok. Veritabanı, dosya sistemi, haber kaynağı gibi alet körükleri (MCP) ekleyin.</p>'
    : "";
  mcpListesi.forEach((m) => {
    const durumBelirteci = m.durum || "kapali";
    const div = document.createElement("div");
    div.className = "mcp-kayit";
    div.innerHTML = `<span style="flex:1">
        <div style="font-size:14px;color:var(--yazi)">${m.ad}</div>
        <div style="font-size:11px;color:var(--yazi-3)">${m.uc || ""}</div>
      </span>
      <span class="mcp-durum ${durumBelirteci}" id="mcpDurum_${m.uid}">${durumBelirteci === "bagli" ? "● bağlı" : durumBelirteci === "hata" ? "! hata" : "○ kapalı"}</span>
      <button class="mcp-kaldir" title="Kaldır">✕</button>`;
    div.querySelector(".mcp-kaldir").onclick = () => {
      mcpListesi = mcpListesi.filter((x) => x.uid !== m.uid);
      mcpKaydet();
    };
    kutu.appendChild(div);
  });
}

function mcpAktif() {
  return mcpListesi.filter((m) => m.durum === "bagli" && (m.aletler && m.aletler.length));
}

function mcpAletDokumu() {
  const aktif = mcpAktif();
  if (!aktif.length) return "";
  return aktif.flatMap((m) => m.aletler.map((a) => {
    const prm = Object.keys(a.parametre || {}).map((k) => `${k} (${a.parametre[k].type || "?"}): ${a.parametre[k].description || ""}`).join("; ");
    return `- ${a.ad}${prm ? " → " + prm : ""}\n  ${a.aciklama || ""}`;
  })).join("\n");
}

async function mcpAletCagir(m, aletAdi, argumanlar) {
  const sonuc = await mcpIstem("call", { uc: m.uc, proto: m.proto || "http", alet: aletAdi, argumanlar });
  if (sonuc.hata) return "Hata: " + sonuc.hata;
  const c = (sonuc.content || []);
  const metn = c.map((x) => x.text || JSON.stringify(x) || "").join(" ");
  const yapili = sonuc.isError ? null : (c.find((x) => x.type === "text")?.text || metn);
  return yapili || "Alet boş döndü";
}

// ── Üst düzey yardımcılar ─────────────────────────────
function durum(goster, metin) {
  const el = $("durum");
  if (!el) return;
  if (goster) { el.classList.remove("hidden"); el.textContent = metin; }
  else el.classList.add("hidden");
}

async function sunucuKontrol() {
  try {
    const r = await fetch(window.location.origin + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model: "ping", messages: [] }) });
    sunucuModu = true;
    return true;
  } catch (e) { sunucuModu = false; return false; }
}

function gecerliKey() { return $("apiKey").value.trim(); }
function gecerliMaxTok() { return 32768; }

function mesajEkle(role, icerik, meta) {
  const chat = $("chat");
  chat.classList.remove("bos-merkez");
  const karsilama = $("karsilama");
  if (karsilama) karsilama.style.display = "none";
  const wrap = document.createElement("div");
  wrap.className = "msg-yuzde " + role;
  const ikon = role === "user" ? "🧑" : (meta && meta.meclis ? "⚖" : "⚛");
  wrap.innerHTML = `<div class="avatar ${role}">${ikon}</div>
    <div class="msg-govde">
      <div class="msg-kim">${role === "user" ? "Sen" : meta && meta.ad ? meta.ad : "LenBeyni"}</div>
      <div class="msg-icerik"></div>
      <div class="msg-eylem"></div>
    </div>`;
  chat.appendChild(wrap);
  const govde = wrap.querySelector(".msg-icerik");
  if (role === "user") govde.textContent = icerik;
  if (meta && meta.skilller) {
    meta.skilller.forEach((s) => {
      const tag = document.createElement("span");
      tag.className = "tag-skill";
      tag.textContent = s;
      govde.insertAdjacentElement("beforebegin", tag);
    });
  }
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

// ── Markdown ──────────────────────────────────────────
function kaçis(metin) {
  return metin.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function mdYazdir(el, md) {
  let html = kaçis(md);
  // kod blokları koru
  const kodBloklari = [];
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, kod) => {
    kodBloklari.push({ lang, kod });
    return `\u0000${kodBloklari.length - 1}\u0000`;
  });

  // satır bazında dönüştür
  const satirlar = html.split("\n");
  let cikti = [];
  let listeTipi = null; // "ul" | "ol" | null
  let tabloAcik = false;

  const satirIci = (s) => s
    .replace(/`([^`\n]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

  for (const satir of satirlar) {
    const s = satir.trim();
    if (!s) { if (listeTipi) { listeTipi = null; } if (tabloAcik) { cikti.push("</table>"); tabloAcik = false; } continue; }

    const kodYer = s.match(/^\u0000(\d+)\u0000$/);
    if (kodYer) {
      if (listeTipi) { cikti.push("</" + listeTipi + ">"); listeTipi = null; }
      const b = kodBloklari[+kodYer[1]];
      cikti.push(`<div class="kod-kopten-wrap"><pre><code>${b.kod}</code></pre><button class="kod-kopyala eylem-btn">Kopyala</button></div>`);
      continue;
    }

    let m;
    if ((m = s.match(/^(#{1,3})\s+(.*)$/))) {
      if (listeTipi) { cikti.push("</" + listeTipi + ">"); listeTipi = null; }
      const lvl = m[1].length;
      cikti.push(`<h${lvl}>${satirIci(m[2])}</h${lvl}>`);
    } else if (/^---$/.test(s)) {
      cikti.push("<hr/>");
    } else if ((m = s.match(/^&gt;\s?(.*)$/))) {
      cikti.push(`<blockquote><p>${satirIci(m[1])}</p></blockquote>`);
    } else if ((m = s.match(/^\s*[-*•]\s+(.*)$/))) {
      if (listeTipi !== "ul") { if (listeTipi) cikti.push("</" + listeTipi + ">"); cikti.push("<ul>"); listeTipi = "ul"; }
      cikti.push(`<li>${satirIci(m[1])}</li>`);
    } else if ((m = s.match(/^\s*\d+\.\s+(.*)$/))) {
      if (listeTipi !== "ol") { if (listeTipi) cikti.push("</" + listeTipi + ">"); cikti.push("<ol>"); listeTipi = "ol"; }
      cikti.push(`<li>${satirIci(m[1])}</li>`);
    } else if (/^\|.+\|$/.test(s)) {
      if (listeTipi) { cikti.push("</" + listeTipi + ">"); listeTipi = null; }
      const hucreler = s.slice(1, -1).split("|").map((c) => c.trim());
      if (hucreler.every((c) => /^:?-+:?$/.test(c))) { continue; } // ayraç satırı
      if (!tabloAcik) { cikti.push("<table><thead><tr>" + hucreler.map((c) => "<th>" + satirIci(c) + "</th>").join("") + "</tr></thead><tbody>"); tabloAcik = true; }
      else cikti.push("<tr>" + hucreler.map((c) => "<td>" + satirIci(c) + "</td>").join("") + "</tr>");
    } else {
      if (listeTipi) { cikti.push("</" + listeTipi + ">"); listeTipi = null; }
      cikti.push(`<p>${satirIci(s)}</p>`);
    }
  }
  if (listeTipi) cikti.push("</" + listeTipi + ">");
  if (tabloAcik) cikti.push("</tbody></table>");

  el.innerHTML = cikti.join("\n");

  // kod kopyala butonlarını bağla
  el.querySelectorAll(".kod-kopyala").forEach((btn) => {
    btn.addEventListener("click", () => {
      const kod = btn.parentElement.querySelector("code").textContent;
      navigator.clipboard.writeText(kod).catch(() => {});
    });
  });
}

// ── Sohbet yönetimi ───────────────────────────────────
function sohbetKaydet() {
  const list = depo.get("sohbetler", []);
  if (!aktifSohbet) return;
  const kayit = list.find((x) => x.id === aktifSohbet);
  if (kayit) kayit.mesajlar = gecmis;
}
function sohbetListesiCiz() {
  const kutu = $("sohbetListesi");
  if (!kutu) return;
  const list = depo.get("sohbetler", []);
  kutu.innerHTML = "";
  list.forEach((s) => {
    const div = document.createElement("div");
    div.className = "sohbet-kayit" + (s.id === aktifSohbet ? " aktif" : "");
    const ilk = s.mesajlar.find((m) => m.role === "user");
    div.innerHTML = `<span class="baslik">${ilk ? ilk.content.slice(0, 40) : "Boş sohbet"}</span><span class="sil">✕</span>`;
    div.querySelector(".baslik").addEventListener("click", () => sohbetAc(s.id));
    div.querySelector(".sil").addEventListener("click", (e) => {
      e.stopPropagation();
      const n = depo.get("sohbetler", []).filter((x) => x.id !== s.id);
      depo.set("sohbetler", n);
      if (aktifSohbet === s.id) { aktifSohbet = null; gecmis = []; $("chat").innerHTML = ""; karsilamaGoster(); }
      sohbetListesiCiz();
    });
    kutu.appendChild(div);
  });
}
function sohbetAc(id) {
  const list = depo.get("sohbetler", []);
  const kayit = list.find((x) => x.id === id);
  if (!kayit) return;
  aktifSohbet = id;
  gecmis = kayit.mesajlar || [];
  const chat = $("chat");
  chat.innerHTML = "";
  chat.classList.remove("bos-merkez");
  $("karsilama").style.display = "none";
  gecmis.forEach((m) => {
    const wrap = mesajEkle(m.role, m.content);
    if (m.role === "ai") mdYazdir(wrap.querySelector(".msg-icerik"), m.content);
    else wrap.querySelector(".msg-icerik").textContent = m.content;
  });
  sohbetListesiCiz();
}
function yeniSohbet() {
  sohbetKaydet();
  aktifSohbet = String(Date.now());
  gecmis = [];
  const list = depo.get("sohbetler", []);
  list.unshift({ id: aktifSohbet, baslik: "Yeni sohbet", mesajlar: [] });
  depo.set("sohbetler", list.slice(0, 30));
  $("chat").innerHTML = "";
  $("chat").classList.add("bos-merkez");
  $("karsilama").style.display = "";
  sohbetListesiCiz();
}
function karsilamaGoster() {
  $("chat").innerHTML = "";
  $("chat").classList.add("bos-merkez");
  $("karsilama").style.display = "";
}

// ── API ───────────────────────────────────────────────
async function mega(mesajlar, model, key, mt, fn) {
  const meta = { model, messages: mesajlar, temperature: 0.7, max_tokens: mt || gecerliMaxTok() };
  if (fn) meta.fns = fn;
  if (sunucuModu !== false) {
    try {
      const r = await fetch(window.location.origin + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(meta) });
      const j = await r.json();
      if (r.ok && j.content !== undefined) return j.content;
      if (String(j.error || "").includes("OPENROUTER_KEY")) sunucuModu = false;
    } catch (e) {
      if (sunucuModu === true) throw e;
      sunucuModu = false;
    }
  }
  if (!key) throw new Error("Sunucu rölesi çalışmıyor ve API key girilmedi.");
  const r = await fetch(OPENROUTER, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + key }, body: JSON.stringify(meta) });
  if (!r.ok) throw new Error("HTTP " + r.status + ": " + (await r.text()).slice(0, 220));
  return (await r.json()).choices[0].message.content;
}

async function megaAkis(mesajlar, model, key, mt, onDelta) {
  const meta = { model, messages: mesajlar, temperature: 0.7, max_tokens: mt || gecerliMaxTok(), stream: true };
  const endpoint = sunucuModu !== false ? window.location.origin + "/api/chat" : OPENROUTER;
  const hdrs = sunucuModu !== false ? { "Content-Type": "application/json" } : { "Content-Type": "application/json", "Authorization": "Bearer " + key };
  if (sunucuModu === false && !key) throw new Error("Sunucu rölesi çalışmıyor ve API key girilmedi.");
  const r = await fetch(endpoint, { method: "POST", headers: hdrs, body: JSON.stringify(meta) });
  if (!r.ok) {
    let msj = "HTTP " + r.status;
    try { msj = (await r.json()).error || msj; } catch (e) { msj = await r.text(); }
    if (sunucuModu !== false && String(msj).includes("OPENROUTER_KEY")) sunucuModu = false;
    throw new Error(String(msj).slice(0, 250));
  }
  if (!r.body) { throw new Error("Tarayıcın streaming desteklemiyor."); }
  const okuyucu = r.body.getReader();
  const decoder = new TextDecoder();
  let buf = "", tam = "";
  while (true) {
    const { done, value } = await okuyucu.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const satir = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!satir.startsWith("data:")) continue;
      const veri = satir.slice(5).trim();
      if (veri === "[DONE]") continue;
      try {
        const delta = JSON.parse(veri)?.choices?.[0]?.delta?.content || "";
        if (delta) { tam += delta; if (onDelta) onDelta(delta); }
      } catch (e) { }
    }
  }
  return tam;
}

// ── Web araçları ──────────────────────────────────────
async function siteCek(url) {
  try {
    const r = await fetch(CORS_YON + encodeURIComponent(url));
    return (await r.text())
      .replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/&[a-z]+;/g, " ")
      .replace(/\s+/g, " ").trim().slice(0, 3500);
  } catch (e) { return "[Site okunamadı]"; }
}
async function aramaNet(sorgu) {
  try {
    const r = await fetch(CORS_YON + encodeURIComponent("https://html.duckduckgo.com/html/?q=" + encodeURIComponent(sorgu)));
    const html = await r.text();
    return [...html.matchAll(/result__a[^>]*href="([^"]+)"[^>]*>(.*?)<\/a>/g)].slice(0, 5).map((m) => {
      let link = m[1];
      const uddg = link.match(/uddg=([^&]+)/);
      if (uddg) link = decodeURIComponent(uddg[1]);
      return m[2].replace(/<[^>]+>/g, "").trim() + " | " + link;
    }).join("\n") || "[Arama sonucu yok]";
  } catch (e) { return "[Arama hatası]"; }
}
function sorudakiUrl(s) {
  const m = s.match(/\b(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,6})+(?:\/[^\s]*)?/);
  return m ? m[0] : null;
}

// ── Ana gönderim akışı ────────────────────────────────
async function sistemPromptu(konu, soyut) {
  const parcalar = [
    "Sen LenBeyni'sin — Gemini/Claude seviyesi bir zeka asistanı. Türkçe, net ve rakiplerinden daha kapsamlı cevap ver.",
    "HEDEF: Shally, kısa kesme aramadan konunun tüm yönlerini ele al. Bol madde, başlık, örnek ve açıklama kullan. Claude'un 'kısa cevap' alışkanlığının ötesine geç.",
  ];
  if (soyut) {
    const y = KONU_YONTEM[konu] || KONU_YONTEM.pratik;
    parcalar.push("YÖNTEM: " + y);
    parcalar.push("ADIM ADIM: (1) önce düşün, (2) kapsamlı yaz, (3) kendi cevabını yeniden oku, eksik/hata varsa düzelt.");
  }
  const skillCikarlari = skillIcerikleri();
  if (skillCikarlari.length) parcalar.push("AKTİF SKILLER:\n" + skillCikarlari.map((s) => "• " + s).join("\n"));
  const mcpDokum = mcpAletDokumu();
  if (mcpDokum) {
    parcalar.push("BAGLI MCP ALETLERİ (ihtiyacın olursa kullan):\n" + mcpDokum +
      "\nBir alet çağırmak için satır şu formatta olmalı: TOOL_CALL: aletAdı (parametre=değer, ...)\n" +
      "Sonucu aldıktan sonra nihai cevabını ver.");
  }
  parcalar.push("Cevaplarını **markdown** ile biçimlendir (başlık, madde, kod bloğu, tablo).");
  return parcalar.join("\n\n");
}

async function ajanBaglam(soru, mesajlar) {
  let baglam = "";
  const url = sorudakiUrl(soru);
  if (url && $("toolSite").checked) {
    durum(true, "Site okunuyor: " + url + "…");
    baglam += "\nSİTE: " + await siteCek(url.startsWith("http") ? url : "https://" + url);
  } else if ($("toolArama").checked) {
    const q = soru.replace(/\b(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,6})+(?:\/[^\s]*)?/g, "").trim();
    if (q && q.split(" ").length >= 3) {
      durum(true, "Web aranıyor: " + q.slice(0, 60) + "…");
      baglam += "\nARAMA: " + await aramaNet(q);
    }
  }
  if (baglam) mesajlar.push({ role: "system", content: "Gerçek web verisi (doğrulanmış):" + baglam });
}

// MCP alet çağrısı — model `TOOL_CALL:` satırı çıkarırsa çalıştır, sonucu geri besle.
async function mcpIsle(soru, cevap, mesajlar) {
  const satir = cevap.split("\n").find((l) => l.trim().startsWith("TOOL_CALL:"));
  if (!satir) return cevap;
  const m = satir.match(/TOOL_CALL:\s*(\w+)\s*\((.*?)\)/s);
  if (!m) return cevap;
  const aletAd = m[1], prm = m[2];
  const argumanlar = {};
  prm.split(/\s*,\s*/).forEach((kv) => { const [k, v] = kv.split("=").map((x) => x.trim().replace(/^["']|["']$/g, "")); if (k) argumanlar[k] = v; });
  for (const svr of mcpAktif()) {
    const alet = svr.aletler.find((a) => a.ad === aletAd);
    if (!alet) continue;
    durum(true, "MCP alet çağrılıyor: " + aletAd + "…");
    const sonuc = await mcpAletCagir(svr, aletAd, argumanlar);
    durum(true, "Alet sonucu işleniyor…");
    mesajlar.push({ role: "user", content: sonuc.slice(0, 3000) });
    const devam = await mega(mesajlar, mesajlar._model, gecerliKey(), gecerliMaxTok());
    return devam;
  }
  return cevap;
}

async function gonder() {
  const soru = $("giris").value.trim();
  const key = gecerliKey();
  if (!soru || tekrarAkis) return;
  if (!key) {
    if (sunucuModu === null) await sunucuKontrol();
    if (sunucuModu === false) { alert("Sunucu rölesi yok ve API key girilmedi."); return; }
  }
  $("giris").value = "";
  otomatikBoyut();
  $("btnGonder").disabled = true;
  tekrarAkis = true;

  const konu = konuBul(soru);
  if ($("swRoute") && $("swRoute").checked) modelPiliCiz(konu);

  try {
    if (mod === "meclis") return await meclisTuru(soru, key), (tekrarAkis = false, $("btnGonder").disabled = false);
    // Tek / Akıl Motoru
    const soyut = mod === "akil";
    const aktifSkillerBu = aktifSkilller.map((i) => skills[i]).filter(Boolean);
    const wrap = mesajEkle("user", soru);
    const [model, mt] = konuModel(modelSecili(), konu);
    const sistemi = await sistemPromptu(konu, soyut);
    const mesajlar = [
      { role: "system", content: sistemi },
      ...gecmis.slice(-14),
      { role: "user", content: soru },
    ];
    await ajanBaglam(soru, mesajlar);

    durum(true, (soyut ? "Akıl Motoru" : "LenBeyni") + " — " + konu + " → " + model.split("/").pop().split(":")[0] + " düşünüyor…");
    const aiWrap = mesajEkle("ai", "", { skilller: aktifSkillerBu.map((s) => s.ikon + " " + s.ad) });
    const govde = aiWrap.querySelector(".msg-icerik");
    let tam = "";
    const update = (p) => { tam += p; govde.innerHTML = ""; govde.textContent = ""; mdYazdir(govde, tam); $("chat").scrollTop = $("chat").scrollHeight; };
    let cevap = await megaAkis(mesajlar, model, key, mt, update);
    if (!cevap) { govde.textContent = "(boş cevap)"; }
    else {
      const once = cevap;
      cevap = await mcpIsle(soru, cevap, mesajlar);
      if (cevap !== once) { govde.innerHTML = ""; mdYazdir(govde, cevap); }
      gecmis.push({ role: "user", content: soru });
      gecmis.push({ role: "assistant", content: cevap });
      gecmis = gecmis.slice(-30);
      sohbetKaydet();
      sohbetListesiCiz();
    }
    govdeEylemleri(aiWrap, govde);
  } catch (e) {
    const hata = document.createElement("div");
    hata.className = "msg-icerik";
    hata.style.color = "#f87171";
    hata.textContent = "Hata: " + e.message;
    mesajEkle("ai").querySelector(".msg-icerik").replaceChildren(hata);
  } finally {
    durum(false);
    tekrarAkis = false;
    $("btnGonder").disabled = false;
    $("giris").focus();
  }
}

async function meclisTuru(soru, key) {
  const secilen = [...document.querySelectorAll('#meclisModelSec input:checked')].map((i) => i.value);
  if (secilen.length < 2) { alert("Meclis için en az 2 model seç."); return; }
  mesajEkle("user", soru);
  const wrap = document.createElement("div");
  wrap.className = "meclis-wrap";
  wrap.innerHTML = `<div class="meclis-baslik">⚖ AI Meclisi</div><div class="meclis-grid"></div>`;
  $("chat").appendChild(wrap);
  const grid = wrap.querySelector(".meclis-grid");
  const sozler = await Promise.all(secilen.map(async (model) => {
    const kart = document.createElement("div");
    kart.className = "meclis-card";
    kart.innerHTML = `<h4>⚛ ${model.split("/").pop().split(":")[0]}</h4><div class="content">…</div>`;
    grid.appendChild(kart);
    const icerik = kart.querySelector(".content");
    try {
      const yanit = await mega([{ role: "system", content: "Sen LenBeyni meclisinin bir üyesisin. Türkçe, net cevap ver." }, { role: "user", content: soru }], model, key);
      icerik.textContent = yanit;
      return { model, yanit };
    } catch (e) { icerik.textContent = "Hata: " + e.message; return { model, yanit: null }; }
  }));
  const gecerliler = sozler.filter((s) => s.yanit);
  if (gecerliler.length >= 2) {
    durum(true, "Meclis en iyi cevabı seçiyor…");
    const liste = sozler.map((s, i) => `--- ÜYE${i + 1} (${s.model}) ---\n${s.yanit}`).join("\n\n");
    try {
      const gerekce = await mega([
        { role: "system", content: "Sen AI meclisinin hakimisin. Cevapları oku, en iyisini seç, 1-2 cümle gerekçe ver. Format: 'ÜYE3 kazandı: <gerekçe>'" },
        { role: "user", content: "Soru: " + soru + "\n\n" + liste },
      ], "dots-studio/dots-3-note-preview:free", key);
      const m = gerekce.match(/ÜYE(\d+)/);
      const kazananIdx = m ? parseInt(m[1]) - 1 : 0;
      if (kazananIdx >= 0 && kazananIdx < sozler.length) {
        const kart = grid.querySelectorAll(".meclis-card")[kazananIdx];
        const el = document.createElement("div");
        el.className = "kazanan";
        el.textContent = "🏆 " + gerekce.trim().slice(0, 400);
        kart.appendChild(el);
        kart.style.borderColor = "#6ee7b7";
      }
    } catch (e) { mesajEkle("ai", "Meclis kararı alınamadı: " + e.message); }
    durum(false);
  }
}

// ── Model seçimi ──────────────────────────────────────
function konuModel(secili, konu) {
  if ($("swRoute") && $("swRoute").checked && KONU_MODELLERI[konu]) return KONU_MODELLERI[konu];
  const sabit = {
    "dots-studio/dots-3-note-preview:free": ["dots-studio/dots-3-note-preview:free", 48000],
    "nvidia/nemotron-3-ultra-550b-a55b:free": ["nvidia/nemotron-3-ultra-550b-a55b:free", 65536],
    "poolside/laguna-s-2.1:free": ["poolside/laguna-s-2.1:free", 32768],
  };
  return sabit[secili] || ["dots-studio/dots-3-note-preview:free", 48000];
}
function modelSecili() {
  return localStorage.getItem("lb_model") || "dots-studio/dots-3-note-preview:free";
}
function modelPiliCiz(konu) {
  const [m] = konuModel(modelSecili(), konu || konuBul($("giris").value || ""));
  const ad = m.split("/").pop().split(":")[0];
  const k = konu || konuBul($("giris").value || "");
  $("modelAdi").textContent = ad;
  $("routingKonu").textContent = k;
  $("routingModel").textContent = ad;
  $("routingRoz").classList.add("acik");
}

// ── Öneri kartları ────────────────────────────────────
const ONERILER = [
  { ik: "💡", t: "Bana 5 günlük üretken bir sabah rutini öner" },
  { ik: "📝", t: "Python'da telefon rehberi uygulaması nasıl yazılır?" },
  { ik: "🌍", t: "Karbon ayak izimi azaltmak için neler yapabilirim?" },
  { ik: "📜", t: "Bir masal kahramanı için benzersiz bir güç tasarla" },
  { ik: "🧠", t: "Akıl Motoru ile kritik düşünme nedir?" },
  { ik: "⚽", t: "İstanbul'da 3 günlük gezi planı hazırla" },
];
function onerilerCiz() {
  const kutu = $("oneriGrid");
  if (!kutu) return;
  ONERILER.forEach((o, i) => {
    const div = document.createElement("div");
    div.className = "oneri";
    div.innerHTML = `<span class="oneri-ikon">${o.ik}</span>${o.t}`;
    div.onclick = () => { $("giris").value = o.t; $("giris").focus(); otomatikBoyut(); };
    kutu.appendChild(div);
  });
}

// ── Girdi boyutlandırma ───────────────────────────────
const girisEl = $("giris");
function otomatikBoyut() {
  girisEl.style.height = "auto";
  girisEl.style.height = Math.min(girisEl.scrollHeight, 160) + "px";
}
girisEl.addEventListener("input", otomatikBoyut);

// ── UI başlatma ───────────────────────────────────────
function govdeEylemleri(wrap, govde) {
  const eylem = wrap.querySelector(".msg-eylem");
  const cop = document.createElement("button");
  cop.className = "eylem-btn"; cop.textContent = "Kopyala";
  cop.onclick = async () => { try { await navigator.clipboard.writeText(govde.textContent.trim()); } catch (e) { } };
  const yenile = document.createElement("button");
  yenile.className = "eylem-btn"; yenile.textContent = "↻ Yeniden üret";
  yenile.onclick = () => { $("giris").value = gecmis.filter((m) => m.role === "user").slice(-1)[0]?.content || ""; gonder(); };
  eylem.appendChild(cop); eylem.appendChild(yenile);
}

function panelAcik() { return !$("panel").classList.contains("hidden"); }
function panelToggle() {
  const p = $("panel");
  p.classList.toggle("hidden");
  if (!p.classList.contains("hidden")) { skillListesiCiz(); mcpListesiCiz(); }
}

function modCipsCiz() {
  const kutu = $("modCips");
  if (!kutu) return;
  const { arama, site, skill, mcp } = {
    arama: $("toolArama").checked, site: $("toolSite").checked,
    skill: aktifSkilller.length, mcp: mcpAktif().length,
  };
  const parcalar = [];
  if (arama) parcalar.push('<span class="mod-cip acik">🌐 web arama</span>');
  if (site) parcalar.push('<span class="mod-cip">🔗 site okuma</span>');
  if (skill > 0) parcalar.push(`<span class="mod-cip acik">🎯 ${skill} skill</span>`);
  if (mcp > 0) parcalar.push(`<span class="mod-cip acik">🔌 ${mcp} MCP</span>`);
  if (mod === "akil") parcalar.push('<span class="mod-cip acik">🧠 Akıl Motoru</span>');
  if (mod === "meclis") parcalar.push('<span class="mod-cip acik">⚖ Meclis</span>');
  kutu.innerHTML = parcalar.join(" ");
}

// Model seçim pili
$("modelPili").onclick = () => {
  const modelSec = document.createElement("select");
  modelSec.className = "select-tarz";
  ["dots-studio/dots-3-note-preview:free", "nvidia/nemotron-3-ultra-550b-a55b:free", "poolside/laguna-s-2.1:free", "cohere/north-mini-code:free"].forEach((m) => {
    const o = document.createElement("option");
    o.value = m; o.textContent = m.split("/").pop().split(":")[0] + " — " + m;
    modelSec.appendChild(o);
  });
  modelSec.value = modelSecili();
  $("modelPili").replaceChildren(modelSec);
  modelSec.focus();
  modelSec.onchange = () => { localStorage.setItem("lb_model", modelSec.value); $("modelPili").innerHTML = '<span id="modelAdi">' + modelSec.value.split("/").pop().split(":")[0] + "</span>"; };
  modelSec.onblur = () => { modelPiliCiz(); };
};

// ── Olay bağlama ──────────────────────────────────────
function bagla() {
  $("btnGonder").addEventListener("click", gonder);
  $("giris").addEventListener("keydown", (e) => {
    const ctrlGerek = $("swKisaYol") && $("swKisaYol").checked;
    if (e.key === "Enter" && (ctrlGerek ? e.ctrlKey && !e.shiftKey : !e.shiftKey)) { e.preventDefault(); gonder(); }
  });
  $("btnTemizle").addEventListener("click", () => { karsilamaGoster(); gecmis = []; sohbetKaydet(); sohbetListesiCiz(); });
  $("btnYeniSohbet").addEventListener("click", yeniSohbet);
  $("btnPanel").addEventListener("click", panelToggle);
  $("btnPanelKapat").addEventListener("click", panelToggle);
  $("btnAyarlar").addEventListener("click", panelToggle);

  // mod cips
  document.querySelectorAll(".mod-chip").forEach((c) => c.addEventListener("click", () => {
    mod = c.dataset.mod;
    document.querySelectorAll(".mod-chip").forEach((x) => x.classList.remove("active"));
    c.classList.add("active");
    $("meclisModelSec").classList.toggle("hidden", mod !== "meclis");
    modelPiliCiz();
    modCipsCiz();
  }));

  // skills
  $("btnSkillEkle").addEventListener("click", () => { $("skillModal").classList.remove("hidden"); $("btnSkillKaydet").onclick = () => { adKaydet("skill"); }; });
  function adKaydet(tur) {
    if (tur === "skill") {
      const ad = $("skillAd").value.trim(), ic = $("skillIcerik").value.trim();
      if (!ad || !ic) { alert("Ad ve içerik zorunlu."); return; }
      skills.push({ ad, ikon: "📦", icerik: ic });
      aktifSkilller.push(skills.length - 1);
      skillKaydet(); $("skillModal").classList.add("hidden");
      $("skillAd").value = ""; $("skillIcerik").value = ""; modCipsCiz();
    }
  }
  $("btnMcpEkle").addEventListener("click", () => { $("mcpModal").classList.remove("hidden"); $("btnMcpBagla").onclick = async () => { await mcpBaglaModal(); }; });
  async function mcpBaglaModal() {
    const ad = $("mcpAd").value.trim(), uc = $("mcpUc").value.trim(), proto = $("mcpProto").value;
    if (!ad || !uc) { alert("Ad ve uç noktası zorunlu."); return; }
    const girdi = { uid: Date.now(), ad, uc, proto, durum: "kapali", aletler: [] };
    mcpListesi.push(girdi);
    mcpKaydet();
    $("mcpModal").classList.add("hidden");
    durum(true, "MCP sunucusuna bağlanılıyor: " + ad + "…");
    await mcpYenile(girdi);
    durum(false);
    modCipsCiz();
    $("mcpAd").value = ""; $("mcpUc").value = "";
  }

  // modal kapat (arka plana tıklayınca)
  document.querySelectorAll(".modal").forEach((m) => m.addEventListener("click", (e) => { if (e.target === m) m.classList.add("hidden"); }));

  // side-bar geçmiş
  $("swGecmis").addEventListener("change", (e) => { $("sohbetListesi").style.display = e.target.checked ? "" : "none"; });
  $("swSidebar").addEventListener("change", (e) => { $("sidebar").style.display = e.target.checked ? "" : "none"; });
  $("swRoute").addEventListener("change", () => { modelPiliCiz(); });
  $("swKisaYol").addEventListener("change", () => { });

  // araç değişimi cips
  $("toolArama").addEventListener("change", modCipsCiz);
  $("toolSite").addEventListener("change", modCipsCiz);

  // API key kaydet
  $("apiKey").value = localStorage.getItem("lb_key") || "";
  $("apiKey").addEventListener("input", () => localStorage.setItem("lb_key", $("apiKey").value));
}

// ── Başlangıç ─────────────────────────────────────────
(async function baslangic() {
  try {
    if (await sunucuKontrol()) {
      const kutu = $("apiKey");
      kutu.placeholder = "Key gerekmez (sunucu rölesi aktif)";
    }
  } catch (e) { }
  modelPiliCiz();
  onerilerCiz();
  skillListesiCiz();
  mcpListesiCiz();
  bagla();
  sohbetListesiCiz();
  $("giris").focus();
})();

// test ortamı için dışa aktarımlar
window.LB = { gonder, mdYazdir, konuBul, skills: () => skills, mcpListesi: () => mcpListesi };