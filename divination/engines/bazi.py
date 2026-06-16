"""八字 / 四柱  ——  lunar-python (MIT)。

Phase 3: 增加 流年/流月/神煞 到 raw['horoscope'] 和 raw['shensha'],
供 normalizer 出 current_cycle 维 signal。
"""
from __future__ import annotations

import datetime as _dt
from lunar_python import Solar
from ..contracts import Birth, ChartResult

_WX = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}

# 60 甲子 (干支循环) — 简化为查表
_TG = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_DZ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _year_gz(year: int) -> str:
    """公历年 → 年干支 (近似: 1984=甲子, 用 lunar 立春会更准, 此处简化)。"""
    # 1984 = 甲子 (0), 1985 = 乙丑 (1)...
    idx = (year - 1984) % 60
    return _TG[idx % 10] + _DZ[idx % 12]


def _month_gz(year: int, month: int) -> str:
    """公历年月 → 月干支 (年上起月法: 甲己之年丙作首, 乙庚之岁戊为头...)。

    简化: 用 (year - 1984) % 5 决定年干起月点 (甲己→丙寅起, 乙庚→戊寅起...)。
    """
    year_tg_idx = (year - 1984) % 10  # 年干在 10 天干中的索引
    # 月支固定: 正月寅, 二月卯...
    month_dz = _DZ[(month + 1) % 12]  # month=1 → 寅 (正月)
    # 年干起月口诀
    start_offset = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}
    tg_start = start_offset.get(year_tg_idx, 2)
    month_tg_idx = (tg_start + month - 1) % 10
    return _TG[month_tg_idx] + month_dz


def _liunian(birth_year: int, current_year: int) -> list[dict]:
    """流年: 出生年到当前+10 年, 每年的年干支。"""
    out = []
    for y in range(birth_year, current_year + 11):
        out.append({"year": y, "ganzhi": _year_gz(y), "label": f"{y}年 {_year_gz(y)}"})
    return out


def _liuyue(year: int, current_month: int) -> list[dict]:
    """流月: 当前年 1-12 月月干支。"""
    return [{"month": m, "ganzhi": _month_gz(year, m), "label": f"{m}月 {_month_gz(year, m)}"}
            for m in range(1, 13)]


def _shensha(lun, ec) -> dict:
    """提取 lunar-python 的神煞 (日柱层面) + 十神 (年/月/日/时四柱)。

    lunar-python 仅提供日柱吉神/凶煞/天神，无年/月/时柱神煞 API（W3 limitation）。
    为扩大覆盖，补充 EightChar 的 ShiShen 十神四柱。
    """
    out = {"吉神": [], "凶煞": [], "天神": [], "十神四柱": {}}
    try:
        ji = lun.getDayJiShen()
        if isinstance(ji, (list, tuple)):
            out["吉神"] = list(ji)
        elif isinstance(ji, str):
            out["吉神"] = [ji] if ji else []
    except Exception:
        pass
    try:
        xiong = lun.getDayXiongSha()
        if isinstance(xiong, (list, tuple)):
            out["凶煞"] = list(xiong)
        elif isinstance(xiong, str):
            out["凶煞"] = [xiong] if xiong else []
    except Exception:
        pass
    try:
        tian = lun.getDayTianShen()
        if isinstance(tian, (list, tuple)):
            out["天神"] = list(tian)
        elif isinstance(tian, str):
            out["天神"] = [tian] if tian else []
    except Exception:
        pass
    # W3 fix: 十神四柱 (年/月/日/时)，扩大神煞覆盖面
    if ec is not None:
        try:
            out["十神四柱"] = {
                "年柱": ec.getYearShiShenGan(),
                "月柱": ec.getMonthShiShenGan(),
                "日柱": ec.getDayShiShenGan(),
                "时柱": ec.getTimeShiShenGan(),
            }
        except Exception:
            pass
    return out


def compute(b: Birth, zi_hour: str = "late") -> ChartResult:
    """zi_hour: 'late'=晚子(23点不换日,lunar-python默认) | 'early'=早子(23点起算次日)"""
    h, d_, mo_, y_ = b.hour, b.day, b.month, b.year
    if zi_hour == "early" and b.hour == 23:
        from datetime import datetime, timedelta
        nd = datetime(b.year, b.month, b.day) + timedelta(days=1)
        y_, mo_, d_, h = nd.year, nd.month, nd.day, 0
        b = type(b)(**{**b.__dict__, "year": y_, "month": mo_, "day": d_, "hour": 0})
    if b.lng is not None:
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            from ..solartime import true_solar_time
            tst = true_solar_time(datetime(b.year,b.month,b.day,b.hour,b.minute,tzinfo=ZoneInfo(b.tz)), b.lng)
            solar = Solar.fromYmdHms(tst.year,tst.month,tst.day,tst.hour,tst.minute,0)
        except Exception:
            solar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
    else:
        solar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
    ec = solar.getLunar().getEightChar()
    lun = solar.getLunar()
    pillars = {
        "year": ec.getYear(), "month": ec.getMonth(),
        "day": ec.getDay(), "hour": ec.getTime(),
    }
    # 五行强弱：数四柱天干地支藏干里各五行出现次数（简化版）
    elements = {v: 0 for v in _WX.values()}
    for wx in (ec.getYearWuXing() + ec.getMonthWuXing()
               + ec.getDayWuXing() + ec.getTimeWuXing()):
        if wx in _WX:
            elements[_WX[wx]] += 1
    # 大运时间轴
    timeline = []
    try:
        yun = ec.getYun(1 if b.gender == "male" else 0)
        for da in yun.getDaYun()[1:9]:
            timeline.append({
                "from": str(da.getStartYear()), "to": str(da.getEndYear()),
                "label": "大运·" + da.getGanZhi(), "score": None,
            })
    except Exception:
        pass

    # ---- 旺衰多因子（藏干计权+通根+党势，W1 升级版）----
    from .. import wuxing as wx
    strength = wx.day_master_strength(pillars)
    es = wx.element_strength(pillars)
    wx_cn = {"木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"}
    elements = {wx_cn[k]: v for k, v in es["scored"].items()}   # 升级：藏干加权后的五行分
    judgement = {
        "旺衰": strength, "五行加权": es["scored"], "五行旺相休囚死": es["states"],
        "月令": es["month_wx"],
        "说明": strength["说明"],
    }

    # ---- Phase 3: 流年/流月/神煞 ----
    now = _dt.datetime.now()
    liunian = _liunian(b.year, now.year)
    liuyue = _liuyue(now.year, now.month)
    shensha = _shensha(lun, ec)
    horoscope = {
        "decadal":  timeline,  # 大运 (已有)
        "yearly":   liunian[-10:],  # 最近 10 年流年
        "monthly":  liuyue,         # 当前年 12 月
        "daily":    [],
        "hourly":   [],
        "current_year": now.year,
        "current_month": now.month,
    }
    return ChartResult(
        method="bazi", school="east", engine="lunar-python",
        normalized={"elements": elements, "timeline": timeline},
        raw={
            "pillars": pillars,
            "day_master": ec.getDayGan(),
            "断": judgement,
            "horoscope": horoscope,
            "shensha": shensha,
        },
    )
