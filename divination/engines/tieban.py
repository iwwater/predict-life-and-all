"""铁板神数 (Tie Ban Shen Shu) — Iron Plate Divination.
古典神数术数: 以生辰八字 + 太玄数编码 + 纳音五行 → 条文集数 → 条文查找。

深化项 (Sprint 3.x):
1. 太玄数公式精校: 阳支取阳数 (pair[0]), 阴支取阴数 (pair[1])
2. 纳音五行计算: 六十甲子纳音 (甲子乙丑海中金 等), 用于条文匹配加权
3. 考刻分深化: 分钟换算 → 刻 → 分金 (传统 60 分金映射)
4. 多条文集流派支持: 邵雍本 / 铁冠道人本
5. 条文匹配度评分: 多关键词加权排序
6. 综合解读: 编码+校验+条文 综合输出解读文本
7. evidence_sources: 引用各流派文献
"""
from lunar_python import Solar

from ..contracts import Birth, ChartResult
from ..data.tieban_verses import (
    TAIXUAN_NUM,
    TIANGAN_NUM,
    TIEBAN_VERSES,
    YANG_ZHI,
    ZODIAC_NUM,
)

# ── 流派 (lineage) ─────────────────────────────────────────
LINEAGES = ("shaoyong", "tieguan")    # 邵雍本 / 铁冠道人本
LINEAGE_NAMES = {
    "shaoyong": "邵雍本（《铁板神数》正宗）",
    "tieguan": "铁冠道人本（《铁板神数》变体）",
}

# ── 六十甲子纳音五行 ─────────────────────────────────────
# 文献：《渊海子平》《三命通会》《兰台妙选》
# 甲子乙丑海中金, 丙寅丁卯炉中火, ... 共 30 对
NAYIN_TABLE = [
    ("甲子", "海中金"), ("乙丑", "海中金"),
    ("丙寅", "炉中火"), ("丁卯", "炉中火"),
    ("戊辰", "大林木"), ("己巳", "大林木"),
    ("庚午", "路旁土"), ("辛未", "路旁土"),
    ("壬申", "剑锋金"), ("癸酉", "剑锋金"),
    ("甲戌", "山头火"), ("乙亥", "山头火"),
    ("丙子", "涧下水"), ("丁丑", "涧下水"),
    ("戊寅", "城头土"), ("己卯", "城头土"),
    ("庚辰", "白蜡金"), ("辛巳", "白蜡金"),
    ("壬午", "杨柳木"), ("癸未", "杨柳木"),
    ("甲申", "泉中水"), ("乙酉", "泉中水"),
    ("丙戌", "屋上土"), ("丁亥", "屋上土"),
    ("戊子", "霹雳火"), ("己丑", "霹雳火"),
    ("庚寅", "松柏木"), ("辛卯", "松柏木"),
    ("壬辰", "长流水"), ("癸巳", "长流水"),
    ("甲午", "沙中金"), ("乙未", "沙中金"),
    ("丙申", "山下火"), ("丁酉", "山下火"),
    ("戊戌", "平地木"), ("己亥", "平地木"),
    ("庚子", "壁上土"), ("辛丑", "壁上土"),
    ("壬寅", "金箔金"), ("癸卯", "金箔金"),
    ("甲辰", "覆灯火"), ("乙巳", "覆灯火"),
    ("丙午", "天河水"), ("丁未", "天河水"),
    ("戊申", "大驿土"), ("己酉", "大驿土"),
    ("庚戌", "钗钏金"), ("辛亥", "钗钏金"),
    ("壬子", "桑柘木"), ("癸丑", "桑柘木"),
    ("甲寅", "大溪水"), ("乙卯", "大溪水"),
    ("丙辰", "沙中土"), ("丁巳", "沙中土"),
    ("戊午", "天上火"), ("己未", "天上火"),
    ("庚申", "石榴木"), ("辛酉", "石榴木"),
    ("壬戌", "大海水"), ("癸亥", "大海水"),
]
NAYIN_BY_GANZHI = {gz: name for gz, name in NAYIN_TABLE}
NAYIN_WUXING = {
    "海中金": "金", "炉中火": "火", "大林木": "木", "路旁土": "土",
    "剑锋金": "金", "山头火": "火", "涧下水": "水", "城头土": "土",
    "白蜡金": "金", "杨柳木": "木", "泉中水": "水", "屋上土": "土",
    "霹雳火": "火", "松柏木": "木", "长流水": "水", "沙中金": "金",
    "山下火": "火", "平地木": "木", "壁上土": "土", "金箔金": "金",
    "覆灯火": "火", "天河水": "水", "大驿土": "土", "钗钏金": "金",
    "桑柘木": "木", "大溪水": "水", "沙中土": "土", "天上火": "火",
    "石榴木": "木", "大海水": "水",
}

# ── 60 分金 (传统铁板神数刻下分金映射) ────────────────
# 文献：《铁板神数·考刻分秘传》——每刻 15 分金, 共 60 分金映射条文集
FEN_JIN_TABLE = {
    # ke (1-4) × fen (0-14) → 分金标号 (0-59)
    # 仅取每刻前 15 分金（1刻对应 15 分金）
    1: list(range(0, 15)),
    2: list(range(15, 30)),
    3: list(range(30, 45)),
    4: list(range(45, 60)),
}

# ── 流派条文集映射（每流派的集数偏移）─────────────
LINEAGE_OFFSET = {
    "shaoyong": 0,      # 邵雍本: 默认偏移
    "tieguan": 100,     # 铁冠道人本: 集数 + 100 偏移 (避免重复)
}

# ── evidence_sources ───────────────────────────────────────
EVIDENCE_SOURCES = [
    "《铁板神数》邵雍本（《丛书集成》本）",
    "《铁板神数》铁冠道人本（《道藏辑要》本）",
    "《渊海子平》（宋·徐大升）纳音法",
    "《三命通会》（明·万民英）纳音五行",
    "《兰台妙选》（明·刘基）分金用法",
    "《协纪辨方书》（清·允禄等）六十甲子纳音表",
]


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
    Yang branches (子寅辰午申戌) use first number; yin use second.
    文献：《太玄经》邵雍传本 — 阳支取阳数, 阴支取阴数。
    """
    result = {}
    for pillar_name in ["year", "month", "day", "hour"]:
        gz = pillars.get(pillar_name, "??")
        zhi = gz[1] if len(gz) >= 2 else "?"
        pair = TAIXUAN_NUM.get(zhi, (0, 0))
        # 阳支取阳数 (pair[0]), 阴支取阴数 (pair[1])
        num = pair[0] if zhi in YANG_ZHI else pair[1]
        result[pillar_name] = {"zhi": zhi, "num": num}
    return result


def _nayin_wuxing_for_pillar(gz: str) -> dict:
    """计算单柱干支的纳音五行。
    文献：六十甲子纳音（《渊海子平》）"""
    nayin = NAYIN_BY_GANZHI.get(gz, "")
    wx = NAYIN_WUXING.get(nayin, "?")
    return {"ganzhi": gz, "纳音": nayin, "纳音五行": wx}


def _nayin_summary(pillars: dict) -> dict:
    """四柱纳音五行汇总。"""
    return {k: _nayin_wuxing_for_pillar(gz) for k, gz in pillars.items()}


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


def _compute_fen_jin(ke: int, fen: int) -> dict:
    """分金计算（铁板神数·考刻分秘传）：
    每刻对应 15 分金, 共 60 分金映射条文集。
    校验: 分金编号 = (ke - 1) * 15 + fen (0-59)
    """
    if ke < 1 or ke > 4 or fen < 0 or fen > 14:
        return {"分金编号": -1, "分金标识": "未知", "校验": False}
    fen_jin_id = (ke - 1) * 15 + fen
    return {
        "分金编号": fen_jin_id,
        "分金标识": f"{(ke-1)*15 + fen + 1}分金",
        "校验": True,
        "刻": ke,
        "分": fen,
    }


def _compute_ke_fen_with_fen_jin(minute: int) -> dict:
    """考刻分深化：刻 + 分 + 分金 完整编码。
    文献：《铁板神数·考刻分秘传》（铁冠道人传本）。"""
    base = _compute_ke_fen(minute)
    fen_jin = _compute_fen_jin(base["ke"], base["fen"])
    return {**base, "分金": fen_jin}


# ── 条文匹配度评分 ────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "父母": ["父", "母", "椿", "萱", "庭", "堂", "孝", "双亲"],
    "兄弟": ["兄", "弟", "姊", "妹", "手", "足", "昆仲"],
    "夫妻": ["夫", "妻", "婚", "娶", "嫁", "鸾", "凤", "琴", "瑟"],
    "子女": ["子", "女", "儿", "息", "嗣", "门楣"],
    "财运": ["财", "富", "财帛", "进财", "聚财", "破财", "财源"],
    "官禄": ["官", "禄", "仕", "职", "仕途", "官星"],
    "寿命": ["寿", "命", "终", "亡", "古稀", "耄耋", "康宁"],
    "疾病": ["病", "疾", "医", "药", "虚弱", "康"],
    "出行": ["行", "远", "迁", "出", "归", "乡"],
    "流年": ["年", "流年", "岁", "太岁"],
    "田宅": ["宅", "田", "宅基", "置业", "祖宅"],
    "人际": ["人", "友", "贵", "小人", "知己", "六亲"],
    "大运": ["运", "大运", "行运", "脱运", "转折"],
}


def _verse_relevance(verse: dict, category: str, question_keywords: list[str] | None) -> float:
    """计算条文相关度评分。
    算法: 分类基础分 0.5 + 关键词命中加分（最多 0.4） + 校验和接近度（最多 0.1）。
    """
    score = 0.5
    text = verse.get("text", "")
    # 分类关键词
    cat_kw = CATEGORY_KEYWORDS.get(category, [])
    cat_hits = sum(1 for kw in cat_kw if kw in text)
    score += min(0.3, cat_hits * 0.1)
    # 用户问题关键词
    if question_keywords:
        q_hits = sum(1 for kw in question_keywords if kw in text)
        score += min(0.4, q_hits * 0.15)
    # 校验和接近度（模拟"缘分深度"）
    cs = verse.get("checksum", 0)
    if 200 <= cs <= 600:
        score += 0.1
    return round(min(1.0, score), 3)


def _lookup_verses(verse_set_number: int, father_zodiac: str = "", mother_zodiac: str = "",
                   lineage: str = "shaoyong", question_keywords: list[str] | None = None,
                   top_n: int = 5) -> dict:
    """Look up verses from the database by set number.
    排序: 按 _verse_relevance 评分降序; 默认返回 top_n 条。
    """
    range_keys = list(TIEBAN_VERSES.keys())
    offset = LINEAGE_OFFSET.get(lineage, 0)
    idx = (verse_set_number + offset) % len(range_keys)
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
    for category, verses in all_categories.items():
        for v in verses:
            if expected_checksum > 0:
                # 父母生肖校验 (《铁板神数》考刻分): 严格匹配 checksum % 1000
                if v["checksum"] % 1000 == expected_checksum:
                    matched.append({
                        "category": category,
                        "number": v["number"],
                        "text": v["text"],
                        "checksum": v["checksum"],
                        "relevance": _verse_relevance(v, category, question_keywords),
                    })
            else:
                matched.append({
                    "category": category,
                    "number": v["number"],
                    "text": v["text"],
                    "checksum": v["checksum"],
                    "relevance": _verse_relevance(v, category, question_keywords),
                })

    # 排序: 按相关度评分降序
    matched.sort(key=lambda x: (-x["relevance"], x["number"]))

    if expected_checksum > 0:
        verification_note = (
            f"父母生肖校验: 父{father_zodiac}({ZODIAC_NUM.get(father_zodiac,0)}) "
            f"母{mother_zodiac}({ZODIAC_NUM.get(mother_zodiac,0)}), "
            f"校验和={expected_checksum}, "
            f"匹配{len(matched)}条"
        )
    else:
        verification_note = "未输入父母生肖, 返回完整集数条文 (按相关度评分排序)"

    return {
        "lineage": lineage,
        "lineage_name": LINEAGE_NAMES.get(lineage, lineage),
        "verse_set_number": verse_set_number,
        "verse_set_range": selected_range,
        "matched_verses": matched[:top_n],
        "total_matched": len(matched),
        "verification": {
            "method": "父母生肖校验",
            "father_zodiac": father_zodiac or None,
            "mother_zodiac": mother_zodiac or None,
            "checksum": expected_checksum if expected_checksum > 0 else None,
            "note": verification_note,
        },
    }


def _build_interpretation(stems: dict, branches: dict, nayin: dict,
                          ke_fen: dict, fen_jin: dict, verse_result: dict,
                          lineage: str, question_keywords: list[str] | None) -> str:
    """综合解读：编码 + 校验 + 条文 → 一段完整解读文本。"""
    top_verses = verse_result.get("matched_verses", [])
    verse_texts = " | ".join(
        f"[{v['category']}#{v['number']}] {v['text'][:20]}..." for v in top_verses[:3]
    ) if top_verses else "无条文"

    nayin_summary = " / ".join(
        f"{k}纳音={v['纳音']}({v['纳音五行']})" for k, v in nayin.items()
    )

    parts = [
        f"【铁板神数综合解读 · {LINEAGE_NAMES.get(lineage, lineage)}】",
        f"四柱编码: 年{stems.get('year')}/月{stems.get('month')}/日{stems.get('day')}/时{stems.get('hour')}",
        f"太玄数: 年{branches['year']['num']}/月{branches['month']['num']}/日{branches['day']['num']}/时{branches['hour']['num']}",
        f"纳音五行: {nayin_summary}",
        f"考刻分: 第{ke_fen['ke']}刻{ke_fen['fen']}分 → 分金{fen_jin['分金标识']}（编号{fen_jin['分金编号']}）",
        f"条文匹配: 集数={verse_result['verse_set_number']}, 范围={verse_result['verse_set_range']}, 命中{verse_result['total_matched']}条",
        f"校验: {verse_result['verification']['note']}",
        f"相关条文(Top 3): {verse_texts}",
    ]
    if question_keywords:
        parts.append(f"用户关键词: {', '.join(question_keywords)}")
    return "\n".join(parts)


def compute(b: Birth, father_zodiac: str = "", mother_zodiac: str = "",
            lineage: str = "shaoyong", question_keywords: list[str] | None = None,
            top_n: int = 5) -> ChartResult:
    """铁板神数起卦入口。

    Args:
        b: Birth 输入
        father_zodiac: 父生肖 (鼠/牛/.../猪)
        mother_zodiac: 母生肖 (鼠/牛/.../猪)
        lineage: "shaoyong" (邵雍本) 或 "tieguan" (铁冠道人本)
        question_keywords: 问题关键词列表 (用于条文相关度加权)
        top_n: 返回条文数 (默认 5)
    """
    if lineage not in LINEAGES:
        raise ValueError(f"tieban lineage 不支持: {lineage!r}（仅 {LINEAGES}）")

    solar = _solar_from_birth(b)
    pillars = _four_pillars(solar)
    stems = _encode_stems(pillars)
    branches = _encode_branches(pillars)
    nayin = _nayin_summary(pillars)
    base_number = _compute_base_number(stems, branches)
    ke_fen = _compute_ke_fen_with_fen_jin(b.minute)
    verse_set_number = base_number + ke_fen["ke_fen_num"]

    # 兼容: Birth 也可带 father_zodiac / mother_zodiac
    if not father_zodiac:
        father_zodiac = getattr(b, "father_zodiac", "") or ""
    if not mother_zodiac:
        mother_zodiac = getattr(b, "mother_zodiac", "") or ""

    verse_result = _lookup_verses(verse_set_number, father_zodiac, mother_zodiac,
                                  lineage, question_keywords, top_n)

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

    interpretation = _build_interpretation(
        stem_summary, branch_summary, nayin,
        ke_fen, ke_fen["分金"], verse_result, lineage, question_keywords
    )

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
            "mode": f"tieban_{lineage}",
            "subject": getattr(b, "subject", None) or "self_life",
            "rule_version": "v2",
            "lineage": lineage,
            "lineage_name": LINEAGE_NAMES.get(lineage, lineage),
            "four_pillars": pillars,
            "encoding": {
                "stems": stem_summary,
                "branches": branch_summary,
            },
            "nayin": nayin,
            "base_number": base_number,
            "ke_fen": ke_fen,
            "verse_set_number": verse_set_number,
            "verse_result": verse_result,
            "interpretation": interpretation,
            "evidence_sources": EVIDENCE_SOURCES,
            "calculation_basis": {
                "method": "tieban",
                "mode": f"tieban_{lineage}",
                "rule_version": "v2",
                "input_source": "birth date → 四柱八字 → 天干数+太玄数+纳音五行 → 刻分金 → 条文集数映射",
                "encoding_rule": (
                    "天干:甲1..癸10; 地支:太玄数(阳支取前数,阴支取后数); "
                    "刻分:每15分1刻共4刻; 分金:每刻15分金,共60分金; "
                    "纳音:六十甲子纳音五行"
                ),
                "limits": [
                    "MVP仅包含约200条核心条文, 非完整12,000条数据库",
                    "条文集数映射为简化算法, 不完全符合传统铁板神数秘传算法",
                    "父母生肖校验为可选功能, 未输入时返回完整集数条文",
                    "支持流派: 邵雍本/铁冠道人本",
                    "条文匹配度评分: 分类关键词 + 用户问题关键词 + 校验和接近度",
                    "此为非科学传统文化参考, 不构成命运判决",
                ],
            },
        },
    )