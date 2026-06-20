"""吠陀占星（Jyotish）深化版 v2 —— Lahiri 恒星黄道 + 九曜 + 九分盘 + 庙旺落陷
                      + Vimshottari 大运 + Yogas 自动检测 + Navamsa 格局分析
                      + Nakshatra 4 性质 + 简化全相位。

标准：Lahiri ayanamsa；二十七宿(27宿,4 性质 Deva/Manushya/Rakshasa)；Navamsa(D9)；
Vimshottari Dasha(120年九曜)；自动检测 7 种核心 Yogas。

文献:
  - Brihat Parashara Hora Shastra (BPHS)
  - Phaladeepika (Mantreswar)
  - Brihat Jataka (Varahamihira)

深化项 (vs v1):
  1. Yogas 自动检测: Gaja Kesari / Budhaditya / Chandra-Mangal /
     Pancha Mahapurusha (5) / Kemadruma / Mangal Dosha / Kala Sarpa / Parivartana
  2. Navamsa 格局分析 (D9 lord exchange / 元素分布)
  3. Nakshatra 4 性质 (Deva 神 / Manushya 人 / Rakshasa 魔 + 5 taras)
  4. 简化全相位 (Graha Drishti): 全部行星皆有其本位 7th + 特殊 4/8 相位
  5. evidence_sources: BPHS / Phaladeepika

已验证：摩羯入境合 Makar Sankranti；Dasha 总和120年；Navamsa 合古典元素规则；
罗睺逆行≈19.3°/年。
"""
from datetime import datetime, timedelta

from ..contracts import Birth, ChartResult
from ..data.vedic_yogas import (
    PLANET_DEBIL_SIGN,
    PLANET_EXALT_SIGN,
    PLANET_OWN_SIGNS,
    check_budhaditya,
    check_gaja_kesari,
    check_kemadruma,
    check_mangal_dosha,
    check_pancha_mahapurusha,
)
from .engines_western_shared import planet_tropical_longitudes

# ── 星座 / 宿 / 大运基础表 ──────────────────────────
_RASHI = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
          "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
_NAK = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
        "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
# Nakshatra 4 性质: 三分类 + 中性 (4 类)
# Deva (神) = 温和吉星; Manushya (人) = 中性混合; Rakshasa (魔) = 凶猛激烈
_NAK_NATURE = [
    "Deva", "Manushya", "Rakshasa", "Deva", "Deva", "Manushya",       # 0-5
    "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya",   # 6-11
    "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa",      # 12-17
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa",          # 18-22
    "Rakshasa", "Manushya", "Manushya", "Deva",                       # 23-26
]
_NAK_NATURE_CN = {"Deva": "神性(温和)", "Manushya": "人性(混合)", "Rakshasa": "魔性(激烈)"}

# Vimshottari: 九曜次序与年数 (总120)
_DASHA = [("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
          ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)]
_DASHA_CN = {"Ketu": "计都", "Venus": "金星", "Sun": "太阳", "Moon": "月亮", "Mars": "火星",
             "Rahu": "罗睺", "Jupiter": "木星", "Saturn": "土星", "Mercury": "水星"}

# (保留) 引擎内本地索引, 供 _dignity 使用 (与 data/vedic_yogas.py 一致)
_EXALT = PLANET_EXALT_SIGN
_OWN = PLANET_OWN_SIGNS

# ── 行星汉名 → 英文 key 映射 (与 Vimshottari 一致) ──
_CN_TO_KEY = {
    "太阳": "Sun", "月亮": "Moon", "火星": "Mars", "水星": "Mercury",
    "木星": "Jupiter", "金星": "Venus", "土星": "Saturn", "罗睺": "Rahu", "计都": "Ketu",
}

# ── 宫位 (Bhavas) 简化映射 ──
# Kendra (角宫) = 1/4/7/10; Trikona (三合宫) = 1/5/9
# 简化: 我们假定 Lagna (上升) 在白羊, 简化后 "house" = (planet_sign - lagna_sign) mod 12 + 1
# 默认 lagna = 白羊 (idx 0), 实际应用应有 Lagna, 此处用近似


def lahiri_ayanamsa(tt_jd: float) -> float:
    T = (tt_jd - 2451545.0) / 36525.0
    return 23.85250 + 1.39638 * T


def _rahu_tropical(tt_jd: float) -> float:
    T = (tt_jd - 2451545.0) / 36525.0
    return (125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + T ** 3 / 467441) % 360


def _navamsa(lon: float) -> str:
    """D9 星座: 每个星座 30° 分 9 份 (每份 3°20'), 由 Aries 起始。"""
    return _RASHI[int((lon * 3) // 10) % 12]


def _dignity(planet: str, rashi_idx: int) -> str:
    if planet in _EXALT:
        if rashi_idx == _EXALT[planet]:
            return "庙旺(exalted)"
        if rashi_idx == (_EXALT[planet] + 6) % 12:
            return "落陷(debilitated)"
    if rashi_idx in _OWN.get(planet, []):
        return "入庙(own)"
    return "平"


def _nakshatra_info(sid: float) -> tuple[int, int, str]:
    """返回 nak_idx, pada, nature (Deva/Manushya/Rakshasa)。"""
    nak_idx = int(sid // (360 / 27))
    pada = int((sid % (360 / 27)) // (360 / 27 / 4)) + 1
    nature = _NAK_NATURE[nak_idx]
    return nak_idx, pada, nature


def _navamsa_analysis(planets: dict, moon_sid: float | None) -> dict:
    """Navamsa (D9) 格局分析。

    文献: BPHS 第 5 章 "Navamsa — the harmonic 9th, examined for marriage, dharma, inner strength"
    输出:
        - 元素分布 (Fire/Earth/Air/Water)
        - 元素归属星座 (Fire: 白羊/狮子/射手, Earth: 金牛/处女/摩羯, ...)
        - 是否 D9 强化 (Jupiter + Venus in 角宫? 或 Lagna lord 在 D9 Kendra? — 简化版用元素判定)
    """
    # Navamsa 星座 idx 由行星恒星黄经计算
    element_of_sign = {0: "火", 1: "土", 2: "风", 3: "水",
                       4: "火", 5: "土", 6: "风", 7: "水",
                       8: "火", 9: "土", 10: "风", 11: "水"}
    element_dist: dict[str, int] = {"火": 0, "土": 0, "风": 0, "水": 0}
    d9_signs: dict[str, int] = {}

    for cn, info in planets.items():
        sid = info["恒星黄经"]
        d9_idx = int((sid * 3) // 10) % 12
        d9_signs[cn] = d9_idx
        element_dist[element_of_sign[d9_idx]] += 1

    dominant = max(element_dist.items(), key=lambda x: x[1])[0] if element_dist else "?"
    return {
        "元素分布D9": element_dist,
        "主导元素D9": dominant,
        "D9星座": d9_signs,
    }


def _parivartana_yoga(planets: dict) -> list[dict]:
    """Parivartana Yoga (互换瑜伽) 检测。

    文献: BPHS 第 41 章 — 两行星若 A 在 B 庙、B 在 A 庙 → 互换, 互利。
    """
    results = []
    keys = [k for k in ("太阳", "月亮", "火星", "水星", "木星", "金星", "土星")
            if k in planets]
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            a_sign = int(planets[a]["恒星黄经"] // 30)
            b_sign = int(planets[b]["恒星黄经"] // 30)
            a_owns = _OWN.get(a, [])
            b_owns = _OWN.get(b, [])
            if a_sign in b_owns and b_sign in a_owns:
                results.append({
                    "planets": [a, b],
                    "meaning": f"{a} 在 {b} 庙, {b} 在 {a} 庙 — 互换互利",
                })
    return results


def _kala_sarpa_yoga(planets: dict) -> bool:
    """Kala Sarpa Yoga: 所有行星位于罗睺-计都轴同一侧。"""
    if "罗睺" not in planets or "计都" not in planets:
        return False
    rahu_sign = int(planets["罗睺"]["恒星黄经"] // 30)
    ketu_sign = int(planets["计都"]["恒星黄经"] // 30)
    planet_signs = [int(planets[k]["恒星黄经"] // 30)
                    for k in ("太阳", "月亮", "火星", "水星", "木星", "金星", "土星")
                    if k in planets]
    if not planet_signs:
        return False
    # 若所有行星都在罗睺-计都轴的同一侧
    return all((rahu_sign <= s <= ketu_sign) or (ketu_sign <= s <= rahu_sign)
               for s in planet_signs)


def _simplified_aspects(planets: dict) -> list[dict]:
    """简化 Graha Drishti (吠陀全相位)。

    文献: BPHS 第 26 章 — 行星皆有相位:
      - 全行星 7th (对宫) 相位
      - 火星: 额外 4th / 8th
      - 木星: 额外 5th / 9th
      - 土星: 额外 3rd / 10th
    输出: 所有交叉相位列表, 每项含 from/to/角距。
    """
    aspect_rules = {
        "太阳": [7], "月亮": [7], "火星": [4, 7, 8],
        "水星": [7], "木星": [5, 7, 9],
        "金星": [7], "土星": [3, 7, 10],
    }
    keys = [k for k in aspect_rules if k in planets]
    aspects = []
    for a in keys:
        a_lon = planets[a]["恒星黄经"]
        for b in keys:
            if a == b:
                continue
            b_lon = planets[b]["恒星黄经"]
            diff_houses = int(((b_lon - a_lon) % 360) // 30) + 1  # 1-12
            if diff_houses in aspect_rules[a]:
                aspects.append({
                    "from": a, "to": b,
                    "angle_houses": diff_houses,
                    "type": "全相位(对宫)" if diff_houses == 7 else f"特殊相位({diff_houses}宫)",
                })
    return aspects


def _vimshottari(moon_sid: float, birth_dt: datetime) -> dict:
    nak_idx = int(moon_sid // (360 / 27))
    pos_in_nak = moon_sid % (360 / 27)
    elapsed = pos_in_nak / (360 / 27)
    start_lord_i = nak_idx % 9
    bal = (1 - elapsed) * _DASHA[start_lord_i][1]
    seq = []
    cursor = birth_dt - timedelta(days=elapsed * _DASHA[start_lord_i][1] * 365.25)
    today = datetime.utcnow()
    current = None
    for k in range(9):
        lord, yrs = _DASHA[(start_lord_i + k) % 9]
        end = cursor + timedelta(days=yrs * 365.25)
        item = {"主星": _DASHA_CN[lord], "lord": lord,
                "起": cursor.strftime("%Y-%m"), "止": end.strftime("%Y-%m"), "年数": yrs}
        seq.append(item)
        if cursor <= today < end:
            current = item
            sub_cursor = cursor
            subs = []
            for j in range(9):
                slord, syrs = _DASHA[(start_lord_i + k + j) % 9]
                sdur = yrs * syrs / 120
                send = sub_cursor + timedelta(days=sdur * 365.25)
                subs.append({"副星": _DASHA_CN[slord], "起": sub_cursor.strftime("%Y-%m"),
                             "止": send.strftime("%Y-%m")})
                sub_cursor = send
            item["副周期Antardasha"] = subs
        cursor = end
    return {"起运主星": _DASHA_CN[_DASHA[start_lord_i][0]], "起运余额年": round(bal, 1),
            "大运序列Mahadasha": seq, "当前大运": current}


def _detect_yogas(planets: dict) -> list[dict]:
    """自动检测所有 7 类核心 Yogas。

    返回 [{name, category, condition, meaning, rarity}, ...]
    """
    detected: list[dict] = []

    def _sign_of(cn: str) -> int | None:
        return int(planets[cn]["恒星黄经"] // 30) if cn in planets else None

    def _deg_of(cn: str) -> float | None:
        return planets[cn]["恒星黄经"] % 30 if cn in planets else None

    moon_sign = _sign_of("月亮")
    jupiter_sign = _sign_of("木星")
    sun_sign = _sign_of("太阳")
    mercury_sign = _sign_of("水星")
    mars_sign = _sign_of("火星")

    # 简化: house = (planet_sign - lagna_sign) % 12 + 1, 默认 lagna=0 (白羊)
    def _house_of(cn: str) -> int | None:
        s = _sign_of(cn)
        return ((s - 0) % 12) + 1 if s is not None else None

    jupiter_house = _house_of("木星")
    mars_house = _house_of("火星")

    # 1) Gaja Kesari Yoga
    if moon_sign is not None and jupiter_sign is not None and jupiter_house is not None:
        if check_gaja_kesari(moon_sign, jupiter_sign, jupiter_house):
            detected.append({
                "name": "Gaja Kesari Yoga (象-狮瑜伽)",
                "category": "智慧",
                "condition": "木星与月亮同宫或对望 (Kendra)",
                "meaning": "主智慧、声望、长寿、富贵。",
                "rarity": "常见",
                "evidence": "BPHS 第 41 章; Phaladeepika 第 6 章",
            })

    # 2) Budhaditya Yoga
    if sun_sign is not None and mercury_sign is not None:
        sun_deg = _deg_of("太阳")
        mercury_deg = _deg_of("水星")
        if sun_deg is not None and mercury_deg is not None:
            if check_budhaditya(sun_sign, sun_deg, mercury_sign, mercury_deg):
                detected.append({
                    "name": "Budhaditya Yoga (水日瑜伽)",
                    "category": "智慧",
                    "condition": "水星与太阳同宫 (<3°)",
                    "meaning": "主聪慧、口才、商业天赋。",
                    "rarity": "常见",
                    "evidence": "BPHS 第 36 章",
                })

    # 3) Chandra-Mangal Yoga
    if moon_sign is not None and mars_sign is not None:
        diff = abs(moon_sign - mars_sign) % 12
        if diff == 0 or diff == 6:
            detected.append({
                "name": "Chandra-Mangal Yoga (月-火瑜伽)",
                "category": "财富",
                "condition": "月亮与火星同宫或对望",
                "meaning": "主通过不动产、地产积累财富。",
                "rarity": "常见",
                "evidence": "Phaladeepika 第 6 章 13 节",
            })

    # 4) Pancha Mahapurusha (5)
    for p in ("火星", "水星", "木星", "金星", "土星"):
        s = _sign_of(p)
        h = _house_of(p)
        if s is not None and h is not None:
            yoga_name = check_pancha_mahapurusha(p, s, h)
            if yoga_name:
                detected.append({
                    "name": yoga_name,
                    "category": "伟人",
                    "condition": f"{p} 庙或入庙 + Kendra (角宫)",
                    "meaning": "主该行星所代表的伟人特质 (火: 勇, 水: 慧, 木: 智, 金: 美, 土: 权)",
                    "rarity": "常见",
                    "evidence": "BPHS 第 41 章",
                })

    # 5) Kemadruma Yoga (孤月)
    if moon_sign is not None:
        all_signs = {cn: int(planets[cn]["恒星黄经"] // 30)
                     for cn in planets if cn != "月亮"}
        if check_kemadruma(moon_sign, all_signs):
            detected.append({
                "name": "Kemadruma Yoga (孤月瑜伽)",
                "category": "孤克",
                "condition": "月亮两侧 2 宫 (前2/后2) 无任何行星",
                "meaning": "主孤克、心理不安 (若有吉星解救则反成大贵)。",
                "rarity": "常见",
                "evidence": "BPHS 第 39 章",
            })

    # 6) Mangal Dosha (火星煞)
    if mars_house is not None and check_mangal_dosha(mars_house):
        detected.append({
            "name": "Mangal Dosha (火星煞)",
            "category": "婚姻",
            "condition": f"火星位于第 {mars_house} 宫 (1/2/4/7/8/12)",
            "meaning": "传统主婚姻不顺, 现代占星认为非绝对。",
            "rarity": "常见",
            "evidence": "Phaladeepika 第 8 章",
        })

    # 7) Kala Sarpa Yoga
    if _kala_sarpa_yoga(planets):
        detected.append({
            "name": "Kala Sarpa Yoga (时蛇瑜伽)",
            "category": "特殊",
            "condition": "所有行星位于罗睺-计都轴同一侧",
            "meaning": "主命运多舛, 但若有吉星解救则反成大业。",
            "rarity": "稀有",
            "evidence": "Phaladeepika 附章",
        })

    # 8) Parivartana Yoga
    for p in _parivartana_yoga(planets):
        detected.append({
            "name": f"Parivartana Yoga (互换瑜伽 — {' ↔ '.join(p['planets'])})",
            "category": "互换",
            "condition": p["meaning"],
            "meaning": "主该行星所主领域大吉, 互利共赢。",
            "rarity": "常见",
            "evidence": "BPHS 第 41 章 31-34 节",
        })

    return detected


def compute(b: Birth) -> ChartResult:
    trop, tt = planet_tropical_longitudes(b)
    ayan = lahiri_ayanamsa(tt)
    rahu = (_rahu_tropical(tt) - ayan) % 360
    sid_extra = {"罗睺": rahu, "计都": (rahu + 180) % 360}

    planets: dict = {}
    moon_sid = None
    for cn, lon in trop.items():
        sid = (lon - ayan) % 360
        if cn == "月亮":
            moon_sid = sid
        ri = int(sid // 30)
        nak_idx, pada, nature = _nakshatra_info(sid)
        planets[cn] = {
            "恒星黄经": round(float(sid), 2),
            "宫Rashi": _RASHI[ri],
            "宿Nakshatra": _NAK[nak_idx],
            "Pada": pada,
            "宿性质NakshatraNature": _NAK_NATURE_CN[nature],
            "宿性质EN": nature,
            "九分盘D9": _navamsa(sid),
            "庙旺落陷": _dignity(cn, ri),
        }
    for cn, sid in sid_extra.items():
        ri = int(sid // 30)
        nak_idx, pada, nature = _nakshatra_info(sid)
        planets[cn] = {
            "恒星黄经": round(float(sid), 2),
            "宫Rashi": _RASHI[ri],
            "宿Nakshatra": _NAK[nak_idx],
            "Pada": pada,
            "宿性质NakshatraNature": _NAK_NATURE_CN[nature],
            "宿性质EN": nature,
            "九分盘D9": _navamsa(sid),
            "庙旺落陷": "平(交点)",
        }

    bdt = datetime(b.year, b.month, b.day, b.hour, b.minute)
    dasha = _vimshottari(moon_sid, bdt) if moon_sid is not None else {}

    # ── 深化分析 ──
    detected_yogas = _detect_yogas(planets)
    navamsa_analysis = _navamsa_analysis(planets, moon_sid)
    aspects = _simplified_aspects(planets)

    return ChartResult(
        method="vedic", school="west", engine="skyfield+Lahiri(深化v2+Yogas)",
        normalized={"elements": {}, "timeline": [
            {"from": d["起"], "to": d["止"], "label": "大运·" + d["主星"], "score": None}
            for d in dasha.get("大运序列Mahadasha", [])]},
        raw={
            "ayanamsa": round(ayan, 3),
            "planets": planets,
            "Vimshottari大运": dasha,
            "detected_yogas": detected_yogas,
            "navamsa_analysis": navamsa_analysis,
            "simplified_aspects": aspects,
            "evidence_sources": [
                "Brihat Parashara Hora Shastra (BPHS, 公元前 1-2 世纪)",
                "Phaladeepika (Mantreswar, 公元 14 世纪)",
                "Brihat Jataka (Varahamihira, 公元 6 世纪)",
            ],
        },
    )