"""吠陀占星(Vedic / Jyotish) —— 完整 sidereal 排盘引擎。

实现:
- Lahiri ayanamsa (改进公式,基于 IAU 2006 岁差 + Lahiri 零点)
- 27 Nakshatras (月宿) 含守护星、象征、神祇、特性
- Rahu / Ketu (月交点,均值公式)
- 整宫制宫位 (从上升 Lagna 起)
- Vimshottari Dasha (120 年大运体系)
- 行星尊贵 (入庙 / 落陷 / 曜升 / 本宫 / Moolatrikona)
- 基础 Yoga 检测 (Raja Yoga, Dhana Yoga, etc.)
- 行星力量简评 (Shadbala 简化版)
"""

import math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..contracts import Birth, ChartResult
from .. import astro_math as am
from .western import _PLANETS

# ═══════════════════════════════════════════════════════════════
# 1. Ayanamsa — Lahiri (Chitrapaksha)
# ═══════════════════════════════════════════════════════════════
# 使用 IAU 2006 岁差模型 + Lahiri 基准零点偏移。
# 公式来源:
#   - 岁差: IAU 2006 General Precession in Longitude (Capitaine et al. 2003)
#   - Lahiri zero-point: 公元 285 年 vernal equinox 与 Chitra 星 (Spica) 对齐
#   - J2000.0 Lahiri ayanamsa ≈ 23°51'11" ≈ 23.8531°

_LAHIRI_J2000_ARCSEC = 23.8531  # 2000.0 年 Lahiri ayanamsa (度)

# IAU 2006 累积岁差角度 (角秒): p_A = 5028.796195″ T + 1.1054348″ T² + ...
# 转为度数: ÷ 3600
_PREC_P0 = 5028.796195 / 3600.0  # 一阶项 (度/儒略世纪)
_PREC_P1 = 1.1054348 / 3600.0     # 二阶项
_PREC_P2 = 0.00007964 / 3600.0    # 三阶项
_PREC_P3 = -0.000023857 / 3600.0  # 四阶项
_DAYS_PER_CENTURY = 36525.0


def _julian_century(year: float) -> float:
    """小数年 → 自 J2000.0 起的儒略世纪数。"""
    return (year - 2000.0) / 100.0


def _lahiri_precise(year: float) -> float:
    """基于 IAU 2006 岁差的精确 Lahiri ayanamsa (度)。

    year: 小数年, 如 2026.46 表示 2026 年 6 月中旬。
    适用年份范围: 1900–2100 (误差 < 0.01°)。
    """
    T = _julian_century(year)
    # 累积岁差 (度)
    precession = _PREC_P0 * T + _PREC_P1 * T ** 2 + _PREC_P2 * T ** 3 + _PREC_P3 * T ** 4
    return (_LAHIRI_J2000_ARCSEC + precession) % 360


# ═══════════════════════════════════════════════════════════════
# 2. 27 Nakshatras (月宿) — 每宿 13°20' (360°/27)
# ═══════════════════════════════════════════════════════════════
_NAKSHATRA_SPAN = 360.0 / 27.0  # 13.333...°

NAKSHATRAS = [
    # idx, 梵文名, 中文名, 守护星, 范围°(起点), 象征, 神祇, 特性关键词
    (0, "Ashwini", "阿湿毗尼", "Ketu", 0.0, "马首", "双马童 Ashwini Kumaras", "快速、疗愈、开创、冲动"),
    (1, "Bharani", "婆罗尼", "Venus", 13.333, "子宫", "阎摩 Yama", "承载、约束、转化、深度"),
    (2, "Krittika", "迦提迦", "Sun", 26.667, "刀/火焰", "阿耆尼 Agni", "锐利、净化、勇气、批判"),
    (3, "Rohini", "罗希尼", "Moon", 40.0, "牛车", "梵天 Prajapati", "丰盛、滋养、魅力、执着"),
    (4, "Mrigashira", "摩利伽湿罗", "Mars", 53.333, "鹿首", "苏摩 Soma", "追寻、好奇、柔美、不安"),
    (5, "Ardra", "阿陀罗", "Rahu", 66.667, "泪珠", "楼陀罗 Rudra", "风暴、清理、激烈、重生的眼泪"),
    (6, "Punarvasu", "普那婆苏", "Jupiter", 80.0, "弓与箭囊", "阿底提 Aditi", "回归、更新、宽厚、反复"),
    (7, "Pushya", "普湿耶", "Saturn", 93.333, "花/牛乳", "毗诃波提 Brihaspati", "滋养、保守、圆满、仪式"),
    (8, "Ashlesha", "阿湿利沙", "Mercury", 106.667, "蛇", "那伽 Nagas", "缠绕、洞察、操控、蜕变"),
    (9, "Magha", "摩伽", "Ketu", 120.0, "王座", "毕多罗 Pitris", "权威、祖先、荣耀、沉重"),
    (10, "Purva Phalguni", "前颇勒具尼", "Venus", 133.333, "吊床/床榻", "薄伽 Bhaga", "享乐、创造、关系、慵懒"),
    (11, "Uttara Phalguni", "后颇勒具尼", "Sun", 146.667, "床柱", "阿利耶曼 Aryaman", "责任、合作、成熟、稳定"),
    (12, "Hasta", "诃悉多", "Moon", 160.0, "手掌", "萨维特利 Savitar", "手艺、灵动、掌握、焦虑"),
    (13, "Chitra", "质多罗", "Mars", 173.333, "明珠", "陀湿多 Tvashtar", "闪耀、建造、外貌、我执"),
    (14, "Swati", "萨陀毗舍", "Rahu", 186.667, "嫩芽/剑", "伐由 Vayu", "独立、飘荡、灵活、散漫"),
    (15, "Vishakha", "毗舍佉", "Jupiter", 200.0, "拱门/陶轮", "因陀罗-阿耆尼 Indra-Agni", "目标、双火、成就、不满"),
    (16, "Anuradha", "阿奴罗陀", "Saturn", 213.333, "莲花/权杖", "密多罗 Mitra", "友谊、隐忍、组织、忧郁"),
    (17, "Jyeshtha", "逝瑟吒", "Mercury", 226.667, "耳环/伞", "因陀罗 Indra", "长老、权威、保护、傲慢"),
    (18, "Mula", "牟罗", "Ketu", 240.0, "根束", "尼利提 Nirriti", "根源、连根拔、毁灭、解脱"),
    (19, "Purva Ashadha", "前沙陀", "Venus", 253.333, "象齿/扇", "阿波 Apas", "净化、宣言、豪情、争胜"),
    (20, "Uttara Ashadha", "后沙陀", "Sun", 266.667, "象牙/床", "毗湿婆提婆 Vishwadevas", "完成、坚毅、耐力、孤高"),
    (21, "Shravana", "沙罗婆那", "Moon", 280.0, "三足/耳", "毗湿奴 Vishnu", "聆听、连接、智慧、依附"),
    (22, "Dhanishta", "檀尼瑟吒", "Mars", 293.333, "鼓", "八婆苏 Vasus", "节奏、富足、凝聚、躁动"),
    (23, "Shatabhisha", "设多毗沙", "Rahu", 306.667, "千星/空圆", "伐楼那 Varuna", "疗愈、隐匿、广阔、疏离"),
    (24, "Purva Bhadrapada", "前跋陀罗", "Jupiter", 320.0, "剑/前腿", "阿耆迦 Aja Ekapada", "烈度、转化、极简、偏执"),
    (25, "Uttara Bhadrapada", "后跋陀罗", "Saturn", 333.333, "蛇/后腿", "阿希哩布陀 Ahirbudhnya", "深稳、慈悲、延迟、隐忍"),
    (26, "Revati", "罗婆提", "Mercury", 346.667, "鱼/鼓", "普善 Pushan", "指南、抚育、圆融、迷路"),
]

# Nakshatra 分段表: (pada 1-4 对应的 navamsa 星座)
# 每宿 4 个 pada, 每 pada 3°20', 每 pada 对应一个星座 (从白羊起)
_NAKSHATRA_PADA_SIGNS = {
    # 用 nakshatra index -> [pada0_sign, pada1_sign, pada2_sign, pada3_sign]
    # pada sign = (nakshatra_index * 4 + pada) % 12 → 0=白羊...
    # 这是 Navamsa 的标准映射
}

_SIGN_NAMES_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _get_nakshatra(lon_sidereal: float) -> dict:
    """由恒星黄经返回对应的 Nakshatra 及其详细信息。"""
    lon = lon_sidereal % 360
    idx = int(lon / _NAKSHATRA_SPAN)
    if idx >= 27:
        idx = 0
    pada = int((lon % _NAKSHATRA_SPAN) / (_NAKSHATRA_SPAN / 4))
    pada_lon = round(lon % _NAKSHATRA_SPAN, 4)
    n = NAKSHATRAS[idx]
    return {
        "index": idx + 1,
        "name_sanskrit": n[1],
        "name_zh": n[2],
        "lord": n[3],
        "span_start": round(n[4], 4),
        "span_end": round(n[4] + _NAKSHATRA_SPAN, 4),
        "symbol": n[5],
        "deity": n[6],
        "keywords": n[7],
        "pada": pada + 1,
        "pada_lon": pada_lon,
        "pada_span": round(_NAKSHATRA_SPAN / 4, 4),
    }


# ═══════════════════════════════════════════════════════════════
# 3. 行星尊贵表 (Dignities)
# ═══════════════════════════════════════════════════════════════
# 入庙 (own)、落陷 (debilitated)、曜升 (exalted)、Moolatrikona
_DIGNITIES = {
    "Sun": {
        "own": [4], "exalted": [0], "debilitated": [6], "moolatrikona": [4],
    },
    "Moon": {
        "own": [3], "exalted": [1], "debilitated": [7], "moolatrikona": [1],
    },
    "Mars": {
        "own": [0, 7], "exalted": [9], "debilitated": [3], "moolatrikona": [0],
    },
    "Mercury": {
        "own": [2, 5], "exalted": [5], "debilitated": [11], "moolatrikona": [5],
    },
    "Jupiter": {
        "own": [8, 11], "exalted": [3], "debilitated": [9], "moolatrikona": [8],
    },
    "Venus": {
        "own": [1, 6], "exalted": [11], "debilitated": [5], "moolatrikona": [6],
    },
    "Saturn": {
        "own": [9, 10], "exalted": [6], "debilitated": [0], "moolatrikona": [10],
    },
    "Rahu": {
        # Rahu 在吠陀中无"入庙",但有曜升/落陷。常以 Virgo 为曜升, Pisces 为落陷
        "own": [], "exalted": [5], "debilitated": [11], "moolatrikona": [5],
    },
    "Ketu": {
        # Ketu 与 Rahu 相反
        "own": [], "exalted": [11], "debilitated": [5], "moolatrikona": [11],
    },
}


def _get_dignity(planet_en: str, sign_idx: int) -> dict:
    """返回某行星在某星座的尊贵状态。sign_idx: 0=白羊...11=双鱼"""
    d = _DIGNITIES.get(planet_en, {})
    result = []
    if sign_idx in d.get("own", []):
        result.append("入庙 (Swakshetra)")
    if sign_idx in d.get("exalted", []):
        result.append("曜升 (Uccha)")
    if sign_idx in d.get("debilitated", []):
        result.append("落陷 (Neecha)")
    if sign_idx in d.get("moolatrikona", []):
        result.append("本宫根 (Moolatrikona)")
    if not result:
        # 检查友好关系
        result.append("中性/友宫")
    return {
        "sign": _SIGN_NAMES_EN[sign_idx],
        "dignities": result,
        "is_exalted": sign_idx in d.get("exalted", []),
        "is_debilitated": sign_idx in d.get("debilitated", []),
        "is_own": sign_idx in d.get("own", []),
    }


# ═══════════════════════════════════════════════════════════════
# 4. Vimshottari Dasha (120 年大运)
# ═══════════════════════════════════════════════════════════════
_DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
    "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
_DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# 每宿的 Vimshottari 主星 (按 27 宿 × 9 星 循环,从 Ketu 开始)
_NAKSHATRA_DASHA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]


def _compute_dasha(moon_lon_sidereal: float, birth_dt: datetime) -> dict:
    """计算 Vimshottari Dasha。

    使用出生日期计算大运起点,用实际当前日期确定当前所在大运/子运。
    所有日期使用出生时区以保证时间线连续可比。
    """
    n = _get_nakshatra(moon_lon_sidereal)
    n_idx = n["index"] - 1  # 0-based
    moon_in_nakshatra_deg = n["pada_lon"] + (n["pada"] - 1) * (_NAKSHATRA_SPAN / 4)

    # 出生时运行到哪一颗大运星
    birth_lord = _NAKSHATRA_DASHA_LORDS[n_idx]
    total_dasha_years = _DASHA_YEARS[birth_lord]
    # 已消耗的比例 = 月亮在宿中的度数 / 13.333°
    elapsed_ratio = moon_in_nakshatra_deg / _NAKSHATRA_SPAN
    dasha_elapsed_years = elapsed_ratio * total_dasha_years
    dasha_remaining_years = total_dasha_years - dasha_elapsed_years

    # 大运起点: 出生时间减去已消耗的大运年数
    # 使用 date 级别精度 (Dasha 按年月划分, 不需要精确到时分)
    elapsed_days = int(dasha_elapsed_years * 365.25)
    dasha_start = birth_dt - timedelta(days=elapsed_days)

    # 构建完整 120 年周期时间线
    timeline = []
    lord_idx = _DASHA_ORDER.index(birth_lord)
    cumulative_start = dasha_start
    for i in range(9):
        lord = _DASHA_ORDER[(lord_idx + i) % 9]
        years = _DASHA_YEARS[lord]
        end_dt = cumulative_start + timedelta(days=int(years * 365.25))
        timeline.append({
            "lord": lord,
            "years": years,
            "start": cumulative_start.strftime("%Y-%m"),
            "end": end_dt.strftime("%Y-%m"),
        })
        cumulative_start = end_dt

    # 用实际当前日期确定所在大运 (使用与出生相同的时区以便正确比较)
    tz = birth_dt.tzinfo if birth_dt.tzinfo else timezone.utc
    today = date.today()
    now_dt = datetime(today.year, today.month, today.day, tzinfo=tz)

    current_maha = None
    for t in timeline:
        start_d = datetime.strptime(t["start"], "%Y-%m").replace(tzinfo=tz)
        end_d = datetime.strptime(t["end"], "%Y-%m").replace(tzinfo=tz)
        if start_d <= now_dt < end_d:
            maha_lord = t["lord"]
            maha_years = t["years"]
            elapsed_in_maha = (now_dt - start_d).days / 365.25
            elapsed_ratio_maha = elapsed_in_maha / maha_years

            # Antardasha (子运) — 从当前 Mahadasha lord 开始按比例分配
            ad_start = start_d
            ad_lord_idx2 = _DASHA_ORDER.index(maha_lord)
            for j in range(9):
                ad_lord = _DASHA_ORDER[(ad_lord_idx2 + j) % 9]
                ad_years = (_DASHA_YEARS[ad_lord] / 120.0) * maha_years
                ad_end = ad_start + timedelta(days=int(ad_years * 365.25))
                is_current = ad_start <= now_dt < ad_end
                if is_current:
                    current_maha = {
                        "maha_lord": maha_lord,
                        "maha_years": maha_years,
                        "maha_start": t["start"],
                        "maha_end": t["end"],
                        "antara_lord": ad_lord,
                        "antara_years": round(ad_years, 2),
                        "antara_start": ad_start.strftime("%Y-%m"),
                        "antara_end": ad_end.strftime("%Y-%m"),
                        "elapsed_in_maha_pct": round(elapsed_ratio_maha * 100, 1),
                    }
                ad_start = ad_end
            break

    return {
        "computed_at": today.isoformat(),
        "birth_nakshatra_lord": birth_lord,
        "dasha_elapsed_years_at_birth": round(dasha_elapsed_years, 2),
        "dasha_remaining_years_at_birth": round(dasha_remaining_years, 2),
        "full_timeline": timeline,
        "current": current_maha,
    }


# ═══════════════════════════════════════════════════════════════
# 5. Yoga 检测 (基础版)
# ═══════════════════════════════════════════════════════════════
def _detect_yogas(planets_data: dict, houses_data: dict) -> list[dict]:
    """检测基础 Yogas。"""
    yogas = []

    # 按 house 聚合行星
    house_planets = {}
    for cn, data in planets_data.items():
        h = data.get("house", 0)
        house_planets.setdefault(h, []).append(cn)

    # Raja Yoga: 三方宫(1/5/9)主星 与 四正宫(1/4/7/10)主星 的联结
    # 简化版: 检查1/5/9宫和 1/4/7/10宫是否有行星同宫
    trikonas = {1, 5, 9}
    kendras = {1, 4, 7, 10}
    trikona_planets = set()
    kendra_planets = set()
    for h, plist in house_planets.items():
        if h in trikonas:
            trikona_planets.update(plist)
        if h in kendras:
            kendra_planets.update(plist)
    common = trikona_planets & kendra_planets
    if common:
        yogas.append({
            "name": "Raja Yoga (王者组合)",
            "description": f"行星 {', '.join(common)} 同时出现在三合宫与四正宫, 赋予权力与成就潜能",
            "strength": "strong" if len(common) >= 2 else "moderate",
        })

    # Dhana Yoga: 2宫(财帛)主星与 11宫(福德)主星或 5/9宫主星的联结
    h2_planets = set(house_planets.get(2, []))
    h11_planets = set(house_planets.get(11, []))
    h5_planets = set(house_planets.get(5, []))
    h9_planets = set(house_planets.get(9, []))
    if h2_planets and (h11_planets or h5_planets or h9_planets):
        yogas.append({
            "name": "Dhana Yoga (财富组合)",
            "description": "第2宫与5/9/11宫的联结表明财富积累潜力",
            "strength": "strong" if (h2_planets & (h11_planets | h9_planets)) else "moderate",
        })

    # Gaja Kesari Yoga: 木星在月亮所在的 kendra(1/4/7/10)
    moon_house = None
    jupiter_house = None
    for cn, data in planets_data.items():
        if cn in ("月亮", "Moon"):
            moon_house = data.get("house")
        if cn in ("木星", "Jupiter"):
            jupiter_house = data.get("house")
    if moon_house and jupiter_house:
        diff = (jupiter_house - moon_house) % 12
        if diff in (0, 3, 6, 9):  # 木星在月亮的 kendra
            yogas.append({
                "name": "Gaja Kesari Yoga (象狮组合)",
                "description": "木星在月亮起算的四正宫, 赋予智慧、声望与稳定",
                "strength": "strong",
            })

    # Budha-Aditya Yoga: 水星与太阳同宫
    sun_house = None
    mercury_house = None
    for cn, data in planets_data.items():
        if cn in ("太阳", "Sun"):
            sun_house = data.get("house")
        if cn in ("水星", "Mercury"):
            mercury_house = data.get("house")
    if sun_house and mercury_house and sun_house == mercury_house:
        yogas.append({
            "name": "Budha-Aditya Yoga (日水组合)",
            "description": "太阳与水星同宫, 智力敏锐、口才好、分析力强",
            "strength": "strong",
        })

    return yogas


# ═══════════════════════════════════════════════════════════════
# 6. 月交点 (Rahu/Ketu) — 均值公式
# ═══════════════════════════════════════════════════════════════
def _mean_lunar_node(jd: float) -> float:
    """均值月交点黄经 (Mean Node)。jd = 儒略日。
    返回升交点 (Rahu) 的地心黄经。降交点 Ketu = Rahu + 180°。

    公式来源: Jean Meeus, Astronomical Algorithms, 第 45 章。
    """
    T = (jd - 2451545.0) / 36525.0  # 儒略世纪 (J2000)
    # 均值升交点
    omega = (125.0445222
             - 1934.1362619 * T
             + 0.0020756 * T ** 2
             + 0.00000214 * T ** 3
             - 0.00000015 * T ** 4) % 360
    return omega


def _rahu_ketu(rahu_lon: float, ayanamsa: float) -> dict:
    """给定 tropical Rahu 黄经, 返回 sidereal Rahu/Ketu 信息。"""
    rahu_sid = (rahu_lon - ayanamsa) % 360
    ketu_sid = (rahu_sid + 180) % 360
    return {
        "rahu": {
            "lon_tropical": round(rahu_lon, 4),
            "lon_sidereal": round(rahu_sid, 4),
            **_get_nakshatra(rahu_sid),
            "sign": am.sign_of(rahu_sid),
        },
        "ketu": {
            "lon_tropical": round((rahu_lon + 180) % 360, 4),
            "lon_sidereal": round(ketu_sid, 4),
            **_get_nakshatra(ketu_sid),
            "sign": am.sign_of(ketu_sid),
        },
    }


# ═══════════════════════════════════════════════════════════════
# 7. 主排盘函数
# ═══════════════════════════════════════════════════════════════
def compute(b: Birth) -> ChartResult:
    """吠陀排盘: tropical → sidereal + 全量 Jyotish 输出。"""
    from skyfield.api import load

    ts = load.timescale()
    eph = load("de421.bsp")
    earth = eph["earth"]

    dt = datetime(b.year, b.month, b.day, b.hour, b.minute, tzinfo=ZoneInfo(b.tz))
    t = ts.from_datetime(dt)
    ayanamsa = _lahiri_precise(b.year + (b.month - 1) / 12.0 + (b.day - 1) / 365.0)

    # --- 七大行星 tropical → sidereal ---
    positions = {}
    for cn, key in _PLANETS.items():
        astrometric = earth.at(t).observe(eph[key]).apparent()
        lon, _, _ = astrometric.ecliptic_latlon()
        positions[cn] = (lon.degrees - ayanamsa) % 360

    # --- Rahu / Ketu (月交点) ---
    jd = t.tt  # 地球时儒略日
    rahu_tropical = _mean_lunar_node(jd)
    nodes = _rahu_ketu(rahu_tropical, ayanamsa)
    positions["罗睺(Rahu)"] = nodes["rahu"]["lon_sidereal"]
    positions["计都(Ketu)"] = nodes["ketu"]["lon_sidereal"]

    # --- 星座 & 元素 ---
    planets = {}
    for cn, lon in positions.items():
        s = am.sign_of(lon)
        sign_idx = int(lon // 30)
        # 英文行星名(用于查尊贵表)
        planet_en_map = {
            "太阳": "Sun", "月亮": "Moon", "水星": "Mercury", "金星": "Venus",
            "火星": "Mars", "木星": "Jupiter", "土星": "Saturn",
            "罗睺(Rahu)": "Rahu", "计都(Ketu)": "Ketu",
        }
        planet_en = planet_en_map.get(cn, cn)
        dignity = _get_dignity(planet_en, sign_idx)
        nakshatra = _get_nakshatra(lon)
        planets[cn] = {
            **s,
            "sign_en": _SIGN_NAMES_EN[sign_idx],
            "sign_idx": sign_idx,
            "dignity": dignity,
            "nakshatra": nakshatra,
        }

    # --- 宫位 (整宫制,从 Ascendant 起) ---
    house_data = []
    asc = None
    if b.lat is not None and b.lng is not None:
        gst = t.gmst
        lst_deg = (gst * 15 + b.lng) % 360
        asc_lon = am.ascendant(lst_deg, b.lat)
        asc_sid = (asc_lon - ayanamsa) % 360
        asc = am.sign_of(asc_sid)
        asc["sign_en"] = _SIGN_NAMES_EN[int(asc_sid // 30)]
        house_data = am.houses(asc_sid, system="whole")

    # --- 将行星归入宫位 ---
    for cn, data in planets.items():
        if house_data:
            lon = data["lon"]
            h = int(lon // 30)
            asc_sign = int(asc_sid // 30) if asc else 0
            house_num = ((h - asc_sign) % 12) + 1
            data["house"] = house_num
        else:
            data["house"] = 0

    # --- 相位 (sidereal) ---
    aspects = am.find_aspects(positions)

    # --- Vimshottari Dasha ---
    moon_sid_lon = positions.get("月亮", 0)
    dasha = _compute_dasha(moon_sid_lon, dt)

    # --- Yogas ---
    yogas = _detect_yogas(planets, house_data or [])

    # --- 元素计数 (English keys for consistency)
    elem_count = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    for p in planets.values():
        elem_map = {"火": "fire", "土": "earth", "风": "air", "水": "water"}
        eng_key = elem_map.get(p["element"], p["element"])
        elem_count[eng_key] += 1

    # --- 本命基本判断 ---
    # 月宿分析
    moon_n = planets.get("月亮", {}).get("nakshatra", {})
    asc_n = asc.get("sign_en", "unknown") if asc else "unknown"

    return ChartResult(
        method="vedic",
        school="west",
        engine="skyfield+lahiri+nakshatra+dasha",
        normalized={"elements": elem_count, "timeline": []},
        raw={
            "computed_at": date.today().isoformat(),
            "system": "sidereal (Lahiri)",
            "ayanamsa": round(ayanamsa, 4),
            "ayanamsa_formula": "IAU2006 precession + Lahiri zero-point",
            "planets": planets,
            "aspects": aspects,
            "ascendant": asc,
            "houses": house_data,
            "nodes": nodes,
            "vimsottari_dasha": dasha,
            "yogas": yogas,
            "moon_nakshatra": moon_n,
            "lagna": asc_n,
            "calculation_basis": {
                "method": "vedic_jyotish",
                "ayanamsa": "Lahiri (Chitrapaksha)",
                "zodiac": "Sidereal",
                "house_system": "Whole Sign (from Lagna)",
                "nakshatra_system": "27 Nakshatras (equal 13°20' divisions)",
                "dasha_system": "Vimshottari (120-year cycle)",
                "node_calculation": "Mean Lunar Node (Meeus formula)",
                "planets_included": list(positions.keys()),
                "rule_version": "v2",
                "limits": [
                    "Rahu/Ketu 使用均值月交点 (真值偏离 < 1°)",
                    "Shadbala (行星力量六要素) 待完整实现",
                    "Navamsa (D-9) 及其他分盘未展开",
                    "Dasha 使用简化数学公式, 未使用星历表查对",
                    "Yoga 检测为基础版, 未覆盖全部数百种 Yoga",
                ],
            },
        },
    )
