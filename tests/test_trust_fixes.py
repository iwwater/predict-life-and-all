"""信任止血回归测试 — 锁定 2026-10 修复的七项「伪造数据/空壳承诺」问题。

覆盖：
1. bazi_v2 路由真接 v2 引擎（不再错接 v1）
2. normalizer 消费 v2 raw 真实键（primary_zh 用神 / current_luck 流年大运）
3. /api/compute/multi agreement_matrix 来自真实盘面（可复现、失败容错、缺数据记 None）
4. 合盘评分来自真实五行（合成盘验证生克矩阵；数据不足显式 insufficient_data）
5. /api/compatibility western 接真实 synastry 引擎
6. /api/calibrate/hour 接真实 hour_calibrator（已知信息真实参与打分、分数有区分度）
7. LLM 客户端签名对齐 max_tokens + 网络超时
8. /api/prompts/{method} 白名单防路径穿越
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from divination.contracts import Birth
from divination.router import (
    COMPATIBLE_PAIRS,
    compute,
    compute_compatibility_score,
    compute_with_validation,
)

BIRTH = Birth(year=1990, month=6, day=15, hour=8, minute=30,
              gender="male", lat=31.23, lng=121.47, tz="Asia/Shanghai")


def _client() -> TestClient:
    from server.main import app
    return TestClient(app)


# ── 1. bazi_v2 路由 ─────────────────────────────────────────────────────


class TestBaziV2Routing:
    def test_router_uses_v2_engine(self):
        r = compute("bazi_v2", BIRTH)
        assert r.raw.get("rule_version") == "v2", "bazi_v2 必须产出 v2 raw"
        assert "yong_shen" in r.raw and "pattern" in r.raw
        assert r.method == "bazi_v2"

    def test_bazi_still_v1_shape(self):
        r = compute("bazi", BIRTH)
        assert "horoscope" in r.raw, "bazi v1 路径不应被改动"
        assert r.raw.get("rule_version") != "v2"

    def test_api_compute_bazi_v2_is_v2(self):
        c = _client()
        resp = c.post("/api/compute", json={
            "method": "bazi_v2",
            "birth": {"year": 1990, "month": 6, "day": 15, "hour": 8, "minute": 30},
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["raw"].get("rule_version") == "v2"


# ── 2. normalizer 消费 v2 raw ──────────────────────────────────────────


class TestNormalizerConsumesV2:
    def test_v2_signals_use_real_keys(self):
        from divination.aggregation.normalizer import normalize
        from divination.contracts import ChartResult
        from divination.engines import bazi_v2

        r = bazi_v2.compute(BIRTH)
        chart = ChartResult(method="bazi_v2", school="east", engine="t",
                            raw=r.raw, normalized=r.normalized)
        signals = normalize("bazi_v2", chart)
        assert len(signals) >= 3
        joined = " ".join(s.evidence for s in signals)
        # v2 独有数据源必须被消费（v1 raw 无这些键，伪造不出来）
        assert "当前大运" in joined, "v2 current_luck.decade_ganzhi 未被消费"
        assert "流年" in joined, "v2 current_luck.annual_ganzhi 未被消费"
        if r.raw.get("yong_shen", {}).get("primary_zh"):
            assert "用神" in joined, "v2 yong_shen.primary_zh 未被消费"

    def test_v1_synthetic_raw_still_works(self):
        """旧键（yong_shen.yong_shen / elements 中文键）兼容不回归。"""
        from divination.aggregation.normalizer import _normalize_bazi
        from divination.contracts import ChartResult

        chart = ChartResult(method="bazi_v2", school="east", engine="t",
                            raw={"day_master": "甲", "strength_score": 60,
                                 "elements": {"金": 30, "木": 40, "水": 20, "火": 5, "土": 5},
                                 "yong_shen": {"yong_shen": "水"},
                                 "yong_shen_quality": {"score": 60},
                                 "shensha": {"summary": {"notable": ["天乙贵人"]}}},
                            normalized={})
        signals = _normalize_bazi("bazi_v2", chart.raw, chart.normalized)
        assert len(signals) >= 3
        assert any("用神水" in s.evidence for s in signals)


# ── 3. agreement_matrix 真实化 ─────────────────────────────────────────


class TestAgreementMatrix:
    def test_deterministic_and_data_derived(self):
        r1 = compute_with_validation(["bazi", "bazi_v2"], BIRTH)
        r2 = compute_with_validation(["bazi", "bazi_v2"], BIRTH)
        cv1, cv2 = r1["cross_validation"], r2["cross_validation"]
        # 同输入必须同输出（hash 版跨进程会漂移，这里锁同进程确定性）
        assert cv1["agreement_matrix"] == cv2["agreement_matrix"]
        # 值必须来自真实最旺五行：bazi 火 / bazi_v2 水（英文键归一到中文）
        assert cv1["domain_checks"]["elements"] == {"火": 1, "水": 1}
        # 互不相同 → 各自与其余可比法的一致率为 0（真实数据，而非编造的 0.7x）
        assert cv1["agreement_matrix"]["bazi"] == 0.0
        assert cv1["agreement_matrix"]["bazi_v2"] == 0.0

    def test_unmappable_element_reported_as_none(self):
        """western 的"风"在五行里无对应 → 不参与共识，记 None 而不是编造。"""
        r = compute_with_validation(["bazi", "western"], BIRTH)
        cv = r["cross_validation"]
        assert cv["agreement_matrix"]["western"] is None
        assert cv["agreement_matrix"]["bazi"] is None  # 只剩 1 个可比法
        assert cv["ensemble_score"] == 0.0

    def test_engine_failure_does_not_crash(self, monkeypatch):
        from divination import router as router_mod

        def boom(birth, **kw):
            raise ValueError("simulated engine failure")

        monkeypatch.setitem(router_mod._ENGINES, "liuyao", boom)
        r = compute_with_validation(["bazi_v2", "liuyao"], BIRTH)
        assert r["charts"]["liuyao"] is None, "失败引擎应为 None 而不是崩溃"
        assert r["charts"]["bazi_v2"] is not None
        assert r["cross_validation"]["agreement_matrix"]["liuyao"] is None
        assert "1/2 法计算成功" in r["cross_validation"]["overall_assessment"]


# ── 4/5. 合盘真实化 ────────────────────────────────────────────────────


class TestCompatibilityScore:
    def test_synthetic_elements_follow_shengke_matrix(self):
        # 甲(木) × 庚(金)：金克木 → 35
        s = compute_compatibility_score({"raw": {"day_master": "甲"}},
                                        {"raw": {"day_master": "庚"}}, "bazi_v2")
        assert s["compatibility_score"] == 35 and s["level"] == "low"
        # 甲(木) × 壬(水)：水生木 → 75
        s = compute_compatibility_score({"raw": {"day_master": "甲"}},
                                        {"raw": {"day_master": "壬"}}, "bazi_v2")
        assert s["compatibility_score"] == 75 and s["level"] == "high"
        # 与 COMPATIBLE_PAIRS 表一致
        assert s["compatibility_score"] == round(COMPATIBLE_PAIRS[("木", "水")] * 100)

    def test_insufficient_data_is_explicit(self):
        s = compute_compatibility_score({"raw": {"foo": 1}}, {"raw": {"bar": 2}}, "tarot")
        assert s["compatibility_score"] is None
        assert s["level"] == "insufficient_data"

    def test_api_bazi_scores_vary_by_pair(self):
        c = _client()
        scores = []
        for y2, m2, d2 in [(1992, 8, 20), (1985, 1, 1), (2000, 7, 7)]:
            resp = c.post("/api/compatibility", json={
                "chart1_birth": {"year": 1990, "month": 5, "day": 15, "hour": 12},
                "chart2_birth": {"year": y2, "month": m2, "day": d2, "hour": 12},
                "method": "bazi_v2",
            })
            assert resp.status_code == 200
            scores.append(resp.json()["compatibility_score"])
        assert all(s is not None for s in scores)
        assert len(set(scores)) > 1, f"不同生辰对必须给出不同分数，实际 {scores}"


class TestSynastryCompatibility:
    def test_api_western_uses_synastry_engine(self):
        c = _client()
        resp = c.post("/api/compatibility", json={
            "chart1_birth": {"year": 1990, "month": 5, "day": 15, "hour": 12,
                            "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai"},
            "chart2_birth": {"year": 1995, "month": 9, "day": 25, "hour": 6,
                             "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai"},
            "method": "western",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("scoring"), "western 合盘必须走真实 synastry 引擎"
        assert body.get("cross_aspects") is not None
        assert body["compatibility_score"] == body["scoring"]["compatibility_score"]
        assert body["breakdown"], "synastry 维度评分 (cross_aspects/house_overlays...) 必须存在"

    def test_api_multi_includes_synastry_results(self):
        c = _client()
        resp = c.post("/api/compatibility", json={
            "chart1_birth": {"year": 1990, "month": 5, "day": 15, "hour": 12,
                             "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai"},
            "chart2_birth": {"year": 1995, "month": 9, "day": 25, "hour": 6,
                             "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai"},
            "methods": ["bazi_v2", "western"],
        })
        assert resp.status_code == 200
        body = resp.json()
        names = {ms["method"] for ms in body["method_scores"]}
        assert "bazi" in names and "western_synastry" in names
        assert all(isinstance(ms["score"], (int, float))
                   for ms in body["method_scores"]), "所有已选方法必须产出真实评分"
        assert isinstance(body["ensemble_score"], (int, float))
        assert "western_synastry" in body["results"], "前端消费的 results.western_synastry 必须存在"
        assert body["results"]["western_synastry"]["scoring"]["breakdown"]


# ── 6. 时辰校准真实化 ──────────────────────────────────────────────────


class TestCalibrateHour:
    def test_api_uses_real_calibrator(self):
        c = _client()
        resp = c.post("/api/calibrate/hour", json={
            "birth": {"year": 1990, "month": 6, "day": 15, "hour": 12,
                      "lat": 31.23, "lng": 121.47, "tz": "Asia/Shanghai"},
            "known_traits": ["leader", "assertive"],
            "known_career": "technology",
            "known_events": [{"year": 2015, "category": "career_start",
                              "polarity": "positive"}],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["candidates"]) == 12
        # 旧 stub 全部恒 0.5 分；真实现的分数必须有区分度
        scores = {round(cand["score"], 3) for cand in body["candidates"]}
        assert len(scores) > 1, f"12 个时辰分数必须不同，实际 {sorted(scores)}"
        assert 0.0 <= body["best_confidence"] <= 100.0
        assert body["best"]["branch"] and body["best_hour"]
        # 已知信息必须真实参与打分（打分明细存在且非中性基线）
        breakdown = body["best"]["score_breakdown"]
        assert "trait_match" in breakdown and "career_match" in breakdown
        assert breakdown["trait_match"] != 10 or breakdown["career_match"] != 7.5, \
            "已知特质/职业不应全部落到中性基线"
        assert "event_timing_match" in breakdown
        # 真太阳时信息（提供经纬度时）
        tst = body["true_solar_time_info"]
        assert tst and "true_solar_time" in tst and "equation_of_time_min" in tst

    def test_hour_calibrator_english_elements_bridge(self):
        """bazi_v2 elements_total 英文键 → 用神打分不再是恒 0（回归 _zh_elements）。"""
        from divination.engines import hour_calibrator as hc

        cand = hc.HourCandidate(
            branch="午", hour=12, traits="",
            chart={"raw": {
                "yong_shen": {"primary_zh": ["水"], "avoid_zh": ["火"]},
                "yong_shen_quality": {"score": 60},
                "elements_total": {"metal": 1.0, "water": 3.0, "fire": 0.5},
            }},
        )
        _, breakdown, _, yong_ratio, _ = hc._score_candidate(cand, [], None, None)
        # 桥接修复后: 用神水占 3/4.5 → min(15, 33)=15 + 忌神弱 +10 + 质量 +1 = 26
        # （修复前英文键取不到 → 恒 0 + 10 + 1 = 11）
        assert breakdown["yong_shen_match"] > 15, \
            f"用神维度应基于真实元素计数，实际 {breakdown['yong_shen_match']}"
        assert yong_ratio > 0.5


# ── 7. LLM 客户端 ──────────────────────────────────────────────────────


class TestLLMClient:
    def test_anthropic_signature_max_tokens_and_timeout(self, monkeypatch):
        from divination.interpret import client as client_mod

        captured = {}

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"content": [{"text": "ok"}]}).encode()

        def fake_urlopen(req, timeout=None):
            captured["timeout"] = timeout
            captured["payload"] = json.loads(req.data.decode())
            return FakeResp()

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        cli = client_mod.AnthropicClient(api_key="sk-test", model="claude-test")
        out = cli.complete(system="s", user="u", max_tokens=4096)
        assert out == "ok"
        # reading_service 以 max_tokens=4096 调用（premium）；签名必须对齐
        assert captured["payload"]["max_tokens"] == 4096
        assert captured["payload"]["model"] == "claude-test"
        assert captured["payload"]["system"] == "s"
        # 网络调用必须带超时（修复前 urlopen 无 timeout 参数）
        assert captured["timeout"] == client_mod.AnthropicClient.DEFAULT_TIMEOUT_SECONDS

    def test_default_max_tokens_applied(self, monkeypatch):
        from divination.interpret import client as client_mod

        captured = {}

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"content": [{"text": "ok"}]}).encode()

        def fake_urlopen(req, timeout=None):
            captured["payload"] = json.loads(req.data.decode())
            return FakeResp()

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        cli = client_mod.AnthropicClient(api_key="sk-test")
        cli.complete("s", "u")  # reader.py 的两位置参数调用方式
        assert captured["payload"]["max_tokens"] == 1500


# ── 8. prompts 白名单 ──────────────────────────────────────────────────


class TestPromptsWhitelist:
    def test_normal_prompt_ok(self):
        c = _client()
        resp = c.get("/api/prompts/bazi")
        assert resp.status_code == 200
        assert resp.json()["method"] == "bazi"

    def test_backslash_traversal_blocked(self):
        c = _client()
        # Windows 下 ..%5C 可逃出目录（修复前实测 200 泄漏文件内容）
        for evil in [
            "/api/prompts/..%5C..%5C..%5Cdocs%5CETHICS",
            "/api/prompts/..%2F..%2F..%2FREADME",
            "/api/prompts/bazi%5C..%5C..%5C..%5C.env",
        ]:
            resp = c.get(evil)
            assert resp.status_code == 404, f"{evil} 不应命中: {resp.status_code}"
            assert "template" not in resp.json()
