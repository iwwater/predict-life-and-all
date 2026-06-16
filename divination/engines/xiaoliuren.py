"""Xiao Liu Ren palm divination.

This engine supports the two entry points exposed by the UI:
- time_xiaoliuren: lunar month, lunar day, and Chinese hour branch.
- number_xiaoliuren: three arbitrary numbers.
"""

from __future__ import annotations

import hashlib
from typing import Any

from ..contracts import Birth, ChartResult

PALACES = [
    {
        "name": "大安",
        "tone": "auspicious",
        "keywords": ["steady", "safe", "settled"],
        "meaning": "事情以稳为主，宜守成、等待、按原计划推进。",
    },
    {
        "name": "留连",
        "tone": "delayed",
        "keywords": ["delay", "stuck", "waiting"],
        "meaning": "事情有拖延、反复、牵连之象，宜先理清关系和流程。",
    },
    {
        "name": "速喜",
        "tone": "auspicious",
        "keywords": ["quick news", "joy", "response"],
        "meaning": "消息来得快，有喜讯或转机，适合主动沟通、快速推进。",
    },
    {
        "name": "赤口",
        "tone": "conflict",
        "keywords": ["argument", "friction", "injury"],
        "meaning": "易有口舌、误会、冲突，凡事先降火，避免硬碰硬。",
    },
    {
        "name": "小吉",
        "tone": "minor luck",
        "keywords": ["help", "small gain", "smooth"],
        "meaning": "小有顺遂，有人相助或局部好转，适合小步试探。",
    },
    {
        "name": "空亡",
        "tone": "void",
        "keywords": ["empty", "uncertain", "not ripe"],
        "meaning": "眼下信息不足或时机未到，不宜重押，先补证据。",
    },
]

HOUR_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _hour_branch_index(hour: int) -> int:
    return ((hour + 1) // 2) % 12


def _parse_numbers(value: Any) -> list[int]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            try:
                out.append(int(item))
            except (TypeError, ValueError):
                pass
        return out[:3]
    text = str(value)
    parts = []
    current = ""
    for ch in text:
        if ch.isdigit():
            current += ch
        elif current:
            parts.append(int(current))
            current = ""
    if current:
        parts.append(int(current))
    return parts[:3]


def _numbers_from_seed(seed: Any) -> list[int]:
    """推导 number_xiaoliuren 三个数字。

    方案 §十一 'AI 不参与随机':
    - 优先用用户输入的 seed 派生
    - 用户给了部分数字(1-2 个)就用 seed 派生补足
    - 没有任何输入时返回明确错误, 不静默用当天日期
    """
    nums = _parse_numbers(seed)
    if len(nums) >= 3:
        return nums[:3]

    seed_str = str(seed or "").strip()
    if not seed_str:
        raise ValueError(
            "number_xiaoliuren 需要 seed (如 1,2,3 或问题文本), "
            "不可静默用当天日期降级 (方案 §十一)。"
        )

    # 用 hashlib 确定性派生 3 个 1-99 的数字
    digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
    while len(nums) < 3:
        # 每 4 字节转 int, 再 mod 99 + 1
        idx = len(nums) * 4
        chunk = digest[idx:idx + 4]
        if len(chunk) < 4:
            chunk = hashlib.sha256(chunk).digest()[:4]
        n = int.from_bytes(chunk, "big") % 99 + 1
        nums.append(n)
    return nums[:3]


def _time_index(month: int, day: int, hour: int) -> tuple[int, dict[str, Any]]:
    hour_idx = _hour_branch_index(hour)
    index = (max(1, month) - 1 + max(1, day) - 1 + hour_idx) % 6
    return index, {
        "month": month,
        "day": day,
        "hour": hour,
        "hour_branch": HOUR_BRANCHES[hour_idx],
        "hour_branch_index": hour_idx + 1,
        "formula": "(lunar_month - 1 + lunar_day - 1 + hour_branch_index_zero_based) % 6",
    }


def _number_index(seed: Any) -> tuple[int, dict[str, Any]]:
    nums = _numbers_from_seed(seed)
    index = (nums[0] - 1 + nums[1] - 1 + nums[2] - 1) % 6
    return index, {
        "numbers": nums,
        "formula": "(n1 - 1 + n2 - 1 + n3 - 1) % 6",
    }


def compute(b: Birth) -> ChartResult:
    mode = getattr(b, "mode", None) or "time_xiaoliuren"
    question = getattr(b, "question", "") or ""

    if mode == "number_xiaoliuren":
        index, basis_input = _number_index(getattr(b, "seed", None))
    else:
        mode = "time_xiaoliuren"
        index, basis_input = _time_index(b.month, b.day, b.hour)

    palace = PALACES[index]
    raw = {
        "mode": mode,
        "subject": getattr(b, "subject", None) or "decision",
        "question": question,
        "result_index": index + 1,
        "palace": palace["name"],
        "tone": palace["tone"],
        "keywords": palace["keywords"],
        "meaning": palace["meaning"],
        "six_palaces": PALACES,
        "rule_version": "v1",
        "calculation_basis": {
            "method": "xiaoliuren",
            "mode": mode,
            "rule_version": "v1",
            "input_source": "time_xiaoliuren uses lunar month/day/hour; number_xiaoliuren uses three numbers or deterministic seed.",
            "input": basis_input,
            "limits": [
                "小六壬适合即时决疑和短期事项，不替代八字、紫微等长期命盘。",
                "不同传承对月日时起数细节略有差异，本版本采用月日时顺推六宫。",
            ],
        },
    }

    return ChartResult(
        method="xiaoliuren",
        school="east",
        engine="self+xiaoliuren-palm",
        normalized={"elements": {}, "timeline": []},
        raw=raw,
    )
