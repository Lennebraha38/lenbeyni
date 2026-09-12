/* ═══════════════════════════════════════════════════════════
   ZenAI Web — Gemini/Claude seviyesi arayüz
   Özellikler: konu→model yönlendirme, Akıl Motoru, Skills ekleme,
   MCP bağlama (JSON-RPC over HTTP rölesi), AI Meclisi, streaming,
   web arama + site okuma, sohbet geçmişi, konuşma listesi.
   ═══════════════════════════════════════════════════════════ */
const OPENROUTER = "https://openrouter.ai/api/v1/chat/completions";
const CORS_YON = "https://api.allorigins.win/raw?url=";
const $ = (id) => document.getElementById(id);

// ── Model görünen adları ─────────────────────────────
// Kullanıcıya ham sağlayıcı model kodları değil, marka adları gösterilir.
// Dahilde (istek/aktarım) gerçek model kodu korunur.
const MODEL_AD = {
  "dots-studio/dots-3-note-preview:free": "Dots-3",
  "nvidia/nemotron-3-ultra-550b-a55b:free": "Nemotron 3",
  "poolside/laguna-s-2.1:free": "Poolside Laguna",
  "cohere/north-mini-code:free": "Cohere North Code",
};
function modelAdi(model) {
  return MODEL_AD[model] || String(model).split("/").pop().split(":")[0];
}
// Marka rozetinden gerçek model koduna dönüş (meclis seçimi vb.)
const ADAN_MODEL = {};
for (const [kod, ad] of Object.entries(MODEL_AD)) ADAN_MODEL[ad.toLowerCase().replace(/\s+/g, "-")] = kod;
function modelKod(marka) {
  if (String(marka).includes("/")) return marka;
  const anahtar = String(marka).toLowerCase().replace(/\s+/g, "-");
  return ADAN_MODEL[anahtar] || marka;
}

// ── Dil / tema / i18n ────────────────────────────────
const L = {
  tr: {
    yenikonus: "Yeni sohbet", gecmisi_gizle: "Geçmişi gizle", ayarlar: "Ayarlar ve Yetenekler", bu_cihazda: "Bu cihazda",
    model_secin: "Model seçin", model_secimi: "Model seçimi",
    karsilama_h2: "Bugün ne yapalım?",
    karsilama_alt: "ZenAI — konuya göre akıllı yönlendirme, Akıl Motoru, Skills ve MCP bağlantılarıyla etkileşimli bir zekâ asistanı.",
    tl_konu: "KONU YÖNLENDİRME", tl_coklu: "ÇOKLU MODEL", tl_skill: "SKILLS + MCP",
    gir_ph: "ZenAI'ye bir şey sor…",
    not_yanilgi: "ZenAI hatalı bilgi verebilir. Önemli bilgileri doğrulayın.",
    dosya_ekle: "Dosya ekle", araclar: "Araçlar: web arama + site okuma + Akıl Motoru",
    gonder: "Gönder", sohbeti_temizle: "Sohbeti temizle", kaynak_ac: "Yetenekler ve bağlantılar",
    panel_baslik: "Yetenekler ve Bağlantılar", kenar_cubuk: "Kenar çubuğu", kenar_goster: "Kenar çubuğu göster",
    akil_route: "Akıl yönlendirme (konu→model)", kisa_yol: "Kısayol: Enter yerine Ctrl+Enter",
    mod: "Mod", sobhet_modu: "Sohbet", akil_motoru: "Akıl Motoru", meclis_modu: "AI Meclisi", meclis_modelleri: "Meclis modelleri",
    araclar_baslik: "Araçlar", web_aramasi: "Web araması", site_okuma: "Site okuma",
    skills_baslik: "Skills (Yetenekler)", skill_ekle: "＋ Ekle",
    skill_ac: "Seçili skill, cevap üretirken sistem talimatınıza eklenir.",
    mcp_baslik: "MCP Bağlantıları", mcp_bagla: "＋ Bağla",
    mcp_ac: "Uzak MCP sunucularını JSON-RPC over HTTP ile bağlayın. Bağlı aletler sohbetinize eklenir.",
    gelistirici: "Geliştirici", apikey_ph: "Sağlayıcı API key (gerekirse)",
    apikey_ac: "Key yalnız bu tarayıcı oturumunda tutulur, disk'e yazılmaz; cevaplar doğrudan sağlayıcıya gönderilir. Sunucu rölesi aktifse key gerekmez.",
    yeni_skill: "Yeni Skill", skill_ad_ph: "Skill adı (örn: Web Uzmanı)",
    skill_icerik_ph: "Sistem talimatı… Örn: 'Sen tecrübeli bir web geliştiricisisin. HTML, CSS, JS önerileri ver.'",
    kaydet: "Kaydet", mcp_sunucu: "MCP Sunucusu Bağla", mcp_ad_ph: "Sunucu adı (örn: Veritabanı)",
    mcp_uc_ph: "Uç noktası (örn: https://sunucu.com/mcp)", mcp_ac2: "Bağlandığında sunucudan alet (tool) listesi çekilir ve sohbete eklenir.",
    bagla_ve_listele: "Bağla ve aletleri listele", kapat: "Kapat",
    arama_ph: "Sohbetlerde ara…", sohbet_yok: "Henüz sohbet yok.", no_bulgu: "Eşleşen sohbet yok.",
    sil: "Sil", duzenle: "Yeniden adlandır", disa_aktar: "Dışa aktar",
    kopyala: "Kopyala", yeniden_uret: "↻ Yeniden üret", hata: "Hata", dusunuyor: "düşünüyor…",
    meclis_sec: "Meclis için en az 2 model seç.", sec_mesaj: "Mesaj",
    dil_degistir: "Dil değiştir", tema_degistir: "Tema değiştir",
    gizlilik: "Gizlilik", sartlar: "Şartlar", iletisim: "İletişim",
    gizlilik_baslik: "Gizlilik Politikası",
    gizlilik_icerik: "<p>ZenAI kendi sunucusunda sohbet içeriği veya girdinizi saklamaz. Girdiler, cevap üretimi için sağlayıcıya iletilir.</p><p>Sohbetleriniz yalnız bu cihazda (tarayıcı yerel deposunda) tutulur; tarayıcı verilerini temizlediğinizde silinir.</p><p>API key'iniz sunucumuza gönderilmez, yalnız içinde bulunduğunuz oturumda doğrudan sağlayıcıya iletilir.</p>",
    sartlar_baslik: "Kullanım Şartları",
    sartlar_icerik: "<p>ZenAI bir yapay zekâ asistanıdır; ürettiği bilgiler hatalı veya güncel olmayabilir. Önemli kararlarınızda doğrulama yapın.</p><p>Yasadışı içerik üretimi, telifli materyalin izinsiz kullanımı ve kötüye kullanım yasaktır.</p><p>Hizmet, veri'de aksama durumunda kesintisizlik garantisi vermez.</p>",
    iletisim_baslik: "İletişim",
    iletisim_icerik: "<p>Geri bildirim, hata bildirimi veya işbirliği için bize ulaşabilirsiniz.</p><p><strong>GitHub:</strong> github.com/Lennebraha38/ZENAI</p><p><strong>Domain:</strong> zenai-two.vercel.app</p>",
  },
  en: {
    yenikonus: "New chat", gecmisi_gizle: "Hide history", ayarlar: "Settings & Skills", bu_cihazda: "On this device",
    model_secin: "Select model", model_secimi: "Model selection",
    karsilama_h2: "What shall we do today?",
    karsilama_alt: "ZenAI — an interactive intelligence assistant with topic routing, Reasoning Engine, Skills and MCP connections.",
    tl_konu: "TOPIC ROUTING", tl_coklu: "MULTI-MODEL", tl_skill: "SKILLS + MCP",
    gir_ph: "Ask ZenAI anything…",
    not_yanilgi: "ZenAI may produce inaccurate information. Verify important details.",
    dosya_ekle: "Attach file", araclar: "Tools: web search + site reading + Reasoning Engine",
    gonder: "Send", sohbeti_temizle: "Clear chat", kaynak_ac: "Skills & connections",
    panel_baslik: "Skills & Connections", kenar_cubuk: "Sidebar", kenar_goster: "Show sidebar",
    akil_route: "Reasoning routing (topic→model)", kisa_yol: "Shortcut: use Ctrl+Enter instead of Enter",
    mod: "Mode", sobhet_modu: "Chat", akil_motoru: "Reasoning Engine", meclis_modu: "AI Council", meclis_modelleri: "Council models",
    araclar_baslik: "Tools", web_aramasi: "Web search", site_okuma: "Site reading",
    skills_baslik: "Skills", skill_ekle: "＋ Add",
    skill_ac: "The selected skill is added to the system instructions while generating.",
    mcp_baslik: "MCP Connections", mcp_bagla: "＋ Connect",
    mcp_ac: "Connect remote MCP servers over JSON-RPC over HTTP. Connected tools join your chat.",
    gelistirici: "Developer", apikey_ph: "Provider API key (if needed)",
    apikey_ac: "The key is held only for this browser session (never written to disk) and is sent straight to the provider. Not needed when the server relay is active.",
    yeni_skill: "New Skill", skill_ad_ph: "Skill name (e.g. Web Expert)",
    skill_icerik_ph: "System instruction… E.g. 'You are an experienced web developer. Give HTML, CSS, JS advice.'",
    kaydet: "Save", mcp_sunucu: "Connect MCP Server", mcp_ad_ph: "Server name (e.g. Database)",
    mcp_uc_ph: "Endpoint (e.g. https://server.com/mcp)", mcp_ac2: "On connect, the tool list is fetched from the server and added to the chat.",
    bagla_ve_listele: "Connect & list tools", kapat: "Close",
    arama_ph: "Search chats…", sohbet_yok: "No chats yet.", no_bulgu: "No matching chats.",
    sil: "Delete", duzenle: "Rename", disa_aktar: "Export",
    kopyala: "Copy", yeniden_uret: "↻ Regenerate", hata: "Error", dusunuyor: "thinking…",
    meclis_sec: "Select at least 2 models for the council.", sec_mesaj: "Message",
    dil_degistir: "Change language", tema_degistir: "Toggle theme",
    gizlilik: "Privacy", sartlar: "Terms", iletisim: "Contact",
    gizlilik_baslik: "Privacy Policy",
    gizlilik_icerik: "<p>ZenAI does not store your chat content or input on its own server. Inputs are forwarded to the provider to generate answers.</p><p>Your chats are kept only on this device (browser local storage); they are erased when you clear browser data.</p><p>Your API key is never sent to our server; during the session it is sent directly to the provider.</p>",
    sartlar_baslik: "Terms of Use",
    sartlar_icerik: "<p>ZenAI is an AI assistant; information it produces may be inaccurate or stale. Verify before making important decisions.</p><p>Generating illegal content, unauthorized use of copyrighted material and abuse are prohibited.</p><p>The service does not guarantee uninterrupted availability.</p>",
    iletisim_baslik: "Contact",
    iletisim_icerik: "<p>Reach out for feedback, bug reports or collaboration.</p><p><strong>GitHub:</strong> github.com/Lennebraha38/ZENAI</p><p><strong>Site:</strong> zenai-two.vercel.app</p>",
  },
};
let dil = localStorage.getItem("lb_dil") || "tr";
let tema = localStorage.getItem("lb_tema") || "koyu";
function t(k) { return (L[dil] && L[dil][k] !== undefined) ? L[dil][k] : (L.tr[k] !== undefined ? L.tr[k] : k); }
function uygulaI18n() {
  document.documentElement.lang = dil === "en" ? "en" : "tr";
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => (el.placeholder = t(el.dataset.i18nPh)));
  document.querySelectorAll("[data-i18n-ar]").forEach((el) => (el.setAttribute("aria-label", t(el.dataset.i18nAr))));
  document.querySelectorAll("[data-i18n-tit]").forEach((el) => (el.title = t(el.dataset.i18nTit)));
  if ($("btnDil")) $("btnDil").textContent = dil === "tr" ? "EN" : "TR";
  const meta = $("metaTema");
  if (meta) meta.setAttribute("content", tema === "aydinlik" ? "#f4f6fb" : "#04060c");
}
function temaAt(yeni) {
  tema = yeni || tema;
  localStorage.setItem("lb_tema", tema);
  document.documentElement.dataset.tema = tema;
  if ($("btnTema")) $("btnTema").textContent = tema === "aydinlik" ? "🌙" : "☀";
  uygulaI18n();
}
function dilAt(yeni) {
  dil = yeni || (dil === "tr" ? "en" : "tr");
  localStorage.setItem("lb_dil", dil);
  uygulaI18n();
  if ($("oneriGrid")) onerilerCiz();
  modelPiliCiz();
  skillListesiCiz();
  mcpListesiCiz();
  sohbetListesiCiz();
  modCipsCiz();
}

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
  kod:       ["cohere/north-mini-code:free", 65536],
  matematik: ["nvidia/nemotron-3-ultra-550b-a55b:free", 65536],
  mantik:    ["nvidia/nemotron-3-ultra-550b-a55b:free", 65536],
  bilim:     ["dots-studio/dots-3-note-preview:free", 48000],
  tarih:     ["dots-studio/dots-3-note-preview:free", 48000],
  dil:       ["dots-studio/dots-3-note-preview:free", 24000],
  yaratici:  ["dots-studio/dots-3-note-preview:free", 40000],
  kultur:    ["dots-studio/dots-3-note-preview:free", 24000],
  pratik:    ["dots-studio/dots-3-note-preview:free", 16000],
  teknoloji: ["dots-studio/dots-3-note-preview:free", 48000],
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
let aktifSkilller = depo.get("aktifSkilller", []);

function skillKaydet() {
  depo.set("skills", skills);
  depo.set("aktifSkilller", aktifSkilller);
  skillListesiCiz();
}

function skillListesiCiz() {
  const kutu = $("skillListesi");
  if (!kutu) return;
  kutu.innerHTML = skills.length === 0
    ? '<p class="panel-aciklama">' + t("skills_baslik") + ' — "＋ Ekle"' + "</p>"
    : "";
  skills.forEach((s, i) => {
    const open = aktifSkilller.includes(i);
    const div = document.createElement("div");
    div.className = "skill-kayit" + (open ? " open" : "");
    div.innerHTML = `<span class="skill-ikon">${s.ikon}</span><span class="skill-ad">${s.ad}</span>
      <span class="mcp-durum ${open ? "bagli" : "kapali"}" style="border:none;padding:0">${open ? "on" : "off"}</span>
      <button class="skill-kaldir" title="${t("sil")}" aria-label="${t("sil")}">✕</button>`;
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
      <button class="mcp-kaldir" title="${t("sil")}" aria-label="${t("sil")}">✕</button>`;
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

// ── Canlı enerji arka planı (canvas) ────────────────────
function arkaBaslat() {
  const cv = $("arka-canvas");
  if (!cv) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const ctx = cv.getContext("2d");
  let genis = 0, yuksek = 0;
  const noktalar = Array.from({ length: 54 }, () => ({
    x: Math.random(), y: Math.random(),
    vx: (Math.random() - 0.5) * 0.00032, vy: (Math.random() - 0.5) * 0.00032,
    r: 0.6 + Math.random() * 1.5,
    t: Math.random() * 6.28,
  }));
  let fare = { x: 0.5, y: 0.5 };
  window.addEventListener("pointermove", (e) => {
    fare.x = e.clientX / Math.max(1, window.innerWidth);
    fare.y = e.clientY / Math.max(1, window.innerHeight);
  }, { passive: true });

  const boyutla = () => {
    genis = cv.width = window.innerWidth;
    yuksek = cv.height = window.innerHeight;
  };
  boyutla();
  window.addEventListener("resize", boyutla);

  function ciz() {
    ctx.clearRect(0, 0, genis, yuksek);
    const px = (fare.x - 0.5) * 26, py = (fare.y - 0.5) * 18;
    const ceyrekX = (x) => (x * genis + px + genis) % genis;
    for (const n of noktalar) {
      n.x += n.vx; n.y += n.vy;
      if (n.x < 0 || n.x > 1) n.vx *= -1;
      if (n.y < 0 || n.y > 1) n.vy *= -1;
      const kx = ceyrekX(n.x), ky = n.y * yuksek + py;
      const gibi = 0.35 + 0.65 * Math.abs(Math.sin(n.t += 0.008));
      const g = ctx.createRadialGradient(kx, ky, 0, kx, ky, n.r * 7);
      g.addColorStop(0, `rgba(62,230,216,${0.45 * gibi})`);
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(kx, ky, n.r * 7, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgba(214,240,255,${0.32 * gibi})`;
      ctx.beginPath(); ctx.arc(kx, ky, n.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.lineWidth = 0.6;
    for (let i = 0; i < noktalar.length; i++) {
      for (let j = i + 1; j < noktalar.length; j++) {
        const a = noktalar[i], b = noktalar[j];
        const dx = (a.x - b.x) * genis, dy = (a.y - b.y) * yuksek;
        const d = Math.hypot(dx, dy);
        if (d < 120) {
          ctx.strokeStyle = `rgba(126,144,255,${0.20 * (1 - d / 120)})`;
          ctx.beginPath();
          ctx.moveTo(ceyrekX(a.x), a.y * yuksek + py);
          ctx.lineTo(ceyrekX(b.x), b.y * yuksek + py);
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(ciz);
  }
  ciz();
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
function gecerliMaxTok() { return 16384; }

function mesajEkle(role, icerik, meta) {
  const chat = $("chat");
  chat.classList.remove("bos-merkez");
  const karsilama = $("karsilama");
  if (karsilama) karsilama.style.display = "none";
  const wrap = document.createElement("div");
  wrap.className = "msg-yuzde " + role;
  const ikon = role === "user" ? "S" : (meta && meta.meclis ? "M" : "Z");
  wrap.innerHTML = `<div class="avatar ${role}">${ikon}</div>
    <div class="msg-govde">
      <div class="msg-kim">${role === "user" ? "Sen" : meta && meta.ad ? meta.ad : "ZenAI"}</div>
      <div class="msg-icerik"></div>
      <div class="msg-eylem"></div>
    </div>`;
  chat.appendChild(wrap);
  const govde = wrap.querySelector(".msg-icerik");
  if (role === "user") govde.textContent = icerik;
  if (meta && meta.sinyal) {
    const s = document.createElement("span");
    s.className = "msg-sinyal";
    s.innerHTML = "<i></i> route " + kaçis(meta.sinyal);
    wrap.querySelector(".msg-govde").insertBefore(s, wrap.querySelector(".msg-kim").nextSibling);
  }
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
  if (!kayit) return;
  kayit.mesajlar = gecmis;
  const ilk = gecmis.find((m) => m.role === "user");
  if (ilk) kayit.baslik = ilk.content.slice(0, 40);
}
function sohbetListesiCiz() {
  const kutu = $("sohbetListesi");
  if (!kutu) return;
  const term = (($("sohbetAra") && $("sohbetAra").value) || "").trim().toLowerCase();
  const list = depo.get("sohbetler", []).filter((s) => !term || (s.baslik || "").toLowerCase().includes(term));
  kutu.innerHTML = "";
  if (list.length === 0) {
    kutu.innerHTML = `<p class="panel-aciklama" style="text-align:center;padding:22px 6px">${t(term ? "no_bulgu" : "sohbet_yok")}</p>`;
    return;
  }
  list.forEach((s) => {
    const div = document.createElement("div");
    div.className = "sohbet-kayit" + (s.id === aktifSohbet ? " aktif" : "");
    div.innerHTML = `<span class="baslik" title="${t("duzenle")}">${kaçis(s.baslik || "")}</span>
      <span class="islemler">
        <button class="iy" aria-label="${t("duzenle")}" title="${t("duzenle")}">✎</button>
        <button class="ds" aria-label="${t("disa_aktar")}" title="${t("disa_aktar")}">⇩</button>
        <button class="sil" aria-label="${t("sil")}" title="${t("sil")}">✕</button>
      </span>`;
    div.querySelector(".baslik").addEventListener("click", () => sohbetAc(s.id));
    div.querySelector(".iy").addEventListener("click", (e) => {
      e.stopPropagation();
      const yeni = prompt(t("duzenle"), s.baslik || "");
      if (yeni && yeni.trim()) {
        const liste = depo.get("sohbetler", []);
        const kayit = liste.find((x) => x.id === s.id);
        if (kayit) { kayit.baslik = yeni.trim().slice(0, 60); depo.set("sohbetler", liste); }
        sohbetListesiCiz();
      }
    });
    div.querySelector(".ds").addEventListener("click", (e) => {
      e.stopPropagation();
      const disa = { uygulama: "ZenAI", disaktarma: new Date().toISOString(), sohbet: s };
      const blob = new Blob([JSON.stringify(disa, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "zenai-" + String(s.baslik || "sohbet").slice(0, 32).replace(/[^a-z0-9çğıöşüÇĞİÖŞÜ]+/gi, "_") + ".json";
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    });
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
async function mega(mesajlar, model, key, mt) {
  const meta = { model, messages: mesajlar, temperature: 0.7, max_tokens: mt || gecerliMaxTok() };
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
    "Sen ZenAI'sin — Türkçe bir asistan. Doğrudan, net ve özlü cevap ver.",
    "KALİTE + UZUNLUK KURALI: Önce tek cümlelik doğrudan cevap. Sonra gerekirse 3-5 kısa madde veya kısa adım akışı. Cevabın uzunluğunu sorunun kapsamına göre ayarla — kullanıcı detay istedadı özet ver, irade yoksa net ve bitmiş ver. Bol tekrar, giriş/bitiş süsü, gereksiz başlık yığını yapma. Çoğu soru 100-250 kelimeyle biter; 400 kelimeyi aşma.",
  ];
  if (soyut) {
    const y = KONU_YONTEM[konu] || KONU_YONTEM.pratik;
    parcalar.push("YÖNTEM: " + y);
    parcalar.push("AKIŞ: görünür adımları kısa tut; her adımı 1-2 cümleyle ver, sonucu en sonda tek cümleyle kapat.");
  }
  const skillCikarlari = skillIcerikleri();
  if (skillCikarlari.length) parcalar.push("AKTİF SKILLER:\n" + skillCikarlari.map((s) => "• " + s).join("\n"));
  const mcpDokum = mcpAletDokumu();
  if (mcpDokum) {
    parcalar.push("BAGLI MCP ALETLERİ (ihtiyacın olursa kullan):\n" + mcpDokum +
      "\nBir alet çağırmak için satır şu formatta olmalı: TOOL_CALL: aletAdı (parametre=değer, ...)\n" +
      "Sonucu aldıktan sonra nihai cevabını ver.");
  }
  parcalar.push("Cevaplarını **markdown** ile hafifçe biçimlendir (gerekirse başlık, madde, kod bloğu).");
  return parcalar.join("\n\n");
}

async function ajanBaglam(soru, mesajlar, konu) {
  let baglam = "";
  const url = sorudakiUrl(soru);
  if (url && $("toolSite").checked) {
    durum(true, "Site okunuyor: " + url + "…");
    baglam += "\nSİTE: " + await siteCek(url.startsWith("http") ? url : "https://" + url);
  } else if ($("toolArama").checked && aramaGerekliMi(soru, konu)) {
    const q = soru.replace(/\b(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,6})+(?:\/[^\s]*)?/g, "").trim();
    if (q && q.split(" ").length >= 3) {
      durum(true, "Web aranıyor: " + q.slice(0, 60) + "…");
      baglam += "\nARAMA: " + await aramaNet(q);
    }
  }
  if (baglam) mesajlar.push({ role: "system", content: "Gerçek web verisi (doğrulanmış):" + baglam });
}

// Sisteme neyi arayıp neyi aramayacağını söyle — web'i körü körüne kullanma.
const ARAMA_TETIK = /(20\d\d|bu\s*yıl|bu\s*ay|geçen\s*hafta|az\s*önce|bugün|dün|yarın|son\s*haber|haberleri|güncel|en\s*son|en\s*yeni|yeni\s*sürüm|son\s*sürüm|sürüm\s*notl|versiyon|çıkış\s*tarihi|çıktı\s*mı|fiyat|fiyatları|ne\s*kadar|kaç\s*para|indirim|kampanya|seçim|maç|skor|galibiyet|hava\s*durumu|açılış\s*saati|kapanış|reçete|yönetmelik|politika|dolar|euro|bitcoin|kaç\s*oldu|en\s*çok\s*(?:satılan|kullanılan|izlenen|okunan)|sıralaması|raporu)\b/i;
const ARAMA_ENGEL = /\b(hikaye|masal|şiir|roman|mektup|şarkı|slogan|senaryo|yaz\b|yazmamı|yazmak|tasarla|tasarlamak|hayal\s*et|öner\b|önerir|önerisi|tavsiye\b|fikir|fikrini|sence|senin\s*görüşün|bence|gibi\s*hissed|hissettir|yorumla?|tarif\s*ver|plan\s*hazırla|ne\s*yarap|\bisten\b)\b/i;
const ARAMA_KONU_ENGEL = { kod: 1, matematik: 1, mantik: 1, yaratici: 1 };

function aramaGerekliMi(soru, konu) {
  const s = soru.toLowerCase();
  if (!s || s.trim().split(/\s+/).length < 3) return false;   // kısa mesele mastır: arama yok
  if (ARAMA_ENGEL.test(s)) return false;                       // üretim/kişisel istek: arama yok
  if (ARAMA_TETIK.test(s)) return true;                        // güncel/haber/fiyat: ara
  if (ARAMA_KONU_ENGEL[konu]) return false;                    // kod/matematik/mantık/yaratıcı: ara
  if (/(nedir|ne\s*demek|kimdir|ne\s*işe\s*yarar|nasıl\s*çalışır|nasıl\s*yapılır|nasıl\s*(?:ölçerim|açarım|kurarım|düzeltebilirim|alabilirim|yazarım)|açıkla|açıklaması|kısaca|neresi)\s*[.?!]?\s*$/i.test(s)) return false;
  return true;
}

// MCP alet çağrısı — model `TOOL_CALL:` satırı çıkarırsa çalıştır, sonucu geri besle.
async function mcpIsle(soru, cevap, mesajlar, model) {
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
    const devam = await mega(mesajlar, model, gecerliKey(), gecerliMaxTok());
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
    await ajanBaglam(soru, mesajlar, konu);

    durum(true, (soyut ? t("akil_motoru") : "ZenAI") + " — " + konu + " → " + modelAdi(model) + " " + t("dusunuyor"));
    const sinyalKonu = konu + " → " + modelAdi(model);
    const aiWrap = mesajEkle("ai", "", { skilller: aktifSkillerBu.map((s) => s.ikon + " " + s.ad), sinyal: sinyalKonu });
    const govde = aiWrap.querySelector(".msg-icerik");
    document.body.classList.add("calisiyor");

    // Akış: dikey kaydırma okuyuşunu durdurmadan, imleci takip ederek akıllı render.
    const yaziyor = document.createElement("div");
    yaziyor.className = "yaziyor";
    yaziyor.innerHTML = "<i></i><i></i><i></i>";
    govde.appendChild(yaziyor);

    let tam = "", renderT = null;
    const tazeCiz = () => {
      if (!tam) return;
      const g = document.createElement("div");
      mdYazdir(g, tam);
      const imlec = document.createElement("span");
      imlec.className = "imlec";
      g.appendChild(imlec);
      govde.querySelectorAll(".yaziyor").forEach((e) => e.remove());
      govde.replaceChildren(g);
      // markdown sonrası tekrar hizalı kalsın
      const c = $("chat");
      if (c.scrollHeight - c.scrollTop - c.clientHeight < 240) c.scrollTop = c.scrollHeight;
    };
    const kuyruk = () => {
      if (renderT) return;
      renderT = setTimeout(() => { renderT = null; tazeCiz(); }, 110);
    };
    const update = (p) => {
      tam += p;
      yaziyor.remove();
      clearTimeout(renderT); renderT = null;
      tazeCiz();
    };

    let cevap = await megaAkis(mesajlar, model, key, mt, update);
    if (!cevap) { govde.textContent = "(boş cevap)"; }
    else {
      const once = cevap;
      cevap = await mcpIsle(soru, cevap, mesajlar, model);
      if (cevap !== once) { govde.replaceChildren(); mdYazdir(govde, cevap); }
      gecmis.push({ role: "user", content: soru });
      gecmis.push({ role: "assistant", content: cevap });
      gecmis = gecmis.slice(-30);
      sohbetKaydet();
      sohbetListesiCiz();
    }
    // kayan imleç: cevabın bittiğini güzelce göster
    const bitisImleci = document.createElement("span");
    bitisImleci.className = "imlec-bitirdi";
    bitisImleci.textContent = "▍";
    govde.appendChild(bitisImleci);
    setTimeout(() => bitisImleci.remove(), 1400);
    govdeEylemleri(aiWrap, govde);
  } catch (e) {
    const hata = document.createElement("div");
    hata.className = "msg-icerik";
    hata.style.color = "#f87171";
    hata.textContent = "Hata: " + e.message;
    mesajEkle("ai").querySelector(".msg-icerik").replaceChildren(hata);
  } finally {
    document.body.classList.remove("calisiyor");
    durum(false);
    tekrarAkis = false;
    $("btnGonder").disabled = false;
    $("giris").focus();
  }
}

async function meclisTuru(soru, key) {
  const secilen = [...document.querySelectorAll('#meclisModelSec input:checked')].map((i) => modelKod(i.value));
  if (secilen.length < 2) { alert(t("meclis_sec")); return; }
  mesajEkle("user", soru);
  const wrap = document.createElement("div");
  wrap.className = "meclis-wrap";
  wrap.innerHTML = `<div class="meclis-baslik">⚖ AI Meclisi</div><div class="meclis-grid"></div>`;
  $("chat").appendChild(wrap);
  const grid = wrap.querySelector(".meclis-grid");
  const sozler = await Promise.all(secilen.map(async (model) => {
    const kart = document.createElement("div");
    kart.className = "meclis-card";
    kart.innerHTML = `<h4>⚛ ${modelAdi(model)}</h4><div class="content">…</div>`;
    grid.appendChild(kart);
    const icerik = kart.querySelector(".content");
    try {
      const yanit = await mega([{ role: "system", content: "Sen ZenAI meclisinin bir üyesisin. Türkçe, net cevap ver." }, { role: "user", content: soru }], model, key);
      icerik.textContent = yanit;
      return { model, yanit };
    } catch (e) { icerik.textContent = "Hata: " + e.message; return { model, yanit: null }; }
  }));
  const gecerliler = sozler.filter((s) => s.yanit);
  if (gecerliler.length >= 2) {
    durum(true, "Meclis en iyi cevabı seçiyor…");
    const liste = sozler.map((s, i) => `--- ÜYE${i + 1} (${modelAdi(s.model)}) ---\n${s.yanit}`).join("\n\n");
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
  const sinir = (m) => [m[0], Math.min(m[1], 16384)];
  if ($("swRoute") && $("swRoute").checked && KONU_MODELLERI[konu]) return sinir(KONU_MODELLERI[konu]);
  const sabit = {
    "dots-studio/dots-3-note-preview:free": sinir(["dots-studio/dots-3-note-preview:free", 48000]),
    "nvidia/nemotron-3-ultra-550b-a55b:free": sinir(["nvidia/nemotron-3-ultra-550b-a55b:free", 65536]),
    "poolside/laguna-s-2.1:free": sinir(["poolside/laguna-s-2.1:free", 32768]),
  };
  return sabit[secili] || sinir(["dots-studio/dots-3-note-preview:free", 48000]);
}
function modelSecili() {
  return localStorage.getItem("lb_model") || "dots-studio/dots-3-note-preview:free";
}
function modelPiliCiz(konu) {
  const [m] = konuModel(modelSecili(), konu || konuBul($("giris").value || ""));
  const ad = modelAdi(m);
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
  cop.className = "eylem-btn"; cop.textContent = t("kopyala");
  cop.onclick = async () => { try { await navigator.clipboard.writeText(govde.textContent.trim()); } catch (e) { } };
  const yenile = document.createElement("button");
  yenile.className = "eylem-btn"; yenile.textContent = t("yeniden_uret");
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
  modelSec.setAttribute("aria-label", t("model_secimi"));
  ["dots-studio/dots-3-note-preview:free", "cohere/north-mini-code:free", "nvidia/nemotron-3-ultra-550b-a55b:free", "poolside/laguna-s-2.1:free"].forEach((m) => {
    const o = document.createElement("option");
    o.value = m; o.textContent = modelAdi(m);
    modelSec.appendChild(o);
  });
  modelSec.value = modelSecili();
  $("modelPili").replaceChildren(modelSec);
  modelSec.focus();
  modelSec.onchange = () => { localStorage.setItem("lb_model", modelSec.value); $("modelPili").innerHTML = '<span id="modelAdi">' + modelAdi(modelSec.value) + "</span>"; };
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
  if ($("swGecmis")) $("swGecmis").addEventListener("change", (e) => { $("sohbetListesi").style.display = e.target.checked ? "" : "none"; });
  if ($("swSidebar")) $("swSidebar").addEventListener("change", (e) => { $("sidebar").style.display = e.target.checked ? "" : "none"; });
  if ($("swRoute")) $("swRoute").addEventListener("change", () => { modelPiliCiz(); });
  if ($("swKisaYol")) $("swKisaYol").addEventListener("change", () => { });

  // sohbet arama
  if ($("sohbetAra")) $("sohbetAra").addEventListener("input", sohbetListesiCiz);

  // araç değişimi cips
  if ($("toolArama")) $("toolArama").addEventListener("change", modCipsCiz);
  if ($("toolSite")) $("toolSite").addEventListener("change", modCipsCiz);

  // dil ve tema
  if ($("btnDil")) $("btnDil").addEventListener("click", () => dilAt());
  if ($("btnTema")) $("btnTema").addEventListener("click", () => temaAt(tema === "aydinlik" ? "koyu" : "aydinlik"));

  // yasal / güven sayfaları
  const bilgiAc = (tur) => {
    $("#bilgiBaslik").textContent = t(tur + "_baslik");
    $("#bilgiIcerik").innerHTML = t(tur + "_icerik");
    $("#bilgiModal").classList.remove("hidden");
  };
  if ($("ayakGizlilik")) $("ayakGizlilik").addEventListener("click", (e) => { e.preventDefault(); bilgiAc("gizlilik"); });
  if ($("ayakSartlar")) $("ayakSartlar").addEventListener("click", (e) => { e.preventDefault(); bilgiAc("sartlar"); });
  if ($("ayakIletisim")) $("ayakIletisim").addEventListener("click", (e) => { e.preventDefault(); bilgiAc("iletisim"); });
  if ($("btnBilgiKapat")) $("btnBilgiKapat").addEventListener("click", () => $("bilgiModal").classList.add("hidden"));

  // API key: kalıcı depolama yok — yalnız bu oturum
  $("apiKey").value = sessionStorage.getItem("lb_key") || "";
  $("apiKey").addEventListener("input", () => sessionStorage.setItem("lb_key", $("apiKey").value.trim()));
}

// ── Başlangıç ─────────────────────────────────────────
(async function baslangic() {
  arkaBaslat();
  temaAt();
  uygulaI18n();
  try {
    if (await sunucuKontrol()) {
      const kutu = $("apiKey");
      kutu.placeholder = t("apikey_ph") + " ✓";
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
window.LB = { gonder, mdYazdir, konuBul, aramaGerekliMi, skills: () => skills, mcpListesi: () => mcpListesi };