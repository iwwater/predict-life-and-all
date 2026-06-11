/** @type {import('tailwindcss').Config} */
// 「古籍×仪器」纸墨为底，朱砂点睛
// 设计 token 对齐 index.css :root 变量
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 纸墨底色
        paper:      { DEFAULT: "#F4EFE6", 2: "#EDE6D8" },
        // 墨色
        ink_paper:  { DEFAULT: "#2B2620", soft: "#6B6256" },
        // 朱砂 — 全站唯一高饱和色
        cinnabar:   { DEFAULT: "#B03A2E", dim: "#8E2E25" },
        // 法系标识
        indigo:     "#2F4858",
        verdigris:  "#5A7058",
        // 界格线
        rule:       { DEFAULT: "#C9BFA9", soft: "rgba(201,191,169,0.5)" },
      },
      fontFamily: {
        display: ["Cinzel", "Noto Serif SC", "serif"],
        sans:    ["Noto Serif SC", "PingFang SC", "system-ui", "sans-serif"],
        mono:    ["JetBrains Mono", "Menlo", "ui-monospace", "monospace"],
        serif:   ["Noto Serif SC", "Noto Serif", "Songti SC", "PingFang SC", "serif"],
        mono_paper: ["JetBrains Mono", "SF Mono", "Menlo", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
