import { Link, Outlet, useLocation } from "react-router-dom";
import { useMemo } from "react";
import { useI18n } from "../lib/i18n";

// ponytail: G2 抽了 5 档字号 + 4 档间距 + 4 个容器 token 到 index.css
// ponytail-debt: 24 个内联 fontSize 散布在 ~20 文件未迁;G3 范围
// ponytail-debt: 容器内边距/间距未切到 --space-*;G3 范围
// ponytail-debt: paper-* 类的 font-size 未切到 --font-* (dark 块同时覆写,要同步改)

const METHOD_NAV = [
  { to: "/", label: "术数" },
  { to: "/cases", label: "问事" },
  { to: "/heshen", label: "合参" },
  { to: "/about", label: "凡例" },
];

const METHOD_LABELS: Record<string, string> = {
  bazi: "八字四柱",
  ziwei: "紫微斗数",
  tieban: "铁板神数",
  qimen: "奇门遁甲",
  liuyao: "六爻",
  meihua: "梅花易数",
  liuren: "大六壬",
  xiaoliuren: "小六壬",
  qian: "灵签",
  chenggu: "称骨",
  hepan: "合盘",
  tarot: "塔罗",
  lenormand: "雷诺曼",
  western: "西方占星",
  vedic: "吠陀占星",
  numerology: "数字命理",
  bazhai: "八宅",
  xuankong: "玄空飞星",
};

export function Layout() {
  const location = useLocation();
  const { lang, toggle: toggleLang } = useI18n();
  const isHome = location.pathname === "/";

  const pageLabel = useMemo(() => {
    if (location.pathname.startsWith("/m/")) {
      return METHOD_LABELS[location.pathname.replace("/m/", "")] || "观盘";
    }
    if (location.pathname === "/cases") return "问事档案";
    if (location.pathname === "/reading") return "十二法合参";
    if (location.pathname === "/heshen") return "合参卷";
    if (location.pathname === "/daily") return "今日";
    if (location.pathname === "/almanac") return "老黄历";
    if (location.pathname === "/compatibility") return "合盘";
    if (location.pathname === "/fengshui") return "风水";
    if (location.pathname === "/history") return "历史";
    if (location.pathname === "/knowledge") return "知识馆";
    if (location.pathname === "/about") return "凡例";
    return "玄枢";
  }, [location.pathname]);

  return (
    <div className="mystic-shell paper-page">
      <header className="mystic-topbar">
        <Link className="mystic-wordmark" to="/">
          玄枢 <i>Mystic Hub</i>
        </Link>

        <nav className="mystic-topnav" aria-label="主导航">
          {METHOD_NAV.map((item) => (
            <Link key={item.to} to={item.to}>
              {item.label}
            </Link>
          ))}
          <button type="button" onClick={toggleLang}>
            {lang === "zh" ? "EN" : "中"}
          </button>
        </nav>
      </header>

      {!isHome && (
        <div className="mystic-breadcrumb" aria-label="当前位置">
          <Link to="/">首页</Link>
          <span>/</span>
          <strong>{pageLabel}</strong>
        </div>
      )}

      <main className={isHome ? "mystic-main mystic-main-home" : "mystic-main"}>
        <Outlet />
      </main>

      <footer className="mystic-footer">
        <div className="mystic-footer-mark" />
        <p>
          本站所有解读为传统文化象征视角的参考，非科学预测，亦不构成医疗、法律、财务等专业意见。
          重大决定请结合现实并咨询专业人士。
        </p>
        <span>MYSTIC HUB · MIT/BSD · COMPUTED, NOT GUESSED</span>
      </footer>
    </div>
  );
}
