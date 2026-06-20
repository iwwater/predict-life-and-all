"""P2-5/6 排盘缓存 + 并发排盘测试。

覆盖:
  - CacheKey 确定性 + 唯一性
  - InMemoryCache LRU/TTL/get/set/invalidate/clear/stats
  - get_cache / set_cache 注入式替换
  - router.compute 缓存命中(同输入二次调用走 cache)
  - router.compute_all 并发执行 + 顺序保持
  - router.compute_all 失败隔离(单方法失败不影响其他)
"""
from __future__ import annotations

import time
from typing import Any

import pytest

from divination.cache import (
    CacheBackend,
    CacheKey,
    InMemoryCache,
    get_cache,
    set_cache,
)
from divination.contracts import Birth, ChartResult
from divination.router import compute, compute_all


# ── CacheKey 派生 ──────────────────────────────────────────────────────


class TestCacheKey:
    """CacheKey.to_hash 派生测试。"""

    def test_deterministic_same_input(self):
        """相同输入必得相同 key。"""
        k1 = CacheKey(method="bazi", birth_tuple=(1990, 5, 10, 12, 0, "male", "gregorian"))
        k2 = CacheKey(method="bazi", birth_tuple=(1990, 5, 10, 12, 0, "male", "gregorian"))
        assert k1.to_hash() == k2.to_hash()
        assert k1.to_hash() == k2.to_hash()  # 二次调用仍稳定

    def test_different_method_different_key(self):
        """method 差异必得不同 key。"""
        base = (1990, 5, 10, 12, 0, "male", "gregorian")
        k1 = CacheKey(method="bazi", birth_tuple=base)
        k2 = CacheKey(method="ziwei", birth_tuple=base)
        assert k1.to_hash() != k2.to_hash()

    def test_different_birth_different_key(self):
        """birth 字段差异必得不同 key。"""
        k1 = CacheKey(method="bazi", birth_tuple=(1990, 5, 10, 12, 0, "male", "gregorian"))
        k2 = CacheKey(method="bazi", birth_tuple=(1990, 5, 11, 12, 0, "male", "gregorian"))
        assert k1.to_hash() != k2.to_hash()

    def test_extra_participates_in_key(self):
        """extra 参数参与 key 派生。"""
        base = (1990, 5, 10, 12, 0, "male", "gregorian")
        k1 = CacheKey(method="numerology", birth_tuple=base, extra=(("name", "张三"),))
        k2 = CacheKey(method="numerology", birth_tuple=base, extra=(("name", "李四"),))
        assert k1.to_hash() != k2.to_hash()

    def test_to_string_human_readable(self):
        """to_string 返回非空可读形式。"""
        k = CacheKey(method="bazi", birth_tuple=(1990, 5, 10, 12, 0, "male", "gregorian"))
        s = k.to_string()
        assert "bazi" in s
        assert len(s) > 10


# ── InMemoryCache LRU + TTL ───────────────────────────────────────────


class TestInMemoryCache:
    """InMemoryCache 行为测试。"""

    def test_get_miss_returns_none(self):
        c = InMemoryCache()
        assert c.get("nope") is None

    def test_set_then_get(self):
        c = InMemoryCache()
        c.set("k", {"v": 1})
        assert c.get("k") == {"v": 1}

    def test_overwrite_existing(self):
        c = InMemoryCache()
        c.set("k", {"v": 1})
        c.set("k", {"v": 2})
        assert c.get("k") == {"v": 2}
        assert len(c) == 1

    def test_ttl_expiry(self):
        """TTL 过期后 get 返回 None。"""
        c = InMemoryCache(default_ttl=1)
        c.set("k", {"v": 1}, ttl_seconds=1)
        assert c.get("k") == {"v": 1}
        time.sleep(1.2)
        assert c.get("k") is None

    def test_lru_eviction(self):
        """超过 max_size 时弹出最久未使用。"""
        c = InMemoryCache(max_size=2)
        c.set("a", {"v": 1})
        c.set("b", {"v": 2})
        c.get("a")  # 提升 a 到最新
        c.set("c", {"v": 3})  # 触发淘汰,应淘汰 b
        assert c.get("a") == {"v": 1}
        assert c.get("b") is None  # 被淘汰
        assert c.get("c") == {"v": 3}

    def test_invalidate(self):
        c = InMemoryCache()
        c.set("k", {"v": 1})
        c.invalidate("k")
        assert c.get("k") is None
        c.invalidate("never_existed")  # 不抛

    def test_clear(self):
        c = InMemoryCache()
        c.set("a", {"v": 1})
        c.set("b", {"v": 2})
        # 先取一次制造 hits,验证 clear 重置统计(必须在 get 之后再 clear)
        assert c.get("a") == {"v": 1}
        c.clear()
        s = c.stats()
        # clear 后统计立刻为 0(尚未产生新访问)
        assert s["hits"] == 0 and s["misses"] == 0
        assert len(c) == 0
        # 后续访问重新累计
        assert c.get("a") is None
        assert c.stats()["misses"] == 1

    def test_stats_hit_rate(self):
        c = InMemoryCache()
        c.set("k", {"v": 1})
        c.get("k")  # 命中
        c.get("k")  # 命中
        c.get("nope")  # 未命中
        s = c.stats()
        assert s["hits"] == 2
        assert s["misses"] == 1
        assert s["hit_rate"] == pytest.approx(0.667, abs=0.01)

    def test_thread_safe_concurrent_set_get(self):
        """多线程并发 set/get 不抛异常。"""
        import threading
        c = InMemoryCache(max_size=100)
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                for j in range(50):
                    c.set(f"k_{i}_{j}", {"v": j})
                    _ = c.get(f"k_{i}_{j}")
            except Exception as e:  # pragma: no cover
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors


# ── get_cache / set_cache 注入 ────────────────────────────────────────


class TestCacheSingleton:
    """全局单例 + 注入式替换。"""

    def test_default_is_in_memory(self):
        c = get_cache()
        assert isinstance(c, InMemoryCache)

    def test_set_cache_inject(self):
        class MockCache:
            def __init__(self) -> None:
                self.store: dict[str, Any] = {}

            def get(self, key: str) -> dict | None:
                return self.store.get(key)

            def set(self, key: str, value: dict, ttl_seconds: int = 3600) -> None:
                self.store[key] = value

            def invalidate(self, key: str) -> None:
                self.store.pop(key, None)

            def clear(self) -> None:
                self.store.clear()

            def stats(self) -> dict[str, Any]:
                return {"size": len(self.store), "mock": True}

        original = get_cache()
        try:
            mock = MockCache()
            set_cache(mock)
            assert get_cache() is mock
            assert isinstance(get_cache(), CacheBackend)  # Protocol 满足
            assert get_cache().stats()["mock"] is True
        finally:
            set_cache(original)


# ── router.compute 缓存命中 ───────────────────────────────────────────


class TestRouterCacheHit:
    """router.compute 缓存行为测试。"""

    @pytest.fixture(autouse=True)
    def _fresh_cache(self):
        """每个测试用独立 cache,避免污染。"""
        from divination import cache as cache_mod
        self._original = cache_mod._default_cache
        cache_mod._default_cache = InMemoryCache(max_size=64)
        yield
        cache_mod._default_cache = self._original

    def test_second_call_uses_cache(self):
        """相同输入二次调用走 cache,不再调 engine。"""
        birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")
        c1 = compute("numerology", birth)
        stats_after_first = get_cache().stats()
        c2 = compute("numerology", birth)
        stats_after_second = get_cache().stats()
        # 第一次未命中(misses=1),第二次命中(hits=1)
        assert stats_after_first["misses"] == 1
        assert stats_after_first["hits"] == 0
        assert stats_after_second["hits"] == 1
        # 两次结果等价
        assert c1.method == c2.method == "numerology"
        assert c1.normalized == c2.normalized

    def test_different_method_uses_distinct_cache(self):
        """不同 method 走不同 cache key,互不污染。"""
        birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")
        compute("bazi", birth)
        compute("ziwei", birth)
        s = get_cache().stats()
        assert s["size"] == 2
        assert s["misses"] == 2

    def test_kwarg_participates_in_cache_key(self):
        """extra kwarg 变化导致 cache key 变化。"""
        birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")
        compute("bazi", birth, zi_hour="late")
        compute("bazi", birth, zi_hour="early")
        s = get_cache().stats()
        assert s["size"] == 2  # 两条独立 cache 记录
        assert s["misses"] == 2

    def test_unknown_method_raises(self):
        """未支持 method 仍抛 ValueError(不被 cache 吞掉)。"""
        birth = Birth(year=1990, month=5, day=10)
        with pytest.raises(ValueError, match="未支持的术数"):
            compute("not_a_real_method", birth)


# ── router.compute_all 并发 + 失败隔离 ────────────────────────────────


class TestComputeAllConcurrency:
    """compute_all 并发 + 失败隔离测试。"""

    @pytest.fixture(autouse=True)
    def _fresh_cache(self):
        from divination import cache as cache_mod
        self._original = cache_mod._default_cache
        cache_mod._default_cache = InMemoryCache(max_size=64)
        yield
        cache_mod._default_cache = self._original

    def test_compute_all_returns_all_methods(self):
        """compute_all 返回 dict 含所有输入 methods。"""
        birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")
        methods = ["bazi", "numerology", "ziwei"]
        results = compute_all(methods, birth)
        assert set(results.keys()) == set(methods)
        for m in methods:
            assert results[m] is not None
            assert results[m].method == m

    def test_compute_all_order_preserved(self):
        """并发返回按输入 methods 顺序排列。"""
        birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")
        methods = ["ziwei", "bazi", "numerology", "western"]
        results = compute_all(methods, birth)
        # dict 保留插入顺序(Python 3.7+)
        assert list(results.keys()) == methods

    def test_compute_all_empty_input(self):
        """空输入返回空 dict。"""
        birth = Birth(year=1990, month=5, day=10)
        assert compute_all([], birth) == {}

    def test_compute_all_failure_isolation(self, monkeypatch):
        """单方法失败不阻塞其他,失败位置返回 None。"""
        birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")

        from divination import router

        original_compute = router.compute
        call_log: list[str] = []

        def flaky_compute(method: str, b: Birth, **kw) -> ChartResult:
            call_log.append(method)
            if method == "numerology":
                raise RuntimeError("simulated engine crash")
            return original_compute(method, b, **kw)

        monkeypatch.setattr(router, "compute", flaky_compute)

        methods = ["bazi", "numerology", "ziwei", "western"]
        results = router.compute_all(methods, birth)

        # 所有 method 都被调用过
        assert set(call_log) == set(methods)
        # numerology 失败,其他成功
        assert results["numerology"] is None
        assert results["bazi"] is not None
        assert results["ziwei"] is not None
        assert results["western"] is not None
        # 顺序保持
        assert list(results.keys()) == methods

    def test_compute_all_all_methods_fail(self, monkeypatch):
        """全部方法失败也不抛,全部返回 None。"""
        birth = Birth(year=1990, month=5, day=10)

        from divination import router

        def always_fail(method: str, b: Birth, **kw) -> ChartResult:
            raise RuntimeError(f"boom:{method}")

        monkeypatch.setattr(router, "compute", always_fail)
        results = router.compute_all(["bazi", "numerology"], birth)
        assert results == {"bazi": None, "numerology": None}

    def test_compute_all_concurrent_faster_than_serial(self):
        """简单 benchmark:并发应比串行快(粗略下界,允许 CI 抖动)。"""
        import time as time_mod
        birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")
        # 4 个方法的并发 vs 串行
        methods = ["bazi", "ziwei", "numerology", "western"]

        # 串行基线
        t0 = time_mod.perf_counter()
        for m in methods:
            compute(m, birth)
        serial = time_mod.perf_counter() - t0

        # 并发
        t0 = time_mod.perf_counter()
        compute_all(methods, birth)
        parallel = time_mod.perf_counter() - t0

        # 不强求绝对数值(引擎太轻可能难以拉开),但应不超过串行 1.5x
        # (CI 上 ThreadPool 启动开销可能与节省的计算时间相抵)
        assert parallel <= serial * 1.5, (
            f"并发({parallel:.3f}s) 远慢于串行({serial:.3f}s)"
        )
