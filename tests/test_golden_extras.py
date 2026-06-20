"""Sprint 0.7 Golden Tests 扩展 —— 文献/天文/概率分布的回归守护。

总计：12 个测试，扩展现有 18 个 golden 测试至 ≥30 个。
覆盖：揲蓍四象概率、Vimshottari 总和/顺序/各段年数、塔罗 seed 复现/牌张唯一性/
牌阵位置数、六爻铜钱概率分布、六爻乾为天六亲分布、八卦五行映射、天干五行表、
二十四山唯一性、西占春分点聚合、五档极性/ScopeTally。

约束：
  - 不修改 divination/ 下任何代码
  - 如发现实际代码行为与注释/经典不符，写 known-issue 测试 + 注释说明
"""
import random
import pytest

from divination import Birth, compute
from divination import yijing as Y
from divination import fengshui as FS
from divination import wuxing as WX
from divination.engines import shicao as SHICAO
from divination.engines import vedic as VEDIC
from divination.engines import liuyao as LIUYAO
from divination.engines import tarot as TAROT


# ─────────────────────────────────────────────────────────────────────────
# 1. 揲蓍四象概率分布（divination/engines/shicao.py）
# ─────────────────────────────────────────────────────────────────────────

def test_shicao_yarrow_distribution_uniform_4象():
    """揲蓍 _yarrow_lines 单爻经验分布 — known issue：实测 = 1/3 / 1/4 / 1/4 / 0
    而非经典 3/16 / 5/16 / 7/16 / 1/16。

    源码分析：_one_yarrow 使用 randint(4,7) 均匀选 q∈{4,5,6,7} → m∈{33,29,25,21}，
    但 _YARROW_MAP 仅定义 {37,33,29,25}，q=7 时 m=21 走默认 line_val=7。
    所以 line_value=6 (老阴) 实际不可达；三象分布为 {7: 1/3, 8: 1/4, 9: 1/4}。

    断言：记录"实测"分布作为 known-issue 守护，触发未来重写时回归告警。
    """
    rng = random.Random(0)
    counts = {6: 0, 7: 0, 8: 0, 9: 0}
    N = 32000
    for _ in range(N):
        r = SHICAO._yarrow_lines(rng, 1)
        counts[r[0]["line_value"]] += 1
    freq = {k: v / N for k, v in counts.items()}
    # known-issue 守护：line_val=6 频率 ≈ 0（代码 _YARROW_MAP 缺 m=21 分支）
    assert freq[6] < 0.01, f"老阴不可达，已实测 ≈0; 实际 {freq[6]:.4f}"
    # 7 出现约 1/3（含 m=33 + m=21 默认两条路径）
    assert 0.40 < freq[7] < 0.58, f"少阳应≈0.50(1/3+1/4默认路径)，实际 {freq[7]:.4f}"
    # 8/9 各约 1/4
    assert 0.20 < freq[8] < 0.32, f"少阴应≈0.25，实际 {freq[8]:.4f}"
    assert 0.20 < freq[9] < 0.32, f"老阳应≈0.25，实际 {freq[9]:.4f}"


# ─────────────────────────────────────────────────────────────────────────
# 2 & 13. Vimshottari Dasha 总和=120 + 9 段年数顺序
# ─────────────────────────────────────────────────────────────────────────

def test_vimshottari_dasha_sum_is_120():
    """吠陀 Vimshottari 大运 9 段总和必须 = 120 年。"""
    assert sum(yrs for _, yrs in VEDIC._DASHA) == 120, "Vimshottari 9 段总和必须=120"


def test_vimshottari_dasha_each_year_count():
    """Vimshottari 各段年数: 7,20,6,10,7,18,16,19,17（实际 _DASHA 顺序）。"""
    expected = [7, 20, 6, 10, 7, 18, 16, 19, 17]
    actual = [yrs for _, yrs in VEDIC._DASHA]
    assert actual == expected, f"Dasha 年数应为 {expected}, 实际 {actual}"


# ─────────────────────────────────────────────────────────────────────────
# 3. Vimshottari 9 段顺序（实际 _DASHA 顺序，与经典"星座起运"顺序略有差异）
# ─────────────────────────────────────────────────────────────────────────

def test_vimshottari_dasha_order():
    """9 段顺序（按实际代码 _DASHA 起首：计都）。
    known-issue：与某些教材"太阳→月亮→..."的首段不同。
    实际顺序：计都, 金星, 太阳, 月亮, 火星, 罗睺, 木星, 土星, 水星。
    """
    expected = ["计都", "金星", "太阳", "月亮", "火星", "罗睺", "木星", "土星", "水星"]
    actual = [VEDIC._DASHA_CN[lord] for lord, _ in VEDIC._DASHA]
    assert actual == expected, f"Dasha 顺序应为 {expected}, 实际 {actual}"


# ─────────────────────────────────────────────────────────────────────────
# 4 & 5. 塔罗同 seed 复现 + 78 张唯一性
# ─────────────────────────────────────────────────────────────────────────

def test_tarot_same_seed_same_deck():
    """同 seed 抽到相同牌组 + 方位。"""
    b = Birth(1990, 5, 15, 12, 0, gender="unspecified")
    r1 = compute("tarot", b, spread="single", seed="test_seed_repro")
    r2 = compute("tarot", b, spread="single", seed="test_seed_repro")
    cards1 = [(c["牌"], c["方位"]) for c in r1.raw["牌面"]]
    cards2 = [(c["牌"], c["方位"]) for c in r2.raw["牌面"]]
    assert cards1 == cards2, f"同 seed 应得相同牌组, r1={cards1}, r2={cards2}"


def test_tarot_78_unique_cards():
    """78 张牌：22 大阿卡纳 + 56 小阿卡纳（4 花色 × 14 阶），且牌名唯一。"""
    from divination.engines.tarot import _build_deck
    deck = _build_deck()
    assert len(deck) == 78, f"应为 78 张, 实际 {len(deck)}"
    names = [c["牌"] for c in deck]
    assert len(set(names)) == 78, f"有重复牌名, 唯一名数={len(set(names))}"
    major = [c for c in deck if c["类别"] == "大阿卡纳"]
    minor = [c for c in deck if c["类别"] != "大阿卡纳"]
    assert len(major) == 22
    assert len(minor) == 56


# ─────────────────────────────────────────────────────────────────────────
# 6. 六爻铜钱概率（理论 9/6 各 1/8, 7/8 各 3/8）
# ─────────────────────────────────────────────────────────────────────────

def test_liuyao_coin_distribution():
    """六爻三钱法经验分布：9,6 各 ≈ 1/8；7,8 各 ≈ 3/8。"""
    b = Birth(1990, 5, 15, 8, 30, gender="male")
    counts = {6: 0, 7: 0, 8: 0, 9: 0}
    N = 8000
    for i in range(N):
        # 用不同 seed 保证独立采样（避免 lru_cache 单次结果复用）
        r = compute("liuyao", b, seed=i * 7919 + 1)
        for t in r.raw["摇钱"]:
            counts[t] += 1
    total = sum(counts.values())
    freq = {k: v / total for k, v in counts.items()}
    # 9/6 理论 0.125, 区间 [0.10, 0.16]
    assert 0.10 <= freq[9] <= 0.16, f"老阳应≈0.125, 实际 {freq[9]:.4f}"
    assert 0.10 <= freq[6] <= 0.16, f"老阴应≈0.125, 实际 {freq[6]:.4f}"
    # 7/8 理论 0.375, 区间 [0.34, 0.42]
    assert 0.34 <= freq[7] <= 0.42, f"少阳应≈0.375, 实际 {freq[7]:.4f}"
    assert 0.34 <= freq[8] <= 0.42, f"少阴应≈0.375, 实际 {freq[8]:.4f}"


# ─────────────────────────────────────────────────────────────────────────
# 7. 乾为天卦（金宫）六亲分布回归
# ─────────────────────────────────────────────────────────────────────────

def test_qian_liuqin_full_set():
    """乾为天（6 阳爻全 7）金宫六亲应覆盖兄弟/父母/子孙/妻财/官鬼全部 5 类。"""
    lines = [1, 1, 1, 1, 1, 1]
    naijia = Y.naijia(lines)
    liuqin_set = {e["六亲"] for e in naijia}
    expected = {"兄弟", "父母", "子孙", "妻财", "官鬼"}
    assert liuqin_set == expected, (
        f"乾为天六亲应为全集 {expected}, 实际 {liuqin_set}"
    )
    # 卦宫与世爻
    hex_info = Y.hexagram_name(lines)
    assert hex_info["name"] == "乾"
    shiying = Y.palace_shiying(hex_info["name"])
    assert shiying["宫"] == "乾"
    assert shiying["宫五行"] == "金"
    assert shiying["世"] == 6 and shiying["应"] == 3


# ─────────────────────────────────────────────────────────────────────────
# 8. 八卦五行映射（yijing.py）
# ─────────────────────────────────────────────────────────────────────────

def test_palace_wuxing_mapping():
    """后天八卦五行（文王序）：乾兑金、离火、震巽木、坎水、艮坤土。"""
    assert Y._GONG_WUXING["乾"] == "金"
    assert Y._GONG_WUXING["兑"] == "金"
    assert Y._GONG_WUXING["离"] == "火"
    assert Y._GONG_WUXING["震"] == "木"
    assert Y._GONG_WUXING["巽"] == "木"
    assert Y._GONG_WUXING["坎"] == "水"
    assert Y._GONG_WUXING["艮"] == "土"
    assert Y._GONG_WUXING["坤"] == "土"


# ─────────────────────────────────────────────────────────────────────────
# 9. 天干五行表（阴阳干同五行）
# ─────────────────────────────────────────────────────────────────────────

def test_gan_wuxing_table():
    """十天干五行表：阴阳干同五行。"""
    assert WX.GAN_WX["甲"] == "木" and WX.GAN_WX["乙"] == "木"
    assert WX.GAN_WX["丙"] == "火" and WX.GAN_WX["丁"] == "火"
    assert WX.GAN_WX["戊"] == "土" and WX.GAN_WX["己"] == "土"
    assert WX.GAN_WX["庚"] == "金" and WX.GAN_WX["辛"] == "金"
    assert WX.GAN_WX["壬"] == "水" and WX.GAN_WX["癸"] == "水"
    assert len(WX.GAN_WX) == 10


# ─────────────────────────────────────────────────────────────────────────
# 10. 二十四山表 24 项唯一
# ─────────────────────────────────────────────────────────────────────────

def test_24_mountains_unique_24():
    """二十四山（玄空飞星坐向）— 24 项且唯一，含三元龙阴阳标注。"""
    assert len(FS._ORDER24) == 24, f"应有 24 山, 实际 {len(FS._ORDER24)}"
    assert len(set(FS._ORDER24)) == 24, f"二十四山有重复: {FS._ORDER24}"
    # 对宫关系（facing_of）
    for s in ["子", "午", "卯", "酉", "乾", "巽"]:
        assert FS.facing_of(s) != s
        assert FS.facing_of(FS.facing_of(s)) == s
    # 三元龙覆盖
    assert len(FS._MOUNTAINS) == 24


# ─────────────────────────────────────────────────────────────────────────
# 11. 塔罗牌阵位置数
# ─────────────────────────────────────────────────────────────────────────

def test_tarot_spreads_position_counts():
    """9 牌阵位置数契约：single=1, three=3, situation=3, decision=5,
    relationship=6, horseshoe=7, mind_body_spirit=3, year_ahead=12, celtic=10。"""
    expected = {
        "single": 1, "three": 3, "situation": 3, "decision": 5,
        "relationship": 6, "horseshoe": 7, "mind_body_spirit": 3,
        "year_ahead": 12, "celtic": 10,
    }
    assert set(TAROT._SPREADS) == set(expected), (
        f"牌阵缺失/多余: 缺={set(expected)-set(TAROT._SPREADS)}, 多={set(TAROT._SPREADS)-set(expected)}"
    )
    for k, v in expected.items():
        assert len(TAROT._SPREADS[k]["positions"]) == v, (
            f"{k} 应有 {v} 位置, 实际 {len(TAROT._SPREADS[k]['positions'])}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 12. 西占春分点（2026-03-20 UTC 太阳入白羊 0°）
# ─────────────────────────────────────────────────────────────────────────

def test_western_vernal_equinox_2026():
    """2026-03-20 UTC 12:00 太阳黄经应在 [355°, 5°] 之间（跨 0° 入白羊）。"""
    b = Birth(2026, 3, 20, 12, 0, lat=0, lng=0, tz="UTC")
    r = compute("western", b)
    sun_lon = r.raw["planets"]["太阳"]["lon"]
    # 跨 0° 检查：min(|lon|, |lon-360|) < 5
    delta = min(sun_lon, 360 - sun_lon)
    assert delta < 5.0, f"春分点 sun_lon 应≈0°, 实际 {sun_lon:.4f}°"
    # 顺带断言太阳在双鱼/白羊交界
    assert r.raw["planets"]["太阳"]["sign"] in ("双鱼", "白羊")


# ─────────────────────────────────────────────────────────────────────────
# 14 & 15. 五档极性枚举 + ScopeTally 五 scope
# ─────────────────────────────────────────────────────────────────────────

def test_dimension_polarity_enum_values():
    """DimensionPolarity 五档枚举值精确匹配。"""
    from divination.aggregation.schema import DimensionPolarity
    assert {p.value for p in DimensionPolarity} == {
        "strong_support", "weak_support", "neutral", "weak_warn", "strong_warn",
    }


def test_time_scope_literal_all_six():
    """ScopeTally 接受全部 6 个 TimeScope 字面值。"""
    from divination.aggregation.schema import ScopeTally
    six_scopes = (
        "long_term", "current_cycle", "short_term",
        "space", "one_question", "relationship",
    )
    for sc in six_scopes:
        t = ScopeTally(scope=sc)
        assert t.scope == sc, f"scope={sc} 不匹配, 实际={t.scope}"