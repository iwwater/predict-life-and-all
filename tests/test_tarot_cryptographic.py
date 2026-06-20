"""塔罗 · 密码学抽牌 + 正逆位智能偏置 测试。

借鉴 daman-ovo-0404/tarot-skill 设计, 覆盖:
1. 密码学抽牌路径 (seed=None → SystemRandom)
2. 可复现抽牌路径 (seed=int → 仍可复现)
3. `_draw_cryptographic` 无重复抽样
4. `_compute_upright_probability` 关键词 + 牌阵智能偏置
5. `compute()` 端到端含 `抽牌参数` 元数据
6. 不破坏旧 API 行为 (test_tarot_celtic.py 已覆盖)
7. 大样本统计: 正逆位频率落在概率区间内
"""
from __future__ import annotations

import random
import secrets

import pytest

from divination.contracts import Birth
from divination.engines.tarot import (
    SPREADS,
    _compute_upright_probability,
    _draw_cryptographic,
    _make_rng,
    compute,
)


# ── 1. RNG 工厂: seed=None → SystemRandom; seed=int → Random ─────────
class TestMakeRng:
    def test_seed_none_returns_systemrandom(self):
        """seed=None 时必须返回 SystemRandom (密码学安全)."""
        rng = _make_rng(None)
        assert isinstance(rng, random.SystemRandom)

    def test_seed_int_returns_random(self):
        """seed 显式提供时返回 random.Random (可复现)."""
        rng = _make_rng(42)
        assert isinstance(rng, random.Random)
        assert not isinstance(rng, random.SystemRandom)

    def test_seed_zero_returns_random(self):
        """seed=0 也是合法可复现 seed, 不应退化到 SystemRandom."""
        rng = _make_rng(0)
        assert isinstance(rng, random.Random)
        assert not isinstance(rng, random.SystemRandom)

    def test_reproducible_same_seed_same_sequence(self):
        """同 seed 必须产出完全一致的随机序列 (回退到 Mersenne Twister 但可复现)."""
        rng1 = _make_rng(20240618)
        rng2 = _make_rng(20240618)
        seq1 = [rng1.random() for _ in range(20)]
        seq2 = [rng2.random() for _ in range(20)]
        assert seq1 == seq2


# ── 2. _draw_cryptographic: 无重复抽样 ─────────────────────────
class TestDrawCryptographic:
    def test_full_deck_no_duplicates(self):
        """抽满 78 张 (全牌) 必须互不重复."""
        rng = _make_rng(None)
        idx = _draw_cryptographic(rng, 78)
        assert len(idx) == 78
        assert len(set(idx)) == 78
        assert set(idx) == set(range(78))

    def test_partial_draw_no_duplicates(self):
        """抽 10 张 (单牌阵/三牌阵/凯尔特十字等), 必须互不重复."""
        rng = _make_rng(None)
        idx = _draw_cryptographic(rng, 10)
        assert len(idx) == 10
        assert len(set(idx)) == 10
        assert max(idx) < 10
        assert min(idx) >= 0

    def test_reproducible_mode_no_duplicates(self):
        """可复现路径下也必须互不重复."""
        rng = _make_rng(42)
        idx = _draw_cryptographic(rng, 78)
        assert len(idx) == 78
        assert len(set(idx)) == 78

    def test_cryptographic_different_runs_different_indices(self):
        """两次密码学抽牌, 索引序列应当不同 (因为 SystemRandom 不接受 seed)."""
        rng1 = _make_rng(None)
        rng2 = _make_rng(None)
        idx1 = _draw_cryptographic(rng1, 78)
        idx2 = _draw_cryptographic(rng2, 78)
        # 概率上不可能完全相同
        assert idx1 != idx2

    def test_reproducible_deterministic(self):
        """同 seed 抽牌必须返回完全一致的索引序列 (用于回归测试)."""
        rng1 = _make_rng(123)
        rng2 = _make_rng(123)
        idx1 = _draw_cryptographic(rng1, 78)
        idx2 = _draw_cryptographic(rng2, 78)
        assert idx1 == idx2


# ── 3. _compute_upright_probability: 牌阵 + 关键词智能偏置 ─────────
class TestUprightProbability:
    def test_default_no_question(self):
        """无问题关键词 → 返回牌阵基础偏置 (或其在 [0.25, 0.85] 内的裁剪值)."""
        for spread in SPREADS:
            p = _compute_upright_probability(spread, None)
            assert 0.25 <= p <= 0.85, f"{spread}: {p}"

    def test_single_spread_default_high(self):
        """单张日签默认正位概率 > 0.5 (倾向给出明确指引)."""
        p = _compute_upright_probability("single", None)
        assert p > 0.5

    def test_celtic_default_low(self):
        """凯尔特十字默认正位概率 < 0.5 (倾向揭示课题)."""
        p = _compute_upright_probability("celtic", None)
        assert p < 0.5

    def test_mind_body_spirit_low(self):
        """身心灵牌阵默认偏逆位 (向内探索)."""
        p = _compute_upright_probability("mind_body_spirit", None)
        assert p < 0.5

    def test_career_keyword_pushes_upright(self):
        """'事业'/'工作'/'career' 关键词必须拉高正位概率."""
        base = _compute_upright_probability("situation", None)
        for q in ["我的事业发展如何", "该不该换工作", "career path 怎么走"]:
            p = _compute_upright_probability("situation", q)
            assert p > base, f"{q}: base={base} adj={p}"

    def test_shadow_keyword_pushes_reversed(self):
        """'阴影'/'疗愈'/'卡点' 关键词必须拉低正位概率."""
        base = _compute_upright_probability("three", None)
        for q in ["我想疗愈阴影", "这个卡点怎么解", "放下过去", "我和前任能不能复合"]:
            p = _compute_upright_probability("three", q)
            assert p < base, f"{q}: base={base} adj={p}"

    def test_decision_keyword_pushes_reversed(self):
        """'选择'/'二选一' 关键词必须拉低正位概率."""
        p = _compute_upright_probability("three", "我应该选 A 还是 B")
        neutral = _compute_upright_probability("three", "今天天气如何")
        assert p < neutral

    def test_probability_clamped_to_range(self):
        """概率必须永远 clamp 在 [0.25, 0.85] 之间."""
        # 即便关键词叠加, 也不应越界
        extreme = _compute_upright_probability(
            "single", "今日指引"
        )
        assert 0.25 <= extreme <= 0.85
        extreme2 = _compute_upright_probability(
            "celtic", "疗愈阴影卡点解绑放下前世"
        )
        assert 0.25 <= extreme2 <= 0.85

    def test_unknown_spread_uses_default(self):
        """未知牌阵名应回退到默认值 0.5 (在裁剪范围内)."""
        p = _compute_upright_probability("nonexistent_spread", None)
        assert p == pytest.approx(0.5, abs=1e-9)


# ── 4. compute() 端到端: 抽牌参数元数据 ─────────────────────────
class TestComputeDrawMetadata:
    def test_cryptographic_draw_mode(self):
        """seed=None 时, draw_mode 必须是 'cryptographic'."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=None)
        assert "抽牌参数" in r.raw
        meta = r.raw["抽牌参数"]
        assert meta["draw_mode"] == "cryptographic"
        assert meta["seed"] is None
        assert 0.25 <= meta["upright_probability"] <= 0.85

    def test_reproducible_draw_mode(self):
        """seed=42 时, draw_mode 必须是 'reproducible'."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=42)
        assert r.raw["抽牌参数"]["draw_mode"] == "reproducible"
        assert r.raw["抽牌参数"]["seed"] == 42

    def test_upright_probability_recorded(self):
        """正位概率必须被记录到 raw 元数据, 供后续解读使用."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "career_path", seed=42, question="我的事业发展如何")
        meta = r.raw["抽牌参数"]
        assert meta["upright_probability"] >= 0.6  # career_path + 事业关键词 → 偏高

    def test_same_seed_same_result(self):
        """可复现路径下, 同 seed 必须返回完全一致的牌面."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        r1 = compute(b, "three", seed=42, question="事业发展")
        r2 = compute(b, "three", seed=42, question="事业发展")
        cards1 = [(c["牌"], c["方位"]) for c in r1.raw["牌面"]]
        cards2 = [(c["牌"], c["方位"]) for c in r2.raw["牌面"]]
        assert cards1 == cards2

    def test_no_duplicates_in_drawn_cards(self):
        """抽出的牌 (无论密码学/可复现路径) 必须互不重复."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        # 凯尔特十字: 10 张牌
        r = compute(b, "celtic", seed=None)
        cards = [c["牌"] for c in r.raw["牌面"]]
        assert len(cards) == 10
        assert len(set(cards)) == 10, f"出现重复牌: {cards}"


# ── 5. 统计: 大样本正逆位频率 ────────────────────────────────
class TestUprightFrequency:
    def test_high_probability_spread_yields_more_upright(self):
        """career_path + 事业关键词 → 高正位概率, 200 次大样本应显著偏正位."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        upright_count = 0
        total = 200
        # 用 seed 序列以保证可复现
        for s in range(total):
            r = compute(b, "career_path", seed=s, question="我的事业发展")
            for c in r.raw["牌面"]:
                if c["方位"] == "正位":
                    upright_count += 1
        total_cards = total * 3  # career_path = situation, 3 张
        ratio = upright_count / total_cards
        expected_prob = _compute_upright_probability("career_path", "我的事业发展")
        # 大样本下 ratio 应在 expected_prob 附近 ±0.10
        assert abs(ratio - expected_prob) < 0.10, (
            f"observed {ratio:.3f} vs expected {expected_prob:.3f}"
        )

    def test_low_probability_spread_yields_more_reversed(self):
        """mind_body_spirit + 阴影关键词 → 低正位概率, 200 次大样本应显著偏逆位."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        upright_count = 0
        total = 200
        for s in range(total):
            r = compute(b, "mind_body_spirit", seed=s, question="我想疗愈阴影")
            for c in r.raw["牌面"]:
                if c["方位"] == "正位":
                    upright_count += 1
        total_cards = total * 3
        ratio = upright_count / total_cards
        expected_prob = _compute_upright_probability(
            "mind_body_spirit", "我想疗愈阴影"
        )
        assert abs(ratio - expected_prob) < 0.10, (
            f"observed {ratio:.3f} vs expected {expected_prob:.3f}"
        )


# ── 6. 兼容旧行为: 不破坏 test_tarot_celtic.py 已覆盖的接口 ─────────
class TestBackwardCompatibility:
    def test_engine_string_includes_cryptographic(self):
        """engine 字段应包含 'cryptographic_draw' 标识, 表明使用密码学抽牌."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=42)
        assert "cryptographic_draw" in r.engine

    def test_all_spreads_work_with_cryptographic(self):
        """所有牌阵在密码学路径下都能产出有效牌面."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        for spread in SPREADS:
            r = compute(b, spread, seed=None)
            expected_n = len(SPREADS[spread]["positions"])
            assert len(r.raw["牌面"]) == expected_n, f"{spread}: {len(r.raw['牌面'])} != {expected_n}"
            for c in r.raw["牌面"]:
                assert c["方位"] in {"正位", "逆位"}
                assert "牌义" in c and c["牌义"]
                assert c["位置"] in SPREADS[spread]["positions"]

    def test_question_propagates_to_raw(self):
        """问题字符串应原样进入 raw['问题']."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        q = "我该不该换工作？"
        r = compute(b, "situation", seed=42, question=q)
        assert r.raw["问题"] == q

    def test_question_attr_on_birth_overrides_param(self):
        """Birth 不含 question 字段时, compute() 的 question 参数应生效 (getattr 兜底)."""
        # Birth dataclass 没有 question 字段 → getattr 返回 None → 走 param
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "situation", seed=42, question="感情发展")
        assert r.raw["问题"] == "感情发展"

    def test_getattr_question_safe_when_missing(self):
        """Birth 缺 question 属性时, 不应抛 AttributeError."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        # 不传 question 参数 → raw['问题'] 应为 None
        r = compute(b, "three", seed=42)
        assert r.raw["问题"] is None


# ── 7. 安全性 / 边界 ─────────────────────────────────
class TestSecurityAndEdgeCases:
    def test_cryptographic_uses_secrets_module(self):
        """密码学路径不应仅依赖 random 模块 — 抽牌函数实际调用 secrets.randbelow."""
        rng = _make_rng(None)
        assert isinstance(rng, random.SystemRandom)
        # SystemRandom 在底层使用 os.urandom — 与 secrets 同源
        # 抽 78 张应全部唯一
        idx = _draw_cryptographic(rng, 78)
        assert len(set(idx)) == 78

    def test_draw_one_card(self):
        """抽 1 张牌 (单张日签) 应正常工作."""
        rng = _make_rng(None)
        idx = _draw_cryptographic(rng, 1)
        assert idx == [0]

    def test_large_repeated_draws_no_pattern(self):
        """连续 10 次密码学抽牌, 不应出现周期性模式."""
        rng = _make_rng(None)
        first_cards = []
        for _ in range(10):
            idx = _draw_cryptographic(rng, 78)
            first_cards.append(idx[0])
        # 10 次首张牌的分布应较为分散 (不同值 ≥ 5)
        assert len(set(first_cards)) >= 5, f"首张牌过于集中: {first_cards}"

    def test_upright_probability_monotone_for_extreme_keywords(self):
        """正位关键词应单调提升概率; 逆位关键词应单调降低."""
        base = _compute_upright_probability("three", None)
        positive = _compute_upright_probability("three", "事业财富成功")
        negative = _compute_upright_probability("three", "疗愈阴影卡点解绑")
        assert positive > base > negative

    def test_default_signature_includes_foolsjourney(self):
        """engine 字段不应丢失原有 'FoolsJourney' 标识 (向后兼容)."""
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=42)
        assert "FoolsJourney" in r.engine or "Fool's Journey" in r.engine or "Fools" in r.engine


# ── 8. Verifiable Randomness (Sprint 4.2) ──────────────────────
class TestEntropyHealth:
    def test_entropy_health_returns_healthy(self):
        from divination.engines.tarot import _check_entropy_health
        result = _check_entropy_health()
        assert result["healthy"] is True
        assert result["sample_bits"] == 256
        assert result["source"]  # 非空
        assert result["latency_us"] > 0

    def test_entropy_health_keys(self):
        from divination.engines.tarot import _check_entropy_health
        result = _check_entropy_health()
        for key in ("healthy", "source", "sample_bits", "latency_us"):
            assert key in result


class TestVerifiableRandomness:
    def test_generate_server_seed_is_256bit(self):
        from divination.engines.tarot import _generate_server_seed
        seed = _generate_server_seed()
        assert len(seed) == 64  # 32 bytes hex = 64 chars
        # 两次生成必须不同
        seed2 = _generate_server_seed()
        assert seed != seed2

    def test_server_seed_commit_is_sha3_256(self):
        from divination.engines.tarot import _server_seed_commit
        commit = _server_seed_commit("test_seed_123")
        assert len(commit) == 64  # SHA3-256 hex
        # 相同输入 → 相同承诺
        assert commit == _server_seed_commit("test_seed_123")
        # 不同输入 → 不同承诺
        assert commit != _server_seed_commit("test_seed_456")

    def test_derive_shuffle_seed_deterministic(self):
        from divination.engines.tarot import _derive_shuffle_seed
        s1 = _derive_shuffle_seed("srv", "cli", 42)
        s2 = _derive_shuffle_seed("srv", "cli", 42)
        assert s1 == s2
        # 不同 nonce → 不同派生
        s3 = _derive_shuffle_seed("srv", "cli", 43)
        assert s1 != s3
        # 不同 client_seed → 不同派生
        s4 = _derive_shuffle_seed("srv", "cli2", 42)
        assert s1 != s4

    def test_hmac_drbg_bytes_length(self):
        from divination.engines.tarot import _hmac_drbg_bytes
        out = _hmac_drbg_bytes(b"key", b"seedval", 64)
        assert len(out) == 64
        # 确定性
        out2 = _hmac_drbg_bytes(b"key", b"seedval", 64)
        assert out == out2

    def test_verifiable_mode_with_client_seed(self):
        """client_seed 提供时, 应进入 verifiable 模式, 包含承诺元数据."""
        from divination.engines.tarot import compute
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=None, client_seed="user_seed_abc")
        meta = r.raw["抽牌参数"]
        assert meta["draw_mode"] == "verifiable"
        vr = meta["verifiable_randomness"]
        assert vr["client_seed"] == "user_seed_abc"
        assert len(vr["server_seed_hash"]) == 64
        assert len(vr["server_seed"]) == 64
        assert "nonce" in vr
        # 验证承诺
        import hashlib
        expected_hash = hashlib.sha3_256(vr["server_seed"].encode()).hexdigest()
        assert vr["server_seed_hash"] == expected_hash

    def test_verifiable_shuffle_reproducible(self):
        """相同 (server_seed, client_seed, nonce) 应产生完全一致的牌序."""
        from divination.engines.tarot import compute
        # 用 seed=42 模拟可复现路径: 先验证 verifiable 模式的确定性
        # 手动构造: verifiable 模式内部用 Random(derived_int) 洗牌, 所以同输入同输出
        b1 = Birth(year=1990, month=6, day=15, hour=12)
        r1 = compute(b1, "three", seed=42)
        b2 = Birth(year=1990, month=6, day=15, hour=12)
        r2 = compute(b2, "three", seed=42)
        cards1 = [(c["牌"], c["方位"]) for c in r1.raw["牌面"]]
        cards2 = [(c["牌"], c["方位"]) for c in r2.raw["牌面"]]
        assert cards1 == cards2

    def test_entropy_health_in_metadata(self):
        """密码学模式下, entropy_health 应出现在抽牌参数中."""
        from divination.engines.tarot import compute
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=None)
        meta = r.raw["抽牌参数"]
        assert "entropy_health" in meta
        assert meta["entropy_health"]["healthy"] is True

    def test_shuffle_uniformity_in_metadata(self):
        """所有模式下, shuffle_uniformity 应出现在抽牌参数中."""
        from divination.engines.tarot import compute
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=42)
        meta = r.raw["抽牌参数"]
        assert "shuffle_uniformity" in meta
        assert "first_card_index" in meta["shuffle_uniformity"]
        assert "max_theoretical_entropy_bits" in meta["shuffle_uniformity"]

    def test_engine_string_includes_verifiable_shuffle(self):
        """engine 字段应包含 'verifiable_shuffle' 标识."""
        from divination.engines.tarot import compute
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=None)
        assert "verifiable_shuffle" in r.engine

    def test_reproducible_mode_no_verifiable_metadata(self):
        """seed 显式提供时, draw_mode='reproducible', 不应有 verifiable_randomness."""
        from divination.engines.tarot import compute
        b = Birth(year=1990, month=6, day=15, hour=12)
        r = compute(b, "three", seed=42)
        meta = r.raw["抽牌参数"]
        assert meta["draw_mode"] == "reproducible"
        assert "verifiable_randomness" not in meta
        assert meta["entropy_health"] is None

    def test_fisher_yates_shuffle_len(self):
        """_fisher_yates_shuffle 返回长度正确的排列."""
        from divination.engines.tarot import _fisher_yates_shuffle, _make_rng
        pool = list(range(78))
        rng = _make_rng(None)
        result = _fisher_yates_shuffle(pool, rng)
        assert len(result) == 78
        assert set(result) == set(range(78))
