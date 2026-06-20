"""星历单例：de421.bsp 与 timescale 只加载一次，全模块复用。
此前 western/vedic/solartime 各自每次 compute 重载星历，是主要性能热点。"""
_TS = None
_EPH = None


def _loader():
    try:
        from skyfield.api import Loader

        from skyfield_data import get_skyfield_data_path
        return Loader(get_skyfield_data_path())   # 离线（星历打进镜像）
    except Exception:
        from skyfield.api import Loader
        return Loader(".")                          # 兜底：首次联网下载


def get_ts():
    global _TS
    if _TS is None:
        _TS = _loader().timescale()
    return _TS


def get_eph():
    global _EPH
    if _EPH is None:
        _EPH = _loader()("de421.bsp")
    return _EPH
