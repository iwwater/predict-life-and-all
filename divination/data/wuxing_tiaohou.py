"""八字调候 (Seasonal Adjustment) — 穷通宝鉴体系。

调候是八字用神选取的核心原则之一，源自《穷通宝鉴》(又名《栏江网》)。
核心思想: 日主生于不同月份，需要不同的五行元素来调节气候，使命局趋于中和。

调候五原则:
  1. 寒木向阳 — 冬春之木需火暖局
  2. 暑木要润 — 夏木需水滋润
  3. 金旺克木需火制 — 秋木需火制金护木
  4. 燥土要润 — 燥土需水润泽
  5. 寒金要暖 — 冬金需火暖局

数据来源: 《穷通宝鉴》(明·余春台 著, 清·任铁樵 注)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ══════════════════════════════════════════════════════════════
# 1. 调候规则数据类
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TiaohouRule:
    """单条调候规则 — 穷通宝鉴体系。

    Attributes:
        day_gan: 日干 (甲-癸)
        month_zhi: 月支 (子-亥)
        primary_use: 第一用神 / 调候用神 (五行元素)
        secondary_use: 第二用神 / 喜神 (五行元素)
        rationale: 调候原理说明
        source: 文献出处
    """
    day_gan: str
    month_zhi: str
    primary_use: str
    secondary_use: str
    rationale: str
    source: str = "《穷通宝鉴》"


# ══════════════════════════════════════════════════════════════
# 2. 调候速查表 (60 条核心规则)
# ══════════════════════════════════════════════════════════════

TIAOHOU_TABLE: dict[tuple[str, str], TiaohouRule] = {
    # ── 甲木 ──
    ("甲", "寅"): TiaohouRule(
        day_gan="甲", month_zhi="寅",
        primary_use="火", secondary_use="水",
        rationale="正月甲木,春寒未尽,寒木向阳,先用丙火解冻,次用癸水润根。丙癸双透,富贵之命。",
    ),
    ("甲", "卯"): TiaohouRule(
        day_gan="甲", month_zhi="卯",
        primary_use="火", secondary_use="水",
        rationale="二月甲木,阳和日暖,丙火为尊,癸水为辅。木气已旺,不宜再见水多。",
    ),
    ("甲", "午"): TiaohouRule(
        day_gan="甲", month_zhi="午",
        primary_use="水", secondary_use="金",
        rationale="五月甲木,火旺木焚,先用壬癸水调候润木,次用庚金发水源。无水火则木枯。",
    ),
    ("甲", "未"): TiaohouRule(
        day_gan="甲", month_zhi="未",
        primary_use="水", secondary_use="金",
        rationale="六月甲木,三伏火旺,先用壬水,次取庚金。庚壬两透,科甲有准。",
    ),
    ("甲", "申"): TiaohouRule(
        day_gan="甲", month_zhi="申",
        primary_use="火", secondary_use="水",
        rationale="七月甲木,金旺乘权,先用丁火制金,次用壬水泄金。丁壬合化,贵格也。",
    ),
    ("甲", "酉"): TiaohouRule(
        day_gan="甲", month_zhi="酉",
        primary_use="火", secondary_use="金",
        rationale="八月甲木,金锐木凋,用丁火制金,配合少许庚金劈甲引丁。丁火为急。",
    ),
    ("甲", "亥"): TiaohouRule(
        day_gan="甲", month_zhi="亥",
        primary_use="火", secondary_use="土",
        rationale="十月甲木,亥中藏壬,水旺木漂,先用戊土制水,次用丙火暖局。水冷木寒,非火不发。",
    ),
    ("甲", "子"): TiaohouRule(
        day_gan="甲", month_zhi="子",
        primary_use="火", secondary_use="土",
        rationale="十一月甲木,冬至阳生,木性归垣,先用丙火解冻,次用戊土制水。丙戊双透,富贵双全。",
    ),
    ("甲", "丑"): TiaohouRule(
        day_gan="甲", month_zhi="丑",
        primary_use="火", secondary_use="土",
        rationale="十二月甲木,天寒地冻,丙火为尊,戊土为辅。丙火解冻,戊土制寒,方成栋梁。",
    ),

    # ── 乙木 ──
    ("乙", "寅"): TiaohouRule(
        day_gan="乙", month_zhi="寅",
        primary_use="火", secondary_use="水",
        rationale="正月乙木,取丙火解寒,癸水润根。丙癸两透,科甲之命。乙木柔韧,不宜金克太过。",
    ),
    ("乙", "卯"): TiaohouRule(
        day_gan="乙", month_zhi="卯",
        primary_use="水", secondary_use="金",
        rationale="二月乙木,阳气渐升,专用癸水润木,少许辛金修剪。水多则木漂,金多则木伤。",
    ),
    ("乙", "午"): TiaohouRule(
        day_gan="乙", month_zhi="午",
        primary_use="水", secondary_use="金",
        rationale="五月乙木,火旺木枯,取壬癸水解炎润木,庚金发源。夏木无水,必主孤贫。",
    ),
    ("乙", "申"): TiaohouRule(
        day_gan="乙", month_zhi="申",
        primary_use="火", secondary_use="水",
        rationale="七月乙木,庚金司权,用丙火制金,癸水泄金润木。丙癸双备,方可言贵。",
    ),
    ("乙", "酉"): TiaohouRule(
        day_gan="乙", month_zhi="酉",
        primary_use="火", secondary_use="水",
        rationale="八月乙木,辛金七杀当令,先用丙丁火制杀,次用癸水润木。无火则木被金伤。",
    ),
    ("乙", "亥"): TiaohouRule(
        day_gan="乙", month_zhi="亥",
        primary_use="火", secondary_use="土",
        rationale="十月乙木,水冷木寒,以丙火为尊,戊土为辅。寒木得火而敷荣。",
    ),
    ("乙", "子"): TiaohouRule(
        day_gan="乙", month_zhi="子",
        primary_use="火", secondary_use="土",
        rationale="十一月乙木,虽冬至一阳生,然木性至柔,需丙火暖局。寒谷回春,全赖丙火。",
    ),

    # ── 丙火 ──
    ("丙", "寅"): TiaohouRule(
        day_gan="丙", month_zhi="寅",
        primary_use="木", secondary_use="水",
        rationale="正月丙火,寅中甲木当权,火得木生,先用壬水调剂,庚金为佐。壬庚两透,贵格。",
    ),
    ("丙", "卯"): TiaohouRule(
        day_gan="丙", month_zhi="卯",
        primary_use="木", secondary_use="水",
        rationale="二月丙火,阳气渐升,专用壬水。壬水为丙火之君,水火既济,功名显达。",
    ),
    ("丙", "午"): TiaohouRule(
        day_gan="丙", month_zhi="午",
        primary_use="水", secondary_use="金",
        rationale="五月丙火,阳刃当令,火势炎炎,非壬水不能解炎。壬庚并透,富贵极品。",
    ),
    ("丙", "未"): TiaohouRule(
        day_gan="丙", month_zhi="未",
        primary_use="水", secondary_use="金",
        rationale="六月丙火,余炎未退,仍用壬水。大暑后用壬,小暑前庚壬并行。",
    ),
    ("丙", "申"): TiaohouRule(
        day_gan="丙", month_zhi="申",
        primary_use="木", secondary_use="水",
        rationale="七月丙火,金旺火衰,用甲木生火,壬水为辅。甲木为丙火之母,母旺子强。",
    ),
    ("丙", "亥"): TiaohouRule(
        day_gan="丙", month_zhi="亥",
        primary_use="木", secondary_use="火",
        rationale="十月丙火,水旺火绝,以甲木生火为急,次用戊土制水。甲戊并透,贵显。",
    ),
    ("丙", "子"): TiaohouRule(
        day_gan="丙", month_zhi="子",
        primary_use="木", secondary_use="火",
        rationale="十一月丙火,冬至一阳生,子中癸水乘权,先用甲木化水,次用丙火助日。",
    ),

    # ── 丁火 ──
    ("丁", "寅"): TiaohouRule(
        day_gan="丁", month_zhi="寅",
        primary_use="金", secondary_use="木",
        rationale="正月丁火,甲木当权,庚金劈甲引丁,方成燎原之势。庚甲两透,科甲无疑。",
    ),
    ("丁", "卯"): TiaohouRule(
        day_gan="丁", month_zhi="卯",
        primary_use="金", secondary_use="木",
        rationale="二月丁火,乙木司令,仍用庚金劈乙引丁。庚甲齐备,功名显达。",
    ),
    ("丁", "午"): TiaohouRule(
        day_gan="丁", month_zhi="午",
        primary_use="水", secondary_use="金",
        rationale="五月丁火,建禄之地,火势猛烈,专用壬水。壬庚并透,水火既济。",
    ),
    ("丁", "申"): TiaohouRule(
        day_gan="丁", month_zhi="申",
        primary_use="木", secondary_use="金",
        rationale="七月丁火,金旺火衰,用甲木生丁火,庚金劈甲。退气之火,不离甲庚。",
    ),
    ("丁", "亥"): TiaohouRule(
        day_gan="丁", month_zhi="亥",
        primary_use="木", secondary_use="金",
        rationale="十月丁火,水旺火绝,以甲木引丁为急,庚金劈甲为佐。甲庚两全,富贵之命。",
    ),
    ("丁", "子"): TiaohouRule(
        day_gan="丁", month_zhi="子",
        primary_use="木", secondary_use="金",
        rationale="十一月丁火,癸水当令,最喜甲木化水引火。庚金劈甲,方能有用。",
    ),

    # ── 戊土 ──
    ("戊", "寅"): TiaohouRule(
        day_gan="戊", month_zhi="寅",
        primary_use="火", secondary_use="木",
        rationale="正月戊土,春寒未尽,先用丙火暖土,次用甲木疏土,癸水润泽。丙甲癸三字全,富贵极品。",
    ),
    ("戊", "卯"): TiaohouRule(
        day_gan="戊", month_zhi="卯",
        primary_use="火", secondary_use="木",
        rationale="二月戊土,仍用丙火暖土,甲木疏土。无丙则土寒不发,无甲则土实不灵。",
    ),
    ("戊", "午"): TiaohouRule(
        day_gan="戊", month_zhi="午",
        primary_use="水", secondary_use="金",
        rationale="五月戊土,火旺土燥,先用壬水解炎润土,次用庚金生水。夏土燥烈,非水不滋。",
    ),
    ("戊", "申"): TiaohouRule(
        day_gan="戊", month_zhi="申",
        primary_use="火", secondary_use="水",
        rationale="七月戊土,金旺泄土,用丙火生土,癸水润金。金旺土虚,不离丙癸。",
    ),
    ("戊", "亥"): TiaohouRule(
        day_gan="戊", month_zhi="亥",
        primary_use="火", secondary_use="木",
        rationale="十月戊土,水旺土寒,先用丙火暖土,次用甲木疏土。非丙不暖,非甲不灵。",
    ),
    ("戊", "子"): TiaohouRule(
        day_gan="戊", month_zhi="子",
        primary_use="火", secondary_use="木",
        rationale="十一月戊土,水冷土冻,以丙火为尊,甲木为佐。寒土向阳,方可生物。",
    ),

    # ── 己土 ──
    ("己", "寅"): TiaohouRule(
        day_gan="己", month_zhi="寅",
        primary_use="火", secondary_use="水",
        rationale="正月己土,取丙火解冻,癸水润土。丙癸双透,贵气自成。己土卑湿,不宜木多。",
    ),
    ("己", "卯"): TiaohouRule(
        day_gan="己", month_zhi="卯",
        primary_use="火", secondary_use="水",
        rationale="二月己土,春木正旺,先用丙火化木,癸水润土。无丙则木克土伤。",
    ),
    ("己", "午"): TiaohouRule(
        day_gan="己", month_zhi="午",
        primary_use="水", secondary_use="火",
        rationale="五月己土,火炎土燥,专用癸水润土。癸丙并行,水火相济。夏土无水则不生物。",
    ),
    ("己", "申"): TiaohouRule(
        day_gan="己", month_zhi="申",
        primary_use="火", secondary_use="水",
        rationale="七月己土,金旺泄土,用丙火生土,癸水润泽。丙癸双用,方成稼穑之功。",
    ),
    ("己", "亥"): TiaohouRule(
        day_gan="己", month_zhi="亥",
        primary_use="火", secondary_use="木",
        rationale="十月己土,水旺土流,先用丙火暖土,次用甲木疏土。丙火为先,否则水冷土寒。",
    ),
    ("己", "子"): TiaohouRule(
        day_gan="己", month_zhi="子",
        primary_use="火", secondary_use="木",
        rationale="十一月己土,天寒地冻,丙火为尊,甲木为佐。火暖土温,方有生机。",
    ),

    # ── 庚金 ──
    ("庚", "寅"): TiaohouRule(
        day_gan="庚", month_zhi="寅",
        primary_use="火", secondary_use="土",
        rationale="正月庚金,余寒未尽,先用丙火暖金,次用戊土生金。丙戊双透,贵气不凡。",
    ),
    ("庚", "卯"): TiaohouRule(
        day_gan="庚", month_zhi="卯",
        primary_use="火", secondary_use="土",
        rationale="二月庚金,卯中乙木当令,财旺身弱,用丁火、戊土。丁火暖局,戊土生金。",
    ),
    ("庚", "午"): TiaohouRule(
        day_gan="庚", month_zhi="午",
        primary_use="水", secondary_use="土",
        rationale="五月庚金,火旺金熔,先用壬水解炎,次用己土护金。无壬则金被火伤。",
    ),
    ("庚", "酉"): TiaohouRule(
        day_gan="庚", month_zhi="酉",
        primary_use="火", secondary_use="木",
        rationale="八月庚金,阳刃当令,金锐太过,用丁火、甲木。丁火炼金,甲木引丁。",
    ),
    ("庚", "亥"): TiaohouRule(
        day_gan="庚", month_zhi="亥",
        primary_use="火", secondary_use="土",
        rationale="十月庚金,水冷金寒,先用丙火暖局,次用戊土制水生金。水冷金寒,非火不发。",
    ),
    ("庚", "子"): TiaohouRule(
        day_gan="庚", month_zhi="子",
        primary_use="火", secondary_use="土",
        rationale="十一月庚金,水旺金沉,丙火为急,戊土为佐。丙戊齐透,方能显贵。",
    ),
    ("庚", "丑"): TiaohouRule(
        day_gan="庚", month_zhi="丑",
        primary_use="火", secondary_use="土",
        rationale="十二月庚金,寒金喜暖,丙火优先,丁火为次,更喜戊土生金。金寒水冷,无火不贵。",
    ),

    # ── 辛金 ──
    ("辛", "寅"): TiaohouRule(
        day_gan="辛", month_zhi="寅",
        primary_use="土", secondary_use="水",
        rationale="正月辛金,木旺金衰,先用己土生金,次用壬水淘洗。己壬两透,珠玉生辉。",
    ),
    ("辛", "午"): TiaohouRule(
        day_gan="辛", month_zhi="午",
        primary_use="水", secondary_use="木",
        rationale="五月辛金,火旺金熔,专用壬水解炎护金,次用甲木生火(制水太过)。辛金柔弱,忌火太多。",
    ),
    ("辛", "申"): TiaohouRule(
        day_gan="辛", month_zhi="申",
        primary_use="水", secondary_use="木",
        rationale="七月辛金,庚金当令,金旺宜泄,用壬水泄金之气,甲木为佐。辛金喜壬淘洗,珠玉增辉。",
    ),
    ("辛", "酉"): TiaohouRule(
        day_gan="辛", month_zhi="酉",
        primary_use="水", secondary_use="木",
        rationale="八月辛金,建禄当令,仍用壬水泄金,甲木为佐。金白水清,文章冠世。",
    ),
    ("辛", "亥"): TiaohouRule(
        day_gan="辛", month_zhi="亥",
        primary_use="火", secondary_use="水",
        rationale="十月辛金,水旺金沉,先用丙火暖局,次用壬水淘洗。丙火调候,壬水洗金,相得益彰。",
    ),
    ("辛", "子"): TiaohouRule(
        day_gan="辛", month_zhi="子",
        primary_use="火", secondary_use="水",
        rationale="十一月辛金,金寒水冷,丙火为尊,戊土为次。寒金喜暖,火土并用方成贵格。",
    ),

    # ── 壬水 ──
    ("壬", "寅"): TiaohouRule(
        day_gan="壬", month_zhi="寅",
        primary_use="金", secondary_use="土",
        rationale="正月壬水,春水泛滥,先用庚金发源,次用戊土为堤。庚戊两透,功名显达。",
    ),
    ("壬", "午"): TiaohouRule(
        day_gan="壬", month_zhi="午",
        primary_use="金", secondary_use="水",
        rationale="五月壬水,火旺水涸,先用庚金生水之源,次用癸水助身。夏水干涸,无庚金发源必涸。",
    ),
    ("壬", "申"): TiaohouRule(
        day_gan="壬", month_zhi="申",
        primary_use="土", secondary_use="金",
        rationale="七月壬水,庚金司权,水源充沛,用戊土为堤防,辛金为辅。水势浩大,需土制之。",
    ),
    ("壬", "亥"): TiaohouRule(
        day_gan="壬", month_zhi="亥",
        primary_use="土", secondary_use="火",
        rationale="十月壬水,建禄当令,水势汪洋,先用戊土为堤,次用丙火暖局。戊丙双透,富贵可期。",
    ),
    ("壬", "子"): TiaohouRule(
        day_gan="壬", month_zhi="子",
        primary_use="土", secondary_use="火",
        rationale="十一月壬水,阳刃当令,水势滔天,戊土制水为先,丙火暖局为次。水冷宜火,水旺宜土。",
    ),
    ("壬", "丑"): TiaohouRule(
        day_gan="壬", month_zhi="丑",
        primary_use="火", secondary_use="土",
        rationale="十二月壬水,水冷土冻,先用丙火解冻,次用戊土制水。丑中己土为堤,丙火暖之则固。",
    ),

    # ── 癸水 ──
    ("癸", "寅"): TiaohouRule(
        day_gan="癸", month_zhi="寅",
        primary_use="金", secondary_use="火",
        rationale="正月癸水,春水至弱,先用辛金发源,次用丙火暖局。辛丙两透,方可言贵。",
    ),
    ("癸", "午"): TiaohouRule(
        day_gan="癸", month_zhi="午",
        primary_use="金", secondary_use="金",
        rationale="五月癸水,火旺水绝,专用庚辛金发源。庚金生水,辛金助之。夏水干涸,非金不生。",
    ),
    ("癸", "申"): TiaohouRule(
        day_gan="癸", month_zhi="申",
        primary_use="金", secondary_use="火",
        rationale="七月癸水,金旺水相,用辛金发源,丙火调候。辛为癸水之母,丙火为调候之需。",
    ),
    ("癸", "亥"): TiaohouRule(
        day_gan="癸", month_zhi="亥",
        primary_use="火", secondary_use="土",
        rationale="十月癸水,建禄当令,水旺用丙火暖局,戊土制水。丙火调候,戊土筑堤,相得益彰。",
    ),
    ("癸", "子"): TiaohouRule(
        day_gan="癸", month_zhi="子",
        primary_use="火", secondary_use="火",
        rationale="十一月癸水,禄旺之地,天寒地冻,专用丙丁火暖局。丙火太阳,丁火灯烛,火多不怕。",
    ),
    ("癸", "丑"): TiaohouRule(
        day_gan="癸", month_zhi="丑",
        primary_use="火", secondary_use="土",
        rationale="十二月癸水,水寒土冻,丙火解冻为先,戊土制水为次。丑为寒土,非火不暖。",
    ),
}


# ══════════════════════════════════════════════════════════════
# 3. 公共函数
# ══════════════════════════════════════════════════════════════

_WX_ZH_TO_EN: dict[str, str] = {
    "木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water",
}


def evaluate_tiaohou(day_gan: str, month_zhi: str) -> Optional[dict]:
    """查询指定日干月支的调候规则。

    Args:
        day_gan: 日干 (甲-癸)
        month_zhi: 月支 (子-亥)

    Returns:
        dict with rule fields, or None if no rule found.
    """
    key = (day_gan, month_zhi)
    rule = TIAOHOU_TABLE.get(key)
    if rule is None:
        return None
    return {
        "day_gan": rule.day_gan,
        "month_zhi": rule.month_zhi,
        "primary_use": rule.primary_use,
        "primary_use_en": _WX_ZH_TO_EN.get(rule.primary_use, ""),
        "secondary_use": rule.secondary_use,
        "secondary_use_en": _WX_ZH_TO_EN.get(rule.secondary_use, ""),
        "rationale": rule.rationale,
        "source": rule.source,
    }


def get_tiaohou_advice(day_gan: str, month_zhi: str) -> dict:
    """获取结构化的调候建议。

    除基础规则外,额外提供五行元素层面的推荐与解读。

    Args:
        day_gan: 日干 (甲-癸)
        month_zhi: 月支 (子-亥)

    Returns:
        dict with advice fields including element recommendations.
    """
    tiaohou = evaluate_tiaohou(day_gan, month_zhi)

    if tiaohou is None:
        return {
            "has_rule": False,
            "message": f"日干{day_gan}生于{month_zhi}月,暂无调候规则记载。",
            "primary_element": None,
            "secondary_element": None,
            "advice_summary": "建议参考日主强弱结合月令取用。",
        }

    return {
        "has_rule": True,
        "day_gan": day_gan,
        "month_zhi": month_zhi,
        "primary_element": tiaohou["primary_use"],
        "primary_element_en": tiaohou["primary_use_en"],
        "secondary_element": tiaohou["secondary_use"],
        "secondary_element_en": tiaohou["secondary_use_en"],
        "rationale": tiaohou["rationale"],
        "source": tiaohou["source"],
        "advice_summary": (
            f"日干{day_gan}生于{month_zhi}月,调候以{tiaohou['primary_use']}为第一用神,"
            f"{tiaohou['secondary_use']}为喜神。{tiaohou['rationale']}"
        ),
    }
