"""铁板神数 (Tie Ban Shen Shu) — Iron Plate Divination.
古典神数术数: 以生辰八字 + 太玄数编码 → 条文集数 → 条文查找。
含父母生肖校验机制 (考刻分)。
"""
from lunar_python import Solar

from ..contracts import Birth, ChartResult
from ..data.tieban_verses import (
    TIEBAN_VERSES,
    TIANGAN_NUM,
    TAIXUAN_NUM,
    YANG_ZHI,
    NAYIN_NUM,
    ZODIAC_NUM,
    VERSE_SET_COUNT,
)


def _solar_from_birth(b: Birth) -> Solar:
    return Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)


def _four_pillars(solar: Solar) -> dict:
    """Extract four pillars: year, month, day, hour in GanZhi."""
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    return {
        "year": ec.getYear(),
        "month": ec.getMonth(),
        "day": ec.getDay(),
        "hour": ec.getTime(),
    }


def _encode_stems(pillars: dict) -> dict:
    """Encode heavenly stems to numerical values."""
    result = {}
    for pillar_name in ["year", "month", "day", "hour"]:
        gz = pillars.get(pillar_name, "??")
        gan = gz[0] if len(gz) >= 1 else "?"
        result[pillar_name] = TIANGAN_NUM.get(gan, 0)
    return result


def _encode_branches(pillars: dict) -> dict:
    """Encode earthly branches using Tai Xuan numbers.
    Yang branches (子寅辰午申戌) use first number; yin use second."""
    result = {}
    for pillar_name in ["year", "month", "day", "hour"]:
        gz = pillars.get(pillar_name, "??")
        zhi = gz[1] if len(gz) >= 2 else "?"
        pair = TAIXUAN_NUM.get(zhi, (0, 0))
        num = pair[0] if zhi in YANG_ZHI else pair[1]
        result[pillar_name] = {"zhi": zhi, "num": num}
    return result


def _compute_base_number(stems: dict, branches: dict) -> int:
    """Compute the primary base number.
    Base = YearGan×1000 + MonthGan×100 + DayGan×10 + HourGan + Σ branch_nums"""
    gan_sum = (
        stems.get("year", 0) * 1000
        + stems.get("month", 0) * 100
        + stems.get("day", 0) * 10
        + stems.get("hour", 0)
    )
    branch_sum = sum(b["num"] for b in branches.values())
    return gan_sum + branch_sum


def _compute_ke_fen(minute: int) -> dict:
    """Compute ke (刻) and fen (分) from birth minute.
    1 ke = 15 minutes, 4 ke per shichen (2 hours).
    ke_fen_num = ke * 100 + fen"""
    ke = (minute // 15) + 1  # 1-4
    fen = minute % 15  # 0-14
    return {
        "ke": ke,
        "fen": fen,
        "ke_fen_num": ke * 100 + fen,
    }


def _lookup_verses(verse_set_number: int, father_zodiac: str = "", mother_zodiac: str = "") -> dict:
    """Look up verses from the database by set number.
    Optionally filter by parents' zodiac checksum."""
    range_keys = list(TIEBAN_VERSES.keys())
    idx = verse_set_number % len(range_keys)
    selected_range = range_keys[idx]
    verse_data = TIEBAN_VERSES[selected_range]
    all_categories = verse_data.get("categories", {})

    # Compute checksum from parents' zodiac if provided
    expected_checksum = 0
    if father_zodiac and mother_zodiac:
        fz_num = ZODIAC_NUM.get(father_zodiac, 0)
        mz_num = ZODIAC_NUM.get(mother_zodiac, 0)
        expected_checksum = (fz_num * 100 + mz_num) % 1000

    matched = []
    verification_note = ""
    for category, verses in all_categories.items():
        for v in verses:
            # If parents zodiac provided, filter by checksum match
            if expected_checksum > 0:
                # 父母生肖校验 (《铁板神数》考刻分): 严格匹配 checksum % 1000, 避免 % 1000 == 0 永远放行
                if v["checksum"] % 1000 == expected_checksum:
                    matched.append({
                        "category": category,
                        "number": v["number"],
                        "text": v["text"],
                        "checksum": v["checksum"],
                    })
            else:
                # No verification — return all verses in the set
                matched.append({
                    "category": category,
                    "number": v["number"],
                    "text": v["text"],
                    "checksum": v["checksum"],
                })

    if expected_checksum > 0:
        verification_note = (
            f"父母生肖校验: 父{father_zodiac}({ZODIAC_NUM.get(father_zodiac,0)}) "
            f"母{mother_zodiac}({ZODIAC_NUM.get(mother_zodiac,0)}), "
            f"校验和={expected_checksum}, "
            f"匹配{len(matched)}条"
        )

    return {
        "verse_set_number": verse_set_number,
        "verse_set_range": selected_range,
        "matched_verses": matched,
        "total_matched": len(matched),
        "verification": {
            "method": "父母生肖校验",
            "father_zodiac": father_zodiac or None,
            "mother_zodiac": mother_zodiac or None,
            "checksum": expected_checksum if expected_checksum > 0 else None,
            "note": verification_note or "未输入父母生肖，返回完整集数条文",
        },
    }


def compute(b: Birth) -> ChartResult:
    solar = _solar_from_birth(b)
    pillars = _four_pillars(solar)
    stems = _encode_stems(pillars)
    branches = _encode_branches(pillars)
    base_number = _compute_base_number(stems, branches)
    ke_fen = _compute_ke_fen(b.minute)
    verse_set_number = base_number + ke_fen["ke_fen_num"]

    # Optional parents' zodiac (passed via mode or custom fields)
    father_zodiac = getattr(b, "father_zodiac", "") or ""
    mother_zodiac = getattr(b, "mother_zodiac", "") or ""
    verse_result = _lookup_verses(verse_set_number, father_zodiac, mother_zodiac)

    # Build stem/branch encoding summaries
    stem_summary = {}
    for k in ["year", "month", "day", "hour"]:
        gz = pillars.get(k, "??")
        gan = gz[0] if len(gz) >= 1 else "?"
        stem_summary[k] = {"gan": gan, "num": TIANGAN_NUM.get(gan, 0)}

    branch_summary = {}
    for k in ["year", "month", "day", "hour"]:
        b_info = branches.get(k, {})
        branch_summary[k] = {
            "zhi": b_info.get("zhi", "?"),
            "num": b_info.get("num", 0),
            "type": "阳" if b_info.get("zhi", "") in YANG_ZHI else "阴" if b_info.get("zhi", "") else "?",
        }

    return ChartResult(
        method="tieban",
        school="east",
        engine="self+tieban-encoding",
        normalized={
            "elements": {},
            "timeline": [],
            "note": "铁板神数以条文编码为核心, 不使用五行计数归一化",
        },
        raw={
            "mode": "tieban_base",
            "subject": getattr(b, "subject", None) or "self_life",
            "rule_version": "v1",
            "four_pillars": pillars,
            "encoding": {
                "stems": stem_summary,
                "branches": branch_summary,
            },
            "base_number": base_number,
            "ke_fen": ke_fen,
            "verse_set_number": verse_set_number,
            "verse_result": verse_result,
            "calculation_basis": {
                "method": "tieban",
                "mode": "tieban_base",
                "rule_version": "v1",
                "input_source": "birth date → 四柱八字 → 天干数+太玄数编码 → 条文集数映射",
                "encoding_rule": "天干:甲1..癸10; 地支:太玄数(阳支取前数,阴支取后数); 刻分:每15分1刻共4刻",
                "limits": [
                    "MVP仅包含约100条核心条文，非完整12,000条数据库",
                    "条文集数映射为简化算法，不完全符合传统铁板神数秘传算法",
                    "父母生肖校验为可选功能，未输入时返回完整集数条文",
                    "此为非科学传统文化参考，不构成命运判决",
                ],
            },
        },
    )
