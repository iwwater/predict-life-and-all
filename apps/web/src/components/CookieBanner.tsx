// Cookie/隐私 banner — 首次访问提示
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const STORAGE_KEY = "mystic-hub.cookie-banner.dismissed";

export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const dismissed = window.localStorage.getItem(STORAGE_KEY);
        if (!dismissed) setVisible(true);
      }
    } catch {
      // 隐私模式下 localStorage 可能抛错 — 默认不显示
    }
  }, []);

  if (!visible) return null;

  const dismiss = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // ignore
    }
    setVisible(false);
  };

  return (
    <div
      role="alert"
      aria-live="polite"
      style={{
        position: "fixed",
        left: "1rem",
        right: "1rem",
        bottom: "1rem",
        maxWidth: "640px",
        margin: "0 auto",
        padding: "0.85rem 1rem",
        background: "var(--paper-raised)",
        border: "1px solid var(--rule-soft)",
        borderRadius: "0.25rem",
        boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
        zIndex: 50,
        fontSize: "0.82rem",
        color: "var(--ink)",
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: "0.5rem",
      }}
    >
      <span style={{ flex: 1, minWidth: "200px" }}>
        本站使用 Cookie 存储本机偏好 (语言、深色模式)。
        详见
        <Link
          to="/privacy"
          style={{ marginLeft: "0.25rem", color: "var(--accent)", textDecoration: "underline" }}
        >
          隐私政策
        </Link>
        。
      </span>
      <button
        type="button"
        onClick={dismiss}
        className="paper-btn"
        style={{ fontSize: "0.78rem", padding: "0.3rem 0.8rem" }}
      >
        知道了
      </button>
    </div>
  );
}
