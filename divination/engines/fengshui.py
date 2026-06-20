"""风水复合引擎 — 综合八宅与玄空飞星。

作为 12 术法聚合中的第 6 个术法，提供综合风水评估。
内部调用 bazhai 和 xuankong 引擎并合并结果。
"""
from __future__ import annotations

from divination.contracts import Birth, ChartResult

from . import bazhai as _bazhai, xuankong as _xuankong


def compute(birth: Birth) -> ChartResult:
    """综合风水排盘 — 八宅 + 玄空飞星。

    Args:
        birth: 出生信息（包含空间相关字段如 sitting, period 等）

    Returns:
        合并的 ChartResult
    """
    bazhai_raw: dict = {}
    xuankong_raw: dict = {}
    errors: list[str] = []

    # 八宅
    try:
        bazhai_result = _bazhai.compute(birth)
        bazhai_raw = bazhai_result.raw
    except Exception as e:
        errors.append(f"bazhai: {e}")

    # 玄空
    try:
        xuankong_result = _xuankong.compute(birth)
        xuankong_raw = xuankong_result.raw
    except Exception as e:
        errors.append(f"xuankong: {e}")

    # 合并分析
    combined: dict = {
        "bazhai": bazhai_raw,
        "xuankong": xuankong_raw,
        "errors": errors,
    }

    # 提取吉凶方综合
    ji_fang = set()
    xiong_fang = set()

    if isinstance(bazhai_raw.get("吉方"), list):
        ji_fang.update(bazhai_raw["吉方"])
    if isinstance(bazhai_raw.get("凶方"), list):
        xiong_fang.update(bazhai_raw["凶方"])

    # 从玄空提取信息
    xuankong_geju = xuankong_raw.get("格局", "")
    combined["summary"] = f"风水综合评估：命卦{bazhai_raw.get('命卦', 'N/A')}，玄空格局{xuankong_geju or '待定'}"
    combined["吉方"] = sorted(ji_fang) if ji_fang else []
    combined["凶方"] = sorted(xiong_fang) if xiong_fang else []
    combined["玄空格局"] = xuankong_geju
    combined["八宅命卦"] = bazhai_raw.get("命卦", "")

    return ChartResult(
        method="fengshui",
        school="east",
        engine="fengshui_composite",
        normalized={},
        raw=combined,
    )
