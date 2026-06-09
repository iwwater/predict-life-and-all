/** @type {import('tailwindcss').Config} */
// 对齐《前端设计计划书》§7:暗夜 + 金 + 青/蓝 双系
//   --bg      #0E1117   暗夜底色
//   --surface #161B22   卡片/抬升
//   --ink     #E6E1D3   暖白文字
//   --muted   #8A8F98   次要文字
//   --gold    #C9A24B   星图金(主点缀)
//   --jade    #4FB3A0   东方·青
//   --azure   #5B8DEF   西方·蓝
//   --danger  #C8553D   凶/警示(克制使用)
//   --ok      #5AA469   吉(克制使用)
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 命名与设计 token 1:1 对应,前端组件用 bg-ink / text-gold 这种语义名
        bg:      { DEFAULT: "#0E1117", deep: "#080A0F" },
        surface: { DEFAULT: "#161B22", raised: "#1C232C" },
        ink:     { DEFAULT: "#E6E1D3", muted: "#8A8F98", soft: "#C8C2B0" },
        gold:    { DEFAULT: "#C9A24B", dim: "#8A6E32", bright: "#E5BC5E" },
        jade:    { DEFAULT: "#4FB3A0", dim: "#36766A" },
        azure:   { DEFAULT: "#5B8DEF", dim: "#3A6BC2" },
        danger:  "#C8553D",
        ok:      "#5AA469",
        line:    "rgba(201, 162, 75, 0.18)",
      },
      fontFamily: {
        display: ["Cinzel", "Noto Serif SC", "serif"],
        sans:    ["Noto Serif SC", "PingFang SC", "Inter", "system-ui", "sans-serif"],
        mono:    ["JetBrains Mono", "Menlo", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow:    "0 0 24px rgba(201, 162, 75, 0.25)",
        "glow-jade":  "0 0 24px rgba(79, 179, 160, 0.22)",
        "glow-azure": "0 0 24px rgba(91, 141, 239, 0.22)",
      },
      backgroundImage: {
        "sky-gradient": "radial-gradient(ellipse at top, rgba(91, 141, 239, 0.08) 0%, transparent 60%)",
      },
    },
  },
  plugins: [],
};
