"""Tests for 奇门遁甲 多盘种深化 (Phase J).

覆盖:
  - pan_type: hour/day/month/year 四种
  - pan_style: turn/fly (转盘 / 飞盘)
  - zhi_run_method: chaibu/maoshan (拆补 / 茅山)
  - 默认参数 = 时家 + 转盘 + 拆补
  - 飞盘九星原位 (九星不带八门)
  - 茅山法按自然三元
  - 月家/日家/年家 走 fallback 模拟
  - 错误参数 -> ValueError
  - 与现有 72 局定局表兼容 (排局字段不变)
  - 完整 4×2×2 = 16 组合 smoke test (核心 12)
"""
from __future__ import annotations

import inspect

import pytest

from divination.contracts import Birth, ChartResult
from divination.engines import qimen
from divination.engines.qimen import (
    _PAN_TYPE_LABELS,
    _PAN_STYLE_LABELS,
    _ZHI_RUN_LABELS,
    _simulate_multi_pan,
)


# ══════════════════════════════════════════════════════════════
# 1. 常量与标签完整性
# ══════════════════════════════════════════════════════════════
def test_pan_type_labels_complete():
    """pan_type 标签覆盖 4 种."""
    assert set(_PAN_TYPE_LABELS.keys()) == {"hour", "day", "month", "year"}
    assert _PAN_TYPE_LABELS["hour"] == "时家奇门"
    assert _PAN_TYPE_LABELS["day"] == "日家奇门"
    assert _PAN_TYPE_LABELS["month"] == "月家奇门"
    assert _PAN_TYPE_LABELS["year"] == "年家奇门"


def test_pan_style_labels_complete():
    """pan_style 标签覆盖 2 种."""
    assert set(_PAN_STYLE_LABELS.keys()) == {"turn", "fly"}
    assert _PAN_STYLE_LABELS["turn"] == "转盘"
    assert _PAN_STYLE_LABELS["fly"] == "飞盘"


def test_zhi_run_labels_complete():
    """zhi_run_method 标签覆盖 2 种."""
    assert set(_ZHI_RUN_LABELS.keys()) == {"chaibu", "maoshan"}
    assert _ZHI_RUN_LABELS["chaibu"] == "拆补法"
    assert _ZHI_RUN_LABELS["maoshan"] == "茅山法"


# ══════════════════════════════════════════════════════════════
# 2. 默认参数向后兼容
# ══════════════════════════════════════════════════════════════
def test_default_params_match_signature():
    """compute 默认参数 = hour/turn/chaibu."""
    sig = inspect.signature(qimen.compute)
    assert sig.parameters["pan_type"].default == "hour"
    assert sig.parameters["pan_style"].default == "turn"
    assert sig.parameters["zhi_run_method"].default == "chaibu"


def test_default_engine_contains_hour_turn_chaibu():
    """默认调用 -> engine 含 hour-turn-chaibu."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0))
    assert "hour" in r.engine
    assert "turn" in r.engine
    assert "chaibu" in r.engine


def test_default_pan_info_present():
    """默认调用 -> raw['pan_info'] 含 pan_type/pan_style/zhi_run_method."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0))
    pi = r.raw["pan_info"]
    assert pi["pan_type"] == "hour"
    assert pi["pan_style"] == "turn"
    assert pi["zhi_run_method"] == "chaibu"


def test_default_preserves_existing_fields():
    """默认调用保留原 72 局定局字段 (向后兼容)."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0))
    for k in ["节气", "排局", "局数", "三元", "遁", "evidence_sources", "断"]:
        assert k in r.raw, f"missing {k}"


# ══════════════════════════════════════════════════════════════
# 3. pan_type 四种盘种
# ══════════════════════════════════════════════════════════════
def test_pan_type_day():
    """日家奇门."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="day")
    assert r.raw["pan_info"]["pan_type"] == "day"
    assert r.raw["pan_info"]["pan_type_label"] == "日家奇门"
    assert r.raw["pan_info"]["ganzhi_basis"] == "日干支"
    assert "day" in r.engine


def test_pan_type_month():
    """月家奇门."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="month")
    assert r.raw["pan_info"]["pan_type"] == "month"
    assert r.raw["pan_info"]["pan_type_label"] == "月家奇门"
    assert r.raw["pan_info"]["ganzhi_basis"] == "月干支"
    assert "month" in r.engine
    # 月家三元范围
    msr = r.raw["pan_info"].get("month_sanyuan_ranges", {})
    assert msr["上元"] == (1, 10)
    assert msr["中元"] == (11, 20)
    assert msr["下元"] == (21, 30)


def test_pan_type_year():
    """年家奇门."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="year")
    assert r.raw["pan_info"]["pan_type"] == "year"
    assert r.raw["pan_info"]["pan_type_label"] == "年家奇门"
    assert r.raw["pan_info"]["ganzhi_basis"] == "年干支"
    assert r.raw["pan_info"].get("year_sanyuan_basis")
    assert "year" in r.engine


def test_pan_type_hour_explicit():
    """显式时家奇门."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="hour")
    assert r.raw["pan_info"]["pan_type"] == "hour"
    assert r.raw["pan_info"]["ganzhi_basis"] == "时干支"


# ══════════════════════════════════════════════════════════════
# 4. pan_style 转盘 / 飞盘
# ══════════════════════════════════════════════════════════════
def test_pan_style_turn_default():
    """转盘: 默认, 无 fly_pan 字段."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_style="turn")
    assert r.raw["pan_info"]["pan_style"] == "turn"
    assert r.raw["pan_info"]["pan_style_label"] == "转盘"
    assert "fly_pan" not in r.raw["pan_info"]


def test_pan_style_fly():
    """飞盘: 九星原位, 不带八门."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_style="fly")
    assert r.raw["pan_info"]["pan_style"] == "fly"
    assert r.raw["pan_info"]["pan_style_label"] == "飞盘"
    fly = r.raw["pan_info"]["fly_pan"]
    # 九星原位 9 宫
    assert fly["九星原位"]["坎"] == "天蓬"
    assert fly["九星原位"]["中"] == "天禽"
    assert len(fly["九星原位"]) == 9


# ══════════════════════════════════════════════════════════════
# 5. zhi_run_method 拆补 / 茅山
# ══════════════════════════════════════════════════════════════
def test_zhi_run_chaibu_default():
    """拆补法: 默认."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), zhi_run_method="chaibu")
    assert r.raw["pan_info"]["zhi_run_method"] == "chaibu"
    assert r.raw["pan_info"]["zhi_run_label"] == "拆补法"
    assert "maoshan_sanyuan" not in r.raw["pan_info"]


def test_zhi_run_maoshan_upper_sanyuan():
    """茅山法: 节内 1-5 日 = 上元."""
    r = qimen.compute(Birth(2024, 6, 22, 14, 30, 0), zhi_run_method="maoshan")
    assert r.raw["pan_info"]["zhi_run_method"] == "maoshan"
    assert r.raw["pan_info"]["zhi_run_label"] == "茅山法"
    # 2024-06-22 ~ 夏至(06-21) 后第 2 天 -> 上元
    assert r.raw["pan_info"]["maoshan_sanyuan"] == "上元"


def test_zhi_run_maoshan_middle_sanyuan():
    """茅山法: 节内 6-10 日 = 中元."""
    # 2024-06-26 = 夏至后第 6 天 -> 中元
    r = qimen.compute(Birth(2024, 6, 27, 14, 30, 0), zhi_run_method="maoshan")
    assert r.raw["pan_info"]["maoshan_sanyuan"] == "中元"


def test_zhi_run_maoshan_lower_sanyuan():
    """茅山法: 节内 11-15 日 = 下元."""
    # 2024-07-02 = 夏至(06-21) 后第 12 天 -> 下元
    r = qimen.compute(Birth(2024, 7, 2, 14, 30, 0), zhi_run_method="maoshan")
    assert r.raw["pan_info"]["maoshan_sanyuan"] == "下元"


# ══════════════════════════════════════════════════════════════
# 6. 参数校验
# ══════════════════════════════════════════════════════════════
def test_invalid_pan_type_raises():
    """非法 pan_type -> ValueError."""
    with pytest.raises(ValueError, match="pan_type"):
        qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="century")


def test_invalid_pan_style_raises():
    """非法 pan_style -> ValueError."""
    with pytest.raises(ValueError, match="pan_style"):
        qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_style="spin")


def test_invalid_zhi_run_raises():
    """非法 zhi_run_method -> ValueError."""
    with pytest.raises(ValueError, match="zhi_run_method"):
        qimen.compute(Birth(2024, 6, 25, 14, 30, 0), zhi_run_method="bad")


# ══════════════════════════════════════════════════════════════
# 7. _simulate_multi_pan 直接测试
# ══════════════════════════════════════════════════════════════
def test_simulate_pan_info_fields():
    """_simulate_multi_pan 返回字段完整."""
    raw = {"sanyuan_days_in_term": 5}
    info = _simulate_multi_pan(raw, "day", "turn", "chaibu")
    for k in ["pan_type", "pan_type_label", "pan_style", "pan_style_label",
              "zhi_run_method", "zhi_run_label", "fallback_simulated",
              "simulation_note", "ganzhi_basis"]:
        assert k in info


def test_simulate_fly_includes_jiuxing_yuanwei():
    """飞盘模拟含九星原位."""
    raw = {"sanyuan_days_in_term": 3}
    info = _simulate_multi_pan(raw, "hour", "fly", "chaibu")
    assert info["fly_pan"]["九星原位"]["艮"] == "天任"
    assert info["fly_pan"]["九星原位"]["兑"] == "天柱"


def test_simulate_simulation_note_nonempty():
    """simulation_note 必须非空."""
    raw = {"sanyuan_days_in_term": 1}
    info = _simulate_multi_pan(raw, "month", "fly", "maoshan")
    assert len(info["simulation_note"]) > 0
    # 包含三种特征
    assert "月家" in info["simulation_note"]
    assert "飞盘" in info["simulation_note"]
    assert "茅山" in info["simulation_note"]


# ══════════════════════════════════════════════════════════════
# 8. 完整 4 × 2 × 2 = 16 组合 smoke test
# ══════════════════════════════════════════════════════════════
@pytest.mark.parametrize("pan_type", ["hour", "day", "month", "year"])
@pytest.mark.parametrize("pan_style", ["turn", "fly"])
@pytest.mark.parametrize("zhi_run_method", ["chaibu", "maoshan"])
def test_all_16_combinations_work(pan_type, pan_style, zhi_run_method):
    """4 × 2 × 2 = 16 组合全部 smoke test 通过."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    r = qimen.compute(b, pan_type=pan_type, pan_style=pan_style,
                      zhi_run_method=zhi_run_method)
    assert isinstance(r, ChartResult)
    assert r.method == "qimen"
    assert r.school == "east"
    pi = r.raw["pan_info"]
    assert pi["pan_type"] == pan_type
    assert pi["pan_style"] == pan_style
    assert pi["zhi_run_method"] == zhi_run_method
    # engine 名含全部 3 段
    assert pan_type in r.engine
    assert pan_style in r.engine
    assert zhi_run_method in r.engine


# ══════════════════════════════════════════════════════════════
# 9. 排盘字段保留 (与原 72 局定局表兼容)
# ══════════════════════════════════════════════════════════════
def test_day_pan_preserves_paiju_field():
    """日家排盘字段仍含 '阳遁/阴遁 X 局 Y 元'."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="day")
    pj = r.raw["排局"]
    assert "遁" in pj and "局" in pj and "元" in pj


def test_year_pan_preserves_paiju_field():
    """年家排盘字段仍含 '阳遁/阴遁 X 局 Y元'."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="year")
    pj = r.raw["排局"]
    assert "遁" in pj and "局" in pj and "元" in pj


def test_fly_pan_preserves_paiju_field():
    """飞盘排盘字段仍含 '阳遁/阴遁 X 局 Y 元'."""
    r = qimen.compute(Birth(2024, 12, 25, 14, 30, 0), pan_style="fly")
    pj = r.raw["排局"]
    assert "遁" in pj and "局" in pj and "元" in pj


def test_maoshan_preserves_paiju_field():
    """茅山法排盘字段仍含 '阳遁/阴遁 X 局 Y 元'."""
    r = qimen.compute(Birth(2024, 12, 25, 14, 30, 0), zhi_run_method="maoshan")
    pj = r.raw["排局"]
    assert "遁" in pj and "局" in pj and "元" in pj


# ══════════════════════════════════════════════════════════════
# 10. engine 命名约定
# ══════════════════════════════════════════════════════════════
def test_engine_name_format():
    """engine 名 = qimen-multipan-... 格式."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0),
                      pan_type="day", pan_style="fly", zhi_run_method="maoshan")
    assert r.engine.startswith("qimen-multipan")
    assert "day" in r.engine
    assert "fly" in r.engine
    assert "maoshan" in r.engine


def test_engine_distinguishes_fallback():
    """kinqimen 缺失时 engine 含 'fallback'."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), pan_type="day")
    assert "fallback" in r.engine


# ══════════════════════════════════════════════════════════════
# 11. 多盘种与局数一致性 (不污染原 72 局表)
# ══════════════════════════════════════════════════════════════
def test_pan_type_does_not_change_jun_num():
    """pan_type 变化不改变 局数 (同节气同一日, 局数固定)."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    r_hour = qimen.compute(b, pan_type="hour")
    r_day = qimen.compute(b, pan_type="day")
    r_month = qimen.compute(b, pan_type="month")
    r_year = qimen.compute(b, pan_type="year")
    assert r_hour.raw["局数"] == r_day.raw["局数"]
    assert r_day.raw["局数"] == r_month.raw["局数"]
    assert r_month.raw["局数"] == r_year.raw["局数"]


def test_pan_style_does_not_change_jun_num():
    """pan_style 变化不改变 局数 (转盘/飞盘同局数)."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    r_turn = qimen.compute(b, pan_style="turn")
    r_fly = qimen.compute(b, pan_style="fly")
    assert r_turn.raw["局数"] == r_fly.raw["局数"]


def test_maoshan_same_jun_as_chaibu_in_same_day():
    """同一日, 茅山与拆补在同一三元内局数相同."""
    b = Birth(2024, 6, 22, 14, 30, 0)   # 夏至后第 2 天 -> 上元
    r_cb = qimen.compute(b, zhi_run_method="chaibu")
    r_ms = qimen.compute(b, zhi_run_method="maoshan")
    # 上元二者必同
    assert r_cb.raw["局数"] == r_ms.raw["局数"]


# ══════════════════════════════════════════════════════════════
# 12. 跨节气多盘种
# ══════════════════════════════════════════════════════════════
def test_different_terms_different_jun():
    """不同节气下, 多盘种局数相应变化."""
    b_xz = Birth(2024, 6, 25, 14, 30, 0)   # 夏至 -> 阴遁
    b_dz = Birth(2024, 12, 25, 14, 30, 0)  # 冬至 -> 阳遁
    r_xz = qimen.compute(b_xz, pan_type="day")
    r_dz = qimen.compute(b_dz, pan_type="day")
    assert "阴遁" in r_xz.raw["排局"]
    assert "阳遁" in r_dz.raw["排局"]
    assert r_xz.raw["局数"] != r_dz.raw["局数"]


def test_year_pan_yin_vs_yang_mirror():
    """年家奇门阴阳遁镜像 (冬至 vs 夏至)."""
    b_xz = Birth(2024, 12, 25, 14, 30, 0)
    b_xz2 = Birth(2024, 6, 25, 14, 30, 0)
    r1 = qimen.compute(b_xz, pan_type="year")
    r2 = qimen.compute(b_xz2, pan_type="year")
    assert r1.raw["遁"] != r2.raw["遁"]
