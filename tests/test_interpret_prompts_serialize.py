"""解读序列化回归: 盘面 raw 与 prompts._serialize 键位契约。

背景(2026-10-23 实锤的两处 KeyError):
- meihua: 体卦/用卦/总断/断语在 raw['断法'](别名 raw['断']) 字典内,
  _serialize 曾从 raw 顶层读 r['体卦'] → KeyError '体卦'
- numerology: raw 结构改为 primary + life_path/destiny/soul_urge 对象,
  _serialize 曾读 r['生命灵数'] → KeyError '生命灵数'
"""
import pytest

from divination.contracts import Birth, ChartResult
from divination.engines.meihua import compute as meihua_compute
from divination.engines.numerology import compute as numerology_compute
from divination.interpret.prompts import _facts, _serialize, build_messages

BIRTH = Birth(1990, 6, 15, 8, 30, "male")


def test_meihua_serialize_reads_ti_yong_from_judgement():
    chart = meihua_compute(BIRTH)
    text = _serialize(chart)
    assert text.startswith("【梅花易数】")
    assert "主卦" in text and "/互" in text and "/变" in text
    assert "体" in text and "用" in text
    assert "总断" in text


def test_meihua_external_omen_serialize():
    chart = meihua_compute(BIRTH, mode="external_omen", question="钥匙在哪里")
    text = _facts(chart)
    assert "外应起卦·字占" in text
    assert "总断" in text


def test_numerology_serialize_new_shape():
    chart = numerology_compute(BIRTH, name="Zhang San", mode="destiny")
    text = _serialize(chart)
    assert "主数命运数9" in text
    assert "生命灵数4" in text
    assert "灵魂驱策2" in text


def test_numerology_life_path_only():
    chart = numerology_compute(BIRTH)
    text = _facts(chart)
    assert "主数生命灵数4" in text
    # 无姓名时不应出现空括号的命运数
    assert "命运数" not in text


def test_facts_degrades_gracefully_on_key_drift():
    """任何方法的 raw 键位漂移都降级为通用 dump, 不炸整次解读。"""
    # bazi 分支有裸键访问 r["pillars"], raw 缺失时应触发降级而不是抛异常
    broken = ChartResult(
        method="bazi", school="east", engine="test",
        normalized={}, raw={},
    )
    text = _facts(broken)
    assert text.startswith("【bazi】")


def test_meihua_empty_raw_still_serializes():
    """meihua 分支全防御性 .get: 空盘也不抛异常, 优雅输出。"""
    empty = ChartResult(
        method="meihua", school="east", engine="test",
        normalized={}, raw={},
    )
    text = _facts(empty)
    assert text.startswith("【梅花易数】")


def test_build_messages_mixed_methods():
    charts = [
        meihua_compute(BIRTH),
        numerology_compute(BIRTH, name="Zhang San", mode="destiny"),
    ]
    msg = build_messages(charts, "最近适合换工作吗")
    assert "【梅花易数】" in msg["user"]
    assert "【数字命理】" in msg["user"]
    assert "【求测者所问】最近适合换工作吗" in msg["user"]
    assert "请按系统规则给出解读" in msg["user"]


def test_interpret_endpoint_accepts_meihua_and_numerology():
    """端到端: /api/interpret 喂梅花+数字命理盘不再 500/error 事件。"""
    import json

    from fastapi.testclient import TestClient
    import server.main as main_module

    meihua = meihua_compute(BIRTH, mode="external_omen", question="钥匙在哪里")
    numerology = numerology_compute(BIRTH, name="Zhang San", mode="destiny")
    payload = {
        "charts": [meihua.to_dict(), numerology.to_dict()],
        "question": "钥匙在哪里",
    }
    client = TestClient(main_module.app)
    resp = client.post("/api/interpret", json=payload)
    assert resp.status_code == 200
    events = [json.loads(line) for line in resp.text.splitlines() if line.strip()]
    assert events, "interpret 流不应为空"
    assert all(ev.get("type") != "error" for ev in events), events
    assert events[-1].get("type") == "done"
