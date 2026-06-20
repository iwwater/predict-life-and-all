"""彭祖百忌 — 老黄历日忌完整表 (10 天干 + 12 地支 = 22 类).

文献:
  - 《协纪辨方书》(清·乾隆官修)
  - 《玉匣记》(清·许真君传)
  - 《择吉会要》(清·姚承舆)

数据结构:
  STEM_TABOOS  - 10 天干日忌讳（每干 1 主忌）
  BRANCH_TABOOS - 12 地支日忌讳（每支 1 主忌）
  TOTAL_TABOO_CATEGORIES - 22 类（10 天干 + 12 地支）

⚠️ 注意:
  - "百忌"传统统计为 ~100 条具体忌讳，源自多个日课体系汇编
  - 本表收录天干忌 10 条 + 地支忌 12 条 = 22 主类
  - lunar-python 内置 getPengZuGan/getPengZuZhi 返回的口诀格式为
    "X不Y Z", 与本表结构一致
"""
from __future__ import annotations

# ══════════════════════════════════════════════════════════════
# 1. 10 天干日忌
# ══════════════════════════════════════════════════════════════
# 字段: stem, taboo_action, consequence, category, severity

STEM_TABOOS: dict[str, dict[str, str]] = {
    "甲": {
        "stem": "甲", "taboo_action": "开仓", "consequence": "财物耗散",
        "category": "财物", "severity": "中",
        "full_text": "甲不开仓,财物耗散",
        "explanation": "甲为木,木主生发。开仓者,泄木气也,故主耗散。",
    },
    "乙": {
        "stem": "乙", "taboo_action": "栽植", "consequence": "千株不长",
        "category": "农事", "severity": "中",
        "full_text": "乙不栽植,千株不长",
        "explanation": "乙为柔木,栽植者耗其生气,故千株不长。",
    },
    "丙": {
        "stem": "丙", "taboo_action": "修灶", "consequence": "必见灾殃",
        "category": "修造", "severity": "高",
        "full_text": "丙不修灶,必见灾殃",
        "explanation": "丙为火,灶亦属火,火上加火,燥烈过甚,主灾。",
    },
    "丁": {
        "stem": "丁", "taboo_action": "剃头", "consequence": "头生疮痍",
        "category": "身体", "severity": "中",
        "full_text": "丁不剃头,头生疮痍",
        "explanation": "丁为阴火,主血脉。剃头则血气外泄,易生疮。",
    },
    "戊": {
        "stem": "戊", "taboo_action": "不受田", "consequence": "田主不祥",
        "category": "田宅", "severity": "中",
        "full_text": "戊不受田,田主不祥",
        "explanation": "戊为阳土,主田宅。不受田则失其根本,主不祥。",
    },
    "己": {
        "stem": "己", "taboo_action": "破券", "consequence": "二比并亡",
        "category": "财务契约", "severity": "高",
        "full_text": "己不破券,二比并亡",
        "explanation": "己为阴土,主契约。破券则失信,主两败俱伤。",
    },
    "庚": {
        "stem": "庚", "taboo_action": "经络", "consequence": "身体遭伤",
        "category": "身体", "severity": "高",
        "full_text": "庚不经络,身体遭伤",
        "explanation": "庚为阳金,主杀伐。经络主血气,金克木伤血。",
    },
    "辛": {
        "stem": "辛", "taboo_action": "酗酒", "consequence": "沉醉不醒",
        "category": "饮食", "severity": "中",
        "full_text": "辛不酗酒,沉醉不醒",
        "explanation": "辛为阴金,主收敛。酗酒则辛金被克,神志昏沉。",
    },
    "壬": {
        "stem": "壬", "taboo_action": "汲水", "consequence": "水泉不洁",
        "category": "生活", "severity": "低",
        "full_text": "壬不汲水,水泉不洁",
        "explanation": "壬为阳水,主江河。汲水者耗其源,主水不清。",
    },
    "癸": {
        "stem": "癸", "taboo_action": "词讼", "consequence": "理弱敌强",
        "category": "诉讼", "severity": "高",
        "full_text": "癸不词讼,理弱敌强",
        "explanation": "癸为阴水,主暗昧。词讼则阴气盛,理屈词穷。",
    },
}

# ══════════════════════════════════════════════════════════════
# 2. 12 地支日忌
# ══════════════════════════════════════════════════════════════
BRANCH_TABOOS: dict[str, dict[str, str]] = {
    "子": {
        "branch": "子", "taboo_action": "问卜", "consequence": "自惹祸殃",
        "category": "神事", "severity": "中",
        "full_text": "子不问卜,自惹祸殃",
        "explanation": "子水主智,但用神日不宜问卜,反招疑神疑鬼。",
    },
    "丑": {
        "branch": "丑", "taboo_action": "冠带", "consequence": "主有灾殃",
        "category": "身体", "severity": "中",
        "full_text": "丑不冠带,主有灾殃",
        "explanation": "丑为墓库,冠带者华而不实,反招灾祸。",
    },
    "寅": {
        "branch": "寅", "taboo_action": "祭祀", "consequence": "神明不享",
        "category": "祭祀", "severity": "中",
        "full_text": "寅不祭祀,神明不享",
        "explanation": "寅为鬼门,祭祀反招邪祟,不享正神。",
    },
    "卯": {
        "branch": "卯", "taboo_action": "穿井", "consequence": "水泉不香",
        "category": "修造", "severity": "中",
        "full_text": "卯不穿井,水泉不香",
        "explanation": "卯为木,水生木则水源泄,故水泉不香。",
    },
    "辰": {
        "branch": "辰", "taboo_action": "哭泣", "consequence": "亲人不祥",
        "category": "丧事", "severity": "高",
        "full_text": "辰不哭泣,亲人不祥",
        "explanation": "辰为天罡,哭泣则伤龙脉,主亲属不安。",
    },
    "巳": {
        "branch": "巳", "taboo_action": "出行", "consequence": "文书不行",
        "category": "出行", "severity": "中",
        "full_text": "巳不出行,文书不行",
        "explanation": "巳为驿马,出行本吉,但巳日出行,主文书阻滞。",
    },
    "午": {
        "branch": "午", "taboo_action": "占疾", "consequence": "药不相当",
        "category": "医药", "severity": "中",
        "full_text": "午不占疾,药不相当",
        "explanation": "午为火,火旺金死,占疾则医药无功。",
    },
    "未": {
        "branch": "未", "taboo_action": "服药", "consequence": "毒气入肠",
        "category": "医药", "severity": "高",
        "full_text": "未不服药,毒气入肠",
        "explanation": "未为木库,木主肝,服药则肝木受伤,毒气内侵。",
    },
    "申": {
        "branch": "申", "taboo_action": "开店", "consequence": "不吉不祥",
        "category": "经商", "severity": "中",
        "full_text": "申不开店,吉凶难料",
        "explanation": "申为刀剑,开店主竞争激烈,成败难料。",
    },
    "酉": {
        "branch": "酉", "taboo_action": "宴客", "consequence": "沉醉不醒",
        "category": "饮食", "severity": "中",
        "full_text": "酉不宴客,沉醉不祥",
        "explanation": "酉为阴金,酒入酉则阴金受克,易致昏沉。",
    },
    "戌": {
        "branch": "戌", "taboo_action": "食犬", "consequence": "作恶吠人",
        "category": "饮食", "severity": "中",
        "full_text": "戌不食犬,作恶吠人",
        "explanation": "戌为火库,食犬则冲戌,主口舌纷争。",
    },
    "亥": {
        "branch": "亥", "taboo_action": "嫁娶", "consequence": "不利新郎",
        "category": "嫁娶", "severity": "高",
        "full_text": "亥不嫁娶,不利新郎",
        "explanation": "亥为乾宫,婚礼本吉,但亥日婚主新郎不利。",
    },
}


# ══════════════════════════════════════════════════════════════
# 3. 派生统计
# ══════════════════════════════════════════════════════════════
TOTAL_TABOO_CATEGORIES = len(STEM_TABOOS) + len(BRANCH_TABOOS)  # = 22
TOTAL_STEM_TABOOS = len(STEM_TABOOS)  # 10
TOTAL_BRANCH_TABOOS = len(BRANCH_TABOOS)  # 12


# ══════════════════════════════════════════════════════════════
# 4. 查询函数
# ══════════════════════════════════════════════════════════════
def get_taboo(day_gan: str, day_zhi: str) -> dict[str, dict[str, str]]:
    """给定日干支,返回对应的天干忌 + 地支忌。"""
    return {
        "stem_taboo": STEM_TABOOS.get(day_gan, {}),
        "branch_taboo": BRANCH_TABOOS.get(day_zhi, {}),
    }


def get_taboo_summary(day_gan: str, day_zhi: str) -> str:
    """返回完整彭祖百忌摘要: '甲不开仓...；子不问卜...'"""
    taboos = get_taboo(day_gan, day_zhi)
    parts = []
    if taboos["stem_taboo"]:
        parts.append(taboos["stem_taboo"]["full_text"])
    if taboos["branch_taboo"]:
        parts.append(taboos["branch_taboo"]["full_text"])
    return "；".join(parts)


def get_severity_distribution() -> dict[str, int]:
    """按严重等级统计（高/中/低）。"""
    dist: dict[str, int] = {"高": 0, "中": 0, "低": 0}
    for t in list(STEM_TABOOS.values()) + list(BRANCH_TABOOS.values()):
        sev = t.get("severity", "中")
        dist[sev] = dist.get(sev, 0) + 1
    return dist


def get_category_distribution() -> dict[str, int]:
    """按类目统计（修造/祭祀/医药 等）。"""
    dist: dict[str, int] = {}
    for t in list(STEM_TABOOS.values()) + list(BRANCH_TABOOS.values()):
        cat = t.get("category", "其他")
        dist[cat] = dist.get(cat, 0) + 1
    return dist


def verify_against_lunar_python(day_gan: str, day_zhi: str) -> dict[str, bool]:
    """与 lunar-python 输出对照（结构化验证）。

    Returns:
        {stem_match: bool, branch_match: bool, both_match: bool}
    """
    from lunar_python import Solar

    # 找一个与 (day_gan, day_zhi) 匹配的日期做对照
    # 简化：直接构造日期，遍历
    solar = Solar.fromYmdHms(2026, 1, 1, 12, 0, 0)
    for _ in range(60):
        lun = solar.getLunar()
        gz = lun.getDayInGanZhi()
        if gz[0] == day_gan and gz[1] == day_zhi:
            pengzu_gan = lun.getPengZuGan() or ""
            pengzu_zhi = lun.getPengZuZhi() or ""
            expected_gan = STEM_TABOOS.get(day_gan, {}).get("full_text", "")
            expected_zhi = BRANCH_TABOOS.get(day_zhi, {}).get("full_text", "")
            return {
                "stem_match": expected_gan.replace(",", "") == pengzu_gan.replace(",", ""),
                "branch_match": expected_zhi.replace(",", "") == pengzu_zhi.replace(",", ""),
                "both_match": False,
                "expected": {"gan": expected_gan, "zhi": expected_zhi},
                "got": {"gan": pengzu_gan, "zhi": pengzu_zhi},
            }
        solar = solar.nextDay(1)
    return {"error": "未找到匹配日干支"}


# ══════════════════════════════════════════════════════════════
# 5. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 彭祖百忌 完整表自检 ===\n")

    print(f"1. 天干忌: {TOTAL_STEM_TABOOS} 条")
    for stem, t in STEM_TABOOS.items():
        print(f"   {stem}: {t['full_text']} ({t['severity']})")

    print(f"\n2. 地支忌: {TOTAL_BRANCH_TABOOS} 条")
    for zhi, t in BRANCH_TABOOS.items():
        print(f"   {zhi}: {t['full_text']} ({t['severity']})")

    print(f"\n3. 总计: {TOTAL_TABOO_CATEGORIES} 类")

    sev = get_severity_distribution()
    print(f"\n4. 严重等级: 高={sev['高']}, 中={sev['中']}, 低={sev['低']}")

    cats = get_category_distribution()
    print(f"\n5. 类目分布 ({len(cats)} 类):")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {c}: {n}")

    # 6. 查询示例
    print("\n6. 查询示例:")
    for dg, dz in [("癸", "亥"), ("甲", "子"), ("己", "卯")]:
        s = get_taboo_summary(dg, dz)
        print(f"   {dg}{dz}日: {s}")

    # 7. 与 lunar-python 对照
    print("\n7. 与 lunar-python 对照 (应匹配):")
    for dg, dz in [("癸", "亥"), ("甲", "子"), ("己", "卯")]:
        v = verify_against_lunar_python(dg, dz)
        if "error" not in v:
            match_gan = "✓" if v["stem_match"] else "✗"
            match_zhi = "✓" if v["branch_match"] else "✗"
            print(f"   {dg}{dz}日: 干{match_gan} {v['expected']['gan']!r} vs {v['got']['gan']!r}")
            print(f"           支{match_zhi} {v['expected']['zhi']!r} vs {v['got']['zhi']!r}")
        else:
            print(f"   {dg}{dz}日: {v['error']}")
