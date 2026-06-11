"""玄空飞星排盘 —— 文献：《沈氏玄空学》。需 period(运 1-9) + sitting(坐山)。
用法：compute(birth, period=8, sitting='子')；运缺省按建造/起造年推。"""
from ..contracts import Birth, ChartResult
from ..fengshui import xuankong as _xk, san_yuan_jiu_yun


def compute(b: Birth, period: int | None = None, sitting: str = "子") -> ChartResult:
    if period is None:
        period = san_yuan_jiu_yun(b.year)["运"]
    r = _xk(period, sitting)
    return ChartResult(method="xuankong", school="east", engine="self(沈氏玄空)",
                       normalized={"elements": {}, "timeline": []}, raw=r)
