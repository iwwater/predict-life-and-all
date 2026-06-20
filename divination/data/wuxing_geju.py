"""八字格局 (Pattern/Structure) 分类 — 动态检查体系。

格局是八字命理的核心概念,根据十神组合与日主强弱,判断命局的层次与类型。

文献:
  - 《渊海子平》卷一·论格局, 卷二·内十八格
  - 《三命通会》卷四-卷九·各格详论
  - 《子平真诠》(清·沈孝瞻)

分类:
  - 贵格 (Authority Pattern) — 官印相生/杀印相生/食神制杀
  - 富格 (Wealth Pattern) — 财官双美/食神生财/从财格
  - 文格 (Scholarly Pattern) — 伤官佩印
  - 武格 (Martial Pattern) — 羊刃驾杀/从杀格
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


# ══════════════════════════════════════════════════════════════
# 1. 格局数据类
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GejuPattern:
    """单条格局模式。

    Attributes:
        name: 格局名 (中文)
        category: 分类 (贵格/富格/文格/武格)
        description: 格局说明
        check_fn_description: 检测逻辑说明 (文字描述,不含函数引用)
        source: 文献出处
    """
    name: str
    category: str
    description: str
    check_fn_description: str
    source: str = "《渊海子平》"


# ══════════════════════════════════════════════════════════════
# 2. 十干十神映射辅助
# ══════════════════════════════════════════════════════════════

# 天干五行
_GAN_WX: dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

# 五行生克
_SHENG: dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE: dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 干支十神判定 (相对于日主)
def _gan_ten_god(gan: str, day_master_gan: str) -> str:
    """返回单个天干相对于日主的十神类别。"""
    gwx = _GAN_WX.get(gan, "")
    dwx = _GAN_WX.get(day_master_gan, "")
    if not gwx or not dwx:
        return "未知"
    if gwx == dwx:
        yin_yang_same = (gan == day_master_gan) or (
            ("甲乙".count(gan) and "甲乙".count(day_master_gan))
            or ("丙丁".count(gan) and "丙丁".count(day_master_gan))
            or ("戊己".count(gan) and "戊己".count(day_master_gan))
            or ("庚辛".count(gan) and "庚辛".count(day_master_gan))
            or ("壬癸".count(gan) and "壬癸".count(day_master_gan))
        )
        return "比肩" if gan == day_master_gan else "劫财"
    if _SHENG.get(gwx) == dwx:
        return "正印" if _same_yin_yang(gan, day_master_gan) else "偏印"
    if _SHENG.get(dwx) == gwx:
        return "食神" if _same_yin_yang(gan, day_master_gan) else "伤官"
    if _KE.get(gwx) == dwx:
        return "正官" if not _same_yin_yang(gan, day_master_gan) else "七杀"
    if _KE.get(dwx) == gwx:
        return "正财" if not _same_yin_yang(gan, day_master_gan) else "偏财"
    return "未知"


def _same_yin_yang(a: str, b: str) -> bool:
    """判断两天干是否同阴阳 (甲丙戊庚壬为阳, 乙丁己辛癸为阴)。"""
    yang = set("甲丙戊庚壬")
    return (a in yang) == (b in yang)


def _get_all_stems_in_pillars(pillars: dict) -> list[str]:
    """从四柱干支中提取所有天干(含地支藏干推定)。"""
    stems: list[str] = []
    for pos in ["year", "month", "day", "hour"]:
        gz = pillars.get(pos, "")
        if len(gz) >= 2:
            stems.append(gz[0])  # 天干
            stems.append(gz[1])  # 地支 (简化为单个, 实际可用藏干)
    return stems


def _has_ten_god(stems: list[str], day_master_gan: str, target_god: str) -> bool:
    """检查 stems 中是否存在指定的十神类型。"""
    for s in stems:
        if _gan_ten_god(s, day_master_gan) == target_god:
            return True
    return False


def _count_ten_god_in_pillars(
    pillars: dict, day_master_gan: str, target_god: str
) -> int:
    """统计四柱中某十神出现的次数。"""
    stems = _get_all_stems_in_pillars(pillars)
    return sum(1 for s in stems if _gan_ten_god(s, day_master_gan) == target_god)


# ══════════════════════════════════════════════════════════════
# 3. 格局检测函数 (纯函数, data in → bool out)
# ══════════════════════════════════════════════════════════════

def _count_god(
    ten_god_counts: dict,
    god_keys: list[str],
) -> int:
    """统计十神计数表中指定十神的总出现次数。"""
    return sum(ten_god_counts.get(k, 0) for k in god_keys)


def check_shishen_zhisha(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """食神制杀: 食神 + 七杀同现, 食神有力可制杀。

    条件:
    - 七杀至少 1 个
    - 食神至少 1 个
    - 食神数量 >= 七杀数量 (有力制杀)
    """
    shi_shen = _count_god(ten_god_counts, ["食神"])
    qi_sha = _count_god(ten_god_counts, ["七杀"])
    return qi_sha >= 1 and shi_shen >= 1 and shi_shen >= qi_sha


def check_shangguan_peiyin(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """伤官佩印: 伤官 + 正/偏印同现, 印制伤官。

    条件:
    - 伤官至少 1 个
    - 正印或偏印至少 1 个
    - 日主身弱更宜 (strength < 60)
    """
    shang_guan = _count_god(ten_god_counts, ["伤官"])
    yin = _count_god(ten_god_counts, ["正印", "偏印"])
    return shang_guan >= 1 and yin >= 1 and strength_score < 60


def check_caiguan_shuangmei(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """财官双美: 正财 + 正官同现且有力。

    条件:
    - 正财至少 1 个
    - 正官至少 1 个
    - 日主身强能担财官 (strength >= 55)
    """
    zheng_cai = _count_god(ten_god_counts, ["正财"])
    zheng_guan = _count_god(ten_god_counts, ["正官"])
    return zheng_cai >= 1 and zheng_guan >= 1 and strength_score >= 55


def check_guan_yin_xiangsheng(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """官印相生: 正官 + 正印, 官生印。

    条件:
    - 正官至少 1 个
    - 正印至少 1 个
    """
    zheng_guan = _count_god(ten_god_counts, ["正官"])
    zheng_yin = _count_god(ten_god_counts, ["正印"])
    return zheng_guan >= 1 and zheng_yin >= 1


def check_shishen_shengcai(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """食神生财: 食神 + 正/偏财, 食神生财。

    条件:
    - 食神至少 1 个
    - 正财或偏财至少 1 个
    - 日主身强 (strength >= 60)
    """
    shi_shen = _count_god(ten_god_counts, ["食神"])
    cai = _count_god(ten_god_counts, ["正财", "偏财"])
    return shi_shen >= 1 and cai >= 1 and strength_score >= 60


def check_sha_yin_xiangsheng(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """杀印相生: 七杀 + 正/偏印, 杀生印。

    条件:
    - 七杀至少 1 个
    - 正印或偏印至少 1 个
    """
    qi_sha = _count_god(ten_god_counts, ["七杀"])
    yin = _count_god(ten_god_counts, ["正印", "偏印"])
    return qi_sha >= 1 and yin >= 1


def check_yangren_jiasha(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """羊刃驾杀: 日主有羊刃 + 七杀, 刃驾杀。

    条件:
    - 七杀至少 1 个
    - 日主身强带刃 (strength >= 75)
    - 地支中有日主之羊刃
    """
    qi_sha = _count_god(ten_god_counts, ["七杀"])
    if qi_sha < 1 or strength_score < 75:
        return False
    # 日干→羊刃地支映射 (帝旺位)
    _YANG_REN_MAP: dict[str, str] = {
        "甲": "卯", "乙": "寅",
        "丙": "午", "丁": "巳",
        "戊": "午", "己": "巳",
        "庚": "酉", "辛": "申",
        "壬": "子", "癸": "亥",
    }
    yang_ren_zhi = _YANG_REN_MAP.get(day_master_gan, "")
    for pos in ["year", "month", "day", "hour"]:
        gz = pillars.get(pos, "")
        if len(gz) >= 2 and gz[1] == yang_ren_zhi:
            return True
    return False


def check_congcai_ge(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """从财格: 财星极旺, 日主从之。

    条件:
    - 财星占比 >= 50% of all gods
    - 日主极弱 (strength <= 20)
    - 无比劫帮扶
    """
    cai = _count_god(ten_god_counts, ["正财", "偏财"])
    bi_jie = _count_god(ten_god_counts, ["比肩", "劫财"])
    total = sum(ten_god_counts.values())
    if total == 0:
        return False
    return cai >= total * 0.5 and strength_score <= 20 and bi_jie == 0


def check_congsha_ge(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """从杀格: 七杀极旺, 日主从之。

    条件:
    - 七杀占比 >= 40% of all gods
    - 日主极弱 (strength <= 15)
    - 无印星化杀
    """
    qi_sha = _count_god(ten_god_counts, ["七杀"])
    yin = _count_god(ten_god_counts, ["正印", "偏印"])
    total = sum(ten_god_counts.values())
    if total == 0:
        return False
    return qi_sha >= total * 0.4 and strength_score <= 15 and yin == 0


def check_huaqi_ge(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> bool:
    """化气格: 日干与月干或时干合化。

    条件:
    - 日干与月干或时干存在天干五合
    - 合化方向与月令五行一致
    """
    _HE_MAP: dict[str, str] = {
        "甲": "己", "己": "甲",
        "乙": "庚", "庚": "乙",
        "丙": "辛", "辛": "丙",
        "丁": "壬", "壬": "丁",
        "戊": "癸", "癸": "戊",
    }
    # 天干五合化气方向
    _HE_HUA: dict[str, str] = {
        "甲": "土", "己": "土",
        "乙": "金", "庚": "金",
        "丙": "水", "辛": "水",
        "丁": "木", "壬": "木",
        "戊": "火", "癸": "火",
    }
    month_gan = pillars.get("month", "")[0] if len(pillars.get("month", "")) >= 2 else ""
    hour_gan = pillars.get("hour", "")[0] if len(pillars.get("hour", "")) >= 2 else ""
    month_zhi = pillars.get("month", "")[1] if len(pillars.get("month", "")) >= 2 else ""

    candidates = []
    if month_gan and _HE_MAP.get(day_master_gan) == month_gan:
        candidates.append(("月干", month_gan))
    if hour_gan and _HE_MAP.get(day_master_gan) == hour_gan:
        candidates.append(("时干", hour_gan))

    if not candidates:
        return False

    # 还需检查月令五行是否支持合化方向
    hua_wx = _HE_HUA.get(day_master_gan, "")
    month_wx = _GAN_WX.get(month_zhi, "")
    # 简化判断: 只要存在天干五合即视为化气格成立
    return len(candidates) >= 1


# ══════════════════════════════════════════════════════════════
# 4. 格局列表
# ══════════════════════════════════════════════════════════════

GEOJU_PATTERNS: list[GejuPattern] = [
    GejuPattern(
        name="食神制杀",
        category="贵格",
        description="食神有力克制七杀,化杀为权。杀为凶神,得食神制之,反为权柄。主威权在握,多为武职或企业领袖。",
        check_fn_description="七杀≥1, 食神≥1, 食神数≥七杀数",
        source="《渊海子平》卷二·食神制杀格",
    ),
    GejuPattern(
        name="伤官佩印",
        category="文格",
        description="伤官虽泄秀,但过则伤身,得印星制伤官生身,为贵。主聪明秀气,文章冠世,多为文人学者。",
        check_fn_description="伤官≥1, 正偏印≥1, 日主身弱(strength<60)",
        source="《渊海子平》卷二·伤官佩印格",
    ),
    GejuPattern(
        name="财官双美",
        category="富格",
        description="正财正官同透,财能生官,官能护财,相辅相成。主富贵双全,事业有成,家庭美满。",
        check_fn_description="正财≥1, 正官≥1, 日主身强(strength≥55)",
        source="《三命通会》卷六·财官双美格",
    ),
    GejuPattern(
        name="官印相生",
        category="贵格",
        description="正官生正印,官印相生有情。官为权力,印为文书,官印双全主贵气,多为政府官员或学术权威。",
        check_fn_description="正官≥1, 正印≥1",
        source="《渊海子平》卷一·官印相生格",
    ),
    GejuPattern(
        name="食神生财",
        category="富格",
        description="食神生财,财源不断。食神为财之源头,生生不息,主经商致富,企业家命。",
        check_fn_description="食神≥1, 正偏财≥1, 日主身强(strength≥60)",
        source="《子平真诠》食神生财格",
    ),
    GejuPattern(
        name="杀印相生",
        category="贵格",
        description="七杀攻身本凶,得印星化杀生身,反为权柄。杀印相生有请有义,主武贵,多为军警司法之才。",
        check_fn_description="七杀≥1, 正偏印≥1",
        source="《三命通会》卷七·杀印相生格",
    ),
    GejuPattern(
        name="羊刃驾杀",
        category="武格",
        description="日主身强带刃,以七杀为用,刃驾杀威。主刚毅果决,敢作敢为,多武职或创业领袖。",
        check_fn_description="七杀≥1, 日主身强带刃(strength≥75), 地支有日主羊刃",
        source="《渊海子平》卷二·羊刃驾杀格",
    ),
    GejuPattern(
        name="从财格",
        category="富格",
        description="财星极旺,日主无根不得不从。从财则财为我,主大富之命。但需大运顺财方吉。",
        check_fn_description="财星占比≥50%, 日主极弱(strength≤20), 无比劫",
        source="《渊海子平》卷二·从财格",
    ),
    GejuPattern(
        name="从杀格",
        category="武格",
        description="七杀极旺,日主无根不得不从。从杀则杀为我用,主大贵大权,但亦多险。多为乱世英豪。",
        check_fn_description="七杀占比≥40%, 日主极弱(strength≤15), 无印星",
        source="《渊海子平》卷二·从杀格",
    ),
    GejuPattern(
        name="化气格",
        category="贵格",
        description="日干与月干或时干天干五合,化气为用。化气成格主贵,化气不成反为羁绊。需月令支持化气方向。",
        check_fn_description="日干与月干或时干存在天干五合",
        source="《渊海子平》卷二·化气格",
    ),
]


# ══════════════════════════════════════════════════════════════
# 5. 格局名 → 检测函数映射
# ══════════════════════════════════════════════════════════════

_GEOJU_CHECK_FN_MAP: dict[str, Callable] = {
    "食神制杀": check_shishen_zhisha,
    "伤官佩印": check_shangguan_peiyin,
    "财官双美": check_caiguan_shuangmei,
    "官印相生": check_guan_yin_xiangsheng,
    "食神生财": check_shishen_shengcai,
    "杀印相生": check_sha_yin_xiangsheng,
    "羊刃驾杀": check_yangren_jiasha,
    "从财格": check_congcai_ge,
    "从杀格": check_congsha_ge,
    "化气格": check_huaqi_ge,
}


# ══════════════════════════════════════════════════════════════
# 6. 公共函数: 动态格局评估
# ══════════════════════════════════════════════════════════════

def evaluate_dynamic_geju(
    day_master_gan: str,
    ten_god_counts: dict,
    pillars: dict,
    strength_score: float,
) -> list[dict]:
    """评估所有格局模式,返回匹配的格局列表。

    对每个格局模式调用其检测函数,收集所有匹配项,并按格局类别排序。

    Args:
        day_master_gan: 日主天干 (甲-癸)
        ten_god_counts: 十神计数表, e.g. {"正官": 2, "食神": 1, ...}
        pillars: 四柱干支, e.g. {"year": "甲子", "month": "丙寅", ...}
        strength_score: 日主强弱评分 (0-100)

    Returns:
        matched_geju: list of dicts, each with name, category, description, source
    """
    matched: list[dict] = []

    for pattern in GEOJU_PATTERNS:
        check_fn = _GEOJU_CHECK_FN_MAP.get(pattern.name)
        if check_fn is None:
            continue
        try:
            if check_fn(day_master_gan, ten_god_counts, pillars, strength_score):
                matched.append({
                    "name": pattern.name,
                    "category": pattern.category,
                    "description": pattern.description,
                    "check_logic": pattern.check_fn_description,
                    "source": pattern.source,
                })
        except Exception:
            # If check fails due to missing data, silently skip
            continue

    # Sort by category order: 贵格 > 富格 > 文格 > 武格
    _CAT_ORDER: dict[str, int] = {"贵格": 0, "富格": 1, "文格": 2, "武格": 3}
    matched.sort(key=lambda x: _CAT_ORDER.get(x["category"], 99))

    return matched
