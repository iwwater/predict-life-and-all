"""八宅风水（命卦+八游年方位吉凶）—— 文献：《八宅明镜》。用出生年+性别。"""
from ..contracts import Birth, ChartResult
from ..fengshui import bazhai as _bazhai


def compute(b: Birth) -> ChartResult:
    r = _bazhai(b.year, b.gender)
    return ChartResult(method="bazhai", school="east", engine="self(八宅明镜)",
                       normalized={"elements": {}, "timeline": []}, raw=r)
