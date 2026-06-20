"""西方/吠陀共用行星黄经（当日黄道 epoch=t）+ 缓存。
会审中西占与吠陀同人同盘 -> 行星只算一次。星历走共享单例。"""
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from .._ephem import get_eph, get_ts
from ..contracts import Birth

_PLANETS = {"太阳": "sun", "月亮": "moon", "水星": "mercury", "金星": "venus",
            "火星": "mars", "木星": "jupiter barycenter", "土星": "saturn barycenter"}


@lru_cache(maxsize=512)
def _compute_cached(year, month, day, hour, minute, tz):
    ts = get_ts(); eph = get_eph(); earth = eph["earth"]
    t = ts.from_datetime(datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz)))
    out = {}
    for cn, key in _PLANETS.items():
        _lat, lon, _d = earth.at(t).observe(eph[key]).apparent().ecliptic_latlon(epoch=t)
        out[cn] = lon.degrees % 360
    return out, float(t.tt), float(t.gmst)   # 经度dict, TT儒略日, 格林尼治恒星时(小时)


def planet_tropical_longitudes(b: Birth):
    out, tt, _gmst = _compute_cached(b.year, b.month, b.day, b.hour, b.minute, b.tz)
    return dict(out), tt


def planets_and_gmst(b: Birth):
    out, _tt, gmst = _compute_cached(b.year, b.month, b.day, b.hour, b.minute, b.tz)
    return dict(out), gmst
