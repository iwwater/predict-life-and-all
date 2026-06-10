// 侧边栏导航:「古籍×仪器」风格 — 纸墨底,栏线分隔,无 emoji
import { NavLink, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { COLOR } from "./ui";
import { useI18n } from "../lib/i18n";

export interface NavItem {
  to: string;
  label: string;
}

export interface NavSection {
  label?: string;
  items: NavItem[];
  accent?: string;
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
        { to: "/", label: t("nav.home") },
      ],
    },
    {
      label: t("section.eastMantra"),
      accent: COLOR.verdigris,
      items: [
        { to: "/method/bazi-v2", label: t("nav.baziV2") },
        { to: "/method/bazi", label: t("nav.bazi") },
        { to: "/method/ziwei", label: t("nav.ziwei") },
        { to: "/method/qimen", label: "奇门遁甲" },
        { to: "/method/liuren", label: t("nav.liuren") },
        { to: "/method/liuyao", label: t("nav.liuyao") },
        { to: "/method/meihua", label: t("nav.meihua") },
        { to: "/method/xiaoliuren", label: t("nav.xiaoliuren") },
        { to: "/method/chenggu", label: t("nav.chenggu") },
        { to: "/method/tieban", label: t("nav.tieban") },
      ],
    },
    {
      label: t("section.westOracle"),
      accent: COLOR.indigo,
      items: [
        { to: "/method/western", label: t("nav.western") },
        { to: "/method/vedic", label: t("nav.vedic") },
        { to: "/method/tarot", label: t("nav.tarot") },
        { to: "/method/lenormand", label: t("nav.lenormand") },
        { to: "/method/numerology", label: t("nav.numerology") },
      ],
    },
    {
      label: t("section.fengshuiNav"),
      accent: COLOR.cinnabar,
      items: [
        { to: "/method/xuankong", label: t("nav.xuankong") },
        { to: "/method/bazhai", label: t("nav.bazhai") },
        { to: "/fengshui", label: t("nav.fengshui") },
      ],
    },
    {
      label: t("section.aggregateNav"),
      accent: COLOR.cinnabar,
      items: [
        { to: "/aggregate", label: t("nav.aggregate") },
        { to: "/reading", label: "12法合参" },
        { to: "/compatibility", label: t("nav.compatibility") },
        { to: "/dateselect", label: t("nav.dateselect") },
        { to: "/daily", label: t("nav.daily") },
        { to: "/almanac", label: t("nav.almanac") },
      ],
    },
    {
      label: t("section.more"),
      items: [
        { to: "/knowledge", label: t("nav.knowledge") },
        { to: "/history", label: t("nav.history") },
        { to: "/about", label: t("nav.about") },
      ],
    },
  ];

  // 路由变化时关闭移动端侧栏
  useEffect(() => {
    onClose();
  }, [location.pathname, location.search]);

  return (
    <>
      {/* 移动端遮罩 */}
      {open && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          style={{ background: "rgba(0,0,0,0.35)" }}
          onClick={onClose}
        />
      )}

      {/* 侧边栏 */}
      <aside
        className={[
          "fixed inset-y-0 left-0 z-50 w-[232px] flex flex-col border-r overflow-y-auto",
          "transition-transform duration-200 ease-out",
          "lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        ].join(" ")}
        style={{
          background: "var(--paper-2)",
          borderColor: "var(--rule)",
        }}
      >
        {/* Logo */}
        <NavLink
          to="/"
          className="flex items-center gap-2.5 px-4 h-14 shrink-0"
          onClick={onClose}
          style={{ borderBottom: "1px solid var(--rule)" }}
        >
          <span
            style={{
              display: "inline-block",
              width: "0.7rem",
              height: "0.7rem",
              background: "var(--cinnabar)",
              borderRadius: 1,
              flexShrink: 0,
            }}
          />
          <span style={{
            fontFamily: "'Noto Serif SC', serif",
            fontWeight: 700,
            fontSize: "1rem",
            letterSpacing: "0.06em",
            color: "var(--ink)",
          }}>
            Mystic Hub
          </span>
          <span style={{
            fontFamily: "'Noto Serif SC', serif",
            fontSize: "0.7rem",
            color: "var(--ink-soft)",
            letterSpacing: "0.3em",
          }}>
            {t("app.name")}
          </span>
        </NavLink>

        {/* 导航区段 */}
        <nav className="flex-1 px-3 py-4 space-y-4">
          {SECTIONS.map((section, si) => (
            <div key={si}>
              {section.label && (
                <div className="flex items-center gap-1.5 px-2 mb-1.5">
                  {section.accent && (
                    <span
                      style={{
                        display: "inline-block",
                        width: 4,
                        height: 4,
                        background: section.accent,
                        borderRadius: "50%",
                        flexShrink: 0,
                      }}
                    />
                  )}
                  <span
                    style={{
                      fontFamily: "'Noto Serif SC', serif",
                      fontSize: "0.65rem",
                      fontWeight: 600,
                      letterSpacing: "0.25em",
                      color: section.accent || "var(--ink-soft)",
                    }}
                  >
                    {section.label}
                  </span>
                </div>
              )}
              <ul className="space-y-px">
                {section.items.map((item, ii) => {
                  const active = isActiveLink(item.to, location.pathname, location.search);
                  return (
                    <li key={ii}>
                      <NavLink
                        to={item.to}
                        onClick={onClose}
                        className="block px-2.5 py-2 rounded-sm text-sm transition-colors"
                        style={{
                          fontFamily: "'Noto Serif SC', serif",
                          color: active ? "var(--cinnabar)" : "var(--ink-soft)",
                          fontWeight: active ? 600 : 400,
                          background: active ? "rgba(176, 58, 46, 0.06)" : "transparent",
                          borderLeft: active ? "2px solid var(--cinnabar)" : "2px solid transparent",
                          letterSpacing: "0.05em",
                        }}
                      >
                        {item.label}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* 底部标识 */}
        <div
          className="px-4 py-3 text-center shrink-0"
          style={{ borderTop: "1px solid var(--rule)" }}
        >
          <div style={{
            fontFamily: "'Noto Serif SC', serif",
            fontSize: "0.6rem",
            color: "var(--ink-soft)",
            letterSpacing: "0.2em",
          }}>
            {t("app.tagline")}
          </div>
        </div>
      </aside>
    </>
  );
}
