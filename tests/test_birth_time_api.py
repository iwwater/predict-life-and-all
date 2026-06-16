from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


BIRTH = {
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 8,
    "minute": 30,
    "gender": "male",
    "calendar": "gregorian",
    "lat": 31.23,
    "lng": 121.47,
    "tz": "Asia/Shanghai",
}


def test_unknown_birth_time_returns_candidate_hours():
    response = client.post("/api/birth-time/rectify", json={
        "birth": BIRTH,
        "birth_time_accuracy": "unknown",
        "known_events": [
            {"year": 2013, "category": "career_start"},
            {"year": 2019, "category": "move"},
            {"year": 2022, "category": "career_change"},
        ],
        "keep_top_n": 4,
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "candidate_hours"
    assert len(data["candidates"]) == 4
    assert data["best"]["score"] >= data["candidates"][-1]["score"]
    assert data["best"]["branch"]
    assert data["uncertainty_note"]
    assert "不宣称绝对" in data["uncertainty_note"]


def test_period_accuracy_limits_candidates_to_period():
    response = client.post("/api/birth-time/rectify", json={
        "birth": BIRTH,
        "birth_time_accuracy": "period",
        "day_period": "morning",
        "known_events": [{"year": 2013, "category": "education"}],
        "keep_top_n": 12,
    })
    assert response.status_code == 200, response.text
    data = response.json()
    hours = {c["hour"] for c in data["candidates"]}
    assert hours <= {6, 8, 10}
    assert len(data["candidates"]) == 3
    assert all("候选位于用户提供的时间段内" in " ".join(c["evidence"]) for c in data["candidates"])


def test_exact_birth_time_returns_single_candidate():
    response = client.post("/api/birth-time/rectify", json={
        "birth": BIRTH,
        "birth_time_accuracy": "exact",
        "known_events": [{"year": 2013, "category": "career_start"}],
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "single_exact"
    assert len(data["candidates"]) == 1
    assert data["best"]["hour"] == BIRTH["hour"]
    assert data["second"] is None
    assert data["confidence_level"] == "high"


def test_rectification_is_deterministic_for_same_input():
    body = {
        "birth": BIRTH,
        "birth_time_accuracy": "approximate",
        "approximate_hour": 9,
        "known_events": [
            {"year": 2014, "category": "career_start"},
            {"year": 2020, "category": "finance"},
        ],
        "keep_top_n": 3,
    }
    first = client.post("/api/birth-time/rectify", json=body).json()
    second = client.post("/api/birth-time/rectify", json=body).json()
    assert first["candidates"] == second["candidates"]
    assert first["best"] == second["best"]


def test_close_candidates_may_request_one_more_question():
    response = client.post("/api/birth-time/rectify", json={
        "birth": BIRTH,
        "birth_time_accuracy": "unknown",
        "known_events": [],
        "keep_top_n": 4,
    })
    assert response.status_code == 200, response.text
    data = response.json()
    if data["next_question"] is not None:
        assert len(data["next_question"]["options"]) <= 4
        assert data["next_question"]["prompt"]
    assert len(data["main_differences"]) >= 1
    assert len(data["common_conclusions"]) >= 1
