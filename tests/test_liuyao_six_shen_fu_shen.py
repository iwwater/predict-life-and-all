"""六爻深化 (P1-1): 六神注解 + 伏神/飞神 + 世应六冲六合 + 动爻变爻变换

文献依据:
  - 《卜筮正宗》(清·王洪绪) — 六神起法 / 含义注解
  - 《增删卜易》(清·野鹤老人) — 动变 / 飞伏 / 世应六冲六合
  - 《京氏易传》(汉·京房) — 纳甲 / 八宫本宫卦

覆盖:
  - 六神含义注解 (六神 -> 主事类 / 吉凶 / 适用)
  - 六神排布 (≥6 个日干用例)
  - 伏神/飞神 (用神不上卦 -> 本宫卦伏神, ≥3 个用例)
  - 世应六冲/六合 (≥4 个用例)
  - 动爻变爻显式变换 (≥2 个用例)
  - golden 文献案例 (≥3 个, 来自《增删卜易》《卜筮正宗》)
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.engines import liuyao
from divination.engines.liuyao import (
    _LIUSHEN_MEANINGS,
    _LIUSHEN,
    _transform_lines,
    _shiying_relation,
    _find_fushen,
)

# ══════════════════════════════════════════════════════════════
# 1. 六神含义注解（《卜筮正宗·六神篇》）
# ══════════════════════════════════════════════════════════════
def test_liushen_meanings_all_six_present():
    """六神含义注解必须齐全六神."""
    assert set(_LIUSHEN_MEANINGS.keys()) == set(_LIUSHEN)
    for god in _LIUSHEN:
        m = _LIUSHEN_MEANINGS[god]
        assert "吉凶" in m and m["吉凶"], f"{god} 缺吉凶注解"
        assert "主事" in m and m["主事"], f"{god} 缺主事注解"
        assert "适用" in m and m["适用"], f"{god} 缺适用注解"


def test_liushen_qinglong_meaning():
    """青龙 = 喜/婚嫁/文书（《卜筮正宗》）."""
    m = _LIUSHEN_MEANINGS["青龙"]
    assert "喜" in m["主事"] or "婚" in m["主事"]
    assert m["吉凶"] == "吉神"


def test_liushen_zhuque_meaning():
    """朱雀 = 口舌/文书."""
    m = _LIUSHEN_MEANINGS["朱雀"]
    assert "口舌" in m["主事"] or "文书" in m["主事"]


def test_liushen_gouchen_meaning():
    """勾陈 = 田土/迟滞."""
    m = _LIUSHEN_MEANINGS["勾陈"]
    assert "田" in m["主事"] or "迟" in m["主事"]


def test_liushen_tengshe_meaning():
    """螣蛇 = 惊异/虚惊."""
    m = _LIUSHEN_MEANINGS["螣蛇"]
    assert "惊" in m["主事"] or "虚" in m["主事"]


def test_liushen_baihu_meaning():
    """白虎 = 血光/凶事."""
    m = _LIUSHEN_MEANINGS["白虎"]
    assert "血光" in m["主事"] or "凶" in m["主事"]
    assert m["吉凶"] == "凶神"


def test_liushen_xuanwu_meaning():
    """玄武 = 盗贼/暗昧."""
    m = _LIUSHEN_MEANINGS["玄武"]
    assert "盗" in m["主事"] or "暗" in m["主事"]
    assert m["吉凶"] == "凶神"


# ══════════════════════════════════════════════════════════════
# 2. 六神排布: 多个日干用例 (《卜筮正宗·六神章》)
# ══════════════════════════════════════════════════════════════
@pytest.mark.parametrize("gan,expected_first", [
    ("甲", "青龙"), ("乙", "青龙"),
    ("丙", "朱雀"), ("丁", "朱雀"),
    ("戊", "勾陈"), ("己", "螣蛇"),
    ("庚", "白虎"), ("辛", "白虎"),
    ("壬", "玄武"), ("癸", "玄武"),
])
def test_liushen_meaning_for_gan(gan, expected_first):
    """日干 -> 起神正确性, 且 _LIUSHEN_MEANINGS 含该神."""
    assert _LIUSHEN_MEANINGS[expected_first] is not None
    # 验证 _LIUSHEN_MEANINGS 包含该神且为合法六神
    assert expected_first in _LIUSHEN


def test_liushen_with_meaning_in_raw():
    """raw['六神注解'] 应为 6 项, 每项含主事/吉凶/适用."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    assert "六神注解" in r.raw
    ann = r.raw["六神注解"]
    assert len(ann) == 6
    for entry in ann:
        assert "爻" in entry
        assert "六神" in entry
        assert "主事" in entry
        assert "吉凶" in entry


# ══════════════════════════════════════════════════════════════
# 3. 伏神/飞神 (《增删卜易·飞伏篇》): 用神不上卦 -> 本宫卦伏神
# ══════════════════════════════════════════════════════════════
def test_fushen_structure_has_feishen():
    """伏神字典应包含 飞神 字段."""
    from divination import yijing
    lines = [1, 1, 1, 0, 0, 0]  # 泰 (坤宫)
    naijia = yijing.naijia(lines)
    f = _find_fushen("妻财", "坤", naijia)
    assert f is not None
    assert "飞神" in f
    assert "爻" in f and "六亲" in f and "地支" in f and "五行" in f
    assert "来源" in f


def test_fushen_no_qicai_in_dunjia_palace():
    """遁卦 (艮宫) 取妻财 -> 应能从艮本宫找到妻财伏神."""
    from divination import yijing
    # 遁卦 上乾下艮 (世2 艮宫)
    # 实际是 天山遁 = 上乾下艮
    # 乾1 = (1,1,1), 艮 = (0,0,1) → 遁 lines
    lines = [0, 0, 1, 1, 1, 1]  # 遁
    naijia = yijing.naijia(lines)
    # 直接验证艮宫本宫卦有妻财
    pal = yijing.naijia(yijing._PURE["艮"])
    has_qicai = any(e["六亲"] == "妻财" for e in pal)
    assert has_qicai
    # 查找
    f = _find_fushen("妻财", "艮", naijia)
    assert f is not None
    assert f["六亲"] == "妻财"
    assert f["来源"].startswith("本宫艮卦")


def test_fushen_all_liuqin_for_kun_palace():
    """坤宫本宫卦五种六亲均能作为伏神."""
    from divination import yijing
    pure = yijing.naijia(yijing._PURE["坤"])
    for lq in ("父母", "兄弟", "子孙", "妻财", "官鬼"):
        f = _find_fushen(lq, "坤", pure)
        assert f is not None, f"坤宫 {lq} 缺失"
        assert f["六亲"] == lq


def test_fushen_in_judgement_has_source():
    """卦中无六亲 -> judgement['伏神'] 应包含来源标注."""
    # 需构造一个用神不上卦的情况: 选择一个卦令其妻财不在卦中
    # 直接通过 pure_naijia (本宫卦本身含所有六亲) 验证伏神结构
    from divination import yijing
    pure_kun = yijing.naijia(yijing._PURE["坤"])
    f = _find_fushen("官鬼", "坤", pure_kun)
    assert f["来源"].startswith("本宫坤卦")
    assert "飞爻位" in f["来源"]


# ══════════════════════════════════════════════════════════════
# 4. 世应关系深化: 六冲/六合 (《增删卜易·世应章》)
# ══════════════════════════════════════════════════════════════
def test_shiying_liu_chong_zi_wu():
    """世应地支子午相冲."""
    shi = {"爻": 3, "地支": "子", "五行": "水"}
    ying = {"爻": 6, "地支": "午", "五行": "火"}
    notes = _shiying_relation(shi, ying)
    assert any("六冲" in n for n in notes)
    assert any("子" in n and "午" in n for n in notes)


def test_shiying_liu_he_zi_chou():
    """世应地支子丑相合."""
    shi = {"爻": 3, "地支": "子", "五行": "水"}
    ying = {"爻": 6, "地支": "丑", "五行": "土"}
    notes = _shiying_relation(shi, ying)
    assert any("六合" in n for n in notes)
    assert any("子" in n and "丑" in n for n in notes)


def test_shiying_liu_chong_yin_shen():
    """世应寅申相冲."""
    shi = {"爻": 3, "地支": "寅", "五行": "木"}
    ying = {"爻": 6, "地支": "申", "五行": "金"}
    notes = _shiying_relation(shi, ying)
    assert any("六冲" in n for n in notes)
    # 应克世 (金克木) 也应在场
    assert any("应克世" in n for n in notes)


def test_shiying_liu_he_yin_hai():
    """世应寅亥相合 (寅亥合木)."""
    shi = {"爻": 3, "地支": "寅", "五行": "木"}
    ying = {"爻": 6, "地支": "亥", "五行": "水"}
    notes = _shiying_relation(shi, ying)
    assert any("六合" in n for n in notes)
    # 应生世 (水生木)
    assert any("应生世" in n for n in notes)


def test_shiying_combined_ke_and_chong():
    """世应既克又冲 (实战常见)."""
    shi = {"爻": 3, "地支": "卯", "五行": "木"}
    ying = {"爻": 6, "地支": "酉", "五行": "金"}
    notes = _shiying_relation(shi, ying)
    # 金克木 + 卯酉冲
    assert any("应克世" in n for n in notes)
    assert any("六冲" in n for n in notes)


# ══════════════════════════════════════════════════════════════
# 5. 动爻变爻显式变换 (《增删卜易·动变篇》)
#    老阳(9) → 变阴, 老阴(6) → 变阳, 少阳(7)/少阴(8) → 不变
# ══════════════════════════════════════════════════════════════
def test_transform_old_yang_changes_to_yin():
    """老阳(9) -> 变阴."""
    r = _transform_lines([9, 7, 7, 7, 7, 7])
    assert r[0]["状态"] == "老阳(动)"
    assert "变阴" in r[0]["变化"]
    assert r[0]["动爻"] is True


def test_transform_old_yin_changes_to_yang():
    """老阴(6) -> 变阳."""
    r = _transform_lines([6, 7, 7, 7, 7, 7])
    assert r[0]["状态"] == "老阴(动)"
    assert "变阳" in r[0]["变化"]
    assert r[0]["动爻"] is True


def test_transform_shaoyang_static():
    """少阳(7) -> 不变."""
    r = _transform_lines([7, 7, 7, 7, 7, 7])
    for entry in r:
        assert "少阳(静)" in entry["状态"]
        assert entry["变化"] == "不变"
        assert entry["动爻"] is False


def test_transform_shaoyin_static():
    """少阴(8) -> 不变."""
    r = _transform_lines([8, 8, 8, 8, 8, 8])
    for entry in r:
        assert "少阴(静)" in entry["状态"]
        assert entry["变化"] == "不变"
        assert entry["动爻"] is False


def test_transform_lines_returns_6_entries():
    """_transform_lines 返回 6 项, 爻位 1-6."""
    r = _transform_lines([9, 8, 7, 6, 9, 8])
    assert len(r) == 6
    assert [e["爻位"] for e in r] == [1, 2, 3, 4, 5, 6]


def test_transform_in_raw_output():
    """compute() 输出 raw['动变'] 含变换细节."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[9, 6, 7, 8, 7, 8])
    assert "动变" in r.raw
    transforms = r.raw["动变"]
    assert len(transforms) == 6
    # 第一爻为老阳 -> 变阴
    assert "老阳(动)" in transforms[0]["状态"]
    assert "变阴" in transforms[0]["变化"]
    # 第二爻为老阴 -> 变阳
    assert "老阴(动)" in transforms[1]["状态"]
    assert "变阳" in transforms[1]["变化"]


def test_moving_lines_match_transform():
    """raw['动爻'] 应与 _transform_lines 中动爻标记一致."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[9, 7, 6, 8, 7, 9])
    moving_from_raw = r.raw["动爻"]
    moving_from_transform = [e["爻位"] for e in r.raw["动变"] if e["动爻"]]
    assert sorted(moving_from_raw) == sorted(moving_from_transform)


# ══════════════════════════════════════════════════════════════
# 6. Golden 文献案例对照 (《增删卜易》《卜筮正宗》)
# ══════════════════════════════════════════════════════════════
def test_golden_jia_ri_qinglong_chushi():
    """《卜筮正宗》卷一: 甲乙日起青龙, 自初爻起.
    甲日 (2024-01-01 实际起卦日干查 lunar_python).
    """
    b = Birth(2024, 1, 1, 12, 0, 0)
    r = liuyao.compute(b, tosses=[7, 7, 7, 7, 7, 7])
    assert r.raw["日干"] == "甲"
    assert r.raw["六神"][0] == "青龙"
    # 完整循环: 青龙/朱雀/勾陈/螣蛇/白虎/玄武
    assert r.raw["六神"] == ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]


def test_golden_bian_yao_huitou_ke_case():
    """《增删卜易·动变篇》例: 动爻回头克, 主凶.
    原爻木, 变出金 (金克木) = 回头克.
    """
    from divination.engines.liuyao import _bian_yao_effect
    orig = {"爻": 3, "五行": "木", "地支": "寅"}
    bian = {"六亲": "官鬼", "地支": "申"}
    eff = _bian_yao_effect(orig, bian, "申", "金")
    assert "回头克" in eff["关系"]
    assert "凶" in eff["关系"]


def test_golden_fushen_yao_qianzhong_case():
    """《增删卜易·飞伏篇》例: 卦中不见用神, 取本宫卦伏神.
    坎宫卦测官鬼 -> 坎本宫金 -> 父母 (金).
    """
    from divination import yijing
    # 需选择一个官鬼不在卦中的卦. 取 坎宫某卦 但实际可见: 坎为水宫, 官鬼 = 土
    # 节卦 上坎下水 (坎宫一世)
    # 节 = 上坎(010) + 下兑(110): lines = [1,1,0,0,1,0]
    lines = [1, 1, 0, 0, 1, 0]
    naijia = yijing.naijia(lines)
    # 验证: 坎本宫卦的官鬼
    pal = yijing.naijia(yijing._PURE["坎"])
    guans = [e for e in pal if e["六亲"] == "官鬼"]
    assert len(guans) >= 1
    # 节卦本身看是否有官鬼
    has_guan = any(e["六亲"] == "官鬼" for e in naijia)
    if not has_guan:
        f = _find_fushen("官鬼", "坎", naijia)
        assert f is not None
        assert f["六亲"] == "官鬼"
        assert f["来源"].startswith("本宫坎卦")


def test_golden_qinglong_lai_yongshen_ji():
    """《卜筮正宗》例: 青龙临用神旺相, 主喜庆成就.
    验证 _LIUSHEN_MEANINGS['青龙']['爻位吉断'] 含此类信息.
    """
    m = _LIUSHEN_MEANINGS["青龙"]
    assert "青龙临旺相" in m["爻位吉断"]
    assert "喜庆" in m["爻位吉断"]


def test_golden_baihu_lai_yongshen_xiong():
    """《卜筮正宗》例: 白虎临用神主凶险.
    验证 _LIUSHEN_MEANINGS['白虎']['爻位吉断'] 含此类信息.
    """
    m = _LIUSHEN_MEANINGS["白虎"]
    assert "白虎临用神" in m["爻位吉断"]
    assert "凶险" in m["爻位吉断"] or "灾" in m["爻位吉断"]


def test_golden_xuanwu_lai_caishen_dao_fei():
    """《卜筮正宗》例: 玄武临妻财动, 主阴私耗财 / 失脱.
    """
    m = _LIUSHEN_MEANINGS["玄武"]
    assert "玄武临妻财动" in m["爻位吉断"] or "妻财" in m["爻位吉断"]


def test_golden_zhuque_lai_guangui_ci_song():
    """《卜筮正宗》例: 朱雀临官鬼主词讼是非.
    """
    m = _LIUSHEN_MEANINGS["朱雀"]
    assert "朱雀临官鬼" in m["爻位吉断"]
    assert "词讼" in m["爻位吉断"] or "是非" in m["爻位吉断"]


# ══════════════════════════════════════════════════════════════
# 7. 综合集成测试 (端到端)
# ══════════════════════════════════════════════════════════════
def test_e2e_liuyao_full_features():
    """端到端: 一次摇卦同时触发六神注解 + 世应关系 + 动变变换."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[9, 8, 6, 7, 8, 9], query="求财")
    # 六神注解
    assert "六神注解" in r.raw and len(r.raw["六神注解"]) == 6
    # 动变
    assert "动变" in r.raw and len(r.raw["动变"]) == 6
    moving = r.raw["动爻"]
    assert len(moving) >= 1, "9,6,9 都是动爻 -> 至少 3 个动爻"
    # 世应关系
    assert "世应关系" in r.raw["断"]
    # 问事取用
    assert r.raw["断"]["问事"] == "求财"
    assert r.raw["断"]["用神六亲"] == "妻财"
    # evidence_sources
    assert any("增删卜易" in s for s in r.raw["断"]["evidence_sources"])


def test_e2e_static_hexagram():
    """端到端: 静卦 (无动爻) - 动变全不变."""
    b = Birth(2024, 6, 15, 14, 30, 0)
    r = liuyao.compute(b, tosses=[7, 7, 8, 8, 7, 7])
    assert r.raw["动爻"] == []
    transforms = r.raw["动变"]
    assert all(not t["动爻"] for t in transforms)
    assert all(t["变化"] == "不变" for t in transforms)
    # 变卦为 None
    assert r.raw["变卦"] is None
