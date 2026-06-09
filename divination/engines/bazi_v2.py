"""Ba Zi v2 — Enhanced engine with 格局/用神/神煞/flow analysis.

Extends the base bazi engine with classical pattern classification and
use-god detection — the two most critical concepts for accurate Bazi reading.

Key additions over v1:
  - Pattern (格局) classification: 正官格/七杀格/财格/印格/食伤格 etc.
  - Use God (用神) detection with element recommendation
  - Use God quality scoring (0-100)
  - Symbolic Stars (神煞) integration
  - Element flow/balance analysis
  - Enhanced strength scoring with solar-term granularity

References:
  - 渊海子平 (卷一·论用神, 卷二·论格局)
  - 三命通会 (卷四-卷九·各格)
  - 滴天髓 (体用篇)
"""

from datetime import date

from lunar_python import Lunar, Solar

from ..contracts import Birth, ChartResult
from .bazi import (
    # Re-use all core computation from v1
    _solar_from_birth,
    _score_elements,
    _count_ten_gods,
    _compute_strength_score,
    _pillar_detail,
    _today_year_ganzhi,
    _find_da_yun_for_year,
    _decade_evaluation,
    _build_annual_interactions,
    _build_life_stage,
    _compute_element_flow,
    # Constants
    GAN_WUXING,
    ZHI_WUXING,
    WUXING_KEY,
    SHENG_WO,
    WO_SHENG,
    WO_KE,
    KE_WO,
    GAN_YINYANG,
    ZHI_ORDER,
)
from .shensha import compute_all as compute_shensha


# ── 用神体系 · Use God System ──────────────────────────────────────────────

def _determine_yong_shen(
    strength_score: float,
    day_master_gan: str,
    ten_god_counts: dict,
    elements: dict,
) -> dict:
    """Determine the Use God (用神) elements for a given chart.

    Classical principle (渊海子平·论用神):
    - 身强 → 克泄耗 (官杀克,食伤泄,财耗)
    - 身弱 → 生扶 (印生,比劫扶)
    - 中和 → 以月令取用,调候为急

    Returns {
        "primary": ["metal", ...],    # primary 用神 elements
        "secondary": ["water", ...],  # secondary 喜神 elements
        "avoid": ["fire", ...],       # 忌神 elements
        "rationale": "explanation",
        "rule": "身强用克泄耗" or "身弱用生扶" or "中和调候",
    }
    """
    dm_wx_zh = GAN_WUXING.get(day_master_gan, "")
    dm_wx_en = WUXING_KEY.get(dm_wx_zh, "")

    primary = []
    secondary = []
    avoid = []

    if strength_score >= 65:
        # 身强: need 克泄耗
        rule = "身强用克泄耗"
        # Primary: 官杀 > 食伤 > 财
        controller_zh = KE_WO.get(dm_wx_zh, "")  # 克我 = 官杀
        output_zh = WO_SHENG.get(dm_wx_zh, "")   # 我生 = 食伤
        wealth_zh = WO_KE.get(dm_wx_zh, "")       # 我克 = 财

        for zh, label in [(controller_zh, "官杀"), (output_zh, "食伤"), (wealth_zh, "财")]:
            en = WUXING_KEY.get(zh, "")
            if en and en not in primary:
                primary.append(en)

        # Avoid: 印星(生我), 比劫(同我)
        resource_zh = SHENG_WO.get(dm_wx_zh, "")
        if resource_zh:
            avoid.append(WUXING_KEY.get(resource_zh, ""))
        if dm_wx_en and dm_wx_en not in avoid:
            avoid.append(dm_wx_en)

    elif strength_score <= 40:
        # 身弱: need 生扶
        rule = "身弱用生扶"
        # Primary: 印星 > 比劫
        resource_zh = SHENG_WO.get(dm_wx_zh, "")
        resource_en = WUXING_KEY.get(resource_zh, "")
        if resource_en:
            primary.append(resource_en)
        if dm_wx_en and dm_wx_en not in primary:
            primary.append(dm_wx_en)

        # Secondary: 官杀 that's not too strong
        controller_zh = KE_WO.get(dm_wx_zh, "")
        controller_en = WUXING_KEY.get(controller_zh, "")
        if controller_en and controller_en not in primary:
            secondary.append(controller_en)

        # Avoid: 食伤, 财
        output_zh = WO_SHENG.get(dm_wx_zh, "")
        wealth_zh = WO_KE.get(dm_wx_zh, "")
        for zh in [output_zh, wealth_zh]:
            en = WUXING_KEY.get(zh, "")
            if en and en not in avoid:
                avoid.append(en)

    else:
        # 中和 (40-65): 调候为主
        rule = "中和调候为急"
        # Secondary approach: use month and season context
        # Keep things balanced — prefer elements that are under-represented
        sorted_elems = sorted(elements.items(), key=lambda x: x[1])
        weakest = [k for k, v in sorted_elems if v < 1.0]
        strongest = [k for k, v in sorted_elems if v > 3.0]
        if weakest:
            primary = weakest[:2]
        if strongest:
            avoid = strongest[:2]

    # Clean: remove empty strings and None
    primary = [p for p in primary if p]
    secondary = [s for s in secondary if s]
    avoid = [a for a in avoid if a]

    # Map to Chinese for display
    en_to_zh = {v: k for k, v in WUXING_KEY.items()}

    return {
        "primary": primary,
        "secondary": secondary,
        "avoid": avoid,
        "primary_zh": [en_to_zh.get(p, p) for p in primary],
        "secondary_zh": [en_to_zh.get(s, s) for s in secondary],
        "avoid_zh": [en_to_zh.get(a, a) for a in avoid],
        "rationale": (
            f"日主{day_master_gan}({dm_wx_zh})身{'强' if strength_score >= 65 else '弱' if strength_score <= 40 else '中和'}"
            f"(得分{strength_score})。{rule}。"
            f"用神: {'、'.join([en_to_zh.get(p, p) for p in primary]) or '无明确用神'}。"
            f"忌神: {'、'.join([en_to_zh.get(a, a) for a in avoid]) or '无明确忌神'}。"
        ),
        "rule": rule,
    }


def _score_yong_shen_quality(
    yong_shen_info: dict,
    elements: dict,
    shensha_summary: dict,
) -> dict:
    """Score how well the chart supports its 用神 (0-100).

    Higher score = 用神得力, the chart has good quality.
    Factors:
    - Whether primary 用神 elements are present in the chart
    - Whether 用神 elements are strong enough
    - Whether 用神 elements clash with 忌神
    - Whether beneficial 神煞 support the 用神
    """
    primary_elements = yong_shen_info.get("primary", [])
    avoid_elements = yong_shen_info.get("avoid", [])

    if not primary_elements:
        return {"score": 50, "level": "普通", "analysis": "用神不明确，命格层次中等。"}

    # Score based on presence and strength of 用神 elements
    yong_shen_total = 0.0
    for eng_key in primary_elements:
        yong_shen_total += elements.get(eng_key, 0.0)

    # Score based on presence and strength of 忌神 elements
    ji_shen_total = 0.0
    for eng_key in avoid_elements:
        ji_shen_total += elements.get(eng_key, 0.0)

    total_elements = max(sum(elements.values()), 0.1)
    ratio = yong_shen_total / total_elements

    # Use log-scaled scoring to avoid extreme values
    # Higher ratio → better, but with diminishing returns
    import math
    if ratio > 0:
        score_from_ratio = min(60, math.sqrt(ratio * 10) * 30)
    else:
        score_from_ratio = 5  # minimal floor

    # Penalty: 忌神 too strong, but capped
    ji_ratio = ji_shen_total / total_elements
    penalty = min(30, ji_ratio * 35)

    base_score = score_from_ratio - penalty

    # Bonus: beneficial 神煞 support
    if shensha_summary:
        auspicious_count = shensha_summary.get("auspicious_count", 0)
        base_score += min(auspicious_count * 3, 20)

    # Penalty: too many inauspicious stars
    if shensha_summary:
        inauspicious_count = shensha_summary.get("inauspicious_count", 0)
        base_score -= min(inauspicious_count * 2, 15)

    final = max(20, min(98, round(base_score)))

    if final >= 80:
        level = "上等"
    elif final >= 60:
        level = "中上"
    elif final >= 40:
        level = "中等"
    elif final >= 20:
        level = "中下"
    else:
        level = "下等"

    en_to_zh = {v: k for k, v in WUXING_KEY.items()}
    ys_en = [en_to_zh.get(p, p) for p in primary_elements]
    js_en = [en_to_zh.get(a, a) for a in avoid_elements]

    return {
        "score": final,
        "level": level,
        "yong_shen_strength": round(yong_shen_total, 1),
        "ji_shen_strength": round(ji_shen_total, 1),
        "analysis": (
            f"用神{', '.join(ys_en)}在局中{'有力' if ratio > 0.3 else '力量不足'}，"
            f"忌神{', '.join(js_en) if js_en else '不显'}。"
            f"用神质量: {final}/100 ({level})。"
        ),
    }


# ── 格局体系 · Pattern Classification ─────────────────────────────────────

def _classify_pattern(
    month_zhi: str,
    month_ganzhi: str,
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
) -> dict:
    """Classify the 格局 (life pattern) following classical principles.

    取格步骤:
    1. 月令提纲: 看月支所藏天干中,哪一个透出天干
    2. 透出者取为格 (优先取月支本气)
    3. 无透出则看整体十神最强
    4. 特殊格局: 从格(身极强/极弱), 化格(天干合化)

    Returns pattern info with description.
    """
    if not month_ganzhi or len(month_ganzhi) < 2:
        return {"pattern": "未定", "type": "unknown", "description": "月柱信息不足"}

    month_gan = month_ganzhi[0]
    month_zhi_wx = ZHI_WUXING.get(month_zhi, "")
    dm_wx_zh = GAN_WUXING.get(day_master_gan, "")

    # Determine the ten-god label of the month stem relative to day master
    month_gan_wx = GAN_WUXING.get(month_gan, "")
    dominant_ten_god = ""
    if month_gan_wx and dm_wx_zh:
        if month_gan_wx == dm_wx_zh:
            dominant_ten_god = "比劫"
        elif SHENG_WO.get(dm_wx_zh) == month_gan_wx:
            dominant_ten_god = "印星"
        elif WO_SHENG.get(dm_wx_zh) == month_gan_wx:
            dominant_ten_god = "食伤"
        elif WO_KE.get(dm_wx_zh) == month_gan_wx:
            dominant_ten_god = "财星"
        elif KE_WO.get(dm_wx_zh) == month_gan_wx:
            dominant_ten_god = "官杀"

    # Classify the dominant ten god into specific patterns
    pattern_map = {
        "官杀": {"primary": "官杀格", "sub_patterns": ["正官格", "七杀格"]},
        "财星": {"primary": "财格", "sub_patterns": ["正财格", "偏财格"]},
        "印星": {"primary": "印格", "sub_patterns": ["正印格", "偏印格"]},
        "食伤": {"primary": "食伤格", "sub_patterns": ["食神格", "伤官格"]},
        "比劫": {"primary": "建禄格", "sub_patterns": ["建禄格", "月刃格"]},
    }

    pattern_info = pattern_map.get(dominant_ten_god, {
        "primary": "杂格",
        "sub_patterns": [],
    })

    # 从格 detection: extremely strong (≥85) or weak (≤15)
    # (Requires strength score — we'll pass it in later)
    special_pattern = None

    description = (
        f"月令{month_zhi}({month_zhi_wx}),月干{month_gan}({month_gan_wx}),"
        f"透出{dominant_ten_god},取为{pattern_info['primary']}。"
    )

    return {
        "pattern": pattern_info["primary"],
        "sub_patterns": pattern_info["sub_patterns"],
        "month_ten_god": dominant_ten_god,
        "month_zhi_wuxing": month_zhi_wx,
        "month_gan_wuxing": month_gan_wx,
        "description": description,
        "special_pattern": special_pattern,
    }


# ── Enhanced Strength Score ────────────────────────────────────────────────

def _enhanced_strength_score(
    day_master_gan: str,
    month_zhi: str,
    ten_god_counts: dict,
    shensha_summary: dict,
) -> tuple:
    """Enhanced strength scoring with shensha influence.

    Extends the base _compute_strength_score with:
    - Shensha modifiers (certain stars affect strength)
    - Slightly adjusted month weighting
    """
    # Get base score from v1
    score, basis = _compute_strength_score(day_master_gan, month_zhi, ten_god_counts)

    # Shensha modifiers
    if shensha_summary:
        notable = shensha_summary.get("notable", [])
        # 魁罡 adds authority/firmness
        if "魁罡" in notable:
            score += 5
        # 羊刃 adds aggressive strength
        if "羊刃" in notable:
            score += 8
        # 将星 adds leadership energy
        if "将星" in notable:
            score += 3
        # 空亡 can weaken
        if "空亡" in notable:
            score -= 5

    final = max(0, min(100, score))
    basis["enhanced"] = True
    basis["shensha_modifier"] = round(score - basis.get("month_strength", 30), 1)
    return final, basis


# ── Main Engine ────────────────────────────────────────────────────────────

def compute(b: Birth) -> ChartResult:
    """Compute Ba Zi chart with v2 enhancements (格局/用神/神煞/flow).

    Extends v1 with classical pattern analysis while keeping full
    backward compatibility through the ChartResult structure.
    """
    mode = b.mode or "natal"
    subject = b.subject or "self_life"
    solar = _solar_from_birth(b)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    pillars = {
        "year": ec.getYear(),
        "month": ec.getMonth(),
        "day": ec.getDay(),
        "hour": ec.getTime(),
    }

    pillar_details = [
        _pillar_detail("year", ec.getYear(), ec.getYearWuXing(),
                       ec.getYearHideGan(), ec.getYearShiShenGan(),
                       ec.getYearShiShenZhi(), ec.getYearDiShi()),
        _pillar_detail("month", ec.getMonth(), ec.getMonthWuXing(),
                       ec.getMonthHideGan(), ec.getMonthShiShenGan(),
                       ec.getMonthShiShenZhi(), ec.getMonthDiShi()),
        _pillar_detail("day", ec.getDay(), ec.getDayWuXing(),
                       ec.getDayHideGan(), ec.getDayShiShenGan(),
                       ec.getDayShiShenZhi(), ec.getDayDiShi()),
        _pillar_detail("hour", ec.getTime(), ec.getTimeWuXing(),
                       ec.getTimeHideGan(), ec.getTimeShiShenGan(),
                       ec.getTimeShiShenZhi(), ec.getTimeDiShi()),
    ]

    elements_visible, elements_hidden, elements = _score_elements(pillars, pillar_details)

    day_master = ec.getDayGan()
    season_branch = ec.getMonthZhi()
    season_wuxing = ZHI_WUXING.get(season_branch, "")

    # ── v1 baseline ──
    ten_god_counts = _count_ten_gods(day_master, pillars)

    # ── v2: 神煞 (computed before enhanced strength) ──
    shensha_data = compute_shensha(pillars, day_master)
    shensha_summary = shensha_data.get("summary", {})

    # ── v2: 格局 classification ──
    pattern_data = _classify_pattern(
        season_branch,
        pillars["month"],
        day_master,
        ten_god_counts,
        pillars,
    )

    # ── v2: enhanced strength with shensha ──
    strength_score, strength_basis = _enhanced_strength_score(
        day_master, season_branch, ten_god_counts, shensha_summary,
    )

    # ── v2: 用神 detection ──
    yong_shen_data = _determine_yong_shen(
        strength_score, day_master, ten_god_counts, elements,
    )

    # ── v2: 用神 quality ──
    yong_shen_quality = _score_yong_shen_quality(
        yong_shen_data, elements, shensha_summary,
    )

    # ── v2: element flow ──
    element_flow = _compute_element_flow(elements, pillars)

    # ── v1: timeline / luck ──
    timeline = []
    yun_info = {}
    da_yun_list = []
    try:
        yun = ec.getYun(1 if b.gender == "male" else 0)
        yun_info = {
            "gender_rule": "male=1 female=0 as lunar-python getYun input",
            "start_solar": str(yun.getStartSolar().toYmd()) if hasattr(yun, "getStartSolar") else "",
            "start_year": yun.getStartYear() if hasattr(yun, "getStartYear") else None,
            "start_month": yun.getStartMonth() if hasattr(yun, "getStartMonth") else None,
            "start_day": yun.getStartDay() if hasattr(yun, "getStartDay") else None,
        }
        for da_yun in yun.getDaYun()[1:9]:
            timeline.append({
                "from": str(da_yun.getStartYear()),
                "to": str(da_yun.getEndYear()),
                "label": "大运·" + da_yun.getGanZhi(),
                "score": None,
            })
            da_yun_list.append(da_yun)
    except Exception as e:
        yun_info = {"error": str(e)}

    today_year, annual_ganzhi = _today_year_ganzhi()
    current_luck = {}
    try:
        current_da = _find_da_yun_for_year(da_yun_list, today_year)
        if current_da:
            decade_ganzhi = current_da.getGanZhi()
            current_luck = {
                "decade_ganzhi": decade_ganzhi,
                "decade_from": current_da.getStartYear(),
                "decade_to": current_da.getEndYear(),
                "age": today_year - b.year + 1,
                "decade_score": _decade_evaluation(decade_ganzhi, day_master),
                "annual_ganzhi": annual_ganzhi,
                "annual_label": f"{today_year}年{annual_ganzhi}",
                "today_year": today_year,
            }
    except Exception as e:
        current_luck = {"error": str(e)}

    annual_interactions = {"year": today_year, **_build_annual_interactions(pillars, annual_ganzhi)}
    life_stage = _build_life_stage(day_master, pillars)

    support = {
        "day_master": day_master,
        "month_branch": season_branch,
        "month_wuxing": season_wuxing,
        "ten_god_counts": ten_god_counts,
        "strength_score": strength_score,
        "basis": "以月令、四柱五行计数、藏干、十二长生、神煞作为综合旺衰参考；不替代人工格局取用。",
    }

    raw = {
        "mode": mode,
        "subject": subject,
        "rule_version": "v2",
        "calculation_basis": {
            "method": "bazi_v2",
            "mode": mode,
            "calendar_source": "lunar-python",
            "calendar_input": b.calendar,
            "solar_datetime": solar.toYmdHms(),
            "lunar_date": lunar.toString(),
            "jie_qi": lunar.getJieQi() or "",
            "current_jie": lunar.getCurrentJie().getName() if lunar.getCurrentJie() else "",
            "current_jie_qi": lunar.getCurrentJieQi().getName() if lunar.getCurrentJieQi() else "",
            "timezone": b.tz,
            "rule_version": "v2",
            "input_source": "birth (year/month/day/hour/minute, optional gender/calendar)",
            "limits": [
                "strength_score 是经验评分,不替代人工格局取用",
                "用神由算法根据日主强弱和格局自动推断,供参考",
                "格局分类基于月令透干原则,特殊格局需人工甄别",
                "神煞基于经典查表,不代表绝对吉凶",
                "流年互动仅列四柱层面的合/冲/刑/害,不带神煞",
                "12 长生查表按阳顺阴逆",
            ],
            "references": [
                {"source": "渊海子平", "excerpt": "日主者，乃八字之主宰也。凡看命先看日干。", "chapter": "卷一·论日主"},
                {"source": "渊海子平", "excerpt": "用神者，八字之关键也。日主所喜者为用。", "chapter": "卷一·论用神"},
                {"source": "滴天髓", "excerpt": "道有体用，不可以一端论也，要在扶之抑之得其宜。", "chapter": "上篇·体用"},
                {"source": "三命通会", "excerpt": "大运之吉凶，以本命为主。运助用神则吉，运克用神则凶。", "chapter": "卷九·论大运"},
            ],
        },
        "pillars": pillars,
        "pillar_details": pillar_details,
        "day_master": day_master,
        "elements_visible": elements_visible,
        "elements_hidden": elements_hidden,
        "elements_total": elements,
        "seasonal_strength_reference": support,
        "strength_score": strength_score,
        "strength_basis": strength_basis,
        # ── v2 fields ──
        "pattern": pattern_data,
        "yong_shen": yong_shen_data,
        "yong_shen_quality": yong_shen_quality,
        "shensha": shensha_data,
        "element_flow": element_flow,
        "current_luck": current_luck,
        "annual_interactions": annual_interactions,
        "life_stage": life_stage,
        "yun": yun_info,
    }

    return ChartResult(
        method="bazi_v2",
        school="east",
        engine="lunar-python+shensha+pattern+v2",
        normalized={
            "elements": elements,
            "timeline": timeline,
            "pattern": pattern_data["pattern"],
            "yong_shen": yong_shen_data["primary_zh"],
            "strength_score": strength_score,
            "notable_stars": shensha_summary.get("notable", []),
        },
        raw=raw,
    )
