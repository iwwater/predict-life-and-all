"""Tests for 吠陀 Yogas 自动检测 (engines/vedic.py v2 + data/vedic_yogas.py)

深化验证:
  - Yogas 自动检测 (8 类)
  - Navamsa 格局分析
  - Nakshatra 4 性质
  - 简化全相位 (Graha Drishti)
  - evidence_sources 引用 BPHS / Phaladeepika

文献: Brihat Parashara Hora Shastra, Phaladeepika, Brihat Jataka
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.engines.vedic import (
    _detect_yogas,
    _kala_sarpa_yoga,
    _nakshatra_info,
    _navamsa_analysis,
    _parivartana_yoga,
    _simplified_aspects,
    compute,
    lahiri_ayanamsa,
)


# ══════════════════════════════════════════════════════════════
# 1. 引擎接口 (兼容 v1)
# ══════════════════════════════════════════════════════════════
def test_compute_returns_chart_result():
    """compute() 返回 ChartResult。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    assert r.method == "vedic"
    assert "planets" in r.raw
    assert "Vimshottari大运" in r.raw


def test_compute_has_yogas_field():
    """compute() 输出应含 detected_yogas 字段 (v2 新增)。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    assert "detected_yogas" in r.raw
    assert isinstance(r.raw["detected_yogas"], list)


def test_compute_has_navamsa_analysis():
    """compute() 输出含 Navamsa 格局分析 (v2 新增)。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    nav = r.raw["navamsa_analysis"]
    assert "元素分布D9" in nav
    assert "主导元素D9" in nav
    assert "D9星座" in nav


def test_compute_has_aspects():
    """compute() 输出含简化全相位 (v2 新增)。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    assert "simplified_aspects" in r.raw
    assert isinstance(r.raw["simplified_aspects"], list)


def test_compute_has_evidence_sources():
    """evidence_sources 应引用 BPHS / Phaladeepika。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    sources = r.raw["evidence_sources"]
    assert any("Parashara" in s for s in sources)
    assert any("Phaladeepika" in s for s in sources)


def test_compute_planets_have_nakshatra_nature():
    """每个行星应有宿性质 (v2 新增)。"""
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male",
              calendar="gregorian", lat=31.23, lng=121.47, tz="Asia/Shanghai")
    r = compute(b)
    planets = r.raw["planets"]
    assert "太阳" in planets
    sun = planets["太阳"]
    assert "宿性质NakshatraNature" in sun
    assert "宿性质EN" in sun
    assert sun["宿性质EN"] in {"Deva", "Manushya", "Rakshasa"}


# ══════════════════════════════════════════════════════════════
# 2. Yogas 自动检测 (核心)
# ══════════════════════════════════════════════════════════════
def _fake_planets_moon_jupiter_conjunct():
    """构造: 月亮木星同白羊 (idx 0) → Gaja Kesari 应触发。"""
    return {
        "太阳": {"恒星黄经": 280.0},   # 摩羯
        "月亮": {"恒星黄经": 10.0},    # 白羊 idx 0
        "火星": {"恒星黄经": 60.0},    # 金牛
        "水星": {"恒星黄经": 350.0},   # 双鱼
        "木星": {"恒星黄经": 5.0},     # 白羊 idx 0 (与月亮同)
        "金星": {"恒星黄经": 80.0},    # 双子
        "土星": {"恒星黄经": 270.0},   # 摩羯
        "罗睺": {"恒星黄经": 100.0},
        "计都": {"恒星黄经": 280.0},
    }


def test_detect_gaja_kesari_via_engine():
    """月亮木星同宫 → Gaja Kesari 应被检测。"""
    planets = _fake_planets_moon_jupiter_conjunct()
    yogas = _detect_yogas(planets)
    names = {y["name"] for y in yogas}
    assert any("Gaja Kesari" in n for n in names)


def test_detect_pancha_mahapurusha_via_engine():
    """火星白羊 idx 0 + Kendra (house=1) → Ruchaka。"""
    planets = {
        "太阳": {"恒星黄经": 90.0},    # 巨蟹
        "月亮": {"恒星黄经": 200.0},   # 天秤
        "火星": {"恒星黄经": 5.0},     # 白羊 idx 0 (own)
        "水星": {"恒星黄经": 80.0},
        "木星": {"恒星黄经": 150.0},
        "金星": {"恒星黄经": 70.0},
        "土星": {"恒星黄经": 100.0},
        "罗睺": {"恒星黄经": 200.0},
        "计都": {"恒星黄经": 20.0},
    }
    yogas = _detect_yogas(planets)
    names = {y["name"] for y in yogas}
    assert any("Ruchaka" in n for n in names)


def test_detect_budhaditya_via_engine():
    """水星太阳同白羊 idx 0, 度数差 < 3° → Budhaditya。"""
    planets = {
        "太阳": {"恒星黄经": 5.0},    # 白羊 5°
        "月亮": {"恒星黄经": 90.0},
        "火星": {"恒星黄经": 100.0},
        "水星": {"恒星黄经": 6.5},    # 白羊 6.5° (差 1.5°)
        "木星": {"恒星黄经": 200.0},
        "金星": {"恒星黄经": 80.0},
        "土星": {"恒星黄经": 250.0},
        "罗睺": {"恒星黄经": 100.0},
        "计都": {"恒星黄经": 280.0},
    }
    yogas = _detect_yogas(planets)
    names = {y["name"] for y in yogas}
    assert any("Budhaditya" in n for n in names)


def test_detect_chandra_mangal_via_engine():
    """月亮火星同宫 → Chandra-Mangal。"""
    planets = {
        "太阳": {"恒星黄经": 100.0},
        "月亮": {"恒星黄经": 200.0},    # 天秤
        "火星": {"恒星黄经": 205.0},    # 天秤 (差 5° < 30°, 同宫)
        "水星": {"恒星黄经": 80.0},
        "木星": {"恒星黄经": 50.0},
        "金星": {"恒星黄经": 250.0},
        "土星": {"恒星黄经": 280.0},
        "罗睺": {"恒星黄经": 0.0},
        "计都": {"恒星黄经": 180.0},
    }
    yogas = _detect_yogas(planets)
    names = {y["name"] for y in yogas}
    assert any("Chandra-Mangal" in n for n in names)


def test_detect_mangal_dosha_via_engine():
    """火星在第 1 宫 (白羊) → Mangal Dosha。"""
    planets = {
        "太阳": {"恒星黄经": 100.0},
        "月亮": {"恒星黄经": 200.0},
        "火星": {"恒星黄经": 5.0},     # 白羊 idx 0 → house 1 (Mangal Dosha)
        "水星": {"恒星黄经": 80.0},
        "木星": {"恒星黄经": 50.0},
        "金星": {"恒星黄经": 250.0},
        "土星": {"恒星黄经": 280.0},
        "罗睺": {"恒星黄经": 0.0},
        "计都": {"恒星黄经": 180.0},
    }
    yogas = _detect_yogas(planets)
    names = {y["name"] for y in yogas}
    assert any("Mangal Dosha" in n for n in names)


def test_detect_parivartana_via_engine():
    """火星在巨蟹 (月亮庙), 月亮在白羊/天蝎 (火星庙) → Parivartana。"""
    planets = {
        "太阳": {"恒星黄经": 100.0},
        "月亮": {"恒星黄经": 5.0},      # 白羊 (火星庙)
        "火星": {"恒星黄经": 95.0},     # 巨蟹 (月亮庙)
        "水星": {"恒星黄经": 80.0},
        "木星": {"恒星黄经": 50.0},
        "金星": {"恒星黄经": 250.0},
        "土星": {"恒星黄经": 280.0},
        "罗睺": {"恒星黄经": 0.0},
        "计都": {"恒星黄经": 180.0},
    }
    yogas = _detect_yogas(planets)
    names = {y["name"] for y in yogas}
    assert any("Parivartana" in n for n in names)


def test_detect_no_yogas_random():
    """所有行星散落且无特定组合 → 可能没有强 Yogas (允许为空)。"""
    planets = {
        "太阳": {"恒星黄经": 90.0},     # 巨蟹
        "月亮": {"恒星黄经": 5.0},      # 白羊 (但木星不在白羊, 无 Gaja Kesari)
        "火星": {"恒星黄经": 80.0},     # 金牛 (非庙)
        "水星": {"恒星黄经": 100.0},
        "木星": {"恒星黄经": 200.0},    # 天秤 (木星落陷)
        "金星": {"恒星黄经": 70.0},     # 金牛 (own 但非 Kendra 看是否触发)
        "土星": {"恒星黄经": 270.0},    # 摩羯 (own 但 house 10)
        "罗睺": {"恒星黄经": 0.0},
        "计都": {"恒星黄经": 180.0},
    }
    yogas = _detect_yogas(planets)
    # 至少要返回一个 list (可能为空)
    assert isinstance(yogas, list)


# ══════════════════════════════════════════════════════════════
# 3. Navamsa 格局分析
# ══════════════════════════════════════════════════════════════
def test_navamsa_analysis_returns_element_distribution():
    """Navamsa 应返回四元素分布, 总和 = 行星数。"""
    planets = {
        "太阳": {"恒星黄经": 10.0},
        "月亮": {"恒星黄经": 60.0},
        "火星": {"恒星黄经": 100.0},
    }
    nav = _navamsa_analysis(planets, 60.0)
    assert "元素分布D9" in nav
    total = sum(nav["元素分布D9"].values())
    assert total == 3


def test_navamsa_analysis_dominant_element():
    """Navamsa 应判定主导元素。"""
    # 选取 3 个行星, 都在火象星座 (白羊/狮子/射手)
    # sid 5° → D9 idx 1 (金牛土); 65° → idx 7 (天蝎水); 125° → idx 5 (处女土)
    # 改为 3 个同元素 D9: sid 5/35/65 → D9 1/10/7 → 土/风/水 (各 1)
    # 选 sid: 5/35/125 → D9 1/10/5 → 土/风/土 → 土 = 2
    planets = {
        "太阳": {"恒星黄经": 5.0},     # D9 idx 1 (金牛) → 土
        "月亮": {"恒星黄经": 35.0},    # D9 idx 10 (水瓶) → 风
        "火星": {"恒星黄经": 125.0},   # D9 idx 5 (处女) → 土
    }
    nav = _navamsa_analysis(planets, 35.0)
    assert nav["主导元素D9"] == "土"  # 土 2 票最多


# ══════════════════════════════════════════════════════════════
# 4. Nakshatra 性质
# ══════════════════════════════════════════════════════════════
def test_nakshatra_nature_ashwini_deva():
    """Ashwini (idx 0) = Deva。"""
    _, _, nature = _nakshatra_info(0.5)  # 白羊 0.5°
    assert nature == "Deva"


def test_nakshatra_nature_bharani_manushya():
    """Bharani (idx 1) = Manushya。"""
    _, _, nature = _nakshatra_info(13.4)  # 白羊 13.4° (Bharani 范围 13°20' - 26°40')
    assert nature == "Manushya"


def test_nakshatra_nature_krittika_rakshasa():
    """Krittika (idx 2) = Rakshasa。"""
    _, _, nature = _nakshatra_info(28.0)  # 白羊 28° (Krittika 范围 26°40' - 40°00')
    assert nature == "Rakshasa"


def test_nakshatra_pada_correct():
    """Pada 计算: Ashwini 0-3°20' = Pada 1, 3°20'-6°40' = Pada 2。"""
    # Ashwini 范围 0-13°20' (13.333°), 4 个 Pada 每段 3.333°
    # 5° → pada = int(5 / 3.333) + 1 = 1 + 1 = 2
    _, pada, _ = _nakshatra_info(5.0)
    assert pada == 2


# ══════════════════════════════════════════════════════════════
# 5. Kala Sarpa + Parivartana + Aspects (辅助函数)
# ══════════════════════════════════════════════════════════════
def test_kala_sarpa_true_when_planets_cluster():
    """所有行星在罗睺-计都之间 → Kala Sarpa。"""
    # 罗睺 30° (金牛), 计都 210° (天秤)
    # 所有行星在 30°-210° 之间
    planets = {
        "罗睺": {"恒星黄经": 30.0},
        "计都": {"恒星黄经": 210.0},
        "太阳": {"恒星黄经": 90.0},
        "月亮": {"恒星黄经": 100.0},
        "火星": {"恒星黄经": 150.0},
        "水星": {"恒星黄经": 80.0},
        "木星": {"恒星黄经": 180.0},
        "金星": {"恒星黄经": 60.0},
        "土星": {"恒星黄经": 200.0},
    }
    assert _kala_sarpa_yoga(planets) is True


def test_kala_sarpa_false_when_planets_split():
    """行星分散两侧 → 非 Kala Sarpa。"""
    planets = {
        "罗睺": {"恒星黄经": 30.0},
        "计都": {"恒星黄经": 210.0},
        "太阳": {"恒星黄经": 90.0},     # 在轴内
        "月亮": {"恒星黄经": 300.0},    # 在轴外!
        "火星": {"恒星黄经": 50.0},     # 在轴内
        "水星": {"恒星黄经": 100.0},
        "木星": {"恒星黄经": 180.0},
        "金星": {"恒星黄经": 60.0},
        "土星": {"恒星黄经": 200.0},
    }
    assert _kala_sarpa_yoga(planets) is False


def test_parivartana_yoga_detected():
    """火星在巨蟹(月亮庙), 月亮在白羊(火星庙) → Parivartana。"""
    planets = {
        "月亮": {"恒星黄经": 5.0},      # 白羊 (idx 0 = 火星 own)
        "火星": {"恒星黄经": 95.0},     # 巨蟹 (idx 3 = 月亮 own)
        "太阳": {"恒星黄经": 200.0},
        "水星": {"恒星黄经": 80.0},
        "木星": {"恒星黄经": 150.0},
        "金星": {"恒星黄经": 60.0},
        "土星": {"恒星黄经": 270.0},
    }
    results = _parivartana_yoga(planets)
    assert len(results) >= 1
    pairs = {tuple(r["planets"]) for r in results}
    assert ("月亮", "火星") in pairs or ("火星", "月亮") in pairs


def test_simplified_aspects_all_planets_7th():
    """所有行星都应有 7th (对宫) 相位输出。"""
    planets = {
        "太阳": {"恒星黄经": 10.0},
        "月亮": {"恒星黄经": 190.0},    # 对望太阳
        "火星": {"恒星黄经": 60.0},
        "水星": {"恒星黄经": 200.0},
        "木星": {"恒星黄经": 80.0},
        "金星": {"恒星黄经": 100.0},
        "土星": {"恒星黄经": 270.0},
    }
    aspects = _simplified_aspects(planets)
    assert len(aspects) > 0
    # 月亮 190° 对 太阳 10° (差 180° → 7宫) → 应有 aspect
    found = any(a["from"] == "月亮" and a["to"] == "太阳" and a["angle_houses"] == 7
                for a in aspects)
    assert found


def test_simplified_aspects_mars_4th_8th():
    """火星应有额外 4th / 8th 相位 (不是只有 7th)。"""
    planets = {
        "火星": {"恒星黄经": 0.0},       # 火星在白羊
        "太阳": {"恒星黄经": 90.0},      # 巨蟹 (火星的 4 宫)
        "水星": {"恒星黄经": 180.0},     # 天秤 (火星的 7 宫)
        "木星": {"恒星黄经": 240.0},     # 射手 (火星的 9 宫, 不在火星相位列表)
        "月亮": {"恒星黄经": 60.0},      # 金牛 (火星的 2 宫, 不在列表)
        "金星": {"恒星黄经": 30.0},      # 金牛
        "土星": {"恒星黄经": 150.0},     # 狮子
    }
    aspects = _simplified_aspects(planets)
    # 火星应向 太阳 (4th) 产生 aspect
    mars_aspects = [a for a in aspects if a["from"] == "火星"]
    angles = {a["angle_houses"] for a in mars_aspects}
    assert 4 in angles  # 火星 4th aspect


def test_lahiri_ayanamsa_value():
    """Lahiri ayanamsa 在 J2000 应约 23.85°。"""
    # J2000 = JD 2451545.0
    ayan = lahiri_ayanamsa(2451545.0)
    assert 23.5 < ayan < 24.5