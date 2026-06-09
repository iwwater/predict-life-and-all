// 侧边栏导航: 中西合璧分类 + 移动端抽屉 + 华美装饰
import { NavLink, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { COLOR } from "./ui";
import { PlanetSymbols, YinYang } from "./MysticElements";
import { useI18n } from "../lib/i18n";

export interface NavItem {
  to: string;
  label: string;
  icon: string;
}

export interface NavSection {
  label?: string;
  items: NavItem[];
  accent?: string; // CSS color for section accent
}

function isActiveLink(to: string, pathname: string, search: string): boolean {
  const [path, qs] = to.split("?");
  if (path === "/") return pathname === "/";
  if (pathname !== path && !pathname.startsWith(path + "/")) return false;
  if (path === "/cast" && !qs) return pathname.startsWith("/cast");
  if (qs) {
    const targetParams = new URLSearchParams(qs);
    const currentParams = new URLSearchParams(search);
    const targetMethods = targetParams.get("methods");
    const currentMethods = currentParams.get("methods");
    if (targetMethods && currentMethods) {
      return currentMethods === targetMethods;
    }
    return false;
  }
  return true;
}

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation();
  const { t } = useI18n();

  const SECTIONS: NavSection[] = [
    {
      items: [
        { to: "/", label: t("nav.home"), icon: "🏠" },
      ],
    },
    {
      label: "聚合解读",
      accent: COLOR.gold,
      items: [
        { to: "/reading", label: "12法合参", icon: "🔮" },
        { to: "/reading-history", label: "报告历史", icon: "📋" },
      ],
    },
    {
      label: t("section.east"),
      accent: COLOR.jade,
      items: [
        { to: "/cast", label: t("nav.cast"), icon: "📜" },
        { to: "/daily", label: t("nav.daily"), icon: "☀️" },
        { to: "/almanac", label: t("nav.almanac"), icon: "📅" },
        { to: "/dateselect", label: t("nav.dateselect"), icon: "🗓️" },
        { to: "/fengshui", label: t("nav.fengshui"), icon: "🧭" },
      ],
    },
    {
      label: t("section.west"),
      accent: COLOR.azure,
      items: [
        { to: "/cast?methods=tarot&spread=celtic_cross", label: t("nav.tarot"), icon: "🃏" },
        { to: "/cast?methods=western", label: t("nav.astrology"), icon: "✨" },
        { to: "/cast?methods=numerology", label: t("nav.numerology"), icon: "🔢" },
      ],
    },
    {
      label: t("section.compat"),
      accent: COLOR.goldBright,
      items: [
        { to: "/compatibility", label: t("nav.compatibility"), icon: "💞" },
      ],
    },
    {
      label: t("section.more"),
      items: [
        { to: "/knowledge", label: t("nav.knowledge"), icon: "📖" },
        { to: "/history", label: t("nav.history"), icon: "📋" },
        { to: "/about", label: t("nav.about"), icon: "ℹ️" },
      ],
    },
  ];

  useEffect(() => {
    onClose();
  }, [location.pathname, location.search]);

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 lg:hidden sidebar-backdrop-enter"
          style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(3px)" }}
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={[
          "fixed inset-y-0 left-0 z-50 w-[248px] flex flex-col border-r overflow-y-auto",
          "transition-transform duration-300 ease-out",
          "lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        ].join(" ")}
        style={{
          background: `linear-gradient(180deg, ${COLOR.bgDeep} 0%, #0C1018 40%, ${COLOR.surface} 100%)`,
          borderColor: COLOR.line,
        }}
      >
        {/* Subtle ambient glow at top */}
        <div
          className="absolute top-0 left-0 right-0 h-32 pointer-events-none"
          style={{
            background: `radial-gradient(ellipse at 50% 0%, rgba(201,162,75,0.06) 0%, transparent 70%)`,
          }}
        />

        {/* Logo */}
        <NavLink
          to="/"
          className="relative flex items-center gap-2 px-5 h-16 shrink-0 tap group"
          onClick={onClose}
          style={{ borderBottom: `1px solid ${COLOR.lineSoft}` }}
        >
          {/* Logo glow ring */}
          <span className="relative flex items-center justify-center w-7 h-7 shrink-0">
            <span
              className="absolute inset-0 rounded-full opacity-30"
              style={{
                background: `radial-gradient(circle, ${COLOR.gold} 0%, transparent 70%)`,
                animation: "pulse 2s ease-in-out infinite",
              }}
            />
            <span
              className="inline-block w-2.5 h-2.5 rounded-full glow-breathe relative z-10"
              style={{ background: COLOR.gold, boxShadow: `0 0 12px ${COLOR.gold}` }}
            />
          </span>
          <span className="font-display text-lg tracking-wider text-shimmer" style={{ color: COLOR.ink }}>
            {t("app.name") === "玄枢" ? "Mystic Hub" : "Mystic Hub"}
          </span>
          <span className="text-[10px] uppercase tracking-[0.2em] opacity-60 group-hover:opacity-100 transition-opacity" style={{ color: COLOR.muted }}>
            {t("app.name")}
          </span>
        </NavLink>

        {/* Nav sections */}
        <nav className="relative flex-1 px-3 py-4 space-y-5">
          {SECTIONS.map((section, si) => (
            <div key={si}>
              {section.label && (
                <div className="flex items-center gap-2 px-3 mb-2">
                  {section.accent && (
                    <span
                      className="inline-block w-1 h-1 rounded-full sidebar-accent-line"
                      style={{ background: section.accent, boxShadow: `0 0 4px ${section.accent}` }}
                    />
                  )}
                  <span
                    className="text-[10px] uppercase tracking-[0.25em] font-semibold"
                    style={{ color: section.accent || COLOR.goldDim }}
                  >
                    {section.label}
                  </span>
                </div>
              )}
              <ul className="space-y-0.5">
                {section.items.map((item, ii) => {
                  const active = isActiveLink(item.to, location.pathname, location.search);
                  return (
                    <li key={ii}>
                      <NavLink
                        to={item.to}
                        onClick={onClose}
                        className={[
                          "flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm transition-all duration-200 tap",
                          active ? "sidebar-link-active" : "sidebar-link",
                        ].join(" ")}
                        style={{
                          color: active ? COLOR.goldBright : COLOR.inkSoft,
                          background: active
                            ? `linear-gradient(90deg, rgba(201,162,75,0.12) 0%, rgba(201,162,75,0.04) 100%)`
                            : "transparent",
                          fontWeight: active ? 600 : 400,
                        }}
                      >
                        <span className="text-base w-5 text-center shrink-0">{item.icon}</span>
                        <span>{item.label}</span>
                        {active && (
                          <span
                            className="ml-auto inline-block w-1.5 h-1.5 rounded-full"
                            style={{ background: COLOR.goldBright, boxShadow: `0 0 8px ${COLOR.gold}` }}
                          />
                        )}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer tagline with decorative top border */}
        <div
          className="relative px-5 py-4 text-[9px] text-center shrink-0"
          style={{ borderTop: `1px solid ${COLOR.lineSoft}` }}
        >
          {/* 行星符号行 */}
          <div className="flex justify-center mb-2">
            <PlanetSymbols size={12} />
          </div>
          {/* Decorative diamond in footer */}
          <div className="flex items-center justify-center gap-2 mb-1">
            <span style={{ color: COLOR.goldDim, fontSize: "6px" }}>◆</span>
            <YinYang size={18} />
            <span style={{ color: COLOR.goldDim, fontSize: "6px" }}>◆</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <span style={{ color: COLOR.goldDim, fontSize: "6px" }}>◆</span>
            <span style={{ color: COLOR.muted }}>{t("app.tagline")}</span>
            <span style={{ color: COLOR.goldDim, fontSize: "6px" }}>◆</span>
          </div>
        </div>
      </aside>
    </>
  );
}
