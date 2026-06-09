"""标准化器 — 将不同术法的 ChartResult 转为统一的 DivinationSignal 列表。

BE-006: 标准化文件
NOR-001: normalize_chart(method, chart) — 统一入口
NOR-002: fallback signal — 某术法无强信号时返回 general_reference
NOR-003: 统一 SIGNAL_KEYS — 所有 normalizer 使用统一 key
NOR-004~015: 每个 normalizer 至少输出 3 个 signal
"""
from __future__ import annotations

from typing import Any

from divination.contracts import ChartResult

from .schema import DivinationSignal

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
) -> DivinationSignal:
    """创建归一化的 signal (strength 0-1)。"""
    # 确保 key 在白名单内
    if signal_key not in SIGNAL_KEYS:
        signal_key = "general_reference"

    return DivinationSignal(
        method=method,
        domain=domain,
        signal_key=signal_key,
        polarity=polarity,
        strength=round(min(1.0, max(0.0, strength)), 3),
        evidence=evidence,
        confidence=round(min(1.0, max(0.0, confidence)), 3),
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
    """NOR-004: 八字 — ≥3 signals。"""
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

    # 1. 事业 — 用神质量
    if yong_name:
        pol = "positive" if yong_score > 0.45 else "negative" if yong_score < 0.3 else "neutral"
        s.append(_make_signal(method, "career", "career_independence", pol,
            strength=yong_score + 0.2,
            evidence=f"用神{yong_name}(质量{yong_score:.0%})",
            confidence=0.7))

    # 2. 长期潜力 — 日主强弱
    if strength > 0.55:
        s.append(_make_signal(method, "self_life", "long_term_potential", "positive",
            strength=strength, evidence=f"日主{day_master}，身强", confidence=0.7))
    elif strength < 0.45:
        s.append(_make_signal(method, "self_life", "short_term_caution", "negative",
            strength=1 - strength, evidence=f"日主{day_master}，身弱", confidence=0.7))
    else:
        s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
            strength=0.5, evidence=f"日主{day_master}，中和", confidence=0.65))

    # 3. 贵人/阻力
    shensha = raw.get("shensha", {})
    notable = shensha.get("summary", {}).get("notable", []) if isinstance(shensha, dict) else []
    benefic = any("贵" in str(n) or "禄" in str(n) or "福" in str(n) for n in notable)
    malefic = any("煞" in str(n) or "劫" in str(n) or "灾" in str(n) for n in notable)
    if benefic:
        s.append(_make_signal(method, "self_life", "noble_help", "positive",
            strength=0.6, evidence=f"神煞: {[n for n in notable if '贵' in str(n) or '禄' in str(n)][:2]}", confidence=0.55))
    elif malefic:
        s.append(_make_signal(method, "self_life", "obstacle_pressure", "negative",
            strength=0.55, evidence=f"神煞提示: {[n for n in notable if '煞' in str(n) or '劫' in str(n)][:2]}", confidence=0.5))
    else:
        s.append(_make_signal(method, "self_life", "general_reference", "neutral",
            strength=0.4, evidence=f"神煞: {notable[:2] if notable else '无显著神煞'}", confidence=0.4))

    # 4. 五行平衡
    if elements:
        total = sum(elements.values())
        if total > 0:
            dominant = max(elements, key=elements.get)
            weak = min(elements, key=elements.get)
            s.append(_make_signal(method, "self_life", "general_reference", "neutral",
                strength=0.5, evidence=f"五行最旺{dominant}最弱{weak}", confidence=0.45))

    return s


def _normalize_ziwei(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-005: 紫微 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    palaces = raw.get("palaces", [])

    def _get_palace(name: str) -> dict:
        return next((p for p in palaces if p.get("name") == name), {})

    def _star_names(stars: list) -> list[str]:
        return [st.get("name", st) if isinstance(st, dict) else st for st in stars]

    # 1. 事业 — 官禄宫
    guanlu = _get_palace("官禄宫")
    gl_names = _star_names(guanlu.get("major_stars", []))
    career_good = any(n in {"紫微", "天府", "天相", "太阳", "武曲"} for n in gl_names)
    if career_good:
        s.append(_make_signal(method, "career", "career_stability", "positive",
            strength=0.65, evidence=f"官禄宫吉星: {gl_names}", confidence=0.6))
    else:
        s.append(_make_signal(method, "career", "career_pressure", "neutral",
            strength=0.45, evidence=f"官禄宫: {gl_names}", confidence=0.5))

    # 2. 感情 — 夫妻宫
    fuqi = _get_palace("夫妻宫")
    fq_names = _star_names(fuqi.get("major_stars", []))
    rel_good = any(n in {"天同", "太阴", "廉贞", "天相"} for n in fq_names)
    rel_hard = any(n in {"七杀", "破军", "贪狼", "巨门"} for n in fq_names)
    if rel_good:
        s.append(_make_signal(method, "relationship", "marriage_stability", "positive",
            strength=0.65, evidence=f"夫妻宫吉星: {fq_names}", confidence=0.6))
    elif rel_hard:
        s.append(_make_signal(method, "relationship", "relationship_conflict", "negative",
            strength=0.55, evidence=f"夫妻宫有挑战: {fq_names}", confidence=0.5))
    else:
        s.append(_make_signal(method, "relationship", "relationship_attraction", "neutral",
            strength=0.5, evidence=f"夫妻宫: {fq_names}", confidence=0.45))

    # 3. 命宫 — 长期潜力
    ming = _get_palace("命宫")
    ming_names = _star_names(ming.get("major_stars", []))
    strong_stars = {"紫微", "天府", "太阳", "武曲", "七杀", "破军", "贪狼"}
    is_strong = any(n in strong_stars for n in ming_names)
    if is_strong:
        s.append(_make_signal(method, "self_life", "long_term_potential", "positive",
            strength=0.7, evidence=f"命宫强势: {ming_names}", confidence=0.65))
    else:
        s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
            strength=0.5, evidence=f"命宫: {ming_names}", confidence=0.55))

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
    """NOR-012: 西方占星 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    planets = raw.get("planets", {})
    aspects = raw.get("aspects", [])
    sun = planets.get("太阳", {})
    moon = planets.get("月亮", {})

    # 1. 长期潜力 — 太阳星座
    sun_sign = sun.get("sign", "") if isinstance(sun, dict) else ""
    s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
        strength=0.6, evidence=f"太阳{sun_sign}", confidence=0.65))

    # 2. 感情吸引 — 金星/月亮
    moon_sign = moon.get("sign", "") if isinstance(moon, dict) else ""
    s.append(_make_signal(method, "relationship", "relationship_attraction", "neutral",
        strength=0.55, evidence=f"月亮{moon_sign}", confidence=0.55))

    # 3. 贵人/阻力 — 相位
    hard = sum(1 for a in aspects if isinstance(a, dict) and a.get("aspect") in ("冲", "刑"))
    soft = sum(1 for a in aspects if isinstance(a, dict) and a.get("aspect") in ("合", "拱", "六合"))
    if soft > hard:
        s.append(_make_signal(method, "self_life", "noble_help", "positive",
            strength=0.55, evidence=f"吉相位{soft}凶相位{hard}", confidence=0.5))
    else:
        s.append(_make_signal(method, "self_life", "obstacle_pressure", "neutral",
            strength=0.45, evidence=f"相位吉{soft}凶{hard}", confidence=0.45))

    return s


def _normalize_vedic(method: str, raw: dict, _norm: dict) -> list[DivinationSignal]:
    """NOR-013: 吠陀占星 — ≥3 signals。"""
    s: list[DivinationSignal] = []
    planets = raw.get("planets", {})

    planet_info = []
    for name, data in planets.items():
        if isinstance(data, dict):
            planet_info.append(f"{name}:{data.get('宫(Rashi)','')}")

    # 1. 长期潜力
    s.append(_make_signal(method, "self_life", "long_term_potential", "neutral",
        strength=0.55, evidence=f"行星宫位: {'; '.join(planet_info[:3])}", confidence=0.55))

    # 2. 感情
    s.append(_make_signal(method, "relationship", "marriage_stability", "neutral",
        strength=0.45, evidence="吠陀星辰婚配参考", confidence=0.45))

    # 3. 时机
    s.append(_make_signal(method, "timing", "timing_transition", "neutral",
        strength=0.4, evidence="吠陀行运参考", confidence=0.4))

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
