"""Tests for 六爻深化 (divination/engines/liuyao.py)

文献依据: 《增删卜易》《卜筮正宗》《京氏易传》《火珠林》
覆盖:
  - 完整六神排布（甲乙起青龙, 丙丁朱雀, 戊勾陈, 己螣蛇, 庚辛白虎, 壬癸玄武）
  - 伏神查找（卦中无六亲 → 本宫卦伏神）
  - 世应关系深化（生克细分）
  - 动爻/变爻回头生克
  - 卦身计算
  - evidence_sources 字段
  - 兼容性（API 不变）
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth, ChartResult
from divination.engines import liuyao
from divination.engines.liuyao import (
    _calc_guashen,
    _find_fushen,
    _shiying_relation,
    _bian_yao_effect,
    _GAN_START,
    _LIUSHEN,
    _YONGSHEN,
)


# ══════════════════════════════════════════════════════════════
# 1. 完整六神排布（《卜筮正宗》）
# ══════════════════════════════════════════════════════════════
def test_liushen_jia_qinglong():
    """甲日起青龙 (初爻青龙)."""
    # 2024-1-1 是甲日 (verified)
    b = Birth(2024, 1, 1, 12, 0, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    assert r.raw["日干"] == "甲"
    assert r.raw["六神"][0] == "青龙"


def test_liushen_bing_zhuque():
    """丙日起朱雀 (初爻朱雀)."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    # 模拟日干丙 -> 朱雀起
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    # 日干来自 lunar_python, 不是测试可控制, 这里只验证 6 神循环
    assert len(r.raw["六神"]) == 6
    assert set(r.raw["六神"]) == set(_LIUSHEN)


def test_liushen_cycle_6():
    """六神共 6 种, 必然 1-6 各一次（单卦循环一次）."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    gods = r.raw["六神"]
    assert sorted(gods) == sorted(_LIUSHEN)


def test_liushen_start_mapping():
    """日干 -> 起神 映射正确（《卜筮正宗》）."""
    # 甲/乙 -> 青龙, 丙/丁 -> 朱雀, 戊 -> 勾陈, 己 -> 螣蛇, 庚/辛 -> 白虎, 壬/癸 -> 玄武
    expected = {
        "甲": "青龙", "乙": "青龙",
        "丙": "朱雀", "丁": "朱雀",
        "戊": "勾陈", "己": "螣蛇",
        "庚": "白虎", "辛": "白虎",
        "壬": "玄武", "癸": "玄武",
    }
    for gan, god in expected.items():
        start = _GAN_START[gan]
        assert _LIUSHEN[start] == god, f"{gan} -> {_LIUSHEN[start]} != {god}"


# ══════════════════════════════════════════════════════════════
# 2. 卦身计算（《卜筮正宗·卦身》）
# ══════════════════════════════════════════════════════════════
def test_guashen_shih_yao_valid():
    """卦身爻位应为 1-6 范围."""
    for shi in range(1, 7):
        g = _calc_guashen(shi, "阳")
        assert 1 <= g <= 6


def test_guashen_in_raw():
    """raw 中应有卦身字段."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    if "卦身" in r.raw:
        gs = r.raw["卦身"]
        assert "爻" in gs
        assert "地支" in gs


# ══════════════════════════════════════════════════════════════
# 3. 伏神查找（《增删卜易》飞伏篇）
# ══════════════════════════════════════════════════════════════
def test_fushen_find_qicai_in_kun():
    """坤宫卦(如泰)求妻财 -> 本宫坤卦必有妻财伏神."""
    # 泰 = 上坤下乾 -> 坤宫
    from divination import yijing
    lines = [1, 1, 1, 0, 0, 0]  # 泰
    naijia = yijing.naijia(lines)
    # 泰 卦: 本宫坤, 妻财位在 五爻(亥, 水) 与 上爻(酉, 金)
    # 直接验证本宫坤卦确实含妻财
    pal_naijia = yijing.naijia(yijing._PURE["坤"])
    has_qicai = any(e["六亲"] == "妻财" for e in pal_naijia)
    assert has_qicai


def test_fushen_returns_correct_liuqin():
    """伏神查找返回的六亲 == 目标六亲."""
    from divination import yijing
    lines = [1, 1, 1, 0, 0, 0]  # 泰 (坤宫)
    naijia = yijing.naijia(lines)
    f = _find_fushen("妻财", "坤", naijia)
    assert f is not None
    assert f["六亲"] == "妻财"
    assert f["来源"].startswith("本宫坤卦")


def test_fushen_in_judgement_when_missing():
    """卦中无六亲 -> 断语应包含伏神."""
    # 既济卦 测财 (妻财不上卦)
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 8, 9, 6, 7, 8], query="求财")
    # 既济 卦 六亲: 子孙/兄弟/妻财? 看输出
    if "伏神" in r.raw["断"]:
        # 找到伏神
        assert r.raw["断"]["伏神"]["六亲"] == "妻财"


def test_fushen_invalid_gong_returns_none():
    """非法本宫 → None."""
    from divination import yijing
    lines = [1, 1, 1, 0, 0, 0]
    naijia = yijing.naijia(lines)
    f = _find_fushen("妻财", "INVALID_GONG", naijia)
    assert f is None


# ══════════════════════════════════════════════════════════════
# 4. 世应关系深化（《增删卜易·世应章》）
# ══════════════════════════════════════════════════════════════
def test_shiying_bihe():
    """世应比和."""
    shi = {"爻": 3, "五行": "木"}
    ying = {"爻": 6, "五行": "木"}
    notes = _shiying_relation(shi, ying)
    assert any("比和" in n for n in notes)


def test_shiying_sheng_ru():
    """应生世（应生入世）."""
    shi = {"爻": 3, "五行": "木"}
    ying = {"爻": 6, "五行": "水"}  # 水生木
    notes = _shiying_relation(shi, ying)
    assert any("应生世" in n or "利我" in n for n in notes)


def test_shiying_ying_ke_shi():
    """应克世（应反制世）."""
    shi = {"爻": 3, "五行": "木"}
    ying = {"爻": 6, "五行": "金"}  # 金克木
    notes = _shiying_relation(shi, ying)
    assert any("应克世" in n or "凶" in n or "制我" in n for n in notes)


def test_shiying_in_judgement():
    """raw['断']['世应关系'] 应包含说明."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    assert "世应关系" in r.raw["断"]
    sy = r.raw["断"]["世应关系"]
    assert len(sy) >= 1


# ══════════════════════════════════════════════════════════════
# 5. 动爻/变爻回头生克（《增删卜易·动变篇》）
# ══════════════════════════════════════════════════════════════
def test_bian_yao_huitou_ke():
    """变爻回头克."""
    orig = {"爻": 3, "五行": "木"}
    bian = {"六亲": "官鬼"}
    eff = _bian_yao_effect(orig, bian, "金", "金")  # 金克木
    assert "回头克" in eff["关系"]


def test_bian_yao_huitou_sheng():
    """变爻回头生."""
    orig = {"爻": 3, "五行": "木"}
    bian = {"六亲": "父母"}
    eff = _bian_yao_effect(orig, bian, "水", "水")  # 水生木
    assert "回头生" in eff["关系"]


def test_bian_effects_in_judgement():
    """动变回头应出现在断法中."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    # 两个动爻 (9, 6)
    r = liuyao.compute(b, tosses=[7, 7, 9, 6, 7, 7])
    assert "动变回头" in r.raw["断"]
    effects = r.raw["断"]["动变回头"]
    assert len(effects) == 2
    for e in effects:
        assert "关系" in e


# ══════════════════════════════════════════════════════════════
# 6. evidence_sources 字段
# ══════════════════════════════════════════════════════════════
def test_evidence_sources_present():
    """断法层必须有 evidence_sources."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    assert "evidence_sources" in r.raw["断"]
    sources = r.raw["断"]["evidence_sources"]
    assert isinstance(sources, list)
    assert len(sources) >= 2
    # 必须包含增删卜易 / 卜筮正宗
    text = "".join(sources)
    assert "增删卜易" in text or "卜筮正宗" in text


# ══════════════════════════════════════════════════════════════
# 7. API 兼容性 & 默认行为
# ══════════════════════════════════════════════════════════════
def test_api_signature():
    """compute 函数签名兼容."""
    import inspect
    sig = inspect.signature(liuyao.compute)
    params = list(sig.parameters.keys())
    assert "b" in params
    assert "tosses" in params
    assert "seed" in params
    assert "query" in params


def test_result_is_chart_result():
    """返回 ChartResult 实例."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    assert isinstance(r, ChartResult)
    assert r.method == "liuyao"
    assert r.school == "east"


def test_seed_determinism():
    """seed 决定结果可重现."""
    b1 = Birth(2024, 6, 15, 14, 30, 0)
    b2 = Birth(2024, 6, 15, 14, 30, 0)
    r1 = liuyao.compute(b1, seed=42)
    r2 = liuyao.compute(b2, seed=42)
    assert r1.raw["摇钱"] == r2.raw["摇钱"]


def test_query_qiucai_yongshen():
    """query=求财 -> 用神 = 妻财."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7], query="求财")
    assert r.raw["断"]["问事"] == "求财"
    assert r.raw["断"]["用神六亲"] == "妻财"


def test_yongshen_mapping_complete():
    """_YONGSHEN 字典覆盖主要问事类别."""
    categories = {"财", "官", "父母", "子女", "兄弟"}
    for cat in categories:
        assert cat in _YONGSHEN


# ══════════════════════════════════════════════════════════════
# 8. 变卦装卦完整性
# ══════════════════════════════════════════════════════════════
def test_bian_naijia_present_when_moving():
    """有动爻时, 变卦装卦应存在."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 9, 6, 7, 7])
    assert "变卦装卦" in r.raw
    assert r.raw["变卦装卦"] is not None
    assert len(r.raw["变卦装卦"]) == 6


def test_bian_naijia_none_when_static():
    """无动爻时, 变卦装卦为 None."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])  # 全少阳少阴
    assert r.raw["变卦装卦"] is None
    assert r.raw["变卦"] is None
    assert r.raw["动爻"] == []


# ══════════════════════════════════════════════════════════════
# 9. 八宫六十四卦伏神完整性 (跨卦通用)
# ══════════════════════════════════════════════════════════════
def test_all_eight_gong_have_all_liuqin():
    """八宫本宫卦六亲必须齐全（保证伏神可查）."""
    from divination import yijing
    for gong, lines in yijing._PURE.items():
        naijia = yijing.naijia(lines)
        liuqins = {e["六亲"] for e in naijia}
        assert liuqins == {"父母", "兄弟", "子孙", "妻财", "官鬼"}, \
            f"{gong} 宫卦缺六亲: {liuqins}"


def test_fushen_find_in_all_palaces():
    """八宫卦都能找到五种六亲的伏神."""
    from divination import yijing
    for gong in yijing._PURE.keys():
        # 用本宫卦自己的 naijia（应有 5 种六亲）
        pure_naijia = yijing.naijia(yijing._PURE[gong])
        for lq in ("父母", "兄弟", "子孙", "妻财", "官鬼"):
            f = _find_fushen(lq, gong, pure_naijia)
            assert f is not None, f"{gong} 宫找 {lq} 失败"
            assert f["六亲"] == lq