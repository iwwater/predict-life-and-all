"""P0-2 收口: CORS 来源、速率限制、可选 API Key、校验错误脱敏。

设计取舍(重要):

* 这套服务是**无状态**的排盘 API —— 不存账号、不存出生数据, 历史报告只存在浏览器
  localStorage。所以「加登录」没有意义; 真正会被滥用的只有两件事:
  1. 花钱的 LLM 端点 (`/api/interpret`, `/api/reading`, `/api/cases/*/cast`);
  2. 无上界的写操作/内存增长。
* 因此默认行为保持开发友好(全开 CORS、不限流), 但只要设置了环境变量就立即收紧,
  `docker-compose.yml` 里已经按生产口径打开:
  - ``MYSTIC_CORS_ORIGINS``: 逗号分隔白名单, 不设则 ``*``(仅建议开发用)
  - ``MYSTIC_RATE_LIMIT_PER_MIN``: 每客户端每分钟请求数, ``0``/不设 = 关闭
  - ``MYSTIC_API_KEY``: 设定后所有非 GET 请求必须带 ``X-API-Key``
* 限流是**进程内**滑窗(单实例足够); 多副本部署请换 Redis 之类共享存储, 见 DEPLOY.md。
"""
from __future__ import annotations

import hmac
import os
import threading
import time
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

# 会烧钱或写状态的路径前缀 —— 只有这些参与限流, GET 元数据/排盘不拦。
RATE_LIMITED_PREFIXES: tuple[str, ...] = (
    "/api/interpret",
    "/api/reading",
    "/api/cases",
)

_WINDOW_SECONDS = 60.0

_LOCK = threading.Lock()
_BUCKETS: dict[tuple[str, str], list[float]] = {}


def cors_origins() -> list[str]:
    """``MYSTIC_CORS_ORIGINS`` 为逗号分隔白名单; 未设置时回落到开发用的 ``*``。"""
    raw = os.environ.get("MYSTIC_CORS_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


def rate_limit_per_min() -> int:
    try:
        return max(0, int(os.environ.get("MYSTIC_RATE_LIMIT_PER_MIN", "0") or 0))
    except ValueError:
        return 0


def api_key() -> str:
    return os.environ.get("MYSTIC_API_KEY", "").strip()


def client_identity(request: Request) -> str:
    """优先信任反代写入的 ``X-Forwarded-For`` 首跳, 否则用直连地址。"""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    client = request.client
    return client.host if client and client.host else "unknown"


def _rate_limit_group(path: str) -> str | None:
    for prefix in RATE_LIMITED_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return prefix
    return None


def _prune_bucket(bucket: list[float], now: float) -> None:
    cutoff = now - _WINDOW_SECONDS
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)


def check_rate_limit(request: Request) -> JSONResponse | None:
    """超限返回 429 响应, 否则 ``None``。"""
    limit = rate_limit_per_min()
    if limit <= 0:
        return None
    group = _rate_limit_group(request.url.path)
    if group is None:
        return None

    now = time.monotonic()
    key = (client_identity(request), group)
    with _LOCK:
        bucket = _BUCKETS.setdefault(key, [])
        _prune_bucket(bucket, now)
        if len(bucket) >= limit:
            retry_after = max(1, int(_WINDOW_SECONDS - (now - bucket[0])) + 1)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"请求过于频繁: 每分钟最多 {limit} 次, 请 {retry_after} 秒后再试",
                    "limit": limit,
                    "group": group,
                },
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)
        # 清理长期不活跃的 key, 避免限流表自己变成内存泄漏
        if len(_BUCKETS) > 4096:
            for stale_key in [k for k, v in _BUCKETS.items() if not v or now - v[-1] > _WINDOW_SECONDS * 5]:
                _BUCKETS.pop(stale_key, None)
    return None


def check_api_key(request: Request) -> JSONResponse | None:
    """配置了 ``MYSTIC_API_KEY`` 时, 非只读请求必须带正确的 ``X-API-Key``。"""
    expected = api_key()
    if not expected:
        return None
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    supplied = request.headers.get("x-api-key", "")
    if hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        return None
    return JSONResponse(
        status_code=401,
        content={"detail": "缺少或无效的 X-API-Key"},
        headers={"WWW-Authenticate": "X-API-Key"},
    )


def guard_request(request: Request) -> JSONResponse | None:
    """请求进入业务代码前的统一守卫; 放行返回 ``None``。"""
    return check_api_key(request) or check_rate_limit(request)


def validation_error_payload(exc: Any) -> dict[str, Any]:
    """把校验错误转成**不含用户输入值**的响应体。

    FastAPI 默认的 422 响应会把 ``input`` 原样带回客户端 —— 出生日期、坐标、
    问题原文都可能出现在错误响应里, 既泄漏用户输入也容易进日志。这里逐条清洗
    掉 ``input``/``url``/``ctx``, 只保留 loc 与 msg。

    注意: ``RequestValidationError.errors()`` 不接受 ``include_input`` 之类的参数,
    所以必须自己过滤, 不能靠 pydantic 的 kwargs。
    """
    try:
        raw = exc.errors()
    except Exception:  # pragma: no cover - 非 pydantic 异常兜底
        return {"detail": [{"msg": str(exc)}]}

    cleaned: list[dict[str, Any]] = []
    for err in raw:
        if not isinstance(err, dict):
            cleaned.append({"msg": str(getattr(err, "msg", err))})
            continue
        item = {key: value for key, value in err.items() if key not in {"input", "url", "ctx"}}
        loc = item.get("loc")
        if isinstance(loc, tuple):
            item["loc"] = list(loc)
        cleaned.append(item)
    return {"detail": cleaned}


def reset_rate_limits_for_tests() -> None:
    with _LOCK:
        _BUCKETS.clear()
