"""八字 / 四柱  ——  lunar-python (MIT)。"""
from lunar_python import Solar
from ..contracts import Birth, ChartResult

_WX = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}


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
    return ChartResult(
        method="bazi", school="east", engine="lunar-python",
        normalized={"elements": elements, "timeline": timeline},
        raw={"pillars": pillars, "day_master": ec.getDayGan(), "断": judgement},
    )
