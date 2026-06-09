// 多 LLM 直连客户端(浏览器内 fetch,不走后端,Key 不出前端)
// 支持 OpenAI / Claude / Gemini / DeepSeek / PackyAPI / 自定义 OpenAI-compatible
import type { LLMConfig, LLMProvider } from "./types";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface ModelInfo {
  id: string;
  object?: string;
  created?: number;
  owned_by?: string;
}

/** 从 OpenAI 兼容的 /v1/models 端点获取可用模型列表 */
export async function fetchModels(cfg: LLMConfig): Promise<string[]> {
  if (!cfg.apiKey) {
    throw new Error("未设置 API Key,请先在 Settings 里填入。");
  }
  const baseUrl = normalizeOpenAICompatBaseUrl(cfg.baseUrl, cfg.provider);
  const url = `${baseUrl}/models`;

  const r = await fetch(url, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${cfg.apiKey}`,
    },
  });

  if (!r.ok) {
    const t = await r.text().catch(() => "");
    if (r.status === 404) {
      throw new Error("该端点不支持 /v1/models 接口。请手动输入模型名称，PackyAPI 常见模型: deepseek-chat, deepseek-reasoner, gpt-4o-mini, gpt-4o, claude-3-5-sonnet。");
    }
    throw new Error(`获取模型列表失败 (${r.status}): ${t.slice(0, 200)}`);
  }

  const data = await r.json();
  const models: string[] = (data.data || [])
    .map((m: ModelInfo) => m.id)
    .filter((id: string) => id && typeof id === "string")
    .sort();

  if (models.length === 0) {
    throw new Error("未获取到任何模型，请检查 API Key 是否有效。");
  }

  return models;
}

const PROVIDER_DEFAULT: Record<LLMProvider, { baseUrl: string; model: string }> = {
  openai:   { baseUrl: "https://api.openai.com/v1",    model: "gpt-4o-mini" },
  claude:   { baseUrl: "https://api.anthropic.com/v1", model: "claude-3-5-haiku-latest" },
  gemini:   { baseUrl: "https://generativelanguage.googleapis.com/v1beta", model: "gemini-1.5-flash" },
  deepseek: { baseUrl: "https://api.deepseek.com/v1",  model: "deepseek-chat" },
  packy:    { baseUrl: "https://www.packyapi.com/v1", model: "deepseek-chat" },
  custom:   { baseUrl: "",                              model: "" },
};

export function defaultConfig(provider: LLMProvider): LLMConfig {
  const d = PROVIDER_DEFAULT[provider];
  return { provider, apiKey: "", baseUrl: d.baseUrl, model: d.model };
}

export function listProviders(): LLMProvider[] {
  return ["openai", "claude", "gemini", "deepseek", "packy", "custom"];
}

export function normalizeOpenAICompatBaseUrl(raw: string | undefined, provider: LLMProvider): string {
  const fallback = provider === "packy" ? PROVIDER_DEFAULT.packy.baseUrl : "";
  const value = (raw || fallback).trim();
  if (!value) return value;
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    let path = url.pathname.replace(/\/+$/, "");

    if (provider === "packy" || host.endsWith("packyapi.com")) {
      if (path === "" || path === "/" || path.startsWith("/console") || path.startsWith("/login") || path.startsWith("/register")) {
        path = "/v1";
      } else if (!path.startsWith("/v1")) {
        path = "/v1";
      }
      url.pathname = path;
      url.search = "";
      url.hash = "";
      return url.toString().replace(/\/$/, "");
    }

    path = path.replace(/\/chat\/completions$/, "");
    if (path === "") path = "/v1";
    url.pathname = path;
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/$/, "");
  } catch {
    return value.replace(/\/+$/, "");
  }
}

/**
 * 流式调用 LLM,逐 token 回调。
 * 注意:浏览器直连 → 用户的 API Key 不会进 server;但浏览器 console 仍可能记录请求。
 */
export async function* streamChat(
  cfg: LLMConfig,
  messages: ChatMessage[],
  signal?: AbortSignal,
): AsyncGenerator<string, void, void> {
  if (!cfg.apiKey) {
    throw new Error("未设置 API Key,请在 Settings 里填入。");
  }
  if (cfg.provider === "claude") {
    yield* streamClaude(cfg, messages, signal);
  } else if (cfg.provider === "gemini") {
    yield* streamGemini(cfg, messages, signal);
  } else {
    // OpenAI-compatible:openai / deepseek / custom
    yield* streamOpenAICompat(cfg, messages, signal);
  }
}

// ---------- OpenAI-compatible (含 DeepSeek) ----------

async function* streamOpenAICompat(
  cfg: LLMConfig,
  messages: ChatMessage[],
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const baseUrl = normalizeOpenAICompatBaseUrl(cfg.baseUrl, cfg.provider);
  const url = `${baseUrl}/chat/completions`;
  const r = await fetch(url, {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${cfg.apiKey}`,
    },
    body: JSON.stringify({
      model: cfg.model,
      messages,
      stream: true,
      temperature: 0.7,
    }),
  });
  if (!r.ok || !r.body) {
    const t = await r.text().catch(() => "");
    if (cfg.provider === "packy" && /model_not_found|无可用渠道|distributor|分组/.test(t)) {
      throw new Error(`PackyAPI 模型与 token 分组不匹配：当前模型 ${cfg.model || "未填写"} 在这个 token 分组下不可用。deepseek-officially 分组请先用 deepseek-chat；如果要用 GPT 模型，需要在 Packy 里切换到支持 GPT 的分组/token。原始错误：${t.slice(0, 160)}`);
    }
    throw new Error(`LLM ${r.status}: ${t.slice(0, 200)}`);
  }
  const reader = r.body.getReader();
  const dec = new TextDecoder("utf-8");
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line || !line.startsWith("data:")) continue;
      const data = line.slice(5).trim();
      if (data === "[DONE]") return;
      try {
        const j = JSON.parse(data);
        const delta = j.choices?.[0]?.delta?.content;
        if (delta) yield delta;
      } catch {
        // 跳过不规范的行
      }
    }
  }
}

// ---------- Anthropic Claude ----------

async function* streamClaude(
  cfg: LLMConfig,
  messages: ChatMessage[],
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const sys = messages.find((m) => m.role === "system")?.content || "";
  const rest = messages.filter((m) => m.role !== "system");
  const url = `${cfg.baseUrl}/messages`;
  const r = await fetch(url, {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      "x-api-key": cfg.apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: cfg.model,
      system: sys,
      messages: rest,
      max_tokens: 4096,
      stream: true,
    }),
  });
  if (!r.ok || !r.body) {
    const t = await r.text().catch(() => "");
    throw new Error(`Claude ${r.status}: ${t.slice(0, 200)}`);
  }
  const reader = r.body.getReader();
  const dec = new TextDecoder("utf-8");
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line.startsWith("data:")) continue;
      const data = line.slice(5).trim();
      try {
        const j = JSON.parse(data);
        if (j.type === "content_block_delta" && j.delta?.text) {
          yield j.delta.text;
        }
      } catch { /* skip */ }
    }
  }
}

// ---------- Google Gemini ----------

async function* streamGemini(
  cfg: LLMConfig,
  messages: ChatMessage[],
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const sys = messages.find((m) => m.role === "system")?.content || "";
  const rest = messages.filter((m) => m.role !== "system");
  const url = `${cfg.baseUrl}/models/${cfg.model}:streamGenerateContent?alt=sse&key=${cfg.apiKey}`;
  const contents = rest.map((m) => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: m.content }],
  }));
  const r = await fetch(url, {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents,
      systemInstruction: { parts: [{ text: sys }] },
      generationConfig: { temperature: 0.7 },
    }),
  });
  if (!r.ok || !r.body) {
    const t = await r.text().catch(() => "");
    throw new Error(`Gemini ${r.status}: ${t.slice(0, 200)}`);
  }
  const reader = r.body.getReader();
  const dec = new TextDecoder("utf-8");
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line.startsWith("data:")) continue;
      const data = line.slice(5).trim();
      try {
        const j = JSON.parse(data);
        const text = j.candidates?.[0]?.content?.parts?.[0]?.text;
        if (text) yield text;
      } catch { /* skip */ }
    }
  }
}
