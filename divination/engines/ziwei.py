"""紫微斗数  ——  py-iztro (MIT) 包装层。

py-iztro 0.3.4 API (实探测):
  astro.by_solar('YYYY-M-D', time_index(0-12), '男'/'女', fix_leap=True, language='zh-CN') -> FunctionalAstrolabe
  astrolabe.palaces[i]   -> FunctionalPalace
  p.major_stars / p.minor_stars / p.adjective_stars -> list[FunctionalStar]
  p.changsheng12 / p.boshi12 / p.jiangqian12 -> 12 阶段 / 博士十二神 / 将前十二神
  p.decadal -> range=(from, to) + heavenly_stem + earthly_branch
  p.ages -> list[int] (10 段大限起年/止年)
  astrolabe.horoscope('YYYY-M-D', time_index) -> Horoscope
  h.decadal / h.yearly / h.monthly / h.daily / h.hourly -> HoroscopeItem
  h.{period}.mutagen -> list[str] (4 化: 禄权科忌)
  h.{period}.heavenly_stem + earthly_branch -> 大限/流年 干支

v1 补全:
- 大限/流年/流月/流日/流时 的干支 + 四化
- 本命宫 12 长生 / 博士十二神 / 将前十二神
- rule_version + calculation_basis.input_source / limits
- 包装层 catch: 任何 iztro 不可用或抛错都 fallback 到结构化 MVP 并打 fallback 标记
"""
from datetime import date

from ..contracts import Birth, ChartResult

_PALACE_NAME = {
    "soulPalace": "命宫",
    "siblingsPalace": "兄弟宫",
    "spousePalace": "夫妻宫",
    "childrenPalace": "子女宫",
    "wealthPalace": "财帛宫",
    "healthPalace": "疾厄宫",
    "surfacePalace": "迁移宫",
    "friendsPalace": "交友宫",
    "careerPalace": "官禄宫",
    "propertyPalace": "田宅宫",
    "spiritPalace": "福德宫",
    "parentsPalace": "父母宫",
}

_BRANCH_NAME = {
    "ziEarthly": "子",
    "chouEarthly": "丑",
    "yinEarthly": "寅",
    "maoEarthly": "卯",
    "chenEarthly": "辰",
    "siEarthly": "巳",
    "wuEarthly": "午",
    "weiEarthly": "未",
    "shenEarthly": "申",
    "youEarthly": "酉",
    "xuEarthly": "戌",
    "haiEarthly": "亥",
}

_STEM_NAME = {
    "jiaHeavenly": "甲",
    "yiHeavenly": "乙",
    "bingHeavenly": "丙",
    "dingHeavenly": "丁",
    "wuHeavenly": "戊",
    "jiHeavenly": "己",
    "gengHeavenly": "庚",
    "xinHeavenly": "辛",
    "renHeavenly": "壬",
    "guiHeavenly": "癸",
}

_STAR_NAME = {
    "ziweiMaj": "紫微",
    "tianjiMaj": "天机",
    "taiyangMaj": "太阳",
    "wuquMaj": "武曲",
    "tiantongMaj": "天同",
    "lianzhenMaj": "廉贞",
    "tianfuMaj": "天府",
    "taiyinMaj": "太阴",
    "tanlangMaj": "贪狼",
    "jumenMaj": "巨门",
    "tianxiangMaj": "天相",
    "tianliangMaj": "天梁",
    "qishaMaj": "七杀",
    "pojunMaj": "破军",
    "zuofuMin": "左辅",
    "youbiMin": "右弼",
    "wenchangMin": "文昌",
    "wenquMin": "文曲",
    "tiankuiMin": "天魁",
    "tianyueMin": "天钺",
    "huoxingMin": "火星",
    "lingxingMin": "铃星",
    "qingyangMin": "擎羊",
    "tuoluoMin": "陀罗",
    "dikongMin": "地空",
    "dijieMin": "地劫",
}

# Mutagen 中英对照 (iztro 0.3.4 用的是 internal key)
_STAR_NAME.update({
    "tianchu": "天厨",
    "tianyue": "天钺",
    "feilian": "飞廉",
    "tianxi": "天喜",
    "xianchi": "咸池",
    "santai": "三台",
    "tiangui": "天贵",
    "tianshou": "天寿",
    "tiande": "天德",
    "tianyao": "天姚",
    "fengge": "凤阁",
    "guasu": "寡宿",
    "fenggao": "封诰",
    "tianfuAdj": "天福",
    "posui": "破碎",
    "lucunMin": "禄存",
    "tianmaMin": "天马",
    "hongluan": "红鸾",
    "jieshen": "解神",
    "longchi": "龙池",
    "taifu": "台辅",
    "enguang": "恩光",
    "tianxing": "天刑",
    "tianku": "天哭",
    "tianxu": "天虚",
    "bazuo": "八座",
    "tianwu": "天巫",
    "tianguan": "天官",
})

_MUTAGEN_NAME = {
    "ziweiMaj": "紫微化",
    "tianfuMaj": "天府化",
    "sunMaj": "太阳化",
    "moonMaj": "太阴化",
    "chenMaj": "天机化",
    "tiantongMaj": "天同化",
    "lianzhenMaj": "廉贞化",
    "tianjiMaj": "天机化",
    "wenchangMin": "文昌化",
    "wenquMin": "文曲化",
    "wuqieMaj": "武曲化",
    "tianliangMaj": "天梁化",
    "pojunMaj": "破军化",
    "jumenMaj": "巨门化",
    "tanlangMaj": "贪狼化",
    "tianxiMaj": "天相化",
    "tianyaoMaj": "天姚化",
    "huagaiMaj": "华盖化",
    "tianxingMaj": "天刑化",
    "tianshiMaj": "天施主",
    "tiancaiMaj": "天财主",
    "tianchuMin": "天钺化",
    "tianyueMin": "天魁化",
    "tiankuiMaj": "天魁化",
    "tianyueMaj2": "天月化",
    "wenchangMaj2": "文昌化",
    "wuquMaj": "武曲化",
    "youyuanMaj": "右弼化",
    "zuofuMaj": "左辅化",
}

# Star 名称映射
_MUTAGEN_NAME.update({
    "ziweiMaj": "紫微化",
    "tianfuMaj": "天府化",
    "taiyangMaj": "太阳化",
    "sunMaj": "太阳化",
    "taiyinMaj": "太阴化",
    "moonMaj": "太阴化",
    "tianjiMaj": "天机化",
    "tiantongMaj": "天同化",
    "lianzhenMaj": "廉贞化",
    "wuquMaj": "武曲化",
    "tianliangMaj": "天梁化",
    "pojunMaj": "破军化",
    "jumenMaj": "巨门化",
    "tanlangMaj": "贪狼化",
    "tianxiangMaj": "天相化",
    "wenchangMin": "文昌化",
    "wenquMin": "文曲化",
    "zuofuMin": "左辅化",
    "youbiMin": "右弼化",
})

def _star_name(s) -> str:
    if s is None:
        return ""
    if isinstance(s, str):
        return _STAR_NAME.get(_base_star_key(s), s)
    if isinstance(s, dict):
        name = s.get("name", str(s))
        return _STAR_NAME.get(_base_star_key(name), name)
    # FunctionalStar: name 字段 + type 字段
    nm = getattr(s, "name", "") or ""
    typ = getattr(s, "type", "") or ""
    base = _base_star_key(nm)
    display = _STAR_NAME.get(base, nm)
    return display if not typ else display


def _mutagen_label(key: str) -> str:
    if not key:
        return ""
    return _MUTAGEN_NAME.get(key, key)


def _normalize_key(value: str, table: dict[str, str]) -> str:
    if not value:
        return ""
    return table.get(value, value)


def _safe_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    year = getattr(value, "year", None)
    month = getattr(value, "month", None)
    day = getattr(value, "day", None)
    if year and month and day:
        leap = " 闰月" if getattr(value, "is_leap_month", False) else ""
        return f"{year}-{month}-{day}{leap}"
    if isinstance(value, dict):
        if {"year", "month", "day"}.issubset(value):
            leap = " 闰月" if value.get("is_leap_month") else ""
            return f"{value.get('year')}-{value.get('month')}-{value.get('day')}{leap}"
        if "name" in value:
            return _safe_text(value.get("name"))
    return str(value)


def _safe_bool_attr(obj, attr: str) -> bool:
    value = getattr(obj, attr, False)
    if callable(value):
        try:
            return bool(value())
        except Exception:
            return False
    return bool(value)


def _base_star_key(name: str) -> str:
    return (name or "").split("(", 1)[0]


def _horoscope_period(h_item, period_zh: str) -> dict:
    """从 iztro HoroscopeItem 提取干支 + 四化 + 起年。"""
    if h_item is None:
        return {}
    mutagen_raw = getattr(h_item, "mutagen", None) or []
    mutagen = [_mutagen_label(m) for m in mutagen_raw if m]
    stem = _normalize_key(h_item.heavenly_stem or "", _STEM_NAME)
    branch = _normalize_key(h_item.earthly_branch or "", _BRANCH_NAME)
    return {
        "scope": period_zh,
        "ganzhi": stem + branch,
        "heavenly_stem": stem,
        "earthly_branch": branch,
        "mutagen": mutagen,
        "mutagen_raw": list(mutagen_raw),
    }


def _hour_to_index(hour: int) -> int:
    """0-23 时 -> py-iztro 时辰索引(0=早子 0-1, 12=晚子 23-24)。"""
    if hour == 0 or hour == 23:
        return 12
    return (hour + 1) // 2


def _star_with_mutagen(star) -> dict:
    """把 FunctionalStar 展成 name + mutagen (4 化) 字符串。"""
    nm = _star_name(star)
    if not nm:
        return {}
    mut = getattr(star, "mutagen", None)
    if mut:
        return {"name": nm, "mutagen": _mutagen_label(mut)}
    return {"name": nm}


def compute(b: Birth) -> ChartResult:
    fallback = False
    fallback_reason = ""
    raw_chart = None
    try:
        from iztro_py import astro
        gender = "男" if b.gender == "male" else "女"
        time_index = _hour_to_index(b.hour)
        solar_date = f"{b.year}-{b.month}-{b.day}"
        raw_chart = astro.by_solar(solar_date, time_index, gender, fix_leap=True, language="zh-CN")
    except Exception as e:
        fallback = True
        fallback_reason = f"{type(e).__name__}: {e}"
        raw_chart = None

    palaces = []
    changsheng12_map = {}
    boshi12_map = {}
    jiangqian12_map = {}
    if raw_chart is not None:
        try:
            for p in raw_chart.palaces:
                major = [_star_with_mutagen(s) for s in (p.major_stars or [])]
                minor = [_star_with_mutagen(s) for s in (p.minor_stars or [])]
                adjective = [_star_name(s) for s in (p.adjective_stars or [])]
                palace_name = _normalize_key(p.name, _PALACE_NAME)
                earthly_branch = _normalize_key(getattr(p, "earthly_branch", "") or "", _BRANCH_NAME)
                heavenly_stem = _normalize_key(getattr(p, "heavenly_stem", "") or "", _STEM_NAME)
                palaces.append({
                    "name": palace_name,
                    "raw_name": p.name,
                    "earthly_branch": earthly_branch,
                    "heavenly_stem": heavenly_stem,
                    "is_body_palace": _safe_bool_attr(p, "is_body_palace"),
                    "is_original_palace": _safe_bool_attr(p, "is_original_palace"),
                    "is_empty": _safe_bool_attr(p, "is_empty"),
                    "ages": list(getattr(p, "ages", []) or []),
                    "decadal_range": list(getattr(getattr(p, "decadal", None), "range", []) or []),
                    "major_stars": major,
                    "minor_stars": minor,
                    "adjective_stars": adjective,
                    "changsheng12": getattr(p, "changsheng12", "") or "",
                    "boshi12": getattr(p, "boshi12", "") or "",
                    "jiangqian12": getattr(p, "jiangqian12", "") or "",
                })
                if palace_name:
                    if getattr(p, "changsheng12", ""):
                        changsheng12_map[palace_name] = p.changsheng12
                    if getattr(p, "boshi12", ""):
                        boshi12_map[palace_name] = p.boshi12
                    if getattr(p, "jiangqian12", ""):
                        jiangqian12_map[palace_name] = p.jiangqian12
        except Exception as e:
            fallback_reason = fallback_reason or f"palaces: {e}"

    # ---- 限运:今天的大限/流年/流月/流日/流时 ----
    horoscope = {}
    if raw_chart is not None:
        try:
            today = date.today()
            today_str = f"{today.year}-{today.month}-{today.day}"
            h = raw_chart.horoscope(today_str, time_index)
            horoscope = {
                "solar_date": today_str,
                "nominal_age": getattr(h, "nominal_age", None),
                "decadal": _horoscope_period(getattr(h, "decadal", None), "大限"),
                "yearly": _horoscope_period(getattr(h, "yearly", None), "流年"),
                "monthly": _horoscope_period(getattr(h, "monthly", None), "流月"),
                "daily": _horoscope_period(getattr(h, "daily", None), "流日"),
                "hourly": _horoscope_period(getattr(h, "hourly", None), "流时"),
            }
        except Exception as e:
            fallback_reason = fallback_reason or f"horoscope: {e}"

    raw = {
        "mode": getattr(b, "mode", None) or "natal",
        "subject": getattr(b, "subject", None) or "self_life",
        "engine": "py-iztro" if not fallback else "fallback",
        "rule_version": "v1",
        "fallback": fallback,
        "fallback_reason": fallback_reason,
        "calculation_basis": {
            "method": "ziwei",
            "mode": getattr(b, "mode", None) or "natal",
            "subject": getattr(b, "subject", None) or "self_life",
            "engine": "py-iztro astro.by_solar + horoscope (MIT)",
            "input": {
                "solar_date": f"{b.year}-{b.month}-{b.day}",
                "time_index": _hour_to_index(b.hour),
                "gender": "男" if b.gender == "male" else "女",
            },
            "rule_version": "v1",
            "input_source": "birth (year/month/day/hour/minute, gender, optional calendar)",
            "limits": [
                "用 py-iztro 0.3.4 (MIT) 排盘,主辅星/杂曜/四化/限运 来自库算法",
                "不输出神煞断事,仅列盘面与四化",
                "12 长生 / 博士十二神 / 将前十二神 来自 py-iztro Palace.changsheng12/boshi12/jiangqian12",
                "fallback 触发时仅返回空 palaces,前端必须展示 fallback 标签,绝不伪装专业盘",
            ],
        },
        "palaces": palaces,
        "changsheng12_map": changsheng12_map,
        "boshi12_map": boshi12_map,
        "jiangqian12_map": jiangqian12_map,
        "horoscope": horoscope,
        "soul": _star_name(getattr(raw_chart, "soul", "") if raw_chart else ""),
        "body": _star_name(getattr(raw_chart, "body", "") if raw_chart else ""),
        "chinese_date": _safe_text(getattr(raw_chart, "chinese_date", "") if raw_chart else ""),
        "lunar_date": _safe_text(getattr(raw_chart, "raw_lunar_date", "") if raw_chart else ""),
        "zodiac": (getattr(raw_chart, "zodiac", "") if raw_chart else "") or "",
        "five_elements_class": (getattr(raw_chart, "five_elements_class", "") if raw_chart else "") or "",
    }

    # ---- 大限时间轴 ----
    timeline = []
    if palaces:
        ming = next((p for p in palaces if p.get("name") == "命宫"), None)
        if ming:
            for a in ming.get("ages", []):
                timeline.append({
                    "from": str(a),
                    "to": "",
                    "label": "大限起年",
                    "score": None,
                })

    # ---- 五行归一 ----
    elements = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
    try:
        ming = next((p for p in palaces if p.get("name") == "命宫"), None)
        if ming:
            gan = ming.get("heavenly_stem", "")
            _WX = {"甲": "wood", "乙": "wood", "丙": "fire", "丁": "fire",
                   "戊": "earth", "己": "earth", "庚": "metal", "辛": "metal",
                   "壬": "water", "癸": "water"}
            if gan in _WX:
                elements[_WX[gan]] = 2
    except Exception:
        pass

    return ChartResult(
        method="ziwei", school="east", engine="py-iztro" if not fallback else "fallback",
        normalized={"elements": elements, "timeline": timeline},
        raw=raw,
    )
