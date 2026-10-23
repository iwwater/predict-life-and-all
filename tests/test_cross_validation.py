"""交叉验证器接线测试 —— 确保 divination/engines/cross_validator.py 的
875 行实现真正参与 /api/compute/multi, 而不是躺在仓库里当死代码。

覆盖三层:
1. 特征提取器对真实引擎 raw 结构的容错(英文五行键 / 紫微宫名无"宫"后缀 /
   西方星座无"座"后缀、相位带"相"后缀);
2. compute_with_validation 的输出契约(ensemble_score 是 0-100 / 单法不伪造高分 /
   数据不足返回 insufficient_data);
3. /api/compute/multi 端点端到端。
"""
from fastapi.testclient import TestClient

from divination.contracts import Birth
from divination.engines.cross_validator import (
    extract_bazi_features,
    extract_western_features,
    extract_ziwei_features,
)
from divination.router import compute_with_validation
from server.main import app

client = TestClient(app)
BIRTH = Birth(1990, 6, 15, 8, 30, gender="male")


# ── 1. 特征提取 ────────────────────────────────────────────────────────
def test_extract_bazi_v2_english_element_keys():
    """bazi_v2 的五行是英文键 elements_total, 必须归一成中文五行。"""
    raw = {
        "day_master": "辛",
        "elements_total": {"metal": 2.0, "wood": 0.6, "water": 3.1, "fire": 1.6, "earth": 1.4},
        "pattern": {"pattern": "食伤格"},
        "yong_shen": {"primary_zh": ["土", "金"]},
        "pillars": {"day": {"ganzhi": "辛亥"}},
        "strength_score": 32.0,
    }
    f = extract_bazi_features(raw)
    assert f["day_master"] == "辛"
    assert f["day_master_element"] == "金"
    assert f["dominant_element"] == "水"
    assert f["weak_element"] == "木"
    assert f["pattern"] == "食伤格"
    assert "土" in f["yong_shen"] and "金" in f["yong_shen"]
    assert set(f["element_balance"]) == {"金", "木", "水", "火", "土"}
    assert f["spouse_palace"] == "亥"


def test_extract_bazi_v1_without_elements_does_not_crash():
    """bazi(v1) raw 只有干支串, 没有五行/格局 —— 应返回空默认值而不抛异常。"""
    raw = {
        "day_master": "辛",
        "pillars": {"year": "庚午", "month": "癸未", "day": "辛亥", "hour": "壬辰"},
        "horoscope": {},
        "断": "…",
    }
    f = extract_bazi_features(raw)
    assert f["day_master_element"] == "金"
    assert f["dominant_element"] in ("", None)
    assert f["spouse_palace"] == "亥"


def test_extract_ziwei_palace_names_without_gong_suffix():
    """紫微引擎的宫名不带"宫"字后缀, 提取器必须两种都认。"""
    raw = {
        "compatibility": None,
        "palaces": [
            {"name": "命宫", "major_stars": ["七杀"]},
            {"name": "官禄", "major_stars": ["破军"]},
            {"name": "财帛", "major_stars": ["贪狼"]},
            {"name": "夫妻", "major_stars": ["廉贞", "天相"]},
        ],
        "five_elements": "土五局",
        "four_transformations": {"yearly": ["天同", "天机", "文昌", "廉贞"]},
    }
    f = extract_ziwei_features(raw)
    assert f["ming_stars"] == ["七杀"]
    assert f["career_stars"] == ["破军"]
    assert f["wealth_stars"] == ["贪狼"]
    assert f["spouse_stars"] == ["廉贞", "天相"]
    assert f["ming_element"] == "土"


def test_extract_western_signs_and_aspects_without_suffixes():
    """西方引擎的星座不带"座"、相位带"相", 分类必须仍然正确。"""
    raw = {
        "planets": {
            "太阳": {"sign": "双子", "degree": 23.6, "element": "风"},
            "月亮": {"sign": "双鱼", "degree": 8.1, "element": "水"},
        },
        "aspects": [
            {"a": "月亮", "b": "水星", "aspect": "刑相", "angle": 90, "orb": 3.6},
            {"a": "太阳", "b": "月亮", "aspect": "三合相", "angle": 120, "orb": 4.1},
        ],
        "ascendant": None,
    }
    f = extract_western_features(raw)
    assert f["sun_sign"] == "双子"
    assert f["moon_sign"] == "双鱼"
    assert f["dominant_western_element"] in ("水", "风")  # 仅两星时并列, 取首个
    assert f["hard_aspects"] == 1
    assert f["soft_aspects"] == 1
    assert f["major_aspects"]


# ── 2. compute_with_validation 契约 ──────────────────────────────────
def test_multi_system_returns_ensemble_score_in_0_100():
    out = compute_with_validation(["bazi_v2", "ziwei", "western"], BIRTH, "self_life")
    cv = out["cross_validation"]
    score = cv["ensemble_score"]
    assert isinstance(score, (int, float))
    assert 0 <= score <= 100, f"ensemble_score 必须是 0-100 量纲, 实际 {score}"
    assert 0 <= cv["confidence"] <= 1
    assert cv["systems_checked"], "应记录实际参与的引擎"
    assert cv["cross_checks"], "应产出逐项交叉校验"
    assert cv["domain_checks"], "应产出域级一致度"
    assert "一致度" in cv["overall_assessment"] or "五行" in cv["overall_assessment"]


def test_domain_checks_have_confidence_and_agreement():
    cv = compute_with_validation(["bazi_v2", "ziwei"], BIRTH, "career")["cross_validation"]
    for domain, d in cv["domain_checks"].items():
        assert 0 <= d["confidence"] <= 100, domain
        assert 0 <= d["agreement"] <= 1, domain
        assert d["checks"] >= 1, domain


def test_single_method_never_fakes_high_score():
    cv = compute_with_validation(["bazi_v2"], BIRTH, "self_life")["cross_validation"]
    assert cv["ensemble_score"] == 0
    assert cv["domain_checks"] == {}
    assert cv["systems_checked"] == ["bazi_v2"]
    assert cv["chart_count"] == 1


def test_agreement_matrix_marks_uncomparable_methods_none():
    cv = compute_with_validation(["bazi_v2", "ziwei"], BIRTH, "self_life")["cross_validation"]
    matrix = cv["agreement_matrix"]
    assert set(matrix) == {"bazi_v2", "ziwei"}
    for v in matrix.values():
        assert v is None or 0 <= v <= 1


# ── 3. 端点端到端 ─────────────────────────────────────────────────────
def test_compute_multi_endpoint_exposes_cross_validation():
    resp = client.post(
        "/api/compute/multi",
        json={
            "methods": ["bazi_v2", "ziwei", "western"],
            "birth": {
                "year": 1990, "month": 6, "day": 15, "hour": 8, "minute": 30,
                "gender": "male", "calendar": "gregorian",
                "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai",
            },
            "subject": "self_life",
            "do_validate": True,
        },
    )
    assert resp.status_code == 200, resp.text
    cv = resp.json()["cross_validation"]
    assert 0 <= cv["ensemble_score"] <= 100
    assert cv["cross_checks"]
    assert len(cv["systems_checked"]) == 3
    assert cv["chart_count"] == 3
