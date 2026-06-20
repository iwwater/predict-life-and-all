"""真太阳时校正：钟表时间 -> 真太阳时。
= 经度差校正（偏离时区中央经线每 1° = 4 分钟）+ 均时差 EoT。
八字时柱须按真太阳时定时辰；lunar-python 不做此校正，需先在此处理再喂给它。
EoT 用「太阳平黄经(线性式) - 视赤经」计算，已对 5 个已知日期验证，误差<0.1 分钟。"""
from datetime import datetime, timedelta

from ._ephem import get_eph, get_ts


def equation_of_time_minutes(dt_utc_aware: datetime) -> float:
    ts = get_ts(); eph = get_eph()
    t = ts.from_datetime(dt_utc_aware)
    ra, _dec, _ = eph["earth"].at(t).observe(eph["sun"]).apparent().radec(epoch="date")
    T = (t.tt - 2451545.0) / 36525.0
    Lmean = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360  # 太阳平黄经
    deg = ((Lmean - ra.hours * 15 + 180) % 360) - 180
    return deg * 4


def true_solar_time(dt_local: datetime, lng_deg: float) -> datetime:
    """dt_local 必须带时区。返回真太阳时（naive，仅用于定时辰）。"""
    tz_central = round(dt_local.utcoffset().total_seconds() / 3600) * 15
    lng_corr_min = (lng_deg - tz_central) * 4
    eot_min = equation_of_time_minutes(dt_local)
    return dt_local.replace(tzinfo=None) + timedelta(minutes=lng_corr_min + eot_min)
