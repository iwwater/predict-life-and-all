# Mystic Hub 上线部署说明

推荐先用一台 VPS + Docker Compose 上线。这个项目由 FastAPI 后端负责排盘和报告接口，React/Vite 前端由 Nginx 对外提供页面，并把 `/api/*` 同域代理到内部后端服务。

## 方案 A：VPS 一站式部署

适合：你有云服务器和域名，想最快让网站可以访问。

服务器建议：

- Ubuntu 22.04/24.04
- 最低 1 核 1G，可运行；建议 2G 内存
- 安装 Docker 和 Docker Compose Plugin
- 开放 80/443 端口

### 1. 准备服务器

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

执行完 `usermod` 后重新登录 SSH。

### 2. 上传代码

方式一：如果代码已在 GitHub/Gitee：

```bash
cd /opt
git clone <your-repo-url> mystic-hub
cd /opt/mystic-hub
```

方式二：直接从 Windows 上传当前项目：

```powershell
Compress-Archive -Path "E:\work\predict life and all\*" -DestinationPath "$env:TEMP\mystic-hub.zip" -Force
scp "$env:TEMP\mystic-hub.zip" root@你的服务器IP:/opt/mystic-hub.zip
```

然后在服务器解压：

```bash
cd /opt
mkdir -p mystic-hub
unzip -o mystic-hub.zip -d mystic-hub
cd mystic-hub
```

### 3. 启动网站

```bash
cd /opt/mystic-hub
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

默认对外开放：

```text
http://服务器IP/
```

后端不会直接暴露到公网，前端通过同域接口访问：

```text
/api/methods
/api/compute
/api/reading
```

### 4. 验证

```bash
docker compose -f deploy/docker-compose.prod.yml ps
curl http://127.0.0.1/api/methods
docker compose -f deploy/docker-compose.prod.yml logs -f --tail=100
```

浏览器打开：

```text
http://你的服务器IP/
```

### 5. 绑定域名

在域名 DNS 中添加：

```text
A  @    服务器公网IP
A  www  服务器公网IP
```

解析生效后访问：

```text
http://你的域名/
```

### 6. HTTPS

最省事是用 Caddy 自动签证书。先让本项目监听 8080：

```bash
WEB_PORT=8080 docker compose -f deploy/docker-compose.prod.yml up -d --build
```

安装 Caddy 后写入 Caddyfile：

```text
your-domain.com {
    reverse_proxy 127.0.0.1:8080
}
```

然后：

```bash
sudo systemctl reload caddy
```

## 方案 B：托管平台

如果不想管服务器，可以用 Railway / Render / Fly.io 这类支持 Docker 的平台。注意：

- 这个项目更适合 Docker 部署。
- 如果平台不支持 Docker Compose，需要拆成两个服务：
  - `server`：使用 `Dockerfile.server`
  - `web`：使用 `Dockerfile.web`
- `deploy/nginx.conf` 默认把 `/api` 代理到 Compose 内部服务名 `server:8000`。如果平台拆服务后不能使用这个服务名，需要把 `proxy_pass` 改成平台提供的后端内网地址。

## 环境变量

后端不强制要求 LLM Key。没有 Key 时会走 fallback/mock 报告。

如果需要服务端模型：

```bash
ANTHROPIC_API_KEY=你的key
LLM_MODEL=claude-3-5-haiku-latest
```

如果使用 Packy / OpenAI 兼容代理，建议先把后端适配成统一的 OpenAI-compatible 客户端，再用：

```bash
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=https://www.packyapi.com/v1
OPENAI_MODEL=实际可用模型名
```

不要把 Key 写进前端构建产物。

### 访问控制与资源保护

默认配置是「本地开发友好」：CORS 允许所有来源、不限流、不需要 API Key。放到公网前建议按下面收紧（三个都是可选环境变量，不设置就维持默认）：

```bash
# 只允许自己的前端域名访问 API（逗号分隔，支持多个）
MYSTIC_CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# 每个 IP 每分钟最多打多少次「会调用 LLM 的」写接口（/api/interpret、/api/reading、/api/cases）
# 0 / 不设置 = 不限流。公网建议 30~120。
MYSTIC_RATE_LIMIT_PER_MIN=60

# 设置后，所有写接口必须带请求头 X-API-Key 才能通过（读接口仍然公开）
MYSTIC_API_KEY=换成你自己的随机串
```

> 限流是**进程内**滑动窗口，多 worker 部署时每个 worker 各自计数（够挡住脚本刷额度，不替代网关限流）。反向代理后面要保证 `X-Forwarded-For` 被正确设置，限流按它的首跳地址识别客户端。

案例库（`/api/cases`）存在进程内存里，受两个开关约束，默认 500 条 / 24 小时：

```bash
MYSTIC_MAX_CASES=500
MYSTIC_CASE_TTL_SECONDS=86400
```

注意：服务端**不持久化**用户的出生数据与解读结果，删除请求返回的 `deleted_fields` 为空是这个原因（历史记录只存在浏览器 localStorage）。

## 更新网站

Git 部署：

```bash
cd /opt/mystic-hub
git pull
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

压缩包部署：

```bash
cd /opt/mystic-hub
unzip -o /opt/mystic-hub.zip -d /opt/mystic-hub
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

## 常见问题

### Docker build 时星历下载失败

当前 `Dockerfile.server` 已经不在构建时联网下载星历，而是把项目根目录里的 `de421.bsp` 打进镜像。确认上传时不要漏掉这个文件。

### 本地 Docker 命令不可用

本机如果没有安装 Docker，就无法在本地验证 compose 构建。可以先在服务器上验证：

```bash
docker compose -f deploy/docker-compose.prod.yml config
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

### API 503 或模型不可用

这通常不是部署问题，而是模型供应商分组/模型名/Key 配置问题。先用 mock/fallback 确认网站和排盘可用，再切真实模型。
