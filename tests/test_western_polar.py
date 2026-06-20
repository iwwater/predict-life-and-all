"""Tests for Placidus极区处理 (P3-12).

Tests cover:
  - is_polar_region function
  - compute_polar_houses function
  - western.py compute() polar warning output

Reference: Placidus半弧公式在极区 (|lat|>66°33') 因永昼/永夜失效。
"""

from __future__ import annotations

import pytest


# ══════════════════════════════════════════════════════════════
# 1. is_polar_region tests
# ══════════════════════════════════════════════════════════════


class TestIsPolarRegion:
    """Test is_polar_region function."""

    def test_import_exists(self):
        """Can import is_polar_region."""
        from divination.engines.western import is_polar_region
        assert callable(is_polar_region)

    def test_equator_not_polar(self):
        """Equator (lat=0) is not polar."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(0.0) is False

    def test_mid_latitude_not_polar(self):
        """Mid latitudes (e.g., Beijing 40°) are not polar."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(40.0) is False

    def test_arctic_circle_is_polar(self):
        """Latitude exactly at Arctic Circle (66.6°) is polar."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(66.6) is True

    def test_north_pole_is_polar(self):
        """North Pole (90°) is polar."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(90.0) is True

    def test_south_pole_is_polar(self):
        """South Pole (-90°) is polar."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(-90.0) is True

    def test_just_below_arctic_not_polar(self):
        """Latitude just below arctic circle (66.0°) is NOT polar."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(66.0) is False

    def test_southern_high_latitude(self):
        """Southern high latitude (-70°) is polar."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(-70.0) is True

    def test_boundary_precision(self):
        """Boundary at >66.55 is polar, 66.54 is not."""
        from divination.engines.western import is_polar_region
        assert is_polar_region(66.56) is True
        assert is_polar_region(66.54) is False


# ══════════════════════════════════════════════════════════════
# 2. compute_polar_houses tests
# ══════════════════════════════════════════════════════════════


class TestComputePolarHouses:
    """Test compute_polar_houses function."""

    def test_import_exists(self):
        """Can import compute_polar_houses."""
        from divination.engines.western import compute_polar_houses
        assert callable(compute_polar_houses)

    def test_returns_list_of_12(self):
        """Returns list of 12 houses."""
        from divination.engines.western import compute_polar_houses
        houses = compute_polar_houses(ramc_deg=0.0, lat_deg=70.0, asc_lon=30.0)
        assert len(houses) == 12

    def test_each_house_has_required_fields(self):
        """Each house dict has house, cusp_lon, and sign."""
        from divination.engines.western import compute_polar_houses
        houses = compute_polar_houses(ramc_deg=50.0, lat_deg=75.0, asc_lon=120.0)
        for h in houses:
            assert "house" in h
            assert "cusp_lon" in h
            assert "sign" in h
            assert 1 <= h["house"] <= 12

    def test_equal_spacing(self):
        """Houses are equally spaced at ~30° intervals."""
        from divination.engines.western import compute_polar_houses
        houses = compute_polar_houses(ramc_deg=10.0, lat_deg=80.0, asc_lon=45.0)
        for i in range(12):
            expected_lon = (45.0 + 30 * i) % 360
            assert abs(houses[i]["cusp_lon"] - expected_lon) < 0.1


# ══════════════════════════════════════════════════════════════
# 3. Western engine polar integration tests
# ══════════════════════════════════════════════════════════════


class TestWesternPolarIntegration:
    """Test western compute() with polar latitudes."""

    def test_polar_birth_produces_warning(self):
        """Birth at polar latitude produces polar_warning in raw."""
        from divination.contracts import Birth
        from divination.engines.western import compute
        b = Birth(year=1990, month=6, day=15, hour=12,
                  lat=70.0, lng=25.0)
        result = compute(b)
        assert "polar_warning" in result.raw

    def test_polar_warning_is_not_none_for_polar(self):
        """polar_warning is not None when lat is polar."""
        from divination.contracts import Birth
        from divination.engines.western import compute
        b = Birth(year=1990, month=6, day=15, hour=12,
                  lat=75.0, lng=30.0)
        result = compute(b)
        warning = result.raw["polar_warning"]
        assert warning is not None
        assert warning.get("is_polar") is True
        assert "warning" in warning
        assert "house_system_fallback" in warning

    def test_non_polar_birth_no_warning(self):
        """Birth at normal latitude has polar_warning = None."""
        from divination.contracts import Birth
        from divination.engines.western import compute
        b = Birth(year=1990, month=6, day=15, hour=12,
                  lat=40.0, lng=116.0)
        result = compute(b)
        assert result.raw.get("polar_warning") is None

    def test_no_lat_no_warning(self):
        """Birth without lat has polar_warning = None."""
        from divination.contracts import Birth
        from divination.engines.western import compute
        b = Birth(year=1990, month=6, day=15, hour=12)
        result = compute(b)
        assert result.raw.get("polar_warning") is None
