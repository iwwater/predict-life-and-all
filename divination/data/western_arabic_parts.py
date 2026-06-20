"""西方占星 · 进阶点 (Arabic Parts + Lilith)。

文献:
  - *Tetrabiblos*（托勒密）— 古典 Arabic Parts 源头 (Lots)
  - *The Astrology of the Fates* (D. Forrest) — 7 主 Lot 详解
  - 现代心理占星 (Liz Greene, Howard Sasportas) — Black Moon Lilith

一、Black Moon Lilith (黑月莉莉丝)
  - 天文: 月亮绕地轨道的远地点 (apogee)
  - 占星: 阴影面、被压抑的女性力量、原始本能
  - 与月亮平均位置偏差可达 ±12° (椭圆轨道)
  - 逆行 (总是)

二、Arabic Parts (阿拉伯点 / Lots / 命运点)
  托勒密 Tetrabiblos 介绍的核心 Lots:
  - Lot of Fortune (Pars Fortunae)        — 福点
  - Lot of Spirit (Pars Spiritus)         — 灵点
  - Lot of Eros (Lot of Love)             — 爱点
  - Lot of Necessity                      — 必然点
  - Lot of Courage                        — 勇气点
  - Lot of Victory                        — 胜利点
  - Lot of Marriage (Day chart)           — 婚姻点 (日生)
  - Lot of Marriage (Night chart)         — 婚姻点 (夜生)

  公式:
    Day chart: ASC + Planet - Sun
    Night chart: ASC + Sun - Planet

  示例 (Lot of Fortune):
    日生: ASC + Moon - Sun
    夜生: ASC + Sun - Moon
"""
from __future__ import annotations

from typing import Any


# ══════════════════════════════════════════════════════════════
# 1. Black Moon Lilith (黑月莉莉丝)
# ══════════════════════════════════════════════════════════════

# Lilith 天文参数: 月亮远地点位置 (J2000 起算)
# 月亮远地点约 8.85 年回归一周, 平均周期 3231.4 天
_LILITH_PERIOD_DAYS = 3231.4
_LILITH_J2000_LON = 93.5  # J2000 时刻 (2000-01-01 12:00 UTC) 月亮远地点黄经约 93.5°

# 平均每日移动
_LILITH_DAILY_MOTION = 360.0 / _LILITH_PERIOD_DAYS  # ≈ 0.1114°/天


def _julian_date(dt) -> float:
    """日期 → JD。"""
    import math
    y, m, d = dt.year, dt.month, dt.day
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + B - 1524.5


def compute_lilith(year: int, month: int, day: int,
                   hour: int = 12, minute: int = 0) -> dict[str, Any]:
    """计算 Black Moon Lilith (月亮远地点) 黄经。

    Args:
        year, month, day: 公历日期
        hour, minute: 时间

    Returns:
        {lilith_lon, lilith_sign, computation}
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("UTC"))
    jd = _julian_date(dt)
    days_since_j2000 = jd - 2451545.0
    lilith_lon = (_LILITH_J2000_LON + days_since_j2000 * _LILITH_DAILY_MOTION) % 360
    return {
        "lilith_lon": round(lilith_lon, 4),
        "lilith_sign": _lon_to_sign_cn(lilith_lon),
        "computation": "Mean Lilith (Moon Apogee, Tropical)",
        "retrograde": True,
        "orbit_period_years": round(_LILITH_PERIOD_DAYS / 365.25, 2),
    }


# ══════════════════════════════════════════════════════════════
# 2. Lilith 12 星座含义
# ══════════════════════════════════════════════════════════════
LILITH_IN_SIGNS: dict[str, str] = {
    "白羊": "原始冲动、独立、被压抑的攻击性",
    "金牛": "感官欲望、对物质/身体的不安全感",
    "双子": "言语阴影、被压抑的言语、狡黠",
    "巨蟹": "女性阴影面、母性创伤、情绪吞噬",
    "狮子": "虚荣阴影、被压抑的创造力、骄傲",
    "处女": "完美主义阴影、被压抑的身体、洁净执念",
    "天秤": "关系阴影、被压抑的不平衡、美学执念",
    "天蝎": "性/死亡阴影、原始力量、转化之痛",
    "射手": "信仰阴影、被压抑的异端、远方执念",
    "摩羯": "权力阴影、被压抑的野心、冷漠",
    "水瓶": "个性阴影、被压抑的反叛、人群疏离",
    "双鱼": "灵性阴影、被压抑的慈悲、沉溺幻象",
}


# ══════════════════════════════════════════════════════════════
# 3. Arabic Parts (Lots) 定义
# ══════════════════════════════════════════════════════════════
# 公式: Day = ASC + Planet - Sun; Night = ASC + Sun - Planet
# 等同: Lot = ASC + Planet - Luminaries (Luminary)

ARABIC_PARTS: list[dict[str, Any]] = [
    {
        "name": "Lot of Fortune",
        "name_cn": "福点",
        "formula_day": "ASC + Moon - Sun",
        "formula_night": "ASC + Sun - Moon",
        "meaning": "物质幸福、健康、财富、世俗成就。",
        "house_meaning": "落入何宫, 即物质利益在何处实现。",
        "category": "核心",
    },
    {
        "name": "Lot of Spirit",
        "name_cn": "灵点",
        "formula_day": "ASC + Sun - Moon",
        "formula_night": "ASC + Moon - Sun",
        "meaning": "精神追求、灵性方向、内在使命。",
        "house_meaning": "落入何宫, 即精神成就所在。",
        "category": "核心",
    },
    {
        "name": "Lot of Eros",
        "name_cn": "爱点",
        "formula_day": "ASC + Venus - Sun",
        "formula_night": "ASC + Sun - Venus",
        "meaning": "情感连接、欲望、爱情模式。",
        "house_meaning": "落入何宫, 即情感投入所在。",
        "category": "关系",
    },
    {
        "name": "Lot of Necessity",
        "name_cn": "必然点",
        "formula_day": "ASC + Mercury - Sun",
        "formula_night": "ASC + Sun - Mercury",
        "meaning": "不可避免的课题、命运、限制。",
        "house_meaning": "落入何宫, 即必修之课所在。",
        "category": "核心",
    },
    {
        "name": "Lot of Courage",
        "name_cn": "勇气点",
        "formula_day": "ASC + Mars - Sun",
        "formula_night": "ASC + Sun - Mars",
        "meaning": "勇气、行动力、战斗精神。",
        "house_meaning": "落入何宫, 即发挥勇气的领域。",
        "category": "行动",
    },
    {
        "name": "Lot of Victory",
        "name_cn": "胜利点",
        "formula_day": "ASC + Jupiter - Sun",
        "formula_night": "ASC + Sun - Jupiter",
        "meaning": "胜利、扩展、信心、成功。",
        "house_meaning": "落入何宫, 即胜利所在。",
        "category": "行动",
    },
    {
        "name": "Lot of Marriage",
        "name_cn": "婚姻点",
        "formula_day": "ASC + Venus - Saturn",
        "formula_night": "ASC + Saturn - Venus",
        "meaning": "伴侣、承诺、关系的长期承诺度。",
        "house_meaning": "落入何宫, 即关系承诺所在。",
        "category": "关系",
    },
]


# 便捷别名映射 (中文/英文 → Lot of Xxx)
PART_NAME_ALIASES: dict[str, str] = {
    "福点": "Lot of Fortune",
    "灵点": "Lot of Spirit",
    "爱点": "Lot of Eros",
    "必然点": "Lot of Necessity",
    "勇气点": "Lot of Courage",
    "胜利点": "Lot of Victory",
    "婚姻点": "Lot of Marriage",
    "Lot of Fortune": "Lot of Fortune",
    "Lot of Spirit": "Lot of Spirit",
    "Lot of Eros": "Lot of Eros",
    "Lot of Necessity": "Lot of Necessity",
    "Lot of Courage": "Lot of Courage",
    "Lot of Victory": "Lot of Victory",
    "Lot of Marriage": "Lot of Marriage",
}


# ══════════════════════════════════════════════════════════════
# 4. Lot 计算引擎
# ══════════════════════════════════════════════════════════════
# ── 12 星座中文 ──
_SIGN_CN = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
            "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]


def _lon_to_sign_cn(lon: float) -> str:
    return _SIGN_CN[int(lon // 30) % 12]


def _normalize_lon(lon: float) -> float:
    """规范化黄经到 0-360 范围。"""
    return lon % 360


def _is_day_chart(sun_house: int) -> bool:
    """判断日生 vs 夜生 (简化: 太阳在第 7-12 宫为夜生, 1-6 宫为日生)。

    Args:
        sun_house: 太阳所在宫位 (1-12)

    Returns:
        True = 日生, False = 夜生
    """
    return sun_house <= 6


def compute_arabic_part(part_name: str, asc_lon: float,
                        planet_lon: float, sun_lon: float,
                        is_day: bool) -> dict[str, Any]:
    """计算某 Arabic Part (Lot) 的黄经。

    Args:
        part_name: Lot 名称 (支持中英文别名, 如 "Lot of Fortune" / "福点")
        asc_lon: ASC (上升点) 黄经
        planet_lon: 主行星黄经
        sun_lon: 太阳黄经
        is_day: True = 日生, False = 夜生

    Returns:
        {part_name, formula_used, lot_lon, lot_sign}
    """
    # 解析别名
    canonical_name = PART_NAME_ALIASES.get(part_name, part_name)
    part_info = next((p for p in ARABIC_PARTS if p["name"] == canonical_name), None)
    if part_info is None:
        raise ValueError(f"未知 Lot: {part_name}")

    # 日生: ASC + Planet - Sun; 夜生: ASC + Sun - Planet
    if is_day:
        lot_lon = _normalize_lon(asc_lon + planet_lon - sun_lon)
        formula_used = part_info["formula_day"]
    else:
        lot_lon = _normalize_lon(asc_lon + sun_lon - planet_lon)
        formula_used = part_info["formula_night"]

    return {
        "part_name": canonical_name,
        "part_name_cn": part_info["name_cn"],
        "formula_used": formula_used,
        "lot_lon": round(lot_lon, 4),
        "lot_sign": _lon_to_sign_cn(lot_lon),
        "is_day_chart": is_day,
    }


def compute_all_main_lots(asc_lon: float, sun_lon: float,
                          moon_lon: float, mercury_lon: float,
                          venus_lon: float, mars_lon: float,
                          jupiter_lon: float, saturn_lon: float,
                          sun_house: int) -> list[dict[str, Any]]:
    """批量计算 7 个核心 Lot。

    Returns:
        7 个 Lot 的计算结果列表
    """
    is_day = _is_day_chart(sun_house)
    lots = []
    planet_map = [
        ("Lot of Fortune", moon_lon),
        ("Lot of Spirit", sun_lon),
        ("Lot of Eros", venus_lon),
        ("Lot of Necessity", mercury_lon),
        ("Lot of Courage", mars_lon),
        ("Lot of Victory", jupiter_lon),
        ("Lot of Marriage", venus_lon),  # 婚姻点公式特殊: 用 venus + saturn
    ]
    saturn_lon_val = saturn_lon
    for part_name, planet_lon in planet_map:
        try:
            if part_name == "Lot of Marriage":
                # 婚姻点: ASC + Venus - Saturn, 夜生: ASC + Saturn - Venus
                if is_day:
                    lot_lon = _normalize_lon(asc_lon + venus_lon - saturn_lon_val)
                else:
                    lot_lon = _normalize_lon(asc_lon + saturn_lon_val - venus_lon)
                formula = "ASC + Venus - Saturn" if is_day else "ASC + Saturn - Venus"
                lots.append({
                    "part_name": "Lot of Marriage",
                    "part_name_cn": "婚姻点",
                    "formula_used": formula,
                    "lot_lon": round(lot_lon, 4),
                    "lot_sign": _lon_to_sign_cn(lot_lon),
                    "is_day_chart": is_day,
                })
            else:
                lots.append(compute_arabic_part(part_name, asc_lon, planet_lon, sun_lon, is_day))
        except ValueError:
            continue
    return lots


# ══════════════════════════════════════════════════════════════
# 5. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 西方占星进阶点 (Lilith + Arabic Parts) 自检 ===\n")

    # 1. Lilith 计算
    print("1. Black Moon Lilith:")
    for y, m, d in [(2026, 6, 18), (1990, 5, 15)]:
        r = compute_lilith(y, m, d)
        print(f"   {y}-{m:02d}-{d:02d}: Lilith {r['lilith_lon']:.2f}° ({r['lilith_sign']}) 轨道周期 {r['orbit_period_years']} 年")

    # 2. Arabic Parts 计算
    print("\n2. Arabic Parts 计算示例 (假设盘):")
    # 假设: ASC=120°, 太阳=90°, 月亮=180°, 水星=85°, 金星=110°, 火星=200°, 木星=60°, 土星=300°
    asc = 120.0
    sun = 90.0
    planets = {"月亮": 180.0, "水星": 85.0, "金星": 110.0, "火星": 200.0, "木星": 60.0, "土星": 300.0}
    lots = compute_all_main_lots(asc, sun, planets["月亮"], planets["水星"],
                                  planets["金星"], planets["火星"], planets["木星"], planets["土星"],
                                  sun_house=10)  # 太阳第 10 宫 → 日生
    print(f"   日生: 太阳在第 10 宫 → {len(lots)} 个 Lot:")
    for lot in lots:
        print(f"   - {lot['part_name_cn']:8s} ({lot['part_name']}): {lot['lot_lon']:.2f}° ({lot['lot_sign']}) [{lot['formula_used']}]")

    # 3. Lilith 12 星座
    print("\n3. Lilith 12 星座含义:")
    for sign, meaning in LILITH_IN_SIGNS.items():
        print(f"   {sign}: {meaning}")
