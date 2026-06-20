"""排盘缓存层：同盘同问幂等，省 LLM 与重算。

设计原则:
  - Protocol 抽象 backend(测试 / 部署可注入)
  - 默认 InMemoryCache(LRU + TTL)
  - FileCache / RedisCache 接口已留,本期不实现
  - 引擎函数本身不感知 cache,由 router 层注入

典型用法:
    from divination.cache import get_cache, set_cache, CacheKey

    cache = get_cache()
    key = CacheKey(method="bazi", birth_tuple=birth.to_tuple(), extra=()).to_hash()
    cached = cache.get(key)
    if cached is not None:
        return cached
    result = compute_engine(...)
    cache.set(key, result.to_dict())
"""
from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
from threading import RLock
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "CacheKey",
    "CacheBackend",
    "InMemoryCache",
    "get_cache",
    "set_cache",
]


# ── Key 派生 ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CacheKey:
    """排盘缓存键。method + birth 字段 + 额外参数一起派生 sha256。

    设计: dataclass(frozen=True) 保证哈希稳定;extra 用 tuple 强约束可哈希。
    """

    method: str
    birth_tuple: tuple
    extra: tuple = ()

    def to_hash(self) -> str:
        """派生 sha256 缓存键。相同输入必得相同 key。"""
        payload = {
            "method": self.method,
            "birth": list(self.birth_tuple),
            "extra": list(self.extra),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return sha256(raw.encode("utf-8")).hexdigest()

    def to_string(self) -> str:
        """人类可读形式(调试用)。"""
        return f"{self.method}:{self.birth_tuple[:4]}:{self.to_hash()[:12]}"


# ── Backend Protocol ──────────────────────────────────────────────────


@runtime_checkable
class CacheBackend(Protocol):
    """缓存后端协议。任何满足该协议的对象都可被注入。

    实现要点:
      - get 返回 None 表示未命中(或已过期)
      - set 必须容忍 None value(实现可选择静默丢弃)
      - invalidate / clear 用于测试与运维
    """

    def get(self, key: str) -> dict | None:
        """取缓存值,过期或不存在返回 None。"""
        ...

    def set(self, key: str, value: dict, ttl_seconds: int = 3600) -> None:
        """写入缓存。ttl_seconds=0 表示永不过期(慎用)。"""
        ...

    def invalidate(self, key: str) -> None:
        """删除单条缓存。"""
        ...

    def clear(self) -> None:
        """清空全部缓存(测试 / 部署切换时用)。"""
        ...

    def stats(self) -> dict[str, Any]:
        """返回命中 / 未命中 / 容量等统计。"""
        ...


# ── 默认实现: 内存 LRU + TTL ──────────────────────────────────────────


class InMemoryCache:
    """LRU + TTL 内存缓存。线程安全(default 实现可被多线程 router 共享)。

    内部用 OrderedDict 实现 LRU:每次访问移动到末尾;超过 max_size 时弹出头部。
    每条记录携带 expires_at 时间戳;get 时惰性检查是否过期。
    """

    def __init__(self, max_size: int = 256, default_ttl: int = 3600) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: OrderedDict[str, tuple[dict, float]] = OrderedDict()
        self._lock = RLock()
        self._hits = 0
        self._misses = 0

    # ── CacheBackend 接口 ──

    def get(self, key: str) -> dict | None:
        """取缓存。命中且未过期则返回 value 并提升 LRU 位置;否则 None。"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expires_at = entry
            if expires_at > 0 and expires_at < time.time():
                # 过期:惰性删除
                del self._store[key]
                self._misses += 1
                return None
            # 命中:移动到末尾(最近使用)
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: dict, ttl_seconds: int = 3600) -> None:
        """写入缓存。ttl<=0 表示永不过期。"""
        if value is None:
            return
        ttl = ttl_seconds if ttl_seconds > 0 else self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else 0.0
        with self._lock:
            if key in self._store:
                # 更新:移动到末尾
                self._store.move_to_end(key)
            self._store[key] = (value, expires_at)
            # LRU 淘汰
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """删除单条缓存(不存在静默成功)。"""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """清空全部缓存并重置统计。"""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, Any]:
        """返回当前统计快照。"""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._store),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total else 0.0,
            }

    # ── 调试辅助 ──

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._store


# ── 全局单例 + 注入式替换 ─────────────────────────────────────────────


_default_cache: CacheBackend = InMemoryCache()


def get_cache() -> CacheBackend:
    """获取全局缓存单例(默认 InMemoryCache)。"""
    return _default_cache


def set_cache(backend: CacheBackend) -> None:
    """注入自定义 backend(测试用 mock、生产可换 Redis)。

    注意:不会清空旧 backend 数据;调用方需自行处理迁移。
    """
    global _default_cache
    _default_cache = backend
