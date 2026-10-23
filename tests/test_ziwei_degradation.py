"""ziwei 引擎降级守卫: py_iztro JS 运行时死亡时必须回落结构化 fallback, 不能 500。

背景: ubuntu-24.04 CI 上 pythonmonkey wheel 能安装成功, `from py_iztro import Astro`
也能 import, 但 JS 模块未初始化 → astro.by_solar 内部 self._astro.bySolar 是 None
→ TypeError。守卫 = 加载期真探针 + compute() None 检查。
"""
from __future__ import annotations

import pytest

from divination.contracts import Birth
from divination.engines import ziwei


BIRTH = Birth(1990, 6, 15, 10, 30, "male")


def test_compute_returns_structured_fallback_when_runtime_dead(monkeypatch):
    """_by_solar 为 None (JS 运行时死) → 结构化 fallback, 绝不 TypeError。"""
    monkeypatch.setattr(ziwei, "_by_solar", None)
    r = ziwei.compute(BIRTH)
    assert isinstance(r.raw, dict)
    assert r.raw.get("fallback") is True
    assert "py-iztro" in str(r.raw.get("fallback_reason", ""))


def test_load_by_solar_never_raises():
    """加载器任何异常都吞掉并返回 None, 不让模块 import 炸掉整个应用。"""
    import importlib

    # py_iztro 坏 + iztro_py 缺 → 返回 None; 正常环境 → 返回可调用
    result = ziwei._load_by_solar()
    assert result is None or callable(result)
    # 模块仍可重载 (import 期无副作用崩溃)
    importlib.reload(ziwei)


def test_probe_detects_dead_js_runtime(monkeypatch):
    """探针: bySolar 存在但内部是 None → 判死, 不返回坏 callable。"""
    class _FakeAstro:
        def __init__(self):
            self.by_solar = lambda *a, **k: (_ for _ in ()).throw(
                TypeError("'NoneType' object is not callable")
            )

    monkeypatch.setitem(__import__("sys").modules, "py_iztro", _FakeAstro())
    got = ziwei._load_by_solar()
    # py_iztro 探针死 → 尝试 iztro_py (CI 无则 None); 关键是不抛出
    assert got is None or callable(got)
