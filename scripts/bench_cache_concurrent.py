"""P2-5/6 性能 benchmark: 并发 compute_all vs 串行 compute。

区分两个场景:
  - cold: 每次都换 birth,保证 cache miss
  - warm: 同 birth 重复调,观察 cache hit 效果

运行:
    .venv/Scripts/python.exe scripts/bench_cache_concurrent.py
"""
from __future__ import annotations

import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from divination.cache import InMemoryCache, get_cache, set_cache  # noqa: E402
from divination.contracts import Birth  # noqa: E402
from divination.router import compute, compute_all  # noqa: E402


def _print(label: str, ts: list[float]) -> None:
    print(f"  {label:<10} mean={statistics.mean(ts)*1000:7.1f}ms  "
          f"min={min(ts)*1000:7.1f}ms  max={max(ts)*1000:7.1f}ms")


def main() -> None:
    set_cache(InMemoryCache(max_size=512))
    methods = ["bazi", "ziwei", "numerology", "western", "vedic", "qimen", "liuyao", "meihua"]
    n = 5

    print(f"=== compute_all benchmark (n={n}, methods={len(methods)}) ===\n")

    # ── cold scenario: 每次新 birth,cache miss(每轮前清空 cache) ──
    print("[cold] 每次换 birth (cache miss, 每轮前 clear):")
    cold_serial: list[float] = []
    cold_parallel: list[float] = []
    for i in range(n):
        get_cache().clear()
        birth = Birth(year=1990 + i, month=5, day=10, hour=12, minute=0, gender="male")
        t0 = time.perf_counter()
        for m in methods:
            compute(m, birth)
        cold_serial.append(time.perf_counter() - t0)

        get_cache().clear()
        t0 = time.perf_counter()
        compute_all(methods, birth)
        cold_parallel.append(time.perf_counter() - t0)
    _print("serial", cold_serial)
    _print("parallel", cold_parallel)
    print(f"  speedup : {statistics.mean(cold_serial) / statistics.mean(cold_parallel):.2f}x\n")

    # ── warm scenario: 同 birth 重复调 ──
    print("[warm] 同 birth 重复 (cache hit):")
    birth = Birth(year=1990, month=5, day=10, hour=12, minute=0, gender="male")
    # 预热
    for m in methods:
        compute(m, birth)

    warm_serial: list[float] = []
    warm_parallel: list[float] = []
    for i in range(n):
        t0 = time.perf_counter()
        for m in methods:
            compute(m, birth)
        warm_serial.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        compute_all(methods, birth)
        warm_parallel.append(time.perf_counter() - t0)
    _print("serial", warm_serial)
    _print("parallel", warm_parallel)
    print(f"  speedup : {statistics.mean(warm_serial) / statistics.mean(warm_parallel):.2f}x\n")

    # ── cache stats ──
    s = get_cache().stats()
    print(f"[cache] {s}")


if __name__ == "__main__":
    main()
