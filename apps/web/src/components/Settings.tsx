import { useState } from "react";
import { useKeys } from "../store/keys";
import { defaultConfig, listProviders, fetchModels } from "../lib/llm-client";
import type { LLMProvider } from "../lib/types";

const PROVIDER_LABELS: Record<LLMProvider, string> = {
  openai: "OpenAI (GPT-4o / GPT-4o-mini)",
  claude: "Anthropic Claude (3.5 Sonnet / Haiku)",
  gemini: "Google Gemini (1.5 Flash / Pro)",
  deepseek: "DeepSeek (deepseek-chat)",
  packy: "PackyAPI (OpenAI 兼容)",
  custom: "自定义 OpenAI 兼容端点",
};

export function Settings() {
  const { config, setProvider, setApiKey, setBaseUrl, setModel, reset } = useKeys();
  const [reveal, setReveal] = useState(false);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [modelError, setModelError] = useState<string | null>(null);
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const providerName = PROVIDER_LABELS[config.provider].split(" (")[0];

  async function handleFetchModels() {
    setFetchingModels(true); setModelError(null); setAvailableModels([]); setShowModelDropdown(false);
    try {
      const models = await fetchModels(config);
      setAvailableModels(models); setShowModelDropdown(true);
      if (models.length > 0 && !models.includes(config.model)) setModel(models[0]);
    } catch (e: any) { setModelError(e?.message || String(e)); }
    finally { setFetchingModels(false); }
  }

  return (
    <div className="paper-frame space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="paper-eyebrow" style={{ marginBottom: 0 }}>LLM 解读设置</h3>
        <button className="paper-btn-ghost" style={{ fontSize: "0.68rem" }} onClick={reset}>重置</button>
      </div>

      <div>
        <label className="paper-label">服务</label>
        <div className="flex flex-wrap gap-1.5" style={{ marginTop: "0.3rem" }}>
          {listProviders().map((provider) => (
            <button key={provider}
              className="paper-tag" style={{
                fontSize: "0.72rem", cursor: "pointer",
                color: config.provider === provider ? "var(--cinnabar)" : "var(--ink-soft)",
                borderColor: config.provider === provider ? "var(--cinnabar)" : "var(--rule)",
              }}
              onClick={() => {
                setProvider(provider);
                if (provider !== "custom") {
                  const defaults = defaultConfig(provider);
                  setBaseUrl(defaults.baseUrl || "");
                  setModel(defaults.model || "");
                }
              }}>{provider}</button>
          ))}
        </div>
        <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", marginTop: "0.3rem" }}>{PROVIDER_LABELS[config.provider]}</div>
      </div>

      <div>
        <label className="paper-label">API Key</label>
        <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)", marginBottom: "0.2rem" }}>
          填写你在 {providerName} 后台创建的 API token。
        </div>
        <div className="flex gap-2">
          <input className="paper-input flex-1" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.78rem" }}
            type={reveal ? "text" : "password"} value={config.apiKey}
            onChange={(e) => setApiKey(e.target.value.trim())}
            placeholder={config.provider === "packy" ? "PackyAPI token" : "sk-..."}
            autoComplete="off" />
          <button className="paper-btn-ghost" style={{ fontSize: "0.72rem" }} onClick={() => setReveal((v) => !v)}>
            {reveal ? "隐藏" : "显示"}
          </button>
        </div>
        <div style={{ fontSize: "0.58rem", color: "var(--ink-soft)", marginTop: "0.2rem" }}>Key 只保存在浏览器本地，不会上传到本服务后端。</div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="paper-label">Base URL</label>
          <input className="paper-input" type="text" value={config.baseUrl || ""}
            onChange={(e) => setBaseUrl(e.target.value.trim())}
            placeholder={config.provider === "packy" ? "https://www.packyapi.com/v1" : "https://api.openai.com/v1"} />
        </div>
        <div>
          <label className="paper-label">模型</label>
          <div className="flex gap-2">
            <div style={{ position: "relative", flex: 1 }}>
              <input className="paper-input w-full" type="text" value={config.model || ""}
                onChange={(e) => { setModel(e.target.value.trim()); setShowModelDropdown(false); }}
                onFocus={() => { if (availableModels.length > 0) setShowModelDropdown(true); }}
                placeholder={config.provider === "packy" ? "deepseek-chat" : "gpt-4o-mini"} />
              {showModelDropdown && availableModels.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-1 z-10 rounded border overflow-y-auto"
                  style={{ maxHeight: "200px", background: "var(--paper)", borderColor: "var(--rule)" }}
                  onMouseLeave={() => setShowModelDropdown(false)}>
                  {availableModels.map((m) => (
                    <button key={m}
                      className="w-full text-left px-3 py-1.5 text-xs"
                      style={{
                        color: m === config.model ? "var(--cinnabar)" : "var(--ink-soft)",
                        background: m === config.model ? "rgba(176,58,46,0.06)" : "transparent",
                        fontWeight: m === config.model ? 600 : 400,
                      }}
                      onClick={() => { setModel(m); setShowModelDropdown(false); }}>{m}</button>
                  ))}
                </div>
              )}
            </div>
            <button className="paper-btn-ghost" style={{ fontSize: "0.72rem", whiteSpace: "nowrap" }}
              onClick={handleFetchModels} disabled={fetchingModels}>
              {fetchingModels ? "获取中…" : "获取模型"}
            </button>
          </div>
          {modelError && <div style={{ fontSize: "0.62rem", color: "var(--cinnabar)", marginTop: "0.2rem" }}>{modelError}</div>}
          {!modelError && availableModels.length > 0 && (
            <div style={{ fontSize: "0.62rem", color: "var(--verdigris)", marginTop: "0.2rem" }}>已加载 {availableModels.length} 个可用模型</div>
          )}
        </div>
      </div>

      <div className="paper-hr" />
      <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", lineHeight: 1.7 }}>
        <p>浏览器会直连所选 provider，请确认网络环境允许访问对应 API。</p>
        <p>PackyAPI 的控制台 token 页只是拿令牌的地方，不要当作 Base URL 填入。</p>
        <p>如果 provider 不支持浏览器 CORS，前端会回退到本服务的 mock 解读。</p>
      </div>
    </div>
  );
}
