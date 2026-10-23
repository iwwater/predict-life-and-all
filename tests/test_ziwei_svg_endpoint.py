"""GET /api/ziwei/svg 端点回归测试 — 紫微盘 SVG 直出.

锁定:
1. 四种盘型 (traditional/wheel/grid/star_map) 各自可渲染, 输出为合法 SVG
2. 五个运程 scope (natal/decadal/yearly/monthly/xiaoxian) 可渲染
3. 非 natal scope 固定方盘布局 (style 参数被忽略, 不报错)
4. 非法 style/scope 返回 422
5. SVG 直出 media type 为 image/svg+xml, 同参数可缓存
6. 小限盘接受显式 age, 且按出生年自动推算不崩
"""
from __future__ import annotations

from fastapi.testclient import TestClient

BIRTH_QS = "year=1990&month=6&day=15&hour=8&minute=30&gender=male"


def _client() -> TestClient:
    from server.main import app
    return TestClient(app)


def _get(client: TestClient, qs: str):
    return client.get(f"/api/ziwei/svg?{qs}")


class TestZiweiSvgStyles:
    def test_all_four_styles_render_svg(self):
        client = _client()
        for style in ("traditional", "wheel", "grid", "star_map"):
            r = _get(client, f"{BIRTH_QS}&style={style}")
            assert r.status_code == 200, f"style={style}: {r.status_code} {r.text[:200]}"
            assert "svg" in r.headers.get("content-type", ""), style
            body = r.text
            assert body.lstrip().startswith("<svg"), f"style={style} not svg root"
            assert "</svg>" in body, style
            assert 'xmlns' in body, style

    def test_invalid_style_422(self):
        client = _client()
        r = _get(client, f"{BIRTH_QS}&style=fancy")
        assert r.status_code == 422

    def test_invalid_scope_422(self):
        client = _client()
        r = _get(client, f"{BIRTH_QS}&scope=lifetime")
        assert r.status_code == 422


class TestZiweiSvgScopes:
    def test_all_five_scopes_render(self):
        client = _client()
        for scope in ("natal", "decadal", "yearly", "monthly", "xiaoxian"):
            r = _get(client, f"{BIRTH_QS}&scope={scope}")
            assert r.status_code == 200, f"scope={scope}: {r.status_code} {r.text[:200]}"
            assert r.text.lstrip().startswith("<svg"), scope
            label = {
                "natal": "本命盘", "decadal": "大限盘", "yearly": "流年盘",
                "monthly": "流月盘", "xiaoxian": "小限盘",
            }[scope]
            assert label in r.text, f"scope={scope} missing label {label}"

    def test_non_natal_scope_ignores_style(self):
        """非 natal scope 固定方盘布局, style=wheel 不 422 也不 TypeError."""
        client = _client()
        r = _get(client, f"{BIRTH_QS}&style=wheel&scope=decadal")
        assert r.status_code == 200
        assert "大限盘" in r.text

    def test_xiaoxian_explicit_age(self):
        client = _client()
        r = _get(client, f"{BIRTH_QS}&scope=xiaoxian&age=36")
        assert r.status_code == 200
        assert "虚岁36" in r.text

    def test_xiaoxian_auto_age(self):
        client = _client()
        r = _get(client, f"{BIRTH_QS}&scope=xiaoxian")
        assert r.status_code == 200
        assert "虚岁" in r.text


class TestZiweiSvgContract:
    def test_media_type_and_cache_header(self):
        client = _client()
        r = _get(client, BIRTH_QS)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/svg+xml")
        assert "max-age" in r.headers.get("cache-control", "")

    def test_deterministic_same_params(self):
        client = _client()
        a = _get(client, f"{BIRTH_QS}&size=640").text
        b = _get(client, f"{BIRTH_QS}&size=640").text
        assert a == b, "same params should render identical SVG"

    def test_size_bounds_422(self):
        client = _client()
        assert _get(client, f"{BIRTH_QS}&size=100").status_code == 422
        assert _get(client, f"{BIRTH_QS}&size=2000").status_code == 422

    def test_missing_required_year_422(self):
        client = _client()
        r = client.get("/api/ziwei/svg?month=6&day=15")
        assert r.status_code == 422
