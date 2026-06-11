"""风水堪舆（可计算部分）—— 玄空飞星 + 八宅。
文献：玄空飞星《沈氏玄空学》(沈竹礽)、《飞星赋》《玄空秘旨》、蒋大鸿《地理辨正》；
      八宅《八宅明镜》(箬冠道人)。
峦头形势（龙穴砂水）为定性相地，不在此算法化。"""

# 后天九宫飞泊顺序：中→乾→兑→艮→离→坎→坤→震→巽
_FLY_ORDER = ["中", "乾", "兌", "艮", "離", "坎", "坤", "震", "巽"]

# 二十四山：(山名) -> (后天卦, 三元龙 地/天/人, 阴阳)
# 阴阳表(沈氏玄空)：地元 壬丙甲庚=阳 辰戌丑未=阴；天元 子午卯酉=阴 乾坤艮巽=阳；人元 癸丁乙辛=阴 寅申巳亥=阳
_MOUNTAINS = {}
_GUA_3SHAN = {
    "坎": ["壬", "子", "癸"], "艮": ["丑", "艮", "寅"], "震": ["甲", "卯", "乙"],
    "巽": ["辰", "巽", "巳"], "離": ["丙", "午", "丁"], "坤": ["未", "坤", "申"],
    "兌": ["庚", "酉", "辛"], "乾": ["戌", "乾", "亥"],
}
_YANG = set("壬丙甲庚") | set("子午卯酉".replace("", "")) | set(["乾", "坤", "艮", "巽"]) | set("寅申巳亥")
# 注：子午卯酉为阴、辰戌丑未为阴、癸丁乙辛为阴；其余为阳
_YIN = set("子午卯酉") | set("辰戌丑未") | set("癸丁乙辛")
for gua, shans in _GUA_3SHAN.items():
    for i, s in enumerate(shans):
        yuan = ["地", "天", "人"][i]
        yy = "阴" if s in _YIN else "阳"
        _MOUNTAINS[s] = {"卦": gua, "三元": yuan, "阴阳": yy}

# 二十四山顺序（自壬起顺时针），对宫(向)= +12
_ORDER24 = ["壬", "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳",
            "丙", "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥"]


def facing_of(sitting: str) -> str:
    i = _ORDER24.index(sitting)
    return _ORDER24[(i + 12) % 24]


def san_yuan_jiu_yun(year: int) -> dict:
    """三元九运。1864 起每 20 年一运，1-9 循环。当前九运=2024–2043。"""
    yun = ((year - 1864) // 20) % 9 + 1
    yuan = "上元" if yun <= 3 else ("中元" if yun <= 6 else "下元")
    return {"运": yun, "元": yuan}


def _fly(center_num: int, forward: bool) -> dict:
    """某星入中，顺(forward)或逆飞九宫。返回 {卦: 星数}。"""
    out = {}
    n = center_num
    step = 1 if forward else -1
    for pal in _FLY_ORDER:
        out[pal] = (n - 1) % 9 + 1
        n += step
    return out


def xuankong(period: int, sitting: str) -> dict:
    """玄空飞星排盘。period=运(1-9)，sitting=坐山(24山之一)。"""
    facing = facing_of(sitting)
    sit_gua = _MOUNTAINS[sitting]["卦"]
    fac_gua = _MOUNTAINS[facing]["卦"]
    # 1) 运盘：运数入中顺飞
    yun_pan = _fly(period, True)
    # 2) 山星/向星基数 = 运盘对应宫数
    shan_base = yun_pan[sit_gua]
    xiang_base = yun_pan[fac_gua]
    # 3) 顺逆：以坐(向)三元龙，取 base 数对应卦中同元龙之山，看其阴阳
    def dir_of(base_num, yuan):
        gua = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"}[base_num]
        if gua == "中":
            gua = sit_gua  # 5入中借坐山卦（简化处理）
        shan = _GUA_3SHAN[gua][{"地": 0, "天": 1, "人": 2}[yuan]]
        return _MOUNTAINS[shan]["阴阳"] == "阳"
    shan_pan = _fly(shan_base, dir_of(shan_base, _MOUNTAINS[sitting]["三元"]))
    xiang_pan = _fly(xiang_base, dir_of(xiang_base, _MOUNTAINS[facing]["三元"]))
    # 4) 组合九宫
    grid = {pal: {"运": yun_pan[pal], "山": shan_pan[pal], "向": xiang_pan[pal]}
            for pal in _FLY_ORDER}
    # 5) 格局：旺山旺向 / 上山下水 / 双星到向(坐)
    sit_s, sit_x = grid[sit_gua]["山"], grid[sit_gua]["向"]
    fac_s, fac_x = grid[fac_gua]["山"], grid[fac_gua]["向"]
    pat = []
    if fac_x == period and sit_s == period:
        pat.append("旺山旺向（丁财两旺）")
    elif fac_s == period and sit_x == period:
        pat.append("上山下水（损丁破财，需形峦化解）")
    elif fac_s == period and fac_x == period:
        pat.append("双星到向（旺财，宜向首见水）")
    elif sit_s == period and sit_x == period:
        pat.append("双星到坐（旺丁，宜坐山见水）")
    return {"运": period, "元旦盘运": period, "坐": sitting, "向": facing,
            "坐卦": sit_gua, "向卦": fac_gua, "九宫": grid,
            "向首": {"山星": fac_s, "向星": fac_x}, "坐山": {"山星": sit_s, "向星": sit_x},
            "格局": pat or ["其他局（需具体断）"]}


# ===== 八宅 =====
_GUA_NUM = {1: "坎", 2: "坤", 3: "震", 4: "巽", 6: "乾", 7: "兌", 8: "艮", 9: "離"}
_EAST4 = {"坎", "離", "震", "巽"}   # 东四命/宅
_WEST4 = {"乾", "坤", "艮", "兌"}   # 西四命/宅


def ming_gua(year: int, gender: str) -> dict:
    """本命卦（三元命卦法）。注：严格应以立春为年界，此处用公历年，临界年需校。"""
    g = year
    s = sum(int(c) for c in str(g))
    while s > 9:
        s = sum(int(c) for c in str(s))
    if gender == "male":
        num = (11 - s)
        num = num - 9 if num > 9 else num
        gua = "坤" if num == 5 else _GUA_NUM[num]
    else:
        num = (s + 4)
        num = num - 9 if num > 9 else num
        gua = "艮" if num == 5 else _GUA_NUM[num]
    return {"命卦": gua, "命": "东四命" if gua in _EAST4 else "西四命"}


# 八宅·八游年（伏位起，依命卦排八方吉凶）；此处给四吉四凶方位性质
_YOUNIAN = {  # 命卦 -> {方位卦: 游年星}
    "坎": {"坎": "伏位", "離": "延年", "震": "天医", "巽": "生气", "乾": "六煞", "坤": "绝命", "兌": "祸害", "艮": "五鬼"},
    "離": {"離": "伏位", "坎": "延年", "巽": "天医", "震": "生气", "坤": "六煞", "乾": "绝命", "艮": "祸害", "兌": "五鬼"},
    "震": {"震": "伏位", "巽": "延年", "坎": "天医", "離": "生气", "兌": "绝命", "艮": "六煞", "乾": "五鬼", "坤": "祸害"},
    "巽": {"巽": "伏位", "震": "延年", "離": "天医", "坎": "生气", "艮": "绝命", "兌": "六煞", "坤": "五鬼", "乾": "祸害"},
    "乾": {"乾": "伏位", "兌": "生气", "艮": "天医", "坤": "延年", "巽": "祸害", "坎": "六煞", "震": "五鬼", "離": "绝命"},
    "坤": {"坤": "伏位", "艮": "生气", "兌": "天医", "乾": "延年", "坎": "绝命", "離": "六煞", "巽": "五鬼", "震": "祸害"},
    "艮": {"艮": "伏位", "坤": "生气", "乾": "天医", "兌": "延年", "離": "祸害", "震": "六煞", "巽": "五鬼", "坎": "绝命"},
    "兌": {"兌": "伏位", "乾": "生气", "坤": "天医", "艮": "延年", "震": "绝命", "巽": "六煞", "離": "五鬼", "坎": "祸害"},
}
_JI = {"生气", "天医", "延年", "伏位"}


def bazhai(year: int, gender: str) -> dict:
    mg = ming_gua(year, gender)
    table = _YOUNIAN[mg["命卦"]]
    fang = {pos: {"游年": star, "吉凶": "吉" if star in _JI else "凶"}
            for pos, star in table.items()}
    return {**mg, "八方": fang,
            "吉方": [p for p, v in fang.items() if v["吉凶"] == "吉"],
            "凶方": [p for p, v in fang.items() if v["吉凶"] == "凶"]}
