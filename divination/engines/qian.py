"""观音灵签 / 关帝灵签。

签谱来自 `divination.data.reference_equipment` 的公开资料库。当前 1-25 为
手工条目，26-100 为基础补全条目；engine 在输出中显式标注资料等级，不把
基础条目伪装成精校古籍。
"""
from __future__ import annotations

import random
import secrets
from typing import Any

from ..contracts import Birth, ChartResult
from ..data.reference_equipment import GUANDI_QIAN, GUANYIN_QIAN, QianDraw

QIAN_TYPES = {
    "guanyin": ("观音灵签", GUANYIN_QIAN),
    "guandi": ("关帝灵签", GUANDI_QIAN),
}

QIAN_TYPE_ALIASES = {
    "观音": "guanyin",
    "观音灵签": "guanyin",
    "guanyin": "guanyin",
    "guandi": "guandi",
    "关帝": "guandi",
    "关帝灵签": "guandi",
}

CATEGORY_ADVICE = {
    "上上": "可顺势推进，但仍需把关键承诺落到书面与行动。",
    "上": "整体偏顺，适合稳扎稳打，不宜贪快。",
    "中": "吉凶未定，重点在补条件、看时机、少冒进。",
    "下": "阻力较多，宜先止损、复盘、缓一步再动。",
    "下下": "警示较重，建议暂停重大动作，先求安全边界。",
}


def _resolve_type(value: str | None) -> str:
    if not value:
        return "guanyin"
    return QIAN_TYPE_ALIASES.get(str(value).strip().lower(), "guanyin")


def _draw_index(seed: Any | None, max_index: int = 100) -> tuple[int, str]:
    if seed is not None and seed != "":
        return random.Random(str(seed)).randint(1, max_index), "seeded"
    return secrets.randbelow(max_index) + 1, "cryptographic"


def _get_entry(qian_list: list[QianDraw], index: int) -> QianDraw:
    index = max(1, min(100, int(index)))
    return qian_list[index - 1]


def _public_entry(entry: QianDraw) -> dict[str, Any]:
    is_base = "待校订" in entry.short_verse or "待校订" in entry.interpretation
    verse = entry.short_verse
    if is_base:
        verse = f"{entry.name}：{entry.category}签。基础条目，宜结合问题背景审慎参看。"
    return {
        "index": entry.index,
        "name": entry.name,
        "category": entry.category,
        "short_verse": verse,
        "interpretation": entry.interpretation,
        "advice": CATEGORY_ADVICE.get(entry.category, "仅供文化参考，重大事项请结合现实条件判断。"),
        "source_quality": "base_catalog" if is_base else "curated",
    }


def compute(b: Birth, qian_type: str | None = None, qian_number: int | None = None,
            seed: Any | None = None, question: str | None = None) -> ChartResult:
    qtype = _resolve_type(getattr(b, "qian_type", None) or qian_type)
    type_name, qian_list = QIAN_TYPES[qtype]
    seed = getattr(b, "seed", None) if getattr(b, "seed", None) is not None else seed
    question = getattr(b, "question", None) or question
    raw_number = getattr(b, "qian_number", None) or qian_number
    if raw_number:
        index, draw_mode = max(1, min(100, int(raw_number))), "manual"
    else:
        index, draw_mode = _draw_index(seed)
    entry = _get_entry(qian_list, index)
    public = _public_entry(entry)

    return ChartResult(
        method="qian",
        school="east",
        engine="self+public-qian-catalog",
        normalized={
            "elements": {},
            "timeline": [],
            "polarity": public["category"],
            "source_quality": public["source_quality"],
        },
        raw={
            "签谱": qtype,
            "签谱名称": type_name,
            "签号": public["index"],
            "签名": public["name"],
            "签等": public["category"],
            "签文": public["short_verse"],
            "解签": public["interpretation"],
            "行动建议": public["advice"],
            "问题": question,
            "draw_mode": draw_mode,
            "seed_used": seed,
            "source_quality": public["source_quality"],
            "calculation_basis": {
                "method": "qian",
                "mode": "manual" if draw_mode == "manual" else "random_draw",
                "rule": "指定签号或 1-100 不放回外的单次抽签",
                "limits": [
                    "灵签输出仅供传统文化参考",
                    "26-100 号为基础资料库条目，未声明为古籍精校全文",
                ],
            },
        },
    )
