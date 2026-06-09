"""Ba Zhai life gua and residential direction analysis."""
from lunar_python import Solar

from ..contracts import Birth, ChartResult

GUA_BY_NUM = {1: "坎", 2: "坤", 3: "震", 4: "巽", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
EAST_FOUR = ["坎", "离", "震", "巽"]
WEST_FOUR = ["乾", "坤", "艮", "兑"]

# 24山 → 八卦 (与 xuankong SAN_TO_GUA 一致)
SITTING_TO_HOUSE_GUA = {
    "壬": "坎", "子": "坎", "癸": "坎",
    "丑": "艮", "艮": "艮", "寅": "艮",
    "甲": "震", "卯": "震", "乙": "震",
    "辰": "巽", "巽": "巽", "巳": "巽",
    "丙": "离", "午": "离", "丁": "离",
    "未": "坤", "坤": "坤", "申": "坤",
    "庚": "兑", "酉": "兑", "辛": "兑",
    "戌": "乾", "乾": "乾", "亥": "乾",
}

# 大游年歌: 每个宅卦的八方向对应星名
# 方位顺序: 北/南/东/西/东北/东南/西南/西北 (或按卦对应)
DAYOU_STARS = {
    "坎": {"北": "伏位", "南": "延年", "东": "天医", "西": "祸害",
           "东北": "五鬼", "东南": "生气", "西南": "绝命", "西北": "六煞"},
    "离": {"南": "伏位", "北": "延年", "东": "生气", "西": "五鬼",
           "东北": "祸害", "东南": "天医", "西南": "六煞", "西北": "绝命"},
    "震": {"东": "伏位", "西": "延年", "南": "生气", "北": "天医",
           "东北": "六煞", "东南": "延年", "西南": "祸害", "西北": "五鬼"},
    "巽": {"东南": "伏位", "西北": "延年", "北": "生气", "南": "天医",
           "东北": "绝命", "西南": "五鬼", "正东": "六煞", "正西": "祸害"},
    "乾": {"西北": "伏位", "东南": "延年", "西南": "天医", "东北": "生气",
           "正西": "绝命", "正南": "六煞", "正东": "五鬼", "正北": "祸害"},
    "坤": {"西南": "伏位", "东北": "延年", "正西": "天医", "正东": "祸害",
           "正北": "绝命", "西北": "生气", "正南": "六煞", "东南": "五鬼"},
    "艮": {"东北": "伏位", "西南": "延年", "西北": "天医", "东南": "祸害",
           "正南": "生气", "正西": "六煞", "正北": "五鬼", "正东": "绝命"},
    "兑": {"正西": "伏位", "正东": "延年", "西北": "生气", "东南": "六煞",
           "东北": "天医", "正南": "五鬼", "西南": "绝命", "正北": "祸害"},
}

# 八星吉凶评级: 1=最吉, 8=最凶
STAR_RANK = {
    "生气": 1, "天医": 2, "延年": 3, "伏位": 4,
    "祸害": 5, "六煞": 6, "五鬼": 7, "绝命": 8,
}

STAR_NATURE: dict[str, str] = {
    "生气": "木·贪狼·最大吉星·旺丁旺财",
    "天医": "土·巨门·大吉星·健康和睦",
    "延年": "金·武曲·中吉星·长寿延年",
    "伏位": "木·辅弼·小吉星·平稳守成",
    "祸害": "土·禄存·凶星·口舌是非",
    "六煞": "水·文曲·凶星·感情桃花",
    "五鬼": "火·廉贞·大凶星·意外官非",
    "绝命": "金·破军·最大凶星·破败伤灾",
}

AUSPICIOUS = {
    "坎": ["东南", "正东", "正南", "正北"],
    "离": ["正东", "东南", "正北", "正南"],
    "震": ["正南", "正北", "东南", "正东"],
    "巽": ["正北", "正南", "正东", "东南"],
    "乾": ["正西", "西南", "东北", "西北"],
    "坤": ["东北", "西北", "正西", "西南"],
    "艮": ["西南", "正西", "西北", "东北"],
    "兑": ["西北", "东北", "西南", "正西"],
}
INAUSPICIOUS = {
    "坎": ["西南", "东北", "西北", "正西"],
    "离": ["西北", "正西", "东北", "西南"],
    "震": ["正西", "西北", "西南", "东北"],
    "巽": ["东北", "西南", "正西", "西北"],
    "乾": ["正南", "正北", "正东", "东南"],
    "坤": ["正北", "正南", "东南", "正东"],
    "艮": ["东南", "正东", "正北", "正南"],
    "兑": ["正东", "东南", "正南", "正北"],
}


def _digital_root(n: int) -> int:
    n = abs(int(n))
    if n == 0:
        return 1
    while n > 9:
        n = sum(int(c) for c in str(n))
    return n


def _ming_gua(year: int, gender: str) -> tuple[int, str]:
    root = _digital_root(year)
    if gender == "female":
        num = _digital_root(root + 4)
        if num == 5:
            num = 8
    else:
        num = 11 - root
        num = _digital_root(num)
        if num == 5:
            num = 2
    return num, GUA_BY_NUM.get(num, "坤")


def _house_resident_match(life_gua: str, house_gua: str) -> dict:
    """宅命相配: 判断宅卦与命卦是否相配."""
    house_east = house_gua in EAST_FOUR
    life_east = life_gua in EAST_FOUR
    matched = house_east == life_east

    if matched:
        level = "东四宅配东四命" if house_east else "西四宅配西四命"
        description = "宅命相配，主吉。门主灶按宅卦吉方安放更佳，居住者与宅气场和谐。"
    else:
        level = "东四宅配西四命" if house_east else "西四宅配东四命"
        description = "宅命不配，建议以门、床、灶改至本命吉方化解；大门开本命吉方、卧床安本命吉方、灶台压本命凶方。"
    return {
        "matched": matched,
        "level": level,
        "description": description,
    }


def _bazhai_stars(house_gua: str) -> dict:
    """获取宅卦对应的八星方位表."""
    stars = DAYOU_STARS.get(house_gua, {})
    result = {}
    for direction, star_name in stars.items():
        rank = STAR_RANK.get(star_name, 9)
        nature = STAR_NATURE.get(star_name, "")
        result[direction] = {
            "star": star_name,
            "rank": rank,
            "auspicious": rank <= 4,
            "nature": nature,
        }
    return result


def compute(b: Birth) -> ChartResult:
    solar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0)
    lunar = solar.getLunar()
    li_chun_year_gz = lunar.getYearInGanZhiByLiChun()
    # Approximate numeric year adjustment via GanZhi-by-LiChun: before LiChun can belong to previous ritual year.
    li_chun_year = b.year - 1 if li_chun_year_gz != lunar.getYearInGanZhi() and b.month <= 2 else b.year
    num, life_gua = _ming_gua(li_chun_year, b.gender)
    is_east = life_gua in EAST_FOUR
    auspicious = AUSPICIOUS[life_gua]
    inauspicious = INAUSPICIOUS[life_gua]

    mode = b.mode or "life_gua"
    raw: dict = {
        "mode": mode,
        "subject": b.subject or "home_fengshui",
        "rule_version": "v1",
        "life_gua": life_gua,
        "life_gua_number": num,
        "is_east": is_east,
        "east_four": EAST_FOUR,
        "west_four": WEST_FOUR,
        "auspicious_dirs": auspicious,
        "inauspicious_dirs": inauspicious,
        "sitting": b.sitting,
        "year_gz": li_chun_year_gz,
        "ritual_year": li_chun_year,
    }

    # ── 宅命相配 (当有坐向输入时) ──
    if b.sitting and mode in ("residential_bazhai", "life_gua"):
        house_gua = SITTING_TO_HOUSE_GUA.get(b.sitting, life_gua)
        match_info = _house_resident_match(life_gua, house_gua)
        bazhai_stars = _bazhai_stars(house_gua)
        raw["house_gua"] = house_gua
        raw["house_is_east"] = house_gua in EAST_FOUR
        raw["house_resident_match"] = match_info
        raw["bazhai_stars"] = bazhai_stars
        # 按大游年歌重算吉凶方(以宅卦为准)
        raw["house_auspicious_dirs"] = [d for d, s in bazhai_stars.items() if s["auspicious"]]
        raw["house_inauspicious_dirs"] = [d for d, s in bazhai_stars.items() if not s["auspicious"]]

    raw["calculation_basis"] = {
        "method": "bazhai",
        "mode": mode,
        "rule_version": "v1",
        "calendar_source": "lunar-python",
        "year_cut": "Li Chun year",
        "formula": "male: 11 - digital_root(year), female: digital_root(year)+4; 5 maps male=2 female=8",
        "scope": "宅主命卦与四吉四凶方；宅命相配分析；大游年八星方位评定",
        "limits": [
            "仅提供命卦和四吉四凶方向，不等于完整风水布局",
            "立春分界近似处理，边缘日期可能偏移一年",
            "数字根函数已防护负数和大数，但仍限制在合理年份范围内(1500-2100)",
        ],
    }

    return ChartResult(
        method="bazhai",
        school="east",
        engine="self+minggua",
        normalized={"elements": {}, "timeline": [], "note": "八宅以命卦(坎离震巽乾坤艮兑)为核心指标, 不直接映射五行数量"},
        raw=raw,
    )
