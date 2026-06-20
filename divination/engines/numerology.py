"""数字命理综合 — 毕达哥拉斯 + 中文三才五格。

文献:
  - Pythagorean Numerology (现代)
  - 《姓名学大辞典》(现代·熊崎氏流派)
  - 《康熙字典》(清) — 笔画基准
  - Chaldean Numerology (古代巴比伦)

支持:
  1. 生命灵数 (Life Path) — 毕达哥拉斯
  2. 命运数 (Destiny) — 姓名毕达哥拉斯
  3. 中文三才五格 — 康熙字典笔画
  4. 大师数 (Master Numbers) — 11/22/33 特殊处理
"""
from __future__ import annotations

from typing import Any

from ..contracts import Birth, ChartResult
from ..data.numerology_xingming import (
    KANGXI_STROKES_ALL,
    SHULI_JIXIONG,
    compute_wuge,
    num_to_wuxing,
)

# 毕达哥拉斯字母映射 (西方体系)
_LETTER_PYTHAGOREAN = {c: (i % 9) + 1 for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}

# Chaldean 数字映射 (简化版)
_LETTER_CHALDEAN = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5, "I": 1,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8, "Q": 1, "R": 2,
    "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 5, "Y": 1, "Z": 7,
}


def _reduce(n: int, keep_masters: bool = True) -> int:
    """数字归约到 1-9 (或保留大师数 11/22/33)。"""
    while n > 9 and not (keep_masters and n in (11, 22, 33)):
        n = sum(int(d) for d in str(n))
    return n


def _life_path_pythagorean(birth_date: str) -> dict:
    """毕达哥拉斯生命灵数。

    Args:
        birth_date: 生日字符串, 格式 YYYY-MM-DD 或 YYYYMMDD
    """
    digits = "".join(c for c in birth_date if c.isdigit())
    if len(digits) < 8:
        return {"error": "日期格式错误"}
    y, m, d = int(digits[:4]), int(digits[4:6]), int(digits[6:8])
    total = sum(int(c) for c in digits)
    life = _reduce(total)
    return {
        "system": "毕达哥拉斯",
        "raw_digits": digits,
        "sum": total,
        "life_path": life,
        "is_master": life in (11, 22, 33),
    }


def _destiny_pythagorean(name: str) -> dict:
    """毕达哥拉斯命运数 (姓名)。

    公式: 姓名每个字母 → 数字 → 相加 → 归约
    """
    total = sum(_LETTER_PYTHAGOREAN.get(ch.upper(), 0) for ch in name if ch.isalpha())
    destiny = _reduce(total)
    return {
        "system": "毕达哥拉斯",
        "name": name,
        "sum": total,
        "destiny": destiny,
        "is_master": destiny in (11, 22, 33),
    }


def _destiny_chaldean(name: str) -> dict:
    """Chaldean 命运数 (古代体系)。"""
    total = sum(_LETTER_CHALDEAN.get(ch.upper(), 0) for ch in name if ch.isalpha())
    destiny = _reduce(total)
    return {
        "system": "Chaldean",
        "name": name,
        "sum": total,
        "destiny": destiny,
    }


def _wuge_chinese(surname: str, given_name: str) -> dict:
    """中文三才五格 (康熙字典笔画)。"""
    return compute_wuge(surname, given_name)


def _meaning(n: int) -> str:
    """数字含义。"""
    meanings = {
        1: "独立·领导",
        2: "合作·敏感",
        3: "表达·创造",
        4: "务实·秩序",
        5: "自由·变化",
        6: "责任·关爱",
        7: "内省·智慧",
        8: "权力·财富",
        9: "博爱·完成",
        11: "灵性·直觉(大师数)",
        22: "实干理想(大师数)",
        33: "大爱导师(大师数)",
    }
    return meanings.get(n, "未知")


def _wuxing_from_name(wuge_result: dict) -> dict:
    """从三才五格中提取五行分布。"""
    return {
        "tiange": wuge_result["tiange"]["wuxing"],
        "renge": wuge_result["renge"]["wuxing"],
        "dige": wuge_result["dige"]["wuxing"],
    }


# ══════════════════════════════════════════════════════════════
# 主 compute 函数
# ══════════════════════════════════════════════════════════════
def compute(b: Birth, name: str | None = None, surname: str | None = None,
            given_name: str | None = None, system: str = "pythagoras") -> ChartResult:
    """数字命理综合引擎主函数。

    Args:
        b: 生辰
        name: 西方姓名 (用于毕达哥拉斯命运数)
        surname: 中文姓氏 (用于三才五格)
        given_name: 中文名字 (用于三才五格)
        system: "pythagoras" | "chaldean"

    Returns:
        ChartResult 含:
            - life_path: 生命灵数 (必填)
            - destiny: 命运数 (如有 name)
            - wuge: 三才五格 (如有 surname + given_name)
            - system_info: 所用体系
            - 综合解读
    """
    birth_str = f"{b.year:04d}{b.month:02d}{b.day:02d}"
    lp = _life_path_pythagorean(birth_str)
    life = lp.get("life_path")

    raw: dict[str, Any] = {
        "system_info": {
            "western": system,
            "chinese": "三才五格" if (surname and given_name) else None,
        },
        "life_path": {
            "number": life,
            "meaning": _meaning(life),
            "is_master": life in (11, 22, 33),
            "calculation_basis": "毕达哥拉斯生辰数字求和归约",
        },
        "elements": {
            "五行": {},  # 由各模块填
        },
        "timeline": [],
    }

    # 元素分布 (简化)
    if life:
        raw["elements"]["生命灵数五行"] = num_to_wuxing(life)
        raw["elements"]["水"] = 0.2 if life in (1, 6) else 0.05
        raw["elements"]["火"] = 0.2 if life in (3, 9) else 0.05
        raw["elements"]["木"] = 0.2 if life in (4, 8) else 0.05
        raw["elements"]["土"] = 0.2 if life in (5, 11) else 0.05
        raw["elements"]["金"] = 0.2 if life in (2, 7) else 0.05

    # 命运数 (西方姓名)
    if name:
        if system == "chaldean":
            dest = _destiny_chaldean(name)
        else:
            dest = _destiny_pythagorean(name)
        raw["destiny"] = {
            "number": dest.get("destiny"),
            "meaning": _meaning(dest.get("destiny", 0)),
            "calculation_basis": f"{dest['system']} 姓名字母映射求和归约",
            "raw_sum": dest.get("sum"),
            "is_master": dest.get("is_master", False),
        }

    # 三才五格 (中文姓名)
    if surname and given_name:
        wuge = _wuge_chinese(surname, given_name)
        raw["wuge"] = wuge
        raw["elements"]["天格五行"] = wuge["tiange"]["wuxing"]
        raw["elements"]["人格五行"] = wuge["renge"]["wuxing"]
        raw["elements"]["地格五行"] = wuge["dige"]["wuxing"]
        raw["综合判断"] = wuge["overall"]
        raw["三才关系"] = wuge["san_cai"]

    # 综合解读
    parts = []
    if life:
        parts.append(f"生命灵数 {life} ({_meaning(life)})")
    if "destiny" in raw:
        parts.append(f"命运数 {raw['destiny']['number']} ({raw['destiny']['meaning']})")
    if "wuge" in raw:
        parts.append(
            f"三才五格：{raw['wuge']['tiange']['wuxing']}/"
            f"{raw['wuge']['renge']['wuxing']}/"
            f"{raw['wuge']['dige']['wuxing']} — {raw['wuge']['overall']}"
        )
    raw["综合解读"] = " · ".join(parts) if parts else "无数据"

    # evidence_sources
    raw["evidence_sources"] = ["《姓名学大辞典》", "《康熙字典》", "Pythagorean Numerology"]

    return ChartResult(
        method="numerology", school="hybrid", engine="self(pythagorean+xingming)",
        normalized=raw.pop("elements", {}),
        raw=raw,
    )
