"""文献层 golden：奇门三元定局/64卦/纳甲六亲(含卦宫bug回归)/八宫世应/玄空名局/称骨/吠陀。"""
import pytest
from divination import Birth, compute
from divination import yijing as Y


def _mk(up, lo):
    B = {"乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
         "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0)}
    return list(B[lo]) + list(B[up])


@pytest.mark.parametrize("up,lo,name", [
    ("乾", "乾", "乾"), ("坤", "乾", "泰"), ("乾", "坤", "否"), ("坎", "离", "既济"),
    ("离", "坎", "未济"), ("坎", "震", "屯"), ("艮", "坎", "蒙"), ("离", "乾", "大有")])
def test_64gua_table(up, lo, name):
    assert Y.hexagram_name(_mk(up, lo))["name"] == name


def test_najia_jin_palace_bug_regression():
    """回归：六亲须以京房卦宫五行论（晋=乾宫金），曾误用上卦（离火）致六亲全错。"""
    got = [(e["地支"], e["六亲"]) for e in Y.naijia(_mk("离", "坤"))]
    assert got == [("未", "父母"), ("巳", "官鬼"), ("卯", "妻财"),
                   ("酉", "兄弟"), ("未", "父母"), ("巳", "官鬼")]


def test_palace_shiying():
    expect = {"乾": 6, "姤": 1, "遯": 2, "否": 3, "观": 4, "剥": 5, "晋": 4, "大有": 3}
    for k, v in expect.items():
        assert Y.palace_shiying(k)["世"] == v and Y.palace_shiying(k)["宫"] == "乾"
    assert len(Y.PALACE_INDEX) == 64


@pytest.mark.parametrize("ymdh,jq,yy,sanyuan", [
    ((2024, 6, 1, 14), "小满", "阳", (5, 2, 8)), ((2024, 12, 25, 10), "冬至", "阳", (1, 7, 4)),
    ((2023, 3, 25, 8), "春分", "阳", (3, 9, 6)), ((2024, 8, 10, 16), "立秋", "阴", (2, 5, 8)),
    ((2024, 10, 15, 9), "寒露", "阴", (6, 9, 3))])
def test_qimen_sanyuan(ymdh, jq, yy, sanyuan):
    """《烟波钓叟歌》二十四节气三元定局。"""
    CN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    r = compute("qimen", Birth(*ymdh, 0, gender="male")).raw
    assert r["节气"] == jq
    assert r["排局"][0] == yy
    ju = next(CN[c] for c in r["排局"] if c in CN)
    assert ju in sanyuan


@pytest.mark.parametrize("sitting,pattern_kw", [
    ("子", "双星到向"), ("午", "双星到坐"), ("丑", "旺山旺向"), ("未", "旺山旺向")])
def test_xuankong_period8(sitting, pattern_kw):
    """《沈氏玄空学》八运名局。"""
    r = compute("xuankong", Birth(2000, 1, 1, gender="male"), period=8, sitting=sitting).raw
    assert any(pattern_kw in p for p in r["格局"])


def test_xuankong_zi_double8():
    r = compute("xuankong", Birth(2000, 1, 1, gender="male"), period=8, sitting="子").raw
    assert r["向首"] == {"山星": 8, "向星": 8}


def test_bazi_pillars_and_strength():
    b = Birth(1990, 5, 15, 8, 30, gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute("bazi", b).raw
    assert r["pillars"] == {"year": "庚午", "month": "辛巳", "day": "庚辰", "hour": "庚辰"}
    s = r["断"]["旺衰"]
    assert s["得地"] is True            # 巳藏庚，金长生
    assert s["强弱"] in ("中和", "偏弱")  # 多因子合理区间


def test_bazi_zi_hour_switch():
    b = Birth(1990, 5, 15, 23, 30, gender="male")
    late = compute("bazi", b, zi_hour="late").raw["pillars"]["day"]
    early = compute("bazi", b, zi_hour="early").raw["pillars"]["day"]
    assert late == "庚辰" and early == "辛巳"


def test_vedic_dasha_total_and_navamsa():
    from divination.engines.vedic import _DASHA, _navamsa
    assert sum(y for _, y in _DASHA) == 120
    assert _navamsa(0) == "白羊" and _navamsa(30) == "摩羯" and _navamsa(120) == "白羊"


def test_chenggu_deterministic():
    b = Birth(1990, 5, 15, 8, 30, gender="male")
    assert compute("chenggu", b).raw["总骨重_两"] == 3.7


def test_tarot_deck_integrity():
    from divination.engines.tarot import _build_deck
    d = _build_deck()
    assert len(d) == 78 and len({c["牌"] for c in d}) == 78
    assert all(c["正位"] and c["逆位"] for c in d)


def test_tarot_spreads_complete():
    """9 牌阵：位置数正确、要领/适用齐全、抽牌张数=位置数、同 seed 确定性。"""
    from divination.engines.tarot import _SPREADS
    expect_n = {"single": 1, "three": 3, "situation": 3, "decision": 5,
                "relationship": 6, "horseshoe": 7, "mind_body_spirit": 3,
                "year_ahead": 12, "celtic": 10}
    assert set(_SPREADS) == set(expect_n)
    for k, sp in _SPREADS.items():
        assert len(sp["positions"]) == expect_n[k]
        assert sp["guide"] and sp["fit"] and sp["名称"]
    b = Birth(1990, 5, 15, 8, 30, gender="male")
    for k in _SPREADS:
        r1 = compute("tarot", b, spread=k, seed=42).raw
        r2 = compute("tarot", b, spread=k, seed=42).raw
        assert len(r1["牌面"]) == expect_n[k]
        assert [(c["牌"], c["方位"]) for c in r1["牌面"]] == \
               [(c["牌"], c["方位"]) for c in r2["牌面"]]
        # 同一阵内无重复牌
        assert len({c["牌"] for c in r1["牌面"]}) == expect_n[k]


def test_hepan_yuanyang_and_chong():
    """合婚定数：甲子×己丑=天地鸳鸯合；庚子×丙午=干克+六冲。"""
    from divination.engines.hepan import analyze_bazi_hehun
    r = analyze_bazi_hehun(
        {"year": "庚午", "month": "戊子", "day": "甲子", "hour": "甲子"},
        {"year": "乙丑", "month": "己丑", "day": "己丑", "hour": "乙丑"})
    assert r["鸳鸯合"] is True
    assert r["日柱"]["日干"]["关系"] == "天干五合"
    r2 = analyze_bazi_hehun(
        {"year": "庚子", "month": "戊子", "day": "庚子", "hour": "丙子"},
        {"year": "丙午", "month": "甲午", "day": "丙午", "hour": "戊午"})
    assert "六冲" in r2["日柱"]["日支"]["关系"]
    assert r2["日柱"]["日干"]["评"] == "下"


def test_hepan_end_to_end():
    """合盘端到端：结构完整、维度档位制、印证/分歧二选一。"""
    a = Birth(1990, 5, 15, 8, 30, gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    p = Birth(1992, 9, 21, 14, 0, gender="female", lat=39.9, lng=116.4, tz="Asia/Shanghai")
    r = compute("hepan", a, partner=p).raw
    assert set(r["维度评级"]) == {"性格相处", "情感吸引", "长期稳定", "互补成长"}
    assert all(v in ("高", "中", "低") for v in r["维度评级"].values())
    assert (r["印证"] is None) != (r["分歧"] is None)  # 恰一个
    assert "关键相位" in r["西方合盘"]
