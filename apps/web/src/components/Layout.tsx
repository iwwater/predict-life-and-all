// 侧边栏 + 顶部精简栏 + 主内容区布局 + 奢华氛围
import { Outlet, useLocation } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { Starfield, GoldDust } from "./Interactions";
import { Sidebar } from "./Sidebar";
import { COLOR } from "./ui";
import { StarArray, PlanetSymbols } from "./MysticElements";
import { useI18n } from "../lib/i18n";

export function Layout() {
  const location = useLocation();
  const [showStars, setShowStars] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { t, lang, toggle: toggleLang } = useI18n();

  // Starfield + GoldDust 只在首页/排盘/结果显示
  useEffect(() => {
    setShowStars(["/", "/cast", "/result", "/reading"].some(
      (p) => location.pathname === p || location.pathname.startsWith(p + "/")
    ));
  }, [location.pathname]);

  // Close sidebar on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const toggleSidebar = useCallback(() => setSidebarOpen((v) => !v), []);

  return (
    <div className="min-h-full flex">
      {/* 星空背景 */}
      {showStars && (
        <div className="fixed inset-0 z-0 pointer-events-none" aria-hidden>
          <Starfield count={55} />
          {/* 金尘氛围粒子 */}
          <GoldDust count={20} />
          {/* 星辰阵列 (玄学元素) */}
          <div className="absolute inset-0">
            <StarArray count={9} size={20} />
          </div>
        </div>
      )}

      {/* 侧边栏 */}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* 主区域 */}
      <div className="flex-1 flex flex-col min-h-full lg:ml-[248px]">
        {/* 顶部精简栏 */}
        <header
          className="sticky top-0 z-30 backdrop-blur-md border-b h-12 flex items-center"
          style={{
            background: "rgba(8, 10, 15, 0.82)",
            borderColor: COLOR.line,
            boxShadow: `0 1px 0 0 ${COLOR.lineSoft}`,
          }}
        >
          {/* 顶部栏底部微光 */}
          <div
            className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
            style={{
              background: `linear-gradient(90deg, transparent 0%, ${COLOR.goldDim}20 20%, ${COLOR.goldBright}30 50%, ${COLOR.goldDim}20 80%, transparent 100%)`,
            }}
          />

          <div className="flex-1 flex items-center justify-between px-4 sm:px-6 relative">
            {/* 左侧:汉堡 + 面包屑 */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="lg:hidden flex items-center justify-center w-8 h-8 rounded-md tap transition-colors"
                style={{ color: COLOR.inkSoft, background: "rgba(255,255,255,0.04)" }}
                onClick={toggleSidebar}
                aria-label={sidebarOpen ? "关闭侧栏" : "打开侧栏"}
              >
                <span className="text-sm">{sidebarOpen ? "✕" : "☰"}</span>
              </button>
              <Breadcrumb pathname={location.pathname} />
            </div>

            {/* 右侧:语言切换 + 装饰性标识 + 行星符号 */}
            <div className="flex items-center gap-2 text-xs" style={{ color: COLOR.muted }}>
              <PlanetSymbols size={11} className="hidden lg:flex opacity-40" />
              {/* 语言切换按钮 */}
              <button
                type="button"
                onClick={toggleLang}
                className="tap px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider transition-all"
                style={{
                  background: "rgba(201,162,75,0.10)",
                  border: `1px solid ${COLOR.goldDim}60`,
                  color: COLOR.goldBright,
                }}
                title={lang === "zh" ? "Switch to English" : "切换到中文"}
              >
                {t("lang.switch")}
              </button>
              <span
                className="hidden sm:inline-block w-1.5 h-1.5 rounded-full glow-breathe"
                style={{ background: COLOR.gold, boxShadow: `0 0 6px ${COLOR.gold}` }}
              />
              <span className="hidden sm:inline tracking-wide" style={{ color: COLOR.inkSoft }}>
                {t("app.name")} · {t("app.tagline").split(" · ")[0]}
              </span>
            </div>
          </div>
        </header>

        {/* 主内容 (带页面过渡) */}
        <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 py-6 relative z-10 page-enter">
          <Outlet />
        </main>

        {/* Footer */}
        <footer
          className="border-t mt-auto relative z-10"
          style={{
            background: `linear-gradient(180deg, rgba(8,10,15,0.4) 0%, rgba(8,10,15,0.7) 100%)`,
            borderColor: COLOR.line,
          }}
        >
          {/* Footer 顶部金线 */}
          <div
            className="h-px"
            style={{
              background: `linear-gradient(90deg, transparent 10%, ${COLOR.goldDim}40 30%, ${COLOR.gold}50 50%, ${COLOR.goldDim}40 70%, transparent 90%)`,
            }}
          />
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 text-xs space-y-2" style={{ color: COLOR.muted }}>
            <p>{t("app.disclaimer")}</p>
            <p>{t("app.compliance")}</p>
          </div>
        </footer>
      </div>
    </div>
  );
}

// 面包屑:从路径推导 (bilingual)
function Breadcrumb({ pathname }: { pathname: string }) {
  const { t, lang } = useI18n();
  const crumbs: { label: string; to?: string }[] = [];

  if (pathname === "/") {
    crumbs.push({ label: t("nav.home") });
  } else if (pathname.startsWith("/cast")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.cast") });
  } else if (pathname.startsWith("/reading")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: "12法合参" });
  } else if (pathname.startsWith("/compatibility")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.compatibility") });
  } else if (pathname.startsWith("/result")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.cast"), to: "/cast" });
    crumbs.push({ label: lang === "zh" ? "结果" : "Result" });
  } else if (pathname.startsWith("/daily")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.daily") });
  } else if (pathname.startsWith("/almanac")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.almanac") });
  } else if (pathname.startsWith("/fengshui")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.fengshui") });
  } else if (pathname.startsWith("/history")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.history") });
  } else if (pathname.startsWith("/reading-history")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: "报告历史" });
  } else if (pathname.startsWith("/about")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.about") });
  } else if (pathname.startsWith("/dateselect")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.dateselect") });
  } else if (pathname.startsWith("/knowledge")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.knowledge") });
  } else if (pathname.startsWith("/methods")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: lang === "zh" ? "术数详情" : "Method Info" });
  } else {
    crumbs.push({ label: t("nav.home"), to: "/" });
  }

  return (
    <nav className="flex items-center gap-1.5 text-xs" style={{ color: COLOR.muted }} aria-label="面包屑">
      {crumbs.map((c, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <span style={{ color: COLOR.line }}>/</span>}
          {c.to ? (
            <a href={c.to} className="hover:underline transition-colors" style={{ color: COLOR.inkSoft }}>
              {c.label}
            </a>
          ) : (
            <span style={{ color: COLOR.goldBright }}>{c.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
