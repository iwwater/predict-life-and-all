// 罗盘采集页 — Sprint 3.1-3.4 升级版
// 三通道输入 (device/physical/manual/map) + 连续采样 + 临界角双候选 + 端到端风水
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { CompassDial } from "../components/CompassDial";
import {
  measureCompass,
  compassFengShui,
  type CompassMeasureResponse,
  type CompassFengShuiResponse,
} from "../lib/api";
import { DIRECTIONS_8, describeSans } from "../lib/compass";
import { COLOR } from "../components/ui";
import { useBirthStore } from "../store/birth";

// ── 常量 ──────────────────────────────────────────────────────────────
const CONTINUOUS_SAMPLE_COUNT = 30; // 连续采样最少次数
const CONTINUOUS_INTERVAL_MS = 300; // 连续采样间隔
const HIGH_DEV_THRESHOLD = 8.0;     // 高波动阈值 (度) — 超过提示复测

type MeasureMode = "single" | "continuous";
type InputChannel = "device" | "manual";

export default function CompassPage() {
  const navigate = useNavigate();
  const birth = useBirthStore((s) => s.birth);

  // 罗盘 dial
  const [direction, setDirection] = useState("正东");
  const [manualDeg, setManualDeg] = useState("");

  // 设备状态
  const [deviceSupported, setDeviceSupported] = useState(false);
  const [azimuth, setAzimuth] = useState<number>(90);
  const [usingManual, setUsingManual] = useState(false);
  const [iosPermGranted, setIosPermGranted] = useState(false);
  const handlerRef = useRef<((e: DeviceOrientationEvent) => void) | null>(null);

  // 测量模式
  const [mode, setMode] = useState<MeasureMode>("single");

  // 连续采样状态
  const [continuousRunning, setContinuousRunning] = useState(false);
  const [continuousSamples, setContinuousSamples] = useState<number[]>([]);
  const [runningMean, setRunningMean] = useState<number>(0);
  const [runningStd, setRunningStd] = useState<number>(0);
  const continuousTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 结果
  const [result, setResult] = useState<CompassMeasureResponse | null>(null);
  const [fengShuiResult, setFengShuiResult] = useState<CompassFengShuiResponse | null>(null);
  const [measuring, setMeasuring] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── 设备罗盘权限 ────────────────────────────────────────────────────

  useEffect(() => {
    const handler = (e: DeviceOrientationEvent) => {
      if (e.alpha !== null && e.alpha !== undefined) {
        setAzimuth(Math.round(e.alpha));
      }
    };
    handlerRef.current = handler;

    const requestPerms = async () => {
      // iOS 13+ 需要用户手势触发 requestPermission
      if (
        typeof DeviceOrientationEvent !== "undefined" &&
        typeof (DeviceOrientationEvent as any).requestPermission === "function"
      ) {
        // iOS: 等待用户点击按钮
        setDeviceSupported(true);
        setUsingManual(true); // 先默认手动，等用户授权
      } else if ("ondeviceorientation" in window) {
        // Android / desktop Chrome
        window.addEventListener("deviceorientation", handler);
        setDeviceSupported(true);
        setUsingManual(false);
      } else {
        setUsingManual(true);
      }
    };
    requestPerms().catch(() => setUsingManual(true));

    return () => {
      if (handlerRef.current) {
        window.removeEventListener("deviceorientation", handlerRef.current);
      }
    };
  }, []);

  // iOS 权限请求 (须用户手势触发)
  const requestIOSPermission = async () => {
    try {
      if (
        typeof (DeviceOrientationEvent as any).requestPermission === "function"
      ) {
        const perm = await (DeviceOrientationEvent as any).requestPermission();
        if (perm === "granted" && handlerRef.current) {
          window.addEventListener("deviceorientation", handlerRef.current);
          setIosPermGranted(true);
          setUsingManual(false);
        }
      }
    } catch {
      setUsingManual(true);
    }
  };

  // ── 单次测量 ──────────────────────────────────────────────────────

  const doSingleMeasure = async () => {
    setMeasuring(true);
    setError(null);
    try {
      const res = await measureCompass({
        magnetic_heading_deg: usingManual || !deviceSupported ? undefined : azimuth,
        manual_azimuth_deg: usingManual ? azimuth : undefined,
        map_direction: direction,
        north_ref: "magnetic",
      });
      setResult(res);
      setFengShuiResult(null);
    } catch (e: any) {
      setError(e.message || "测量失败");
    } finally {
      setMeasuring(false);
    }
  };

  // ── 连续采样 ──────────────────────────────────────────────────────

  const startContinuous = async () => {
    setContinuousRunning(true);
    setContinuousSamples([]);
    setRunningMean(0);
    setRunningStd(0);
    setError(null);

    // 采集第一个样本
    const samples: number[] = [azimuth];
    setContinuousSamples([...samples]);
    updateRunningStats(samples);

    continuousTimerRef.current = setInterval(() => {
      setContinuousSamples((prev) => {
        const next = [...prev, azimuth];
        if (next.length >= CONTINUOUS_SAMPLE_COUNT) {
          stopContinuous(next);
        }
        updateRunningStats(next);
        return next;
      });
    }, CONTINUOUS_INTERVAL_MS);
  };

  const stopContinuous = (finalSamples?: number[]) => {
    if (continuousTimerRef.current) {
      clearInterval(continuousTimerRef.current);
      continuousTimerRef.current = null;
    }
    setContinuousRunning(false);

    const samples = finalSamples || continuousSamples;
    if (samples.length >= 3) {
      // 用所有已采集样本调用 /measure 的 samples 参数
      finishContinuousMeasure(samples);
    }
  };

  const updateRunningStats = (samples: number[]) => {
    if (samples.length < 2) {
      setRunningMean(samples[0] || 0);
      setRunningStd(0);
      return;
    }
    // 环形均值
    const sinSum = samples.reduce((s, d) => s + Math.sin((d * Math.PI) / 180), 0);
    const cosSum = samples.reduce((s, d) => s + Math.cos((d * Math.PI) / 180), 0);
    const mean = ((Math.atan2(sinSum, cosSum) * 180) / Math.PI + 360) % 360;
    const n = samples.length;
    const r = Math.sqrt(sinSum ** 2 + cosSum ** 2) / n;
    const std = r >= 1.0 ? 0 : (Math.sqrt(-2 * Math.log(Math.max(r, 1e-10))) * 180) / Math.PI;
    setRunningMean(Math.round(mean));
    setRunningStd(Math.round(std * 100) / 100);
  };

  const finishContinuousMeasure = async (samples: number[]) => {
    setMeasuring(true);
    try {
      const res = await measureCompass({
        magnetic_heading_deg: usingManual ? undefined : samples[samples.length - 1],
        manual_azimuth_deg: usingManual ? samples[samples.length - 1] : undefined,
        samples,
        north_ref: "magnetic",
      });
      setResult(res);
      setFengShuiResult(null);
    } catch (e: any) {
      setError(e.message || "测量失败");
    } finally {
      setMeasuring(false);
    }
  };

  const manualStopContinuous = () => {
    stopContinuous();
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (continuousTimerRef.current) clearInterval(continuousTimerRef.current);
    };
  }, []);

  // ── 手动角度输入 ──────────────────────────────────────────────────

  const submitManualDeg = () => {
    const deg = parseFloat(manualDeg);
    if (isNaN(deg) || deg < 0 || deg > 360) return;
    setAzimuth(deg);
    setManualDeg("");
    // 在 manual 模式下直接做单次测量
    doSingleMeasureWithDeg(deg);
  };

  const doSingleMeasureWithDeg = async (deg: number) => {
    setMeasuring(true);
    setError(null);
    try {
      const res = await measureCompass({
        manual_azimuth_deg: deg,
        north_ref: "magnetic",
      });
      setResult(res);
      setFengShuiResult(null);
    } catch (e: any) {
      setError(e.message || "测量失败");
    } finally {
      setMeasuring(false);
    }
  };

  // ── 罗盘 → 风水 端到端 (Sprint 3.3) ──────────────────────────────

  const computeFengShui = async () => {
    if (!result) return;
    setMeasuring(true);
    setError(null);
    try {
      const res = await compassFengShui({
        magnetic_heading_deg: result.input_channel === "device" ? result.raw_heading : undefined,
        manual_azimuth_deg: result.input_channel === "manual" ? result.raw_heading : undefined,
        map_direction: result.input_channel === "map" ? result.direction : undefined,
        birth_year: birth.year,
        gender: birth.gender,
        north_ref: "magnetic",
      });
      setFengShuiResult(res);
    } catch (e: any) {
      setError(e.message || "风水计算失败");
    } finally {
      setMeasuring(false);
    }
  };

  // ── 导航 ──────────────────────────────────────────────────────────

  const proceedToCase = () => {
    if (!result) return;
    // 同时存 localStorage (兜底) 和 navigation state (主通道)
    localStorage.setItem("pending_sitting", result.sans);
    if (fengShuiResult) {
      localStorage.setItem("pending_fengshui", JSON.stringify(fengShuiResult));
    }
    navigate("/cases", {
      state: {
        pendingSitting: result.sans,
        pendingFengShui: fengShuiResult,
        pendingDirection: result.direction,
      },
    });
  };

  // ── 当前方位显示 ──────────────────────────────────────────────────

  const displayAzimuth = mode === "continuous" && continuousSamples.length > 0
    ? runningMean
    : azimuth;
  const displayQuality = result?.quality || "low";

  return (
    <div className="max-w-lg mx-auto px-4 py-8 flex flex-col gap-6">

      {/* 标题 */}
      <div>
        <h1 className="font-display text-xl" style={{ color: COLOR.goldBright }}>罗盘采集</h1>
        <p className="text-sm mt-1" style={{ color: COLOR.muted }}>
          {deviceSupported && !usingManual
            ? "手机罗盘已就绪"
            : iosPermGranted
              ? "iOS 罗盘已授权"
              : "使用手动输入方位"}
        </p>
      </div>

      {/* iOS 权限按钮 (仅 iOS 13+ 需要) */}
      {deviceSupported && usingManual && !iosPermGranted && (
        <button
          onClick={requestIOSPermission}
          className="w-full py-3 rounded text-sm font-medium"
          style={{ background: COLOR.cinnabar, color: "white" }}
        >
          启用手机罗盘 (需授权)
        </button>
      )}

      {/* 罗盘 dial */}
      <div className="flex justify-center">
        <CompassDial
          value={direction}
          onChange={(code) => {
            setDirection(code);
            const dir8 = DIRECTIONS_8.find((d) => d.code === code);
            if (dir8 && usingManual) {
              setAzimuth(DIRECTIONS_8.indexOf(dir8) * 45);
            }
          }}
          show24
          size={260}
        />
      </div>

      {/* 当前读数 */}
      <div className="text-center">
        <span className="text-3xl font-display" style={{ color: COLOR.gold }}>
          {displayAzimuth}°
        </span>
        <span className="text-sm ml-2" style={{ color: COLOR.muted }}>
          {describeSans(result?.sans || DIRECTIONS_8.find((d) => d.code === direction)?.sans || "卯")}
        </span>
        {/* 八字信息 */}
        {result && (
          <div className="text-xs mt-1" style={{ color: COLOR.goldDim }}>
            {result.trigram}卦 · {result.element} · {result.sans_zh}
          </div>
        )}
      </div>

      {/* 模式切换 */}
      <div className="flex gap-2 justify-center">
        <button
          onClick={() => { setMode("single"); setContinuousRunning(false); }}
          className="px-4 py-1.5 rounded text-xs font-medium"
          style={{
            background: mode === "single" ? "rgba(201,162,75,0.15)" : "transparent",
            border: `1px solid ${mode === "single" ? COLOR.goldDim : "var(--rule)"}`,
            color: mode === "single" ? COLOR.goldBright : COLOR.inkSoft,
          }}
        >
          单次测量
        </button>
        <button
          onClick={() => setMode("continuous")}
          className="px-4 py-1.5 rounded text-xs font-medium"
          style={{
            background: mode === "continuous" ? "rgba(201,162,75,0.15)" : "transparent",
            border: `1px solid ${mode === "continuous" ? COLOR.goldDim : "var(--rule)"}`,
            color: mode === "continuous" ? COLOR.goldBright : COLOR.inkSoft,
          }}
        >
          连续采样 (≥{CONTINUOUS_SAMPLE_COUNT}次)
        </button>
      </div>

      {/* 操作区 */}
      <div className="flex flex-col gap-3">
        {mode === "single" ? (
          <>
            {/* 手动输入框 */}
            {usingManual && (
              <div className="flex gap-2">
                <input
                  type="number" min="0" max="360" placeholder="0-360°"
                  value={manualDeg}
                  onChange={(e) => setManualDeg(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") submitManualDeg(); }}
                  className="flex-1 px-3 py-2 rounded text-sm"
                  style={{ background: "var(--paper)", border: `1px solid var(--rule)`, color: COLOR.ink }}
                />
                <button
                  onClick={submitManualDeg}
                  className="px-4 py-2 rounded text-sm font-medium"
                  style={{ background: COLOR.cinnabar, color: "white" }}
                >
                  记录
                </button>
              </div>
            )}
            <button
              onClick={doSingleMeasure}
              disabled={measuring}
              className="w-full py-3 rounded text-sm font-medium disabled:opacity-50"
              style={{ background: COLOR.cinnabar, color: "white" }}
            >
              {measuring ? "测量中..." : usingManual
                ? `测量 ${azimuth}°`
                : `测量当前方位 (${azimuth}°)`}
            </button>
          </>
        ) : (
          <>
            {/* 连续采样控制 */}
            {!continuousRunning ? (
              <button
                onClick={startContinuous}
                disabled={measuring}
                className="w-full py-3 rounded text-sm font-medium disabled:opacity-50"
                style={{ background: COLOR.cinnabar, color: "white" }}
              >
                开始连续采样 (每 {CONTINUOUS_INTERVAL_MS}ms, 共 {CONTINUOUS_SAMPLE_COUNT} 次)
              </button>
            ) : (
              <button
                onClick={manualStopContinuous}
                className="w-full py-3 rounded text-sm font-medium"
                style={{ background: "var(--cinnabar-dim)", color: "white" }}
              >
                停止采样 ({continuousSamples.length}/{CONTINUOUS_SAMPLE_COUNT})
              </button>
            )}

            {/* 连续采样实时统计 */}
            {continuousSamples.length > 0 && (
              <div
                className="p-3 rounded text-xs"
                style={{ background: "rgba(201,162,75,0.05)", border: `1px solid var(--rule)` }}
              >
                <div className="flex justify-between mb-1">
                  <span style={{ color: COLOR.muted }}>已采集</span>
                  <span style={{ color: COLOR.ink }}>{continuousSamples.length} 次</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span style={{ color: COLOR.muted }}>环形均值</span>
                  <span style={{ color: COLOR.gold }}>{runningMean}°</span>
                </div>
                <div className="flex justify-between mb-1">
                  <span style={{ color: COLOR.muted }}>标准差</span>
                  <span style={{
                    color: runningStd > HIGH_DEV_THRESHOLD ? COLOR.cinnabar : COLOR.ink,
                  }}>
                    {runningStd}°
                  </span>
                </div>
                {runningStd > HIGH_DEV_THRESHOLD && (
                  <div className="mt-2 py-1.5 px-2 rounded text-xs font-medium" style={{
                    background: "rgba(229,88,60,0.1)",
                    color: COLOR.cinnabar,
                  }}>
                    ⚠ 波动较大 (σ &gt; {HIGH_DEV_THRESHOLD}°)，建议远离金属/电器后复测
                  </div>
                )}
                {/* 进度条 */}
                <div className="mt-2 h-1 rounded-full" style={{ background: "var(--rule)" }}>
                  <div
                    className="h-1 rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(100, (continuousSamples.length / CONTINUOUS_SAMPLE_COUNT) * 100)}%`,
                      background: COLOR.gold,
                    }}
                  />
                </div>
              </div>
            )}
          </>
        )}

        {/* 错误提示 */}
        {error && (
          <div className="p-3 rounded text-xs" style={{ background: "rgba(229,88,60,0.08)", color: COLOR.cinnabar }}>
            {error}
          </div>
        )}

        {/* ── 罗盘结果 ── */}
        {result && (
          <div
            className="mt-2 p-4 rounded flex flex-col gap-2"
            style={{ background: "rgba(201,162,75,0.08)", border: `1px solid ${COLOR.goldDim}` }}
          >
            {/* 质量 + 通道 */}
            <div className="flex justify-between items-center">
              <span className="text-xs" style={{ color: COLOR.muted }}>
                通道: {result.input_channel} · 北基准: {result.north_ref}
              </span>
              <span
                className="px-2 py-0.5 rounded text-xs font-medium"
                style={{
                  background: result.quality === "high"
                    ? "rgba(72,199,142,0.15)"
                    : result.quality === "medium"
                      ? "rgba(201,162,75,0.15)"
                      : "rgba(229,88,60,0.15)",
                  color: result.quality === "high" ? "#48c78e" : result.quality === "medium" ? COLOR.gold : COLOR.cinnabar,
                }}
              >
                {result.quality === "high" ? "高精度" : result.quality === "medium" ? "中精度" : "低精度"}
              </span>
            </div>

            {/* 坐山结果 */}
            <div className="text-center">
              <div className="text-2xl font-display" style={{ color: COLOR.goldBright }}>
                {result.sans_zh}
              </div>
              <div className="text-sm mt-1" style={{ color: COLOR.inkSoft }}>
                真北 {result.true_heading}° · {result.direction} · {result.trigram}卦
              </div>
              <div className="text-xs mt-1" style={{ color: COLOR.muted }}>
                磁偏角 {result.declination_deg}° ({result.declination_source})
              </div>
            </div>

            {/* 临界角双候选 */}
            {result.dual_candidate && (
              <div
                className="mt-1 p-2 rounded text-xs font-medium"
                style={{ background: "rgba(229,88,60,0.08)", color: COLOR.cinnabar }}
              >
                ⚠ 临界角: 距山界仅 {result.distance_to_boundary}° (阈值 5°)
                <br />
                候选: {result.sans}/{result.alt_sans} — 建议远离金属/电器后复测
              </div>
            )}

            {/* 风水提示 */}
            {result.tip && (
              <div className="text-xs" style={{ color: COLOR.inkSoft }}>
                💡 {result.tip}
              </div>
            )}

            {/* fengshui_warning */}
            {result.fengshui_warning && (
              <div className="text-xs italic" style={{ color: COLOR.cinnabar }}>
                {result.fengshui_warning}
              </div>
            )}
          </div>
        )}

        {/* ── 风水端到端结果 (Sprint 3.3) ── */}
        {result && !fengShuiResult && (
          <button
            onClick={computeFengShui}
            disabled={measuring}
            className="w-full py-2 rounded text-sm font-medium disabled:opacity-50"
            style={{ background: "rgba(201,162,75,0.12)", border: `1px solid ${COLOR.goldDim}`, color: COLOR.goldBright }}
          >
            {measuring ? "计算中..." : "计算风水 (八宅+玄空) →"}
          </button>
        )}

        {fengShuiResult && (
          <div
            className="mt-2 p-4 rounded flex flex-col gap-2"
            style={{ background: "rgba(201,162,75,0.06)", border: `1px solid ${COLOR.goldDim}` }}
          >
            <div className="text-sm font-medium" style={{ color: COLOR.goldBright }}>
              风水综合评估
            </div>
            <div className="text-sm" style={{ color: COLOR.inkSoft }}>
              {fengShuiResult.fengshui_summary}
            </div>
            {fengShuiResult.bazhai && (
              <div className="text-xs" style={{ color: COLOR.muted }}>
                八宅: 命卦 {fengShuiResult.bazhai.命卦 || "N/A"} · 吉方 {fengShuiResult.bazhai.吉方?.join("、") || "待定"}
              </div>
            )}
            {fengShuiResult.xuankong && (
              <div className="text-xs" style={{ color: COLOR.muted }}>
                玄空: {fengShuiResult.xuankong.格局 || "待定"} · 运 {fengShuiResult.xuankong.运 || "N/A"}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 底部导航 */}
      <div className="flex gap-3 mt-4">
        <button
          onClick={() => navigate(-1)}
          className="flex-1 py-3 rounded text-sm"
          style={{ border: `1px solid var(--rule)`, color: COLOR.inkSoft }}
        >
          返回
        </button>
        <button
          onClick={proceedToCase}
          disabled={!result}
          className="flex-1 py-3 rounded text-sm font-medium disabled:opacity-40"
          style={{ background: result ? COLOR.cinnabar : "transparent", color: "white" }}
        >
          用此坐向继续 →
        </button>
      </div>
    </div>
  );
}
