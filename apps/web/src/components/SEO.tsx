// SEO: 动态设置 document title + meta description
import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useI18n } from "../lib/i18n";

const SEO_MAP: Record<string, string> = {
  "/": "seo.home",
  "/cast": "seo.cast",
  "/result": "seo.result",
  "/daily": "seo.daily",
  "/almanac": "seo.almanac",
  "/dateselect": "seo.dateselect",
  "/fengshui": "seo.fengshui",
  "/compatibility": "seo.compat",
  "/knowledge": "seo.knowledge",
  "/about": "seo.about",
  "/history": "seo.history",
};

const DEFAULT_DESC = {
  zh: "中西融通命理平台：八字、紫微、奇门、六壬、风水 + 西方占星、塔罗、雷诺曼。AI 解读，十四术数一站式排盘。",
  en: "East-West divination platform: Ba Zi, Zi Wei, Qi Men, Feng Shui + Western Astrology, Tarot, Lenormand. AI-powered readings across 14 arts.",
};

export function SEO() {
  const { pathname } = useLocation();
  const { t, lang } = useI18n();

  useEffect(() => {
    const seoKey = SEO_MAP[pathname];
    let title: string;
    if (seoKey) {
      title = t(seoKey);
    } else if (pathname.startsWith("/methods/")) {
      title = lang === "zh" ? "术数详情 — 玄枢" : "Method Info — Mystic Hub";
    } else {
      title = lang === "zh" ? "玄枢 Mystic Hub" : "Mystic Hub";
    }

    document.title = title;

    // Update meta description
    let descMeta = document.querySelector('meta[name="description"]');
    if (!descMeta) {
      descMeta = document.createElement("meta");
      descMeta.setAttribute("name", "description");
      document.head.appendChild(descMeta);
    }
    descMeta.setAttribute("content", DEFAULT_DESC[lang]);

    // Update html lang
    document.documentElement.lang = lang;
  }, [pathname, lang, t]);

  return null;
}
