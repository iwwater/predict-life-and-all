"""Ba Zi / Four Pillars using lunar-python as the calendar authority.

Adds v1 补全:
- strength_score (0-100) + strength_basis (5 类十神计数)
- current_luck (今日所在大运 + 流年)
- annual_interactions (流年干支 vs 原局 4 柱的合/冲/刑/害)
- life_stage (12 长生查表: 阳顺阴逆)
- rule_version + calculation_basis.input_source / limits
"""
from datetime import date

from lunar_python import Lunar, Solar

from ..contracts import Birth, ChartResult

# ---- 12 长生查表 ---------------------------------------------------------
CHANGSHENG_STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
ZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
# 阳干: 长生位
YANG_CHANGSHENG = {"甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申"}
# 阴干: 长生位 (逆推)
YIN_CHANGSHENG = {"乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯"}
GAN_YINYANG = {
    "甲": "yang", "丙": "yang", "戊": "yang", "庚": "yang", "壬": "yang",
    "乙": "yin", "丁": "yin", "己": "yin", "辛": "yin", "癸": "yin",
}

# ---- 五行 ---------------------------------------------------------------
WUXING_KEY = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}
GAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土",
    "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
ZHI_WUXING = {
    "子": "水", "亥": "水", "寅": "木", "卯": "木",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "巳": "火", "午": "火", "申": "金", "酉": "金",
}

HIDDEN_STEM_WEIGHTS = [0.7, 0.2, 0.1]


def _empty_elements() -> dict:
    return {v: 0.0 for v in WUXING_KEY.values()}


def _add_wuxing_count(bucket: dict, wuxing: str, amount: float = 1.0) -> None:
    key = WUXING_KEY.get(wuxing)
    if key:
        bucket[key] = round(float(bucket.get(key, 0.0)) + amount, 4)


def _score_elements(pillars: dict, pillar_details: list[dict]) -> tuple[dict, dict, dict]:
    """Count visible stems/branches plus weighted hidden stems.

    Earlier versions counted only the eight visible stem/branch elements. That
    can make a chart look like it has no trace of an element even when branches
    contain it in hidden stems. The default normalized view should reflect both.
    """
    visible = _empty_elements()
    hidden = _empty_elements()

    for gz in pillars.values():
        if len(gz) < 2:
            continue
        gan, zhi = gz[0], gz[1]
        _add_wuxing_count(visible, GAN_WUXING.get(gan, ""), 1.0)
        _add_wuxing_count(visible, ZHI_WUXING.get(zhi, ""), 1.0)

    for detail in pillar_details:
        for idx, gan in enumerate(detail.get("hidden_stems") or []):
            weight = HIDDEN_STEM_WEIGHTS[idx] if idx < len(HIDDEN_STEM_WEIGHTS) else 0.1
            _add_wuxing_count(hidden, GAN_WUXING.get(gan, ""), weight)

    total = _empty_elements()
    for key in total:
        total[key] = round(visible.get(key, 0.0) + hidden.get(key, 0.0), 4)
    return visible, hidden, total
# 生我 = 印星
SHENG_WO = {"金": "土", "木": "水", "水": "金", "火": "木", "土": "火"}
# 我生 = 食伤
WO_SHENG = {"金": "水", "木": "火", "水": "木", "火": "土", "土": "金"}
# 我克 = 财星
WO_KE = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}
# 克我 = 官杀
KE_WO = {"金": "火", "木": "金", "水": "土", "火": "水", "土": "木"}

# ---- 生克制化 元素流动分析 -------------------------------------------------

def _compute_element_flow(elements: dict, pillars: dict) -> dict:
    """Analyze the generation (生) and restriction (克) dynamics between elements.

    For each element, computes:
    - in_flow: how much it's generated (score from its "parent")
    - out_flow: how much generates outward (to its "child")
    - restrict_in: how much it's restricted by its "controller"
    - restrict_out: how much it restricts its "controlled"
    - balance: 0-100 score where 100 = perfect flow balance

    A healthy chart has smooth flow: each element both receives and gives.
    """
    # Chinese → English mapping
    ZH_TO_EN = WUXING_KEY
    EN_TO_ZH = {v: k for k, v in WUXING_KEY.items()}

    en_keys = list(WUXING_KEY.values())
    flow = {}
    for k in en_keys:
        flow[k] = {
            "value": elements.get(k, 0.0),
            "in_flow": 0.0,   # receives generation
            "out_flow": 0.0,  # generates outward
            "restrict_in": 0.0,  # gets restricted
            "restrict_out": 0.0,  # restricts others
            "balance": 50.0,  # default neutral
        }

    for eng_key in en_keys:
        zh_key = EN_TO_ZH.get(eng_key, "")
        if not zh_key:
            continue
        val = elements.get(eng_key, 0.0)

        # "Out flow": this element generates its child
        child_zh = WO_SHENG.get(zh_key, "")
        child_en = WUXING_KEY.get(child_zh, "")
        if child_en and child_en in flow:
            flow[child_en]["in_flow"] += val

        # "In flow": this element receives from its parent
        parent_zh = SHENG_WO.get(zh_key, "")
        parent_en = WUXING_KEY.get(parent_zh, "")
        if parent_en and parent_en in flow:
            flow[eng_key]["in_flow"] = flow[eng_key].get("in_flow", 0.0)

        # "Restrict out": this element restricts its controlled
        controlled_zh = WO_KE.get(zh_key, "")
        controlled_en = WUXING_KEY.get(controlled_zh, "")
        if controlled_en and controlled_en in flow:
            flow[controlled_en]["restrict_in"] += val

        # "Restrict in": this element is restricted by its controller
        controller_zh = KE_WO.get(zh_key, "")
        controller_en = WUXING_KEY.get(controller_zh, "")
        if controller_en and controller_en in flow:
            flow[eng_key]["restrict_in"] = flow[eng_key].get("restrict_in", 0.0)

    # Compute balance scores
    for eng_key in en_keys:
        f = flow[eng_key]
        val = f["value"]
        gen_in = f["in_flow"]
        restrict_pressure = f["restrict_in"]

        # Ideal: generation > restriction, and value is reasonable
        if val < 0.5:
            f["balance"] = max(0.0, round(gen_in * 10.0, 1))
        elif restrict_pressure > gen_in:
            # Being suppressed: score drops
            ratio = gen_in / max(restrict_pressure, 0.1)
            f["balance"] = round(max(10.0, min(90.0, ratio * 50.0)), 1)
        elif gen_in >= val * 0.5:
            # Well nourished
            f["balance"] = round(min(95.0, 60.0 + (gen_in - val * 0.5) * 20.0), 1)
        else:
            # Under-nourished
            ratio = gen_in / max(val * 0.5, 0.1)
            f["balance"] = round(max(10.0, min(70.0, ratio * 50.0)), 1)

        # Health analysis label
        if f["balance"] >= 70:
            f["label"] = "旺盛"
        elif f["balance"] >= 45:
            f["label"] = "平和"
        elif f["balance"] >= 25:
            f["label"] = "偏弱"
        else:
            f["label"] = "虚弱"

    return {
        "elements": flow,
        "overall_balance": round(
            sum(f["balance"] for f in flow.values()) / max(len(flow), 1), 1
        ),
        "interpretation": _summarize_flow(flow),
    }


def _summarize_flow(flow: dict) -> str:
    """Generate a human-readable summary of element flow dynamics."""
    strong = []
    weak = []
    for eng_key, f in flow.items():
        en_name = eng_key.capitalize()
        zh_name = {v: k for k, v in WUXING_KEY.items()}.get(eng_key, eng_key)
        if f["balance"] >= 70:
            strong.append(f"{zh_name}({f['label']})")
        elif f["balance"] < 25:
            weak.append(f"{zh_name}({f['label']})")

    parts = []
    if strong:
        parts.append(f"强旺: {'、'.join(strong)}")
    if weak:
        parts.append(f"偏弱: {'、'.join(weak)}")
    if not parts:
        parts.append("五行大致平衡")

    return "。".join(parts) + "。"


# ---- 12 支互动 -----------------------------------------------------------
CHONG_PAIRS = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
HE_PAIRS = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申")]
XING_TRIPLES = [("寅", "巳", "申"), ("丑", "戌", "未"), ("子", "卯")]
HAI_PAIRS = [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]
# 天干合
TIANGAN_HE = {
    "甲": "己", "己": "甲",
    "乙": "庚", "庚": "乙",
    "丙": "辛", "辛": "丙",
    "丁": "壬", "壬": "丁",
    "戊": "癸", "癸": "戊",
}


def _is_yang(gan: str) -> bool:
    return GAN_YINYANG.get(gan) == "yang"


def _changsheng_index(gan: str, zhi: str) -> int:
    """Return 12-stage index for (gan, zhi), or -1 when unknown."""
    if gan not in YANG_CHANGSHENG and gan not in YIN_CHANGSHENG:
        return -1
    if zhi not in ZHI_ORDER:
        return -1
    start_zhi = YANG_CHANGSHENG.get(gan) if _is_yang(gan) else YIN_CHANGSHENG.get(gan)
    start_idx = ZHI_ORDER.index(start_zhi)
    target_idx = ZHI_ORDER.index(zhi)
    if _is_yang(gan):
        return (target_idx - start_idx) % 12
    return (start_idx - target_idx) % 12


def _stage_for(gan: str, zhi: str) -> str:
    idx = _changsheng_index(gan, zhi)
    if idx < 0:
        return ""
    return CHANGSHENG_STAGES[idx]


def _zhi_relationship(a: str, b: str) -> list[str]:
    if a == b or not a or not b:
        return []
    rels = []
    if any({a, b} == set(p) for p in CHONG_PAIRS):
        rels.append("冲")
    if any({a, b} == set(p) for p in HE_PAIRS):
        rels.append("合")
    if any(a in t and b in t for t in XING_TRIPLES):
        rels.append("刑")
    if any({a, b} == set(p) for p in HAI_PAIRS):
        rels.append("害")
    return rels


def _gan_relationship(a: str, b: str) -> str:
    if TIANGAN_HE.get(a) == b:
        return "合"
    return ""


def _ten_god_label(day_master_wx: str, target_wx: str) -> str:
    if not target_wx or not day_master_wx:
        return ""
    if target_wx == day_master_wx:
        return "比劫"
    if SHENG_WO.get(day_master_wx) == target_wx:
        return "印星"
    if WO_SHENG.get(day_master_wx) == target_wx:
        return "食伤"
    if WO_KE.get(day_master_wx) == target_wx:
        return "财星"
    if KE_WO.get(day_master_wx) == target_wx:
        return "官杀"
    return ""


def _count_ten_gods(day_master_gan: str, pillars: dict) -> dict:
    """Count five categories of ten gods across all 4 pillars (干 + 支)."""
    dm_wx = GAN_WUXING.get(day_master_gan, "")
    counts = {"比劫": 0, "印星": 0, "食伤": 0, "官杀": 0, "财星": 0}
    seen_day_master = False
    for gz in pillars.values():
        if len(gz) < 2:
            continue
        gan, zhi = gz[0], gz[1]
        if gan == day_master_gan and not seen_day_master:
            seen_day_master = True
        else:
            gan_wx = GAN_WUXING.get(gan, "")
            label = _ten_god_label(dm_wx, gan_wx)
            if label:
                counts[label] += 1
        zhi_wx = ZHI_WUXING.get(zhi, "")
        label = _ten_god_label(dm_wx, zhi_wx)
        if label:
            counts[label] += 1
    return counts


def _month_strength_score(month_zhi: str, day_master_gan: str) -> int:
    """0-40: month strength contribution."""
    dm_wx = GAN_WUXING.get(day_master_gan, "")
    season_wx = ZHI_WUXING.get(month_zhi, "")
    if season_wx == dm_wx:
        return 40  # 得令
    if SHENG_WO.get(dm_wx) == season_wx:
        return 30  # 印当令
    if WO_SHENG.get(dm_wx) == season_wx:
        return 15  # 食伤当令 (泄气)
    if WO_KE.get(dm_wx) == season_wx:
        return 20  # 财当令
    if KE_WO.get(dm_wx) == season_wx:
        return 5   # 官杀当令 (克我)
    return 10


def _compute_strength_score(day_master_gan: str, month_zhi: str, ten_god_counts: dict) -> tuple:
    """经验评分: 0-100,综合月令 + 同党/异党计数。"""
    month_strength = _month_strength_score(month_zhi, day_master_gan)
    peer_count = ten_god_counts.get("比劫", 0)
    resource_count = ten_god_counts.get("印星", 0)
    ally_count = peer_count + resource_count
    output_count = (
        ten_god_counts.get("食伤", 0)
        + ten_god_counts.get("财星", 0)
        + ten_god_counts.get("官杀", 0)
    )
    ally_bonus = min(ally_count * 4, 30)
    output_penalty = min(output_count * 3, 30)
    score = 30 + month_strength + ally_bonus - output_penalty
    if score > 100:
        score = 100
    if score < 0:
        score = 0
    basis = {
        "month_strength": month_strength,
        "month_branch": month_zhi,
        "month_wuxing": ZHI_WUXING.get(month_zhi, ""),
        "peer_count": peer_count,
        "resource_count": resource_count,
        "output_count": ten_god_counts.get("食伤", 0),
        "official_count": ten_god_counts.get("官杀", 0),
        "wealth_count": ten_god_counts.get("财星", 0),
        "ally_total": ally_count,
    }
    return score, basis


def _solar_from_birth(b: Birth) -> Solar:
    if b.calendar == "lunar":
        return Lunar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0).getSolar()
    return Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)


def _pillar_detail(label, ganzhi, wuxing, hide_gan, shi_shen_gan, shi_shen_zhi, dishi) -> dict:
    return {
        "label": label,
        "ganzhi": ganzhi,
        "gan": ganzhi[0],
        "zhi": ganzhi[1],
        "wuxing": wuxing,
        "hidden_stems": list(hide_gan or []),
        "ten_god_stem": shi_shen_gan,
        "ten_god_branch": list(shi_shen_zhi or []),
        "growth_stage": dishi,
    }


def _today_year_ganzhi() -> tuple:
    """(year, annual_ganzhi) for today."""
    today = date.today()
    s = Solar.fromYmd(today.year, today.month, today.day)
    l = s.getLunar()
    return today.year, l.getYearInGanZhi()


def _find_da_yun_for_year(da_yun_list, year: int):
    for da in da_yun_list:
        if da.getStartYear() <= year <= da.getEndYear():
            return da
    return None


def _decade_evaluation(ganzhi: str, day_master_gan: str) -> int:
    """Simple decade score: 70 ally, 50 wealth, 40 official, 30 output."""
    if not ganzhi or len(ganzhi) < 2:
        return 50
    gan, zhi = ganzhi[0], ganzhi[1]
    dm_wx = GAN_WUXING.get(day_master_gan, "")
    gz_wx_set = {GAN_WUXING.get(gan, ""), ZHI_WUXING.get(zhi, "")}
    if dm_wx in gz_wx_set:
        return 70  # 比劫
    if SHENG_WO.get(dm_wx) in gz_wx_set:
        return 70  # 印
    if any(WO_SHENG.get(gx) == dm_wx for gx in gz_wx_set):
        return 30  # 食伤
    if any(WO_KE.get(dm_wx) == gx for gx in gz_wx_set):
        return 50  # 财
    if any(KE_WO.get(dm_wx) == gx for gx in gz_wx_set):
        return 40  # 官杀
    return 50


def _build_annual_interactions(pillars: dict, annual_ganzhi: str) -> dict:
    """流年干支 vs 原局 4 柱的合/冲/刑/害。"""
    interactions = []
    if not annual_ganzhi or len(annual_ganzhi) < 2:
        return {"ganzhi": annual_ganzhi, "interactions": interactions}
    annual_gan, annual_zhi = annual_ganzhi[0], annual_ganzhi[1]
    kind_map = {"冲": "clash", "合": "combine", "刑": "punish", "害": "harm"}
    for label, gz in pillars.items():
        if not gz or len(gz) < 2:
            continue
        pillar_gan, pillar_zhi = gz[0], gz[1]
        for kind in _zhi_relationship(annual_zhi, pillar_zhi):
            interactions.append({
                "pillar": label,
                "pillar_ganzhi": gz,
                "kind": kind_map.get(kind, kind),
                "kind_zh": kind,
                "note": f"流年{annual_zhi}与{label}柱{pillar_zhi}{kind}",
            })
        if _gan_relationship(annual_gan, pillar_gan):
            interactions.append({
                "pillar": label,
                "pillar_ganzhi": gz,
                "kind": "combine",
                "kind_zh": "天干合",
                "note": f"流年{annual_gan}与{label}柱{pillar_gan}天干合",
            })
    return {"ganzhi": annual_ganzhi, "interactions": interactions}


def _build_life_stage(day_master: str, pillars: dict) -> dict:
    stages = []
    for label, gz in pillars.items():
        if not gz or len(gz) < 2:
            continue
        zhi = gz[1]
        stages.append({
            "pillar": label,
            "pillar_ganzhi": gz,
            "zhi": zhi,
            "stage": _stage_for(day_master, zhi),
        })
    return {
        "day_master": day_master,
        "is_yang": _is_yang(day_master),
        "rule": "阳顺阴逆: 阳干从长生位起子位顺行, 阴干从长生位起子位逆行",
        "stages": stages,
    }


def compute(b: Birth) -> ChartResult:
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
        _pillar_detail("year", ec.getYear(), ec.getYearWuXing(), ec.getYearHideGan(), ec.getYearShiShenGan(), ec.getYearShiShenZhi(), ec.getYearDiShi()),
        _pillar_detail("month", ec.getMonth(), ec.getMonthWuXing(), ec.getMonthHideGan(), ec.getMonthShiShenGan(), ec.getMonthShiShenZhi(), ec.getMonthDiShi()),
        _pillar_detail("day", ec.getDay(), ec.getDayWuXing(), ec.getDayHideGan(), ec.getDayShiShenGan(), ec.getDayShiShenZhi(), ec.getDayDiShi()),
        _pillar_detail("hour", ec.getTime(), ec.getTimeWuXing(), ec.getTimeHideGan(), ec.getTimeShiShenGan(), ec.getTimeShiShenZhi(), ec.getTimeDiShi()),
    ]

    elements_visible, elements_hidden, elements = _score_elements(pillars, pillar_details)

    day_master = ec.getDayGan()
    season_branch = ec.getMonthZhi()
    season_wuxing = ZHI_WUXING.get(season_branch, "")

    ten_god_counts = _count_ten_gods(day_master, pillars)
    strength_score, strength_basis = _compute_strength_score(day_master, season_branch, ten_god_counts)

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

    # --- current_luck (今天所在大运 + 流年) ---
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
                "age": today_year - b.year + 1,  # 虚岁近似
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
        "basis": "以月令、四柱五行计数、藏干和十二长生作为旺衰参考；不替代人工格局取用。",
    }

    raw = {
        "mode": mode,
        "subject": subject,
        "rule_version": "v1",
        "calculation_basis": {
            "method": "bazi",
            "mode": mode,
            "calendar_source": "lunar-python",
            "calendar_input": b.calendar,
            "solar_datetime": solar.toYmdHms(),
            "lunar_date": lunar.toString(),
            "jie_qi": lunar.getJieQi() or "",
            "current_jie": lunar.getCurrentJie().getName() if lunar.getCurrentJie() else "",
            "current_jie_qi": lunar.getCurrentJieQi().getName() if lunar.getCurrentJieQi() else "",
            "timezone": b.tz,
            "rule_version": "v1",
            "input_source": "birth (year/month/day/hour/minute, optional gender/calendar)",
            "limits": [
                "strength_score 是经验评分,不替代人工格局取用",
                "流年互动仅列四柱层面的合/冲/刑/害,不带神煞",
                "12 长生查表按阳顺阴逆,只反映十二长生阶段,不替代神煞和大运细节",
            ],
            "references": [
                {"source": "渊海子平", "excerpt": "日主者，乃八字之主宰也。凡看命先看日干。", "chapter": "卷一·论日主"},
                {"source": "滴天髓", "excerpt": "欲识三元万法宗，先观帝载与神功。", "chapter": "上篇·通神论"},
                {"source": "三命通会", "excerpt": "财为养命之源。正官为六格之首。", "chapter": "卷四·卷六"},
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
        "current_luck": current_luck,
        "annual_interactions": annual_interactions,
        "life_stage": life_stage,
        "yun": yun_info,
    }
    return ChartResult(
        method="bazi",
        school="east",
        engine="lunar-python+strength-v1",
        normalized={"elements": elements, "timeline": timeline},
        raw=raw,
    )
