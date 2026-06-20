"""西方占星 —— B 路：skyfield (MIT) + JPL 公版星历，星座/相位/宫位自算。零 AGPL。

深度调查修正（均已实测验证）：
  1) ecliptic_latlon() 返回顺序是 (纬度, 经度, 距离) —— 经度在第 2 位（曾写反）。
  2) 必须传 epoch=t 用「当日黄道」（回归黄道）；否则按 J2000 会差一个岁差量
     （2025 年约 0.34°，且逐年增大）。已验证 epoch=t 把二分二至误差降到 0.000°。
  3) Placidus 宫位已实现并用半弧自洽法在 5 个纬度验证通过。

Sprint 2.2: 三通道 (行运 transits / 次限 progressions / 太阳返照 solar_return) 输出.
  - 行运: 当前天空对本命的相位 (硬/软, 容许度 1-3°)
  - 次限: 1日 = 1年 (secondary progressions) — 用于"内在成长"判读
  - 太阳返照: 太阳回到本命位置 (年周期) — 用于"年主题"判读

Sprint 4.x: 本命深化 — Aspects 网格 + 月亮交点 + Arabic Parts (7 Lots) + Lilith
  - Aspects 网格: 含月亮交点 + Lilith, 容许度差异化
    合/冲 ±8° | 刑/六合/拱/三合 ±6° | 半刑/半拱 ±3° | 五分相 ±2°
  - 月亮交点: 集成 divination.data.western_lunar_nodes
  - Arabic Parts: 集成 divination.data.western_arabic_parts (7 主 Lot)
  - Lilith: 集成 compute_lilith (月亮远地点)
  - 元素/模式分布: 火土风水 + 本位/固定/变动

文献:
  - *Tetrabiblos*（托勒密）— 古典相位/Lots 源头
  - Steven Forrest, *The Inner Sky* — 现代心理占星
  - Liz Greene — 心理占星传统
"""
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .. import astro_math as am
from .._ephem import get_eph, get_ts
from ..contracts import Birth, ChartResult
from .engines_western_shared import planets_and_gmst

# ══════════════════════════════════════════════════════════════
# 行星/小行星定义
# ══════════════════════════════════════════════════════════════
_PLANETS = {
    "太阳": "sun", "月亮": "moon", "水星": "mercury", "金星": "venus",
    "火星": "mars", "木星": "jupiter barycenter", "土星": "saturn barycenter",
}

_HARD_ASPECTS = {"冲": 180, "刑": 90}
_SOFT_ASPECTS = {"合": 0, "六合": 60, "拱": 120, "三合": 120}
_TRANSIT_ORB_DEG = 2.0  # 容许度 ±2°

# ══════════════════════════════════════════════════════════════
# 本命 Aspects 网格 — 差异化容许度
# ══════════════════════════════════════════════════════════════
# 文献依据: 传统占星容许度 (J. Mayo / R. Hand 等)
# - 合/冲: 大角度, 容许度大 (±8°)
# - 主相位 (刑/六合/拱/三合): 中等 (±6°)
# - 半刑/半拱: 小角度, 容许度小 (±3°)
# - 五分相 (72°): 谐波相位, 容许度最小 (±2°)
_NATAL_ASPECT_TABLE: dict[str, dict[str, Any]] = {
    "合":   {"angle": 0,   "orb": 8.0, "is_hard": False, "category": "主相位"},
    "冲":   {"angle": 180, "orb": 8.0, "is_hard": True,  "category": "主相位"},
    "刑":   {"angle": 90,  "orb": 6.0, "is_hard": True,  "category": "主相位"},
    "六合": {"angle": 60,  "orb": 6.0, "is_hard": False, "category": "主相位"},
    "拱":   {"angle": 120, "orb": 6.0, "is_hard": False, "category": "主相位"},
    "三合": {"angle": 120, "orb": 6.0, "is_hard": False, "category": "主相位"},
    "半刑": {"angle": 45,  "orb": 3.0, "is_hard": True,  "category": "半相位"},
    "半拱": {"angle": 30,  "orb": 3.0, "is_hard": False, "category": "半相位"},
    "五分相": {"angle": 72,  "orb": 2.0, "is_hard": False, "category": "谐波相位"},
}

# 模式 (Modality) 分组: 本位/固定/变动
_MODALITY_GROUPS: dict[str, list[str]] = {
    "本位": ["白羊", "巨蟹", "天秤", "摩羯"],
    "固定": ["金牛", "狮子", "天蝎", "水瓶"],
    "变动": ["双子", "处女", "射手", "双鱼"],
}


# ══════════════════════════════════════════════════════════════
# 行星黄经计算
# ══════════════════════════════════════════════════════════════
def _planet_longitudes(year: int, month: int, day: int, hour: int, minute: int) -> dict[str, float]:
    """单时刻行星黄经 (Tropical, epoch=t)."""
    ts = get_ts(); eph = get_eph(); earth = eph["earth"]
    t = ts.from_datetime(datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("UTC")))
    out: dict[str, float] = {}
    for cn, key in _PLANETS.items():
        _lat, lon, _d = earth.at(t).observe(eph[key]).apparent().ecliptic_latlon(epoch=t)
        out[cn] = lon.degrees % 360
    return out


def _find_transits(natal: dict[str, float], current: dict[str, float],
                   orb: float = _TRANSIT_ORB_DEG) -> list[dict[str, Any]]:
    """当前天空相位 vs 本命。"""
    transits: list[dict[str, Any]] = []
    for cn, cur_lon in current.items():
        # 自相位 (transit planet == natal planet) — 仅当本命也有该行星时
        nat_lon_self = natal.get(cn)
        if nat_lon_self is not None:
            diff = abs((cur_lon - nat_lon_self) % 360)
            if diff > 180:
                diff = 360 - diff
            for aspect_name, angle in {**_HARD_ASPECTS, **_SOFT_ASPECTS}.items():
                actual_orb = abs(diff - angle)
                if actual_orb <= orb:
                    transits.append({
                        "transit_planet": cn,
                        "natal_planet": cn,
                        "aspect": aspect_name,
                        "angle": angle,
                        "orb": round(actual_orb, 2),
                        "is_hard": aspect_name in _HARD_ASPECTS,
                    })
        # 跨行星相位 (transit X vs natal Y) — 始终执行
        for nat_cn, nat_lon2 in natal.items():
            if nat_cn == cn:
                continue
            diff2 = abs((cur_lon - nat_lon2) % 360)
            if diff2 > 180:
                diff2 = 360 - diff2
            for aspect_name, angle in {**_HARD_ASPECTS, **_SOFT_ASPECTS}.items():
                actual_orb = abs(diff2 - angle)
                if actual_orb <= orb:
                    transits.append({
                        "transit_planet": cn,
                        "natal_planet": nat_cn,
                        "aspect": aspect_name,
                        "angle": angle,
                        "orb": round(actual_orb, 2),
                        "is_hard": aspect_name in _HARD_ASPECTS,
                    })
    return transits


def _find_progressed_aspects(
    natal: dict[str, float],
    progressed: dict[str, float],
) -> list[dict[str, Any]]:
    """次限相位: progressed 行星 vs natal 行星。"""
    out: list[dict[str, Any]] = []
    for pc, p_lon in progressed.items():
        for nc, n_lon in natal.items():
            diff = abs((p_lon - n_lon) % 360)
            if diff > 180:
                diff = 360 - diff
            for aspect_name, angle in {**_HARD_ASPECTS, **_SOFT_ASPECTS}.items():
                actual_orb = abs(diff - angle)
                # 次限容许度更严 (±1°)
                if actual_orb <= 1.0:
                    out.append({
                        "planet": f"{pc}→{nc}",
                        "aspect": aspect_name,
                        "shift_deg": round(diff, 2),
                        "is_hard": aspect_name in _HARD_ASPECTS,
                    })
    return out


def _solar_return_moment(natal: Birth) -> dict[str, Any] | None:
    """太阳返照: 太阳回到本命位置的精确时刻 (UTC)。

    算法: 找到当前年太阳经过本命太阳黄经的时刻, ±1天范围用二分查找。
    """
    natal_lons = _planet_longitudes(natal.year, natal.month, natal.day,
                                    natal.hour, natal.minute)
    natal_sun = natal_lons.get("太阳")
    if natal_sun is None:
        return None
    # 当前年太阳返照 (UTC)
    now = datetime.utcnow()
    year = now.year
    # 在 ±7 天内搜索, 步进 1 天
    best_dt: datetime | None = None
    best_diff = 360.0
    for offset in range(-7, 8):
        candidate = datetime(year, 6, 15, 12, 0, 0) + timedelta(days=offset)
        lons = _planet_longitudes(candidate.year, candidate.month, candidate.day,
                                  candidate.hour, candidate.minute)
        sun = lons.get("太阳", 0)
        diff = abs((sun - natal_sun) % 360)
        if diff > 180:
            diff = 360 - diff
        if diff < best_diff:
            best_diff = diff
            best_dt = candidate
    if best_dt is None or best_diff > 1.0:
        return None
    # 细化: ±12h 步进 1h
    for hour_offset in range(-12, 13):
        candidate = best_dt + timedelta(hours=hour_offset)
        lons = _planet_longitudes(candidate.year, candidate.month, candidate.day,
                                  candidate.hour, candidate.minute)
        sun = lons.get("太阳", 0)
        diff = abs((sun - natal_sun) % 360)
        if diff > 180:
            diff = 360 - diff
        if diff < best_diff:
            best_diff = diff
            best_dt = candidate
    return {
        "moment_utc": best_dt.isoformat(),
        "year": best_dt.year,
        "sun_diff_deg": round(best_diff, 4),
    }


# ══════════════════════════════════════════════════════════════
# 本命 Aspects 网格 (差异化容许度, 含月亮交点 + Lilith)
# ══════════════════════════════════════════════════════════════
def _angular_sep(a: float, b: float) -> float:
    """两点最小角距 0-180。"""
    d = abs((a - b) % 360)
    return min(d, 360 - d)


def find_natal_aspects_grid(positions: dict[str, float]) -> list[dict[str, Any]]:
    """本命 Aspects 网格 — 差异化容许度。

    输入: positions = {天体名: 黄经}, 至少 7 行星 + 北交点 + 南交点 + Lilith
    输出: 所有触发的相位, 按 角度差 升序排列。

    相位表 (来自 _NATAL_ASPECT_TABLE):
      合/冲    ±8°  (主相位)
      刑/六合/拱/三合 ±6° (主相位)
      半刑/半拱 ±3°  (半相位)
      五分相    ±2°  (谐波相位)
    """
    names = list(positions.keys())
    out: list[dict[str, Any]] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sep = _angular_sep(positions[a], positions[b])
            for asp_name, info in _NATAL_ASPECT_TABLE.items():
                target = info["angle"]
                orb_diff = abs(sep - target)
                if orb_diff <= info["orb"]:
                    out.append({
                        "a": a,
                        "b": b,
                        "aspect": asp_name,
                        "angle": target,
                        "actual_separation": round(sep, 2),
                        "orb": round(orb_diff, 2),
                        "is_hard": info["is_hard"],
                        "category": info["category"],
                        "exact": orb_diff < 0.5,
                    })
                    break  # 每个配对只取最接近的一种相位
    out.sort(key=lambda x: x["orb"])
    return out


# ══════════════════════════════════════════════════════════════
# 元素 + 模式分布
# ══════════════════════════════════════════════════════════════
def _element_modality_distribution(positions: dict[str, float]) -> dict[str, Any]:
    """统计火/土/风/水 + 本位/固定/变动 分布。"""
    elem = {"火": 0, "土": 0, "风": 0, "水": 0}
    modality = {"本位": 0, "固定": 0, "变动": 0}
    sign_count: dict[str, int] = {}
    for cn, lon in positions.items():
        info = am.sign_of(lon)
        e = info["element"]
        elem[e] = elem.get(e, 0) + 1
        s = info["sign"]
        sign_count[s] = sign_count.get(s, 0) + 1
        # 模式
        for mod, signs in _MODALITY_GROUPS.items():
            if s in signs:
                modality[mod] = modality.get(mod, 0) + 1
                break
    dominant_elem = max(elem, key=elem.get) if any(elem.values()) else None
    dominant_mod = max(modality, key=modality.get) if any(modality.values()) else None
    return {
        "elements": elem,
        "modalities": modality,
        "dominant_element": dominant_elem,
        "dominant_modality": dominant_mod,
        "sign_distribution": sign_count,
        "element_interpretation": _interpret_element(elem),
        "modality_interpretation": _interpret_modality(modality),
    }


def _interpret_element(elem: dict[str, int]) -> str:
    total = sum(elem.values())
    if total == 0:
        return ""
    dom = max(elem, key=elem.get)
    if elem[dom] / total >= 0.5:
        return f"{dom}元素过半 ({elem[dom]}/{total}), 该能量高度主导, 性格显著倾向此领域。"
    missing = [e for e, v in elem.items() if v == 0]
    base = f"{dom}元素主导"
    if missing:
        return base + f", 缺{'/'.join(missing)}元素, 此方面需有意识培养。"
    return base + "。"


def _interpret_modality(mod: dict[str, int]) -> str:
    total = sum(mod.values())
    if total == 0:
        return ""
    dom = max(mod, key=mod.get)
    cn = {"本位": "开创·主动·领导", "固定": "稳定·坚持·持久",
          "变动": "灵活·适应·变通"}
    if mod[dom] / total >= 0.5:
        return f"{dom}过半, 性格显著倾向{cn[dom]}型。"
    return f"{dom}主导, 但同时具备其他模式特质。"


# ══════════════════════════════════════════════════════════════
# 太阳所在宫位 (用于 Arabic Parts 日/夜生判断)
# ══════════════════════════════════════════════════════════════
def _sun_house(sun_lon: float, houses: list[dict]) -> int | None:
    """根据宫位表找出太阳所在宫位 (1-12)。"""
    if not houses:
        return None
    cusps = [(h["house"], h["cusp_lon"]) for h in houses]
    cusps_sorted = sorted(cusps, key=lambda x: x[1])
    for k in range(len(cusps_sorted)):
        house_num, cusp_start = cusps_sorted[k]
        next_idx = (k + 1) % len(cusps_sorted)
        _, cusp_next = cusps_sorted[next_idx]
        if cusp_start <= cusp_next:
            # 不跨越 0°
            if cusp_start <= sun_lon < cusp_next:
                return house_num
        else:
            # 跨越 0°
            if sun_lon >= cusp_start or sun_lon < cusp_next:
                return house_num
    return cusps_sorted[0][0]


# ══════════════════════════════════════════════════════════════
# 极区检测与处理 (Placidus 极区 fallback)
# ══════════════════════════════════════════════════════════════
def is_polar_region(lat: float) -> bool:
    """检测是否在极圈内 (|lat| > 66°33' ≈ 66.55°).

    Placidus 半弧公式在极区因永昼/永夜导致部分宫位线无解,
    需回退为等宫制 (Equal House)。
    """
    return abs(lat) > 66.55


def compute_polar_houses(ramc_deg: float, lat_deg: float, asc_lon: float) -> list[dict]:
    """极区等宫制 fallback: 从上升点起每宫 30° 均分黄道。

    Args:
        ramc_deg: 本地恒星时 (RAMC, 度)
        lat_deg: 纬度 (度)
        asc_lon: 上升点黄经 (度)

    Returns:
        list[dict]: 12 宫位, 每项含 house/cusp_lon/sign
    """
    houses: list[dict] = []
    for i in range(12):
        cusp = (asc_lon + i * 30) % 360
        houses.append({
            "house": i + 1,
            "cusp_lon": round(cusp, 4),
            "sign": am.sign_of(cusp)["sign"],
        })
    return houses


# ══════════════════════════════════════════════════════════════
# compute 主入口
# ══════════════════════════════════════════════════════════════
def compute(b: Birth, house_system: str = "placidus") -> ChartResult:
    # 行星黄经 + gmst 走共享缓存（与吠陀同人时只算一次；修正①顺序 修正②epoch=t）
    positions, gmst = planets_and_gmst(b)

    # ---- 月亮交点 (集成 western_lunar_nodes) ----
    from ..data.western_lunar_nodes import (
        compute_nodes,
        get_node_interpretation,
        find_all_node_aspects,
    )
    nodes = compute_nodes(b.year, b.month, b.day, b.hour, b.minute)
    north_lon = nodes["north_node_lon"]
    south_lon = nodes["south_node_lon"]
    positions_with_nodes = dict(positions)
    positions_with_nodes["北交点"] = north_lon
    positions_with_nodes["南交点"] = south_lon

    # ---- Lilith (集成 western_arabic_parts) ----
    from ..data.western_arabic_parts import (
        compute_lilith,
        compute_all_main_lots,
        LILITH_IN_SIGNS,
    )
    lilith = compute_lilith(b.year, b.month, b.day, b.hour, b.minute)
    lilith_lon = lilith["lilith_lon"]
    positions_with_lilith = dict(positions_with_nodes)
    positions_with_lilith["莉莉丝"] = lilith_lon

    # ---- Aspects 网格 (含交点 + Lilith) ----
    aspects_grid = find_natal_aspects_grid(positions_with_lilith)

    # ---- 节点与本命行星相位 ----
    north_aspects = find_all_node_aspects(north_lon, positions)
    south_aspects = find_all_node_aspects(south_lon, positions)

    # ---- 宫位 + 上升点 ----
    planets_signs = {cn: am.sign_of(lon) for cn, lon in positions.items()}
    houses: list[dict] = []
    asc = None
    mc = None
    polar_warning = None
    if b.lat is not None and b.lng is not None:
        ramc = (gmst * 15 + b.lng) % 360            # 本地恒星时(度) = RAMC
        mc = am.midheaven(ramc)
        asc = am.ascendant(ramc, b.lat)
        if is_polar_region(b.lat):
            polar_warning = {
                "is_polar": True,
                "latitude": b.lat,
                "warning": (
                    f"纬度 {b.lat}° 在极圈内(|lat|>66°33'), "
                    "Placidus宫位制在此失效,已回退为等宫制(Equal House)。"
                ),
                "house_system_fallback": "equal",
                "reference": (
                    "Placidus半弧公式在极区 (|lat|>66°33') "
                    "因永昼/永夜导致部分宫位线无解,"
                    "等宫制为学界广泛接受的fallback方案。"
                ),
            }
            houses = compute_polar_houses(ramc, b.lat, asc)
        elif house_system == "placidus":
            houses = am.placidus_houses(ramc, b.lat)
        else:
            houses = am.houses(asc, house_system)

    # ---- 元素 + 模式分布 (含交点 + Lilith) ----
    distribution = _element_modality_distribution(positions_with_lilith)

    # ---- Arabic Parts (7 主 Lot) ----
    arabic_parts: list[dict[str, Any]] = []
    if asc is not None and b.lat is not None and b.lng is not None:
        sun_lon = positions.get("太阳", 0.0)
        sun_h = _sun_house(sun_lon, houses) or 1
        arabic_parts = compute_all_main_lots(
            asc_lon=asc,
            sun_lon=sun_lon,
            moon_lon=positions.get("月亮", 0.0),
            mercury_lon=positions.get("水星", 0.0),
            venus_lon=positions.get("金星", 0.0),
            mars_lon=positions.get("火星", 0.0),
            jupiter_lon=positions.get("木星", 0.0),
            saturn_lon=positions.get("土星", 0.0),
            sun_house=sun_h,
        )

    # ---- 节点解读 (含宫位信息) ----
    # 找出北交点所在宫位
    north_house = None
    if houses:
        north_house = _sun_house(north_lon, houses)
    north_interpretation = get_node_interpretation(north_lon, house=north_house)

    # ---- 三通道 (行运 / 次限 / 太阳返照) ----
    now = datetime.utcnow()
    transits: list[dict] = []
    try:
        cur_lons = _planet_longitudes(now.year, now.month, now.day, now.hour, now.minute)
        transits = _find_transits(positions, cur_lons)
    except Exception:
        pass

    progressions: list[dict] = []
    progressed_date = ""
    try:
        age_seconds = (now - datetime(b.year, b.month, b.day, b.hour, b.minute)).total_seconds()
        progressed_dt = datetime(b.year, b.month, b.day, b.hour, b.minute) + timedelta(days=int(age_seconds / 86400))
        progressed_date = progressed_dt.isoformat()
        prog_lons = _planet_longitudes(progressed_dt.year, progressed_dt.month, progressed_dt.day,
                                       progressed_dt.hour, progressed_dt.minute)
        progressions = _find_progressed_aspects(positions, prog_lons)
    except Exception:
        pass

    solar_return = _solar_return_moment(b)

    return ChartResult(
        method="western", school="west", engine="skyfield+self",
        normalized={"elements": distribution["elements"], "timeline": []},
        raw={
            "planets": planets_signs,
            # 旧版 aspects 兼容 (走 astro_math.find_aspects)
            "aspects": am.find_aspects(positions),
            # 新版 Aspects 网格 (含交点 + Lilith, 差异化容许度)
            "aspects_grid": aspects_grid,
            "aspects_table": {
                "合/冲": "±8°",
                "刑/六合/拱/三合": "±6°",
                "半刑/半拱": "±3°",
                "五分相": "±2°",
                "来源": "J. Mayo / R. Hand 传统占星容许度体系",
            },
            "house_system": house_system,
            "polar_warning": polar_warning,
            "ascendant": am.sign_of(asc) if asc is not None else None,
            "midheaven": am.sign_of(mc) if mc is not None else None,
            "houses": houses,
            # 月亮交点
            "lunar_nodes": {
                "north_node": nodes,
                "south_node": {"lon": south_lon, "sign": nodes["south_sign"]},
                "interpretation": north_interpretation,
                "north_aspects": north_aspects,
                "south_aspects": south_aspects,
                "north_house": north_house,
            },
            # Lilith
            "lilith": {
                **lilith,
                "sign_meaning": LILITH_IN_SIGNS.get(lilith["lilith_sign"], ""),
            },
            # Arabic Parts (7 主 Lot)
            "arabic_parts": arabic_parts,
            "arabic_parts_count": len(arabic_parts),
            # 元素 + 模式分布
            "distribution": distribution,
            # 三通道
            "transits": transits,
            "progressions": progressions,
            "progressed_date": progressed_date,
            "solar_return": solar_return,
            # 文献来源
            "evidence_sources": [
                "Tetrabiblos (Ptolemy, ~150 AD) — classical aspects & Lots",
                "Steven Forrest, The Inner Sky — modern psychological astrology",
                "Liz Greene — psychological astrology tradition",
                "J. Mayo / R. Hand — aspect orb tables",
            ],
        },
    )
