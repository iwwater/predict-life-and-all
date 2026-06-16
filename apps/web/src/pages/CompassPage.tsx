// 罗盘采集页：手机罗盘/手动输入 → 24 山 → 接入 space 数据
import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { CompassDial } from "../components/CompassDial";
import {
  createCompassSession, addCompassSample, getCompassSession,
  convertAzimuth, type CompassSession,
} from "../lib/api";
import { DIRECTIONS_8, describeSans } from "../lib/compass";
import { COLOR } from "../components/ui";

export default function CompassPage() {
  const navigate = useNavigate();
  const [direction, setDirection] = useState("正东");
  const [manualDeg, setManualDeg] = useState("");
  const [session, setSession] = useState<CompassSession | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [samples, setSamples] = useState<number[]>([]);
  const [compassResult, setCompassResult] = useState<string>("");
  const [resultAzimuth, setResultAzimuth] = useState<number>(0);
  const [quality, setQuality] = useState<"high" | "medium" | "low">("low");
  const [deviceSupported, setDeviceSupported] = useState(false);
  const [azimuth, setAzimuth] = useState<number>(90);
  const [usingManual, setUsingManual] = useState(false);
  const handlerRef = useRef<((e: DeviceOrientationEvent) => void) | null>(null);

  // 请求罗盘权限 & 监听
  useEffect(() => {
    const handler = (e: DeviceOrientationEvent) => {
      if (e.alpha !== null) {
        // alpha = 磁北偏角 (0-360)
        setAzimuth(Math.round(e.alpha));
      }
    };
    handlerRef.current = handler;

    const requestPerms = async () => {
      if (typeof DeviceOrientationEvent !== "undefined" &&
          typeof (DeviceOrientationEvent as any).requestPermission === "function") {
        try {
          const perm = await (DeviceOrientationEvent as any).requestPermission();
          if (perm === "granted") {
            window.addEventListener("deviceorientation", handler);
            setDeviceSupported(true);
          }
        } catch {
          setUsingManual(true);
        }
      } else if ("ondeviceorientation" in window) {
        window.addEventListener("deviceorientation", handler);
        setDeviceSupported(true);
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

  // 开始采样会话
  const startSession = async (dir: string) => {
    const s = await createCompassSession(`${dir}向`);
    setSession(s);
    setSessionId(s.session_id);
    setSamples([]);
  };

  // 记录当前方位
  const recordSample = useCallback(async (deg: number) => {
    if (!sessionId) return;
    const result = await addCompassSample(sessionId, deg);
    setSamples((prev) => [...prev, deg]);
    if (result.closed) {
      const updated = await getCompassSession(sessionId);
      setCompassResult(updated.result_sans);
      setResultAzimuth(updated.result_azimuth);
      setQuality(updated.quality);
    }
    return result;
  }, [sessionId]);

  // 手动输入方位
  const submitManual = async () => {
    const deg = parseFloat(manualDeg);
    if (isNaN(deg) || deg < 0 || deg > 360) return;
    setAzimuth(deg);
    if (!sessionId) {
      await startSession(DIRECTIONS_8.find((d) => d.code === direction)?.code || "正东");
    }
    await recordSample(deg);
    setManualDeg("");
  };

  // 把当前罗盘方位用于自动记录
  const recordCurrent = async () => {
    if (!sessionId) {
      await startSession(direction);
    }
    await recordSample(azimuth);
  };

  const proceed = () => {
    if (!compassResult) return;
    // 存到 localStorage，下一个 reading flow 读取
    localStorage.setItem("pending_sitting", compassResult);
    navigate("/cases/new");
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-8 flex flex-col gap-6">

      {/* 标题 */}
      <div>
        <h1 className="font-display text-xl" style={{ color: COLOR.goldBright }}>罗盘采集</h1>
        <p className="text-sm mt-1" style={{ color: COLOR.muted }}>
          {deviceSupported ? "手机罗盘已就绪，点击「记录」记录当前方位" : "使用手动输入方位"}
        </p>
      </div>

      {/* 罗盘 dial */}
      <div className="flex justify-center">
        <CompassDial value={direction} onChange={(code) => {
          setDirection(code);
          const dir8 = DIRECTIONS_8.find((d) => d.code === code);
          if (dir8) {
            setAzimuth(DIRECTIONS_8.indexOf(dir8) * 45);
          }
        }} show24 size={260} />
      </div>

      {/* 当前读数 */}
      <div className="text-center">
        <span className="text-3xl font-display" style={{ color: COLOR.gold }}>
          {usingManual ? "—" : `${azimuth}°`}
        </span>
        <span className="text-sm ml-2" style={{ color: COLOR.muted }}>
          {describeSans(DIRECTIONS_8.find((d) => d.code === direction)?.sans || "卯")}
        </span>
      </div>

      {/* 操作区 */}
      <div className="flex flex-col gap-3">
        {!usingManual ? (
          <button
            onClick={recordCurrent}
            className="w-full py-3 rounded text-sm font-medium"
            style={{ background: COLOR.cinnabar, color: "white" }}
          >
            记录当前方位 ({azimuth}°)
          </button>
        ) : (
          <div className="flex gap-2">
            <input
              type="number" min="0" max="360" placeholder="0-360°"
              value={manualDeg}
              onChange={(e) => setManualDeg(e.target.value)}
              className="flex-1 px-3 py-2 rounded text-sm"
              style={{ background: "var(--paper)", border: `1px solid var(--rule)`, color: COLOR.ink }}
            />
            <button
              onClick={submitManual}
              className="px-4 py-2 rounded text-sm font-medium"
              style={{ background: COLOR.cinnabar, color: "white" }}
            >
              记录
            </button>
          </div>
        )}

        {/* 采样历史 */}
        {samples.length > 0 && (
          <div className="text-xs" style={{ color: COLOR.muted }}>
            已记录 {samples.length} 次: {samples.map((s) => `${s}°`).join(" · ")}
          </div>
        )}

        {/* 结果 */}
        {compassResult && (
          <div
            className="mt-2 p-4 rounded text-center"
            style={{ background: "rgba(201,162,75,0.08)", border: `1px solid ${COLOR.goldDim}` }}
          >
            <div className="text-xs mb-1" style={{ color: COLOR.muted }}>
              结算结果 · 质量: {quality}
            </div>
            <div className="text-2xl font-display" style={{ color: COLOR.goldBright }}>
              {compassResult}山
            </div>
            <div className="text-sm mt-1" style={{ color: COLOR.inkSoft }}>
              {resultAzimuth}° · {describeSans(compassResult)}
            </div>
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
          onClick={proceed}
          disabled={!compassResult}
          className="flex-1 py-3 rounded text-sm font-medium disabled:opacity-40"
          style={{ background: compassResult ? COLOR.cinnabar : "transparent", color: "white" }}
        >
          用此坐向继续 →
        </button>
      </div>
    </div>
  );
}
