"""西方占星  ——  完整 natal chart + 10 行星 + 整宫制 + 相位 + 宫主星分析。

B 路:skyfield (MIT) + JPL 星历(公版), 星座/相位/宫位自算。
零 AGPL, 可闭源商用。首次运行 skyfield 会自动下载 de421.bsp(联网即可)。

v2 新增:
- 天海冥三王星 (Uranus / Neptune / Pluto)
- 星座模式(开创/固定/变动)与元素分布统计
- 宫主星分析 (house rulers)
- 相位模式统计 (合/冲/拱/刑/六合)
- 上升守护星
"""
from ..contracts import Birth, ChartResult
from .. import astro_math as am

# v1 古典七星
_PLANETS_CLASSICAL = {
    "太阳": "sun", "月亮": "moon",
    "水星": "mercury", "金星": "venus",
    "火星": "mars",
    "木星": "jupiter barycenter", "土星": "saturn barycenter",
}

# v2: 10 行星 (古典 + 三王星)
_PLANETS = {
    **_PLANETS_CLASSICAL,
    "天王星": "uranus barycenter",
    "海王星": "neptune barycenter",
    "冥王星": "pluto barycenter",
}

# 宫主星映射 (古典守护, 用于整宫制)
_HOUSE_RULER = {
    0: "火星",     # 白羊 → 火
    1: "金星",     # 金牛 → 金
    2: "水星",     # 双子 → 水
    3: "月亮",     # 巨蟹 → 月
    4: "太阳",     # 狮子 → 日
    5: "水星",     # 处女 → 水
    6: "金星",     # 天秤 → 金
    7: "冥王星",   # 天蝎 → 冥(古典:火星)
    8: "木星",     # 射手 → 木
    9: "土星",     # 摩羯 → 土
    10: "天王星",  # 水瓶 → 天(古典:土星)
    11: "海王星",  # 双鱼 → 海(古典:木星)
}

_HOUSE_RULER_CLASSICAL = {
    0: "火星", 1: "金星", 2: "水星", 3: "月亮",
    4: "太阳", 5: "水星", 6: "金星", 7: "火星",
    8: "木星", 9: "土星", 10: "土星", 11: "木星",
}

# 星座模式 (Modality)
_SIGN_MODALITY = {
    "白羊座": "开创", "金牛座": "固定", "双子座": "变动",
    "巨蟹座": "开创", "狮子座": "固定", "处女座": "变动",
    "天秤座": "开创", "天蝎座": "固定", "射手座": "变动",
    "摩羯座": "开创", "水瓶座": "固定", "双鱼座": "变动",
}

_MODALITY_CN_TO_EN = {"开创": "cardinal", "固定": "fixed", "变动": "mutable"}


def _analyze_distribution(planets: dict) -> dict:
    """分析行星在元素和模式中的分布。"""
    elem_count = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    modality_count = {"cardinal": 0, "fixed": 0, "mutable": 0}

    for p_name, p_data in planets.items():
        el = p_data.get("element", "")
        elem_map = {"火": "fire", "土": "earth", "风": "air", "水": "water"}
        eng = elem_map.get(el, el)
        if eng in elem_count:
            elem_count[eng] += 1

        sign_name = p_data.get("sign_name_zh", "")
        modality_cn = _SIGN_MODALITY.get(sign_name, "")
        modality_en = _MODALITY_CN_TO_EN.get(modality_cn, "")
        if modality_en in modality_count:
            modality_count[modality_en] += 1

    dom_elem = max(elem_count, key=elem_count.get) if any(elem_count.values()) else None
    dom_mod = max(modality_count, key=modality_count.get) if any(modality_count.values()) else None
    missing = [e for e, c in elem_count.items() if c == 0]

    elem_notes = {
        "fire": "火元素代表行动力与热情",
        "earth": "土元素代表务实与稳定",
        "air": "风元素代表思维与沟通",
        "water": "水元素代表情感与直觉",
    }
    mod_notes = {
        "cardinal": "开创模式强——善于启动,但可能缺乏持续力",
        "fixed": "固定模式强——稳定持久,但可能抗拒变化",
        "mutable": "变动模式强——适应力好,但可能方向感弱",
    }

    interpretation = []
    if dom_elem:
        interpretation.append(f"主导元素: {elem_notes.get(dom_elem, '')}")
    if dom_mod:
        interpretation.append(mod_notes.get(dom_mod, ""))
    if missing:
        missing_cn = [{"fire": "火", "earth": "土", "air": "风", "water": "水"}.get(m, m) for m in missing]
        interpretation.append(f"缺失元素: {'/'.join(missing_cn)}——此领域需要外部补充或刻意发展")

    return {
        "elements": elem_count,
        "modalities": modality_count,
        "dominant_element": dom_elem,
        "dominant_modality": dom_mod,
        "missing_elements": missing,
        "interpretation": "。".join(interpretation) + "。" if interpretation else "",
    }


def _compute_house_rulers(planets: dict, houses: list, asc_sign_idx: int | None) -> dict:
    """计算宫主星位置和状态。"""
    if asc_sign_idx is None or not houses:
        return {}

    house_rulers = {}
    for h in houses:
        h_num = h.get("house", 0)
        if h_num < 1:
            continue
        cusp_sign_idx = (asc_sign_idx + h_num - 1) % 12
        ruler_cn = _HOUSE_RULER.get(cusp_sign_idx, "")
        ruler_classical = _HOUSE_RULER_CLASSICAL.get(cusp_sign_idx, "")

        ruler_house = None
        ruler_sign = None
        for p_name, p_data in planets.items():
            if p_name == ruler_cn or p_name == ruler_classical:
                ruler_house = p_data.get("house")
                ruler_sign = p_data.get("sign_name_zh", "")
                break

        house_rulers[f"第{h_num}宫"] = {
            "cusp_sign_idx": cusp_sign_idx,
            "ruler": ruler_cn,
            "ruler_classical": ruler_classical,
            "ruler_in_house": ruler_house,
            "ruler_in_sign": ruler_sign,
        }

    return house_rulers


def _compute_asc_ruler(asc_sign_idx: int | None, planets: dict) -> dict:
    """计算上升星座的守护星及其位置。"""
    if asc_sign_idx is None:
        return {}
    ruler_cn = _HOUSE_RULER.get(asc_sign_idx, "")
    ruler_classical = _HOUSE_RULER_CLASSICAL.get(asc_sign_idx, "")

    ruler_data = None
    for p_name, p_data in planets.items():
        if p_name == ruler_cn or p_name == ruler_classical:
            ruler_data = {
                "planet": p_name,
                "sign": p_data.get("sign_name_zh", ""),
                "house": p_data.get("house"),
                "element": p_data.get("element", ""),
                "dignity": "入庙" if ruler_cn == p_name else "古典守护",
            }
            break

    return {
        "ascendant_sign_idx": asc_sign_idx,
        "ruler": ruler_cn,
        "ruler_classical": ruler_classical,
        "ruler_position": ruler_data,
    }


def _summarize_aspects(aspects: list) -> dict:
    """统计相位类型分布。"""
    type_count = {}
    for a in aspects:
        t = a.get("type", a.get("aspect", "unknown"))
        type_count[t] = type_count.get(t, 0) + 1

    major_types = {"合": "conjunction", "冲": "opposition", "拱": "trine", "刑": "square", "六合": "sextile"}
    summary = {}
    for cn, en in major_types.items():
        if cn in type_count:
            summary[en] = type_count[cn]

    hard = summary.get("square", 0) + summary.get("opposition", 0)
    soft = summary.get("trine", 0) + summary.get("sextile", 0)
    conj = summary.get("conjunction", 0)

    note = ""
    if hard > soft + 2:
        note = "硬相位(刑冲)较多,人生张力大,但也提供了成长的动力和韧性"
    elif soft > hard + 3:
        note = "软相位(拱/六合)较多,天赋自然流露,但可能缺乏突破舒适圈的紧迫感"
    elif conj > soft + hard:
        note = "合相突出,能量高度集中,某些人生领域会出现极端体验"
    else:
        note = "相位分布均衡,软硬张力适中"

    return {
        "breakdown": summary,
        "total": sum(summary.values()),
        "hard_aspects": hard,
        "soft_aspects": soft,
        "conjunctions": conj,
        "note": note,
    }


def compute(b: Birth, eph_path: str = "de421.bsp") -> ChartResult:
    from skyfield.api import load
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ts = load.timescale()
    eph = load(eph_path)
    earth = eph["earth"]

    dt = datetime(b.year, b.month, b.day, b.hour, b.minute, tzinfo=ZoneInfo(b.tz))
    t = ts.from_datetime(dt)

    # ── 10 行星地心黄经 ──
    positions = {}
    for cn, key in _PLANETS.items():
        try:
            astrometric = earth.at(t).observe(eph[key]).apparent()
            lon, lat, _ = astrometric.ecliptic_latlon()
            positions[cn] = lon.degrees % 360
        except Exception:
            # 如果某颗行星加载失败(如 de421 不含冥王星),跳过
            pass

    planets = {cn: am.sign_of(lon) for cn, lon in positions.items()}

    # ── 相位 ──
    aspects = am.find_aspects(positions)

    # ── 宫位 & 上升 ──
    house_data, asc_sign_idx = [], None
    asc = None
    if b.lat is not None and b.lng is not None:
        gst = t.gmst
        lst_deg = (gst * 15 + b.lng) % 360
        asc_lon = am.ascendant(lst_deg, b.lat)
        asc_sign_idx = int(asc_lon // 30) if asc_lon else None
        asc = am.sign_of(asc_lon) if asc_lon is not None else None
        house_data = am.houses(asc_lon if asc_lon else 0, system="whole")

    # ── 将行星归入宫位 ──
    planets_with_houses = {}
    for cn, data in planets.items():
        p_data = dict(data)
        if house_data and asc_sign_idx is not None:
            lon = data["lon"]
            h = int(lon // 30)
            house_num = ((h - asc_sign_idx) % 12) + 1
            p_data["house"] = house_num
        else:
            p_data["house"] = 0
        planets_with_houses[cn] = p_data

    # ── 分布分析 ──
    distribution = _analyze_distribution(planets_with_houses)

    # ── 宫主星分析 ──
    house_rulers = _compute_house_rulers(planets_with_houses, house_data, asc_sign_idx)

    # ── 上升守护星 ──
    asc_ruler = _compute_asc_ruler(asc_sign_idx, planets_with_houses)

    # ── 相位汇总 ──
    aspect_summary = _summarize_aspects(aspects)

    # ── 归一化元素(用于跨引擎对比) ──
    elem_count = distribution["elements"]

    return ChartResult(
        method="western",
        school="west",
        engine="skyfield+self+v2",
        normalized={
            "elements": elem_count,
            "timeline": [],
        },
        raw={
            "rule_version": "v2",
            "planet_count": len(positions),
            "planets": planets_with_houses,
            "aspects": aspects,
            "ascendant": asc,
            "ascendant_sign_idx": asc_sign_idx,
            "houses": house_data,
            "distribution": distribution,
            "house_rulers": house_rulers,
            "ascendant_ruler": asc_ruler,
            "aspect_summary": aspect_summary,
            "calculation_basis": {
                "method": "western_astrology",
                "mode": "natal",
                "rule_version": "v2",
                "calendar_source": "skyfield + de421.bsp (JPL)",
                "house_system": "whole sign",
                "planets_included": list(positions.keys()),
                "planet_count": len(positions),
                "limits": [
                    "木星/土星/天王/海王/冥王使用 barycenter(质心),高精度场景需区分",
                    "宫位系统仅限整宫制(whole sign),Placidus 待实现",
                    "不包含小行星、阿拉伯点、中点等进阶技法",
                    "不包含出生前新月/满月等月相分析",
                    "三王星可能不被 de421.bsp 覆盖(该星历以 1900-2050 为主),若缺失会自动跳过",
                ],
            },
        },
    )
