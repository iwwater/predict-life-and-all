"""POST/GET /api/compass - 罗盘测量记录 + 连续采样。

Sprint 3 升级:
  - 三通道输入 (device / physical / manual / map)
  - declination 校正 (WMM 简化, 占位)
  - 临界角双候选 < 5°
  - 24 山元数据列表

24 山与 8 方位转换, 供风水系术法 (八宅/玄空/奇门) 使用。
方案 §二-4 + §九。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from divination.engines.compass import (
    DUAL_CANDIDATE_THRESHOLD_DEG,
    SANS_24,
    SANS_ELEMENT,
    SANS_TRIGRAM,
    circular_mean,
    circular_std,
    estimate_declination,
    get_fengshui_tip,
    heading_to_24mountain,
    heading_to_direction,
    list_24_mountains,
    magnetic_to_true_heading,
    normalize_heading,
)

router = APIRouter(prefix="/compass", tags=["compass"])

# ── Pydantic 模型 ─────────────────────────────────────────────────────────────

class CompassReading(BaseModel):
    """单次罗盘测量."""
    sans: str = Field(..., description="24 山 e.g. '子', '卯', '巽'")
    direction: str = Field(..., description="8 方位 e.g. '正北', '正东'")
    azimuth_deg: float = Field(..., ge=0, le=360, description="磁北偏角度数 0-360")
    device: str = Field(default="manual", description="测量来源: 'phone_compass' / 'manual' / '实体罗盘'")
    note: str | None = None
    north_ref: str = Field(default="magnetic", description="'magnetic' | 'true'")


class CompassSessionCreate(BaseModel):
    """创建采样会话."""
    direction_hint: str = Field(..., description="预期坐向（用户口述）e.g. '大门朝东'")
    sample_count: int = Field(default=5, ge=2, le=20, description="采样次数")
    north_ref: str = Field(default="magnetic", description="'magnetic' | 'true'")


class CompassSessionAddSample(BaseModel):
    """向采样会话追加一个读数."""
    azimuth_deg: float = Field(..., ge=0, le=360)


class CompassSession(BaseModel):
    session_id: str
    direction_hint: str
    target_sans: str
    target_direction: str
    samples: list[float]
    readings: list[CompassReading]
    result_sans: str
    result_direction: str
    result_azimuth: float
    std_dev: float
    quality: str  # "high" / "medium" / "low"
    dual_candidate: bool = False
    alt_sans: str | None = None
    distance_to_boundary: float = 0.0
    north_ref: str = "magnetic"
    created_at: float
    closed: bool = False


class CompassMeasureRequest(BaseModel):
    """Sprint 3.1: 三通道输入."""
    magnetic_heading_deg: float | None = None
    physical_compass_sans: str | None = None
    manual_azimuth_deg: float | None = None
    map_direction: str | None = None
    lat: float | None = None
    lng: float | None = None
    declination_deg: float | None = None
    north_ref: str = "magnetic"
    samples: list[float] | None = None


class CompassMeasureResponse(BaseModel):
    """罗盘测量输出."""
    input_channel: str
    raw_heading: float
    north_ref: str
    declination_deg: float
    declination_source: str
    true_heading: float
    sans: str
    alt_sans: str | None = None
    sans_zh: str
    trigram: str
    element: str
    direction: str
    dual_candidate: bool
    distance_to_boundary: float
    quality: str
    tip: str
    fengshui_warning: str | None = None


# ── 内存存储 ──────────────────────────────────────────────────────────────

_sessions: dict[str, CompassSession] = {}


# ── 8 方位映射 (Sprint 3 委托给 engine, 但保留以向后兼容) ─────────

DIRECTION_TO_SANS: dict[str, str] = {
    "正北": "子", "东北": "艮", "正东": "卯", "东南": "巽",
    "正南": "午", "西南": "坤", "正西": "酉", "西北": "乾",
}


# ── 工具函数 (向后兼容) ─────────────────────────────────────────────

def azimuth_to_sans(azimuth_deg: float) -> str:
    """磁北偏角度数 → 24 山 (委托 engine)."""
    return heading_to_24mountain(azimuth_deg)["sans"]


def azimuth_to_direction(azimuth_deg: float) -> str:
    """磁北偏角度数 → 8 方位."""
    return heading_to_direction(azimuth_deg)


def compute_result(samples: list[float]) -> tuple[str, str, float, float, str]:
    """从一组方位角计算最终结果."""
    mean = circular_mean(samples)
    std = circular_std(samples)
    result = heading_to_24mountain(mean)
    result_dir = heading_to_direction(mean)
    if std <= 3.0:
        quality = "high"
    elif std <= 8.0:
        quality = "medium"
    else:
        quality = "low"
    return result["sans"], result_dir, round(mean, 1), round(std, 2), quality


# ── 端点 ─────────────────────────────────────────────────────────────────

@router.get("/24-mountains")
def get_24_mountains():
    """Sprint 3.1: 列出 24 山完整元数据 (中心角/边界/卦/五行/提示)."""
    return {"mountains": list_24_mountains(), "total": 24}


@router.post("/measure", response_model=CompassMeasureResponse)
def measure_compass(body: CompassMeasureRequest):
    """Sprint 3.1: 三通道输入 + declination 校正 + 双候选检测.

    通道:
      1. device (手机罗盘磁北, magnetic_heading_deg)
      2. physical (实体罗盘直接读 24 山, physical_compass_sans)
      3. manual (手动输入 0-360 方位角, manual_azimuth_deg)
      4. map (地图方向, map_direction)

    临界角 (距山界 < 5°): 返回双候选, 建议复测.
    """
    # 通道检测
    if body.physical_compass_sans:
        if body.physical_compass_sans not in SANS_24:
            raise HTTPException(400, f"unknown sans: {body.physical_compass_sans}")
        idx = SANS_24.index(body.physical_compass_sans)
        raw_heading = idx * 15.0
        channel = "physical"
    elif body.magnetic_heading_deg is not None:
        raw_heading = body.magnetic_heading_deg
        channel = "device"
    elif body.manual_azimuth_deg is not None:
        raw_heading = body.manual_azimuth_deg
        channel = "manual"
    elif body.map_direction:
        direction_to_az = {
            "正北": 0, "东北": 45, "正东": 90, "东南": 135,
            "正南": 180, "西南": 225, "正西": 270, "西北": 315,
        }
        if body.map_direction not in direction_to_az:
            raise HTTPException(400, f"unknown direction: {body.map_direction}")
        raw_heading = direction_to_az[body.map_direction]
        channel = "map"
    else:
        raise HTTPException(400, "no input channel provided")

    # declination 校正
    if body.north_ref == "magnetic" and (body.lat is not None or body.declination_deg is not None):
        if body.declination_deg is not None:
            converted = magnetic_to_true_heading(
                raw_heading, body.lat or 0, body.lng or 0,
                declination=body.declination_deg,
            )
        else:
            converted = magnetic_to_true_heading(
                raw_heading, body.lat or 0, body.lng or 0,
            )
        true_heading = converted["true_heading"]
        declination = converted["declination"]
        dec_source = converted["declination_source"]
    else:
        true_heading = raw_heading
        declination = 0.0
        dec_source = "none"

    # 24 山 (用真北)
    result = heading_to_24mountain(true_heading)
    direction = heading_to_direction(true_heading)

    # 临界角警告
    warning = None
    if result["dual_candidate"]:
        warning = (
            f"距山界仅 {result['distance_to_boundary']:.1f}° (阈值 {DUAL_CANDIDATE_THRESHOLD_DEG}°), "
            f"建议远离金属/电器复测, 候选: {result['sans']}/{result['alt_sans']}"
        )

    return CompassMeasureResponse(
        input_channel=channel,
        raw_heading=round(raw_heading, 2),
        north_ref=body.north_ref,
        declination_deg=declination,
        declination_source=dec_source,
        true_heading=round(true_heading, 2),
        sans=result["sans"],
        alt_sans=result["alt_sans"],
        sans_zh=result["sans_zh"],
        trigram=result["trigram"],
        element=result["element"],
        direction=direction,
        dual_candidate=result["dual_candidate"],
        distance_to_boundary=result["distance_to_boundary"],
        quality=result["quality"],
        tip=result["tip"],
        fengshui_warning=warning,
    )


@router.post("/sessions", response_model=CompassSession)
def create_session(body: CompassSessionCreate):
    """创建罗盘采样会话."""
    sid = f"cmp_{uuid.uuid4().hex[:12]}"
    target_dir = body.direction_hint.replace("大门朝", "").replace("坐", "").strip()
    target_sans = DIRECTION_TO_SANS.get(target_dir, "子")
    session = CompassSession(
        session_id=sid,
        direction_hint=body.direction_hint,
        target_sans=target_sans,
        target_direction=target_dir,
        samples=[],
        readings=[],
        result_sans="",
        result_direction="",
        result_azimuth=0.0,
        std_dev=0.0,
        quality="low",
        north_ref=body.north_ref,
        created_at=datetime.now(timezone.utc).timestamp(),
    )
    _sessions[sid] = session
    return session


@router.post("/sessions/{session_id}/samples")
def add_sample(session_id: str, body: CompassSessionAddSample):
    """向采样会话追加一个方位读数."""
    if session_id not in _sessions:
        raise HTTPException(404, "session not found")
    s = _sessions[session_id]
    if s.closed:
        raise HTTPException(400, "session already closed")

    az = body.azimuth_deg
    s.samples.append(az)
    sans_info = heading_to_24mountain(az)
    direction = heading_to_direction(az)
    s.readings.append(CompassReading(
        sans=sans_info["sans"], direction=direction, azimuth_deg=az, device="phone_compass"
    ))

    if len(s.samples) >= 3:
        result_sans, result_dir, result_az, std_dev, quality = compute_result(s.samples)
        sans_24_info = heading_to_24mountain(result_az)
        s.result_sans = result_sans
        s.result_direction = result_dir
        s.result_azimuth = result_az
        s.std_dev = std_dev
        s.quality = quality
        s.dual_candidate = sans_24_info["dual_candidate"]
        s.alt_sans = sans_24_info["alt_sans"]
        s.distance_to_boundary = sans_24_info["distance_to_boundary"]
        s.closed = True

    return {"added": az, "samples_count": len(s.samples), "closed": s.closed}


@router.get("/sessions/{session_id}", response_model=CompassSession)
def get_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(404, "session not found")
    return _sessions[session_id]


@router.post("/readings", response_model=CompassReading)
def save_reading(body: CompassReading):
    """直接保存一个罗盘读数 (无需采样会话)."""
    sans = body.sans if body.sans in SANS_24 else heading_to_24mountain(body.azimuth_deg)["sans"]
    direction = body.direction if body.direction else heading_to_direction(body.azimuth_deg)
    return CompassReading(
        sans=sans, direction=direction, azimuth_deg=body.azimuth_deg,
        device=body.device, note=body.note, north_ref=body.north_ref,
    )


@router.get("/convert/{azimuth_deg}")
def convert_azimuth(azimuth_deg: float, north_ref: str = "magnetic",
                     lat: float | None = None, lng: float | None = None):
    """磁北偏角 → 24 山 + 8 方位 + 八卦 + 五行."""
    if north_ref == "magnetic" and lat is not None and lng is not None:
        converted = magnetic_to_true_heading(azimuth_deg, lat, lng)
        h = converted["true_heading"]
    else:
        h = azimuth_deg
    sans_info = heading_to_24mountain(h)
    direction = heading_to_direction(h)
    return {
        "azimuth_deg": round(normalize_heading(azimuth_deg), 1),
        "sans": sans_info["sans"],
        "sans_zh": sans_info["sans_zh"],
        "direction": direction,
        "trigram": sans_info["trigram"],
        "element": sans_info["element"],
        "fengshui_tip": sans_info["tip"],
        "dual_candidate": sans_info["dual_candidate"],
        "alt_sans": sans_info["alt_sans"],
        "distance_to_boundary": sans_info["distance_to_boundary"],
    }


# ── Sprint 3.3: 罗盘 → 风水 端到端 ────────────────────────────────────

class CompassFengShuiRequest(BaseModel):
    """罗盘测量 + 风水参数 → 端到端八宅/玄空.

    Sprint 3.3: 一接口完成 compass → 24 山 → bazhai/xuankong → 合并结果.
    """
    # ── 罗盘输入 (同 CompassMeasureRequest, 四通道) ──
    magnetic_heading_deg: float | None = None
    physical_compass_sans: str | None = None
    manual_azimuth_deg: float | None = None
    map_direction: str | None = None
    lat: float | None = None
    lng: float | None = None
    declination_deg: float | None = None
    north_ref: str = "magnetic"

    # ── 八字/出生 (八宅命卦需要) ──
    birth_year: int = Field(..., description="出生年 (八宅命卦)")
    gender: str = Field("unspecified", description="male / female / unspecified")

    # ── 风水参数 ──
    construction_year: int | None = None  # 建造年 (玄空运推算)
    period: int | None = None             # 显式玄空运 (1-9)
    facing: str | None = None             # 朝向 (8 方位)


class CompassFengShuiResponse(BaseModel):
    """罗盘-风水端到端输出."""
    # 罗盘结果
    sitting: str                          # 坐山 (24 山)
    sitting_zh: str                       # e.g. "卯山"
    direction: str                        # 8 方位
    true_heading: float                   # 真北方位角
    declination_deg: float                # 磁偏角
    quality: str                          # high / medium / low
    dual_candidate: bool
    alt_sitting: str | None = None
    fengshui_warning: str | None = None

    # 风水结果
    bazhai: dict | None = None           # 八宅排盘
    xuankong: dict | None = None         # 玄空排盘
    fengshui_summary: str = ""           # 综合摘要


@router.post("/fengshui", response_model=CompassFengShuiResponse)
def compass_fengshui(body: CompassFengShuiRequest):
    """罗盘 → 风水 端到端流水线.

    Sprint 3.3 + 重构: 一次调用完成
      1. 罗盘测量 (4 通道 + declination 校正) — 与 /measure 逻辑一致
      2. 24 山 → 坐山
      3. 通过 router.compute("fengshui", birth) 统一调度 bazhai + xuankong
      4. 综合风水评估
    """
    from divination.contracts import Birth
    from divination import router

    # ── 第一步: 罗盘测量 (复用 /measure 逻辑) ──
    if body.physical_compass_sans:
        if body.physical_compass_sans not in SANS_24:
            raise HTTPException(400, f"unknown sans: {body.physical_compass_sans}")
        idx = SANS_24.index(body.physical_compass_sans)
        raw_heading = float(idx * 15)
    elif body.magnetic_heading_deg is not None:
        raw_heading = float(body.magnetic_heading_deg)
    elif body.manual_azimuth_deg is not None:
        raw_heading = float(body.manual_azimuth_deg)
    elif body.map_direction:
        direction_to_az = {
            "正北": 0, "东北": 45, "正东": 90, "东南": 135,
            "正南": 180, "西南": 225, "正西": 270, "西北": 315,
        }
        if body.map_direction not in direction_to_az:
            raise HTTPException(400, f"unknown direction: {body.map_direction}")
        raw_heading = float(direction_to_az[body.map_direction])
    else:
        raise HTTPException(400, "no input channel provided")

    # declination 校正
    if body.north_ref == "magnetic" and (body.lat is not None or body.declination_deg is not None):
        if body.declination_deg is not None:
            converted = magnetic_to_true_heading(
                raw_heading, body.lat or 0, body.lng or 0,
                declination=body.declination_deg,
            )
        else:
            converted = magnetic_to_true_heading(
                raw_heading, body.lat or 0, body.lng or 0,
            )
        true_heading = converted["true_heading"]
        declination = converted["declination"]
    else:
        true_heading = raw_heading
        declination = 0.0

    sans_info = heading_to_24mountain(true_heading)
    direction = heading_to_direction(true_heading)

    # 临界角警告
    warning = None
    if sans_info["dual_candidate"]:
        warning = (
            f"距山界仅 {sans_info['distance_to_boundary']:.1f}° (阈值 {DUAL_CANDIDATE_THRESHOLD_DEG}°), "
            f"建议远离金属/电器复测, 候选: {sans_info['sans']}/{sans_info['alt_sans']}"
        )

    sitting = sans_info["sans"]

    # ── 第二步: 通过 router.compute("fengshui", birth) 统一调度 ──
    # 推算 period: 显式 > 建造年 > 出生年
    period = body.period
    if period is None:
        from divination.fengshui import san_yuan_jiu_yun
        period = san_yuan_jiu_yun(body.construction_year or body.birth_year)["运"]

    birth = Birth(
        year=body.birth_year,
        month=1, day=1, hour=12,        # 八宅/玄空只用年, 月日时给占位值
        gender=body.gender,
        calendar="gregorian",
        sitting=sitting,
        facing=body.facing or direction,
        construction_year=body.construction_year,
        period=period,
    )

    bazhai_result: dict | None = None
    xuankong_result: dict | None = None
    try:
        chart = router.compute("fengshui", birth)
        # fengshui 复合引擎 raw = { bazhai, xuankong, errors, summary, 吉方, 凶方, ... }
        bazhai_result = chart.raw.get("bazhai") or None
        xuankong_result = chart.raw.get("xuankong") or None
        if bazhai_result is not None:
            # 附上罗盘坐向 (信息增益, 与重构前一致)
            bazhai_result = {**bazhai_result, "坐山": sitting, "朝向": direction}
    except Exception:
        # 兜底: 直接调底层函数 (保持原行为)
        from divination.fengshui import bazhai as _bazhai, xuankong as _xk
        try:
            bazhai_result = _bazhai(body.birth_year, body.gender)
            bazhai_result["坐山"] = sitting
            bazhai_result["朝向"] = direction
        except Exception:
            pass
        try:
            xuankong_result = _xk(period, sitting)
        except Exception:
            pass

    # ── 第三步: 综合摘要 ──
    life_gua = bazhai_result.get("命卦", "N/A") if bazhai_result else "N/A"
    xuankong_pat = xuankong_result.get("格局", "待定") if xuankong_result else "待定"
    if isinstance(xuankong_pat, list):
        xuankong_pat = "、".join(str(p) for p in xuankong_pat) or "待定"
    summary = f"坐{sitting}山 ({direction}), 命卦{life_gua}, 玄空{xuankong_pat}"

    return CompassFengShuiResponse(
        sitting=sitting,
        sitting_zh=sans_info["sans_zh"],
        direction=direction,
        true_heading=round(true_heading, 2),
        declination_deg=declination,
        quality=sans_info["quality"],
        dual_candidate=sans_info["dual_candidate"],
        alt_sitting=sans_info["alt_sans"],
        fengshui_warning=warning,
        bazhai=bazhai_result,
        xuankong=xuankong_result,
        fengshui_summary=summary,
    )
