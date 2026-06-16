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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
import time

from .api import birth_time, cases, chart, methods, prompts, interpret, almanac, reading
from .api import daily as daily_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("mystic-hub")

app = FastAPI(
    title="Mystic Hub API",
    version="0.1.0",
    description="中西方统一算命引擎 + AI 解读后端",
)

# CORS:开发期全开,生产请收敛 origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": app.version, "service": "mystic-hub"}


@app.middleware("http")
async def _log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    dt_ms = int((time.perf_counter() - t0) * 1000)
    log.info("%s %s → %s (%dms)", request.method, request.url.path, response.status_code, dt_ms)
    return response


@app.exception_handler(ValidationError)
async def _validation_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def _unhandled(request, exc):
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
