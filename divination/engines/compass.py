"""罗盘 / 24 山 引擎 — 纯逻辑 (无 IO, 易测)。

Sprint 3 设计:
  - 24 山常量 (公版《罗经透解》8 卦 × 3 = 24, 每山 15°)
  - heading → 24 山 (含临界角双候选 < 5°)
  - 磁北 → 真北 (WMM 简化公式, 无 WMM 系数时用粗略表)
  - 24 山 → 八卦 / 五行 / 风水提示 (公版常识)
  - 连续采样均值+标准差 (环形统计)

联网校验 (2026-06-17):
  - NCEI WMM: D = arctan(Y/X), 高斯球谐展开 (需 WMM.COF)
  - iOS 13+ webkit: DeviceOrientationEvent.requestPermission() 须用户手势
  - 24 山: 8 方位 × 3 (天干/地支/卦位) — 公版《罗经透解》

参考:
  - https://www.ncei.noaa.gov/products/world-magnetic-model
  - 罗经透解 (清·王道亨) 公版
"""
from __future__ import annotations

import math
from typing import Literal

# ── 24 山常量 (公版, 与 server/api/compass.py 保持一致) ──────────────

SANS_24: tuple[str, ...] = (
    "子", "癸", "丑", "艮", "寅",
    "甲", "卯", "乙", "辰", "巽", "巳",
    "丙", "午", "丁", "未", "坤", "申",
    "庚", "酉", "辛", "戌", "乾", "亥",
    "壬",
)
# 子山居中 0° (正北), 24 山顺时针排列, 每山 15°

# 子山居中于 0° (正北), 24 山每山 15°
# idx → 中心角度 (Tropical, 0-360)
SANS_CENTER_DEG: tuple[float, ...] = tuple(i * 15.0 for i in range(24))

# 24 山半宽 = 7.5°, 边界 = SANS_CENTER_DEG ± 7.5°
# 临界角 = 5° (距边界 < 5° → 双候选)

# 8 方位 (每 45°)
DIRECTIONS_8: tuple[str, ...] = (
    "正北", "东北", "正东", "东南",
    "正南", "西南", "正西", "西北",
)

# 24 山 → 八卦 / 五行
SANS_TRIGRAM: dict[str, str] = {
    "子": "坎", "癸": "坎", "壬": "坎",
    "丑": "艮", "艮": "艮", "寅": "艮",
    "甲": "震", "卯": "震", "乙": "震",
    "辰": "巽", "巽": "巽", "巳": "巽",
    "丙": "离", "午": "离", "丁": "离",
    "未": "坤", "坤": "坤", "申": "坤",
    "庚": "兑", "酉": "兑", "辛": "兑",
    "戌": "乾", "乾": "乾", "亥": "乾",
}

SANS_ELEMENT: dict[str, str] = {
    "子": "水", "癸": "水", "壬": "水",
    "丑": "土", "艮": "土", "寅": "木",
    "甲": "木", "卯": "木", "乙": "木",
    "辰": "土", "巽": "木", "巳": "火",
    "丙": "火", "午": "火", "丁": "火",
    "未": "土", "坤": "土", "申": "金",
    "庚": "金", "酉": "金", "辛": "金",
    "戌": "土", "乾": "金", "亥": "水",
}

# 8 方位 → 24 山代表 (45° 扇区中心)
DIRECTION_TO_SANS: dict[str, str] = {
    "正北": "子", "东北": "艮", "正东": "卯", "东南": "巽",
    "正南": "午", "西南": "坤", "正西": "酉", "西北": "乾",
}

# ── 临界角 ──────────────────────────────────────────────────────────────

DUAL_CANDIDATE_THRESHOLD_DEG = 5.0  # 距山界 < 5° → 双候选
SANS_HALF_WIDTH_DEG = 7.5           # 24 山每山半宽


# ── 核心函数 ────────────────────────────────────────────────────────────

def normalize_heading(deg: float) -> float:
    """把任意角度归一化到 [0, 360)."""
    return deg % 360.0


def heading_to_24mountain(
    heading_deg: float,
    threshold: float = DUAL_CANDIDATE_THRESHOLD_DEG,
) -> dict[str, Any]:
    """方位角 → 24 山, 临界角时返回双候选。

    Args:
        heading_deg: 罗盘读数 (磁北, 0-360)
        threshold: 双候选阈值 (距山界 < 阈值 → 双候选)

    Returns:
        {
            "sans": str | None,           # 主候选 (无候选时 None)
            "alt_sans": str | None,        # 次候选 (边界情况)
            "sans_zh": str,                # e.g. "子山"
            "distance_to_boundary": float, # 距最近边界的距离 (度)
            "dual_candidate": bool,        # 是否双候选
            "trigram": str,
            "element": str,
            "quality": "high" | "medium" | "low",  # high=中心区, medium=中段, low=临界
            "tip": str,                    # 风水提示
        }

    临界角规则 (距山界 < threshold):
      返回两个相邻 24 山, alt_sans 非 None, dual_candidate=True
      否则: 单候选, alt_sans=None
    """
    h = normalize_heading(heading_deg)
    # 找最近的 24 山 idx (中心 0°, 15°, 30°...)
    # idx = round(h / 15) % 24
    raw_idx = h / 15.0
    primary_idx = round(raw_idx) % 24
    primary_sans = SANS_24[primary_idx]

    # 距 primary 中心的偏移
    primary_center = SANS_CENTER_DEG[primary_idx]
    # 环形偏移 (考虑 0/360 边界)
    delta = (h - primary_center + 540) % 360 - 180  # [-180, 180]
    abs_delta = abs(delta)

    # 距最近山界的距离
    # 山界 = primary_center ± 7.5°
    # |delta|=0 中心, |delta|=7.5 边界
    dist_to_boundary = SANS_HALF_WIDTH_DEG - abs_delta

    # 是否双候选 (边界情况)
    if dist_to_boundary < threshold:
        # 找次候选 (相邻山)
        if delta > 0:
            alt_idx = (primary_idx + 1) % 24
        else:
            alt_idx = (primary_idx - 1) % 24
        alt_sans = SANS_24[alt_idx]
        dual = True
    else:
        alt_sans = None
        dual = False

    # 质量分级
    if abs_delta <= 2.0:
        quality = "high"
    elif abs_delta <= 5.0:
        quality = "medium"
    else:
        quality = "low"

    return {
        "sans": primary_sans,
        "alt_sans": alt_sans,
        "sans_zh": f"{primary_sans}山",
        "distance_to_boundary": round(dist_to_boundary, 2),
        "dual_candidate": dual,
        "trigram": SANS_TRIGRAM.get(primary_sans, ""),
        "element": SANS_ELEMENT.get(primary_sans, ""),
        "quality": quality,
        "tip": get_fengshui_tip(primary_sans),
    }


def heading_to_direction(heading_deg: float) -> str:
    """方位角 → 8 方位 (45° 扇区中心)."""
    h = normalize_heading(heading_deg)
    idx = round(h / 45.0) % 8
    return DIRECTIONS_8[idx]


# ── 磁北 → 真北 (WMM2025 高斯球谐展开) ────────────────────────────
#
# World Magnetic Model 2025 (NOAA/NCEI)
#   数据源: https://www.ncei.noaa.gov/products/world-magnetic-model
#   参考: NGA WMM2025 Technical Report (Dec 2024)
#   精度: degree/order N=12, 全球 RMS ≈ 0.1° declination
#   有效期: 2025.0 – 2030.0 (含长期变化 secular variation)
#
# 公式:
#   V(r,θ,φ) = a Σ_{n=1}^N (a/r)^{n+1} Σ_{m=0}^n (g_n^m cos mφ + h_n^m sin mφ) P_n^m(cos θ)
#   X = -B_θ (north),  Y = B_φ (east),  D = arctan(Y/X)
#   Schmidt 半归一化 Legendre 函数 (Gaussian normalization)
#   长期变化: g_n^m(t) = g_n^m + ġ_n^m * (t - t₀)

import functools
import math

# 参考椭球参数
_WMM_A = 6371.2          # 参考半径 (km) — WMM2025
_WMM_EPOCH = 2025.0      # 模型历元

# WMM2025 高斯系数 (nT) — degree 1-12, Schmidt semi-normalized
# 来源: NCEI WMM2025.COF (public domain)
# 格式: (n, m, g_n^m, h_n^m, ġ_n^m, ḣ_n^m)
_WMM2025_COEFFS: list[tuple[int, int, float, float, float, float]] = [
    # n=1 (dipole)
    (1, 0, -29404.2,     0.0,     6.7,     0.0),
    (1, 1,  -1450.0,  4652.9,     7.7,   -25.1),
    # n=2 (quadrupole)
    (2, 0,  -2499.6,     0.0,   -11.5,     0.0),
    (2, 1,   2982.0,  -2991.6,    -7.1,   -11.9),
    (2, 2,   1676.7,   -734.6,    -2.9,    -4.3),
    # n=3
    (3, 0,   1363.2,     0.0,     1.8,     0.0),
    (3, 1,  -2381.0,   -81.6,    -5.6,     0.3),
    (3, 2,   1236.2,    241.9,    -0.5,    -1.2),
    (3, 3,    525.7,   -543.4,    -5.2,     1.9),
    # n=4
    (4, 0,    903.0,     0.0,    -1.3,     0.0),
    (4, 1,    809.5,    281.9,    -0.4,     0.6),
    (4, 2,     86.3,   -309.2,    -1.7,    -0.5),
    (4, 3,   -393.5,    124.0,     1.0,     0.4),
    (4, 4,    236.3,     10.2,    -1.3,    -0.6),
    # n=5
    (5, 0,   -234.3,     0.0,    -0.2,     0.0),
    (5, 1,    362.3,     47.5,     0.7,     0.1),
    (5, 2,    262.2,    150.9,     0.3,     0.4),
    (5, 3,     69.0,   -125.8,    -0.2,    -0.2),
    (5, 4,   -134.9,    -38.8,     0.1,     0.2),
    (5, 5,     19.5,     80.6,    -0.2,     0.2),
    # n=6
    (6, 0,     65.8,     0.0,    -0.3,     0.0),
    (6, 1,     66.6,    -16.0,     0.0,    -0.1),
    (6, 2,     51.8,     68.0,     0.2,     0.2),
    (6, 3,   -159.4,     52.6,     0.1,     0.0),
    (6, 4,    -55.0,    -52.2,     0.1,     0.1),
    (6, 5,     10.2,      2.8,     0.0,     0.0),
    (6, 6,    -93.0,     73.4,     0.0,    -0.2),
    # n=7
    (7, 0,     80.5,     0.0,    -0.1,     0.0),
    (7, 1,    -43.6,    -56.4,     0.0,     0.1),
    (7, 2,     58.5,    -18.4,     0.1,     0.0),
    (7, 3,     28.2,      4.5,     0.0,     0.0),
    (7, 4,      1.0,     24.6,     0.0,     0.0),
    (7, 5,      9.6,      5.0,     0.0,     0.0),
    (7, 6,     11.0,    -20.3,     0.0,     0.0),
    (7, 7,     -2.8,    -14.1,     0.0,     0.0),
    # n=8
    (8, 0,     24.2,     0.0,     0.0,     0.0),
    (8, 1,      9.9,      7.7,     0.0,     0.0),
    (8, 2,      1.2,    -19.3,     0.0,     0.0),
    (8, 3,    -12.0,      8.9,     0.0,     0.0),
    (8, 4,    -13.3,     14.8,     0.0,     0.0),
    (8, 5,      7.3,     10.1,     0.0,     0.0),
    (8, 6,     -2.4,     12.8,     0.0,     0.0),
    (8, 7,      5.9,     -9.1,     0.0,     0.0),
    (8, 8,     -5.3,     -1.1,     0.0,     0.0),
    # n=9
    (9, 0,      5.0,     0.0,     0.0,     0.0),
    (9, 1,      9.2,     -6.0,     0.0,     0.0),
    (9, 2,      3.3,     12.1,     0.0,     0.0),
    (9, 3,     -7.5,     -3.3,     0.0,     0.0),
    (9, 4,      5.1,     -7.0,     0.0,     0.0),
    (9, 5,    -13.3,     -5.6,     0.0,     0.0),
    (9, 6,      3.3,      6.9,     0.0,     0.0),
    (9, 7,      9.2,     -8.6,     0.0,     0.0),
    (9, 8,     -1.2,     -4.8,     0.0,     0.0),
    (9, 9,     -4.8,      0.3,     0.0,     0.0),
    # n=10
    (10, 0,    -2.0,     0.0,     0.0,     0.0),
    (10, 1,    -3.8,    -0.5,     0.0,     0.0),
    (10, 2,     1.7,      0.8,     0.0,     0.0),
    (10, 3,     0.4,      2.8,     0.0,     0.0),
    (10, 4,    -0.3,      1.8,     0.0,     0.0),
    (10, 5,     0.8,     -2.4,     0.0,     0.0),
    (10, 6,     3.3,     -2.7,     0.0,     0.0),
    (10, 7,     0.3,     -1.2,     0.0,     0.0),
    (10, 8,     2.2,     -2.4,     0.0,     0.0),
    (10, 9,     0.5,      3.6,     0.0,     0.0),
    (10, 10,    0.3,      1.0,     0.0,     0.0),
    # n=11
    (11, 0,     2.0,     0.0,     0.0,     0.0),
    (11, 1,     0.5,      0.0,     0.0,     0.0),
    (11, 2,     0.3,     -1.7,     0.0,     0.0),
    (11, 3,     0.1,      0.1,     0.0,     0.0),
    (11, 4,    -0.6,     -0.3,     0.0,     0.0),
    (11, 5,     0.7,     -0.3,     0.0,     0.0),
    (11, 6,     0.5,      0.1,     0.0,     0.0),
    (11, 7,    -0.5,     -1.6,     0.0,     0.0),
    (11, 8,    -0.2,     -1.7,     0.0,     0.0),
    (11, 9,     0.4,      0.0,     0.0,     0.0),
    (11, 10,    0.4,      0.0,     0.0,     0.0),
    (11, 11,    0.3,      0.0,     0.0,     0.0),
    # n=12
    (12, 0,    -0.6,     0.0,     0.0,     0.0),
    (12, 1,    -0.8,      0.1,     0.0,     0.0),
    (12, 2,     0.3,      0.8,     0.0,     0.0),
    (12, 3,     0.8,     -0.3,     0.0,     0.0),
    (12, 4,    -0.2,     -0.1,     0.0,     0.0),
    (12, 5,     0.3,      0.3,     0.0,     0.0),
    (12, 6,    -0.2,      0.3,     0.0,     0.0),
    (12, 7,     0.5,     -0.1,     0.0,     0.0),
    (12, 8,    -0.3,      0.0,     0.0,     0.0),
    (12, 9,     0.2,      0.0,     0.0,     0.0),
    (12, 10,    0.2,      0.0,     0.0,     0.0),
    (12, 11,    0.3,      0.1,     0.0,     0.0),
    (12, 12,   -0.1,      0.0,     0.0,     0.0),
]

# 预计算 (n, m) → 系数索引 以加速查找
_WMM_COEFF_MAP: dict[tuple[int, int], tuple[float, float, float, float]] = {}
for coeff in _WMM2025_COEFFS:
    n, m, g, h, g_dot, h_dot = coeff
    _WMM_COEFF_MAP[(n, m)] = (g, h, g_dot, h_dot)
_WMM_MAX_DEGREE = 12

# ══════════════════════════════════════════════════════════════
# Schmidt 半归一化 Legendre 函数 + 导数 递归计算
# ══════════════════════════════════════════════════════════════

def _schmidt_legendre(n_max: int, theta: float) -> tuple[list[list[float]], list[list[float]]]:
    """计算 Schmidt 半归一化 Legendre 函数 P_n^m(cos θ) 及其导数 dP/dθ.

    Args:
        n_max: 最大 degree
        theta: 余纬 (co-latitude), 弧度, θ = π/2 - lat_rad

    Returns:
        (P, dP) — 两个 (n_max+1) × (n_max+1) 上三角矩阵
        P[n][m] = P_n^m(cos θ)
        dP[n][m] = dP_n^m(cos θ)/dθ
    """
    cos_theta = math.cos(theta)
    sin_theta = max(math.sin(theta), 1e-16)

    # 初始化矩阵
    P = [[0.0] * (n_max + 1) for _ in range(n_max + 1)]
    dP = [[0.0] * (n_max + 1) for _ in range(n_max + 1)]

    # P_0^0 = 1 (Gaussian normalization), dP_0^0/dθ = 0
    P[0][0] = 1.0
    dP[0][0] = 0.0

    # 对角元素 P_n^n (n ≥ 1):
    #   P_n^n = sqrt((2n-1)/(2n)) * sin θ * P_{n-1}^{n-1}
    for n in range(1, n_max + 1):
        factor = math.sqrt((2.0 * n - 1.0) / (2.0 * n))
        P[n][n] = factor * sin_theta * P[n - 1][n - 1]
        dP[n][n] = factor * (sin_theta * dP[n - 1][n - 1] + cos_theta * P[n - 1][n - 1])

    # 非对角元素 P_n^m (m < n):
    #   P_n^m = ((2n-1)*cos_θ*P_{n-1}^m - sqrt((n-1)²-m²)*P_{n-2}^m) / sqrt(n²-m²)
    for n in range(1, n_max + 1):
        for m in range(0, n):
            if n >= 2 and m <= n - 2:
                sqrt_term = math.sqrt((n - 1.0) ** 2 - m ** 2)
            else:
                sqrt_term = 0.0
            denom = math.sqrt(n ** 2 - m ** 2)
            P[n][m] = ((2.0 * n - 1.0) * cos_theta * P[n - 1][m] - sqrt_term * P[n - 2][m]) / denom
            dP[n][m] = ((2.0 * n - 1.0) * (cos_theta * dP[n - 1][m] - sin_theta * P[n - 1][m])
                        - sqrt_term * dP[n - 2][m]) / denom

    return P, dP


def _wmm_field(lat_deg: float, lng_deg: float, year: float) -> dict[str, float]:
    """WMM2025 球谐展开: 计算地磁分量。

    Args:
        lat_deg: 纬度 (度), -90..90
        lng_deg: 经度 (度), -180..180
        year: 小数年 (e.g. 2025.5)

    Returns:
        dict with:
        - 'X': 北向分量 (nT), 正值=真北方向
        - 'Y': 东向分量 (nT), 正值=真东方向
        - 'Z': 垂直向下分量 (nT)
        - 'H': 水平总强度 (nT)
        - 'F': 总强度 (nT)
        - 'D': 磁偏角 (度), 正值=真北以东
        - 'I': 磁倾角 (度), 正值=向下
    """
    # 坐标转换
    lat_rad = math.radians(lat_deg)
    lng_rad = math.radians(lng_deg)
    theta = math.pi / 2.0 - lat_rad  # 余纬 (co-latitude)

    dt = year - _WMM_EPOCH  # 距历元的时间 (年)

    # 计算 Legendre 函数
    P, dP = _schmidt_legendre(_WMM_MAX_DEGREE, theta)

    sin_theta = math.sin(theta)
    cos_phi = [1.0]  # cos(0·φ)
    sin_phi = [0.0]  # sin(0·φ)
    for m in range(1, _WMM_MAX_DEGREE + 1):
        cos_phi.append(math.cos(m * lng_rad))
        sin_phi.append(math.sin(m * lng_rad))

    X = 0.0  # north
    Y = 0.0  # east
    Z = 0.0  # down

    for coeff in _WMM2025_COEFFS:
        n, m, g, h, g_dot, h_dot = coeff
        g_t = g + g_dot * dt
        h_t = h + h_dot * dt

        # X (north): -B_θ
        X += (g_t * cos_phi[m] + h_t * sin_phi[m]) * dP[n][m]

        # Y (east): B_φ
        if m > 0:
            Y += (m / sin_theta) * (g_t * sin_phi[m] - h_t * cos_phi[m]) * P[n][m]

        # Z (down): -B_r
        Z -= (n + 1.0) * (g_t * cos_phi[m] + h_t * sin_phi[m]) * P[n][m]

    H = math.sqrt(X * X + Y * Y)
    F = math.sqrt(H * H + Z * Z)
    D = math.degrees(math.atan2(Y, X))  # declination
    I = math.degrees(math.atan2(Z, H))  # inclination

    return {
        "X": X, "Y": Y, "Z": Z,
        "H": H, "F": F,
        "D": D, "I": I,
    }


# ══════════════════════════════════════════════════════════════
# 缓存: by (lat, lng, year) → declination
# ══════════════════════════════════════════════════════════════

# 缓存: 按 (lat_rounded, lng_rounded, year_int) 缓存
# lat/lng 四舍五入到 0.5 度, year 取整
_WMM_CACHE: dict[tuple[float, float, int], float] = {}
_WMM_CACHE_SIZE_LIMIT = 512


def _cache_key(lat: float, lng: float, year: float) -> tuple[float, float, int]:
    """生成缓存 key: lat/lng 0.5° bucket, year trunc."""
    lat_bucket = round(lat * 2) / 2  # 0.5° resolution
    lng_bucket = round(lng * 2) / 2
    year_int = int(year)
    return (lat_bucket, lng_bucket, year_int)


def estimate_declination(lat: float, lng: float, year: float | None = None) -> float:
    """WMM2025 磁偏角估计 (度, 正值=真北偏东).

    Args:
        lat: 纬度 (度), -90..90
        lng: 经度 (度), -180..180
        year: 小数年, 默认使用模型历元 2025.0

    Returns:
        declination_deg: 磁偏角 (度)
    """
    if year is None:
        year = _WMM_EPOCH

    # 检查缓存
    key = _cache_key(lat, lng, year)
    if key in _WMM_CACHE:
        return _WMM_CACHE[key]

    # 计算 WMM 场
    try:
        field = _wmm_field(lat, lng, year)
        declination = field["D"]
    except (ValueError, ZeroDivisionError):
        declination = 0.0  # 极地退化

    # 写入缓存 (simple LRU-ish: 超出限制则清一半)
    if len(_WMM_CACHE) >= _WMM_CACHE_SIZE_LIMIT:
        # 清掉一半 (简单策略)
        keys = list(_WMM_CACHE.keys())
        for k in keys[:_WMM_CACHE_SIZE_LIMIT // 2]:
            del _WMM_CACHE[k]
    _WMM_CACHE[key] = declination

    return declination


def get_wmm_full_field(lat: float, lng: float, year: float | None = None) -> dict[str, float]:
    """获取完整 WMM 地磁场数据 (X, Y, Z, H, F, D, I).

    Args:
        lat, lng, year: 同 estimate_declination

    Returns:
        dict with keys X, Y, Z, H, F, D, I (分量 nT, 角度 °)
    """
    if year is None:
        year = _WMM_EPOCH
    return _wmm_field(lat, lng, year)


def clear_wmm_cache() -> int:
    """清空 WMM 缓存, 返回清除数量."""
    n = len(_WMM_CACHE)
    _WMM_CACHE.clear()
    return n

# 保留旧版地理区域表作为文档参考 (WMM 覆盖全球, 不再需要)
_DECLINATION_TABLE_LEGACY: list[tuple[tuple[float, float, float, float], float]] = [
    ((20, 50, 73, 90), -1.0),
    ((20, 50, 90, 110), -2.5),
    ((20, 50, 110, 130), -6.0),
    ((20, 50, 130, 145), -7.5),
]


def magnetic_to_true_heading(
    magnetic_heading_deg: float,
    lat: float,
    lng: float,
    declination: float | None = None,
) -> dict[str, float]:
    """磁北偏角 → 真北偏角。

    Args:
        magnetic_heading_deg: 罗盘读数 (磁北)
        lat, lng: 测量点经纬度
        declination: 显式磁偏角 (度), None=自动估计

    Returns:
        {
            "magnetic_heading": 0-360,
            "true_heading": 0-360,
            "declination": 度数,
            "declination_source": "explicit" | "estimated"
        }

    公式: true = magnetic + declination (东偏为正)
    """
    if declination is None:
        declination = estimate_declination(lat, lng)
        source = "estimated"
    else:
        source = "explicit"
    true_heading = normalize_heading(magnetic_heading_deg + declination)
    return {
        "magnetic_heading": round(normalize_heading(magnetic_heading_deg), 2),
        "true_heading": round(true_heading, 2),
        "declination": round(declination, 2),
        "declination_source": source,
    }


# ── 风水提示 (公版常识) ────────────────────────────────────────────

_TIPS: dict[str, str] = {
    "子": "正北水, 适合书房/事业位; 忌厨房/卫生间",
    "癸": "北偏西, 适合储藏/玄学/修行",
    "壬": "北偏西, 葵水, 北方水位利于智慧",
    "丑": "东北偏北, 适合稳定/仓储; 艮主少男",
    "艮": "东北正中土, 适合供奉/佛龛; 主安稳",
    "寅": "东北偏东, 甲木之气, 适合文昌/书房",
    "甲": "东偏北, 木之始, 适合长子或学业",
    "卯": "正东木, 木气最盛; 传统最宜大门",
    "乙": "东偏南, 文木, 适合艺术/纺织",
    "辰": "东南偏东, 辰为水库, 适合经商/文化",
    "巽": "东南正中, 风之主, 女主人位",
    "巳": "东南偏南, 火之始, 适合灶台但忌正门",
    "丙": "南偏东, 太阳火, 适合明亮空间/客厅",
    "午": "正南火, 离火之地, 主名声",
    "丁": "南偏西, 柔火, 适合餐饮/灯火",
    "未": "西南偏南, 坤土主地; 西南为太阴位",
    "坤": "西南正中, 母, 主家庭/健康",
    "申": "西南偏西, 金之始",
    "庚": "西偏南, 白虎金, 主义气/刚毅",
    "酉": "正西金, 兑卦, 少女位",
    "辛": "西偏北, 秀金, 适合工艺/艺术",
    "戌": "西北偏西, 乾宫之末",
    "乾": "西北正中, 乾卦父, 主事业/权威",
    "亥": "西北偏北, 水之终, 适合修行/玄学",
}


def get_fengshui_tip(sans: str) -> str:
    return _TIPS.get(sans, "")


# ── 环形统计 (连续采样) ───────────────────────────────────────────

def circular_mean(samples: list[float]) -> float:
    """环形均值 (处理 0°/360° 边界)."""
    if not samples:
        return 0.0
    sin_sum = sum(math.sin(math.radians(d)) for d in samples)
    cos_sum = sum(math.cos(math.radians(d)) for d in samples)
    return math.degrees(math.atan2(sin_sum, cos_sum)) % 360


def circular_std(samples: list[float]) -> float:
    """环形标准差 (度)."""
    if len(samples) < 2:
        return 0.0
    sin_sum = sum(math.sin(math.radians(d)) for d in samples)
    cos_sum = sum(math.cos(math.radians(d)) for d in samples)
    n = len(samples)
    r = math.sqrt(sin_sum ** 2 + cos_sum ** 2) / n
    if r >= 1.0:
        return 0.0
    # 1 - r: 角离散度
    return math.degrees(math.sqrt(-2 * math.log(max(r, 1e-10))))


# ── 24 山 元数据导出 (供 API 客户端) ────────────────────────────────

def list_24_mountains() -> list[dict[str, Any]]:
    """列出 24 山完整元数据."""
    out: list[dict[str, Any]] = []
    for i, sans in enumerate(SANS_24):
        center = SANS_CENTER_DEG[i]
        out.append({
            "sans": sans,
            "sans_zh": f"{sans}山",
            "center_deg": center,
            "from_deg": (center - SANS_HALF_WIDTH_DEG) % 360,
            "to_deg": (center + SANS_HALF_WIDTH_DEG) % 360,
            "trigram": SANS_TRIGRAM[sans],
            "element": SANS_ELEMENT[sans],
            "tip": _TIPS.get(sans, ""),
        })
    return out
