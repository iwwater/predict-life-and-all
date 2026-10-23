"""FastAPI app 入口。

启动:
    uv run uvicorn server.main:app --reload --port 8000

端点(全部 /api 前缀):
    GET  /health
    GET  /api/methods
    POST /api/compute
    POST /api/interpret            (流式 NDJSON)
    GET  /api/prompts/{method}
    GET  /api/cases
"""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .api import almanac, birth_time, cases, chart, compass, daily as daily_api, dream, extended_knowledge, hepan_share, interpret, knowledge, methods, prompts, reading, users
from . import security

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("mystic-hub")

app = FastAPI(
    title="Mystic Hub API",
    version="0.1.0",
    description="中西方统一算命引擎 + AI 解读后端",
)

# CORS: 默认放开给本地开发; 生产用 MYSTIC_CORS_ORIGINS 收敛成白名单(见 DEPLOY.md)
app.add_middleware(
    CORSMiddleware,
    allow_origins=security.cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(methods.router,   prefix="/api", tags=["meta"])
app.include_router(chart.router,     prefix="/api", tags=["chart"])
app.include_router(interpret.router, prefix="/api", tags=["interpret"])
app.include_router(prompts.router,   prefix="/api", tags=["prompts"])
app.include_router(cases.router, prefix="/api", tags=["cases"])
app.include_router(birth_time.router, prefix="/api", tags=["birth-time"])
app.include_router(daily_api.router, prefix="/api", tags=["daily"])
app.include_router(almanac.router, prefix="/api", tags=["almanac"])
app.include_router(reading.router,  prefix="/api", tags=["reading"])
app.include_router(compass.router, prefix="/api", tags=["compass"])
app.include_router(hepan_share.router, prefix="/api", tags=["hepan-share"])
app.include_router(knowledge.router, tags=["knowledge"])
app.include_router(extended_knowledge.router, tags=["knowledge-ext"])
app.include_router(dream.router)
app.include_router(users.router, prefix="/api", tags=["users"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": app.version, "service": "mystic-hub"}


@app.middleware("http")
async def _log_requests(request: Request, call_next):
    # 先过安全守卫(可选 API Key + 烧钱端点限流), 直接把响应返回给客户端
    blocked = security.guard_request(request)
    if blocked is not None:
        log.warning("blocked %s %s → %s", request.method, request.url.path, blocked.status_code)
        return blocked

    t0 = time.perf_counter()
    response = await call_next(request)
    dt_ms = int((time.perf_counter() - t0) * 1000)
    log.info("%s %s → %s (%dms)", request.method, request.url.path, response.status_code, dt_ms)
    return response


@app.exception_handler(RequestValidationError)
async def _request_validation_error(request, exc):
    # FastAPI 请求体校验走 RequestValidationError(不是 pydantic 的 ValidationError),
    # 默认响应会把 input 原样带出去 —— 统一改走脱敏版本
    return JSONResponse(status_code=422, content=security.validation_error_payload(exc))


@app.exception_handler(ValidationError)
async def _validation_error(request, exc):
    # 不把 input_value 回显给客户端(出生信息/坐标/问题原文都可能出现在里面)
    return JSONResponse(status_code=422, content=security.validation_error_payload(exc))


@app.exception_handler(Exception)
async def _unhandled(request, exc):
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
