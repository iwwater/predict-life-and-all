"""标准化器 — 将不同术法的 ChartResult 转为统一的 DivinationSignal 列表。

BE-006: 标准化文件

每种术法的 raw 数据结构不同，本模块负责从中提取统一信号。
核心思路：
  - 遍历每个术法的 raw/normalized 数据
  - 提取关键信号 (signal_key + polarity + strength)
  - 附上盘面证据 (evidence)
  - 输出统一的 DivinationSignal 格式
"""
from __future__ import annotations

from typing import Any

from divination.contracts import ChartResult

from .schema import DivinationSignal


def normalize(method: str, chart: ChartResult) -> list[DivinationSignal]:
    """将单个术法的排盘结果标准化为统一信号列表。

    Args:
        method: 术法标识
        chart: 排盘结果

    Returns:
        DivinationSignal 列表
    """
    raw = chart.raw
    normalized = chart.normalized

    signals: list[DivinationSignal] = []

    try:
        if method in ("bazi", "bazi_v2"):
            signals.extend(_normalize_bazi(method, raw, normalized))
        elif method == "ziwei":
            signals.extend(_normalize_ziwei(method, raw, normalized))
        elif method == "qimen":
            signals.extend(_normalize_qimen(method, raw, normalized))
        elif method == "liuyao":
            signals.extend(_normalize_liuyao(method, raw, normalized))
        elif method == "meihua":
            signals.extend(_normalize_meihua(method, raw, normalized))
        elif method in ("fengshui", "bazhai"):
            signals.extend(_normalize_bazhai(method, raw, normalized))
        elif method == "xuankong":
            signals.extend(_normalize_xuankong(method, raw, normalized))
        elif method == "western":
            signals.extend(_normalize_western(method, raw, normalized))
        elif method == "vedic":
            signals.extend(_normalize_vedic(method, raw, normalized))
        elif method == "tarot":
            signals.extend(_normalize_tarot(method, raw, normalized))
        elif method == "numerology":
            signals.extend(_normalize_numerology(method, raw, normalized))
    except Exception:
        # 单个术法标准化失败不阻塞整体流程
        pass

    return signals


# ── 各术法标准化实现 ─────────────────────────────────────────────────────────

def _bazi_strength_pattern(raw: dict) -> list[DivinationSignal]:
    """从八字提取日主强弱和格局信号。"""
    signals: list[DivinationSignal] = []
    day_master = raw.get("day_master", "")
    strength = raw.get("strength_score", 50)
    pattern = raw.get("pattern", {})
    pattern_name = pattern.get("pattern", "") if isinstance(pattern, dict) else str(pattern)

    # 日主强弱
    if strength > 55:
        signals.append(DivinationSignal(
            method="bazi_v2", domain="self_life",
            signal_key="day_master_strong",
            polarity="positive", strength=strength,
            evidence=f"日主{day_master}，身强({strength}分)",
            confidence=75,
        ))
    elif strength < 45:
        signals.append(DivinationSignal(
            method="bazi_v2", domain="self_life",
            signal_key="day_master_weak",
            polarity="negative", strength=100 - strength,
            evidence=f"日主{day_master}，身弱({strength}分)",
            confidence=70,
        ))
    else:
        signals.append(DivinationSignal(
            method="bazi_v2", domain="self_life",
            signal_key="day_master_balanced",
            polarity="neutral", strength=strength,
            evidence=f"日主{day_master}，中和({strength}分)",
            confidence=70,
        ))

    # 格局
    if pattern_name:
        signals.append(DivinationSignal(
            method="bazi_v2", domain="self_life",
            signal_key=f"pattern_{pattern_name}",
            polarity="positive" if "贵" in str(pattern.get("category", "")) else "neutral",
            strength=65,
            evidence=f"格局「{pattern_name}」({pattern.get('category', '待定')}类)",
            confidence=65,
        ))

    return signals


def _bazi_career_wealth(raw: dict) -> list[DivinationSignal]:
    """从八字提取事业财运信号。"""
    signals: list[DivinationSignal] = []
    elements = raw.get("elements", {})
    day_master = raw.get("day_master", "")

    # 用神
    yong = raw.get("yong_shen", {})
    yong_name = yong.get("yong_shen", "") if isinstance(yong, dict) else str(yong)
    yong_score = raw.get("yong_shen_quality", {}).get("score", 50)
    if isinstance(yong_score, dict):
        yong_score = yong_score.get("score", 50)

    if yong_name:
        signals.append(DivinationSignal(
            method="bazi_v2", domain="career",
            signal_key="yong_shen",
            polarity="positive" if yong_score > 45 else "negative",
            strength=min(90, yong_score + 10),
            evidence=f"用神{yong_name}(质量{yong_score}分)",
            confidence=70,
        ))

    # 五行平衡
    if elements:
        total = sum(elements.values())
        if total > 0:
            dominant = max(elements, key=elements.get)
            weak = min(elements, key=elements.get)
            signals.append(DivinationSignal(
                method="bazi_v2", domain="self_life",
                signal_key="element_balance",
                polarity="neutral",
                strength=50,
                evidence=f"五行: 最旺{dominant}，最弱{weak}",
                confidence=60,
            ))

    # 神煞
    shensha = raw.get("shensha", {})
    notable = shensha.get("summary", {}).get("notable", []) if isinstance(shensha, dict) else []
    if notable:
        signals.append(DivinationSignal(
            method="bazi_v2", domain="self_life",
            signal_key="notable_stars",
            polarity="positive" if any("吉" in str(n) for n in notable) else "neutral",
            strength=55,
            evidence=f"神煞: {notable[:3]}",
            confidence=55,
        ))

    return signals


def _normalize_bazi(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化八字/八字精算版。"""
    signals: list[DivinationSignal] = []
    signals.extend(_bazi_strength_pattern(raw))
    signals.extend(_bazi_career_wealth(raw))

    # 大运流年
    timeline = _normalized.get("timeline", [])
    if timeline:
        current = timeline[0] if timeline else {}
        signals.append(DivinationSignal(
            method=method, domain="timing",
            signal_key="current_luck_cycle",
            polarity="neutral",
            strength=55,
            evidence=f"当前大运: {current.get('label', '')}",
            confidence=55,
        ))

    return signals


def _normalize_ziwei(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化紫微斗数。"""
    signals: list[DivinationSignal] = []
    palaces = raw.get("palaces", [])

    # 命宫
    ming = next((p for p in palaces if p.get("name") == "命宫"), {})
    ming_stars = ming.get("major_stars", [])
    # Handle dict stars with 'name' key
    _ming_names = [s.get("name", s) if isinstance(s, dict) else s for s in ming_stars]
    strong_stars = {"紫微", "天府", "太阳", "武曲", "七杀", "破军", "贪狼"}
    is_strong = any(n in strong_stars for n in _ming_names)

    signals.append(DivinationSignal(
        method=method, domain="self_life",
        signal_key="ming_palace_strength",
        polarity="positive" if is_strong else "neutral",
        strength=70 if is_strong else 50,
        evidence=f"命宫主星: {_ming_names}，{'强势' if is_strong else '中和'}",
        confidence=65,
    ))

    # 官禄宫
    guanlu = next((p for p in palaces if p.get("name") == "官禄宫"), {})
    gl_stars = guanlu.get("major_stars", [])
    _gl_names = [s.get("name", s) if isinstance(s, dict) else s for s in gl_stars]
    career_strong = any(n in {"紫微", "天府", "天相", "太阳", "武曲"} for n in _gl_names)

    signals.append(DivinationSignal(
        method=method, domain="career",
        signal_key="career_palace",
        polarity="positive" if career_strong else "neutral",
        strength=65 if career_strong else 45,
        evidence=f"官禄宫主星: {_gl_names}",
        confidence=60,
    ))

    # 夫妻宫
    fuqi = next((p for p in palaces if p.get("name") == "夫妻宫"), {})
    fq_stars = fuqi.get("major_stars", [])
    _fq_names = [s.get("name", s) if isinstance(s, dict) else s for s in fq_stars]
    good_rel = any(n in {"天同", "太阴", "廉贞", "天相"} for n in _fq_names)
    challenging_rel = any(n in {"七杀", "破军", "贪狼", "巨门"} for n in _fq_names)

    if good_rel:
        signals.append(DivinationSignal(
            method=method, domain="relationship",
            signal_key="spouse_palace_good",
            polarity="positive", strength=65,
            evidence=f"夫妻宫主星: {_fq_names}，吉星",
            confidence=60,
        ))
    elif challenging_rel:
        signals.append(DivinationSignal(
            method=method, domain="relationship",
            signal_key="spouse_palace_challenging",
            polarity="negative", strength=55,
            evidence=f"夫妻宫主星: {_fq_names}，有挑战",
            confidence=55,
        ))

    return signals


def _normalize_qimen(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化奇门遁甲。"""
    signals: list[DivinationSignal] = []
    duan = raw.get("断", raw)

    # 格局
    patterns = duan.get("格局", [])
    if patterns:
        good = sum(1 for p in patterns if "吉" in str(p))
        bad = sum(1 for p in patterns if "凶" in str(p))
        signals.append(DivinationSignal(
            method=method, domain="decision",
            signal_key="qimen_pattern",
            polarity="positive" if good > bad else "negative" if bad > good else "neutral",
            strength=min(90, 50 + (good - bad) * 10),
            evidence=f"格局: {patterns[:3]}（吉{good}凶{bad}）",
            confidence=65,
        ))

    # 门状态
    door_status = duan.get("门状态", {})
    if door_status:
        signals.append(DivinationSignal(
            method=method, domain="decision",
            signal_key="door_status",
            polarity="neutral",
            strength=55,
            evidence=f"门状态: {door_status}",
            confidence=55,
        ))

    return signals


def _normalize_liuyao(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化六爻。"""
    signals: list[DivinationSignal] = []
    duan = raw.get("断", raw)
    gua_name = raw.get("本卦", {}).get("name", "")

    verdict = duan.get("断语", duan.get("提示", ""))
    polarity = "neutral"
    if any(w in str(verdict) for w in ("吉", "利", "成", "可", "好")):
        polarity = "positive"
    elif any(w in str(verdict) for w in ("凶", "不利", "不成", "慎", "忌")):
        polarity = "negative"

    signals.append(DivinationSignal(
        method=method, domain="decision",
        signal_key="liuyao_verdict",
        polarity=polarity,
        strength=65,
        evidence=f"本卦{gua_name}: {verdict}",
        confidence=60,
    ))

    return signals


def _normalize_meihua(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化梅花易数。"""
    signals: list[DivinationSignal] = []
    duan = raw.get("断", raw)

    body = raw.get("体卦", "")
    usage = raw.get("用卦", "")
    verdict = duan.get("总断", duan.get("断语", ""))

    # 体用生克
    polarity = "neutral"
    if "生" in str(verdict) and "用生体" in str(verdict):
        polarity = "positive"
    elif "克" in str(verdict) and "用克体" in str(verdict):
        polarity = "negative"

    signals.append(DivinationSignal(
        method=method, domain="decision",
        signal_key="meihua_body_usage",
        polarity=polarity,
        strength=60,
        evidence=f"体卦{body}用卦{usage}: {verdict}",
        confidence=55,
    ))

    return signals


def _normalize_bazhai(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化八宅/风水。"""
    signals: list[DivinationSignal] = []

    if method == "bazhai":
        gua = raw.get("命卦", "")
        ji = raw.get("吉方", [])
        xiong = raw.get("凶方", [])
        signals.append(DivinationSignal(
            method=method, domain="home_fengshui",
            signal_key="ming_gua",
            polarity="neutral",
            strength=55,
            evidence=f"命卦{gua}，吉方{ji}，凶方{xiong}",
            confidence=55,
        ))
    elif method == "fengshui":
        # 风水复合引擎，可能综合了八宅+玄空
        signals.append(DivinationSignal(
            method=method, domain="home_fengshui",
            signal_key="fengshui_composite",
            polarity="neutral",
            strength=55,
            evidence=str(raw.get("summary", raw))[:200],
            confidence=50,
        ))

    return signals


def _normalize_xuankong(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化玄空飞星。"""
    signals: list[DivinationSignal] = []

    yun = raw.get("运", "")
    geju = raw.get("格局", "")
    zuo = raw.get("坐", "")
    xiang = raw.get("向", "")

    signals.append(DivinationSignal(
        method=method, domain="home_fengshui",
        signal_key="xuankong_feixing",
        polarity="neutral",
        strength=55,
        evidence=f"{yun}运 {zuo}山{xiang}向，格局{geju}",
        confidence=55,
    ))

    return signals


def _normalize_western(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化西方占星。"""
    signals: list[DivinationSignal] = []
    planets = raw.get("planets", {})
    aspects = raw.get("aspects", [])
    ascendant = raw.get("ascendant", {}).get("sign", "")

    # 太阳/月亮星座
    sun = planets.get("太阳", {})
    moon = planets.get("月亮", {})
    if isinstance(sun, dict):
        signals.append(DivinationSignal(
            method=method, domain="self_life",
            signal_key="sun_sign",
            polarity="neutral",
            strength=60,
            evidence=f"太阳{sun.get('sign', '')}{sun.get('degree', 0)}°",
            confidence=65,
        ))
    if isinstance(moon, dict):
        signals.append(DivinationSignal(
            method=method, domain="self_life",
            signal_key="moon_sign",
            polarity="neutral",
            strength=55,
            evidence=f"月亮{moon.get('sign', '')}{moon.get('degree', 0)}°",
            confidence=60,
        ))

    # 上升
    if ascendant:
        signals.append(DivinationSignal(
            method=method, domain="self_life",
            signal_key="ascendant",
            polarity="neutral",
            strength=60,
            evidence=f"上升{ascendant}",
            confidence=65,
        ))

    # 相位
    hard = sum(1 for a in aspects if isinstance(a, dict) and a.get("aspect") in ("冲", "刑"))
    soft = sum(1 for a in aspects if isinstance(a, dict) and a.get("aspect") in ("合", "拱", "六合"))
    signals.append(DivinationSignal(
        method=method, domain="relationship",
        signal_key="aspect_balance",
        polarity="positive" if soft > hard else "negative" if hard > soft * 1.5 else "neutral",
        strength=55,
        evidence=f"吉相位{soft}，凶相位{hard}",
        confidence=55,
    ))

    return signals


def _normalize_vedic(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化吠陀占星。"""
    signals: list[DivinationSignal] = []
    planets = raw.get("planets", {})

    # 汇总行星宫位信息
    planet_info = []
    for name, data in planets.items():
        if isinstance(data, dict):
            rasi = data.get("宫(Rashi)", "")
            nakshatra = data.get("宿(Nakshatra)", "")
            planet_info.append(f"{name}:{rasi}/{nakshatra}")

    signals.append(DivinationSignal(
        method=method, domain="self_life",
        signal_key="vedic_planets",
        polarity="neutral",
        strength=55,
        evidence=f"行星宫宿: {'; '.join(planet_info[:5])}",
        confidence=55,
    ))

    return signals


def _normalize_tarot(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化塔罗。"""
    signals: list[DivinationSignal] = []
    cards = raw.get("牌面", [])

    positive_count = 0
    negative_count = 0
    for c in cards:
        if isinstance(c, dict):
            kw = str(c.get("关键词", ""))
            if any(w in kw for w in ("吉", "正", "成功", "爱", "光明", "和谐")):
                positive_count += 1
            elif any(w in kw for w in ("凶", "逆", "失败", "冲突", "黑暗")):
                negative_count += 1
            signals.append(DivinationSignal(
                method=method, domain="decision",
                signal_key=f"card_{c.get('位置', '')}",
                polarity="positive" if positive_count > 0 else "neutral",
                strength=55,
                evidence=f"{c.get('位置', '')}: {c.get('牌', '')} ({c.get('方位', '')})",
                confidence=50,
            ))

    # 整体倾向
    signals.append(DivinationSignal(
        method=method, domain="decision",
        signal_key="tarot_overall",
        polarity="positive" if positive_count > negative_count else
                 "negative" if negative_count > positive_count else "neutral",
        strength=50 + abs(positive_count - negative_count) * 10,
        evidence=f"正位{positive_count}逆位{negative_count}",
        confidence=50,
    ))

    return signals


def _normalize_numerology(method: str, raw: dict, _normalized: dict) -> list[DivinationSignal]:
    """标准化数字命理。"""
    signals: list[DivinationSignal] = []
    life_path = raw.get("生命灵数", raw.get("life_path", ""))

    signals.append(DivinationSignal(
        method=method, domain="self_life",
        signal_key="life_path_number",
        polarity="neutral",
        strength=50,
        evidence=f"生命灵数{life_path}: {raw.get('释义', '')}",
        confidence=45,
    ))

    return signals


# ── 批量标准化 ───────────────────────────────────────────────────────────────

def normalize_all(charts: dict[str, ChartResult]) -> list[DivinationSignal]:
    """批量标准化所有术法的排盘结果。

    Args:
        charts: {method: ChartResult}

    Returns:
        所有术法的统一信号列表
    """
    all_signals: list[DivinationSignal] = []
    for method, chart in charts.items():
        try:
            signals = normalize(method, chart)
            all_signals.extend(signals)
        except Exception:
            # 单个术法标准化失败不阻塞整体
            pass
    return all_signals
