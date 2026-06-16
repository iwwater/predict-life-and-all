"""POST/GET /api/compass - 罗盘测量记录 + 连续采样。

24 山与 8 方位转换，供风水系术法（八宅/玄空/奇门）使用。
方案 §二-4 + §九。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/compass", tags=["compass"])

# ── 24 山 ────────────────────────────────────────────────────────────────────
SANS_24 = [
    "壬", "子", "癸", "丑", "艮", "寅",  # 北 → 东北
    "甲", "卯", "乙", "辰", "巽", "巳",  # 东 → 东南
    "丙", "午", "丁", "未", "坤", "申",  # 南 → 西南
    "庚", "酉", "辛", "戌", "乾", "亥",  # 西 → 西北
]

# 8 方位 → 24 山代表（每个 45° 扇区取中间那个山）
DIRECTION_TO_SANS: dict[str, str] = {
    "正北": "子",
    "东北": "艮",
    "正东": "卯",
    "东南": "巽",
    "正南": "午",
    "西南": "坤",
    "正西": "酉",
    "西北": "乾",
}

# 24 山 → 八卦
SANS_TRIGRAM: dict[str, str] = {
    "子": "坎", "癸": "坎", "丑": "艮", "艮": "艮", "寅": "艮",
    "甲": "震", "卯": "震", "乙": "震", "辰": "巽", "巽": "巽", "巳": "巽",
    "丙": "离", "午": "离", "丁": "离", "未": "坤", "坤": "坤", "申": "坤",
    "庚": "兑", "酉": "兑", "辛": "兑", "戌": "乾", "乾": "乾", "亥": "乾",
}

# 24 山 → 五行
SANS_ELEMENT: dict[str, str] = {
    "子": "水", "癸": "水", "丑": "土", "艮": "土", "寅": "木",
    "甲": "木", "卯": "木", "乙": "木", "辰": "土", "巽": "木", "巳": "火",
    "丙": "火", "午": "火", "丁": "火", "未": "土", "坤": "土", "申": "金",
    "庚": "金", "酉": "金", "辛": "金", "戌": "土", "乾": "金", "亥": "水",
}

# ── Pydantic 模型 ─────────────────────────────────────────────────────────────

class CompassReading(BaseModel):
    """单次罗盘测量。"""
    sans: str = Field(..., description="24 山 e.g. '子', '卯', '巽'")
    direction: str = Field(..., description="8 方位 e.g. '正北', '正东'")
    azimuth_deg: float = Field(..., ge=0, le=360, description="磁北偏角度数 0-360")
    device: str = Field(default="manual", description="测量来源: 'phone_compass' / 'manual' / '实体罗盘'")
    note: Optional[str] = None


class CompassSessionCreate(BaseModel):
    """创建采样会话。"""
    direction_hint: str = Field(..., description="预期坐向（用户口述）e.g. '大门朝东'")
    sample_count: int = Field(default=5, ge=2, le=20, description="采样次数")


class CompassSessionAddSample(BaseModel):
    """向采样会话追加一个读数。"""
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
    created_at: float
    closed: bool = False


# ── 内存存储 ─────────────────────────────────────────────────────────────────
_sessions: dict[str, CompassSession] = {}


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def azimuth_to_sans(azimuth_deg: float) -> str:
    """磁北偏角度数 → 24 山。"""
    # 24 山每山 15°，子山居中于 0°（正北）
    # 壬=337.5°, 子=352.5°, 癸=7.5°...
    normalized = azimuth_deg % 360
    # 24 等分，每个 15°，从子(0°)开始
    idx = round(normalized / 15) % 24
    return SANS_24[idx]


def azimuth_to_direction(azimuth_deg: float) -> str:
    """磁北偏角度数 → 8 方位。"""
    normalized = azimuth_deg % 360
    idx = round(normalized / 45) % 8
    dirs = ["正北", "东北", "正东", "东南", "正南", "西南", "正西", "西北"]
    return dirs[idx]


def compute_result(samples: list[float]) -> tuple[str, str, float, float, str]:
    """从一组方位角计算最终结果。

    Returns: (result_sans, result_direction, result_azimuth, std_dev, quality)
    """
    import statistics
    mean_deg = statistics.mean(samples)
    std = statistics.stdev(samples) if len(samples) > 1 else 0.0

    # 环形平均（处理 0°/360° 边界）
    sin_sum = sum(__import__("math").sin(__import__("math").radians(d)) for d in samples)
    cos_sum = sum(__import__("math").cos(__import__("math").radians(d)) for d in samples)
    mean_rad = __import__("math").atan2(sin_sum, cos_sum)
    circ_mean = __import__("math").degrees(mean_rad) % 360

    result_sans = azimuth_to_sans(circ_mean)
    result_dir = azimuth_to_direction(circ_mean)

    # 质量评估（标准差越小质量越高）
    if std <= 3.0:
        quality = "high"
    elif std <= 8.0:
        quality = "medium"
    else:
        quality = "low"

    return result_sans, result_dir, round(circ_mean, 1), round(std, 2), quality


# ── 端点 ─────────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=CompassSession)
def create_session(body: CompassSessionCreate):
    """创建罗盘采样会话。"""
    sid = f"cmp_{uuid.uuid4().hex[:12]}"
    # 从 direction_hint 反推目标山
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
        created_at=datetime.now(timezone.utc).timestamp(),
    )
    _sessions[sid] = session
    return session


@router.post("/sessions/{session_id}/samples")
def add_sample(session_id: str, body: CompassSessionAddSample):
    """向采样会话追加一个方位读数。"""
    if session_id not in _sessions:
        raise HTTPException(404, "session not found")
    s = _sessions[session_id]
    if s.closed:
        raise HTTPException(400, "session already closed")

    az = body.azimuth_deg
    s.samples.append(az)
    sans = azimuth_to_sans(az)
    direction = azimuth_to_direction(az)
    s.readings.append(CompassReading(
        sans=sans, direction=direction, azimuth_deg=az, device="phone_compass"
    ))

    # 自动结算：达到目标采样数则关闭
    if len(s.samples) >= 3:
        result_sans, result_dir, result_az, std_dev, quality = compute_result(s.samples)
        s.result_sans = result_sans
        s.result_direction = result_dir
        s.result_azimuth = result_az
        s.std_dev = std_dev
        s.quality = quality
        s.closed = True

    return {"added": az, "samples_count": len(s.samples), "closed": s.closed}


@router.get("/sessions/{session_id}", response_model=CompassSession)
def get_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(404, "session not found")
    return _sessions[session_id]


@router.post("/readings", response_model=CompassReading)
def save_reading(body: CompassReading):
    """直接保存一个罗盘读数（无需采样会话）。"""
    sans = body.sans if body.sans in SANS_24 else azimuth_to_sans(body.azimuth_deg)
    direction = body.direction if body.direction else azimuth_to_direction(body.azimuth_deg)
    return CompassReading(
        sans=sans,
        direction=direction,
        azimuth_deg=body.azimuth_deg,
        device=body.device,
        note=body.note,
    )


@router.get("/convert/{azimuth_deg}")
def convert_azimuth(azimuth_deg: float):
    """把磁北偏角转为 24 山 + 8 方位 + 八卦 + 五行。"""
    sans = azimuth_to_sans(azimuth_deg)
    direction = azimuth_to_direction(azimuth_deg)
    return {
        "azimuth_deg": round(azimuth_deg % 360, 1),
        "sans": sans,
        "sans_zh": f"{sans}山",
        "direction": direction,
        "trigram": SANS_TRIGRAM.get(sans, ""),
        "element": SANS_ELEMENT.get(sans, ""),
        "fengshui_tip": _fengshui_tip(sans),
    }


def _fengshui_tip(sans: str) -> str:
    tips = {
        "子": "正北水，适合做书房或事业位；忌做厨房/卫生间",
        "癸": "北偏西，适合储藏/玄学/修行",
        "丑": "东北偏北，适合稳定/仓储；艮主少男",
        "艮": "东北土，适合供奉/佛龛；主安稳",
        "寅": "东北偏东，甲木之气，适合文昌/书房",
        "甲": "东偏北，木之始，适合长子或学业",
        "卯": "正东木，木气最盛，传统最宜大门；东四宅之一",
        "乙": "东偏南，文木，适合艺术/纺织",
        "辰": "东南偏东，适合经商/文化；辰为水库",
        "巽": "东南正中，风之主，女主人位；东四宅之一",
        "巳": "东南偏南，火之始，适合灶台但忌正门",
        "丙": "南偏东，太阳火，适合明亮空间/客厅",
        "午": "正南火，离火之地，南四宅之一；主名声",
        "丁": "南偏西，柔火，适合餐饮/灯火",
        "未": "西南偏南，坤土主地；西南为太阴位",
        "坤": "西南正中，坤卦母，主家庭/健康；西四宅之一",
        "申": "西南偏西，金之始；庚金带阳刚",
        "庚": "西偏南，白虎金，主义气/刚毅；西四宅之一",
        "酉": "正西金，兑卦，少女位；西四宅之一",
        "辛": "西偏北，秀金，适合工艺/艺术",
        "戌": "西北偏西，乾宫之末；代表寺庙/高岗",
        "乾": "西北金，乾卦父，主事业/权威；西四宅之一",
        "亥": "西北偏北，水之终；适合修行/玄学",
        "壬": "北偏西，葵水；北方水位利于智慧",
    }
    return tips.get(sans, "")
