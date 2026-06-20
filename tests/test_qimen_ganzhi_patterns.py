"""Tests for 奇门遁甲 干组合格局 (divination/data/qimen_patterns.py + engine 集成)

文献依据: 《奇门遁甲统宗》《奇门遁甲秘笈大全》《烟波钓叟歌》《遁甲神应经》
覆盖:
  - 12 项 GANZHI_PATTERN_TABLE 数据契约 (id/name/category/polarity/source/check_fn)
  - 单 pattern 检测 (每项 ≥ 1 active 案例 + ≥ 1 inactive 案例)
  - detect_patterns 总函数 (全图/部分成立/全不成立)
  - source 字段非空契约
  - golden 对照 (《奇门统宗》案例)
  - engine 集成 (qimen._judge 输出干组合格局, compute() 顶层暴露)
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth, ChartResult
from divination.data.qimen_patterns import (
    GANZHI_PATTERN_TABLE,
    QimenPattern,
    count_patterns_by_polarity,
    detect_patterns,
)
from divination.engines import qimen
from divination.engines.qimen import _judge


# ══════════════════════════════════════════════════════════════
# 1. 数据契约完整性
# ══════════════════════════════════════════════════════════════
def test_pattern_table_count():
    """GANZHI_PATTERN_TABLE 至少 12 项."""
    assert len(GANZHI_PATTERN_TABLE) >= 12


def test_pattern_table_required_fields():
    """每条 pattern 必须有 id/name/category/polarity/description/source/check_fn."""
    required_attrs = {"id", "name", "category", "polarity", "description", "source", "check_fn"}
    for p in GANZHI_PATTERN_TABLE:
        for attr in required_attrs:
            assert hasattr(p, attr), f"pattern 缺字段 {attr}: {p}"
            v = getattr(p, attr)
            assert v is not None, f"pattern.{attr} 为 None: {p.id}"


def test_pattern_ids_unique():
    """所有 pattern.id 必须唯一."""
    ids = [p.id for p in GANZHI_PATTERN_TABLE]
    assert len(ids) == len(set(ids)), f"重复 id: {ids}"


def test_pattern_polarity_valid():
    """polarity 必须在约定枚举内."""
    valid = {"auspicious", "slightly_auspicious", "inauspicious",
             "slightly_inauspicious", "neutral"}
    for p in GANZHI_PATTERN_TABLE:
        assert p.polarity in valid, f"{p.id} polarity 非法: {p.polarity}"


def test_pattern_category_valid():
    """category 必须在约定枚举内."""
    valid = {"gan_zhi_ju", "men_ju", "xing_ju", "fu_yin", "fan_yin"}
    for p in GANZHI_PATTERN_TABLE:
        assert p.category in valid, f"{p.id} category 非法: {p.category}"


def test_pattern_source_non_empty():
    """source 字段必须非空 (契约要求, 文献依据)."""
    for p in GANZHI_PATTERN_TABLE:
        assert p.source and len(p.source) > 0, f"{p.id} source 为空"
        # 必须包含文献出处标志 (《》或卷)
        assert "《" in p.source, f"{p.id} source 缺《》: {p.source}"


def test_pattern_callable_check_fn():
    """check_fn 必须是 callable."""
    for p in GANZHI_PATTERN_TABLE:
        assert callable(p.check_fn), f"{p.id} check_fn 不可调用"


def test_pattern_frozen():
    """QimenPattern 是 frozen dataclass."""
    p = GANZHI_PATTERN_TABLE[0]
    with pytest.raises(Exception):
        p.name = "新名"  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════
# 2. 单 pattern 检测 (12 项 × active+inactive)
# ══════════════════════════════════════════════════════════════
# ─── 2.1 青龙返首 ───
def test_qinglong_fanshou_active():
    """青龙返首: 天盘甲 + 地盘戊."""
    t = {"坎": "甲"}
    d = {"坎": "戊"}
    res = detect_patterns(t, d)
    assert any(p.id == "qinglong_fanshou" for p in res)


def test_qinglong_fanshou_inactive():
    """青龙返首 inactive: 无甲+戊组合."""
    t = {"坎": "乙", "艮": "丙"}
    d = {"坎": "庚", "艮": "戊"}
    res = detect_patterns(t, d)
    assert not any(p.id == "qinglong_fanshou" for p in res)


# ─── 2.2 飞鸟跌穴 ───
def test_feiniao_diexue_active():
    """飞鸟跌穴: 天盘甲 + 地盘庚."""
    t = {"坎": "甲"}
    d = {"坎": "庚"}
    res = detect_patterns(t, d)
    assert any(p.id == "feiniao_diexue" for p in res)


def test_feiniao_diexue_inactive():
    """飞鸟跌穴 inactive: 无甲+庚组合."""
    t = {"坎": "乙"}
    d = {"坎": "戊"}
    res = detect_patterns(t, d)
    assert not any(p.id == "feiniao_diexue" for p in res)


# ─── 2.3 天辅时 ───
def test_tianfu_shi_active():
    """天辅时: 三奇临本时辰所在宫."""
    t = {"坎": "乙"}  # 三奇
    d = {"坎": "戊"}
    ctx = {"hour_gong": "坎"}
    res = detect_patterns(t, d, ctx)
    assert any(p.id == "tianfu_shi" for p in res)


def test_tianfu_shi_inactive():
    """天辅时 inactive: 三奇不在本时辰宫."""
    t = {"坎": "戊"}  # 非三奇
    d = {"坎": "乙"}
    ctx = {"hour_gong": "坎"}
    res = detect_patterns(t, d, ctx)
    assert not any(p.id == "tianfu_shi" for p in res)


# ─── 2.4 三诈五假 ───
def test_sanzha_wujia_active():
    """三诈五假: 三奇 + 吉门(开门/休门/生门)."""
    t = {"坎": "乙"}
    d = {"坎": "戊"}
    ctx = {"doors": {"坎": "开门"}}
    res = detect_patterns(t, d, ctx)
    assert any(p.id == "sanzha_wujia" for p in res)


def test_sanzha_wujia_inactive():
    """三诈五假 inactive: 三奇 + 凶门."""
    t = {"坎": "乙"}
    d = {"坎": "戊"}
    ctx = {"doors": {"坎": "死门"}}
    res = detect_patterns(t, d, ctx)
    assert not any(p.id == "sanzha_wujia" for p in res)


# ─── 2.5 白虎猖狂 ───
def test_baihu_changkuang_active():
    """白虎猖狂: 天盘庚 + 地盘日干(乙)."""
    t = {"坎": "庚"}
    d = {"坎": "乙"}
    ctx = {"day_gan": "乙"}
    res = detect_patterns(t, d, ctx)
    assert any(p.id == "baihu_changkuang" for p in res)


def test_baihu_changkuang_inactive():
    """白虎猖狂 inactive: 无庚+日干组合."""
    t = {"坎": "丙"}
    d = {"坎": "乙"}
    ctx = {"day_gan": "乙"}
    res = detect_patterns(t, d, ctx)
    assert not any(p.id == "baihu_changkuang" for p in res)


# ─── 2.6 荧惑入荧 ───
def test_yinghuo_ruying_active():
    """荧惑入荧: 丙+丙."""
    t = {"坎": "丙"}
    d = {"坎": "丙"}
    res = detect_patterns(t, d)
    assert any(p.id == "yinghuo_ruying" for p in res)


def test_yinghuo_ruying_inactive():
    """荧惑入荧 inactive: 无丙+丙."""
    t = {"坎": "丙"}
    d = {"坎": "丁"}
    res = detect_patterns(t, d)
    assert not any(p.id == "yinghuo_ruying" for p in res)


# ─── 2.7 太白人荧 ───
def test_taibai_ruying_active():
    """太白人荧: 庚+丙."""
    t = {"坎": "庚"}
    d = {"坎": "丙"}
    res = detect_patterns(t, d)
    assert any(p.id == "taibai_ruying" for p in res)


def test_taibai_ruying_inactive():
    """太白人荧 inactive: 无庚+丙."""
    t = {"坎": "庚"}
    d = {"坎": "乙"}
    res = detect_patterns(t, d)
    assert not any(p.id == "taibai_ruying" for p in res)


# ─── 2.8 朱雀入江 ───
def test_zhuque_rujiang_active():
    """朱雀入江: 乙+癸."""
    t = {"坎": "乙"}
    d = {"坎": "癸"}
    res = detect_patterns(t, d)
    assert any(p.id == "zhuque_rujiang" for p in res)


def test_zhuque_rujiang_inactive():
    """朱雀入江 inactive: 无乙+癸."""
    t = {"坎": "乙"}
    d = {"坎": "戊"}
    res = detect_patterns(t, d)
    assert not any(p.id == "zhuque_rujiang" for p in res)


# ─── 2.9 青龙入天牢 ───
def test_qinglong_rutianlao_active():
    """青龙入天牢: 乙+庚."""
    t = {"坎": "乙"}
    d = {"坎": "庚"}
    res = detect_patterns(t, d)
    assert any(p.id == "qinglong_rutianlao" for p in res)


def test_qinglong_rutianlao_inactive():
    """青龙入天牢 inactive: 无乙+庚."""
    t = {"坎": "乙"}
    d = {"坎": "丙"}
    res = detect_patterns(t, d)
    assert not any(p.id == "qinglong_rutianlao" for p in res)


# ─── 2.10 六仪击刑 ───
def test_liuyi_jixing_active():
    """六仪击刑: 六甲旬首加临被刑支所在宫.

    戊刑卯 (坎=子, 离=午, 震=卯). 所以天盘戊在震(卯) → 击刑.
    """
    t = {"震": "戊"}  # 戊在震 (卯)
    d = {"震": "乙"}
    res = detect_patterns(t, d)
    assert any(p.id == "liuyi_jixing" for p in res)


def test_liuyi_jixing_inactive():
    """六仪击刑 inactive: 六仪不在被刑宫."""
    # 戊刑卯, 若戊在坎(子) → 不击刑
    t = {"坎": "戊"}
    d = {"坎": "乙"}
    res = detect_patterns(t, d)
    assert not any(p.id == "liuyi_jixing" for p in res)


# ─── 2.11 伏吟 ───
def test_fuyin_active():
    """伏吟: ≥3 宫天盘+地盘同干."""
    t = {"坎": "戊", "艮": "己", "震": "庚"}
    d = {"坎": "戊", "艮": "己", "震": "庚"}
    res = detect_patterns(t, d)
    assert any(p.id == "fuyin" for p in res)


def test_fuyin_inactive():
    """伏吟 inactive: 同干 < 3 宫."""
    t = {"坎": "戊", "艮": "乙"}
    d = {"坎": "戊", "艮": "己"}
    res = detect_patterns(t, d)
    assert not any(p.id == "fuyin" for p in res)


# ─── 2.12 反吟 ───
def test_fanyin_active():
    """反吟: ≥3 宫天盘+地盘相冲干 (甲庚/乙辛/丙壬/丁癸)."""
    t = {"坎": "甲", "艮": "乙", "震": "丙"}
    d = {"坎": "庚", "艮": "辛", "震": "壬"}
    res = detect_patterns(t, d)
    assert any(p.id == "fanyin" for p in res)


def test_fanyin_inactive():
    """反吟 inactive: 无 ≥3 宫相冲."""
    t = {"坎": "甲", "艮": "乙"}
    d = {"坎": "庚", "艮": "戊"}  # 仅 1 对冲
    res = detect_patterns(t, d)
    assert not any(p.id == "fanyin" for p in res)


# ══════════════════════════════════════════════════════════════
# 3. detect_patterns 总函数
# ══════════════════════════════════════════════════════════════
def test_detect_patterns_multiple_active():
    """多格局同时激活: 青龙返首 + 飞鸟跌穴 + 青龙入天牢."""
    # 坎: 甲+戊 → 青龙返首
    # 艮: 乙+庚 → 青龙入天牢
    t = {"坎": "甲", "艮": "乙"}
    d = {"坎": "戊", "艮": "庚"}
    ctx = {"doors": {"艮": "开门"}}
    res = detect_patterns(t, d, ctx)
    ids = {p.id for p in res}
    assert "qinglong_fanshou" in ids  # 坎甲+戊
    assert "qinglong_rutianlao" in ids  # 艮乙+庚
    assert "sanzha_wujia" in ids  # 艮乙 + 开门 (三奇之一 + 吉门)


def test_detect_patterns_all_inactive():
    """全盘无激活: 随机盘."""
    t = {"坎": "戊", "艮": "己"}
    d = {"坎": "乙", "艮": "丙"}
    # 无 day_gan, 无 doors → 应仅触发需要 doors/day_gan 的失效, 其他也不命中
    res = detect_patterns(t, d)
    # 此时格局应全不命中 (无甲加戊, 无丙+丙, 等)
    ids = {p.id for p in res}
    # 无任何激活 (因为无 day_gan 且组合无特殊)
    assert len(res) == 0 or all(
        p.id in ("yinghuo_ruying", "taibai_ruying") for p in res
    )
    # 实际: t=戊,d=乙 / t=己,d=丙 → 都不命中特殊组合
    # 排除伏吟/反吟 (需 ≥3 宫)
    assert "fuyin" not in ids
    assert "fanyin" not in ids


def test_detect_patterns_full_chart_falling_into_chaos():
    """九宫全部分布, 应触发多个格局."""
    # 精心构造: 同时触发多个格局
    # 坎: 甲+戊 → 青龙返首
    # 艮: 乙+庚 → 青龙入天牢 + 三诈五假 (开门)
    # 巽: 丙+丙 → 荧惑入荧
    # 离: 乙+癸 → 朱雀入江
    t = {
        "坎": "甲", "艮": "乙", "震": "戊", "巽": "丙", "离": "乙",
        "坤": "己", "兑": "丁", "乾": "辛", "中": "壬",
    }
    d = {
        "坎": "戊", "艮": "庚", "震": "壬", "巽": "丙", "离": "癸",
        "坤": "辛", "兑": "甲", "乾": "乙", "中": "己",
    }
    ctx = {"doors": {"艮": "开门", "离": "休门"}, "day_gan": "乙"}
    res = detect_patterns(t, d, ctx)
    # 至少 5+ 格局激活
    assert len(res) >= 5, f"仅 {len(res)} 激活: {[p.id for p in res]}"


def test_detect_patterns_ctx_optional():
    """无 ctx (None) 也能调用, 不抛异常."""
    t = {"坎": "甲"}
    d = {"坎": "戊"}
    res = detect_patterns(t, d, None)
    # 应至少激活青龙返首 (无需 ctx)
    assert any(p.id == "qinglong_fanshou" for p in res)


def test_detect_patterns_empty():
    """空字典不抛异常, 返回空."""
    res = detect_patterns({}, {})
    assert res == []


# ══════════════════════════════════════════════════════════════
# 4. 统计函数
# ══════════════════════════════════════════════════════════════
def test_count_patterns_by_polarity():
    """count_patterns_by_polarity 正确分类."""
    t = {"坎": "甲", "艮": "乙", "震": "丙"}
    d = {"坎": "戊", "艮": "庚", "震": "丙"}
    ctx = {"doors": {"艮": "开门"}}
    active = detect_patterns(t, d, ctx)
    summary = count_patterns_by_polarity(active)
    assert summary["auspicious"] >= 1
    assert summary["inauspicious"] >= 1
    assert isinstance(summary, dict)


# ══════════════════════════════════════════════════════════════
# 5. Engine 集成: _judge 输出干组合格局
# ══════════════════════════════════════════════════════════════
def test_judge_includes_ganzhi_patterns():
    """_judge 输出含 '干组合格局' / '干组合格局数' 字段."""
    raw = {
        "天盘三奇六仪": {"坎": "甲", "艮": "乙"},
        "地盘三奇六仪": {"坎": "戊", "艮": "庚"},
        "八门": {"艮": "开门"},
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年丙寅月乙未日甲寅時",
        "值符值使": {},
    }
    out = _judge(raw)
    assert "干组合格局" in out
    assert "干组合格局数" in out
    assert isinstance(out["干组合格局"], list)
    assert out["干组合格局数"] == len(out["干组合格局"])


def test_judge_pattern_entry_fields():
    """每条干组合格局条目含 id/name/polarity/category/description/source."""
    raw = {
        "天盘三奇六仪": {"坎": "甲"},
        "地盘三奇六仪": {"坎": "戊"},
        "八门": {},
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年丙寅月戊申日甲寅時",
        "值符值使": {},
    }
    out = _judge(raw)
    for entry in out["干组合格局"]:
        for k in ("id", "name", "polarity", "category", "description", "source"):
            assert k in entry, f"缺字段 {k}"
            assert entry[k]


def test_judge_backward_compat():
    """原有 '格局' 字段保持存在 (向后兼容)."""
    raw = {
        "天盘三奇六仪": {"坎": "乙", "艮": "丙", "震": "丁"},
        "地盘三奇六仪": {},
        "八门": {},
        "九星": {},
        "八神": {},
        "旬空": {},
        "干支": "甲辰年丙寅月戊申日甲寅時",
        "值符值使": {},
    }
    out = _judge(raw)
    assert "格局" in out
    assert isinstance(out["格局"], list)


# ══════════════════════════════════════════════════════════════
# 6. compute() 顶层暴露
# ══════════════════════════════════════════════════════════════
def test_compute_top_level_patterns():
    """compute() 输出的 raw 含 'qimen_patterns' / 'qimen_pattern_count'."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0))
    assert "qimen_patterns" in r.raw
    assert "qimen_pattern_count" in r.raw
    assert isinstance(r.raw["qimen_patterns"], list)
    assert r.raw["qimen_pattern_count"] == len(r.raw["qimen_patterns"])


def test_compute_fallback_patterns_present():
    """fallback 模式也含干组合格局 (可能为空)."""
    r = qimen.compute(Birth(2024, 6, 25, 14, 30, 0))
    # fallback 盘面无完整天地盘, 所以格局可能为空, 但字段必在
    assert "qimen_patterns" in r.raw
    assert "qimen_pattern_count" in r.raw


# ══════════════════════════════════════════════════════════════
# 7. Golden 对照 (《奇门遁甲统宗》案例)
# ══════════════════════════════════════════════════════════════
def test_golden_yanluo_wang_jia_typical_pan():
    """典型凶盘: 庚+乙(白虎猖狂) + 乙+庚(青龙入天牢) + 丙+丙(荧惑入荧).

    复现《奇门遁甲统宗》卷八 案例 1: 三凶格齐出, 大凶.
    """
    t = {"坎": "庚", "艮": "乙", "震": "丙"}
    d = {"坎": "乙", "艮": "庚", "震": "丙"}
    ctx = {"day_gan": "乙"}
    res = detect_patterns(t, d, ctx)
    ids = {p.id for p in res}
    assert "baihu_changkuang" in ids
    assert "qinglong_rutianlao" in ids
    assert "yinghuo_ruying" in ids


def test_golden_qinglong_feiniao_jixiong_pan():
    """典型吉盘: 甲+戊(青龙返首) + 甲+庚(飞鸟跌穴) + 乙+开门(三诈).

    复现《奇门遁甲统宗》卷七 案例 1: 三吉格齐出, 大吉.
    """
    t = {"坎": "甲", "艮": "甲"}  # 两宫皆甲
    d = {"坎": "戊", "艮": "庚"}
    ctx = {"doors": {"坎": "开门", "艮": "休门"}}
    res = detect_patterns(t, d, ctx)
    ids = {p.id for p in res}
    assert "qinglong_fanshou" in ids
    assert "feiniao_diexue" in ids


# ══════════════════════════════════════════════════════════════
# 8. 错误处理: check_fn 异常时降级
# ══════════════════════════════════════════════════════════════
def test_check_fn_exception_graceful():
    """check_fn 抛异常时, 不破坏主流程 (返回空 + warning log)."""
    from divination.data.qimen_patterns import detect_patterns as _det

    # 构造一个 check_fn 必抛异常的 pattern (临时 patch)
    from divination.data import qimen_patterns as qp_mod

    class BadPattern(QimenPattern):
        def __init__(self):
            super().__init__(
                id="bad_test",
                name="测试坏",
                category="gan_zhi_ju",
                polarity="neutral",
                description="测试用坏 pattern",
                source="《测试》",
                check_fn=lambda t, d, ctx: (_ for _ in ()).throw(RuntimeError("bad")),
            )

    # 临时插入并测试
    orig_table = qp_mod.GANZHI_PATTERN_TABLE
    qp_mod.GANZHI_PATTERN_TABLE = [BadPattern()]
    try:
        # 不抛异常, 仅 warning log
        res = _det({"坎": "甲"}, {"坎": "戊"}, {})
        assert res == []
    finally:
        qp_mod.GANZHI_PATTERN_TABLE = orig_table


# ══════════════════════════════════════════════════════════════
# 9. 数据驱动契约: pattern 与检测逻辑解耦
# ══════════════════════════════════════════════════════════════
def test_pattern_independence():
    """每条 pattern.check_fn 可独立测试 (无需 dataset)."""
    for p in GANZHI_PATTERN_TABLE:
        # 单独调用 check_fn 不抛异常
        try:
            result = p.check_fn({"坎": "甲"}, {"坎": "戊"}, {})
            assert isinstance(result, bool), f"{p.id} 应返回 bool, 实际 {type(result)}"
        except Exception as e:
            # 仅 ctx 缺失可能抛 (如白虎猖狂需 day_gan), 用 None ctx 测
            result = p.check_fn({"坎": "甲"}, {"坎": "戊"}, None)
            assert isinstance(result, bool), f"{p.id} 仍异常: {e}"