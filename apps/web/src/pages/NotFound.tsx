// 404 神秘错误页 — 西方星座 + 东方八卦融合
import { Link } from "react-router-dom";
import { COLOR } from "../components/ui";
import { YinYang, ZodiacRing, StarArray, MetatronCube } from "../components/MysticElements";

export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden>
        {/* 星座环 — 左上 */}
        <div className="absolute -left-20 -top-10 opacity-[0.06] spin-slow-rev">
          <ZodiacRing size={300} />
        </div>
        {/* 梅塔特隆立方体 — 右下 */}
        <div className="absolute -right-16 -bottom-16 opacity-[0.05] spin-slow">
          <MetatronCube size={280} />
        </div>
        {/* 太极 — 中央背景 */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.04] yinyang-breathe">
          <YinYang size={260} />
        </div>
        {/* 星辰阵列 — 底部 */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 opacity-[0.12]">
          <StarArray count={7} size={20} />
        </div>
      </div>

      {/* 主体内容 */}
      <div className="relative z-10 space-y-5">
        {/* 神秘编号 */}
        <div
          className="text-8xl sm:text-9xl font-display text-shimmer select-none"
          style={{ fontFamily: "'Cinzel', serif", lineHeight: 1 }}
        >
          4♇4
        </div>

        {/* 东西方释义 */}
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <span
            className="text-[10px] uppercase tracking-[0.3em] px-3 py-1 rounded-full"
            style={{
              background: "rgba(79,179,160,0.10)",
              border: "1px solid rgba(79,179,160,0.30)",
              color: COLOR.jade,
            }}
          >
            无明 · Avidyā
          </span>
          <span
            className="text-[10px] uppercase tracking-[0.3em] px-3 py-1 rounded-full"
            style={{
              background: "rgba(91,141,239,0.10)",
              border: "1px solid rgba(91,141,239,0.30)",
              color: COLOR.azure,
            }}
          >
            Void · 虚空
          </span>
        </div>

        <h1
          className="text-2xl sm:text-3xl font-display"
          style={{ color: COLOR.goldBright }}
        >
          此页不在命盘之中
        </h1>

        <p className="text-sm max-w-md mx-auto leading-relaxed" style={{ color: COLOR.inkSoft }}>
          你所寻之境不在八卦之内，亦不落黄道十二宫。<br />
          或许是星象偏移，或许是卦爻未成——请折返，另寻他途。
        </p>

        {/* 返回链接组 */}
        <div className="flex items-center justify-center gap-3 pt-4">
          <Link
            to="/"
            className="btn-primary gold-sweep-host text-sm px-6 py-3"
          >
            ✦ 返回首页
          </Link>
          <Link
            to="/cast"
            className="btn-ghost text-sm px-5 py-3"
            style={{ borderColor: COLOR.goldDim, color: COLOR.goldBright }}
          >
            排盘问事 →
          </Link>
        </div>

        {/* 底部卦辞 */}
        <div className="pt-6">
          <div className="text-xs opacity-30" style={{ color: COLOR.muted }}>
            「眇能视，跛能履，履虎尾，咥人，凶」——《易·履卦》
          </div>
        </div>
      </div>
    </div>
  );
}
