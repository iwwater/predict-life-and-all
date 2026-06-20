"""Xiao Liu Ren palm divination.

This engine supports the two entry points exposed by the UI:
- time_xiaoliuren: lunar month, lunar day, and Chinese hour branch.
- number_xiaoliuren: three arbitrary numbers.
"""

from __future__ import annotations

import hashlib
from typing import Any

from ..contracts import Birth, ChartResult
from ..data.xiaoliuren_ke_jing import evaluate_number_rules, get_number_wuxing, NUMBER_KE_RULES

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


def _interpret_multi_numbers(nums: list[int], question: str = "") -> dict:
    """对多数字进行数字课经评估, 含问题意图联动.

    意图联动 (intent 关键词):
      - 时间/日期关键词 → 加权时间类规则 (顺数/逆数) 在 summary 中
      - 感情/关系关键词 → 加权和谐类规则 (两奇一偶/三才分布) 在 summary 中
      - 事业/财运关键词 → 加权格局类规则 (全大数/全小数/五行属性) 在 summary 中

    Args:
        nums: 三个数字列表.
        question: 用户问题文本 (可选).

    Returns:
        {
            "numbers": list[int],
            "number_rules_matched": list[dict],
            "wuxing_distribution": dict,
            "intent_context": str,
            "summary": str,
        }
    """
    matched_rules = evaluate_number_rules(nums)
    wuxing_dist = get_number_wuxing(nums)

    # ── intent linkage ──
    intent_context = ""
    summary_parts: list[str] = []
    q = question.lower() if question else ""

    # 分类关键词
    time_keywords = [
        "时间", "时候", "几月", "哪天", "何时", "多久", "时机", "日期",
        "年", "月", "日", "今年", "明年", "when", "time",
    ]
    relationship_keywords = [
        "感情", "恋爱", "爱情", "婚姻", "结婚", "分手", "复合", "对象",
        "另一半", "桃花", "姻缘", "喜欢", "关系", "情侣", "夫妻",
        "love", "relationship", "marriage",
    ]
    career_wealth_keywords = [
        "工作", "事业", "职业", "跳槽", "升职", "创业", "财运", "赚钱",
        "投资", "生意", "财富", "收入", "老板", "公司", "求职",
        "career", "job", "money", "wealth", "business",
    ]

    # 检测问题意图
    has_time = any(kw in q for kw in time_keywords)
    has_relationship = any(kw in q for kw in relationship_keywords)
    has_career_wealth = any(kw in q for kw in career_wealth_keywords)

    # 按规则分类 grouping
    temporal_rules = [
        r for r in matched_rules
        if r["rule_id"] in ("shunshu", "nishu", "sanshu_xiangtong")
    ]
    harmony_rules = [
        r for r in matched_rules
        if r["rule_id"] in ("liangqiyiou", "dazhongxiao", "sanqi", "sanou")
    ]
    fortune_rules = [
        r for r in matched_rules
        if r["rule_id"] in ("quandashu", "quanxiaoshu", "sanmu", "sanhuo", "sanjin", "sanshui")
    ]
    special_rules = [
        r for r in matched_rules
        if r["rule_id"] in ("han7", "han9")
    ]

    # Build intent context and weighted summary
    if has_time:
        intent_context = f"问题涉及时间/时机 (关键词命中: temporal), "
        if temporal_rules:
            summary_parts.append("三传数字模式显示时序走向: " + "; ".join(
                f"{r['name']}: {r['interpretation'][:40]}" for r in temporal_rules
            ))
        if special_rules:
            summary_parts.append("特殊数变数提示: " + "; ".join(
                f"{r['name']}: {r['advice']}" for r in special_rules
            ))
    elif has_relationship:
        intent_context = f"问题涉及感情/关系 (关键词命中: relationship), "
        if harmony_rules:
            summary_parts.append("阴阳和谐课式显示关系走向: " + "; ".join(
                f"{r['name']}: {r['interpretation'][:40]}" for r in harmony_rules
            ))
        if "sanshui" in [r["rule_id"] for r in matched_rules]:
            summary_parts.append("三水格提示情感多虑, 宜减少猜疑、加强沟通。")
    elif has_career_wealth:
        intent_context = f"问题涉及事业/财运 (关键词命中: career/wealth), "
        if fortune_rules:
            summary_parts.append("大小格局课式显示事态规模: " + "; ".join(
                f"{r['name']}: {r['interpretation'][:40]}" for r in fortune_rules
            ))
        if "sanjin" in [r["rule_id"] for r in matched_rules]:
            summary_parts.append("三金格提示事业宜多合作, 刚极易折。")
        if "sanhuo" in [r["rule_id"] for r in matched_rules]:
            summary_parts.append("三火格提示行动力旺盛, 但注意避免冲动决策。")

    # Fallback: no specific intent detected or no matched rules in target category
    if not summary_parts:
        intent_context = intent_context + "通用解读 " if intent_context else ""
        for r in matched_rules:
            summary_parts.append(f"{r['name']}: {r['interpretation'][:50]}")

    # Always include wuxing note
    summary_parts.append(
        f"五行分布: 主导{wuxing_dist['dominant_wuxing']}, "
        f"计数{wuxing_dist['wuxing_counts']}."
    )

    tone_counts = {"auspicious": 0, "inauspicious": 0, "mixed": 0, "neutral": 0}
    for r in matched_rules:
        tone_counts[r["tone"]] = tone_counts.get(r["tone"], 0) + 1
    if tone_counts["auspicious"] > tone_counts["inauspicious"]:
        tone_summary = "总体偏吉, 有利因素较多。"
    elif tone_counts["inauspicious"] > tone_counts["auspicious"]:
        tone_summary = "总体偏凶, 需谨慎行事。"
    elif tone_counts["mixed"] > 0:
        tone_summary = "吉凶参半, 需视具体情境权衡。"
    else:
        tone_summary = "中性, 事态平稳。"
    summary_parts.append(tone_summary)

    return {
        "numbers": nums,
        "number_rules_matched": matched_rules,
        "wuxing_distribution": wuxing_dist,
        "intent_context": intent_context.strip(", ") if intent_context else "无特定意图关键词命中",
        "summary": " ".join(summary_parts),
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

    # P3-3: 数字起卦深化 — 多数字课经评估 + 意图联动
    if mode == "number_xiaoliuren":
        nums = _numbers_from_seed(getattr(b, "seed", None))
        multi_interpretation = _interpret_multi_numbers(nums, question)
        raw["multi_number_interpretation"] = multi_interpretation
        raw["number_ke_rules_total"] = len(NUMBER_KE_RULES)

    return ChartResult(
        method="xiaoliuren",
        school="east",
        engine="self+xiaoliuren-palm",
        normalized={"elements": {}, "timeline": []},
        raw=raw,
    )
