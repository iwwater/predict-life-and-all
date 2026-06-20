"""八字 / 四柱  ——  lunar-python (MIT)。"""
from lunar_python import Solar

from .. import wuxing as _wuxing
from ..contracts import Birth, ChartResult

_WX = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}

# ── 兼容层: bazi_v2 与 hour_calibrator 需要的常量别名 ───────────────────────
# 复用 wuxing 模块的常量, 并补齐 bazi_v2 用的命名 (WUXING_KEY/KE_WO/SHENG_WO).
GAN_WUXING = _wuxing.GAN_WX                              # 天干 → 五行
ZHI_WUXING = _wuxing.ZHI_WX                              # 地支 → 五行
WO_SHENG = _wuxing.SHENG                                 # 我生
WO_KE = _wuxing.KE                                       # 我克
WUXING_KEY = {"木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"}
# 反向映射: 五行 → 克我/生我 (生克闭环)
KE_WO = {v: k for k, v in WO_KE.items()}                 # 克我 (我被X克 → X克我)
SHENG_WO = {v: k for k, v in WO_SHENG.items()}           # 生我 (我被X生 → X生我)


def compute(b: Birth, zi_hour: str = "late") -> ChartResult:
    """zi_hour: 'late'=晚子(23点不换日,lunar-python默认) | 'early'=早子(23点起算次日)"""
    h, d_, mo_, y_ = b.hour, b.day, b.month, b.year
    if zi_hour == "early" and b.hour == 23:
        from datetime import datetime, timedelta
        nd = datetime(b.year, b.month, b.day) + timedelta(days=1)
        y_, mo_, d_, h = nd.year, nd.month, nd.day, 0
        b = type(b)(**{**b.__dict__, "year": y_, "month": mo_, "day": d_, "hour": 0})
    if b.lng is not None:
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo

            from ..solartime import true_solar_time
            tst = true_solar_time(datetime(b.year,b.month,b.day,b.hour,b.minute,tzinfo=ZoneInfo(b.tz)), b.lng)
            solar = Solar.fromYmdHms(tst.year,tst.month,tst.day,tst.hour,tst.minute,0)
        except Exception:
            solar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
    else:
        solar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
    ec = solar.getLunar().getEightChar()
    pillars = {
        "year": ec.getYear(), "month": ec.getMonth(),
        "day": ec.getDay(), "hour": ec.getTime(),
    }
    # 五行强弱：数四柱天干地支藏干里各五行出现次数（简化版）
    elements = {v: 0 for v in _WX.values()}
    for wx in (ec.getYearWuXing() + ec.getMonthWuXing()
               + ec.getDayWuXing() + ec.getTimeWuXing()):
        if wx in _WX:
            elements[_WX[wx]] += 1
    # 大运时间轴
    timeline = []
    try:
        yun = ec.getYun(1 if b.gender == "male" else 0)
        for da in yun.getDaYun()[1:9]:
            timeline.append({
                "from": str(da.getStartYear()), "to": str(da.getEndYear()),
                "label": "大运·" + da.getGanZhi(), "score": None,
            })
    except Exception:
        pass

    # ---- 旺衰多因子（藏干计权+通根+党势，W1 升级版）----
    from .. import wuxing as wx
    strength = wx.day_master_strength(pillars)
    es = wx.element_strength(pillars)
    wx_cn = {"木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"}
    elements = {wx_cn[k]: v for k, v in es["scored"].items()}   # 升级：藏干加权后的五行分
    judgement = {
        "旺衰": strength, "五行加权": es["scored"], "五行旺相休囚死": es["states"],
        "月令": es["month_wx"],
        "说明": strength["说明"],
    }
    # ---- Sprint 2.1: 流年/流月/当前大运 (raw.horoscope) ----
    from datetime import datetime as _dt
    now = _dt.utcnow()
    current_year = now.year
    current_month = now.month

    yearly = []
    try:
        # Sprint 2.1: 覆盖人生 ±60 年, 包含本命年前后大跨度
        # (1984 甲子 / 1998 戊寅 / 2014 甲午 golden case 验证需要)
        for y in range(current_year - 60, current_year + 30):
            s = Solar.fromYmdHms(y, 6, 15, 0, 0, 0)
            lun = s.getLunar()
            gz_year = lun.getYearInGanZhi()
            yearly.append({"year": y, "ganzhi": gz_year})
    except Exception:
        pass

    monthly: list[dict] = []
    try:
        for m in range(1, 13):
            s = Solar.fromYmdHms(current_year, m, 15, 0, 0, 0)
            lun = s.getLunar()
            gz_month = lun.getMonthInGanZhi()
            monthly.append({"month": m, "ganzhi": gz_month})
    except Exception:
        pass

    # 当前大运: 按当前年找 timeline 匹配
    current_dayun = None
    for d in timeline:
        try:
            if int(d["from"]) <= current_year <= int(d["to"]):
                current_dayun = d
                break
        except Exception:
            pass

    horoscope = {
        "current_year": current_year,
        "current_month": current_month,
        "yearly": yearly,
        "monthly": monthly,
        "current_dayun": current_dayun,
    }

    return ChartResult(
        method="bazi", school="east", engine="lunar-python",
        normalized={"elements": elements, "timeline": timeline},
        raw={
            "pillars": pillars,
            "day_master": ec.getDayGan(),
            "断": judgement,
            "horoscope": horoscope,
        },
    )


# ══════════════════════════════════════════════════════════════
# bazi_v2 依赖的辅助函数 (由 bazi_v2.py 通过 importlib 动态导入)
# ══════════════════════════════════════════════════════════════

from datetime import datetime as _dt
from typing import Any


def _solar_from_birth(b: Birth):
    """从 Birth 合约构造 lunar-python Solar 对象."""
    if b.calendar == "lunar":
        from lunar_python import Lunar
        lunar = Lunar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
        return lunar.getSolar()
    return Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)


def _pillar_detail(
    position: str,
    ganzhi: str,
    wuxing: str,
    hide_gan: str,
    shi_shen_gan: str,
    shi_shen_zhi: str,
    di_shi: str,
) -> dict:
    """Construct a pillar detail dict from lunar-python output."""
    return {
        "position": position,
        "ganzhi": ganzhi,
        "wuxing": wuxing,
        "hide_gan": hide_gan,
        "shi_shen_gan": shi_shen_gan,
        "shi_shen_zhi": shi_shen_zhi,
        "di_shi": di_shi,
    }


def _score_elements(
    pillars: dict,
    pillar_details: list[dict],
) -> tuple[dict, dict, dict]:
    """Score element weights from visible/hidden stems and branches.

    Returns (elements_visible, elements_hidden, elements_total).
    """
    wuxing_en_map = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}
    elements_visible: dict[str, float] = {v: 0.0 for v in wuxing_en_map.values()}
    elements_hidden: dict[str, float] = {v: 0.0 for v in wuxing_en_map.values()}

    for pd in pillar_details:
        # visible stem
        gan_wx = GAN_WUXING.get(pd["ganzhi"][0], "")
        if gan_wx in wuxing_en_map:
            elements_visible[wuxing_en_map[gan_wx]] += 1.0
        # visible branch
        zhi_wx = ZHI_WUXING.get(pd["ganzhi"][1], "")
        if zhi_wx in wuxing_en_map:
            elements_visible[wuxing_en_map[zhi_wx]] += 0.5
        # hidden stems (藏干)
        if pd.get("hide_gan"):
            for hg in pd["hide_gan"]:
                hg_wx = GAN_WUXING.get(hg, "")
                if hg_wx in wuxing_en_map:
                    elements_hidden[wuxing_en_map[hg_wx]] += 0.3

    elements_total = {
        k: round(elements_visible.get(k, 0) + elements_hidden.get(k, 0), 1)
        for k in wuxing_en_map.values()
    }
    return elements_visible, elements_hidden, elements_total


def _count_ten_gods(day_master: str, pillars: dict) -> dict:
    """Count ten-god types across all four pillars."""
    dm_wx = GAN_WUXING.get(day_master, "")
    wuxing_en_map = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}

    counts: dict[str, int] = {}
    for pos, ganzhi in pillars.items():
        if len(ganzhi) < 1:
            continue
        gan = ganzhi[0]
        gan_wx = GAN_WUXING.get(gan, "")
        if not gan_wx or not dm_wx:
            continue
        # Determine ten-god relation
        if gan_wx == dm_wx:
            label = "比劫"
        elif WO_SHENG.get(dm_wx) == gan_wx:
            label = "食伤"
        elif WO_KE.get(dm_wx) == gan_wx:
            label = "财星"
        elif KE_WO.get(dm_wx) == gan_wx:
            label = "官杀"
        elif SHENG_WO.get(dm_wx) == gan_wx:
            label = "印星"
        else:
            label = "未知"
        counts[label] = counts.get(label, 0) + 1
    return counts


def _compute_element_flow(elements: dict, pillars: dict) -> dict:
    """Compute element flow analysis (相生相克 directions)."""
    wx_order = ["wood", "fire", "earth", "metal", "water"]
    flow_lines: list[str] = []
    for i, wx in enumerate(wx_order):
        val = elements.get(wx, 0)
        next_val = elements.get(wx_order[(i + 1) % 5], 0)
        if val >= 2 and next_val >= 1:
            flow_lines.append(f"{wx}生{wx_order[(i+1)%5]}有力")
        if val >= 3:
            flow_lines.append(f"{wx}过旺需泄")
    return {
        "flow_directions": flow_lines,
        "balance_note": "五行流通以连续相生为佳，断流处为病。",
    }


def _today_year_ganzhi() -> tuple[int, str]:
    """Return (current_year, year_ganzhi)."""
    now = _dt.utcnow()
    try:
        s = Solar.fromYmdHms(now.year, 6, 15, 12, 0, 0)
        gz = s.getLunar().getYearInGanZhi()
        return now.year, gz
    except Exception:
        return now.year, ""


def _find_da_yun_for_year(da_yun_list: list, year: int):
    """Find the da_yun that covers the given year."""
    for dy in da_yun_list:
        try:
            if dy.getStartYear() <= year <= dy.getEndYear():
                return dy
        except Exception:
            continue
    return None


def _decade_evaluation(decade_ganzhi: str, day_master: str) -> dict:
    """Evaluate a decade pillar against the day master."""
    if not decade_ganzhi or len(decade_ganzhi) < 2:
        return {"score": 50, "note": "无法评估"}
    decade_gan = decade_ganzhi[0]
    dm_wx = GAN_WUXING.get(day_master, "")
    dg_wx = GAN_WUXING.get(decade_gan, "")
    if dm_wx and dg_wx:
        if WO_SHENG.get(dm_wx) == dg_wx:
            return {"score": 70, "note": "大运天干为日主食伤，利于发挥才华。"}
        if SHENG_WO.get(dm_wx) == dg_wx:
            return {"score": 80, "note": "大运天干为日主印星，利于学习与贵人。"}
        if KE_WO.get(dm_wx) == dg_wx:
            return {"score": 55, "note": "大运天干为日主官杀，有压力亦有动力。"}
        if WO_KE.get(dm_wx) == dg_wx:
            return {"score": 65, "note": "大运天干为日主财星，利于求财。"}
    return {"score": 60, "note": "大运与日主同五行或关系不显。"}


def _build_annual_interactions(pillars: dict, annual_ganzhi: str) -> dict:
    """Build annual interactions (流年与四柱的合冲刑害关系)."""
    if not annual_ganzhi or len(annual_ganzhi) < 2:
        return {"year": _dt.utcnow().year, "interactions": []}
    interactions: list[dict] = []
    annual_gan = annual_ganzhi[0]
    annual_zhi = annual_ganzhi[1]
    for pos, ganzhi in pillars.items():
        if len(ganzhi) < 2:
            continue
        pzhi = ganzhi[1]
        # Simplified check: 六冲 (opposite branches)
        chong_map = {
            "子": "午", "午": "子", "丑": "未", "未": "丑",
            "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
            "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
        }
        if chong_map.get(pzhi) == annual_zhi:
            interactions.append({"pillar": pos, "type": "冲", "note": f"{pzhi}冲{annual_zhi}"})
    return {"year": _dt.utcnow().year, "interactions": interactions}


def _build_life_stage(day_master: str, pillars: dict) -> dict:
    """Build a simple life-stage assessment."""
    return {
        "day_master": day_master,
        "stage_hint": "由日主在四柱位置及大运流年综合判定",
        "note": "此为基础参考，详细断命需结合大运流年。",
    }


def _compute_strength_score(
    day_master_gan: str,
    month_zhi: str,
    ten_god_counts: dict,
) -> tuple[float, dict]:
    """Compute day master strength score (0-100).

    Factors:
    - Month branch seasonality (月令) — heaviest weight (30)
    - Same-element count in ten gods (比劫) — medium weight (20)
    - Resource element count (印星) — medium weight (15)
    - Controlling/pressure count (官杀) — negative weight
    - Output count (食伤) — minor drain
    - Sheng-ke cycle: month branch support or suppression
    """
    dm_wx = GAN_WUXING.get(day_master_gan, "")
    month_wx = ZHI_WUXING.get(month_zhi, "")

    basis: dict = {"month_branch": month_zhi, "month_wx": month_wx}

    # 1. Month branch seasonality (月令) — base score
    season_strength = 30.0  # default moderate
    if month_wx == dm_wx:
        season_strength = 45.0  # 同五行 = 当令
    elif WO_SHENG.get(dm_wx) == month_wx:
        season_strength = 20.0  # 我生月 = 泄气
    elif SHENG_WO.get(dm_wx) == month_wx:
        season_strength = 40.0  # 生我月 = 相
    elif KE_WO.get(dm_wx) == month_wx:
        season_strength = 15.0  # 克我月 = 囚
    elif WO_KE.get(dm_wx) == month_wx:
        season_strength = 25.0  # 我克月 = 休

    basis["season_strength"] = season_strength

    # 2. Same-element (比劫) count
    bijie = ten_god_counts.get("比劫", 0)
    bijie_score = min(25, bijie * 12)
    basis["bijie_score"] = bijie_score

    # 3. Resource (印星) support
    yinxing = ten_god_counts.get("印星", 0)
    yin_score = min(20, yinxing * 10)
    basis["yin_score"] = yin_score

    # 4. Penalty from controlling (官杀)
    guansha = ten_god_counts.get("官杀", 0)
    guansha_penalty = min(20, guansha * 8)
    basis["guansha_penalty"] = guansha_penalty

    # 5. Drain from output (食伤)
    shishang = ten_god_counts.get("食伤", 0)
    shishang_drain = min(15, shishang * 5)
    basis["shishang_drain"] = shishang_drain

    # 6. Wealth (财星) minor drain
    caixing = ten_god_counts.get("财星", 0)
    caixing_drain = min(10, caixing * 4)
    basis["caixing_drain"] = caixing_drain

    total_score = (
        season_strength
        + bijie_score
        + yin_score
        - guansha_penalty
        - shishang_drain
        - caixing_drain
    )
    final = max(5, min(95, total_score))

    basis["total_score"] = round(final, 1)
    basis["month_strength"] = season_strength
    basis["detail"] = (
        f"月令{month_zhi}({month_wx}){season_strength}, "
        f"比劫{bijie_score}, 印星{yin_score}, "
        f"官杀-{guansha_penalty}, 食伤-{shishang_drain}, 财星-{caixing_drain}"
    )

    return final, basis
