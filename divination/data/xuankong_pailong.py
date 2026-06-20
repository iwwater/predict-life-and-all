"""玄空飞星 · 排龙诀 + 三元龙分析。

文献：
  - 《沈氏玄空学》(清·沈竹礽)
  - 《地理辨正》(清·蒋大鸿)
  - 《玄空秘旨》
  - 《飞星赋》

核心概念：
  - 三元龙: 二十四山按 地元/天元/人元 分组（每卦 3 山）
  - 排龙诀: 看 来龙入首（龙从哪个方向来）与 山向 的关系
  - 净阴净阳: 山向是否纯阴/纯阳（最佳 vs. 阴阳驳杂）
  - 一卦纯清: 山向 + 来龙 + 去水 三者同属一卦（元龙一致）
"""
from __future__ import annotations

# 复用于 divination/fengshui.py 的常量
_GUA_3SHAN = {
    "坎": ["壬", "子", "癸"], "艮": ["丑", "艮", "寅"], "震": ["甲", "卯", "乙"],
    "巽": ["辰", "巽", "巳"], "離": ["丙", "午", "丁"], "坤": ["未", "坤", "申"],
    "兌": ["庚", "酉", "辛"], "乾": ["戌", "乾", "亥"],
}

_YIN = {"子", "午", "卯", "酉", "辰", "戌", "丑", "未", "癸", "丁", "乙", "辛"}
# 子午卯酉 = 阴；辰戌丑未 = 阴；癸丁乙辛 = 阴；其余 = 阳
_YANG = {"壬", "丙", "甲", "庚", "乾", "坤", "艮", "巽", "寅", "申", "巳", "亥"}


# ══════════════════════════════════════════════════════════════
# 1. 三元龙基础数据
# ══════════════════════════════════════════════════════════════
YUANLONG_TABLE: dict[str, dict[str, str]] = {}

for gua, shans in _GUA_3SHAN.items():
    for i, s in enumerate(shans):
        yuan = ["地", "天", "人"][i]
        yy = "阴" if s in _YIN else "阳"
        YUANLONG_TABLE[s] = {"卦": gua, "三元": yuan, "阴阳": yy}


# ══════════════════════════════════════════════════════════════
# 2. 二十四山完整信息表（与 fengshui.py 同步）
# ══════════════════════════════════════════════════════════════
TWENTY_FOUR_SHAN: dict[str, dict[str, str]] = {}
for shan, info in YUANLONG_TABLE.items():
    TWENTY_FOUR_SHAN[shan] = {
        "卦": info["卦"],
        "三元": info["三元"],
        "阴阳": info["阴阳"],
        "本卦山": info["卦"] == shan,  # 卦名与山名相同（八宫之卦）
    }


# 二十四山顺序（自壬起顺时针）
ORDER_24 = ["壬", "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳",
            "丙", "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥"]


# ══════════════════════════════════════════════════════════════
# 3. 排龙诀 · 来龙方位分析
# ══════════════════════════════════════════════════════════════
PAILONG_JUDGMENT: dict[str, dict[str, str]] = {
    "一卦纯清": {
        "pattern": "来龙 + 山 + 向 + 水 同属一卦",
        "luck": "大吉",
        "meaning": "三元龙一致,气运纯粹,大富贵之格。",
    },
    "父母三般卦": {
        "pattern": "来龙与山向为父母卦（隔一位）",
        "luck": "吉",
        "meaning": "三般卦之一,主家业昌盛。",
    },
    "连珠三般卦": {
        "pattern": "来龙与山向为连珠（同元龙）",
        "luck": "大吉",
        "meaning": "三般卦之最佳,主财丁两旺。",
    },
    "夫妇正配": {
        "pattern": "山向阴阳相配（一阴一阳）",
        "luck": "吉",
        "meaning": "山向阴阳调和,家宅安宁。",
    },
    "纯阴纯阳": {
        "pattern": "山向纯阴或纯阳（不驳杂）",
        "luck": "吉",
        "meaning": "阴阳不杂,主家道兴隆。",
    },
    "阴阳驳杂": {
        "pattern": "山向阴阳混合（阴中有阳或阳中有阴）",
        "luck": "凶",
        "meaning": "阴阳驳杂,主家宅不安,人丁不旺。",
    },
    "上山下水": {
        "pattern": "山星下水,水星上山（颠倒）",
        "luck": "大凶",
        "meaning": "主家破人亡,绝嗣之祸。",
    },
    "金龙不动": {
        "pattern": "山向两星到山到向,中宫不动",
        "luck": "大吉",
        "meaning": "山星向星归位,生气凝聚,丁财两旺。",
    },
}


# ══════════════════════════════════════════════════════════════
# 4. 二十四山 → 八卦 双向映射
# ══════════════════════════════════════════════════════════════
SHAN_TO_GUA: dict[str, str] = {shan: info["卦"] for shan, info in TWENTY_FOUR_SHAN.items()}
GUA_TO_SHANS: dict[str, list[str]] = {gua: shans for gua, shans in _GUA_3SHAN.items()}


# ══════════════════════════════════════════════════════════════
# 5. 查询函数
# ══════════════════════════════════════════════════════════════
def get_shan_info(shan: str) -> dict[str, str]:
    """查询山向信息：卦/三元/阴阳。"""
    return TWENTY_FOUR_SHAN.get(shan, {})


def is_yang(shan: str) -> bool:
    """判断山向是否属阳。"""
    info = get_shan_info(shan)
    return info.get("阴阳") == "阳"


def is_yin(shan: str) -> bool:
    """判断山向是否属阴。"""
    info = get_shan_info(shan)
    return info.get("阴阳") == "阴"


def get_yuan_long(shan: str) -> str:
    """查询某山的元龙（地/天/人）。"""
    info = get_shan_info(shan)
    return info.get("三元", "")


def get_gua(shan: str) -> str:
    """查询某山所属卦。"""
    return SHAN_TO_GUA.get(shan, "")


def get_shans_in_gua(gua: str) -> list[str]:
    """查询某卦下的三个山。"""
    return GUA_TO_SHANS.get(gua, [])


# ══════════════════════════════════════════════════════════════
# 6. 净阴净阳判断
# ══════════════════════════════════════════════════════════════
def judge_jing_yin_yang(sitting: str, facing: str) -> dict:
    """判断山向是否净阴/净阳。

    规则:
        - 山阴向阳: 阴阳相配, 吉
        - 山阳向阴: 阴阳相配, 吉
        - 山阴向阴: 纯阴, 平常
        - 山阳向阳: 纯阳, 平常
        - 净阴: 卦中三山皆阴 → 大吉
        - 净阳: 卦中三山皆阳 → 大吉
    """
    sit_yy = get_shan_info(sitting).get("阴阳", "")
    fac_yy = get_shan_info(facing).get("阴阳", "")
    sit_gua = get_gua(sitting)
    fac_gua = get_gua(facing)
    same_gua = sit_gua == fac_gua

    if sit_yy != fac_yy and same_gua:
        # 一卦内阴阳相配 → 净阴/净阳
        which = "净阳" if sit_yy == "阳" else "净阴"
        luck = "大吉"
        meaning = f"山{sitting}向{facing}, 一卦纯阴纯阳, {which}, 大吉。"
    elif sit_yy == fac_yy and same_gua:
        # 一卦内纯阴或纯阳 → 驳杂
        luck = "凶"
        meaning = f"山{sitting}向{facing}, 一卦内纯阴/纯阳, 驳杂, 不吉。"
    elif sit_yy != fac_yy:
        # 异卦但阴阳相配
        luck = "吉"
        meaning = f"山{sitting}向{facing}, 异卦阴阳相配, 吉。"
    else:
        # 异卦同阴/同阳
        luck = "平"
        meaning = f"山{sitting}向{facing}, 异卦同阴/同阳, 平常。"

    return {
        "sitting": sitting,
        "facing": facing,
        "sit_gua": sit_gua,
        "fac_gua": fac_gua,
        "sit_yin_yang": sit_yy,
        "fac_yin_yang": fac_yy,
        "same_gua": same_gua,
        "luck": luck,
        "meaning": meaning,
    }


# ══════════════════════════════════════════════════════════════
# 7. 三元龙格局判断
# ══════════════════════════════════════════════════════════════
def judge_yuan_long_pattern(sitting: str, facing: str) -> dict:
    """判断山向的三元龙格局。

    规则:
        - 同元龙: 山/向同一元（地/天/人）→ 一卦纯清, 大吉
        - 父母卦: 山/向为父母三般 → 吉
        - 纯异元: 山/向元龙完全不同 → 平常
    """
    sit_yuan = get_yuan_long(sitting)
    fac_yuan = get_yuan_long(facing)

    if sit_yuan == fac_yuan:
        luck = "大吉"
        pattern = "一卦纯清（同元龙）"
        meaning = f"山{sitting}（{sit_yuan}元龙）向{facing}（{fac_yuan}元龙）, 元龙一致, 一卦纯清, 大吉。"
    else:
        # 判断是否为父母三般卦
        # 简化: 异元但同卦 → 可推算
        sit_gua = get_gua(sitting)
        fac_gua = get_gua(facing)
        if sit_gua == fac_gua:
            luck = "吉"
            pattern = "父母三般卦（同卦异元）"
            meaning = f"山{sitting}（{sit_yuan}元龙）向{facing}（{fac_yuan}元龙）, 同卦异元, 吉。"
        else:
            luck = "平"
            pattern = "异卦异元"
            meaning = f"山{sitting}（{sit_yuan}元龙）向{facing}（{fac_yuan}元龙）, 异卦异元, 平常。"

    return {
        "sitting": sitting,
        "facing": facing,
        "sit_yuan": sit_yuan,
        "fac_yuan": fac_yuan,
        "pattern": pattern,
        "luck": luck,
        "meaning": meaning,
    }


# ══════════════════════════════════════════════════════════════
# 8. 排龙诀 · 来龙方位分析
# ══════════════════════════════════════════════════════════════
def judge_pai_long(coming_dragon: str, sitting: str, facing: str) -> dict:
    """排龙判断: 来龙 + 山 + 向 三者关系。

    Args:
        coming_dragon: 来龙方位（24 山之一）
        sitting: 坐山（24 山之一）
        facing: 向（24 山之一）

    Returns:
        {
            coming_dragon: 24山
            sitting: 24山
            facing: 24山
            dragon_gua: 来龙所属卦
            sit_gua: 坐山所属卦
            fac_gua: 向所属卦
            same_gua_all: 三者同卦
            yuan_long_all_match: 三者同元龙
            luck: 大吉/吉/平/凶
            meaning: 详细说明
        }
    """
    dragon_info = get_shan_info(coming_dragon)
    sit_info = get_shan_info(sitting)
    fac_info = get_shan_info(facing)

    dragon_gua = dragon_info.get("卦", "")
    sit_gua = sit_info.get("卦", "")
    fac_gua = fac_info.get("卦", "")
    dragon_yuan = dragon_info.get("三元", "")
    sit_yuan = sit_info.get("三元", "")
    fac_yuan = fac_info.get("三元", "")

    same_gua_all = dragon_gua == sit_gua == fac_gua
    yuan_long_match = dragon_yuan == sit_yuan == fac_yuan

    if same_gua_all and yuan_long_match:
        luck = "大吉"
        pattern = "一卦纯清"
        meaning = f"来龙{coming_dragon}（{dragon_gua}卦{dragon_yuan}元龙）, 山{sitting}, 向{facing}, 三者一卦纯清, 大吉。"
    elif same_gua_all:
        luck = "吉"
        pattern = "同卦异元"
        meaning = f"来龙{coming_dragon}（{dragon_gua}卦{dragon_yuan}元龙）, 山{sitting}, 向{facing}, 同卦异元, 吉。"
    elif yuan_long_match:
        luck = "吉"
        pattern = "同元龙异卦"
        meaning = f"来龙{coming_dragon}, 山{sitting}, 向{facing}, 元龙一致, 吉。"
    else:
        luck = "平"
        pattern = "驳杂"
        meaning = f"来龙{coming_dragon}, 山{sitting}, 向{facing}, 卦与元龙皆驳杂, 平常。"

    return {
        "coming_dragon": coming_dragon,
        "sitting": sitting,
        "facing": facing,
        "dragon_gua": dragon_gua,
        "sit_gua": sit_gua,
        "fac_gua": fac_gua,
        "same_gua_all": same_gua_all,
        "yuan_long_match": yuan_long_match,
        "pattern": pattern,
        "luck": luck,
        "meaning": meaning,
    }


# ══════════════════════════════════════════════════════════════
# 9. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 玄空排龙诀 + 三元龙 自检 ===\n")

    # 1. 二十四山基础
    print(f"1. 二十四山基础信息表: {len(TWENTY_FOUR_SHAN)} 山")
    # 展示 八宫 + 三元分布
    for gua in ["坎", "艮", "震", "巽", "離", "坤", "兌", "乾"]:
        shans = get_shans_in_gua(gua)
        yuans = [get_yuan_long(s) for s in shans]
        yys = [get_shan_info(s)["阴阳"] for s in shans]
        print(f"   {gua}: {shans} (元龙:{yuans}, 阴阳:{yys})")

    # 2. 净阴净阳示例
    print("\n2. 净阴净阳判断示例:")
    for sit, fac in [("子", "午"), ("壬", "丙"), ("癸", "丁"),
                     ("子", "丙"), ("卯", "酉"), ("乾", "巽")]:
        r = judge_jing_yin_yang(sit, fac)
        print(f"   山{sit}向{fac}: {r['luck']} | {r['meaning']}")

    # 3. 三元龙格局示例
    print("\n3. 三元龙格局示例:")
    for sit, fac in [("子", "癸"), ("壬", "子"), ("乾", "亥"), ("甲", "寅")]:
        r = judge_yuan_long_pattern(sit, fac)
        print(f"   山{sit}向{fac}: {r['pattern']} → {r['luck']}")

    # 4. 排龙诀示例
    print("\n4. 排龙诀示例:")
    for dragon, sit, fac in [("子", "子", "午"), ("壬", "壬", "丙"),
                              ("乾", "乾", "巽"), ("甲", "乙", "庚")]:
        r = judge_pai_long(dragon, sit, fac)
        print(f"   来龙{dragon} + 山{sit}向{fac}: {r['pattern']} → {r['luck']}")
