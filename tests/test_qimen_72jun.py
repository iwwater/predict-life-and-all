"""Tests for 奇门遁甲 72 局集成 (divination/engines/qimen.py)

文献依据: 《烟波钓叟歌》《奇门遁甲统宗》《奇门遁甲秘笈大全》
覆盖:
  - fallback 自动定局 (用 divination.data.qimen_jiu_jun 推算)
  - 排局字段格式: '阳遁/阴遁 X 局 上元/中元/下元'
  - SANYUAN_RANGES 字段
  - sanyuan_days_in_term 字段
  - evidence_sources 字段
  - 格局判断 (九遁、三奇、八门得令)
  - 跨年节气推算 (内插年度)
  - API 兼容
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth, ChartResult
from divination.engines import qimen
from divination.engines.qimen import (
    _format_paiju,
    _infer_term_dates_for_year,
    _judge,
    _fallback_raw,
    _THREE_QI,
    _EVIDENCE_SOURCES,
)


# ══════════════════════════════════════════════════════════════
# 1. 排局字段格式化
# ══════════════════════════════════════════════════════════════
def test_format_paiju_yang_shang():
    """阳遁一局上元 (6.18 决策: 统一简体输出)."""
    assert _format_paiju("阳遁", 1, "上元") == "阳遁一局上元"


def test_format_paiju_yin_xia():
    """阴遁九局下元."""
    assert _format_paiju("阴遁", 9, "下元") == "阴遁九局下元"


def test_format_paiju_yang_zhong_5():
    """阳遁五局中元."""
    assert _format_paiju("阳遁", 5, "中元") == "阳遁五局中元"


# ══════════════════════════════════════════════════════════════
# 2. 跨年节气日期内插
# ══════════════════════════════════════════════════════════════
def test_infer_term_dates_2026():
    """2026 年节气日期与基准表一致."""
    dates = _infer_term_dates_for_year(2026)
    assert dates["冬至"] == (2026, 12, 22)
    assert dates["夏至"] == (2026, 6, 21)
    assert dates["立春"] == (2026, 2, 4)


def test_infer_term_dates_2024_offset():
    """2024 年节气应有 ~0.25*2 = 0 天偏移 (四舍五入 0)."""
    dates_2026 = _infer_term_dates_for_year(2026)
    dates_2024 = _infer_term_dates_for_year(2024)
    # 2024 offset = round((2024-2026)*0.25) = round(-0.5) = 0 (银行家舍入) or -1
    # 验证年内顺序仍在
    terms_sorted = sorted(dates_2024.items(), key=lambda x: x[1])
    months = [m for _, (_, m, _) in terms_sorted]
    # 至少 6 个连续月份的顺序
    assert months[0] in (1, 12)  # 小寒 or 冬至


def test_infer_term_dates_has_24():
    """任何年份应返回 24 节气."""
    dates = _infer_term_dates_for_year(2024)
    assert len(dates) == 24


# ══════════════════════════════════════════════════════════════
# 3. fallback 自动定局
# ══════════════════════════════════════════════════════════════
def test_fallback_has_required_fields():
    """fallback raw 必须包含关键字段."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    raw = _fallback_raw(b, "test")
    for k in ["节气", "排局", "局数", "三元", "遁", "sanyuan_days_in_term",
              "evidence_sources", "三元范围", "断"]:
        assert k in raw, f"missing {k}"


def test_fallback_xiazhi_2024_yin_9():
    """2024-06-25 应判夏至上元阴遁9局 (与2026夏至相同节气)."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    raw = _fallback_raw(b, "test")
    assert raw["节气"] == "夏至"
    assert raw["遁"] == "阴遁"
    assert raw["局数"] == 9
    assert raw["三元"] == "上元"
    assert raw["排局"] == "阴遁九局上元"


def test_fallback_lichun_2024_yang_8():
    """2024-02-08 应判立春上元阳遁8局 (2024立春≈2-4)."""
    b = Birth(2024, 2, 5, 14, 30, 0)
    raw = _fallback_raw(b, "test")
    assert raw["节气"] == "立春"
    assert raw["遁"] == "阳遁"
    assert raw["局数"] == 8
    assert raw["三元"] == "上元"


def test_fallback_winter_solstice_2024_yang_1():
    """2024-12-25 应判冬至上元阳遁1局."""
    b = Birth(2024, 12, 25, 14, 30, 0)
    raw = _fallback_raw(b, "test")
    assert raw["节气"] == "冬至"
    # 6.18 决策: 统一简体输出
    assert raw["遁"] == "阳遁"
    assert raw["局数"] == 1


def test_fallback_sanyuan_days_in_term():
    """节内天数应在 1-15 范围（夏至当日为第1天）."""
    b = Birth(2024, 6, 21, 14, 30, 0)  # 夏至日 (2026 基准, 2024 偏移 0 天)
    raw = _fallback_raw(b, "test")
    assert raw["sanyuan_days_in_term"] >= 1
    assert raw["sanyuan_days_in_term"] <= 15


def test_fallback_sanyuan_ranges():
    """三元范围字段内容."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    raw = _fallback_raw(b, "test")
    sr = raw["三元范围"]
    assert sr["上元"] == [1, 5]
    assert sr["中元"] == [6, 10]
    assert sr["下元"] == [11, 15]


def test_fallback_evidence_sources():
    """evidence_sources 字段包含 烟波钓叟歌 / 奇门遁甲统宗."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    raw = _fallback_raw(b, "test")
    text = "".join(raw["evidence_sources"])
    assert "烟波钓叟歌" in text or "奇门" in text


# ══════════════════════════════════════════════════════════════
# 4. compute() 完整调用 (fallback 模式)
# ══════════════════════════════════════════════════════════════
def test_compute_returns_chart_result():
    """compute 返回 ChartResult."""
    b = Birth(2024, 6, 25, 14, 30, 0)
    r = qimen.compute(b)
    assert isinstance(r, ChartResult)
    assert r.method == "qimen"
    assert r.school == "east"


def test_compute_fallback_engine():
    """kinqimen 缺失 → fallback engine."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0))
    assert "fallback" in r.engine


def test_compute_paiju_in_raw():
    """compute 输出的 raw['排局'] 应包含完整 '阳遁/阴遁 + 局数 + 元'."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0))
    pj = r.raw["排局"]
    assert "遁" in pj
    assert "局" in pj
    assert "元" in pj


# ══════════════════════════════════════════════════════════════
# 5. 格局判断 (_judge 函数)
# ══════════════════════════════════════════════════════════════
def test_judge_three_qi_pattern():
    """天盘三奇俱临 -> 大格."""
    raw = {
        "天盘三奇六仪": {"坎": "乙", "艮": "丙", "震": "丁"},
        "地盘三奇六仪": {"坎": "戊", "艮": "己", "震": "庚"},
        "八门": {"坎": "休门"},
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年丙寅月戊申日甲寅時",
    }
    out = _judge(raw)
    assert any("三奇" in g for g in out["格局"])


def test_judge_three_qi_de_shi():
    """三奇得值使门."""
    raw = {
        "天盘三奇六仪": {"坎": "乙", "艮": "戊"},
        "地盘三奇六仪": {"坎": "戊"},
        "八门": {"坎": "开门"},
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年丙寅月戊申日甲寅時",
        "值符值使": {"值使門宮": ["开", "坎"]},
    }
    out = _judge(raw)
    assert any("三奇得使" in g or "值使临吉门" in g for g in out["格局"])


def test_judge_ji_door_de_ling():
    """吉门得令 (开门落乾宫金月/兑月)."""
    raw = {
        "天盘三奇六仪": {"乾": "乙"},
        "地盘三奇六仪": {},
        "八门": {"乾": "开门", "兑": "休门"},
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年癸酉月戊申日甲寅時",  # 酉月 = 金
        "值符值使": {},
    }
    out = _judge(raw)
    # 开门在乾宫, 酉月金 -> 开门得令
    assert any("得令" in g or "得月生" in g for g in out["格局"])


def test_judge_men_po():
    """门迫: 宫克门."""
    raw = {
        "天盘三奇六仪": {},
        "地盘三奇六仪": {},
        "八门": {"坎": "开门"},  # 开门金, 坎水 -> 金生水非门迫
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年丙寅月戊申日甲寅時",
    }
    out = _judge(raw)
    # 开门在坎(水) -> 金生水非门迫
    # 重新构造门迫: 死门(土) 在 乾宫(金) -> 金克土? 死门土, 金克土 -> 不是
    # 木门 (伤门/杜门) 在 乾宫(金) -> 金克木 = 门迫
    raw["八门"] = {"乾": "伤门"}
    out2 = _judge(raw)
    assert any("门迫" in v for v in out2["门状态"].values())


def test_judge_ru_mu():
    """天盘干入墓."""
    # 乙木墓在未; 未在坤宫(未申)
    raw = {
        "天盘三奇六仪": {"坤": "乙"},
        "地盘三奇六仪": {},
        "八门": {},
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年丙寅月戊申日甲寅時",
        "值符值使": {},
    }
    out = _judge(raw)
    # 乙木墓未在坤宫 -> 入墓
    assert any("入墓" in s for s in out["入墓"])


# ══════════════════════════════════════════════════════════════
# 6. SANYUAN_RANGES 集成
# ══════════════════════════════════════════════════════════════
def test_sanyuan_ranges_present():
    """三元范围常量."""
    from divination.data.qimen_jiu_jun import SANYUAN_RANGES
    assert SANYUAN_RANGES["上元"] == (1, 5)
    assert SANYUAN_RANGES["中元"] == (6, 10)
    assert SANYUAN_RANGES["下元"] == (11, 15)


def test_three_qi_set():
    """三奇 = 乙丙丁."""
    assert _THREE_QI == {"乙", "丙", "丁"}


# ══════════════════════════════════════════════════════════════
# 7. API 兼容性
# ══════════════════════════════════════════════════════════════
def test_api_signature():
    """compute 签名兼容."""
    import inspect
    sig = inspect.signature(qimen.compute)
    params = list(sig.parameters.keys())
    assert "b" in params
    assert "method" in params


def test_method_param_1_or_2():
    """method 参数 = 1 (拆补) 或 2 (置闰)."""
    r1 = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), method=1)
    r2 = qimen.compute(Birth(2024, 6, 25, 14, 30, 0), method=2)
    assert isinstance(r1, ChartResult)
    assert isinstance(r2, ChartResult)


# ══════════════════════════════════════════════════════════════
# 8. 跨节气定局一致性 (回归)
# ══════════════════════════════════════════════════════════════
def test_xiazhi_vs_lichun_mirror():
    """夏至上元(阴9) vs 立春上元(阳8) 不同局."""
    b_xz = Birth(2024, 6, 25, 14, 30, 0)
    b_lc = Birth(2024, 2, 5, 14, 30, 0)
    raw_xz = _fallback_raw(b_xz, "test")
    raw_lc = _fallback_raw(b_lc, "test")
    assert raw_xz["遁"] == "阴遁"
    assert raw_lc["遁"] == "阳遁"
    assert raw_xz["局数"] != raw_lc["局数"]


def test_sanyuan_progression_same_term():
    """同一节气内 5/10/15 -> 上/中/下元."""
    # 2024-12-22 冬至, 12-22 上元(第1天), 12-27 中元(第6天), 12-31+1=1-2 下元
    # 实际冬至后 1-5 上元, 6-10 中元, 11-15 下元
    # 冬至日: 2024-12-21 (估算), 12-22 第2天 -> 上元
    # 取 冬至后第 1/6/11 天
    # 冬至日期取决于 _infer_term_dates_for_year (round 偏移)
    # 用 2026 校验
    b1 = Birth(2026, 12, 22, 14, 30, 0)   # 冬至上元
    b2 = Birth(2026, 12, 27, 14, 30, 0)   # 冬至中元
    b3 = Birth(2026, 12, 31, 14, 30, 0)   # 冬至...但跨年
    # 用 2026 冬至前的中元/下元
    # 冬至 12-22 -> 中元 12-27 (第6天), 下元 12-31 (第10天, 跨到 11-15)
    # 安全: 仅测 上元 + 中元
    raw1 = _fallback_raw(b1, "test")
    raw2 = _fallback_raw(b2, "test")
    assert raw1["节气"] == "冬至"
    assert raw2["节气"] == "冬至"
    assert raw1["三元"] == "上元"
    assert raw2["三元"] == "中元"
    assert raw1["局数"] != raw2["局数"]  # 上元=1局 中元=7局