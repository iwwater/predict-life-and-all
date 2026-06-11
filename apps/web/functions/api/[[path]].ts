/**
 * Cloudflare Pages Function — API 代理
 * 将所有 /api/* 请求转发到后端服务器。
 *
 * 环境变量（Cloudflare Pages → Settings → Environment variables）:
 *   API_BACKEND = http://你的VPS_IP:8000   （必填）
 *
 * 本地开发仍然走 vite.config.ts 的 proxy 到 localhost:8000，
 * 本文件只在 Cloudflare Pages 生产环境生效。
 */

interface Env {
  API_BACKEND: string;
}

export const onRequest = async (context: {
  request: Request;
  env: Env;
}): Promise<Response> => {
  const { request, env } = context;

  // 本地开发不经过 Pages Functions（vite proxy 直接处理）
  const backend = env.API_BACKEND;

  // 调试：检查 env 里到底有什么（部署成功后删掉此行）
  if (!backend || !backend.startsWith("http")) {
    return new Response(
      JSON.stringify({
        detail: "API backend not configured. Set API_BACKEND env variable.",
        debug: {
          hasEnv: typeof env !== "undefined",
          envKeys: env ? Object.keys(env) : [],
          apiBackendValue: backend || "(empty)",
          hint: "请确保在 Cloudflare Pages → Settings → Environment variables 中添加了 API_BACKEND，然后 PUSH 新代码触发部署（Retry deployment 不会重新读取变量）",
        },
      }),
      {
        status: 502,
        headers: { "content-type": "application/json" },
      }
    );
  }

  const url = new URL(request.url);
  url.hostname = new URL(backend).hostname;
  url.port = new URL(backend).port || "8000";
  url.protocol = new URL(backend).protocol;

  // 构建转发请求
  const headers = new Headers(request.headers);
  headers.set("x-forwarded-for", request.headers.get("cf-connecting-ip") || "");
  headers.set("x-forwarded-host", url.hostname);

  const proxyRequest = new Request(url.toString(), {
    method: request.method,
    headers,
    body:
      request.method !== "GET" && request.method !== "HEAD"
        ? await request.text()
        : undefined,
  });

  try {
    const response = await fetch(proxyRequest);
    // SSE 流式转发（/api/interpret）
    if (
      response.headers.get("content-type")?.includes("text/event-stream")
    ) {
      return new Response(response.body, {
        status: response.status,
        headers: {
          "content-type": "text/event-stream",
          "cache-control": "no-cache",
          connection: "keep-alive",
          "access-control-allow-origin": "*",
        },
      });
    }
    return response;
  } catch (err: any) {
    return new Response(
      JSON.stringify({ detail: `Backend unreachable: ${err.message}` }),
      { status: 502, headers: { "content-type": "application/json" } }
    );
  }
};
