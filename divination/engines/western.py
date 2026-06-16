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

    # Phase 3: 行运 transits — 当前时刻行星 vs 本命行星的相位
    transits: list[dict] = []
    transit_date_str: str | None = None
    try:
        from datetime import datetime as _dt
        from datetime import timezone as _tz
        now = _dt.now(_tz.utc)
        t_now = ts.from_datetime(now)
        transit_date_str = now.isoformat()
        transit_positions: dict[str, float] = {}
        for cn, key in _PLANETS.items():
            _lat, lon, _d = earth.at(t_now).observe(eph[key]).apparent().ecliptic_latlon(epoch=t_now)
            transit_positions[cn] = lon.degrees % 360
        # 用 am.find_aspects 算本命 vs 行运 (按顺序: natal → transit)
        for natal_cn, natal_lon in positions.items():
            for trans_cn, trans_lon in transit_positions.items():
                diff = abs(natal_lon - trans_lon) % 360
                if diff > 180:
                    diff = 360 - diff
                # W4 fix: 容许度按 transit 行星重要性分级
                # 外行星(冥王10°/木星8°/土星8°)用大orb，内行星按重要性递减
                PLANET_ORB = {
                    "冥王": 10, "Pluto": 10,
                    "木星": 8, "Jupiter": 8, "土星": 8, "Saturn": 8,
                    "太阳": 8, "Sun": 8,
                    "火星": 6, "Mars": 6,
                    "金星": 5, "Venus": 5,
                    "水星": 4, "Mercury": 4,
                    "月亮": 4, "Moon": 4,
                }
                planet_orb = PLANET_ORB.get(trans_cn, 5)  # default 5°
                for asp_name, asp_deg, base_orb in [
                    ("合", 0, 8), ("冲", 180, 8), ("刑", 90, 6), ("拱", 120, 6), ("六合", 60, 4),
                ]:
                    orb = min(planet_orb, base_orb)  # 用较小者，更严格
                    if abs(diff - asp_deg) <= orb:
                        is_hard = asp_name in ("冲", "刑")
                        transits.append({
                            "natal_planet": natal_cn,
                            "transit_planet": trans_cn,
                            "aspect": asp_name,
                            "orb": round(abs(diff - asp_deg), 2),
                            "is_hard": is_hard,
                        })
                        break
        # 截断最多 12 条 (避免过载)
        transits = transits[:12]
    except Exception:
        transits = []

    # Phase H: 次限推运 (secondary progressions)
    # "出生后第 N 天 = N 岁时的星图" — 1 day = 1 year
    progressions: list[dict] = []
    prog_date_str: str | None = None
    try:
        from datetime import date as _date
        birth_date = _date(b.year, b.month, b.day)
        today = _date.today()
        days_lived = (today - birth_date).days
        # Progressed date = birth + days_lived days (1 day = 1 year)
        prog_dt = _date(birth_date.year, birth_date.month, birth_date.day)
        import datetime as _dt
        prog_target = prog_dt + _dt.timedelta(days=days_lived)
        prog_date_str = prog_target.isoformat()
        # Compute planetary positions at progressed date
        prog_t = ts.from_datetime(
            _dt.datetime(prog_target.year, prog_target.month, prog_target.day, b.hour, b.minute)
        )
        prog_positions: dict[str, float] = {}
        for cn, key in _PLANETS.items():
            _lat, lon, _d = earth.at(prog_t).observe(eph[key]).apparent().ecliptic_latlon(epoch=prog_t)
            prog_positions[cn] = lon.degrees % 360
        # Aspects: progressed vs natal (same orb as W4)
        for natal_cn, natal_lon in positions.items():
            prog_lon = prog_positions.get(natal_cn, natal_lon)
            diff = abs(natal_lon - prog_lon) % 360
            if diff > 180:
                diff = 360 - diff
            for asp_name, asp_deg, base_orb in [
                ("合", 0, 8), ("冲", 180, 8), ("刑", 90, 6), ("拱", 120, 6), ("六合", 60, 4),
            ]:
                if abs(diff - asp_deg) <= base_orb:
                    progressions.append({
                        "planet": natal_cn,
                        "natal_lon": round(natal_lon, 2),
                        "progressed_lon": round(prog_lon, 2),
                        "shift_deg": round(diff, 2),
                        "aspect": asp_name,
                        "is_hard": asp_name in ("冲", "刑"),
                    })
                    break
        progressions = progressions[:10]
    except Exception:
        progressions = []

    return ChartResult(
        method="western", school="west", engine="skyfield+self",
        normalized={"elements": elem, "timeline": []},
        raw={"planets": planets, "aspects": aspects, "house_system": house_system,
             "ascendant": am.sign_of(asc) if asc is not None else None,
             "midheaven": am.sign_of(mc) if mc is not None else None,
             "houses": houses,
             "transits": transits,
             "transit_date": transit_date_str,
             "progressions": progressions,
             "progressed_date": prog_date_str},
    )
