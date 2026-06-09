import { useState } from "react";
import { useKeys } from "../store/keys";
import { defaultConfig, listProviders, fetchModels } from "../lib/llm-client";
import { COLOR } from "./ui";
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
    setFetchingModels(true);
    setModelError(null);
    setAvailableModels([]);
    setShowModelDropdown(false);
    try {
      const models = await fetchModels(config);
      setAvailableModels(models);
      setShowModelDropdown(true);
      // If current model is not in list, auto-select the first one
      if (models.length > 0 && !models.includes(config.model)) {
        setModel(models[0]);
      }
    } catch (e: any) {
      setModelError(e?.message || String(e));
    } finally {
      setFetchingModels(false);
    }
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg" style={{ color: COLOR.goldBright }}>LLM 解读设置</h3>
        <button className="btn-ghost text-xs" onClick={reset}>重置</button>
      </div>

      <div>
        <label className="label">服务</label>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
          {listProviders().map((provider) => (
            <button
              key={provider}
              className={`btn-ghost text-xs ${config.provider === provider ? "nav-link-active" : ""}`}
              onClick={() => {
                setProvider(provider);
                if (provider === "custom") return;
                const defaults = defaultConfig(provider);
                setBaseUrl(defaults.baseUrl || "");
                setModel(defaults.model || "");
              }}
            >
              {provider}
            </button>
          ))}
        </div>
        <div className="text-[10px] mt-2" style={{ color: COLOR.muted }}>{PROVIDER_LABELS[config.provider]}</div>
      </div>

      <div>
        <label className="label">API Key</label>
        <div className="text-[10px] mb-1" style={{ color: COLOR.muted }}>
          填写你在 {providerName} 后台创建的 API token。PackyAPI 请填“令牌管理”里创建的 token，不是控制台页面地址。
        </div>
        <div className="flex gap-2">
          <input
            className="input flex-1 font-mono"
            type={reveal ? "text" : "password"}
            value={config.apiKey}
            onChange={(e) => setApiKey(e.target.value.trim())}
            placeholder={config.provider === "packy" ? "PackyAPI token" : "sk-..."}
            autoComplete="off"
          />
          <button className="btn-ghost text-xs" onClick={() => setReveal((value) => !value)}>
            {reveal ? "隐藏" : "显示"}
          </button>
        </div>
        <div className="text-[10px] mt-1" style={{ color: COLOR.muted }}>
          Key 只保存在浏览器本地，不会上传到本服务后端。
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="label">Base URL</label>
          <div className="text-[10px] mb-1" style={{ color: COLOR.muted }}>
            PackyAPI 使用 https://www.packyapi.com/v1 或 https://api-slb.packyapi.com/v1；误填 /console/token 会自动规整到 /v1。
          </div>
          <input
            className="input"
            type="text"
            value={config.baseUrl || ""}
            onChange={(e) => setBaseUrl(e.target.value.trim())}
            placeholder={config.provider === "packy" ? "https://www.packyapi.com/v1" : "https://api.openai.com/v1"}
          />
        </div>
        <div>
          <label className="label">模型</label>
          <div className="text-[10px] mb-1" style={{ color: COLOR.muted }}>
            点击「获取模型」从 API 拉取可用模型列表，或手动输入模型名称。
          </div>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                className="input w-full"
                type="text"
                value={config.model || ""}
                onChange={(e) => { setModel(e.target.value.trim()); setShowModelDropdown(false); }}
                onFocus={() => { if (availableModels.length > 0) setShowModelDropdown(true); }}
                placeholder={config.provider === "packy" ? "deepseek-chat" : "gpt-4o-mini"}
              />
              {showModelDropdown && availableModels.length > 0 && (
                <div
                  className="absolute left-0 right-0 top-full mt-1 z-10 rounded border overflow-y-auto"
                  style={{ maxHeight: "200px", background: "var(--bg-card, #1a1a2e)", borderColor: COLOR.lineSoft }}
                  onMouseLeave={() => setShowModelDropdown(false)}
                >
                  {availableModels.map((m) => (
                    <button
                      key={m}
                      className={`w-full text-left px-3 py-1.5 text-xs hover:opacity-80 ${m === config.model ? "font-semibold" : ""}`}
                      style={{
                        color: m === config.model ? COLOR.goldBright : COLOR.inkSoft,
                        background: m === config.model ? "rgba(212,175,55,0.08)" : "transparent",
                      }}
                      onClick={() => { setModel(m); setShowModelDropdown(false); }}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              className="btn-ghost text-xs whitespace-nowrap"
              onClick={handleFetchModels}
              disabled={fetchingModels}
              style={fetchingModels ? { opacity: 0.6 } : undefined}
            >
              {fetchingModels ? "获取中…" : "获取模型"}
            </button>
          </div>
          {modelError && (
            <div className="text-[10px] mt-1" style={{ color: COLOR.danger }}>{modelError}</div>
          )}
          {!modelError && availableModels.length > 0 && (
            <div className="text-[10px] mt-1" style={{ color: COLOR.ok }}>
              已加载 {availableModels.length} 个可用模型
            </div>
          )}
        </div>
      </div>

      <div className="divider-soft" />

      <div className="text-xs space-y-1" style={{ color: COLOR.muted }}>
        <div>浏览器会直连所选 provider，请确认网络环境允许访问对应 API。</div>
        <div>PackyAPI 的控制台 token 页只是拿令牌的地方，不要当作 Base URL 填入。</div>
        <div>如果 provider 不支持浏览器 CORS，前端会回退到本服务的 mock 解读。</div>
      </div>
    </div>
  );
}
