"""数字命理（毕达哥拉斯派）—— 生命灵数 + 命运数（姓名）。文献：Pythagorean numerology。"""
from ..contracts import Birth, ChartResult

_MEANING = {1: "独立·领导", 2: "合作·敏感", 3: "表达·创造", 4: "务实·秩序",
            5: "自由·变化", 6: "责任·关爱", 7: "内省·智慧", 8: "权力·财富",
            9: "博爱·完成", 11: "灵性·直觉(大师数)", 22: "实干理想(大师数)", 33: "大爱导师(大师数)"}
_LETTER = {c: (i % 9) + 1 for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}


def _reduce(n: int) -> int:
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n


def compute(b: Birth, name: str | None = None) -> ChartResult:
    digits = sum(int(d) for d in f"{b.year}{b.month:02d}{b.day:02d}")
    life = _reduce(digits)
    raw = {"生命灵数": life, "释义": _MEANING.get(life, "")}
    if name:
        total = sum(_LETTER.get(ch.upper(), 0) for ch in name if ch.upper() in _LETTER)
        dest = _reduce(total)
        raw["命运数"] = dest
        raw["命运数释义"] = _MEANING.get(dest, "")
    return ChartResult(method="numerology", school="west", engine="self(Pythagorean)",
                       normalized={"elements": {}, "timeline": []}, raw=raw)
