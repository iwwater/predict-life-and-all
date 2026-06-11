"""天文层 golden：历史上抓出 3 个真 bug 的全部验证，固化为带数值阈值的回归。"""
import math
import pytest
from skyfield_data import get_skyfield_data_path
from skyfield.api import Loader

load = Loader(get_skyfield_data_path())
ts = load.timescale(); eph = load("de421.bsp"); earth, sun = eph["earth"], eph["sun"]


def sun_lon(y, mo, d, h, mi):
    _, lon, _ = earth.at(ts.utc(y, mo, d, h, mi)).observe(sun).apparent().ecliptic_latlon(
        epoch=ts.utc(y, mo, d, h, mi))
    return lon.degrees % 360


@pytest.mark.parametrize("label,args,expect", [
    ("春分", (2020, 3, 20, 3, 49), 0), ("夏至", (2020, 6, 20, 21, 43), 90),
    ("秋分", (2020, 9, 22, 13, 30), 180), ("冬至", (2020, 12, 21, 10, 2), 270)])
def test_sun_longitude_equinox(label, args, expect):
    """守护：ecliptic_latlon 顺序(纬,经,距) + 当日黄道 epoch=t（两个历史 bug）。"""
    lon = sun_lon(*args)
    assert abs((lon - expect + 180) % 360 - 180) < 0.02, label


def test_ascendant_on_horizon():
    """守护：上升点公式。反推地平高度必须≈0 且在东方。"""
    from divination import astro_math as am
    from datetime import datetime
    from zoneinfo import ZoneInfo
    for args, lat, lng in [((1990, 5, 15, 8, 30, "Asia/Shanghai"), 31.23, 121.47),
                           ((1985, 11, 2, 14, 0, "Europe/London"), 51.51, -0.13),
                           ((2001, 7, 4, 23, 15, "America/New_York"), 40.71, -74.01)]:
        t = ts.from_datetime(datetime(*args[:5], tzinfo=ZoneInfo(args[5])))
        lst = (t.gmst * 15 + lng) % 360
        asc = am.ascendant(lst, lat)
        # 反推 alt/az
        eps = 23.4367
        lo, e, la = map(math.radians, (asc, eps, lat))
        ra = math.atan2(math.sin(lo) * math.cos(e), math.cos(lo))
        dec = math.asin(math.sin(e) * math.sin(lo))
        H = math.radians(lst) - ra
        alt = math.degrees(math.asin(math.sin(la) * math.sin(dec)
                                     + math.cos(la) * math.cos(dec) * math.cos(H)))
        az = math.degrees(math.atan2(-math.cos(dec) * math.sin(H),
                                     math.sin(dec) * math.cos(la)
                                     - math.cos(dec) * math.sin(la) * math.cos(H))) % 360
        assert abs(alt) < 0.01
        assert 0 < az < 180  # 东方


@pytest.mark.parametrize("ramc,lat", [(120, 31.23), (200, 51.51), (330, 40.71), (80, 1.3), (150, 59.9)])
def test_placidus_semi_arc(ramc, lat):
    """守护：Placidus 半弧自洽（含赤道/高纬）。"""
    from divination import astro_math as am
    cusps = {c["house"]: c["cusp_lon"] for c in am.placidus_houses(ramc, lat)}
    eps = 23.4367
    def ra_of(lon):
        return math.degrees(math.atan2(math.sin(math.radians(lon)) * math.cos(math.radians(eps)),
                                       math.cos(math.radians(lon)))) % 360
    def dsa(lon):
        x = -math.tan(math.radians(lat)) * math.tan(math.radians(
            math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lon))))))
        return math.degrees(math.acos(max(-1, min(1, x))))
    for h, kind, f in [(11, "day", 1/3), (12, "day", 2/3), (2, "night", 2/3), (3, "night", 1/3)]:
        H = ((ramc - ra_of(cusps[h]) + 180) % 360) - 180
        ds = dsa(cusps[h])
        exp = -f * ds if kind == "day" else -(180 - f * (180 - ds))
        exp = ((exp + 180) % 360) - 180
        assert abs(((H - exp + 180) % 360) - 180) < 0.02


@pytest.mark.parametrize("ymd,expect", [
    ((2024, 2, 11), -14.2), ((2024, 11, 3), 16.5), ((2024, 4, 15), 0.0),
    ((2024, 7, 26), -6.5), ((2024, 5, 14), 3.7)])
def test_equation_of_time(ymd, expect):
    """守护：均时差用平黄经（历史 bug：误用视黄经差 5-7 分钟）。"""
    from datetime import datetime, timezone
    from divination.solartime import equation_of_time_minutes
    v = equation_of_time_minutes(datetime(*ymd, 12, tzinfo=timezone.utc))
    assert abs(v - expect) < 1.0
