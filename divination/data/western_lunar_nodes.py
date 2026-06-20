"""西方占星 · 月亮交点 (Lunar Nodes) — 北交点与南交点。

文献：
  - *Tetrabiblos*（托勒密）— 古代占星传统
  - 现代心理占星（Steven Forrest, *The Inner Sky*）
  - 进化占星流派（Jeffrey Wolf Green）

天文：
  - 北交点 (North Node / Dragon's Head / Caput Draconis / 罗睺 Rahu)
  - 南交点 (South Node / Dragon's Tail / Cauda Draconis / 计都 Ketu)
  - 几何定义：月亮绕地轨道与黄道的两个交点（升交点/降交点）
  - 逆行运动：约 18.6 年回归一周
  - 平均每天退行 ~0.053° (~3'11"/天)

占星含义：
  - 北交点：今生发展方向、灵魂进化、需学习的课题
  - 南交点：前世/过去习惯、舒适区、需放下的执念
  - 与印度吠陀占星 (Jyotish) 的 Rahu/Ketu 概念相通
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

# ══════════════════════════════════════════════════════════════
# 1. 节点含义（占星释义）
# ══════════════════════════════════════════════════════════════
NODE_MEANINGS: dict[str, dict[str, str]] = {
    "北交点": {
        "name_en": "North Node / Caput Draconis / Rahu",
        "astronomical": "月亮绕地轨道升交点（黄道由南向北穿过）",
        "core": "今生发展方向、灵魂进化、需学习的课题",
        "shadow": "过度发展可致贪婪、不安、追逐虚幻",
        "keywords": "成长 / 方向 / 使命 / 进化",
        "house_meaning": "落入何宫, 即人生主战场 / 重点发展领域",
    },
    "南交点": {
        "name_en": "South Node / Cauda Draconis / Ketu",
        "astronomical": "月亮绕地轨道降交点（黄道由北向南穿过）",
        "core": "前世/过去习惯、舒适区、需放下的执念",
        "shadow": "过度依赖可致停滞、逃避、重复旧模式",
        "keywords": "过去 / 熟悉 / 释放 / 内在智慧",
        "house_meaning": "落入何宫, 即天然优势 / 需节制之处",
    },
}


# ══════════════════════════════════════════════════════════════
# 2. 12 星座 / 12 宫位的节点含义（速查表）
# ══════════════════════════════════════════════════════════════
NODE_IN_SIGNS: dict[str, dict[str, str]] = {
    "白羊": {
        "north": "学习独立、开创、勇敢行动, 放下过度依赖他人。",
        "south": "天生果决, 但需学会与人合作而非独断。",
    },
    "金牛": {
        "north": "学习建立稳定、价值观、物质安全感, 放下混乱。",
        "south": "天生稳重, 但需开放接受变化, 不固守舒适区。",
    },
    "双子": {
        "north": "学习沟通、学习、传递信息, 放下孤立。",
        "south": "天生善言, 但需深入而非浅尝辄止。",
    },
    "巨蟹": {
        "north": "学习情感表达、关怀、建立家庭, 放下冷漠。",
        "south": "天生敏感, 但需设界限, 不被情绪淹没。",
    },
    "狮子": {
        "north": "学习自信、创造、自我表达, 放下自我否定。",
        "south": "天生有创造力, 但需谦虚, 不独霸舞台。",
    },
    "处女": {
        "north": "学习精进、服务、分析能力, 放下混乱。",
        "south": "天生有条理, 但需接受不完美, 不求全责备。",
    },
    "天秤": {
        "north": "学习合作、关系、公平, 放下孤立或过度迁就。",
        "south": "天生擅平衡, 但需独立决策, 不依赖他人肯定。",
    },
    "天蝎": {
        "north": "学习深度、转化、情感真相, 放下表面化。",
        "south": "天生洞察, 但需放手, 不控制一切。",
    },
    "射手": {
        "north": "学习探索、信念、远见, 放下狭隘。",
        "south": "天生乐观, 但需落地, 不空想不切实际。",
    },
    "摩羯": {
        "north": "学习纪律、责任、长期建设, 放下急功近利。",
        "south": "天生有责任感, 但需开放情感, 不压抑人性。",
    },
    "水瓶": {
        "north": "学习独立、人道、革新, 放下传统束缚。",
        "south": "天生独特, 但需与人协作, 不孤立自赏。",
    },
    "双鱼": {
        "north": "学习慈悲、灵性、想象力, 放下混乱与逃避。",
        "south": "天生有灵性, 但需落地实修, 不沉溺幻象。",
    },
}


# ══════════════════════════════════════════════════════════════
# 3. 12 宫位的节点含义（速查表）
# ══════════════════════════════════════════════════════════════
NODE_IN_HOUSES: dict[str, dict[str, str]] = {
    1: {
        "north": "自我成长方向明确, 此生需建立独立人格。",
        "south": "前世已有强烈自我, 此生需学会让步。",
    },
    2: {
        "north": "此生重点发展价值观与物质基础。",
        "south": "前世已熟悉财务, 此生需放下执着。",
    },
    3: {
        "north": "此生重点发展沟通、学习、表达。",
        "south": "前世已善沟通, 此生需深入而非泛泛。",
    },
    4: {
        "north": "此生重点建立家庭、情感根基。",
        "south": "前世已熟悉家庭, 此生需走出舒适圈。",
    },
    5: {
        "north": "此生重点发展创造力、子女、自我表达。",
        "south": "前世已富有创造力, 此生需脚踏实地。",
    },
    6: {
        "north": "此生重点发展技能、服务、健康习惯。",
        "south": "前世已有技能, 此生需扩展视野。",
    },
    7: {
        "north": "此生重点发展关系、合作、伴侣。",
        "south": "前世已熟悉关系, 此生需先独立。",
    },
    8: {
        "north": "此生重点发展深度、转化、共享资源。",
        "south": "前世已熟悉权力, 此生需放手。",
    },
    9: {
        "north": "此生重点发展哲学、远行、高等教育。",
        "south": "前世已有智慧, 此生需专注当下。",
    },
    10: {
        "north": "此生重点发展事业、公众形象、使命。",
        "south": "前世已有成就, 此生需学会谦卑。",
    },
    11: {
        "north": "此生重点发展社群、理想、友谊。",
        "south": "前世已擅社交, 此生需深度连接。",
    },
    12: {
        "north": "此生重点发展灵性、内在、潜意识。",
        "south": "前世熟悉灵性, 此生需入世实践。",
    },
}


# ══════════════════════════════════════════════════════════════
# 4. 天文计算（北交点 + 南交点）
# ══════════════════════════════════════════════════════════════
# 占星常用 Mean Node (平均交点)
# 简单算法: 月亮黄经 - 月亮近地点角 + 180° ≈ 北交点
# 严格算法: 用 J2000 框架下月亮轨道升交点 (岁差修正 ~-0.053°/天)

# Mean Node J2000 起算 (约 125.044555° at J2000)
_MEAN_NODE_J2000 = 125.044555
_NODE_REGRESSION_PER_DAY = -0.0529539  # ~18.6 年回归 (逆行)
# 注意：实际 J2000 时 mean node ≈ 125.044555°, 但 sidereal/tropical 转换需 -0.5° 左右

# 节点符号
NODE_SYMBOLS = {
    "北交点": "☊",  # Dragon's Head
    "南交点": "☋",  # Dragon's Tail
}


def _julian_date(dt: datetime) -> float:
    """日期 → JD (简化版, 用于 Mean Node 计算)。"""
    import math
    y, m, d = dt.year, dt.month, dt.day
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + B - 1524.5


def _mean_node_longitude(dt: datetime) -> float:
    """计算平均月亮交点黄经（Tropical）。

    算法：
      T = (JD - 2451545.0) / 36525.0  (J2000 起儒略世纪)
      Ω = 125.044555 - 1934.13626 * T (天文算法精度)

    Returns:
        月亮北交点黄经（度, 0-360, Tropical）
    """
    jd = _julian_date(dt)
    T = (jd - 2451545.0) / 36525.0
    # Meeus 天文算法 (简化)
    omega = 125.044555 - 1934.13626 * T + 0.0021 * T * T
    return omega % 360


def _south_node_longitude(dt: datetime) -> float:
    """南交点 = 北交点 + 180°。"""
    return (_mean_node_longitude(dt) + 180.0) % 360


def compute_nodes(year: int, month: int, day: int,
                  hour: int = 12, minute: int = 0) -> dict[str, Any]:
    """计算月亮北交点与南交点黄经。

    Args:
        year, month, day: 公历日期
        hour, minute: 时间（默认正午, 节点每日变化极小, ±1° ≈ 18.6 天）

    Returns:
        {
            "north_node_lon": 北交点黄经（度）,
            "south_node_lon": 南交点黄经（度）,
            "north_sign": 北交点所在星座（中文）,
            "south_sign": 南交点所在星座（中文）,
            "delta_to_true_node": 与真节点的偏差 (需 JPL 星历, 此处约 ±1-2°),
            "computation": "Mean Node (Tropical)"
        }
    """
    dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("UTC"))
    north_lon = _mean_node_longitude(dt)
    south_lon = (north_lon + 180.0) % 360

    return {
        "north_node_lon": round(north_lon, 4),
        "south_node_lon": round(south_lon, 4),
        "north_sign": _lon_to_sign_cn(north_lon),
        "south_sign": _lon_to_sign_cn(south_lon),
        "north_symbol": NODE_SYMBOLS["北交点"],
        "south_symbol": NODE_SYMBOLS["南交点"],
        "delta_to_true_node": "约 ±1-2°（需 JPL 星历校准）",
        "computation": "Mean Node (Tropical, Meeus 简化)",
        "retrograde": True,  # 节点永远逆行
    }


def _lon_to_sign_cn(lon: float) -> str:
    """黄经 → 中文星座。"""
    signs = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
             "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
    idx = int(lon // 30) % 12
    return signs[idx]


# ══════════════════════════════════════════════════════════════
# 5. 综合查询
# ══════════════════════════════════════════════════════════════
def get_node_interpretation(north_lon: float, house: int | None = None) -> dict[str, str]:
    """根据北交点位置 + 宫位,返回完整占星解读。

    Args:
        north_lon: 北交点黄经（度）
        house: 北交点所在宫位 (1-12), 可选

    Returns:
        {sign_meaning, north_meaning, south_meaning, house_meaning (可选)}
    """
    sign = _lon_to_sign_cn(north_lon)
    south_lon = (north_lon + 180.0) % 360
    south_sign = _lon_to_sign_cn(south_lon)

    result = {
        "north_sign": sign,
        "north_meaning": NODE_IN_SIGNS.get(sign, {}).get("north", ""),
        "south_sign": south_sign,
        "south_meaning": NODE_IN_SIGNS.get(south_sign, {}).get("south", ""),
    }
    if house is not None and 1 <= house <= 12:
        result["house"] = house
        result["house_meaning_north"] = NODE_IN_HOUSES.get(house, {}).get("north", "")
        result["house_meaning_south"] = NODE_IN_HOUSES.get(house, {}).get("south", "")

    return result


# ══════════════════════════════════════════════════════════════
# 6. 节点与本命行星相位（Phase F · 月亮交点相位）
# ══════════════════════════════════════════════════════════════
# 节点与本命行星的相位关系, 是判断灵魂课题的关键指标

NODE_ASPECTS: dict[str, dict[str, str]] = {
    "合": {"degree": 0, "orb": 3.0, "meaning": "强势连接, 节点与该行星同频, 是此生核心议题。"},
    "六合": {"degree": 60, "orb": 2.0, "meaning": "和谐连接, 节点与该行星互补, 易得助。"},
    "拱": {"degree": 120, "orb": 2.0, "meaning": "流动连接, 节点与该行星自然整合, 大吉。"},
    "刑": {"degree": 90, "orb": 1.5, "meaning": "紧张连接, 节点与该行星冲突, 需调整。"},
    "冲": {"degree": 180, "orb": 3.0, "meaning": "对立连接, 节点与该行星对峙, 大课题。"},
}


def check_node_aspect(node_lon: float, planet_lon: float, orb: float | None = None) -> dict | None:
    """检查节点与某行星的相位。

    Args:
        node_lon: 节点黄经（度）
        planet_lon: 行星黄经（度）
        orb: 容许度（度, None 时使用默认）

    Returns:
        {aspect: 名称, degree: 实际度数差, orb_diff: 与精确相位之差, exact: 是否精确相位}
        或 None (无相位)
    """
    diff = abs((planet_lon - node_lon) % 360)
    if diff > 180:
        diff = 360 - diff

    for aspect_name, info in NODE_ASPECTS.items():
        target = info["degree"]
        use_orb = orb if orb is not None else info["orb"]
        if abs(diff - target) <= use_orb:
            return {
                "aspect": aspect_name,
                "target_degree": target,
                "actual_diff": round(diff, 2),
                "orb_diff": round(abs(diff - target), 2),
                "exact": abs(diff - target) < 0.5,
                "meaning": info["meaning"],
            }
    return None


def find_all_node_aspects(node_lon: float, natal_planets: dict[str, float],
                          orb: float | None = None) -> list[dict]:
    """检查节点与所有本命行星的相位。

    Args:
        node_lon: 节点黄经
        natal_planets: {planet: longitude} 本命盘所有行星黄经
        orb: 容许度（默认）

    Returns:
        [{aspect_info, planet}, ...] 所有触发的相位
    """
    aspects = []
    for planet, planet_lon in natal_planets.items():
        aspect = check_node_aspect(node_lon, planet_lon, orb)
        if aspect:
            aspect_info = dict(aspect)
            aspect_info["planet"] = planet
            aspects.append(aspect_info)
    # 按紧张程度排序 (冲 > 刑 > 拱 > 六合 > 合)
    order = {"冲": 5, "刑": 4, "拱": 3, "六合": 2, "合": 1}
    aspects.sort(key=lambda a: -order.get(a["aspect"], 0))
    return aspects


# ══════════════════════════════════════════════════════════════
# 7. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 西方月亮交点 自检 ===\n")

    # 1. 计算示例
    print("1. 北/南交点计算:")
    for y, m, d in [(2026, 6, 18), (1990, 5, 15), (2000, 1, 1)]:
        r = compute_nodes(y, m, d)
        print(f"   {y}-{m:02d}-{d:02d}: 北交点 {r['north_node_lon']:.2f}° ({r['north_sign']} {r['north_symbol']}) "
              f"| 南交点 {r['south_node_lon']:.2f}° ({r['south_sign']} {r['south_symbol']})")

    # 2. 解读示例
    print("\n2. 解读示例:")
    interp = get_node_interpretation(60.0, house=7)  # 双子座第 7 宫
    print(f"   北交点 {interp['north_sign']}: {interp['north_meaning']}")
    print(f"   南交点 {interp['south_sign']}: {interp['south_meaning']}")
    print(f"   第 7 宫: 北={interp['house_meaning_north']}")
    print(f"           南={interp['house_meaning_south']}")

    # 3. 12 星座速查
    print("\n3. 12 星座含义 (北交点):")
    for sign, m in NODE_IN_SIGNS.items():
        print(f"   {sign}: {m['north']}")

    # 4. 12 宫位速查
    print("\n4. 12 宫位含义 (北交点):")
    for h in range(1, 13):
        print(f"   第{h}宫: {NODE_IN_HOUSES[h]['north']}")

    # 5. 节点与行星相位检测示例
    print("\n5. 节点与行星相位示例:")
    # 测试: 北交点在白羊 0°, 太阳在 1° → 合相位
    r = check_node_aspect(0.0, 1.0)
    print(f"   节点 0° + 行星 1°: {r}")
    r = check_node_aspect(0.0, 180.0)
    print(f"   节点 0° + 行星 180°: {r}")
    r = check_node_aspect(0.0, 90.0)
    print(f"   节点 0° + 行星 90° (刑): {r}")
    r = check_node_aspect(0.0, 60.0)
    print(f"   节点 0° + 行星 60° (六合): {r}")
    r = check_node_aspect(0.0, 50.0)
    print(f"   节点 0° + 行星 50° (无相位): {r}")

    # 6. 多行星相位
    print("\n6. 多行星相位 (节点在 0°, 多行星):")
    natal = {"太阳": 1.0, "月亮": 180.0, "金星": 60.0, "火星": 50.0}
    aspects = find_all_node_aspects(0.0, natal)
    for a in aspects:
        print(f"   {a['planet']:6s}: {a['aspect']} (差 {a['actual_diff']}°)")
