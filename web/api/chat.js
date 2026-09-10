// Zenai sunucu rölesi (Vercel Serverless).
// Kullanıcı ASLA key görmez/girmez — key sadece burada (env OPENROUTER_KEY).
const OPENROUTER = "https://openrouter.ai/api/v1/chat/completions";

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(200).end();

  const KEY = process.env.OPENROUTER_KEY || "";
  if (!KEY) {
    return res.status(500).json({ error: "Sunucuda OPENROUTER_KEY yok. Vercel -> Settings -> Environment Variables -> OPENROUTER_KEY ekle." });
  }
  if (req.method !== "POST") return res.status(405).json({ error: "POST gerekli" });

  const { model, messages, temperature = 0.7, max_tokens = 16384, stream = false } = req.body || {};
  if (!model || !messages) return res.status(400).json({ error: "model ve messages gerekli" });

  try {
    const r = await fetch(OPENROUTER, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + KEY },
      body: JSON.stringify({ model, messages, temperature, max_tokens, stream }),
    });

    if (stream) {
      // SSE'yi oldugu gibi bayraktan gecir
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(decoder.decode(value));
      }
      return res.end();
    }

    const data = await r.json();
    if (!r.ok) return res.status(r.status).json({ error: data?.error?.message || JSON.stringify(data).slice(0, 300) });
    return res.json({ content: data.choices?.[0]?.message?.content || "" });
  } catch (e) {
    return res.status(500).json({ error: String(e.message || e).slice(0, 300) });
  }
}