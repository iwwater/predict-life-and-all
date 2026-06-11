"""紫微斗数  ——  py-iztro (上游 iztro, MIT)。"""
from py_iztro import Astro
from ..contracts import Birth, ChartResult

_astro = Astro()


def compute(b: Birth) -> ChartResult:
    g = "男" if b.gender == "male" else "女"
    # py-iztro 时辰用 0-12 序号；hour//2 近似
    r = _astro.by_solar(f"{b.year}-{b.month}-{b.day}", b.hour // 2, g, True, "zh-CN")
    palaces = [{
        "name": p.name,
        "is_body": p.is_body_palace,
        "major_stars": [s.name for s in p.major_stars],
    } for p in r.palaces]
    return ChartResult(
        method="ziwei", school="east", engine="py-iztro",
        normalized={"elements": {}, "timeline": []},
        raw={"soul": r.soul, "body": r.body, "five_elements": r.five_elements_class,
             "palaces": palaces},
    )
