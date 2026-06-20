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


def test_context_answer_advances_case():
    """Sprint 1.2: 提供一个答案后, 该题从列表移除, 仍有后续问题。"""
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
    # offer_status 已答 → 不再出现
    qids = [q["id"] for q in updated["minimal_questions"]]
    assert "offer_status" not in qids
    # 仍可能有后续问题 (reversibility, urgency)
    assert len(updated["minimal_questions"]) <= 2


def test_context_all_answers_marks_case_ready():
    """Sprint 1.2: 提供所有追问答案后, minimal_questions 为空 + status=context_ready。"""
    case = client.post("/api/cases", json={
        "question": "我是否应该接受这份新工作？",
        "birth": BIRTH,
    }).json()
    # 循环答完所有问题, 直到列表为空
    current = case
    for _ in range(5):  # 安全上限
        if not current["minimal_questions"]:
            break
        answers = {q["id"]: f"test_{q['id']}" for q in current["minimal_questions"]}
        current = client.post(f"/api/cases/{current['case_id']}/context", json={
            "answers": answers,
            "constraints": {"cash_reserve_months": 4},
        }).json()
    assert current["minimal_questions"] == []
    assert current["status"] == "context_ready"


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


# ── Sprint 1.7 新增 ─────────────────────────────────────────────────

def test_idempotency_on_create():
    """Sprint 1.7: 同 (question+birth+goal) → 复用同 case (draft 状态)."""
    body = {"question": "我该换工作吗", "birth": BIRTH}
    r1 = client.post("/api/cases", json=body).json()
    r2 = client.post("/api/cases", json=body).json()
    assert r1["case_id"] == r2["case_id"]
    assert r1["idempotency_key"] == r2["idempotency_key"]


def test_idempotency_different_inputs_create_separate():
    """Sprint 1.7: 不同问题 → 不同 case."""
    r1 = client.post("/api/cases", json={"question": "我该换工作吗", "birth": BIRTH}).json()
    r2 = client.post("/api/cases", json={"question": "我该创业吗", "birth": BIRTH}).json()
    assert r1["case_id"] != r2["case_id"]


def test_list_versions():
    """Sprint 1.7: GET /api/cases/{id}/versions 列所有版本."""
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    # cast parent
    client.post(
        f"/api/cases/{case['case_id']}/cast",
        json={"depth": "free"},
        headers={"Idempotency-Key": "v1"},
    )
    # create 2 child versions
    client.post(f"/api/cases/{case['case_id']}/versions", json={
        "changed_condition": "A",
    })
    client.post(f"/api/cases/{case['case_id']}/versions", json={
        "changed_condition": "B",
    })
    r = client.get(f"/api/cases/{case['case_id']}/versions")
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 3  # parent + 2 children
    assert versions[0]["case_id"] == case["case_id"]
    assert versions[1]["version"] == 2
    assert versions[2]["version"] == 3


def test_select_version_overrides_latest():
    """Sprint 1.7: 选定旧版本后, /result 返回旧版 result."""
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    # cast parent
    cast1 = client.post(
        f"/api/cases/{case['case_id']}/cast",
        json={"depth": "free"},
        headers={"Idempotency-Key": "v1"},
    ).json()
    # create v2
    child = client.post(f"/api/cases/{case['case_id']}/versions", json={
        "changed_condition": "updated",
    }).json()
    # cast v2
    cast2 = client.post(
        f"/api/cases/{child['case_id']}/cast",
        json={"depth": "free"},
        headers={"Idempotency-Key": "v2"},
    ).json()
    # 默认 /result 返 v2
    r = client.get(f"/api/cases/{case['case_id']}/result").json()
    assert r["result"]["session_id"] == cast2["result"]["session_id"]
    # 选定 v1
    select_resp = client.post(f"/api/cases/{case['case_id']}/versions/1/select")
    assert select_resp.status_code == 200
    assert select_resp.json()["selected_version"] == 1
    # /result 应返 v1
    r = client.get(f"/api/cases/{case['case_id']}/result").json()
    assert r["result"]["session_id"] == cast1["result"]["session_id"]


def test_select_invalid_version_404():
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    client.post(
        f"/api/cases/{case['case_id']}/cast",
        json={"depth": "free"},
        headers={"Idempotency-Key": "v1"},
    )
    r = client.post(f"/api/cases/{case['case_id']}/versions/99/select")
    assert r.status_code == 404


def test_select_uncast_version_409():
    case = client.post("/api/cases", json={"question": "我该不该换工作？", "birth": BIRTH}).json()
    client.post(
        f"/api/cases/{case['case_id']}/cast",
        json={"depth": "free"},
        headers={"Idempotency-Key": "v1"},
    )
    client.post(f"/api/cases/{case['case_id']}/versions", json={
        "changed_condition": "x",
    })
    # v2 还没 cast
    r = client.post(f"/api/cases/{case['case_id']}/versions/2/select")
    assert r.status_code == 409
