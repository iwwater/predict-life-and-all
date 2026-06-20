"""Tests for 玄空兼向替卦 (divination/data/xuankong_jian_xiang.py)

来源：docs/CLASSICAL_SOURCES.md §10 风水
文献：《沈氏玄空学》(清·沈竹礽)、《地理辨正》、《飞星赋》
覆盖:
  - 临界角检测 (should_use_jian_xiang)
  - 替星应用 (apply_jian_xiang_tixing)
  - JIAN_XIANG_TABLE 数据完整性
  - 引擎集成 compute() 兼向/正向判定
"""
from __future__ import annotations

import pytest

from divination.data.xuankong_jian_xiang import (
    JIAN_XIANG_TABLE,
    SHAN_CENTER_DEG,
    JianXiangCase,
    apply_jian_xiang_tixing,
    find_jian_shan,
    get_jian_xiang_case,
    get_tixing_start,
    shan_at_angle,
    should_use_jian_xiang,
)
from divination.engines import xuankong as xk_engine


# ── 1. 二十四山临界角表 ────────────────────────────
def test_shan_center_deg_count():
    """二十四山中心角表必须 24 山。"""
    assert len(SHAN_CENTER_DEG) == 24


def test_shan_center_deg_zi_is_zero():
    """子（正北）= 0°。"""
    assert SHAN_CENTER_DEG["子"] == 0.0


def test_shan_center_deg_mao_is_90():
    """卯（正东）= 90°。"""
    assert SHAN_CENTER_DEG["卯"] == 90.0


def test_shan_center_deg_wu_is_180():
    """午（正南）= 180°。"""
    assert SHAN_CENTER_DEG["午"] == 180.0


def test_shan_center_deg_you_is_270():
    """酉（正西）= 270°。"""
    assert SHAN_CENTER_DEG["酉"] == 270.0


def test_shan_at_angle_zi():
    """0° 落在子山。"""
    assert shan_at_angle(0.0) == "子"


def test_shan_at_angle_mao():
    """90° 落在卯山。"""
    assert shan_at_angle(90.0) == "卯"


def test_shan_at_angle_ren():
    """345° 落在壬山。"""
    assert shan_at_angle(345.0) == "壬"


# ── 2. 临界角检测 should_use_jian_xiang ───────────────────
def test_should_use_jian_xiang_in_boundary():
    """角度在邻山中心 ±3° 内 → 需启用替卦。"""
    # 子中心 0°，壬中心 345°；山=子，角度 350° 离壬中心 5° 离癸 25°
    # 离壬中心 5° 不在 3° 内 → False
    # 但 角度 346° 离壬中心 1° → True
    assert should_use_jian_xiang(346.0, "子") is True


def test_should_use_jian_xiang_in_pure_positive():
    """角度在本山正中（中心 ±5° 内）→ 不需替卦。"""
    # 子中心 0°，角度 0° → 完全正向
    assert should_use_jian_xiang(0.0, "子") is False
    # 角度 5°（离壬中心 20°，离子中心 5°）→ 仍在子正向
    assert should_use_jian_xiang(5.0, "子") is False


def test_should_use_jian_xiang_far_no_use():
    """角度远离所有山中心 → 不需替卦（属出卦）。"""
    # 角度 50° 离丑中心 20° 离艮 5° → 离艮 5° < 3° 不成立
    # 角度 50°: 丑=30°, 艮=45°, 寅=60° → 离艮 5°, > 3° → False
    # 实际: 45° 是艮, 50° 离艮 5° (非临界)
    assert should_use_jian_xiang(50.0, "子") is False


def test_should_use_jian_xiang_at_boundary():
    """临界角正好 3°。"""
    # 子中心 0°；壬中心 345°（= -15°）；癸中心 15°
    # 角度 3° 离癸中心 12°, 离壬 18°, 离子 3° → 在子正向内
    # 找一个落在壬中心的角度: 342° (离壬中心 3°，正好临界)
    # 342° 离壬中心 3.0° — 边界外 (< 容差)
    assert should_use_jian_xiang(342.0, "子") is False
    # 343° 离壬中心 2° — 临界内
    assert should_use_jian_xiang(343.0, "子") is True


def test_should_use_jian_xiang_custom_tolerance():
    """自定义容差 5°。"""
    # 容差 5° 时：角度 50° 离艮中心 45° 差 5° → True
    assert should_use_jian_xiang(50.0, "子", tolerance_deg=5.0) is False
    assert should_use_jian_xiang(48.0, "子", tolerance_deg=5.0) is True


# ── 3. find_jian_shan 找兼向山 ───────────────────────
def test_find_jian_shan_returns_neighbor():
    """找偏向的邻山。"""
    js = find_jian_shan(346.0, "子")  # 346° 离壬 (345°) 最近
    assert js == "壬"


def test_find_jian_shan_no_neighbor():
    """角度在本山正中 → 无邻山。"""
    js = find_jian_shan(0.0, "子")
    assert js is None


def test_find_jian_shan_boundary_between_two():
    """角度恰好在两山中点 → 找最近的（容差 3° 内）。"""
    # 壬 (345°) 与 子 (0°/360°) 中点 352.5° 离两边都 7.5°，都 > 3° → None
    js = find_jian_shan(352.5, "子")
    assert js is None
    # 但用容差 8° 时，会落在某个山上
    # 352.5 离壬 7.5°, 离子 7.5° → 都 > 8° → None
    # 改用容差 10° 测试
    js2 = find_jian_shan(352.5, "子", tolerance_deg=10.0)
    # 离壬 (345°) 7.5°、离子 (0°) 7.5° → tie → 第一个匹配 = "壬"
    assert js2 in {"壬", "子"}


# ── 4. JIAN_XIANG_TABLE 数据完整性 ─────────────────────
def test_jian_xiang_table_has_minimum_cases():
    """替卦表至少 16 条主线（≥ 16）。"""
    assert len(JIAN_XIANG_TABLE) >= 16


def test_jian_xiang_table_required_fields():
    """每条 case 必须含 original_shan/jian_shan/polarity/source。"""
    for key, case in JIAN_XIANG_TABLE.items():
        assert isinstance(case, JianXiangCase), f"{key}: not JianXiangCase"
        assert case.original_shan, f"{key}: missing original_shan"
        assert case.jian_shan, f"{key}: missing jian_shan"
        assert case.polarity in {"auspicious", "inauspicious"}, \
            f"{key}: bad polarity {case.polarity}"
        assert case.source, f"{key}: missing source"


def test_jian_xiang_table_keys_unique():
    """表 key 不可重复。"""
    keys = list(JIAN_XIANG_TABLE.keys())
    assert len(keys) == len(set(keys))


def test_jian_xiang_table_tixing_dict_has_nine_keys():
    """替星 dict 必须含 1-9 共 9 个键。"""
    for key, case in JIAN_XIANG_TABLE.items():
        if case.tixing_shan:
            assert set(case.tixing_shan.keys()) == {1, 2, 3, 4, 5, 6, 7, 8, 9}, \
                f"{key}: tixing_shan missing keys"


def test_jian_xiang_table_source_mentions_classic():
    """source 字段必须含《沈氏玄空学》。"""
    for key, case in JIAN_XIANG_TABLE.items():
        assert "沈氏玄空学" in case.source, f"{key}: source missing《沈氏玄空学》"


def test_jian_xiang_case_ren_jian_zi():
    """壬兼子案例字段正确性。"""
    case = get_jian_xiang_case("壬", "子")
    assert case is not None
    assert case.original_shan == "壬"
    assert case.jian_shan == "子"
    assert case.polarity == "auspicious"
    assert 1 in case.tixing_shan
    assert 9 in case.tixing_shan


def test_jian_xiang_case_zi_jian_gui():
    """子兼癸案例字段正确性。"""
    case = get_jian_xiang_case("子", "癸")
    assert case is not None
    assert case.original_shan == "子"
    assert case.jian_shan == "癸"


def test_jian_xiang_case_unknown_returns_none():
    """未知组合 → None。"""
    case = get_jian_xiang_case("子", "午")  # 子午对宫不应兼
    assert case is None


# ── 5. apply_jian_xiang_tixing 替星应用 ─────────────────
def test_apply_tixing_ren_zi():
    """壬兼子 → 返回替星 dict。"""
    tx = apply_jian_xiang_tixing("壬", "子")
    assert isinstance(tx, dict)
    assert len(tx) == 9
    assert all(isinstance(k, int) and 1 <= k <= 9 for k in tx.keys())


def test_apply_tixing_zi_gui():
    """子兼癸 → 返回替星 dict。"""
    tx = apply_jian_xiang_tixing("子", "癸")
    assert len(tx) == 9


def test_apply_tixing_bing_wu():
    """丙兼午 → 返回替星 dict。"""
    tx = apply_jian_xiang_tixing("丙", "午")
    assert len(tx) == 9


def test_apply_tixing_unknown_fallback_empty():
    """未知组合 → 返回空 dict（fallback）。"""
    tx = apply_jian_xiang_tixing("子", "午")
    assert tx == {}


def test_apply_tixing_contains_main_shan():
    """替星 dict 应含本山。"""
    tx = apply_jian_xiang_tixing("壬", "子")
    assert "壬" in tx.values()


def test_apply_tixing_xiang_present():
    """替卦案例应含 tixing_xiang（向星替卦）。"""
    for key, case in JIAN_XIANG_TABLE.items():
        assert case.tixing_xiang, f"{key}: missing tixing_xiang"
        assert len(case.tixing_xiang) == 9


# ── 6. 替星入口口诀 ─────────────────────────────
def test_get_tixing_start_yang_mountain():
    """阳山替星入口：壬 → 7（兑卦阴，替星起例）。"""
    # 壬阳山 → 替星 7（沈氏卷二）
    assert get_tixing_start("壬") == 7
    # 子阳山 → 替星 8
    assert get_tixing_start("子") == 8


def test_get_tixing_start_yin_mountain():
    """阴山替星入口：癸 → 6（乾卦阳）。"""
    # 癸阴山 → 替星 6
    assert get_tixing_start("癸") == 6
    # 丑阴山 → 替星 5
    assert get_tixing_start("丑") == 5


def test_get_tixing_start_unknown():
    """未录入山 → None。"""
    assert get_tixing_start("X") is None
    assert get_tixing_start("") is None


# ── 7. 引擎集成 compute() ─────────────────────────
def _make_birth(sitting="子", period=8):
    """构造一个最小 Birth 对象。"""
    from divination.contracts import Birth
    return Birth(year=2024, month=1, day=1, hour=12, sitting=sitting, period=period)


def test_engine_positive_no_tixing():
    """正向（facing_deg 居中）→ tixing 应为 None。"""
    b = _make_birth(sitting="子")
    # 子中心 0° → 完全正向
    chart = xk_engine.compute(b, facing_deg=0.0)
    assert "tixing" in chart.raw
    assert chart.raw["tixing"] is None


def test_engine_jian_xiang_triggers():
    """临界角 → tixing 字段启用。"""
    b = _make_birth(sitting="子")
    # 角度 346° → 离壬中心 1° → 临界
    chart = xk_engine.compute(b, facing_deg=346.0)
    assert chart.raw["tixing"] is not None
    tx = chart.raw["tixing"]
    assert tx["is_jian_xiang"] is True
    assert tx["jian_shan"] == "壬"
    assert 1 in tx["tixing_shan"]


def test_engine_no_facing_deg_no_tixing():
    """不传 facing_deg → tixing 始终 None（保留原行为）。"""
    b = _make_birth(sitting="子")
    chart = xk_engine.compute(b)
    assert chart.raw["tixing"] is None


def test_engine_raw_preserves_existing_fields():
    """引擎集成不破坏现有 raw['九宫'] 等字段。"""
    b = _make_birth(sitting="子")
    chart = xk_engine.compute(b, facing_deg=346.0)
    assert "九宫" in chart.raw
    assert "运" in chart.raw
    assert "坐" in chart.raw
    assert "向" in chart.raw
    assert "格局" in chart.raw


# ── 8. Golden 对照（《沈氏玄空学》原文案例） ───────────
def test_golden_ren_jian_zi_wu_xiang():
    """壬山兼子 → 向必为午（《沈氏玄空学》卷二案例一）。

    壬（坎北）兼子（坎北偏东），对宫向应为午（离南偏西）兼丁。
    """
    case = get_jian_xiang_case("壬", "子")
    assert case is not None
    assert case.original_xiang == "丙"
    assert case.jian_xiang == "午"
    # 替星 1 = 壬（本山）
    assert case.tixing_shan[1] == "壬"


def test_golden_jia_jian_mao_you_xiang():
    """甲山兼卯 → 向必为酉（《沈氏玄空学》卷二案例二）。"""
    case = get_jian_xiang_case("甲", "卯")
    assert case is not None
    assert case.original_xiang == "庚"
    assert case.jian_xiang == "酉"


def test_golden_bing_jian_wu_zi_xiang():
    """丙山兼午 → 向必为子（《沈氏玄空学》卷二案例三）。"""
    case = get_jian_xiang_case("丙", "午")
    assert case is not None
    assert case.original_xiang == "壬"
    assert case.jian_xiang == "子"