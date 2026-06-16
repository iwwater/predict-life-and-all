"""标准化器 — 将不同术法的 ChartResult 转为统一的 DivinationSignal 列表。

BE-006: 标准化文件
NOR-001: normalize_chart(method, chart) — 统一入口
NOR-002: fallback signal — 某术法无强信号时返回 general_reference
NOR-003: 统一 SIGNAL_KEYS — 所有 normalizer 使用统一 key
NOR-004~015: 每个 normalizer 至少输出 3 个 signal
Phase 1: 5 维职责分派 — 每个 signal 自动打 dimension + time_scope 标签
"""
from __future__ import annotations

from typing import Any, Optional

from divination.contracts import ChartResult

from .schema import DivinationSignal

# ── Phase 1: 方法→5 维 默认映射 (NOR-019) ──────────────────────────────────
# _make_signal() 收到未指定的 dimension/time_scope 时, 用此表兜底。
# 老的 12 法 normalizer 不需改一行, 4 新法 / hepan / chenggu 显式传入覆盖。
_METHOD_DIMENSION: dict[str, str] = {
    "bazi":      "long_term",  "bazi_v2":  "long_term",
    "ziwei":     "long_term",
    "qimen":     "one_question",
    "liuyao":    "one_question",
    "meihua":    "one_question",
    "fengshui":  "space",      "bazhai":   "space",      "xuankong": "space",
    "western":   "long_term",
    "vedic":     "long_term",
    "tarot":     "one_question",
    "numerology":"long_term",
    "liuren":    "one_question",
    "xiaoliuren":"one_question",
    "tieban":    "long_term",
    "lenormand": "one_question",
    "shicao":    "one_question",
    "hepan":     "relationship",
    "chenggu":   "long_term",
}

_METHOD_TIME_SCOPE: dict[str, str] = {
    "bazi":      "long_term",  "bazi_v2":  "long_term",
    "ziwei":     "long_term",
    "qimen":     "short_term",
    "liuyao":    "short_term",
    "meihua":    "short_term",
    "fengshui":  "space",      "bazhai":   "space",      "xuankong": "space",
    "western":   "long_term",
    "vedic":     "long_term",
    "tarot":     "short_term",
    "numerology":"long_term",
    "liuren":    "short_term",
    "xiaoliuren":"short_term",
    "tieban":    "long_term",
    "lenormand": "short_term",
    "shicao":    "short_term",
    "hepan":     "long_term",
    "chenggu":   "long_term",
}

# ═══════════════════════════════════════════════════════════════════════════════
# SIG-001~011: 统一信号键白名单
# ═══════════════════════════════════════════════════════════════════════════════

SIGNAL_KEYS: set[str] = {
    # ── 事业类 (SIG-001) ──
    "career_independence",
    "career_stability",
    "career_pressure",
    # ── 财富类 (SIG-002) ──
    "wealth_growth",
    "wealth_risk",
    "wealth_stability",
    # ── 感情类 (SIG-003) ──
    "relationship_attraction",
    "relationship_conflict",
    "marriage_stability",
    # ── 决策类 (SIG-004) ──
    "decision_support",
    "decision_delay",
    "decision_risk",
    # ── 时机类 (SIG-005) ──
    "timing_opportunity",
    "timing_obstacle",
    "timing_transition",
    # ── 健康反思类 (SIG-006) ──
    "health_pressure",
    "emotional_pressure",
    "rest_recovery",
    # ── 贵人/阻力类 (SIG-007) ──
    "noble_help",
    "obstacle_pressure",
    # ── 变动类 (SIG-008) ──
    "mobility_change",
    "relocation_signal",
    # ── 风水类 (SIG-009) ──
    "environment_support",
    "direction_benefit",
    "layout_risk",
    # ── 长期潜力 (SIG-010) ──
    "long_term_potential",
    "short_term_caution",
    # ── 通用 fallback (SIG-011) ──
    "general_reference",
}

# Domain → 常用 key 映射
DOMAIN_KEYS: dict[str, list[str]] = {
    "self_life":      ["long_term_potential", "noble_help", "general_reference"],
    "career":         ["career_independence", "career_stability", "career_pressure", "long_term_potential"],
    "wealth":         ["wealth_growth", "wealth_risk", "wealth_stability", "long_term_potential"],
    "relationship":   ["relationship_attraction", "relationship_conflict", "marriage_stability"],
    "decision":       ["decision_support", "decision_delay", "decision_risk"],
    "timing":         ["timing_opportunity", "timing_obstacle", "timing_transition"],
    "health":         ["health_pressure", "emotional_pressure", "rest_recovery"],
    "home_fengshui":  ["environment_support", "direction_benefit", "layout_risk"],
}


def _make_signal(
    method: str,
    domain: str,
    signal_key: str,
    polarity: str,
    strength: float,
    evidence: str = "",
    confidence: float = 0.5,
    dimension: Optional[str] = None,
    time_scope: Optional[str] = None,
) -> DivinationSignal:
    """创建归一化的 signal (strength 0-1, NOR-018)。

    Phase 1: dimension/time_scope 未指定时, 用 _METHOD_DIMENSION / _METHOD_TIME_SCOPE
    按方法名兜底, 保证所有 signal 都有 5 维标签。
    """
    # 确保 key 在白名单内
    if signal_key not in SIGNAL_KEYS:
        signal_key = "general_reference"

    if dimension is None:
        dimension = _METHOD_DIMENSION.get(method)
    if time_scope is None:
        time_scope = _METHOD_TIME_SCOPE.get(method)

    return DivinationSignal(
        method=method,
        domain=domain,
        signal_key=signal_key,
        polarity=polarity,
        strength=round(min(1.0, max(0.0, strength)), 3),
        evidence=evidence,
        confidence=round(min(1.0, max(0.0, confidence)), 3),
        dimension=dimension,
        time_scope=time_scope,
    )


def _fallback(method: str, domain: str = "self_life") -> DivinationSignal:
    """NOR-002: 当术法无法提取强信号时的 fallback。"""
    return _make_signal(
        method=method,
        domain=domain,
        signal_key="general_reference",
        polarity="neutral",
        strength=0.3,
        evidence=f"{method} 通用参考信号",
        confidence=0.3,
    )


# ── NOR-001: 统一入口 ───────────────────────────────────────────────────────

def normalize(method: str, chart: ChartResult) -> list[DivinationSignal]:
    """将单个术法的排盘结果标准化为统一信号列表。

    每个方法必须返回 ≥3 个 signal (NOR-004~015)。
    """
    raw = chart.raw
    normalized = chart.normalized

    signals: list[DivinationSignal] = []

    try:
        if method in ("bazi", "bazi_v2"):
            signals = _normalize_bazi(method, raw, normalized)
        elif method == "ziwei":
            signals = _normalize_ziwei(method, raw, normalized)
        elif method == "qimen":
            signals = _normalize_qimen(method, raw, normalized)
        elif method == "liuyao":
            signals = _normalize_liuyao(method, raw, normalized)
        elif method == "shicao":
            signals = _normalize_shicao(method, raw, normalized)
        elif method == "meihua":
            signals = _normalize_meihua(method, raw, normalized)
        elif method in ("fengshui", "bazhai"):
            signals = _normalize_bazhai(method, raw, normalized)
        elif method == "xuankong":
            signals = _normalize_xuankong(method, raw, normalized)
        elif method == "western":
            signals = _normalize_western(method, raw, normalized)
        elif method == "vedic":
            signals = _normalize_vedic(method, raw, normalized)
        elif method == "tarot":
            signals = _normalize_tarot(method, raw, normalized)
        elif method == "numerology":
            signals = _normalize_numerology(method, raw, normalized)
        elif method == "liuren":
            signals = _normalize_liuren(method, raw, normalized)
        elif method == "xiaoliuren":
            signals = _normalize_xiaoliuren(method, raw, normalized)
        elif method == "tieban":
            signals = _normalize_tieban(method, raw, normalized)
        elif method == "lenormand":
            signals = _normalize_lenormand(method, raw, normalized)
    except Exception:
        pass

    # 确保 ≥3 个 signal
    while len(signals) < 3:
        signals.append(_fallback(method))

    return signals


# ═══════════════════════════════════════════════════════════════════════════════
# 各术法标准化实现 (NOR-004~015)
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_bazi(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-004: 八字 — ≥3 signals (natal long_term + 流年/神煞 current_cycle)。"""
    s: list[DivinationSignal] = []
    day_master = raw.get("day_master", "")
    strength = raw.get("strength_score", 50) / 100  # normalize to 0-1
    elements = raw.get("elements", {})
    yong = raw.get("yong_shen", {})
    yong_name = yong.get("yong_shen", "") if isinstance(yong, dict) else str(yong)
    yong_score = raw.get("yong_shen_quality", {}).get("score", 50)
    if isinstance(yong_score, dict):
        yong_score = yong_score.get("score", 50)
    yong_score = yong_score / 100

    # 1. 事业 — 用神质量 (natal, long_term)
    if yong_name:
        pol = "positive" if yong_score > 0.45 else "negative" if yong_score < 0.3 else "neutral"
        s.append(_make_signal(method, "career", "career_independence", pol,
            strength=yong_score + 0.2,
            evidence=f"用神{yong_name}(质量{yong_score:.0%})",
            confidence=0.7,
            dimension="long_term", time_scope="long_term"))

    # 2. 长期潜力 — 日主强弱 (natal, long_term)
    if strength > 0.55:
        s.append(_make_signal(method, "self_life", "long_term_potential", "positive",
            strength=strength, evidence=f"日主{day_master}，身强", confidence=0.7,
            dimension="long_term", time_scope="long_term"))
    elif strength < 0.45:
        s.append(_make_signal(method, "self_life", "short_term_caution", "negative",
            strength=1 - strength, evidence=f"日主{day_master}，身弱", confidence=0.7,
            dimension="long_term", time_scope="long_term"))
    else:
        s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
            strength=0.5, evidence=f"日主{day_master}，中和", confidence=0.65,
            dimension="long_term", time_scope="long_term"))

    # 3. Phase 3: 神煞 (current_cycle, 流年/月/日) — 用 lunar-python 吉神/凶煞
    shensha = raw.get("shensha", {})
    if isinstance(shensha, dict):
        ji_list = shensha.get("吉神", []) or shensha.get("summary", {}).get("notable", [])
        xiong_list = shensha.get("凶煞", []) or []
        if isinstance(ji_list, str):
            ji_list = [ji_list] if ji_list else []
        if isinstance(xiong_list, str):
            xiong_list = [xiong_list] if xiong_list else []
        # W2: lunar-python 全量返回，不用关键词过滤
        # W3 fix: 合并日柱吉神 + 凶煞 + 天神 + 年月日时十神
        all_benefic = list(ji_list) + list(shensha.get("天神", []))
        all_malefic = list(xiong_list)
        # W3: 十神四柱扩大覆盖面（年/月/日/时柱十神）
        shi_shen_4 = shensha.get("十神四柱", {})
        if shi_shen_4:
            # 十神中的吉神类
            pos_shishen = {v for v in shi_shen_4.values()
                           if v in ("印", "比", "劫", "食", "财")}
            neg_shishen = {v for v in shi_shen_4.values()
                           if v in ("杀", "官", "枭", "刃")}
            all_benefic += list(pos_shishen)
            all_malefic += list(neg_shishen)
        if all_benefic:
            unique_ben = list(dict.fromkeys(all_benefic))  # dedup preserving order
            s.append(_make_signal(method, "self_life", "noble_help", "positive",
                strength=0.6, evidence=f"吉神: {unique_ben[:3]}", confidence=0.6,
                dimension="current_cycle", time_scope="current_cycle"))
        elif all_malefic:
            unique_mal = list(dict.fromkeys(all_malefic))
            s.append(_make_signal(method, "self_life", "obstacle_pressure", "negative",
                strength=0.55, evidence=f"凶煞: {unique_mal[:3]}", confidence=0.55,
                dimension="current_cycle", time_scope="current_cycle"))
        else:
            s.append(_make_signal(method, "self_life", "general_reference", "neutral",
                strength=0.4, evidence=f"神煞: 吉{len(all_benefic)}条, 凶{len(all_malefic)}条", confidence=0.4,
                dimension="current_cycle", time_scope="current_cycle"))

    # 4. Phase 3: 当前流年 (current_cycle)
    horoscope = raw.get("horoscope", {}) or {}
    yearly = horoscope.get("yearly", [])
    current_year = horoscope.get("current_year")
    if current_year and yearly:
        cur = next((y for y in yearly if y.get("year") == current_year), None)
        if cur:
            gz = cur.get("ganzhi", "")
            # 用 day_master 和流年天干的简单生克判断 (天干 5 合 / 克)
            dm_tg = day_master[:1] if day_master else ""
            liu_tg = gz[:1] if gz else ""
            # 简化: 同五行 = 比和 (中性), 生日 = positive, 克日 = negative
            sheng_map = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
            wx_map = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土",
                      "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
            dm_wx = wx_map.get(dm_tg, "")
            liu_wx = wx_map.get(liu_tg, "")
            if dm_wx and liu_wx:
                if sheng_map.get(liu_wx) == dm_wx:
                    pol = "positive"  # 流年生日
                elif sheng_map.get(dm_wx) == liu_wx:
                    pol = "negative"  # 日生流年(耗)
                elif liu_wx == dm_wx:
                    pol = "neutral"  # 比和
                else:
                    pol = "neutral"  # 克/反克 复杂, 留中
            else:
                pol = "neutral"
            s.append(_make_signal(method, "timing", "timing_transition", pol,
                strength=0.55, confidence=0.5,
                dimension="current_cycle", time_scope="current_cycle",
                evidence=f"{current_year}流年{cur.get('ganzhi','')}: 日主{dm_tg}, 流年{liu_tg}({liu_wx})"))

    # 5. 五行平衡 (natal, long_term)
    if elements:
        total = sum(elements.values())
        if total > 0:
            dominant = max(elements, key=elements.get)
            weak = min(elements, key=elements.get)
            s.append(_make_signal(method, "self_life", "general_reference", "neutral",
                strength=0.5, evidence=f"五行最旺{dominant}最弱{weak}", confidence=0.45,
                dimension="long_term", time_scope="long_term"))

    return s


def _normalize_ziwei(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-005: 紫微 — ≥3 signals (natal + 4 化 current_cycle)。"""
    s: list[DivinationSignal] = []
    palaces = raw.get("palaces", [])

    def _get_palace(name: str) -> dict:
        return next((p for p in palaces if p.get("name") == name), {})

    def _star_names(stars: list) -> list[str]:
        return [st.get("name", st) if isinstance(st, dict) else st for st in stars]

    # 1. 事业 — 官禄宫 (natal, long_term)
    guanlu = _get_palace("官禄宫")
    gl_names = _star_names(guanlu.get("major_stars", []))
    career_good = any(n in {"紫微", "天府", "天相", "太阳", "武曲"} for n in gl_names)
    if career_good:
        s.append(_make_signal(method, "career", "career_stability", "positive",
            strength=0.65, evidence=f"官禄宫吉星: {gl_names}", confidence=0.6,
            dimension="long_term", time_scope="long_term"))
    else:
        s.append(_make_signal(method, "career", "career_pressure", "neutral",
            strength=0.45, evidence=f"官禄宫: {gl_names}", confidence=0.5,
            dimension="long_term", time_scope="long_term"))

    # 2. 感情 — 夫妻宫 (natal, long_term)
    fuqi = _get_palace("夫妻宫")
    fq_names = _star_names(fuqi.get("major_stars", []))
    rel_good = any(n in {"天同", "太阴", "廉贞", "天相"} for n in fq_names)
    rel_hard = any(n in {"七杀", "破军", "贪狼", "巨门"} for n in fq_names)
    if rel_good:
        s.append(_make_signal(method, "relationship", "marriage_stability", "positive",
            strength=0.65, evidence=f"夫妻宫吉星: {fq_names}", confidence=0.6,
            dimension="long_term", time_scope="long_term"))
    elif rel_hard:
        s.append(_make_signal(method, "relationship", "relationship_conflict", "negative",
            strength=0.55, evidence=f"夫妻宫有挑战: {fq_names}", confidence=0.5,
            dimension="long_term", time_scope="long_term"))
    else:
        s.append(_make_signal(method, "relationship", "relationship_attraction", "neutral",
            strength=0.5, evidence=f"夫妻宫: {fq_names}", confidence=0.45,
            dimension="long_term", time_scope="long_term"))

    # 3. 命宫 — 长期潜力 (natal, long_term)
    ming = _get_palace("命宫")
    ming_names = _star_names(ming.get("major_stars", []))
    strong_stars = {"紫微", "天府", "太阳", "武曲", "七杀", "破军", "贪狼"}
    is_strong = any(n in strong_stars for n in ming_names)
    if is_strong:
        s.append(_make_signal(method, "self_life", "long_term_potential", "positive",
            strength=0.7, evidence=f"命宫强势: {ming_names}", confidence=0.65,
            dimension="long_term", time_scope="long_term"))
    else:
        s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
            strength=0.5, evidence=f"命宫: {ming_names}", confidence=0.55,
            dimension="long_term", time_scope="long_term"))

    # 4. Phase 3: 4 化 → current_cycle signal
    # 取 decadal (大限) 和 yearly (流年) 两层 4 化, 各出 1-2 个 current_cycle signal
    four_trans = raw.get("four_transformations", {})
    decadal_muts = four_trans.get("decadal", []) or []
    yearly_muts = four_trans.get("yearly", []) or []

    # 化禄/化权/化科 → positive, 化忌 → negative
    POSITIVE_KEYS = {"lu", "huaLu", "huaQuan", "huaKe", "luminance", "M", "F"}  # 各种 py_iztro 命名
    NEGATIVE_KEYS = {"ji", "huaJi", "obstacle", "B"}

    def _classify_mutagen(mut: str) -> str:
        if not mut:
            return "neutral"  # 空字符串不计（py_iztro 0.3+ 旧 API 兼容）
        m = mut.lower()
        if "ji" in m or "obstacle" in m:
            return "negative"
        return "positive"

    if decadal_muts:
        pol_count = {"positive": 0, "negative": 0, "neutral": 0}
        for mut in decadal_muts:
            pol_count[_classify_mutagen(mut)] += 1
        overall = "positive" if pol_count["positive"] > pol_count["negative"] else "negative" if pol_count["negative"] > pol_count["positive"] else "neutral"
        s.append(_make_signal(
            method, "timing", "timing_opportunity" if overall == "positive" else "timing_obstacle",
            overall, strength=0.6, confidence=0.55,
            dimension="current_cycle", time_scope="current_cycle",
            evidence=f"大限4化: {decadal_muts} ({pol_count['positive']}吉{pol_count['negative']}忌)",
        ))

    if yearly_muts:
        pol_count = {"positive": 0, "negative": 0, "neutral": 0}
        for mut in yearly_muts:
            pol_count[_classify_mutagen(mut)] += 1
        overall = "positive" if pol_count["positive"] > pol_count["negative"] else "negative" if pol_count["negative"] > pol_count["positive"] else "neutral"
        s.append(_make_signal(
            method, "timing", "timing_transition",
            overall, strength=0.55, confidence=0.5,
            dimension="current_cycle", time_scope="current_cycle",
            evidence=f"流年4化: {yearly_muts} ({pol_count['positive']}吉{pol_count['negative']}忌)",
        ))

    # monthly / daily / hourly 任一有有效 4 化 → 出短期 current_cycle signal
    short_scopes = [(s_name, [m for m in (four_trans.get(s_name, []) or []) if m]) for s_name in ("monthly", "daily", "hourly")]
    has_short = any(muts for _, muts in short_scopes)
    if has_short:
        all_muts = [m for _, muts in short_scopes for m in muts]
        pol_count = {"positive": 0, "negative": 0, "neutral": 0}
        for mut in all_muts:
            pol_count[_classify_mutagen(mut)] += 1
        overall = "positive" if pol_count["positive"] > pol_count["negative"] else "negative" if pol_count["negative"] > pol_count["positive"] else "neutral"
        s.append(_make_signal(
            method, "decision", "decision_support" if overall == "positive" else "decision_risk",
            overall, strength=0.5, confidence=0.45,
            dimension="current_cycle", time_scope="current_cycle",
            evidence=f"流月/日/时4化: {all_muts[:4]}",
        ))

    return s


def _normalize_qimen(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-006: 奇门 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    duan = raw.get("断", raw)
    patterns = duan.get("格局", [])
    door_status = duan.get("门状态", {})

    # 1. 决策支持
    good_pat = sum(1 for p in patterns if "吉" in str(p))
    bad_pat = sum(1 for p in patterns if "凶" in str(p))
    if good_pat > bad_pat:
        s.append(_make_signal(method, "decision", "decision_support", "positive",
            strength=0.6 + min(0.3, good_pat * 0.1),
            evidence=f"吉格{good_pat}凶格{bad_pat}", confidence=0.65))
    elif bad_pat > good_pat:
        s.append(_make_signal(method, "decision", "decision_risk", "negative",
            strength=0.5 + min(0.3, bad_pat * 0.1),
            evidence=f"凶格{bad_pat}多于吉格{good_pat}", confidence=0.6))
    else:
        s.append(_make_signal(method, "decision", "decision_delay", "neutral",
            strength=0.45, evidence=f"格局吉凶各半", confidence=0.5))

    # 2. 时机
    if door_status:
        s.append(_make_signal(method, "timing", "timing_opportunity", "neutral",
            strength=0.5, evidence=f"门状态: {door_status}", confidence=0.5))

    # 3. 贵人
    if "休" in str(door_status) or "生" in str(door_status):
        s.append(_make_signal(method, "self_life", "noble_help", "positive",
            strength=0.55, evidence=f"吉门相助", confidence=0.5))
    else:
        s.append(_make_signal(method, "self_life", "general_reference", "neutral",
            strength=0.35, evidence="奇门遁甲综合参考", confidence=0.4))

    return s


def _normalize_shicao(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-007b: 蓍草筮法（揲四归奇）— ≥3 signals。

    与六爻(_normalize_liuyao)共用用神体系，但概率分布不同（蓍草法概率：
    老阳 3/16, 少阳 5/16, 少阴 7/16, 老阴 1/16），在证据中体现。
    """
    s: list[DivinationSignal] = []
    duan = raw.get("断", raw)
    verdict = str(duan.get("断语", duan.get("提示", "")))
    yarrow_lines = raw.get("yarrow_lines", [])
    moving = raw.get("动爻", [])
    rule_version = raw.get("rule_version", "")

    # 1. 决策支持 — 同用神体系
    if any(w in verdict for w in ("吉", "利", "成", "可", "好")):
        s.append(_make_signal(method, "decision", "decision_support", "positive",
            strength=0.65, evidence=f"蓍草{rule_version}: {verdict}",
            confidence=0.62))
    elif any(w in verdict for w in ("凶", "不利", "不成", "慎", "忌")):
        s.append(_make_signal(method, "decision", "decision_risk", "negative",
            strength=0.6, evidence=f"蓍草{rule_version}: {verdict}",
            confidence=0.62))
    else:
        s.append(_make_signal(method, "decision", "decision_delay", "neutral",
            strength=0.5, evidence=f"蓍草（揲四归奇）{rule_version}: 待定",
            confidence=0.5))

    # 2. 时机
    if moving:
        line_vals = [r["line_value"] for r in yarrow_lines]
        # 老阴(6)最少(1/16)为最深变，老阳(9)次之(3/16)
        laoyin_count = sum(1 for v in line_vals if v == 6)
        laoyang_count = sum(1 for v in line_vals if v == 9)
        evidence = (f"蓍草动爻{len(moving)}个"
                    f"（老阴{laoyin_count}老阳{laoyang_count}）")
        s.append(_make_signal(method, "timing", "timing_transition", "neutral",
            strength=0.5, evidence=evidence, confidence=0.45))
    else:
        s.append(_make_signal(method, "timing", "timing_transition", "neutral",
            strength=0.45, evidence="蓍草六爻安静（无动爻）", confidence=0.4))

    # 3. 变动
    if moving:
        s.append(_make_signal(method, "self_life", "mobility_change", "positive",
            strength=0.55, evidence=f"蓍草法动爻：第{','.join(str(m) for m in moving)}爻",
            confidence=0.5))
    else:
        s.append(_make_signal(method, "self_life", "general_reference", "neutral",
            strength=0.35, evidence="蓍草（揲四归奇）综合参考", confidence=0.4))

    return s


def _normalize_liuyao(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-007: 六爻 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    duan = raw.get("断", raw)
    gua_name = raw.get("本卦", {}).get("name", "")
    verdict = str(duan.get("断语", duan.get("提示", "")))

    # 1. 决策支持
    if any(w in verdict for w in ("吉", "利", "成", "可", "好")):
        s.append(_make_signal(method, "decision", "decision_support", "positive",
            strength=0.65, evidence=f"本卦{gua_name}: {verdict}", confidence=0.6))
    elif any(w in verdict for w in ("凶", "不利", "不成", "慎", "忌")):
        s.append(_make_signal(method, "decision", "decision_risk", "negative",
            strength=0.6, evidence=f"本卦{gua_name}: {verdict}", confidence=0.6))
    else:
        s.append(_make_signal(method, "decision", "decision_delay", "neutral",
            strength=0.5, evidence=f"本卦{gua_name}: 待定", confidence=0.5))

    # 2. 时机
    s.append(_make_signal(method, "timing", "timing_transition", "neutral",
        strength=0.45, evidence=f"六爻卦象参考", confidence=0.4))

    # 3. 变动
    if raw.get("动爻") or raw.get("变卦"):
        s.append(_make_signal(method, "self_life", "mobility_change", "neutral",
            strength=0.5, evidence="卦有动爻，在变", confidence=0.45))
    else:
        s.append(_make_signal(method, "self_life", "general_reference", "neutral",
            strength=0.35, evidence="六爻综合参考", confidence=0.4))

    return s


def _normalize_meihua(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-008: 梅花 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    duan = raw.get("断", raw)
    body = raw.get("体卦", "")
    usage = raw.get("用卦", "")
    verdict = str(duan.get("总断", duan.get("断语", "")))

    # 1. 决策
    if "用生体" in verdict or "体克用" in verdict:
        s.append(_make_signal(method, "decision", "decision_support", "positive",
            strength=0.6, evidence=f"体{body}用{usage}: {verdict}", confidence=0.55))
    elif "用克体" in verdict or "体生用" in verdict:
        s.append(_make_signal(method, "decision", "decision_risk", "negative",
            strength=0.55, evidence=f"体{body}用{usage}: {verdict}", confidence=0.55))
    else:
        s.append(_make_signal(method, "decision", "decision_delay", "neutral",
            strength=0.45, evidence=f"体{body}用{usage}", confidence=0.5))

    # 2. 时机
    s.append(_make_signal(method, "timing", "timing_transition", "neutral",
        strength=0.4, evidence="梅花易数卦象", confidence=0.4))

    # 3. 变动
    s.append(_make_signal(method, "self_life", "mobility_change", "neutral",
        strength=0.45, evidence=f"主卦{raw.get('主卦',{}).get('name','')} 变卦{raw.get('变卦',{}).get('name','')}", confidence=0.4))

    return s


def _normalize_bazhai(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-009/010: 风水/八宅 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    gua = raw.get("命卦", "")
    ji = raw.get("吉方", [])
    xiong = raw.get("凶方", [])

    # 1. 环境支持
    s.append(_make_signal(method, "home_fengshui", "environment_support", "positive" if ji else "neutral",
        strength=0.5 + min(0.3, len(ji) * 0.05),
        evidence=f"命卦{gua}吉方{ji}", confidence=0.55))

    # 2. 风水风险
    if xiong:
        s.append(_make_signal(method, "home_fengshui", "layout_risk", "negative",
            strength=0.4 + min(0.3, len(xiong) * 0.05),
            evidence=f"凶方{xiong}", confidence=0.5))
    else:
        s.append(_make_signal(method, "home_fengshui", "layout_risk", "neutral",
            strength=0.3, evidence="无明显凶方", confidence=0.4))

    # 3. 方向
    s.append(_make_signal(method, "home_fengshui", "direction_benefit", "neutral",
        strength=0.45, evidence=f"命卦{gua}风水参考", confidence=0.45))

    return s


def _normalize_xuankong(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-011: 玄空 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    yun = raw.get("运", "")
    geju = raw.get("格局", "")

    # 1. 环境
    s.append(_make_signal(method, "home_fengshui", "environment_support",
        "positive" if "旺" in str(geju) else "neutral",
        strength=0.55, evidence=f"{yun}运格局{geju}", confidence=0.5))

    # 2. 风水风险
    s.append(_make_signal(method, "home_fengshui", "layout_risk",
        "negative" if "凶" in str(geju) or "煞" in str(geju) else "neutral",
        strength=0.4, evidence=f"玄空飞星{geju}", confidence=0.45))

    # 3. 方向
    s.append(_make_signal(method, "home_fengshui", "direction_benefit", "neutral",
        strength=0.45, evidence=f"{yun}运坐{raw.get('坐','')}向{raw.get('向','')}", confidence=0.45))

    return s


def _normalize_western(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-012: 西方占星 — ≥3 signals (natal long_term + 行运 current_cycle)。"""
    s: list[DivinationSignal] = []
    planets = raw.get("planets", {})
    aspects = raw.get("aspects", [])
    sun = planets.get("太阳", {})
    moon = planets.get("月亮", {})

    # 1. 长期潜力 — 太阳星座 (natal, long_term)
    sun_sign = sun.get("sign", "") if isinstance(sun, dict) else ""
    s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
        strength=0.6, evidence=f"太阳{sun_sign}", confidence=0.65,
        dimension="long_term", time_scope="long_term"))

    # 2. 感情吸引 — 月亮星座 (natal, long_term)
    moon_sign = moon.get("sign", "") if isinstance(moon, dict) else ""
    s.append(_make_signal(method, "relationship", "relationship_attraction", "neutral",
        strength=0.55, evidence=f"月亮{moon_sign}", confidence=0.55,
        dimension="long_term", time_scope="long_term"))

    # 3. 贵人/阻力 — 本命相位 (natal, long_term)
    hard = sum(1 for a in aspects if isinstance(a, dict) and a.get("aspect") in ("冲", "刑"))
    soft = sum(1 for a in aspects if isinstance(a, dict) and a.get("aspect") in ("合", "拱", "六合"))
    if soft > hard:
        s.append(_make_signal(method, "self_life", "noble_help", "positive",
            strength=0.55, evidence=f"本命吉相位{soft}凶相位{hard}", confidence=0.5,
            dimension="long_term", time_scope="long_term"))
    else:
        s.append(_make_signal(method, "self_life", "obstacle_pressure", "neutral",
            strength=0.45, evidence=f"本命相位吉{soft}凶{hard}", confidence=0.45,
            dimension="long_term", time_scope="long_term"))

    # 4. Phase 3: 行运 transits (current_cycle)
    transits = raw.get("transits", []) or []
    if transits:
        hard_n = sum(1 for t in transits if isinstance(t, dict) and t.get("is_hard"))
        soft_n = len(transits) - hard_n
        if hard_n > soft_n:
            pol = "negative"
            sk = "timing_obstacle"
        elif soft_n > hard_n:
            pol = "positive"
            sk = "timing_opportunity"
        else:
            pol = "neutral"
            sk = "timing_transition"
        # 挑一个 orb 最小 (最紧) 的相位作为 evidence
        tightest = min(transits, key=lambda t: t.get("orb", 99) if isinstance(t, dict) else 99)
        s.append(_make_signal(method, "timing", sk, pol,
            strength=0.55, confidence=0.5,
            dimension="current_cycle", time_scope="current_cycle",
            evidence=f"行运 {len(transits)} 相位 (硬{hard_n}/柔{soft_n}), 最紧: {tightest.get('natal_planet','')}{tightest.get('aspect','')}{tightest.get('transit_planet','')} orb={tightest.get('orb','')}"))

    # Phase H: 次限推运 (secondary progressions) → current_cycle signal
    progressions = raw.get("progressions", []) or []
    prog_date = raw.get("progressed_date", "")
    if progressions:
        hard_n = sum(1 for p in progressions if isinstance(p, dict) and p.get("is_hard"))
        soft_n = len(progressions) - hard_n
        if soft_n > hard_n:
            pol, sk = "positive", "timing_opportunity"
        elif hard_n > soft_n:
            pol, sk = "negative", "timing_obstacle"
        else:
            pol, sk = "neutral", "timing_transition"
        tightest = min(progressions, key=lambda p: abs(p.get("shift_deg", 999) - ({"合": 0, "冲": 180, "刑": 90, "拱": 120, "六合": 60}.get(p.get("aspect", ""), 0)))) if progressions else {}
        s.append(_make_signal(method, "timing", f"prog_{sk}", pol,
            strength=0.52, confidence=0.48,
            dimension="current_cycle", time_scope="current_cycle",
            evidence=f"次限推运 {len(progressions)} 相位 (次限期{prog_date})，{tightest.get('planet','')}{tightest.get('aspect','')}"))

    return s


def _normalize_vedic(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-013: 吠陀占星 — ≥3 signals + current_cycle (W6: Vimshottari Dasha)。"""
    s: list[DivinationSignal] = []
    planets = raw.get("planets", {})

    planet_info = []
    for name, data in planets.items():
        if isinstance(data, dict):
            planet_info.append(f"{name}:{data.get('宫Rashi','')}")

    # 1. 长期潜力
    s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
        strength=0.55, evidence=f"行星宫位: {'; '.join(planet_info[:3])}", confidence=0.55))

    # 2. 感情
    s.append(_make_signal(method, "relationship", "marriage_stability", "neutral",
        strength=0.45, evidence="吠陀星辰婚配参考", confidence=0.45))

    # 3. 时机
    s.append(_make_signal(method, "timing", "timing_transition", "neutral",
        strength=0.4, evidence="吠陀行运参考", confidence=0.4))

    # W6: 当前大运信号 (current_cycle) — 读取 Vimshottari Dasha
    dasha_data = raw.get("Vimshottari大运", {})
    curr_dasha = dasha_data.get("当前大运", {})
    if curr_dasha:
        dasha_lord = curr_dasha.get("主星", "")
        dasha_start = curr_dasha.get("起", "")
        dasha_end = curr_dasha.get("止", "")
        # 获取大运主星的庙旺落陷
        lord_dignity = planets.get(dasha_lord, {}).get("庙旺落陷", "") if dasha_lord in planets else ""
        # 庙旺→强吉, 入庙→吉, 落陷→凶, 平→中性
        if "庙旺" in lord_dignity or "exalt" in lord_dignity.lower():
            pol, strength = "positive", 0.7
        elif "入庙" in lord_dignity or "own" in lord_dignity.lower():
            pol, strength = "positive", 0.65
        elif "落陷" in lord_dignity or "fall" in lord_dignity.lower():
            pol, strength = "negative", 0.65
        else:
            pol, strength = "neutral", 0.5
        s.append(_make_signal(method, "self_life", "current_cycle_dasha", pol,
            strength=strength,
            evidence=f"当前大运: {dasha_lord} ({dasha_start}~{dasha_end}, {lord_dignity})",
            confidence=0.7,
            dimension="current_cycle", time_scope="current_cycle"))

    return s


def _normalize_tarot(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-014: 塔罗 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    cards = raw.get("牌面", [])

    pos_count = 0
    neg_count = 0
    for c in cards:
        if isinstance(c, dict):
            kw = str(c.get("关键词", ""))
            if any(w in kw for w in ("吉", "正", "成功", "爱", "光明", "和谐", "力量")):
                pos_count += 1
            elif any(w in kw for w in ("凶", "逆", "失败", "冲突", "黑暗", "欺骗")):
                neg_count += 1

    # 1. 决策
    if pos_count > neg_count:
        s.append(_make_signal(method, "decision", "decision_support", "positive",
            strength=0.55 + min(0.3, pos_count * 0.1),
            evidence=f"正位{pos_count}逆位{neg_count}", confidence=0.5))
    elif neg_count > pos_count:
        s.append(_make_signal(method, "decision", "decision_risk", "negative",
            strength=0.5 + min(0.3, neg_count * 0.1),
            evidence=f"逆位{neg_count}正位{pos_count}", confidence=0.5))
    else:
        s.append(_make_signal(method, "decision", "decision_delay", "neutral",
            strength=0.45, evidence="牌面正逆均衡", confidence=0.45))

    # 2. 感情
    s.append(_make_signal(method, "relationship", "relationship_attraction", "neutral",
        strength=0.45, evidence="塔罗感情指引", confidence=0.4))

    # 3. 短期提示
    s.append(_make_signal(method, "self_life", "short_term_caution", "neutral",
        strength=0.4, evidence="塔罗当下指引", confidence=0.4))

    return s


def _normalize_numerology(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-015: 数字命理 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    life_path = raw.get("生命灵数", raw.get("life_path", ""))

    # 1. 长期潜力
    s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
        strength=0.5, evidence=f"生命灵数{life_path}", confidence=0.45))

    # 2. 事业独立性
    s.append(_make_signal(method, "career", "career_independence", "neutral",
        strength=0.4, evidence=f"灵数{life_path}事业倾向", confidence=0.4))

    # 3. 感情
    s.append(_make_signal(method, "relationship", "relationship_attraction", "neutral",
        strength=0.4, evidence=f"灵数{life_path}感情倾向", confidence=0.35))

    return s


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 0 新增术法标准化 (NOR-016~019)
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_liuren(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-016: 大六壬 — 三传 + 课式 → 短期一事一断。"""
    s: list[DivinationSignal] = []
    three = raw.get("three_transmissions", {})
    chu = three.get("chu_chuan", "")
    pattern = raw.get("pattern", {})
    pattern_name = pattern.get("name", "未明") if isinstance(pattern, dict) else "未明"
    pattern_type = pattern.get("type", "neutral") if isinstance(pattern, dict) else "neutral"

    # 1. 课式结论
    polarity_map = {"auspicious": "positive", "inauspicious": "negative", "neutral": "neutral"}
    pol = polarity_map.get(pattern_type, "neutral")
    s.append(_make_signal(
        method, "decision", "decision_support", pol,
        strength=0.6, confidence=0.55,
        dimension="one_question", time_scope="short_term",
        evidence=f"课式: {pattern_name}, 初传{three.get('chu_chuan','?')}→{three.get('zhong_chuan','?')}→{three.get('mo_chuan','?')}",
    ))

    # 2. 时机信号
    timing_pol = pol if pol != "neutral" else "mixed"
    s.append(_make_signal(
        method, "timing", "timing_transition", timing_pol,
        strength=0.5, confidence=0.45,
        dimension="one_question", time_scope="short_term",
        evidence=f"大六壬 {pattern_name} 课, 三传变化提示",
    ))

    # 3. 通用参考
    s.append(_make_signal(
        method, "self_life", "general_reference", "neutral",
        strength=0.4, confidence=0.4,
        dimension="one_question", time_scope="short_term",
        evidence=f"大六壬 {pattern_name} ({raw.get('day_ganzhi', '?')})",
    ))

    return s


def _normalize_xiaoliuren(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-017: 小六壬 — 六宫掌诀 → 短期即时决疑。"""
    s: list[DivinationSignal] = []
    palace_name = raw.get("palace", "未明")
    tone = raw.get("tone", "neutral")

    polarity_map = {
        "auspicious": "positive",
        "minor luck": "positive",
        "delayed": "mixed",
        "conflict": "negative",
        "void": "mixed",
    }
    pol = polarity_map.get(tone, "neutral")

    # 1. 决策
    s.append(_make_signal(
        method, "decision", "decision_support" if pol == "positive" else "decision_delay" if pol in ("mixed", "negative") else "decision_risk",
        pol, strength=0.6, confidence=0.55,
        dimension="one_question", time_scope="short_term",
        evidence=f"小六壬落 {palace_name} 宫 ({tone})",
    ))

    # 2. 时机
    s.append(_make_signal(
        method, "timing", "timing_opportunity" if pol == "positive" else "timing_obstacle",
        pol, strength=0.5, confidence=0.45,
        dimension="one_question", time_scope="short_term",
        evidence=f"即时信号: {palace_name}",
    ))

    # 3. 通用
    s.append(_make_signal(
        method, "self_life", "general_reference", "neutral",
        strength=0.4, confidence=0.4,
        dimension="one_question", time_scope="short_term",
        evidence=f"小六壬: {raw.get('meaning', '')}",
    ))

    return s


def _normalize_tieban(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-018: 铁板神数 — 条文集数 → 长期命格参考。"""
    s: list[DivinationSignal] = []
    verse = raw.get("verse_result", {})
    matched = verse.get("matched_verses", []) if isinstance(verse, dict) else []
    total = verse.get("total_matched", 0) if isinstance(verse, dict) else 0

    # 1. 长期格局 (用条文分布推断)
    if total == 0:
        pol, strength = "neutral", 0.3
    elif total < 5:
        pol, strength = "neutral", 0.4
    else:
        pol, strength = "mixed", 0.5

    s.append(_make_signal(
        method, "self_life", "long_term_potential", pol,
        strength=strength, confidence=0.45,
        dimension="long_term", time_scope="long_term",
        evidence=f"铁板神数 集数{raw.get('verse_set_number', '?')}, 匹配{total}条条文",
    ))

    # 2. 关系 (条文里夫妻/父母类)
    relationship_verses = [v for v in matched if v.get("category") in ("夫妻", "父母")]
    if relationship_verses:
        s.append(_make_signal(
            method, "relationship", "marriage_stability", "mixed",
            strength=0.5, confidence=0.4,
            dimension="long_term", time_scope="long_term",
            evidence=f"铁板条文涵盖 {len(relationship_verses)} 条婚恋类",
        ))
    else:
        s.append(_make_signal(
            method, "relationship", "general_reference", "neutral",
            strength=0.4, confidence=0.35,
            dimension="long_term", time_scope="long_term",
            evidence="铁板神数未匹配婚恋类条文",
        ))

    # 3. 财运
    wealth_verses = [v for v in matched if v.get("category") == "财运"]
    pol_w = "positive" if len(wealth_verses) >= 2 else "neutral" if len(wealth_verses) == 1 else "neutral"
    s.append(_make_signal(
        method, "wealth", "wealth_growth" if pol_w == "positive" else "general_reference",
        pol_w, strength=0.45, confidence=0.4,
        dimension="long_term", time_scope="long_term",
        evidence=f"铁板神数 财运类条文 {len(wealth_verses)} 条",
    ))

    return s


def _normalize_lenormand(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-019: 雷诺曼 — 36 牌 + 牌阵组合 → 短期具体事。"""
    s: list[DivinationSignal] = []
    cards = raw.get("cards", [])
    analysis = raw.get("analysis", {})
    tone = analysis.get("tone", "neutral") if isinstance(analysis, dict) else "neutral"
    pos_n = analysis.get("positive_count", 0) if isinstance(analysis, dict) else 0
    neg_n = analysis.get("negative_count", 0) if isinstance(analysis, dict) else 0

    polarity_map = {"positive": "positive", "negative": "negative", "neutral": "neutral"}
    pol = polarity_map.get(tone, "neutral")

    # 1. 决策 (雷诺曼核心 = 具体事)
    s.append(_make_signal(
        method, "decision", "decision_support" if pol == "positive" else "decision_delay",
        pol, strength=0.6, confidence=0.55,
        dimension="one_question", time_scope="short_term",
        evidence=f"雷诺曼 {raw.get('spread_name', '?')}: {pos_n}正{neg_n}负",
    ))

    # 2. 时机 (看牌阵 timing)
    top_card = cards[0] if cards else {}
    timing_hint = top_card.get("timing", "未知") if isinstance(top_card, dict) else "未知"
    s.append(_make_signal(
        method, "timing", "timing_transition", pol,
        strength=0.5, confidence=0.45,
        dimension="one_question", time_scope="short_term",
        evidence=f"核心牌 {top_card.get('name_zh', '?')} 节奏: {timing_hint}",
    ))

    # 3. 关系 (如果牌里出现 Heart/Ring/Bouquet 等)
    rel_cards = [c for c in cards if isinstance(c, dict) and c.get("name") in ("心", "戒指", "花束", "百合", "鸟")]
    if rel_cards:
        s.append(_make_signal(
            method, "relationship", "relationship_attraction" if pol == "positive" else "relationship_conflict",
            pol, strength=0.5, confidence=0.45,
            dimension="one_question", time_scope="short_term",
            evidence=f"雷诺曼出现关系类牌: {', '.join(c.get('name_zh','?') for c in rel_cards)}",
        ))
    else:
        s.append(_make_signal(
            method, "relationship", "general_reference", "neutral",
            strength=0.35, confidence=0.3,
            dimension="one_question", time_scope="short_term",
            evidence="雷诺曼未抽到关系类牌",
        ))

    return s


# ── 批量标准化 ───────────────────────────────────────────────────────────────

def normalize_all(charts: dict[str, Any]) -> list[DivinationSignal]:
    """批量标准化所有术法的排盘结果。"""
    all_signals: list[DivinationSignal] = []
    for method, chart in charts.items():
        try:
            signals = normalize(method, chart)
            all_signals.extend(signals)
        except Exception:
            all_signals.append(_fallback(method))
    return all_signals
