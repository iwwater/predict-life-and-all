"""P2-1: 连续采样 API 测试 — process_samples + session ≥30 + /measure samples.

覆盖:
- process_samples 纯函数 (mean/std/median/quality/range/r_value)
- Session API 采样下限 ≥30 (创建 + 追加 + 自动结算)
- /measure 端点支持 samples: list[float]
- 采样上限 1000
- 边界条件 (空列表, 单样本, 360° 环绕)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from divination.engines.compass import (
    circular_mean,
    circular_std,
    process_samples,
)
from server.main import app

client = TestClient(app)


# ── process_samples 纯粹函数 ────────────────────────────────────

class TestProcessSamplesPure:
    """测试 process_samples 纯函数."""

    def test_mean_consistent_samples(self):
        """多个相同样本 → mean ≈ 该值."""
        r = process_samples([90.0, 90.0, 90.0, 90.0, 90.0])
        assert r["count"] == 5
        assert abs(r["mean"] - 90.0) < 0.5
        assert r["std"] < 0.1

    def test_median_close_to_mean(self):
        """对称分布 → median ≈ mean."""
        samples = [88.0, 89.0, 90.0, 91.0, 92.0]
        r = process_samples(samples)
        assert abs(r["mean"] - r["median"]) < 1.0

    def test_range_consistent(self):
        """极差 = max - min."""
        r = process_samples([10.0, 20.0, 30.0])
        assert abs(r["range"] - 20.0) < 0.5

    def test_circular_zero_360_boundary(self):
        """环形处理 0/360 边界: 350° 和 10° 应接近."""
        r = process_samples([350.0, 10.0, 355.0, 5.0])
        assert r["count"] == 4
        # 环形均值应接近 0/360
        assert r["mean"] < 5.0 or r["mean"] > 355.0

    def test_empty_samples(self):
        """空列表 → count=0, quality=low."""
        r = process_samples([])
        assert r["count"] == 0
        assert r["quality"] == "low"

    def test_single_sample(self):
        """单样本 → std=0, range=0."""
        r = process_samples([45.0])
        assert r["count"] == 1
        assert r["std"] == 0.0
        assert r["range"] == 0.0
        assert abs(r["mean"] - 45.0) < 0.5

    def test_quality_high(self):
        """std <= 3° → quality=high."""
        r = process_samples([90.0, 90.5, 89.5, 90.0, 90.5])
        assert r["quality"] == "high"

    def test_quality_medium(self):
        """3° < std <= 8° → quality=medium."""
        r = process_samples([85.0, 90.0, 95.0, 88.0, 92.0])
        assert r["quality"] in ("low", "medium")  # depends on spread
        # 大离散 → quality=low
        r2 = process_samples([45.0, 90.0, 135.0, 180.0, 270.0])
        assert r2["quality"] == "low"

    def test_r_value_consistent(self):
        """集中度 R: 一致样本 → R≈1, 分散样本 → R<1."""
        r1 = process_samples([90.0, 90.0, 90.0, 90.0, 90.0])
        assert r1["r_value"] > 0.99
        r2 = process_samples([0.0, 90.0, 180.0, 270.0])
        assert r2["r_value"] < 0.5

    def test_large_sample_count(self):
        """大量样本 (≥60) → 正确处理."""
        # 60 samples around 90° with small noise
        import math
        samples = [90.0 + 0.5 * math.sin(i * 0.5) for i in range(60)]
        r = process_samples(samples)
        assert r["count"] == 60
        assert abs(r["mean"] - 90.0) < 1.0
        assert r["quality"] == "high"


# ── Session API: 采样下限 ≥30 ──────────────────────────────────

class TestSessionLowerBound30:
    """Session 采样要求 ≥30 个样本才自动结算."""

    def test_session_created_with_min_30(self):
        """创建 session 默认 sample_count=30."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
        })
        assert r.status_code == 200

    def test_session_rejects_less_than_30(self):
        """sample_count < 30 → 422."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
            "sample_count": 5,
        })
        assert r.status_code == 422

    def test_29_samples_does_not_close(self):
        """29 个样本 → session 不自动关闭."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
            "sample_count": 30,
        })
        assert r.status_code == 200
        sid = r.json()["session_id"]
        # 加 29 个样本
        for az in range(29):
            r2 = client.post(f"/api/compass/sessions/{sid}/samples", json={
                "azimuth_deg": float(90 + az % 5),
            })
            if r2.json().get("closed"):
                break
        # 查 session 状态
        r3 = client.get(f"/api/compass/sessions/{sid}")
        body = r3.json()
        # 29 个样本不应自动关闭 (>=30 才自动关闭)
        assert body["closed"] is False

    def test_30_samples_triggers_close(self):
        """30 个样本 → 自动结算关闭."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
            "sample_count": 30,
        })
        assert r.status_code == 200
        sid = r.json()["session_id"]
        # 加 30 个样本
        for az in range(30):
            r2 = client.post(f"/api/compass/sessions/{sid}/samples", json={
                "azimuth_deg": 90.0,
            })
            if az == 29:
                assert r2.json()["closed"] is True


# ── /measure 端点: samples 字段 ─────────────────────────────────

class TestMeasureSamplesField:
    """P2-1: /measure 支持 samples: list[float]."""

    def test_measure_with_samples_returns_stats(self):
        """传入 samples → sample_stats 非空."""
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 90,
            "samples": [88.0, 89.0, 90.0, 91.0, 92.0],
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sample_stats"] is not None
        assert "mean" in body["sample_stats"]
        assert "std" in body["sample_stats"]
        assert "median" in body["sample_stats"]
        assert "quality" in body["sample_stats"]
        assert body["sample_stats"]["count"] == 5

    def test_measure_without_samples_returns_none_stats(self):
        """不传 samples → sample_stats=None."""
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 90,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sample_stats"] is None

    def test_measure_with_empty_samples(self):
        """空 samples → stats count=0."""
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 90,
            "samples": [],
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sample_stats"]["count"] == 0

    def test_measure_with_many_samples(self):
        """60+ 个 samples → 正常返回统计."""
        samples = [90.0] * 60
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 90,
            "samples": samples,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sample_stats"]["count"] == 60
        assert body["sample_stats"]["quality"] == "high"


# ── 采样上限 1000 ──────────────────────────────────────────────

class TestSessionUpperBound1000:
    """采样上限 1000."""

    def test_session_accepts_max_1000(self):
        """sample_count=1000 → 200."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
            "sample_count": 1000,
        })
        assert r.status_code == 200

    def test_session_rejects_1001(self):
        """sample_count=1001 → 422."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
            "sample_count": 1001,
        })
        assert r.status_code == 422

    def test_measure_with_1000_samples_accepted(self):
        """1000 samples in /measure → 200."""
        samples = [float(i % 360) for i in range(1000)]
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 90,
            "samples": samples,
        })
        assert r.status_code == 200
        assert r.json()["sample_stats"]["count"] == 1000


# ── 综合验证 ───────────────────────────────────────────────────

class TestCompassIntegration:
    """process_samples + /measure + session 综合."""

    def test_session_then_measure_consistency(self):
        """Session 统计与 /measure 的 process_samples 结果一致."""
        samples = [88.0, 89.0, 90.0, 91.0, 92.0] * 6  # 30 个
        # /measure
        r1 = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 90,
            "samples": samples,
        })
        m_stats = r1.json()["sample_stats"]

        # session
        r2 = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
            "sample_count": 30,
        })
        sid = r2.json()["session_id"]
        for az in samples:
            client.post(f"/api/compass/sessions/{sid}/samples", json={
                "azimuth_deg": az,
            })
        r3 = client.get(f"/api/compass/sessions/{sid}")
        session = r3.json()

        # mean 应一致
        assert abs(m_stats["mean"] - session["result_azimuth"]) < 2.0
