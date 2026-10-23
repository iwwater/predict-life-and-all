/** LiuyaoPage v2 — 六爻专页（仪式型）
 *  闭环：问事 → 摇卦(代摇/亲手) → 六爻竖排 + 装卦表 → 动爻/旬空/月破 → 解读
 *  依据: 前端重构指示v2 §三·卜类
 */
import { type FormEvent, useState, useCallback, useEffect, useRef } from "react";
import type { Birth, ChartResult } from "../../lib/types";
import { computeChart } from "../../lib/api";
import { useI18n } from "../../lib/i18n";
import { useBasket } from "../../store/basket";
import { useBirthStore } from "../../store/birth";
import { COLOR } from "../../components/ui";
import { MethodSourcesPanel } from "../../components/MethodSourcesPanel";

// 六爻自下而上: 初爻(index 0) → 上爻(index 5)
const YAO_NAMES = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"];
const YAO_NAMES_EN = ["L1", "L2", "L3", "L4", "L5", "L6"];

type CoinToss = "old_yin" | "young_yin" | "young_yang" | "old_yang";

// 掷币 → 爻值: 6老阴(动) 7少阳 8少阴 9老阳(动) —— 引擎契约 list[int]
const TOSS_INT: Record<CoinToss, number> = { old_yin: 6, young_yang: 7, young_yin: 8, old_yang: 9 };

// 真三枚铜钱: 每枚正面3/背面2, 三枚之和 6-9 —— 老阴/老阳各 1/8, 动爻率与实物一致
function randomToss(): CoinToss {
  let sum = 0;
  for (let i = 0; i < 3; i++) sum += Math.random() < 0.5 ? 3 : 2;
  return sum === 6 ? "old_yin" : sum === 7 ? "young_yang" : sum === 8 ? "young_yin" : "old_yang";
}

export function LiuyaoPage() {
  const { t, lang } = useI18n();
  const birthStore = useBirthStore();
  const basketAdd = useBasket((s) => s.add);
  const inBasket = useBasket((s) => s.has("liuyao"));

  // 问事（必填！）
  const [question, setQuestion] = useState("");
  // 摇卦模式
  const [shakeMode, setShakeMode] = useState<"auto" | "manual">("auto");
  // 铜钱结果（6爻）
  const [tosses, setTosses] = useState<(CoinToss | null)[]>([null, null, null, null, null, null]);
  const [currentYao, setCurrentYao] = useState(0); // 亲手摇的当前爻位
  // 摇卦动画
  const [shaking, setShaking] = useState(false);
  const [shakeIdx, setShakeIdx] = useState(-1); // 正在落的爻

  // 状态
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const animTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 代摇：自动连摇6爻
  // 局部数组快照逐爻落定 —— 不用函数式更新, 避免同 tick 的 reset 与更新竞态丢首爻
  const autoShake = useCallback(() => {
    if (shaking) return;
    setShaking(true);
    const results: (CoinToss | null)[] = [null, null, null, null, null, null];
    setTosses([...results]);
    setShakeIdx(0);
    let idx = 0;
    const go = () => {
      if (idx >= 6) {
        setShaking(false);
        setShakeIdx(-1);
        return;
      }
      results[idx] = randomToss();
      setTosses([...results]);
      setShakeIdx(idx);
      idx++;
      animTimer.current = setTimeout(go, 450);
    };
    go();
  }, [shaking]);

  // 亲手摇：逐爻
  const manualToss = () => {
    if (currentYao >= 6) return;
    setTosses((prev) => {
      const next = [...prev];
      next[currentYao] = randomToss();
      return next;
    });
    setCurrentYao((i) => i + 1);
  };

  const resetTosses = () => {
    setTosses([null, null, null, null, null, null]);
    setCurrentYao(0);
    setShaking(false);
    setShakeIdx(-1);
    if (animTimer.current) clearTimeout(animTimer.current);
  };

  useEffect(() => {
    return () => { if (animTimer.current) clearTimeout(animTimer.current); };
  }, []);

  const submit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const b = birthStore.toApiBirth();
      const chart = await computeChart({
        method: "liuyao", birth: b,
        options: {
          mode: shakeMode === "auto" ? "time_qigua" : "manual_coin",
          question: question || "问事",
          // 掷币映射成引擎契约的 int 爻值; 代摇也发送 —— 页面上看到的铜钱就是入盘的铜钱
          tosses: (tosses.filter(Boolean) as CoinToss[]).map((t) => TOSS_INT[t]),
        },
      });
      setChart(chart);
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }, [question, shakeMode, tosses, birthStore]);

  const addToBasket = () => {
    basketAdd({ method: "liuyao", chart, birth: birthStore.toApiBirth(), addedAt: Date.now() });
  };

  const allTossed = tosses.every((t) => t !== null);
  const r = chart?.raw as Record<string, any> | undefined;
  // 引擎 raw 中文键: 摇钱(list[int])/本卦/变卦/动爻/世/应/六爻装卦(naijia)/断{用神六亲,断语,世应关系,提示}
  const yaoQian: number[] = Array.isArray(r?.["摇钱"]) ? r!["摇钱"] : [];
  const dongYao: number[] = Array.isArray(r?.["动爻"]) ? r!["动爻"] : [];
  const naijia: any[] = Array.isArray(r?.["六爻装卦"]) ? r!["六爻装卦"] : [];
  const duan = (r?.["断"] || {}) as Record<string, any>;
  const hexagram = r?.["本卦"]?.["name"] || "";
  const bianGua = r?.["变卦"]?.["name"] || "";
  const yongshen = duan["用神六亲"] || "";
  const yongshenAdvice = Array.isArray(duan["断语"]) ? duan["断语"].join("；") : String(duan["断语"] || "");
  // 装卦表 + 摇钱合并成渲染行: is_yang 由摇钱 7/9 推, is_dong 由动爻表推
  const yaos: any[] = naijia.map((nj: any, i: number) => ({
    position: nj["爻"],
    is_yang: yaoQian.length === 6 ? [7, 9].includes(yaoQian[i]) : false,
    is_dong: dongYao.includes(nj["爻"]),
    dizhi: nj["地支"],
    liuqin: nj["六亲"],
    liushen: nj["六神"],
    shiying: nj["世应"],
    xunkong: nj["旬空"],
    yuepo: nj["月破"],
  }));

  return (
    <div className="space-y-6">
      <header>
        <h1 className="paper-title">
          <span className="stamp" />
          {lang === "zh" ? "六爻起卦" : "Liu Yao"}
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--ink-soft)", marginTop: "0.4rem", lineHeight: 1.6 }}>
          {lang === "zh"
            ? "心诚则灵。先写下所问之事，然后摇卦。系统默认为你代摇，亦可亲手逐爻落钱。"
            : "Focus your mind on the question, then cast the coins."}
        </p>
      </header>

      {/* 第0步：问事 — 最重要，放最前面 */}
      <section className="paper-frame space-y-3">
        <h2 className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>
          {lang === "zh" ? "一、所问之事（必填）" : "1. Your Question (required)"}
        </h2>
        <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>
          {lang === "zh"
            ? "一事一问，心念专一。六爻靠用神取用，问题越具体，解读越准。"
            : "One clear question per hexagram. The more specific, the better the reading."}
        </p>
        <textarea
          className="paper-input"
          style={{ minHeight: 80, fontSize: "0.9rem" }}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={lang === "zh" ? "例如：这次跳槽去XX公司对我事业发展有利吗？" : "e.g. Will this job change benefit my career?"}
        />
      </section>

      {/* 第1步：摇卦 */}
      <section className="paper-frame space-y-4">
        <h2 className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>
          {lang === "zh" ? "二、摇卦" : "2. Cast the Hexagram"}
        </h2>

        {/* 模式切换 */}
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => { setShakeMode("auto"); resetTosses(); }}
            className="paper-tag" style={{
              cursor: "pointer", fontSize: "0.78rem",
              color: shakeMode === "auto" ? "var(--cinnabar)" : "var(--ink-soft)",
              borderColor: shakeMode === "auto" ? "var(--cinnabar)" : "var(--rule)",
              background: shakeMode === "auto" ? "rgba(176,58,46,0.04)" : "transparent",
            }}>
            {lang === "zh" ? "代摇（推荐）" : "Auto Toss"}
          </button>
          <button type="button" onClick={() => { setShakeMode("manual"); resetTosses(); }}
            className="paper-tag" style={{
              cursor: "pointer", fontSize: "0.78rem",
              color: shakeMode === "manual" ? "var(--cinnabar)" : "var(--ink-soft)",
              borderColor: shakeMode === "manual" ? "var(--cinnabar)" : "var(--rule)",
              background: shakeMode === "manual" ? "rgba(176,58,46,0.04)" : "transparent",
            }}>
            {lang === "zh" ? "亲手摇" : "Manual Toss"}
          </button>
        </div>

        {/* 代摇 */}
        {shakeMode === "auto" && (
          <div className="space-y-3">
            <button type="button" className="paper-btn" onClick={autoShake} disabled={shaking}
              style={{ minWidth: 140 }}>
              {shaking ? (lang === "zh" ? "摇卦中…" : "Shaking…") : (lang === "zh" ? "开始摇卦" : "Start Casting")}
            </button>
            {/* 铜钱落定动画 */}
            <div className="grid grid-cols-6 gap-2">
              {YAO_NAMES_EN.map((name, i) => {
                const t = tosses[i];
                const isLanding = shakeIdx === i;
                const isOld = t === "old_yin" || t === "old_yang";
                const isYang = t === "young_yang" || t === "old_yang";
                return (
                  <div key={i} className="text-center p-2 rounded-sm" style={{
                    border: `1px solid ${isLanding ? "var(--cinnabar)" : t ? "var(--rule)" : "transparent"}`,
                    background: t ? "var(--paper-2)" : "transparent",
                    transition: "all 0.3s",
                    transform: isLanding ? "scale(1.1)" : "scale(1)",
                  }}>
                    <div style={{ fontSize: "0.62rem", color: "var(--ink-soft)" }}>{name}</div>
                    {t !== null && (
                      <div
                        className={`coin coin--landed`}
                        style={{ animationDelay: `${i * 450}ms` }}
                        aria-hidden="true"
                      >
                        {isYang ? "⚊" : "⚋"}
                      </div>
                    )}
                    {t === null && (
                      <div style={{ fontSize: "1.5rem", color: "var(--ink-soft)", height: "1.8rem", lineHeight: "1.8rem" }}>—</div>
                    )}
                    {t && (
                      <div style={{ fontSize: "0.62rem", color: isOld ? "var(--cinnabar)" : "var(--ink-soft)", marginTop: "0.1rem" }}>
                        {isOld ? (isYang ? "● 老阳" : "○ 老阴") : (isYang ? "少阳" : "少阴")}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 亲手摇 */}
        {shakeMode === "manual" && (
          <div className="space-y-3">
            <p style={{ fontSize: "0.72rem", color: "var(--ink-soft)" }}>
              {lang === "zh"
                ? `逐爻摇卦：点击按钮落定第 ${Math.min(currentYao + 1, 6)} 爻（自下而上）。${currentYao >= 6 ? "六爻全。" : ""}`
                : `Cast one line at a time. Line ${Math.min(currentYao + 1, 6)} of 6.`}
            </p>
            <button type="button" className="paper-btn" onClick={manualToss} disabled={currentYao >= 6}>
              {currentYao >= 6
                ? (lang === "zh" ? "六爻全" : "All 6 Done")
                : (lang === "zh" ? `摇第 ${currentYao + 1} 爻` : `Toss Line ${currentYao + 1}`)}
            </button>
            {/* 已摇爻位 */}
            <div className="space-y-1.5">
              {[...YAO_NAMES].reverse().map((name, ri) => {
                const i = 5 - ri; // 上爻先显示
                const t = tosses[i];
                const isYang = t === "young_yang" || t === "old_yang";
                const isOld = t === "old_yin" || t === "old_yang";
                return (
                  <div key={i} className="flex items-center gap-3 px-3 py-1.5 rounded-sm"
                    style={{ background: t ? "var(--paper-2)" : "transparent", border: t ? "1px solid var(--rule)" : "1px dashed var(--rule)" }}>
                    <span style={{ fontSize: "0.7rem", color: "var(--ink-soft)", minWidth: 36 }}>{name}</span>
                    <span style={{ fontSize: "1.3rem", color: t ? (isYang ? "var(--cinnabar)" : "var(--ink)") : "var(--ink-soft)", fontWeight: isOld ? 700 : 400 }}>
                      {t === null ? "· · ·" : isYang ? "——⚊" : "— ⚋—"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* 第2步：起卦 */}
      {allTossed && !chart && (
        <form onSubmit={submit} className="paper-frame">
          <button type="submit" className="paper-btn" disabled={loading || !question.trim()} style={{ minWidth: 140 }}>
            {loading ? (lang === "zh" ? "起卦中…" : "Computing…") : (lang === "zh" ? "起卦解卦" : "Interpret Hexagram")}
          </button>
          {!question.trim() && (
            <span style={{ fontSize: "0.7rem", color: "var(--cinnabar)", marginLeft: "0.5rem" }}>
              {lang === "zh" ? "请先填写问题" : "Please fill in your question first"}
            </span>
          )}
          {error && <div className="paper-error" style={{ marginTop: "0.5rem" }}>{error}</div>}
        </form>
      )}

      {/* 盘面结果 */}
      {chart && (
        <div className="space-y-5 animate-fade-in">
          {/* 卦名 + 六爻竖排（自下而上: 初→上） */}
          <section className="paper-frame space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 style={{ fontFamily: "'Noto Serif SC', serif", fontSize: "1.2rem", fontWeight: 700, color: "var(--cinnabar)" }}>
                {hexagram || (lang === "zh" ? "本卦" : "Hexagram")}
              </h2>
              {bianGua && (
                <span className="paper-tag" style={{ color: "var(--ink-soft)" }}>
                  {lang === "zh" ? `之 ${bianGua}` : `→ ${bianGua}`}
                </span>
              )}
              {yongshen && (
                <span className="paper-tag" style={{ borderColor: "var(--cinnabar)", color: "var(--cinnabar)" }}>
                  {lang === "zh" ? "用神" : "Yong Shen"}: {yongshen}
                </span>
              )}
            </div>
            <div className="space-y-2">
              {yaos.length > 0 ? yaos.map((yao: any, i: number) => {
                const isYang = yao.is_yang;
                const isDong = yao.is_dong;
                const pos = yao.position || i;
                const name = (pos >= 1 && pos <= 6) ? YAO_NAMES[pos - 1] : `爻${pos}`;
                return (
                  <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-sm"
                    style={{
                      border: `1px solid ${isDong ? "var(--cinnabar)" : "var(--rule)"}`,
                      background: isDong ? "rgba(176,58,46,0.04)" : "var(--paper-2)",
                    }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--ink-soft)", minWidth: 40, fontFamily: "'Noto Serif SC', serif" }}>
                      {name}
                    </span>
                    <span style={{
                      fontSize: "1.4rem",
                      color: isYang ? "var(--cinnabar)" : "var(--ink)",
                      fontWeight: isDong ? 700 : 400,
                      fontFamily: "'Noto Serif SC', serif",
                    }}>
                      {isYang ? "——⚊" : "— ⚋—"}
                    </span>
                    {isDong && (
                      <span style={{ fontSize: "0.62rem", color: "#fff", background: "var(--cinnabar)", padding: "0.05rem 0.35rem", borderRadius: 2, fontFamily: "'JetBrains Mono', monospace" }}>
                        {lang === "zh" ? "动" : "Δ"}
                      </span>
                    )}
                    {/* 装卦信息 */}
                    <div className="flex gap-2 ml-auto flex-wrap" style={{ fontSize: "0.65rem", color: "var(--ink-soft)" }}>
                      {yao.dizhi && <span>{yao.dizhi}</span>}
                      {yao.liuqin && <span style={{ color: "var(--verdigris)" }}>{yao.liuqin}</span>}
                      {yao.liushen && <span style={{ color: "var(--ink-soft)" }}>{yao.liushen}</span>}
                      {yao.shiying && (
                        <span style={{
                          color: yao.shiying === "世" ? "var(--cinnabar)" : "var(--cinnabar)",
                          fontWeight: 600,
                          background: "rgba(176,58,46,0.1)",
                          padding: "0 0.25rem",
                          borderRadius: 2,
                        }}>
                          {yao.shiying}
                        </span>
                      )}
                      {yao.xunkong && <span style={{ color: "#999" }}>空</span>}
                      {yao.yuepo && <span style={{ color: "#c44" }}>破</span>}
                    </div>
                  </div>
                );
              }) : (
                // 如果没有 yao_details，显示简单的六爻
                [0, 1, 2, 3, 4, 5].reverse().map((ri) => {
                  const i = 5 - ri;
                  const t = tosses[i];
                  const isYang = t === "young_yang" || t === "old_yang";
                  const isDong = t === "old_yin" || t === "old_yang";
                  return (
                    <div key={i} className="flex items-center gap-3 px-3 py-1.5 rounded-sm"
                      style={{ border: `1px solid ${isDong ? "var(--cinnabar)" : "var(--rule)"}`, background: "var(--paper-2)" }}>
                      <span style={{ fontSize: "0.72rem", color: "var(--ink-soft)", minWidth: 40 }}>{YAO_NAMES[5 - ri]}</span>
                      <span style={{ fontSize: "1.4rem", color: isYang ? "var(--cinnabar)" : "var(--ink)", fontWeight: isDong ? 700 : 400 }}>
                        {isYang ? "——⚊" : "— ⚋—"}
                      </span>
                      {isDong && (
                        <span style={{ fontSize: "0.62rem", color: "#fff", background: "var(--cinnabar)", padding: "0.05rem 0.35rem", borderRadius: 2 }}>
                          {lang === "zh" ? "动" : "Δ"}
                        </span>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </section>

          {/* 用神断语框 */}
          {yongshenAdvice && (
            <section className="paper-frame" style={{ borderColor: "var(--cinnabar)", borderWidth: "1.5px", background: "rgba(176,58,46,0.03)" }}>
              <div className="paper-eyebrow" style={{ color: "var(--cinnabar)" }}>
                {lang === "zh" ? "用神断语" : "Yong Shen Reading"}
              </div>
              <div style={{ fontSize: "0.88rem", color: "var(--ink)", lineHeight: 1.7, fontFamily: "'Noto Serif SC', serif" }}>
                {yongshenAdvice}
              </div>
              {duan["提示"] && (
                <div style={{ fontSize: "0.72rem", color: "var(--ink-soft)", marginTop: "0.5rem", lineHeight: 1.6 }}>
                  {Array.isArray(duan["提示"]) ? duan["提示"].join("；") : String(duan["提示"])}
                </div>
              )}
            </section>
          )}

          {/* 底部操作栏 */}
          <div className="flex items-center justify-between gap-3 flex-wrap"
            style={{ borderTop: "1px solid var(--rule)", paddingTop: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--ink-soft)", fontFamily: "'JetBrains Mono', monospace" }}>
              engine: {chart.engine} · {chart.elapsed_ms}ms
            </div>
            <div className="flex gap-2">
              <button type="button" className="paper-btn-ghost" onClick={addToBasket}
                style={{ fontSize: "0.78rem" }} disabled={inBasket}>
                {inBasket ? (lang === "zh" ? "已收入卷宗" : "In Docket") : (lang === "zh" ? "收入合参" : "Add to Cross-Ref")}
              </button>
              <button type="button" className="paper-btn" onClick={() => { setChart(null); resetTosses(); }}
                style={{ fontSize: "0.78rem" }}>
                {lang === "zh" ? "重新起卦" : "Recast"}
              </button>
            </div>
          </div>
        </div>
      )}
      <MethodSourcesPanel method="liuyao" />
    </div>
  );
}
