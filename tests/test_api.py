import json

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)

BIRTH = {
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 8,
    "minute": 30,
    "gender": "male",
    "calendar": "gregorian",
    "lat": 31.23,
    "lng": 121.47,
    "tz": "Asia/Shanghai",
    "is_leap_month": False,
}

METHODS = [
    "bazi",
    "ziwei",
    "qimen",
    "western",
    "vedic",
    "liuyao",
    "meihua",
    "chenggu",
    "bazhai",
    "xuankong",
    "tarot",
    "numerology",
    "lenormand",
    "liuren",
]


def _compute(method: str) -> dict:
    response = client.post(
        "/api/compute",
        json={"method": method, "birth": BIRTH, "options": {}},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _compute_with_options(method: str, options: dict) -> dict:
    response = client.post(
        "/api/compute",
        json={"method": method, "birth": BIRTH, "options": options},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _parse_ndjson(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def test_health_and_methods():
    assert client.get("/health").json()["status"] == "ok"

    response = client.get("/api/methods")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert set(METHODS) <= set(ids)
    tarot = next(item for item in response.json() if item["id"] == "tarot")
    assert "subjects" in tarot
    assert "modes" in tarot
    assert "required_inputs" in tarot
    assert "recommended_for" in tarot


def test_compute_all_methods():
    for method in METHODS:
        payload = _compute(method)
        assert payload["method"] == method
        assert payload["school"] in {"east", "west"}
        assert payload["engine"]
        assert isinstance(payload["raw"], dict)
        assert isinstance(payload["normalized"], dict)


def test_interpret_mock_stream():
    charts = [_compute("bazi"), _compute("western")]
    response = client.post(
        "/api/interpret",
        json={"charts": charts, "question": "今年事业如何?", "client": "mock"},
    )
    assert response.status_code == 200

    events = _parse_ndjson(response.text)
    assert any(event["type"] == "delta" and event["text"] for event in events)
    done = next(event for event in events if event["type"] == "done")
    assert done["meta"]["blocked"] is False
    assert "bazi" in done["meta"]["methods"]


def test_interpret_crisis_block():
    charts = [_compute("bazi")]
    response = client.post(
        "/api/interpret",
        json={"charts": charts, "question": "我活不下去了", "client": "mock"},
    )
    assert response.status_code == 200

    events = _parse_ndjson(response.text)
    done = next(event for event in events if event["type"] == "done")
    assert done["meta"]["blocked"] is True
    assert "crisis_redirect" in done["meta"]["flags"]


def test_anthropic_client_does_not_accept_request_body_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    charts = [_compute("bazi")]
    response = client.post(
        "/api/interpret",
        json={
            "charts": charts,
            "question": "test",
            "client": "anthropic",
            "api_key": "should-not-be-used",
        },
    )
    assert response.status_code == 400
    assert "ANTHROPIC_API_KEY" in response.text


def test_invalid_mode_rejected():
    response = client.post(
        "/api/compute",
        json={"method": "tarot", "birth": BIRTH, "options": {"mode": "not_a_mode"}},
    )
    assert response.status_code == 422


def test_tarot_upright_reversed_keywords_separate():
    payload = _compute_with_options("tarot", {"subject": "tarot_guidance", "spread": "single", "seed": 1})
    raw = payload["raw"]
    for card in raw["cards"]:
        assert card["keywords_upright"]
        assert card["keywords_reversed"]
        assert card["keywords"] in {card["keywords_upright"], card["keywords_reversed"]}
        assert card["image_hint"]
    basis = raw["calculation_basis"]
    assert basis["rule_version"] in {"v1", "v2"}
    assert raw["rule_version"] in {"v1", "v2"}


def test_tarot_position_template_filled_per_spread():
    payload = _compute_with_options("tarot", {"subject": "decision", "spread": "choice_two", "seed": 7})
    raw = payload["raw"]
    for card in raw["cards"]:
        assert card["position_template_filled"]
        assert card["name"] in card["position_template_filled"]
        assert ("正位" in card["position_template_filled"]) or ("逆位" in card["position_template_filled"])


def test_tarot_recommend_spread_matrix_resolves():
    from divination.engines.tarot import SPREAD_MATRIX, recommend_spread
    for subject, matrix in SPREAD_MATRIX.items():
        for budget in ("quick", "reflective", "deep"):
            rec = recommend_spread(subject, budget)
            assert rec["spread"] in SPREAD_MATRIX[subject]["by_budget"].values() or rec["spread"] == matrix["default"]
            assert rec["spread_name"]
            assert rec["position_count"] >= 1
    fallback = recommend_spread("__unknown_subject__", "quick")
    assert fallback["spread"] in {"single", "three_time"}


def test_ziwei_horoscope_and_mutagen():
    payload = _compute("ziwei")
    raw = payload["raw"]
    assert raw["rule_version"] == "v1"
    basis = raw["calculation_basis"]
    assert basis["rule_version"] == "v1"
    assert basis["input_source"]
    assert isinstance(basis["limits"], list) and basis["limits"]
    h = raw.get("horoscope", {})
    for scope in ("decadal", "yearly", "monthly", "daily", "hourly"):
        item = h.get(scope)
        assert item is not None, f"missing horoscope scope {scope}"
        assert item.get("ganzhi")
        assert isinstance(item.get("mutagen"), list)
        assert len(item["mutagen"]) == 4  # 禄权科忌
    # 本命 12 宫必有
    assert len(raw["palaces"]) == 12
    # 五行局 (3-6 范围,常见 2-9)
    assert raw.get("five_elements_class")
    # 12 长生 / 博士十二神 / 将前十二神 map
    assert isinstance(raw.get("changsheng12_map"), dict)
    assert isinstance(raw.get("boshi12_map"), dict)
    assert isinstance(raw.get("jiangqian12_map"), dict)
    # fallback 标注: 如未触发,字段应为 False
    assert raw["fallback"] is False
    assert raw["engine"] == "py-iztro"


def test_ziwei_each_palace_has_majors_or_minors():
    payload = _compute("ziwei")
    palaces = payload["raw"]["palaces"]
    for p in palaces:
        assert p["name"]
        assert isinstance(p["major_stars"], list)
        assert isinstance(p["minor_stars"], list)
        assert isinstance(p["adjective_stars"], list)


def test_ziwei_fallback_marker_present():
    """Ensure fallback flag is present and serialized so the result page can surface it."""
    payload = _compute("ziwei")
    raw = payload["raw"]
    assert "fallback" in raw
    assert "fallback_reason" in raw
    assert "engine" in raw


def test_bazi_rule_version_and_strength_score():
    payload = _compute("bazi")
    raw = payload["raw"]
    assert raw["rule_version"] == "v1"
    assert raw["calculation_basis"]["rule_version"] == "v1"
    assert raw["calculation_basis"]["input_source"]
    assert isinstance(raw["calculation_basis"]["limits"], list) and raw["calculation_basis"]["limits"]
    score = raw["strength_score"]
    assert isinstance(score, int) and 0 <= score <= 100
    basis = raw["strength_basis"]
    assert basis["month_strength"] in {5, 10, 15, 20, 30, 40}
    assert sum([basis["peer_count"], basis["resource_count"], basis["output_count"],
                basis["official_count"], basis["wealth_count"]]) > 0
    # 庚 日主 + 巳 月 (火克金) → 官杀当令 + 身弱走向,分数不应当出现满分或零
    assert 0 < score < 100


def test_bazi_elements_include_visible_hidden_and_total():
    payload = _compute("bazi")
    raw = payload["raw"]
    total = payload["normalized"]["elements"]
    visible = raw["elements_visible"]
    hidden = raw["elements_hidden"]
    assert set(total) == {"metal", "wood", "water", "fire", "earth"}
    assert set(visible) == set(total)
    assert set(hidden) == set(total)
    assert sum(total.values()) > sum(visible.values())
    assert any(value > 0 for value in hidden.values())


def test_bazi_current_luck_and_annual_interactions():
    payload = _compute("bazi")
    raw = payload["raw"]
    cl = raw["current_luck"]
    assert cl.get("decade_ganzhi")
    assert cl.get("annual_ganzhi")
    assert cl.get("decade_from") <= cl.get("decade_to")
    assert cl.get("age", 0) >= 0
    assert cl.get("decade_score") in {30, 40, 50, 70}
    ai = raw["annual_interactions"]
    assert ai.get("ganzhi")
    # 1990-05-15 庚日主, 流年常见互动: 天干合或地支冲合刑害
    for item in ai.get("interactions", []):
        assert item["kind"] in {"clash", "combine", "punish", "harm"}
        assert item["pillar"] in {"year", "month", "day", "hour"}


def test_bazi_life_stage_12_changsheng():
    payload = _compute("bazi")
    raw = payload["raw"]
    ls = raw["life_stage"]
    assert ls["day_master"] == raw["day_master"]
    assert ls["is_yang"] in {True, False}
    stages = ls["stages"]
    assert len(stages) == 4
    valid_stages = set(CHANGESHENG_STAGES) if False else {"长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"}
    for s in stages:
        assert s["pillar"] in {"year", "month", "day", "hour"}
        assert s["stage"] in valid_stages


def test_bazi_year_ganzhi_changes_with_calendar_input():
    solar = _compute("bazi")
    from divination.engines.bazi import _solar_from_birth
    from divination.contracts import Birth
    b = Birth(year=1990, month=5, day=15, hour=8, minute=30, gender="male", calendar="gregorian", tz="Asia/Shanghai")
    solar_obj = _solar_from_birth(b)
    assert solar_obj.toYmdHms().startswith("1990-05-15")
    # 农历输入解析验证
    b_lunar = Birth(year=1990, month=4, day=21, hour=8, minute=30, gender="male", calendar="lunar", tz="Asia/Shanghai")
    solar_obj2 = _solar_from_birth(b_lunar)
    assert solar_obj2.toYmd() != ""


def test_tarot_calculation_basis_includes_limits():
    payload = _compute_with_options("tarot", {"subject": "relationship", "spread": "relationship_cross", "seed": 3})
    basis = payload["raw"]["calculation_basis"]
    assert basis["method"] == "tarot"
    assert basis["input_source"]
    assert isinstance(basis["limits"], list) and basis["limits"]


def test_tarot_spreads_seed_and_no_duplicate_cards():
    expected_counts = {
        "single": 1,
        "three_time": 3,
        "three_mind": 3,
        "choice_two": 6,
        "relationship_cross": 5,
        "career_path": 5,
        "celtic_cross": 10,
    }
    for spread, count in expected_counts.items():
        payload = _compute_with_options(
            "tarot",
            {"subject": "relationship", "spread": spread, "seed": 42},
        )
        raw = payload["raw"]
        assert raw["spread"] == spread
        assert len(raw["cards"]) == count
        names = [card["name"] for card in raw["cards"]]
        assert len(names) == len(set(names))
        assert len(raw["spread_schema"]) == count

    first = _compute_with_options("tarot", {"spread": "career_path", "seed": 99})["raw"]["cards"]
    second = _compute_with_options("tarot", {"spread": "career_path", "seed": 99})["raw"]["cards"]
    assert first == second

    daily_seed_first = _compute_with_options("tarot", {"spread": "single", "seed": "daily-2026-06-06"})["raw"]
    daily_seed_second = _compute_with_options("tarot", {"spread": "single", "seed": "daily-2026-06-06"})["raw"]
    assert daily_seed_first["seed_used"] == "daily-2026-06-06"
    assert daily_seed_first["cards"] == daily_seed_second["cards"]


def test_liuyao_modes_and_manual_coin_priority():
    manual = _compute_with_options(
        "liuyao",
        {"mode": "manual_coin", "subject": "career", "method_inputs": {"tosses": [6, 7, 8, 9, 7, 8]}},
    )
    assert manual["raw"]["mode"] == "manual_coin"
    assert manual["raw"]["dong_yao"] == [1, 4]
    assert manual["raw"]["using_god"] == "官鬼"

    numbered = _compute_with_options("liuyao", {"mode": "number_qigua", "seed": 123})
    assert numbered["raw"]["calculation_basis"]["mode"] == "number_qigua"


def test_meihua_modes_are_recorded():
    payload = _compute_with_options("meihua", {"mode": "external_omen", "subject": "lost_item", "question": "钥匙在哪里"})
    assert payload["raw"]["mode"] == "external_omen"
    assert payload["raw"]["calculation_basis"]["subject"] == "lost_item"


def test_xuankong_sitting_and_year_change_grid():
    east = _compute_with_options("xuankong", {"sitting": "卯", "construction_year": 2024})
    west = _compute_with_options("xuankong", {"sitting": "酉", "construction_year": 2004})
    assert east["raw"]["sitting"] == "卯"
    assert west["raw"]["sitting"] == "酉"
    assert east["raw"]["period_number"] != west["raw"]["period_number"]
    assert east["raw"]["facing"] != west["raw"]["facing"]


def test_bazhai_gender_difference_same_year():
    male = _compute_with_options("bazhai", {"subject": "home_fengshui"})
    female_birth = {**BIRTH, "gender": "female"}
    response = client.post(
        "/api/compute",
        json={"method": "bazhai", "birth": female_birth, "options": {"subject": "home_fengshui"}},
    )
    assert response.status_code == 200
    female = response.json()
    assert male["raw"]["life_gua"] != female["raw"]["life_gua"]


# -- /api/daily ----------------------------------------------------------

def test_daily_get_without_birth():
    response = client.get("/api/daily", params={"date": "2026-06-06"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2026-06-06"
    t = payload["today"]
    assert t["ganzhi_day"]  # 非空
    assert t["day_wuxing"] in {"金", "木", "水", "火", "土"}
    assert t["tarot_card"]["name"]
    assert t["tarot_card"]["orient"] in {"正位", "逆位"}
    # lenormand card should also be present (default card_type=both)
    assert t.get("lenormand_card"), "lenormand_card should be present with default card_type=both"
    assert t["lenormand_card"]["name"]
    assert t["lenormand_card"]["name_en"]
    assert t["question_seed"]
    assert "user" not in payload
    assert "interaction" not in payload
    basis = payload["calculation_basis"]
    assert basis["method"] == "daily_v1"
    assert basis["rule_version"] == "v1"
    assert "lunar-python" in basis["input_source"]
    assert basis["limits"]  # 非空限制文本


def test_daily_post_with_birth_attaches_user_and_interaction():
    response = client.post(
        "/api/daily",
        json={"date": "2026-06-06", "birth": BIRTH},
    )
    assert response.status_code == 200
    payload = response.json()
    u = payload["user"]
    it = payload["interaction"]
    assert u["day_master"]  # 非空
    assert u["day_wuxing"] in {"金", "木", "水", "火", "土"}
    assert it["relation"] in {"比和", "印", "食伤", "官杀", "财"}
    assert it["label"] and it["action"] and it["watch"]
    assert it["subject_hint"] in {
        "self_life", "decision", "career", "relationship",
    }
    # 用户日主 庚 + 今日金 → 同元素 → 比和
    assert it["relation"] == "比和"


def test_daily_same_input_same_output():
    body = {"date": "2026-06-06", "birth": BIRTH}
    a = client.post("/api/daily", json=body).json()
    b = client.post("/api/daily", json=body).json()
    assert a == b
    # 同一天不同生日,塔罗会因 seed 不同而不同
    other = {**BIRTH, "year": 1992, "month": 7, "day": 22}
    c = client.post("/api/daily", json={"date": "2026-06-06", "birth": other}).json()
    # 同元素 vs 不同元素:仅验证结果稳定(同输入同输出)
    c2 = client.post("/api/daily", json={"date": "2026-06-06", "birth": other}).json()
    assert c == c2


def test_daily_different_date_different_card_or_gz():
    same_birth = BIRTH
    a = client.post("/api/daily", json={"date": "2026-06-06", "birth": same_birth}).json()
    b = client.post("/api/daily", json={"date": "2026-06-07", "birth": same_birth}).json()
    # 日柱必须不同(后一天)
    assert a["today"]["ganzhi_day"] != b["today"]["ganzhi_day"]
    # 塔罗种子随日期变,牌面通常会变
    assert a["today"]["tarot_card"]["seed_used"] != b["today"]["tarot_card"]["seed_used"]


def test_daily_invalid_date_returns_422():
    response = client.get("/api/daily", params={"date": "2026/06/06"})
    assert response.status_code == 422
    body = response.json()
    assert "date" in body["detail"].lower()


def test_daily_today_default_when_no_date():
    response = client.get("/api/daily")
    assert response.status_code == 200
    payload = response.json()
    from datetime import date
    assert payload["date"] == date.today().isoformat()


def test_multi_region_consistency():
    """所有14个案例跑bazi+western排盘，验证不抛异常且返回合理数据。"""
    import json
    from pathlib import Path

    cases_file = Path(__file__).parent.parent / "server" / "data" / "celebrity_cases.json"
    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    assert len(cases) >= 14, f"Expected >=14 cases, got {len(cases)}"

    regions_seen = set()
    for case in cases:
        birth = {
            "year": case["year"], "month": case["month"], "day": case["day"],
            "hour": case["hour"], "minute": case["minute"],
            "gender": case["gender"], "calendar": "gregorian",
            "lat": case["lat"], "lng": case["lng"], "tz": case["tz"],
        }
        # 八字排盘
        try:
            r_bazi = client.post("/api/compute", json={"method": "bazi", "birth": birth, "options": {}})
            assert r_bazi.status_code == 200, f"bazi failed for {case['id']}: {r_bazi.text}"
            data = r_bazi.json()
            assert data["method"] == "bazi"
            assert "pillars" in data["raw"]
            assert "elements" in data.get("normalized", {})
        except Exception as e:
            raise AssertionError(f"bazi error for {case['id']} ({case['name_zh']}, {case['tz']}): {e}")

        # 西方占星排盘
        try:
            r_western = client.post("/api/compute", json={"method": "western", "birth": birth, "options": {}})
            if r_western.status_code == 500 and "ephemeris" in r_western.text.lower():
                print(f"  [SKIP western for {case['id']}]: {r_western.json()['detail']}")
            else:
                assert r_western.status_code == 200, f"western failed for {case['id']}: {r_western.text}"
                data = r_western.json()
                assert data["method"] == "western"
                assert "planets" in data["raw"]
        except AssertionError:
            raise
        except Exception as e:
            raise AssertionError(f"western error for {case['id']} ({case['name_zh']}, {case['tz']}): {e}")

        # 记录时区多样性
        tz_prefix = case["tz"].split("/")[0]
        regions_seen.add(tz_prefix)

    assert len(regions_seen) >= 5, f"Expected diverse timezone coverage, got {regions_seen}"
