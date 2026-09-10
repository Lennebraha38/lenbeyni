// LenBeyni MCP Rölesi (Vercel Serverless).
// Tarayıcıdan uzak MCP sunucularına JSON-RPC over HTTP ile alet listeleme/çağırma.
// CORS ve anahtar sorunlarını sunucu tarafında çözer; key tarayıcıya asla sızmaz.
const MCP_HEADERS = { "Content-Type": "application/json", "Accept": "application/json, text/event-stream" };

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).json({ error: "POST gerekli" });

  const { action, uc, proto = "http", alet, argumanlar } = req.body || {};
  if (!uc) return res.status(400).json({ error: "Uç nokta (uc) gerekli" });

  try {
    if (action === "tools") {
      const payload = { jsonrpc: "2.0", id: 1, method: "tools/list" };
      const data = await mcpIste(uc, proto, payload);
      return res.json({ tools: (data?.result?.tools || []).map((t) => ({
        name: t.name,
        description: t.description || "",
        inputSchema: t.inputSchema || {},
      })) });
    }

    if (action === "call") {
      if (!alet) return res.status(400).json({ error: "alet gerekli" });
      const payload = { jsonrpc: "2.0", id: 2, method: "tools/call", params: { name: alet, arguments: argumanlar || {} } };
      const data = await mcpIste(uc, proto, payload);
      const result = data?.result || {};
      return res.json({ content: result.content || [], isError: !!result.isError });
    }

    return res.status(400).json({ error: "Bilinmeyen aksiyon" });
  } catch (e) {
    return res.status(502).json({ error: String(e.message || e).slice(0, 300) });
  }
}

// JSON-RPC over HTTP isteği. SSE uçları için önce initialize/initialized el sıkışması yapılır.
async function mcpIste(uc, proto, payload) {
  if (proto === "sse") {
    // SSE: önce /initialize + /notifications gönder, sonra tekrar iste
    await fetch(uc, { method: "POST", headers: MCP_HEADERS, body: JSON.stringify({
      jsonrpc: "2.0", id: 0, method: "initialize",
      params: { protocolVersion: "2025-03-26", capabilities: {}, clientInfo: { name: "lenbeyni", version: "1.0" } },
    }) });
  }
  const r = await fetch(uc, { method: "POST", headers: MCP_HEADERS, body: JSON.stringify(payload) });
  if (!r.ok) throw new Error("MCP HTTP " + r.status);
  const gövde = await r.text();
  try { return JSON.parse(gövde); }
  catch (e) {
    // SSE satırlarından JSON-RPC yanıtını çıkar
    const satir = gövde.split("\n").find((s) => s.startsWith("data:"));
    if (satir) return JSON.parse(satir.slice(5).trim());
    throw new Error("MCP yanıtı JSON veya SSE değil");
  }
}