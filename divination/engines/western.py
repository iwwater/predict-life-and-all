"""西方占星 —— B 路：skyfield (MIT) + JPL 公版星历，星座/相位/宫位自算。零 AGPL。

深度调查修正（均已实测验证）：
  1) ecliptic_latlon() 返回顺序是 (纬度, 经度, 距离) —— 经度在第 2 位（曾写反）。
  2) 必须传 epoch=t 用「当日黄道」（回归黄道）；否则按 J2000 会差一个岁差量
     （2025 年约 0.34°，且逐年增大）。已验证 epoch=t 把二分二至误差降到 0.000°。
  3) Placidus 宫位已实现并用半弧自洽法在 5 个纬度验证通过。
"""
from ..contracts import Birth, ChartResult
from .. import astro_math as am

_PLANETS = {
    "太阳": "sun", "月亮": "moon", "水星": "mercury", "金星": "venus",
    "火星": "mars", "木星": "jupiter barycenter", "土星": "saturn barycenter",
}


def _loader():
    try:
        from skyfield_data import get_skyfield_data_path
        from skyfield.api import Loader
        return Loader(get_skyfield_data_path())   # 离线（推荐：星历打进镜像）
    except Exception:
        from skyfield.api import Loader
        return Loader(".")                          # 首次联网自动下载 de421.bsp


def compute(b: Birth, house_system: str = "placidus") -> ChartResult:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    load = _loader()
    ts = load.timescale(); eph = load("de421.bsp"); earth = eph["earth"]

    dt = datetime(b.year, b.month, b.day, b.hour, b.minute, tzinfo=ZoneInfo(b.tz))
    t = ts.from_datetime(dt)

    # 行星地心黄经（修正①顺序 修正②当日黄道 epoch=t）
    positions = {}
    for cn, key in _PLANETS.items():
        _lat, lon, _d = earth.at(t).observe(eph[key]).apparent().ecliptic_latlon(epoch=t)
        positions[cn] = lon.degrees % 360

    planets = {cn: am.sign_of(lon) for cn, lon in positions.items()}
    aspects = am.find_aspects(positions)

    houses, asc, mc = [], None, None
    if b.lat is not None and b.lng is not None:
        ramc = (t.gmst * 15 + b.lng) % 360         # 本地恒星时(度) = RAMC
        mc = am.midheaven(ramc)
        asc = am.ascendant(ramc, b.lat)
        if house_system == "placidus":
            houses = am.placidus_houses(ramc, b.lat)
        else:
            houses = am.houses(asc, house_system)

    elem = {"火": 0, "土": 0, "风": 0, "水": 0}
    for p in planets.values():
        elem[p["element"]] += 1

    return ChartResult(
        method="western", school="west", engine="skyfield+self",
        normalized={"elements": elem, "timeline": []},
        raw={"planets": planets, "aspects": aspects, "house_system": house_system,
             "ascendant": am.sign_of(asc) if asc is not None else None,
             "midheaven": am.sign_of(mc) if mc is not None else None,
             "houses": houses},
    )
