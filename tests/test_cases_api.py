from fastapi.testclient import TestClient

from server.api.cases import _reset_store_for_tests
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


def setup_function():
    _reset_store_for_tests()


def test_create_case_classifies_event_and_limits_questions():
    response = client.post("/api/cases", json={
        "question": "我是否应该接受这份新工作？",
        "birth": BIRTH,
        "location": "东京",
    })
    assert response.status_code == 200, response.text
    case = response.json()
    assert case["case_id"].startswith("case_")
    assert case["event_type"] in {"career", "decision"}
    assert case["question"] == "我是否应该接受这份新工作？"
    assert len(case["minimal_questions"]) <= 2
    assert any(q["id"] == "offer_status" for q in case["minimal_questions"])
    assert case["status"] == "draft"


def test_context_answer_marks_case_ready():
    case = client.post("/api/cases", json={
        "question": "我是否应该接受这份新工作？",
        "birth": BIRTH,
    }).json()
    response = client.post(f"/api/cases/{case['case_id']}/context", json={
        "answers": {"offer_status": "已有正式 offer"},
        "constraints": {"cash_reserve_months": 4},
    })
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["context"]["offer_status"] == "已有正式 offer"
    assert updated["constraints"]["cash_reserve_months"] == 4
    assert updated["minimal_questions"] == []
    assert updated["status"] == "context_ready"


def test_cast_requires_idempotency_key():
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    response = client.post(f"/api/cases/{case['case_id']}/cast", json={"depth": "free"})
    assert response.status_code == 422


def test_cast_is_fixed_and_idempotent():
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    cast_url = f"/api/cases/{case['case_id']}/cast"
    headers = {"Idempotency-Key": "case-test-1"}

    first = client.post(cast_url, json={"depth": "free"}, headers=headers)
    assert first.status_code == 200, first.text
    first_payload = first.json()
    assert first_payload["idempotent"] is False
    assert first_payload["case"]["status"] == "officially_cast"

    second = client.post(cast_url, json={"depth": "premium"}, headers=headers)
    assert second.status_code == 200, second.text
    second_payload = second.json()
    assert second_payload["idempotent"] is True
    assert second_payload["result"]["session_id"] == first_payload["result"]["session_id"]

    third = client.post(cast_url, json={"depth": "premium"}, headers={"Idempotency-Key": "case-test-2"})
    assert third.status_code == 200, third.text
    assert third.json()["result"]["session_id"] == first_payload["result"]["session_id"]

    result = client.get(f"/api/cases/{case['case_id']}/result")
    assert result.status_code == 200
    assert result.json()["result"]["session_id"] == first_payload["result"]["session_id"]


def test_context_cannot_change_after_official_cast():
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    client.post(
        f"/api/cases/{case['case_id']}/cast",
        json={"depth": "free"},
        headers={"Idempotency-Key": "fixed"},
    )
    response = client.post(f"/api/cases/{case['case_id']}/context", json={
        "answers": {"offer_status": "只有口头机会"},
    })
    assert response.status_code == 409


def test_changed_condition_creates_new_version_without_overwriting_parent():
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    cast = client.post(
        f"/api/cases/{case['case_id']}/cast",
        json={"depth": "free"},
        headers={"Idempotency-Key": "v1"},
    ).json()

    response = client.post(f"/api/cases/{case['case_id']}/versions", json={
        "changed_condition": "收到正式合同",
        "context_updates": {"offer_status": "已有正式 offer"},
    })
    assert response.status_code == 200, response.text
    child = response.json()
    assert child["case_id"] != case["case_id"]
    assert child["parent_case_id"] == case["case_id"]
    assert child["version"] == case["version"] + 1
    assert child["result_session_id"] is None
    assert child["context"]["changed_condition"] == "收到正式合同"

    parent_result = client.get(f"/api/cases/{case['case_id']}/result").json()
    assert parent_result["result"]["session_id"] == cast["result"]["session_id"]
