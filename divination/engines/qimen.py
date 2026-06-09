"""奇门遁甲  ——  纯 Python 自实现(lunar-python 替代 sxtwl/ephem)。

时家奇门(转盘 / 拆补局,MVP 简化版):
- 用 lunar-python 算真太阳时 + 节气 + 干支
- 三元 + 局数基于日干支 + 时辰在该旬中的位置
- 输出 3x3 宫格(地盘/天盘/九星/八门/八神)

注:本实现为 MVP 简化版,够"看盘 + 解读"用;商业精度请接专业排盘师。
"""
from ..contracts import Birth, ChartResult
from datetime import datetime, timedelta


# ---------- 静态常量 ----------

# 洛书九宫(后天八卦顺序): 巽4 离9 坤2 / 震3 中5 兑7 / 艮8 坎1 乾6
GONG_BY_LUO_SHU = {
    4: "巽", 9: "离", 2: "坤",
    3: "震", 5: "中", 7: "兑",
    8: "艮", 1: "坎", 6: "乾",
}
GONG_NUM = {v: k for k, v in GONG_BY_LUO_SHU.items()}

# 八卦宫位顺序(顺飞阳遁,逆飞阴遁)
CLOCKWISE = ["坎", "艮", "震", "巽", "离", "坤", "兑", "乾"]

# 三奇六仪(地盘干序)
SAN_QI_LIU_YI = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
YIN_DUN_ORDER = ["戊", "乙", "丙", "丁", "癸", "壬", "辛", "庚", "己"]

# 九星 + 八门
NINE_STARS = {
    1: "天蓬", 8: "天任", 3: "天冲", 4: "天辅", 9: "天英",
    2: "天芮", 7: "天柱", 6: "天心", 5: "天禽",
}
EIGHT_DOORS = {
    1: "休", 8: "生", 3: "伤", 4: "杜", 9: "景",
    2: "死", 7: "惊", 6: "开",
}
EIGHT_GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
YIN_DUN_GODS = ["值符", "螣蛇", "太阴", "六合", "玄武", "白虎", "九天", "九地"]


# ---------- 干支计算(用 lunar-python,跨平台零 C 依赖) ----------

def _gz_str(idx: int) -> str:
    """60 甲子索引 -> "甲子" 字符串。"""
    return f"{'甲乙丙丁戊己庚辛壬癸'[idx % 10]}{'子丑寅卯辰巳午未申酉戌亥'[idx % 12]}"


def _hour_branch_index(dt: datetime) -> int:
    """真太阳时 → 时辰支索引(0=子时...11=亥时)。早子时(0:00-0:59)归 0。"""
    h = dt.hour
    if h == 23:
        return 11  # 晚子时
    return (h + 1) // 2  # 0-1→0(子), 2-3→1(丑), ... , 22-23→11(亥)


def _true_solar_time(year: int, month: int, day: int, hour: int, minute: int,
                     lng: float | None) -> datetime:
    """粗略真太阳时(经度校正,无纬度校正)。"""
    if lng is None:
        return datetime(year, month, day, hour, minute)
    # 中国标准时(UTC+8)对应东八区(120°E),经度差 1° 折 4 分钟
    diff_min = int((lng - 120.0) * 4)
    return datetime(year, month, day, hour, minute) + timedelta(minutes=diff_min)


def _get_ganzhi(dt: datetime) -> dict:
    """从 datetime 拿年月日时干支(lunar-python)。"""
    from lunar_python import Solar
    sol = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
    lun = sol.getLunar()
    return {
        "年": lun.getYearInGanZhi(),
        "月": lun.getMonthInGanZhi(),
        "日": lun.getDayInGanZhi(),
        "时": lun.getTimeInGanZhi(),
    }


def _get_solar_term(dt: datetime) -> str:
    """查当前时辰所在节气(lunar-python)。"""
    from lunar_python import Solar
    sol = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
    return sol.getLunar().getJieQi() or sol.getLunar().getPrevJieQi().getName() or "冬至"


# ---------- 奇门起局 ----------

_YANG_DUN_BASE = {  # 阳遁三元基础局(简化版,基于日干支 0-59 索引 mod 15 落点)
    # 甲子旬(0-9)、甲戌旬(10-19)、甲申旬(20-29)、
    # 甲午旬(30-39)、甲辰旬(40-49)、甲寅旬(50-59)
    0: 1, 1: 7, 2: 3, 3: 9, 4: 5,
    10: 1, 11: 7, 12: 3, 13: 9, 14: 5,
    20: 1, 21: 7, 22: 3, 23: 9, 24: 5,
    30: 1, 31: 7, 32: 3, 33: 9, 34: 5,
    40: 1, 41: 7, 42: 3, 43: 9, 44: 5,
    50: 1, 51: 7, 52: 3, 53: 9, 54: 5,
}


def _gan_zhi_index(gz: str) -> int:
    """60 甲子索引。"""
    tgs = "甲乙丙丁戊己庚辛壬癸"
    dzs = "子丑寅卯辰巳午未申酉戌亥"
    # 用 baseDate 算索引(更稳,避免散点计算)
    base = datetime(1900, 1, 31, 0, 0)  # 已知庚子日
    target = datetime(1900, 1, 31)  # 简化为日柱
    # 改用 lunar-python 算
    from lunar_python import Solar
    # 通过年干支反算
    tg = gz[0]
    dz = gz[1]
    for i in range(60):
        if tgs[i % 10] == tg and dzs[i % 12] == dz:
            return i
    return 0


def _get_yu_and_ju(gz_day: str, gz_hour: str, yang_dun: bool) -> tuple[str, int]:
    """根据日干支和时辰,确定 元(上/中/下) 和 局(1-9)。
    简化算法:日干支 0-59 索引 mod 15 决定基础三元,时辰在该旬中的位置决定局数偏移。
    """
    day_idx = _gan_zhi_index(gz_day)
    hour_idx = _gan_zhi_index(gz_hour)
    xun_idx = day_idx // 10 * 10  # 旬起始

    # 三元(每 5 日 1 元,15 日 1 轮)
    pos_in_yuans = day_idx % 15
    yuan = "上元" if pos_in_yuans < 5 else ("中元" if pos_in_yuans < 10 else "下元")

    # 基础局(查表,默认填 1)
    base_ju = _YANG_DUN_BASE.get(xun_idx, 1)

    # 时辰在该旬中的位置(0-9)
    hour_in_xun = (hour_idx - xun_idx) % 10

    # 阳遁 + 1 / 阴遁 - 1(简化)
    ju = ((base_ju - 1) + hour_in_xun) % 9 + 1
    if not yang_dun:
        ju = 10 - ju  # 阳 1 ↔ 阴 9,阳 5 = 阴 5
        if ju == 10:
            ju = 5

    return yuan, ju


def _layout_earth(yang_dun: bool, ju: int) -> dict[str, str]:
    """地盘:三奇六仪按阳顺/阴逆,从 1 宫起戊布入九宫。"""
    # 戊开始的宫位(1, 8, 3, 4, 9, 2, 7, 6, 5) 阳遁
    # 阴遁(1, 6, 7, 2, 9, 4, 3, 8, 5)
    yang_seq = [1, 8, 3, 4, 9, 2, 7, 6, 5]
    yin_seq = [1, 6, 7, 2, 9, 4, 3, 8, 5]
    seq = yang_seq if yang_dun else yin_seq
    gans = SAN_QI_LIU_YI if yang_dun else YIN_DUN_ORDER
    return {GONG_BY_LUO_SHU[seq[i]]: gans[i] for i in range(9)}




def _rotate(gong_list: list[str], start: str, yang_dun: bool) -> list[str]:
    """把 gong_list 从 start 开始按阳顺/阴逆重排。"""
    if start not in gong_list:
        return list(gong_list)
    n = len(gong_list)
    start_idx = gong_list.index(start)
    result = [None] * n
    for i in range(n):
        if yang_dun:
            result[i] = gong_list[(start_idx + i) % n]
        else:
            result[i] = gong_list[(start_idx - i) % n]
    return result


def _layout_sky_and_stars(earth: dict[str, str], hour_gan: str, yang_dun: bool) -> tuple[dict, dict]:
    """天盘:九星 + 天干(按时干转)。"""
    # 找时干在地盘的位置
    zhifu_gong = next((g for g, gan in earth.items() if gan == hour_gan), "巽")
    # 时家奇门:阳遁时干落在 1/8/3/4/9/2/7/6 宫的"原始"九星顺序飞布
    star_seq = ["坎", "艮", "震", "巽", "离", "坤", "兑", "乾", "中"]
    # 时干落宫在 star_seq 里的索引
    if zhifu_gong in star_seq:
        start = star_seq.index(zhifu_gong)
    else:
        start = 0
    # 天盘九星(按时干转的顺序)
    sky_gans = [earth[g] for g in star_seq]  # 戊己庚辛壬癸丁丙乙 按 1,8,3,4,9,2,7,6,5
    # 重新排序,使得 zhifu_gong 位对应时干
    sky_gans_reordered = sky_gans[start:] + sky_gans[:start]
    stars_reordered = ["天蓬", "天任", "天冲", "天辅", "天英",
                       "天芮", "天柱", "天心", "天禽"]
    stars_reordered = stars_reordered[start:] + stars_reordered[:start]
    # 中宫特殊处理
    sky = {star_seq[i]: (sky_gans_reordered[i], stars_reordered[i])
           for i in range(9)}
    sky_pan = {g: sky[g][0] for g in star_seq}
    stars = {g: sky[g][1] for g in star_seq}
    return sky_pan, stars


def _layout_doors(earth: dict[str, str], hour_gan: str, yang_dun: bool) -> dict[str, str]:
    """人盘:八门(按值使门转)。值使门=时干落宫对应的原始八门位。"""
    # 值使门 = 时干在地盘对应的宫位 → 阳遁/阴遁八门起始
    zhifu_gong = next((g for g, gan in earth.items() if gan == hour_gan), None)
    # 阳遁八门原始:坎1=休, 艮8=生, 震3=伤, 巽4=杜, 离9=景, 坤2=死, 兑7=惊, 乾6=开
    door_seq_gong = ["坎", "艮", "震", "巽", "离", "坤", "兑", "乾"]
    door_seq = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
    if zhifu_gong in door_seq_gong:
        start = door_seq_gong.index(zhifu_gong)
    else:
        start = 0
    n = len(door_seq)
    ordered = [None] * n
    if yang_dun:
        for i in range(n):
            ordered[i] = door_seq[(start + i) % n]
    else:
        for i in range(n):
            ordered[i] = door_seq[(start - i) % n]
    return {g: (ordered[i] if i < len(ordered) else "")
            for i, g in enumerate(door_seq_gong)}


def _layout_gods(zhifu_gong: str, yang_dun: bool) -> dict[str, str]:
    """神盘:八神(随值符飞,从值符落宫起)。阴遁逆排,阳遁顺排。"""
    gods = EIGHT_GODS if yang_dun else YIN_DUN_GODS
    god_seq_gong = ["坎", "艮", "震", "巽", "离", "坤", "兑", "乾"]
    if zhifu_gong not in god_seq_gong:
        return {}
    start = god_seq_gong.index(zhifu_gong)
    n = len(gods)
    ordered = [None] * n
    for i in range(n):
        if yang_dun:
            ordered[i] = gods[i % n]
        else:
            ordered[i] = gods[(-i) % n]
    # 将值符放在 start 宫位
    rotated = god_seq_gong[start:] + god_seq_gong[:start]
    if yang_dun:
        result = {rotated[i]: ordered[i] for i in range(n)}
    else:
        result = {rotated[i]: ordered[i] for i in range(n)}
    return result


# ---------- 对外接口 ----------

# 干支五行映射
_GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
           "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
_STAR_WX = {"天蓬": "水", "天任": "土", "天冲": "木", "天辅": "木", "天英": "火",
            "天芮": "土", "天柱": "金", "天心": "金", "天禽": "土"}
_DOOR_WX = {"休": "水", "生": "土", "伤": "木", "杜": "木", "景": "火",
            "死": "土", "惊": "金", "开": "金"}


def _count_elements(earth: dict, sky: dict, stars: dict, doors: dict) -> dict:
    """从地盘、天盘、九星、八门统计五行分布。"""
    elem = {"metal": 0, "wood": 0, "water": 0, "fire": 0, "earth": 0}
    wx_key = {"金": "metal", "木": "wood", "水": "water", "火": "fire", "土": "earth"}
    for gan in earth.values():
        wx = _GAN_WX.get(gan, "")
        if wx in wx_key:
            elem[wx_key[wx]] += 1
    for gan in sky.values():
        wx = _GAN_WX.get(gan[0] if isinstance(gan, tuple) else gan, "")
        if wx in wx_key:
            elem[wx_key[wx]] += 1
    for star in stars.values():
        wx = _STAR_WX.get(star, "")
        if wx in wx_key:
            elem[wx_key[wx]] += 1
    for door in doors.values():
        wx = _DOOR_WX.get(door, "")
        if wx in wx_key:
            elem[wx_key[wx]] += 1
    return elem


def compute(b: Birth) -> ChartResult:
    dt = _true_solar_time(b.year, b.month, b.day, b.hour, b.minute, b.lng)
    gz = _get_ganzhi(dt)
    solar_term = _get_solar_term(dt)
    yang_dun = solar_term in ("冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
                              "春分", "清明", "谷雨", "立夏", "小满", "芒种")
    yuan, ju = _get_yu_and_ju(gz["日"], gz["时"], yang_dun)

    earth = _layout_earth(yang_dun, ju)
    sky, stars = _layout_sky_and_stars(earth, gz["时"][0], yang_dun)
    doors = _layout_doors(earth, gz["时"][0], yang_dun)

    # 值符值使 — must compute before _layout_gods
    zhifu_gong = next((g for g, gan in earth.items() if gan == gz["时"][0]), "巽")
    gods = _layout_gods(zhifu_gong, yang_dun) if zhifu_gong else {}
    zhifu_star = stars.get(zhifu_gong, "")
    zhifu_door = doors.get(zhifu_gong, "")

    return ChartResult(
        method="qimen", school="east", engine="lunar-python+self",
        normalized={"elements": _count_elements(earth, sky, stars, doors), "timeline": []},
        raw={
            "mode": getattr(b, "mode", None) or "hour_qimen",
            "subject": getattr(b, "subject", None) or "decision",
            "rule_version": "v1",
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "true_solar_time": dt.strftime("%H:%M"),
            "solar_term": solar_term,
            "dun": "阳遁" if yang_dun else "阴遁",
            "yuan": yuan,
            "ju": ju,
            "ganzhi": gz,
            "earth_pan": earth,
            "sky_pan": sky,
            "stars": stars,
            "doors": doors,
            "gods": gods,
            "zhifu": {
                "star": zhifu_star, "star_gong": zhifu_gong,
                "door": zhifu_door, "door_gong": zhifu_gong,
                "gan": gz["时"][0], "gan_gong": zhifu_gong,
            },
            "xun_shou": f"{gz['日']} 所在旬头(旬首)",
            "config": {
                "layout": "转盘 (revolving plate)",
                "method": "拆补 (chai-bu)",
                "fallback_to": "置闰待补",
                "true_solar_time": "经度校正,无纬度",
            },
            "calculation_basis": {
                "method": "qimen",
                "mode": getattr(b, "mode", None) or "hour_qimen",
                "subject": getattr(b, "subject", None) or "decision",
                "rule_version": "v1",
                "scope": "时家奇门为主；日家/刻家作为 mode 预留，不在本版本替换盘面。",
                "calendar_source": "lunar-python",
                "time_rule": "经度校正真太阳时，按节气定阴阳遁，按日时干支定元局。",
                "input_source": "birth (year/month/day/hour/minute) + optional lng",
                "accuracy_level": "structured_mvp_with_basis",
                "limits": [
                    "拆补法仅在时家奇门下使用; 置闰法尚未补入, 标注为 '拆补/置闰待补'",
                    "九宫神门星仪结构完整, 但不包含奇门遁甲的八诈/九遁/天盘格局逐项分析",
                    "日家/刻家奇门作为 mode 预留, 当前一律按时家排盘",
                ],
            },
        },
    )
