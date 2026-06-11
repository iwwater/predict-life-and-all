"""西方/吠陀共用：取行星回归黄经（当日黄道 epoch=t）。"""
from ..contracts import Birth

_PLANETS = {"太阳": "sun", "月亮": "moon", "水星": "mercury", "金星": "venus",
            "火星": "mars", "木星": "jupiter barycenter", "土星": "saturn barycenter"}


def _loader():
    try:
        from skyfield_data import get_skyfield_data_path
        from skyfield.api import Loader
        return Loader(get_skyfield_data_path())
    except Exception:
        from skyfield.api import Loader
        return Loader(".")


def planet_tropical_longitudes(b: Birth):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    load = _loader(); ts = load.timescale(); eph = load("de421.bsp"); earth = eph["earth"]
    t = ts.from_datetime(datetime(b.year, b.month, b.day, b.hour, b.minute, tzinfo=ZoneInfo(b.tz)))
    out = {}
    for cn, key in _PLANETS.items():
        _lat, lon, _d = earth.at(t).observe(eph[key]).apparent().ecliptic_latlon(epoch=t)
        out[cn] = lon.degrees % 360
    return out, t.tt
