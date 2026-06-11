// 古籍×仪器 布局:侧边栏 + 顶部栏 + 主内容 + 凡例式页脚
import { Outlet, useLocation } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { Sidebar } from "./Sidebar";
import { COLOR } from "./ui";
import { useI18n } from "../lib/i18n";

export function Layout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { t, lang, toggle: toggleLang } = useI18n();

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
    <div className="min-h-full flex paper-page">
      {/* 侧边栏 */}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* 主区域 */}
      <div className="flex-1 flex flex-col min-h-full lg:ml-[232px]">
        {/* 顶部栏 — 界格线底边, 无毛玻璃 */}
        <header
          className="sticky top-0 z-30 flex items-center h-12"
          style={{
            background: "var(--paper)",
            borderBottom: "1px solid var(--rule)",
          }}
        >
          <div className="flex-1 flex items-center justify-between px-4 sm:px-6">
            {/* 左侧:汉堡 + 面包屑 */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="lg:hidden flex items-center justify-center w-8 h-8"
                style={{ color: "var(--ink-soft)", fontFamily: "'Noto Serif SC', serif" }}
                onClick={toggleSidebar}
                aria-label={sidebarOpen ? "关闭侧栏" : "打开侧栏"}
              >
                <span style={{ fontSize: "1.1rem" }}>{sidebarOpen ? "✕" : "☰"}</span>
              </button>
              <Breadcrumb pathname={location.pathname} />
            </div>

            {/* 右侧:语言切换 + 标识 */}
            <div className="flex items-center gap-3 text-xs" style={{ color: "var(--ink-soft)" }}>
              <button
                type="button"
                onClick={toggleLang}
                className="paper-tag"
                style={{ cursor: "pointer", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.65rem" }}
              >
                {lang === "zh" ? "EN" : "中"}
              </button>
              <span className="hidden sm:inline" style={{ fontFamily: "'Noto Serif SC', serif", letterSpacing: "0.08em" }}>
                {t("app.name")} · {t("app.tagline").split(" · ")[0]}
              </span>
            </div>
          </div>
        </header>

        {/* 主内容 */}
        <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 py-5 animate-fade-in">
          <Outlet />
        </main>

        {/* Footer — 凡例样式 */}
        <footer
          className="mt-auto"
          style={{ borderTop: "1px solid var(--rule)" }}
        >
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5">
            <div className="paper-fanli">
              <div className="paper-fanli-title">凡 例</div>
              <p>{t("app.disclaimer")}</p>
              <p style={{ marginTop: "0.5rem" }}>{t("app.compliance")}</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

// 面包屑:从路径推导
function Breadcrumb({ pathname }: { pathname: string }) {
  const { t, lang } = useI18n();
  const crumbs: { label: string; to?: string }[] = [];

  if (pathname === "/") {
    crumbs.push({ label: t("nav.home") });
  } else if (pathname.startsWith("/m/")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    const m = pathname.replace("/m/", "");
    const labels: Record<string, string> = {
      bazi: t("nav.bazi"), ziwei: t("nav.ziwei"), qimen: "奇门遁甲",
      liuyao: t("nav.liuyao"), meihua: t("nav.meihua"), chenggu: t("nav.chenggu"),
      western: t("nav.western"), vedic: t("nav.vedic"),
      tarot: t("nav.tarot"), numerology: t("nav.numerology"),
      xuankong: t("nav.xuankong"), bazhai: t("nav.bazhai"),
      hepan: lang === "zh" ? "合盘" : "Synastry",
    };
    crumbs.push({ label: labels[m] || m });
  } else if (pathname.startsWith("/heshen")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: lang === "zh" ? "合参" : "Cross-Reference" });
  } else if (pathname.startsWith("/method/")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    const m = pathname.replace("/method/", "");
    const labels: Record<string, string> = {
      bazi: t("nav.bazi"), "bazi-v2": t("nav.baziV2"), ziwei: t("nav.ziwei"), qimen: "奇门遁甲",
      liuyao: t("nav.liuyao"), meihua: t("nav.meihua"), chenggu: t("nav.chenggu"),
      liuren: t("nav.liuren"), tieban: t("nav.tieban"), xiaoliuren: t("nav.xiaoliuren"),
      western: t("nav.western"), vedic: t("nav.vedic"),
      tarot: t("nav.tarot"), lenormand: t("nav.lenormand"), numerology: t("nav.numerology"),
      xuankong: t("nav.xuankong"), bazhai: t("nav.bazhai"),
    };
    crumbs.push({ label: labels[m] || m });
  } else if (pathname.startsWith("/aggregate")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: t("nav.aggregate") });
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
  } else if (pathname.startsWith("/result-sample")) {
    crumbs.push({ label: t("nav.home"), to: "/" });
    crumbs.push({ label: lang === "zh" ? "风格样张" : "Style Sample" });
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
    <nav className="flex items-center gap-1.5 text-xs" style={{ color: "var(--ink-soft)" }} aria-label="面包屑">
      {crumbs.map((c, i) => (
        <span key={i} className="flex items-center gap-1.5" style={{ fontFamily: "'Noto Serif SC', serif" }}>
          {i > 0 && <span style={{ color: "var(--rule)" }}>/</span>}
          {c.to ? (
            <a href={c.to} className="paper-link" style={{ fontSize: "0.75rem", borderBottom: "none" }}>
              {c.label}
            </a>
          ) : (
            <span style={{ color: "var(--cinnabar)", fontWeight: 600 }}>{c.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
