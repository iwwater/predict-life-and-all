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
  const { t, lang } = useI18n();

  const SECTIONS: NavSection[] = [
    {
      items: [
        { to: "/", label: t("nav.home") },
      ],
    },
    {
      label: lang === "zh" ? "命" : "Destiny",
      accent: COLOR.verdigris,
      items: [
        { to: "/m/bazi", label: t("nav.bazi") },
        { to: "/m/ziwei", label: t("nav.ziwei") },
      ],
    },
    {
      label: lang === "zh" ? "卜" : "Divination",
      accent: COLOR.indigo,
      items: [
        { to: "/m/qimen", label: "奇门遁甲" },
        { to: "/m/liuyao", label: t("nav.liuyao") },
        { to: "/m/meihua", label: t("nav.meihua") },
        { to: "/m/chenggu", label: t("nav.chenggu") },
      ],
    },
    {
      label: lang === "zh" ? "相" : "Physiognomy",
      accent: COLOR.cinnabar,
      items: [
        { to: "/m/hepan", label: lang === "zh" ? "合盘" : "Synastry" },
        { to: "/m/tarot", label: t("nav.tarot") },
        { to: "/m/western", label: t("nav.western") },
        { to: "/m/vedic", label: t("nav.vedic") },
        { to: "/m/numerology", label: t("nav.numerology") },
      ],
    },
    {
      label: lang === "zh" ? "山" : "Feng Shui",
      accent: COLOR.verdigris,
      items: [
        { to: "/m/bazhai", label: t("nav.bazhai") },
        { to: "/m/xuankong", label: t("nav.xuankong") },
        { to: "/fengshui", label: t("nav.fengshui") },
      ],
    },
    {
      label: lang === "zh" ? "合参" : "Cross-Ref",
      accent: COLOR.cinnabar,
      items: [
        { to: "/heshen", label: lang === "zh" ? "合参" : "Cross-Ref" },
        { to: "/reading", label: "12法合参" },
        { to: "/compatibility", label: t("nav.compatibility") },
        { to: "/daily", label: t("nav.daily") },
        { to: "/almanac", label: t("nav.almanac") },
      ],
    },
    {
      label: t("section.more"),
      items: [
        { to: "/knowledge", label: t("nav.knowledge") },
        { to: "/history", label: t("nav.history") },
        { to: "/dateselect", label: t("nav.dateselect") },
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
