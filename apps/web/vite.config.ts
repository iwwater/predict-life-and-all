import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";

// Tailwind 的配置默认按 process.cwd() 查找 tailwind.config.js。
// 从仓库根启动( node apps/web/node_modules/vite/bin/vite.js apps/web )时 cwd 不是 apps/web,
// 于是它拿不到 content 配置、静默产出 0 个工具类 —— 页面只剩 preflight, 布局塌成块流。
// 这里显式把配置路径钉死, 与启动目录无关。
const here = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      plugins: [
        tailwindcss({ config: `${here}tailwind.config.js` }),
        autoprefixer(),
      ],
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: { sourcemap: true },
});
