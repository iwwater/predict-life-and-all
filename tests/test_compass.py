"""Sprint 3 — 罗盘三通道 + 临界角双候选 + declination 校正 测试。

覆盖:
- heading_to_24mountain 中心/边界/临界
- 24 山元数据完整 (24 项, 每山 15°)
- declination 估算 (中国/日本/北美)
- magnetic → true 转换
- API 三通道输入 (device/physical/manual/map)
- 临界角双候选 + fengshui_warning
- 环形均值/标准差 (处理 0/360 边界)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from divination.engines.compass import (
    DUAL_CANDIDATE_THRESHOLD_DEG,
    SANS_24,
    SANS_CENTER_DEG,
    SANS_HALF_WIDTH_DEG,
    SANS_TRIGRAM,
    circular_mean,
    circular_std,
    estimate_declination,
    heading_to_24mountain,
    heading_to_direction,
    list_24_mountains,
    magnetic_to_true_heading,
    normalize_heading,
)
from server.main import app


client = TestClient(app)


# ── 24 山 元数据 ───────────────────────────────────────────────────

class Test24Mountains:
    def test_24_mountains_list(self):
        m = list_24_mountains()
        assert len(m) == 24
        for i, mt in enumerate(m):
            assert mt["sans"] == SANS_24[i]
            assert mt["center_deg"] == i * 15.0
            # 边界 ± 7.5
            assert mt["from_deg"] == (i * 15.0 - SANS_HALF_WIDTH_DEG) % 360
            assert mt["to_deg"] == (i * 15.0 + SANS_HALF_WIDTH_DEG) % 360
            assert mt["trigram"] in {"坎", "艮", "震", "巽", "离", "坤", "兑", "乾"}
            assert mt["element"] in {"水", "火", "木", "金", "土"}


# ── heading → 24 山 (中心区) ─────────────────────────────────────

class TestHeadingTo24Mountain_Center:
    def test_zero_deg_is_zi(self):
        """0° = 子 (正北)."""
        r = heading_to_24mountain(0)
        assert r["sans"] == "子"
        assert r["distance_to_boundary"] == SANS_HALF_WIDTH_DEG
        assert r["dual_candidate"] is False
        assert r["quality"] == "high"
        assert r["trigram"] == "坎"

    def test_90_deg_is_mao(self):
        """90° = 卯 (正东中心)."""
        r = heading_to_24mountain(90)
        assert r["sans"] == "卯"
        assert r["trigram"] == "震"

    def test_75_deg_is_jia(self):
        """75° = 甲 (东偏北)."""
        r = heading_to_24mountain(75)
        assert r["sans"] == "甲"
        assert r["trigram"] == "震"

    def test_180_deg_is_wu(self):
        r = heading_to_24mountain(180)
        assert r["sans"] == "午"
        assert r["trigram"] == "离"

    def test_270_deg_is_you(self):
        r = heading_to_24mountain(270)
        assert r["sans"] == "酉"
        assert r["trigram"] == "兑"

    def test_45_deg_is_gen(self):
        r = heading_to_24mountain(45)
        assert r["sans"] == "艮"

    def test_360_same_as_0(self):
        r1 = heading_to_24mountain(0)
        r2 = heading_to_24mountain(360)
        assert r1["sans"] == r2["sans"]


# ── 临界角双候选 ──────────────────────────────────────────────────

class TestDualCandidateBoundary:
    def test_at_boundary_dual(self):
        """距边界 < 5° → 双候选."""
        # 壬(345°) 与 子(0°) 边界在 352.5° / 7.5°
        # 351° → 距壬中心 345° 偏移 6°, 距边界 1.5° < 5° → dual
        r = heading_to_24mountain(351)
        assert r["sans"] == "壬"
        assert r["dual_candidate"] is True
        assert r["alt_sans"] in ("子", "亥")  # 相邻山
        assert r["distance_to_boundary"] < 5.0

    def test_at_center_no_dual(self):
        """中心 → 无双候选."""
        r = heading_to_24mountain(0)
        assert r["dual_candidate"] is False
        assert r["distance_to_boundary"] == SANS_HALF_WIDTH_DEG

    def test_at_4_deg_from_boundary_dual(self):
        """距边界 4° → dual (< 5°)."""
        # 子山中心 0°, 上界 7.5°
        # 4° → 距上界 3.5° < 5° → dual
        r = heading_to_24mountain(4)
        assert r["sans"] == "子"
        assert r["dual_candidate"] is True

    def test_at_6_deg_from_boundary_no_dual(self):
        """距边界 6° → 不 dual (> 5°)."""
        r = heading_to_24mountain(1.5)  # 距子山上界 6°
        assert r["dual_candidate"] is False


# ── 8 方位 ────────────────────────────────────────────────────────

class TestDirection:
    def test_0_is_north(self):
        assert heading_to_direction(0) == "正北"

    def test_45_is_northeast(self):
        assert heading_to_direction(45) == "东北"

    def test_90_is_east(self):
        assert heading_to_direction(90) == "正东"

    def test_180_is_south(self):
        assert heading_to_direction(180) == "正南"


# ── 磁北 → 真北 (declination) ──────────────────────────────────

class TestMagneticToTrue:
    def test_explicit_declination(self):
        r = magnetic_to_true_heading(
            magnetic_heading_deg=100, lat=31, lng=121, declination=-6.0
        )
        assert r["true_heading"] == 94.0  # 100 + (-6)
        assert r["declination"] == -6.0
        assert r["declination_source"] == "explicit"

    def test_estimated_declination_east_china(self):
        """中国东部 (上海) WMM2025 declination ≈ -3.8°."""
        r = magnetic_to_true_heading(magnetic_heading_deg=100, lat=31, lng=121)
        assert r["declination_source"] == "estimated"
        # WMM2025 高斯球谐展开值 — 比旧表 -6.0 更精确
        assert r["declination"] == pytest.approx(-3.77, abs=0.5)

    def test_estimated_declination_west_china(self):
        """中国西部 (新疆) WMM2025 declination ≈ 0.9°."""
        r = magnetic_to_true_heading(magnetic_heading_deg=100, lat=40, lng=80)
        # WMM2025 值 — 新疆实际磁偏角接近零
        assert r["declination"] == pytest.approx(0.88, abs=0.5)

    def test_estimated_declination_japan(self):
        """日本 (东京) WMM2025 declination ≈ -4.7°."""
        r = magnetic_to_true_heading(magnetic_heading_deg=100, lat=35, lng=139)
        assert r["declination"] == pytest.approx(-4.65, abs=0.5)

    def test_unknown_region_returns_zero(self):
        """大西洋 (0,0) — WMM2025 不再简单回零, 而是给出实际磁偏角."""
        r = magnetic_to_true_heading(magnetic_heading_deg=100, lat=0, lng=0)
        # WMM2025: 尼日利亚/加纳海域 declination ≈ -4.9°
        assert r["declination"] == pytest.approx(-4.85, abs=0.5)


# ── 环形统计 ─────────────────────────────────────────────────────

class TestCircularStats:
    def test_mean_no_wrap(self):
        m = circular_mean([10, 20, 30])
        assert 19 < m < 21

    def test_mean_handles_0_360_boundary(self):
        """350° + 10° 应 ≈ 0° (环形), 不是 180° (算术平均)."""
        m = circular_mean([350, 10, 5, 355])
        assert m < 5 or m > 355  # 接近 0/360

    def test_std_single_sample(self):
        assert circular_std([45]) == 0.0

    def test_std_consistent_samples(self):
        """3 个相同样本 → std=0."""
        assert circular_std([100, 100, 100]) < 0.1

    def test_std_spread_samples(self):
        """大离散 → 大 std."""
        std = circular_std([0, 90, 180, 270])
        assert std > 30


# ── API: 三通道输入 ─────────────────────────────────────────────

class TestMeasureAPI:
    def test_device_channel(self):
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 90,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["input_channel"] == "device"
        assert body["sans"] == "卯"
        assert body["direction"] == "正东"
        assert body["dual_candidate"] is False

    def test_physical_channel(self):
        r = client.post("/api/compass/measure", json={
            "physical_compass_sans": "子",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["input_channel"] == "physical"
        assert body["sans"] == "子"
        assert body["raw_heading"] == 0.0

    def test_physical_invalid_sans(self):
        r = client.post("/api/compass/measure", json={
            "physical_compass_sans": "假山",
        })
        assert r.status_code == 400

    def test_manual_channel(self):
        r = client.post("/api/compass/measure", json={
            "manual_azimuth_deg": 180,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["input_channel"] == "manual"
        assert body["sans"] == "午"

    def test_map_channel(self):
        r = client.post("/api/compass/measure", json={
            "map_direction": "正东",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["input_channel"] == "map"
        assert body["sans"] == "卯"
        assert body["raw_heading"] == 90.0

    def test_no_input_returns_400(self):
        r = client.post("/api/compass/measure", json={})
        assert r.status_code == 400

    def test_dual_candidate_with_warning(self):
        """距边界 < 5° → fengshui_warning 非空."""
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 4.0,  # 距子山上界 3.5°
        })
        assert r.status_code == 200
        body = r.json()
        assert body["dual_candidate"] is True
        assert body["alt_sans"] is not None
        assert "距山界" in body["fengshui_warning"]
        assert "复测" in body["fengshui_warning"]


# ── API: declination 校正 ──────────────────────────────────────

class TestMeasureDeclination:
    def test_explicit_declination_used(self):
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 100,
            "lat": 31, "lng": 121,
            "declination_deg": -10.0,
        })
        body = r.json()
        assert body["declination_deg"] == -10.0
        assert body["declination_source"] == "explicit"
        assert body["true_heading"] == 90.0  # 100 + (-10)

    def test_estimated_declination_china(self):
        r = client.post("/api/compass/measure", json={
            "magnetic_heading_deg": 100,
            "lat": 31, "lng": 121,
        })
        body = r.json()
        # WMM2025: 上海 declination ≈ -3.77° (比旧表 -6.0 精确)
        assert body["declination_deg"] == pytest.approx(-3.77, abs=0.5)
        assert body["declination_source"] == "estimated"


# ── API: 24 山列表 ─────────────────────────────────────────────

class TestListEndpoint:
    def test_get_24_mountains(self):
        r = client.get("/api/compass/24-mountains")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 24
        assert len(body["mountains"]) == 24
        # 第一项: 子 (正北, center 0°)
        assert body["mountains"][0]["sans"] == "子"
        assert body["mountains"][0]["center_deg"] == 0
        # 第二项: 癸 (center 15°)
        assert body["mountains"][1]["sans"] == "癸"
        assert body["mountains"][1]["center_deg"] == 15
        # 最末项: 壬 (center 345°)
        assert body["mountains"][23]["sans"] == "壬"
        assert body["mountains"][23]["center_deg"] == 345


# ── API: convert (向后兼容) ────────────────────────────────────

class TestConvertEndpoint:
    def test_basic_convert(self):
        r = client.get("/api/compass/convert/90")
        body = r.json()
        assert body["sans"] == "卯"
        assert body["trigram"] == "震"

    def test_convert_with_true_north(self):
        """north_ref=true + lat/lng → declination 校正."""
        r = client.get("/api/compass/convert/100?north_ref=true&lat=31&lng=121")
        body = r.json()
        # 100 - 6 = 94 → 应是 甲 (90-105° 中心 97.5°? 不, 中心 90°)
        # 100 在 卯(90) 和 乙(105) 之间, 距卯 10°, 距乙 5°
        # 距边界 7.5 - 5 = 2.5° < 5° → dual
        assert body["sans"] in ("卯", "乙")
        assert body["dual_candidate"] is True


# ── Sprint 3.3: 罗盘 → 风水 端到端 ────────────────────────────────

class TestCompassFengShuiE2E:

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        from divination.cache import get_cache
        get_cache().clear()
        yield
    """端到端: 罗盘测量 → 24 山 → 八宅 + 玄空."""

    def test_device_channel_to_fengshui(self):
        """device 通道 + 出生年 → 八宅+玄空."""
        r = client.post("/api/compass/fengshui", json={
            "magnetic_heading_deg": 90,
            "birth_year": 1984,
            "gender": "male",
            "construction_year": 2020,
        })
        assert r.status_code == 200
        body = r.json()
        # 罗盘层
        assert body["sitting"] == "卯"
        assert body["sitting_zh"] == "卯山"
        assert body["direction"] == "正东"
        assert body["quality"] in ("high", "medium", "low")
        # 风水层
        assert body["bazhai"] is not None
        assert "命卦" in body["bazhai"]
        assert body["xuankong"] is not None
        assert "格局" in body["xuankong"]
        # 摘要
        assert "卯山" in body["fengshui_summary"]
        assert "正东" in body["fengshui_summary"]

    def test_manual_channel_to_fengshui(self):
        """manual 通道 → 风水."""
        r = client.post("/api/compass/fengshui", json={
            "manual_azimuth_deg": 0,
            "birth_year": 1990,
            "gender": "female",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sitting"] == "子"
        assert body["direction"] == "正北"
        assert body["bazhai"] is not None
        assert body["xuankong"] is not None

    def test_map_channel_to_fengshui(self):
        """map 通道 → 风水."""
        r = client.post("/api/compass/fengshui", json={
            "map_direction": "正南",
            "birth_year": 1975,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sitting"] == "午"
        assert body["direction"] == "正南"

    def test_physical_channel_to_fengshui(self):
        """physical 通道 (直接 24 山) → 风水."""
        r = client.post("/api/compass/fengshui", json={
            "physical_compass_sans": "子",
            "birth_year": 1988,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sitting"] == "子"

    def test_dual_candidate_fengshui(self):
        """临界角 → double candidate + warning."""
        r = client.post("/api/compass/fengshui", json={
            "magnetic_heading_deg": 4.0,  # 距子山边界 3.5°
            "birth_year": 1995,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["dual_candidate"] is True
        assert body["alt_sitting"] is not None
        assert body["fengshui_warning"] is not None
        assert "复测" in body["fengshui_warning"]

    def test_explicit_declination(self):
        """显式磁偏角 + 风水."""
        r = client.post("/api/compass/fengshui", json={
            "magnetic_heading_deg": 100,
            "lat": 31, "lng": 121,
            "declination_deg": -10.0,
            "birth_year": 1984,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["declination_deg"] == -10.0
        assert body["true_heading"] == 90.0  # 100 + (-10)

    def test_no_channel_returns_400(self):
        """无输入通道 → 400."""
        r = client.post("/api/compass/fengshui", json={
            "birth_year": 1984,
        })
        assert r.status_code == 400

    def test_invalid_physical_sans_returns_400(self):
        """无效 24 山 → 400."""
        r = client.post("/api/compass/fengshui", json={
            "physical_compass_sans": "假山",
            "birth_year": 1984,
        })
        assert r.status_code == 400

    def test_bazhai_life_gua_correct_for_male_1984(self):
        """1984 男 → 命卦兌 (西四命)."""
        r = client.post("/api/compass/fengshui", json={
            "manual_azimuth_deg": 90,
            "birth_year": 1984,
            "gender": "male",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["bazhai"]["命卦"] == "兌"
        assert body["bazhai"]["命"] == "西四命"

    def test_bazhai_ji_fang_returned(self):
        """八宅吉方/凶方非空."""
        r = client.post("/api/compass/fengshui", json={
            "manual_azimuth_deg": 0,
            "birth_year": 1990,
            "gender": "female",
        })
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body["bazhai"]["吉方"], list)
        assert len(body["bazhai"]["吉方"]) > 0
        assert isinstance(body["bazhai"]["凶方"], list)

    def test_xuankong_period_from_construction_year(self):
        """construction_year 推运."""
        r = client.post("/api/compass/fengshui", json={
            "manual_azimuth_deg": 0,
            "birth_year": 1984,
            "construction_year": 2024,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["xuankong"] is not None
        # 2024 → 九运 (2024-2043)
        assert body["xuankong"].get("运") == 9

    def test_xuankong_explicit_period(self):
        """显式指定玄空运."""
        r = client.post("/api/compass/fengshui", json={
            "manual_azimuth_deg": 0,
            "birth_year": 1984,
            "period": 8,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["xuankong"] is not None
        assert body["xuankong"].get("运") == 8


# ── Sprint 3.3: 路由修复验证 ───────────────────────────────────────

class TestRouterFengShuiMethod:
    """router.py: fengshui 方法应指向复合风水引擎而非单独 bazhai."""

    def test_fengshui_method_exists(self):
        """fengshui 方法注册为复合引擎."""
        from divination.router import _ENGINES
        assert "fengshui" in _ENGINES
        from divination.engines.fengshui import compute as fengshui_compute
        assert _ENGINES["fengshui"] is fengshui_compute

    def test_fengshui_is_not_bazhai(self):
        """fengshui 不应再指向 bazhai.compute."""
        from divination.router import _ENGINES
        from divination.engines.bazhai import compute as bazhai_compute
        assert _ENGINES["fengshui"] is not bazhai_compute

    def test_bazhai_still_registered(self):
        """bazhai 方法仍独立可用."""
        from divination.router import _ENGINES
        assert "bazhai" in _ENGINES
        from divination.engines.bazhai import compute as bazhai_compute
        assert _ENGINES["bazhai"] is bazhai_compute

    def test_xuankong_still_registered(self):
        """xuankong 方法仍独立可用."""
        from divination.router import _ENGINES
        assert "xuankong" in _ENGINES
        from divination.engines.xuankong import compute as xuankong_compute
        assert _ENGINES["xuankong"] is xuankong_compute


# ── Sprint 3.3: Birth 扩展字段 ─────────────────────────────────────

class TestBirthSpaceFields:
    """Birth dataclass 扩展: sitting / facing / construction_year / period."""

    def test_birth_with_sitting(self):
        from divination.contracts import Birth
        b = Birth(year=1984, month=6, day=15, sitting="卯")
        assert b.sitting == "卯"

    def test_birth_with_construction(self):
        from divination.contracts import Birth
        b = Birth(year=1984, month=6, day=15, construction_year=2020)
        assert b.construction_year == 2020

    def test_birth_default_space_fields_none(self):
        from divination.contracts import Birth
        b = Birth(year=1984, month=6, day=15)
        assert b.sitting is None
        assert b.facing is None
        assert b.construction_year is None
        assert b.period is None

    def test_birth_with_all_space_fields(self):
        from divination.contracts import Birth
        b = Birth(year=1984, month=6, day=15, sitting="子", facing="正南",
                  construction_year=2020, period=8, address="北京")
        assert b.sitting == "子"
        assert b.facing == "正南"
        assert b.period == 8
        assert b.address == "北京"


# ── Sprint 3.4: 连续采样 API ──────────────────────────────────────

class TestContinuousSamplingAPI:
    """session API 连续采样 + 统计."""

    def test_create_session_and_add_samples(self):
        """创建会话 → 加样本 → 自动结算 (>=30 样本自动关闭)."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
        })
        assert r.status_code == 200
        sid = r.json()["session_id"]

        # 加 30 个样本 (第 30 个样本后自动关闭)
        for i, az in enumerate([88, 92, 90] * 10):  # 30 samples
            r = client.post(f"/api/compass/sessions/{sid}/samples", json={
                "azimuth_deg": float(az),
            })
            assert r.status_code == 200
            if r.json().get("closed"):
                break  # session 已自动关闭

        # 查结果
        r = client.get(f"/api/compass/sessions/{sid}")
        assert r.status_code == 200
        body = r.json()
        assert body["closed"] is True
        assert len(body["samples"]) >= 30
        assert body["result_sans"] == "卯"
        assert body["result_direction"] == "正东"

    def test_session_not_found(self):
        r = client.get("/api/compass/sessions/nonexistent")
        assert r.status_code == 404

    def test_high_deviation_session(self):
        """大离散样本 → quality=low."""
        r = client.post("/api/compass/sessions", json={
            "direction_hint": "大门朝东",
        })
        sid = r.json()["session_id"]
        for az in [45, 90, 135, 180, 270] * 6:  # 30 samples
            client.post(f"/api/compass/sessions/{sid}/samples", json={"azimuth_deg": float(az)})
        r = client.get(f"/api/compass/sessions/{sid}")
        body = r.json()
        assert body["quality"] == "low"


# ── Sprint 3.4: 编译导出验证 ──────────────────────────────────────

class TestEnginesExports:
    """engines __init__.py 导出所有引擎 (含 compass)."""

    def test_compass_importable(self):
        from divination.engines import compass
        assert compass is not None
        assert hasattr(compass, "heading_to_24mountain")
        assert hasattr(compass, "SANS_24")

    def test_fengshui_importable(self):
        from divination.engines import fengshui
        assert fengshui is not None
        assert hasattr(fengshui, "compute")

    def test_all_engines_importable(self):
        from divination.engines import __all__ as engine_list
        assert "compass" in engine_list
        assert "fengshui" in engine_list
        assert "bazhai" in engine_list
        assert "xuankong" in engine_list


# ── WMM2025 球谐展开测试 (Sprint 4.3) ─────────────────────────

class TestWMM2025Field:
    def test_field_returns_all_keys(self):
        from divination.engines.compass import _wmm_field
        field = _wmm_field(31.0, 121.0, 2025.0)
        for key in ("X", "Y", "Z", "H", "F", "D", "I"):
            assert key in field
            assert isinstance(field[key], float)

    def test_declination_beijing(self):
        """北京 (39.9, 116.4) WMM2025 declination."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(39.9, 116.4, 2025.0)
        # 北京 declination ≈ -3.6° ~ -4.0° (2025)
        assert -5.0 < d < -2.0

    def test_declination_shanghai(self):
        """上海 (31.2, 121.5) WMM2025 declination."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(31.2, 121.5, 2025.0)
        assert -5.0 < d < -2.0

    def test_declination_tokyo(self):
        """东京 (35.7, 139.7) WMM2025 declination."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(35.7, 139.7, 2025.0)
        assert -6.5 < d < -3.5

    def test_declination_london(self):
        """伦敦 (51.5, -0.1) WMM2025 declination — 正值 (东偏)."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(51.5, -0.1, 2025.0)
        # 伦敦 declination ≈ +1° ~ +2° (2025)
        assert 0.0 < d < 3.0

    def test_declination_new_york(self):
        """纽约 (40.7, -74.0) WMM2025 declination — 负值 (西偏)."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(40.7, -74.0, 2025.0)
        # 纽约 declination ≈ -9° ~ -10° (2025)
        assert -12.0 < d < -7.0

    def test_declination_sydney(self):
        """悉尼 (-33.9, 151.2) WMM2025 declination — 正值 (东偏)."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(-33.9, 151.2, 2025.0)
        # 悉尼 declination ≈ +12° ~ +14° (2025)
        assert 10.0 < d < 15.0

    def test_secular_variation(self):
        """长期变化: declination 随年份漂移."""
        from divination.engines.compass import estimate_declination
        d_2025 = estimate_declination(31.0, 121.0, 2025.0)
        d_2028 = estimate_declination(31.0, 121.0, 2028.0)
        # 3 年的 declination 变化应该在 ~0.1° ~ 0.5° 范围
        assert abs(d_2025 - d_2028) < 1.0
        assert d_2025 != d_2028  # 有变化

    def test_high_latitude_stable(self):
        """高纬度 (极地) 不应崩溃."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(80.0, 0.0, 2025.0)
        assert isinstance(d, float)
        assert -180.0 <= d <= 180.0

    def test_equator_stable(self):
        """赤道不应崩溃."""
        from divination.engines.compass import estimate_declination
        d = estimate_declination(0.0, 120.0, 2025.0)
        assert isinstance(d, float)

    def test_get_wmm_full_field(self):
        """get_wmm_full_field 返回完整地磁数据."""
        from divination.engines.compass import get_wmm_full_field
        field = get_wmm_full_field(31.0, 121.0, 2025.0)
        assert field["H"] > 0  # 水平强度恒正
        assert field["F"] > field["H"]  # 总强度 > 水平强度


class TestWMMCache:
    def test_cache_hit(self):
        """相同坐标应命中缓存."""
        from divination.engines.compass import estimate_declination, clear_wmm_cache, _WMM_CACHE
        clear_wmm_cache()
        assert len(_WMM_CACHE) == 0
        d1 = estimate_declination(31.0, 121.0, 2025.0)
        assert len(_WMM_CACHE) >= 1
        d2 = estimate_declination(31.0, 121.0, 2025.0)
        assert len(_WMM_CACHE) >= 1  # 未增加
        assert d1 == d2

    def test_clear_cache(self):
        from divination.engines.compass import estimate_declination, clear_wmm_cache, _WMM_CACHE
        estimate_declination(31.0, 121.0, 2025.0)
        n = clear_wmm_cache()
        assert n > 0
        assert len(_WMM_CACHE) == 0

    def test_cache_key_rounding(self):
        """坐标四舍五入到 0.5° bucket: 31.1 和 31.3 应命中同一 key."""
        from divination.engines.compass import _cache_key
        k1 = _cache_key(31.1, 121.0, 2025.0)
        k2 = _cache_key(31.3, 121.0, 2025.0)
        # 31.1*2=62.2→round→62→/2→31.0
        # 31.3*2=62.6→round→63→/2→31.5
        # 不同 bucket
        assert k1 != k2
        # 31.0 和 31.4 应同一bucket
        k3 = _cache_key(31.0, 121.0, 2025.0)
        k4 = _cache_key(30.9, 121.0, 2025.0)
        assert k3 == k4

    def test_cache_different_years_different_keys(self):
        from divination.engines.compass import _cache_key
        k1 = _cache_key(31.0, 121.0, 2025.0)
        k2 = _cache_key(31.0, 121.0, 2026.0)
        assert k1 != k2


class TestLegacyTableDocumented:
    def test_legacy_table_exists(self):
        """旧版地理区域表保留为文档参考."""
        from divination.engines.compass import _DECLINATION_TABLE_LEGACY
        assert len(_DECLINATION_TABLE_LEGACY) == 4
        assert _DECLINATION_TABLE_LEGACY[0][1] == -1.0  # 新疆
