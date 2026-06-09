"""西方占星的纯数学层:星座、四元素、相位、上升点、宫位。
完全自实现,不依赖任何星历库 —— 输入只是黄经度数,因此可独立测试。
"""
import math

SIGNS = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
         "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
ELEMENTS = ["火", "土", "风", "水"]  # 按星座顺序循环

ASPECTS = {  # 相位角 -> (名称, 容许度 orb)
    0:   ("合相", 8),
    60:  ("六分相", 4),
    90:  ("刑相", 6),
    120: ("拱相", 6),
    180: ("冲相", 8),
}


def sign_of(longitude: float) -> dict:
    """黄经 -> 星座名 + 宫内度数 + 元素。"""
    lon = longitude % 360
    idx = int(lon // 30)
    return {
        "sign": SIGNS[idx],
        "degree": round(lon % 30, 2),
        "element": ELEMENTS[idx % 4],
        "lon": round(lon, 4),
    }


def _sep(a: float, b: float) -> float:
    """两点最小角距 0-180。"""
    d = abs((a - b) % 360)
    return min(d, 360 - d)


def find_aspects(positions: dict[str, float]) -> list[dict]:
    """positions: {行星名: 黄经}。返回所有命中的相位。"""
    names = list(positions)
    out = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            sep = _sep(positions[names[i]], positions[names[j]])
            for angle, (label, orb) in ASPECTS.items():
                if abs(sep - angle) <= orb:
                    out.append({
                        "a": names[i], "b": names[j],
                        "aspect": label, "angle": angle,
                        "orb": round(abs(sep - angle), 2),
                    })
                    break
    return out


def ascendant(lst_deg: float, lat_deg: float, obliquity_deg: float = 23.4367) -> float:
    """上升点黄经。lst_deg = 本地恒星时(度)=RAMC;lat=纬度;obliquity=黄赤交角。
    标准公式;建议在你的环境用已知星盘校验一次。
    """
    ramc = math.radians(lst_deg)
    eps = math.radians(obliquity_deg)
    lat = math.radians(lat_deg)
    asc = math.atan2(
        math.cos(ramc),
        -(math.sin(ramc) * math.cos(eps) + math.tan(lat) * math.sin(eps)),
    )
    return math.degrees(asc) % 360


def houses(asc_lon: float, system: str = "whole") -> list[dict]:
    """宫位划分。
    whole = 整宫制(上升所在星座为第1宫,每宫一整个星座);
    equal = 等宫制(上升度数起,每 30° 一宫)。
    Placidus 需迭代天文计算,留作 TODO。
    """
    cusps = []
    if system == "whole":
        start = (int(asc_lon // 30)) * 30  # 上升星座起点
    elif system == "equal":
        start = asc_lon
    else:
        raise NotImplementedError("Placidus 待实现(B 路需自算,迭代法)")
    for h in range(12):
        cusps.append({"house": h + 1, "cusp_lon": round((start + 30 * h) % 360, 2)})
    return cusps
