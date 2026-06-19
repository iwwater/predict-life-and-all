"""Zi Wei Dou Shu charting via the iztro Python ports."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from typing import Any, Callable

from ..contracts import Birth, ChartResult

ENGINE_NAME = "py-iztro"
RULE_VERSION = "v1"


def _load_by_solar() -> Callable[[str, int, str], Any]:
    try:
        from py_iztro import Astro  # type: ignore

        astro = Astro()
        return lambda solar_date, time_index, gender: astro.by_solar(
            solar_date, time_index, gender, True, "zh-CN"
        )
    except ModuleNotFoundError:
        import iztro_py  # type: ignore

        return lambda solar_date, time_index, gender: iztro_py.by_solar(
            solar_date, time_index, gender, True, "zh-CN"
        )


_by_solar = _load_by_solar()


def _time_index(hour: int) -> int:
    """iztro uses 0 for early Zi, 1-11 for Chou-Hai, and 12 for late Zi."""
    if hour == 23:
        return 12
    return max(0, min(11, (hour + 1) // 2))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _extract_year_gan(chart, birth: Birth) -> str | None:
    """从 py_iztro chart.chinese_date 提取出生年干 (甲/乙/.../癸).

    chinese_date.yearly 形如 [("甲子", 1984), ...] 或类似结构, 取干支字符串首字符.
    若 py_iztro 接口不暴露 chinese_date, 退化为用 lunar-python 直接计算年干.
    """
    cd = getattr(chart, "chinese_date", None)
    yearly = getattr(cd, "yearly", None) if cd else None
    if yearly:
        first = yearly[0] if isinstance(yearly, (list, tuple)) and yearly else None
        if first is not None:
            # 多种可能结构: ("甲子", 1984) / [年, 干支] / 干支字符串本身
            ganzhi = None
            if isinstance(first, (list, tuple)):
                for item in first:
                    s = _text(item)
                    if s and any(g in s for g in "甲乙丙丁戊己庚辛壬癸"):
                        ganzhi = s
                        break
            else:
                ganzhi = _text(first)
            if ganzhi:
                for ch in ganzhi:
                    if ch in "甲乙丙丁戊己庚辛壬癸":
                        return ch
    # Fallback: 用 lunar-python 直接从 birth.year 计算年干 (按立春年界近似)
    ganzhi_cycle = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    # 公历年 1984=甲子, 4年一循环: 1984%10=4 → 0
    return ganzhi_cycle[(birth.year - 4) % 10]


def _star_names(stars: Any) -> list[str]:
    return [_text(getattr(star, "name", star)) for star in (stars or [])]


def _model_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return getattr(value, "__dict__", {}) or {}


def _item_ganzhi(item: dict[str, Any]) -> str:
    stem = item.get("heavenly_stem") or item.get("stem") or ""
    branch = item.get("earthly_branch") or item.get("branch") or ""
    return _text(item.get("ganzhi") or f"{stem}{branch}")


def _horoscope(chart: Any, birth: Birth, time_index: int) -> dict[str, Any]:
    query_date = f"{date.today().year}-{birth.month}-{birth.day}"
    try:
        raw = _model_dict(chart.horoscope(query_date, time_index))
    except Exception:
        raw = {}

    result: dict[str, Any] = {}
    for scope in ("decadal", "yearly", "monthly", "daily", "hourly"):
        item = _model_dict(raw.get(scope))
        mutagen = list(item.get("mutagen") or item.get("mutagens") or [])
        result[scope] = {
            "name": _text(item.get("name") or scope),
            "index": item.get("index"),
            "ganzhi": _item_ganzhi(item),
            "heavenly_stem": _text(item.get("heavenly_stem")),
            "earthly_branch": _text(item.get("earthly_branch")),
            "palace_names": item.get("palace_names") or [],
            "mutagen": [_text(x) for x in mutagen[:4]],
        }

    return result


def _palaces(chart: Any) -> list[dict[str, Any]]:
    palaces: list[dict[str, Any]] = []
    for palace in getattr(chart, "palaces", []) or []:
        palaces.append(
            {
                "name": _text(getattr(palace, "name", "")),
                "index": getattr(palace, "index", None),
                "is_body": bool(getattr(palace, "is_body_palace", False)),
                "is_body_palace": bool(getattr(palace, "is_body_palace", False)),
                "is_original_palace": bool(getattr(palace, "is_original_palace", False)),
                "heavenly_stem": _text(getattr(palace, "heavenly_stem", "")),
                "earthly_branch": _text(getattr(palace, "earthly_branch", "")),
                "major_stars": _star_names(getattr(palace, "major_stars", [])),
                "minor_stars": _star_names(getattr(palace, "minor_stars", [])),
                "adjective_stars": _star_names(getattr(palace, "adjective_stars", [])),
                "changsheng12": _text(getattr(palace, "changsheng12", "")),
                "boshi12": _text(getattr(palace, "boshi12", "")),
                "jiangqian12": _text(getattr(palace, "jiangqian12", "")),
                "suiqian12": _text(getattr(palace, "suiqian12", "")),
            }
        )
    return palaces


def _palace_map(palaces: list[dict[str, Any]], key: str) -> dict[str, str]:
    return {p["name"]: p[key] for p in palaces if p.get("name") and p.get(key)}


def _extract_four_transformations(horoscope: dict[str, Any]) -> dict[str, list[str]]:
    """提取 5 个 scope (decadal/yearly/monthly/daily/hourly) 的 4 化 (禄/权/科/忌)。

    用于 Phase 3 normalizer 出 current_cycle 维 signal。
    """
    out: dict[str, list[str]] = {}
    for scope in ("decadal", "yearly", "monthly", "daily", "hourly"):
        item = horoscope.get(scope) or {}
        mutagens = item.get("mutagen") or item.get("mutagens") or []
        out[scope] = list(mutagens) if isinstance(mutagens, list) else []
    return out


def _enrich_four_transformations(sihua_raw: dict[str, list[str]], year_gan: str | None = None) -> dict[str, Any]:
    """丰富四化数据：含化星、含义、吉凶。

    文献依据: 顾祥弘《飞星紫微斗数全书》, 陈世兴《紫微斗数全书》四化篇。

    Args:
        sihua_raw: {scope: [mutagen_list]} 来自 _extract_four_transformations
        year_gan: 出生年干 (可选, 用于本命四化判定)

    Returns:
        {
            "natal": {禄/权/科/忌: {star, meaning, category}},  # 本命四化
            "decadal": {scope: enriched...},
            "yearly": ...,
            "interpretation": 综合解读文本,
            "evidence_sources": ["飞星紫微斗数全书", "紫微斗数全书"]
        }
    """
    from ..data.ziwei_sihua import NATAL_SIHUA, SIHUA_MEANINGS, get_sihua_meaning

    result: dict[str, Any] = {
        "natal": {},
        "current_decadal": {},
        "current_yearly": {},
        "interpretation": "",
        "evidence_sources": ["《飞星紫微斗数全书》(顾祥弘)", "《紫微斗数全书》四化篇"],
    }

    # 本命四化（基于生年天干）
    if year_gan and year_gan in NATAL_SIHUA:
        natal_sihua = NATAL_SIHUA[year_gan]
        for hua_type, star in natal_sihua.items():
            meaning = get_sihua_meaning(f"化{hua_type}", star)
            result["natal"][hua_type] = {
                "star": star,
                "category": SIHUA_MEANINGS.get(f"化{hua_type}", {}).get("category", ""),
                "meaning": meaning,
            }

    # 大限 / 流年 四化（原始 + 含义）
    # 支持多种格式: "贪狼化禄" / "化禄贪狼" / "贪狼 化禄" 等
    KNOWN_STARS = ("廉贞", "破军", "武曲", "太阳", "天机", "天梁",
                   "紫微", "太阴", "天同", "文昌", "巨门", "贪狼",
                   "右弼", "文曲", "左辅")

    def parse_mutagen(m: str) -> tuple[str, str] | None:
        """解析单条四化, 返回 (hua_type, star)。"""
        m = str(m).strip()
        for hua_type in ["禄", "权", "科", "忌"]:
            for star in KNOWN_STARS:
                # 匹配 "贪狼化禄" 或 "化禄贪狼" 等
                patterns = [
                    f"{star}化{hua_type}",
                    f"化{hua_type}{star}",
                    f"{star} 化{hua_type}",
                    f"化{hua_type} {star}",
                    f"{star}{hua_type}",
                ]
                if any(p in m for p in patterns) or (star in m and hua_type in m and len(m) <= 8):
                    return (hua_type, star)
        return None

    for scope_name, mutagens in sihua_raw.items():
        enriched_scope: dict[str, Any] = {}
        for m in (mutagens or []):
            parsed = parse_mutagen(m)
            if parsed:
                hua_type, star = parsed
                enriched_scope[f"化{hua_type}"] = {
                    "star": star,
                    "meaning": get_sihua_meaning(f"化{hua_type}", star),
                }
        if scope_name == "decadal":
            result["current_decadal"] = enriched_scope
        elif scope_name == "yearly":
            result["current_yearly"] = enriched_scope

    # 综合解读
    parts = []
    if result["natal"]:
        natal_str = " · ".join(
            f"{t}{info['star']}" for t, info in result["natal"].items()
        )
        parts.append(f"本命四化: {natal_str}")
    if result["current_decadal"]:
        dec_str = " · ".join(
            f"{t}{info['star']}" for t, info in result["current_decadal"].items()
        )
        parts.append(f"当前大限: {dec_str}")
    if result["current_yearly"]:
        yr_str = " · ".join(
            f"{t}{info['star']}" for t, info in result["current_yearly"].items()
        )
        parts.append(f"本年流年: {yr_str}")
    result["interpretation"] = " | ".join(parts) if parts else "暂无四化数据"

    return result


def _fallback_chart(b: Birth, reason: str) -> ChartResult:
    """Return a stable structural chart when the native iztro engine is unsafe."""
    time_index = _time_index(b.hour)
    solar_date = f"{b.year}-{b.month}-{b.day}"
    palace_names = [
        "life", "siblings", "spouse", "children", "wealth", "health",
        "travel", "friends", "career", "property", "fortune", "parents",
    ]
    palaces = [
        {
            "name": name,
            "index": i,
            "is_body": False,
            "is_body_palace": False,
            "is_original_palace": i == 0,
            "heavenly_stem": "",
            "earthly_branch": "",
            "major_stars": [],
            "minor_stars": [],
            "adjective_stars": [],
            "changsheng12": "",
            "boshi12": "",
            "jiangqian12": "",
            "suiqian12": "",
        }
        for i, name in enumerate(palace_names)
    ]
    horoscope = {
        scope: {
            "name": scope,
            "index": None,
            "ganzhi": "fallback",
            "heavenly_stem": "",
            "earthly_branch": "",
            "palace_names": [],
            "mutagen": ["", "", "", ""],
        }
        for scope in ("decadal", "yearly", "monthly", "daily", "hourly")
    }
    raw = {
        "rule_version": RULE_VERSION,
        "engine": f"{ENGINE_NAME}-fallback",
        "fallback": True,
        "fallback_reason": reason,
        "calculation_basis": {
            "method": "ziwei",
            "mode": "natal",
            "rule_version": RULE_VERSION,
            "input_source": "safe structural fallback; native py-iztro was unavailable or unstable",
            "solar_date": solar_date,
            "time_index": time_index,
            "gender": b.gender,
            "limits": [
                "This fallback preserves the response shape but does not contain a full Zi Wei astrolabe.",
                "Use it only to keep the app stable when the native iztro backend is unavailable.",
            ],
        },
        "soul": "",
        "body": "",
        "five_elements": "fallback",
        "five_elements_class": "fallback",
        "palaces": palaces,
        "horoscope": horoscope,
        "changsheng12_map": {},
        "boshi12_map": {},
        "jiangqian12_map": {},
    }
    return ChartResult(
        method="ziwei",
        school="east",
        engine=f"{ENGINE_NAME}-fallback",
        normalized={"elements": {}, "timeline": []},
        raw=raw,
    )


def _compute_in_subprocess(b: Birth) -> ChartResult:
    env = os.environ.copy()
    env["MYSTIC_ZIWEI_CHILD"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["MYSTIC_ZIWEI_BIRTH"] = json.dumps(b.__dict__)
    code = (
        "import json, os;"
        "from divination.contracts import Birth;"
        "from divination.engines.ziwei import _compute_native;"
        # 过滤出 Birth.__init__ 接受的字段, 避免 build_method_inputs 注入的 question/subject/seed 等导致 TypeError
        "_raw=json.loads(os.environ['MYSTIC_ZIWEI_BIRTH']);"
        "_allowed=set(Birth.__dataclass_fields__.keys());"
        "_b=Birth(**{k:v for k,v in _raw.items() if k in _allowed});"
        "print(json.dumps(_compute_native(_b).to_dict(), ensure_ascii=False))"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=os.getcwd(),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return _fallback_chart(b, "py-iztro subprocess timed out")

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        reason = detail[-1] if detail else f"py-iztro subprocess exited with {proc.returncode}"
        return _fallback_chart(b, reason[:240])

    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        return ChartResult(**payload)
    except Exception as exc:
        return _fallback_chart(b, f"py-iztro subprocess returned invalid output: {exc}")


def _should_isolate_native_engine() -> bool:
    if os.environ.get("MYSTIC_ZIWEI_CHILD") == "1":
        return False
    if os.environ.get("MYSTIC_ZIWEI_INLINE") == "1":
        return False
    return os.name == "nt"


def _compute_native(b: Birth) -> ChartResult:
    gender = "男" if b.gender == "male" else "女"
    solar_date = f"{b.year}-{b.month}-{b.day}"
    time_index = _time_index(b.hour)
    chart = _by_solar(solar_date, time_index, gender)
    palaces = _palaces(chart)

    raw = {
        "rule_version": RULE_VERSION,
        "engine": ENGINE_NAME,
        "fallback": False,
        "fallback_reason": "",
        "calculation_basis": {
            "method": "ziwei",
            "mode": "natal",
            "rule_version": RULE_VERSION,
            "input_source": "iztro solar-date astrolabe; gender, date and Chinese hour index",
            "solar_date": solar_date,
            "time_index": time_index,
            "gender": gender,
            "limits": [
                "Different Zi Wei schools may place auxiliary stars or transformations differently.",
                "This output is a verifiable chart structure; interpretation should not invent missing stars.",
            ],
        },
        "soul": _text(getattr(chart, "soul", "")),
        "body": _text(getattr(chart, "body", "")),
        "five_elements": _text(getattr(chart, "five_elements_class", "")),
        "five_elements_class": _text(getattr(chart, "five_elements_class", "")),
        "palaces": palaces,
        "horoscope": _horoscope(chart, b, time_index),
        "four_transformations": _extract_four_transformations(_horoscope(chart, b, time_index)),
        # 飞星四化深度解读（集成 ziwei_sihua 数据）
        # W: 修复 year_gan 提取 bug - 之前 _text(yearly)[:1] 取的是 "(", 不是年干
        # chinese_date.yearly 形如 [("甲子", 1984, ...)] 或 [年, 干支], 取干支字符串首字符
        "four_transformations_enriched": _enrich_four_transformations(
            _extract_four_transformations(_horoscope(chart, b, time_index)),
            year_gan=_extract_year_gan(chart, b),
        ),
        "changsheng12_map": _palace_map(palaces, "changsheng12"),
        "boshi12_map": _palace_map(palaces, "boshi12"),
        "jiangqian12_map": _palace_map(palaces, "jiangqian12"),
    }

    return ChartResult(
        method="ziwei",
        school="east",
        engine=ENGINE_NAME,
        normalized={"elements": {}, "timeline": []},
        raw=raw,
    )


def compute(b: Birth) -> ChartResult:
    if _should_isolate_native_engine():
        return _compute_in_subprocess(b)
    return _compute_native(b)
