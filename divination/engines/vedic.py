"""吠陀占星（Jyotish）深化版 —— Lahiri 恒星黄道 + 九曜(含罗睺计都) + 九分盘 + 庙旺落陷 + Vimshottari 大运。
标准：Lahiri ayanamsa；二十七宿；Navamsa(D9)；Vimshottari Dasha(120年九曜)。
已验证：摩羯入境合 Makar Sankranti；Dasha 总和120年；Navamsa 合古典元素规则；罗睺逆行≈19.3°/年。"""
from datetime import datetime, timedelta
from ..contracts import Birth, ChartResult
from .engines_western_shared import planet_tropical_longitudes

_RASHI = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
          "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
_NAK = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
        "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
# Vimshottari：九曜次序与年数（总120）
_DASHA = [("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
          ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)]
_DASHA_CN = {"Ketu": "计都", "Venus": "金星", "Sun": "太阳", "Moon": "月亮", "Mars": "火星",
             "Rahu": "罗睺", "Jupiter": "木星", "Saturn": "土星", "Mercury": "水星"}
# 庙旺(exalt sign idx)，落陷=+6，入庙(own signs)
_EXALT = {"太阳": 0, "月亮": 1, "火星": 9, "水星": 5, "木星": 3, "金星": 11, "土星": 6}
_OWN = {"太阳": [4], "月亮": [3], "火星": [0, 7], "水星": [2, 5],
        "木星": [8, 11], "金星": [1, 6], "土星": [9, 10]}


def lahiri_ayanamsa(tt_jd: float) -> float:
    T = (tt_jd - 2451545.0) / 36525.0
    return 23.85250 + 1.39638 * T


def _rahu_tropical(tt_jd: float) -> float:
    T = (tt_jd - 2451545.0) / 36525.0
    return (125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + T ** 3 / 467441) % 360


def _navamsa(lon: float) -> str:
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


def _vimshottari(moon_sid: float, birth_dt: datetime) -> dict:
    nak_idx = int(moon_sid // (360 / 27))
    pos_in_nak = moon_sid % (360 / 27)
    elapsed = pos_in_nak / (360 / 27)
    start_lord_i = nak_idx % 9
    # 起运余额
    bal = (1 - elapsed) * _DASHA[start_lord_i][1]
    seq = []
    cursor = birth_dt - timedelta(days=elapsed * _DASHA[start_lord_i][1] * 365.25)  # 本命大运起点
    today = datetime(2026, 6, 10)
    current = None
    for k in range(9):
        lord, yrs = _DASHA[(start_lord_i + k) % 9]
        end = cursor + timedelta(days=yrs * 365.25)
        item = {"主星": _DASHA_CN[lord], "lord": lord,
                "起": cursor.strftime("%Y-%m"), "止": end.strftime("%Y-%m"), "年数": yrs}
        seq.append(item)
        if cursor <= today < end:
            current = item
            # 当前大运的副周期(Antardasha)
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


def compute(b: Birth) -> ChartResult:
    trop, tt = planet_tropical_longitudes(b)
    ayan = lahiri_ayanamsa(tt)
    # 加罗睺计都
    rahu = (_rahu_tropical(tt) - ayan) % 360
    sid_extra = {"罗睺": rahu, "计都": (rahu + 180) % 360}

    planets = {}
    moon_sid = None
    for cn, lon in trop.items():
        sid = (lon - ayan) % 360
        if cn == "月亮":
            moon_sid = sid
        ri = int(sid // 30)
        nak_idx = int(sid // (360 / 27))
        pada = int((sid % (360 / 27)) // (360 / 27 / 4)) + 1
        planets[cn] = {"恒星黄经": round(float(sid), 2), "宫Rashi": _RASHI[ri],
                       "宿Nakshatra": _NAK[nak_idx], "Pada": pada,
                       "九分盘D9": _navamsa(sid), "庙旺落陷": _dignity(cn, ri)}
    for cn, sid in sid_extra.items():
        ri = int(sid // 30); nak_idx = int(sid // (360 / 27))
        planets[cn] = {"恒星黄经": round(float(sid), 2), "宫Rashi": _RASHI[ri],
                       "宿Nakshatra": _NAK[nak_idx],
                       "Pada": int((sid % (360 / 27)) // (360 / 27 / 4)) + 1,
                       "九分盘D9": _navamsa(sid), "庙旺落陷": "平(交点)"}

    from zoneinfo import ZoneInfo
    bdt = datetime(b.year, b.month, b.day, b.hour, b.minute)
    dasha = _vimshottari(moon_sid, bdt) if moon_sid is not None else {}

    return ChartResult(
        method="vedic", school="west", engine="skyfield+Lahiri(深化)",
        normalized={"elements": {}, "timeline": [
            {"from": d["起"], "to": d["止"], "label": "大运·" + d["主星"], "score": None}
            for d in dasha.get("大运序列Mahadasha", [])]},
        raw={"ayanamsa": round(ayan, 3), "planets": planets, "Vimshottari大运": dasha},
    )
