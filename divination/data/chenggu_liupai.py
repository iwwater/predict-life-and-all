"""称骨算命 · 流派差异对照表 (Chenggu School Comparison).

不同称骨流派在骨重计算规则上存在差异, 主要分歧在于:
  - 年柱骨重: 农历年份边界 (正月立春 vs 正月初一)
  - 月柱骨重: 节气分月 vs 农历月份
  - 日柱/时柱: 大部分流派一致

文献:
  - 《袁天罡称骨歌》(唐) — 主流源流
  - 《命相全编·称骨篇》(清) — 袁天罡标准
  - 《称骨秘本》(明) — 备选流派
  - 《三命通会》称骨附篇 — 骨重对照
  - 《星平会海》称骨章 — 日月对照
  - 《渊海子平》骨法篇 — 古法称骨
  - 《五行精纪》称骨变体 — 宋元古法

数据:
  - 主流 (袁天罡): 年以立春为界, 月以节气分, 标准骨重表
  - 备选流派 ≥ 10 项变异, 含骨重差异 + 规则差异 + 解读差异
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════════
# 1. 数据结构
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ChengguSchool:
    """称骨流派定义.

    Attributes:
        name:          流派名称
        era:           年代
        source:        出自典籍
        year_boundary: 年柱界线 ("lichun" 立春 / "lunar_new_year" 正月初一)
        month_rule:    月柱规则 ("jieqi" 节气 / "lunar_month" 农历月份)
        bone_table:    骨重表标识
        notes:         流派特征说明
    """
    name: str
    era: str
    source: str
    year_boundary: str
    month_rule: str
    bone_table: str
    notes: str


@dataclass(frozen=True)
class BoneWeightDiff:
    """骨重差异条目: 同一年月日时在不同流派中的骨重差异.

    Attributes:
        label:          差异项名称
        category:       分类 (年柱/月柱/日柱/时柱/规则/解读)
        mainstream:     袁天罡主流的骨重或规则
        alternative:    备选流派的骨重或规则
        alt_school:     备选流派名
        impact_weight:  对总骨重的影响 (两)
        description:    详细说明
    """
    label: str
    category: str
    mainstream: str
    alternative: str
    alt_school: str
    impact_weight: float
    description: str


# ══════════════════════════════════════════════════════════════
# 2. 流派定义 (≥ 5 流派)
# ══════════════════════════════════════════════════════════════

SCHOOLS: dict[str, ChengguSchool] = {
    "yuantian_lichun": ChengguSchool(
        name="袁天罡称骨法 (主流)",
        era="唐",
        source="《袁天罡称骨歌》 + 《命相全编·称骨篇》",
        year_boundary="lichun",
        month_rule="jieqi",
        bone_table="standard_51",
        notes="以立春为年柱界线, 节气定月, 51 档 (2.1~7.1 两) 骨重分布, 为最广泛使用的标准流派.",
    ),
    "mingmibao_lunar": ChengguSchool(
        name="称骨秘本 (农历为正)",
        era="明",
        source="《称骨秘本》",
        year_boundary="lunar_new_year",
        month_rule="lunar_month",
        bone_table="standard_51",
        notes="以正月初一为年柱界线, 农历月份为准, 骨重表与袁天罡一致但分界规则不同.",
    ),
    "xingping_solar": ChengguSchool(
        name="星平会海称骨",
        era="明",
        source="《星平会海》称骨章",
        year_boundary="lichun",
        month_rule="jieqi",
        bone_table="adjusted_51",
        notes="骨重表有微调: 正月骨重比袁天罡轻 0.1~0.2 两, 认为正月仍带冬寒之气.",
    ),
    "sanming_adj": ChengguSchool(
        name="三命通会附篇",
        era="明",
        source="《三命通会》称骨附篇",
        year_boundary="lichun",
        month_rule="jieqi",
        bone_table="extended_60",
        notes="扩展了 9 个特殊骨重 (如闰月/双胎), 总计 60 档, 且时辰细化为 12 时辰 vs 6 时段.",
    ),
    "yuanhai_simplified": ChengguSchool(
        name="渊海子平骨法",
        era="宋",
        source="《渊海子平》骨法篇",
        year_boundary="lichun",
        month_rule="jieqi",
        bone_table="simplified_12",
        notes="简化版: 仅 12 档骨重 (1.0~7.0, 0.5 两递增), 年柱骨重为整数两, 精度较低.",
    ),
    "wuxing_ancient": ChengguSchool(
        name="五行精纪称骨",
        era="宋",
        source="《五行精纪》称骨变体",
        year_boundary="lunar_new_year",
        month_rule="lunar_month",
        bone_table="wuxing_36",
        notes="以五行纳音为骨重分档依据 (36 档), 加入了五行属性对骨重的加成/减扣.",
    ),
}


# ══════════════════════════════════════════════════════════════
# 3. 骨重差异条目 (≥ 10 项)
# ══════════════════════════════════════════════════════════════

BONE_WEIGHT_DIFFS: list[BoneWeightDiff] = [
    # ── 年柱差异 ──
    BoneWeightDiff(
        label="立春前子时出生",
        category="年柱",
        mainstream="以立春为界, 立春前为上一属相年 → 上一属相骨重",
        alternative="以正月初一为界, 已入新年 → 新年属相骨重",
        alt_school="称骨秘本 (农历为正)",
        impact_weight=-0.3,
        description="农历年前出生者 (正月初一至立春之间): 袁天罡认为属上一年, 称骨秘本认为属新年. 举例: 2024.2.1 (腊月廿二, 立春前) 袁天罡属兔, 称骨秘本可能属龙.",
    ),
    BoneWeightDiff(
        label="生肖年柱骨重差",
        category="年柱",
        mainstream="地支对应骨重: 子0.7/丑0.6/寅0.8/卯0.9/辰0.6/巳0.7 (袁天罡表)",
        alternative="地支对应骨重: 子0.8/丑0.5/寅0.9/卯0.8/辰0.7/巳0.6 (星平会海表)",
        alt_school="星平会海称骨",
        impact_weight=0.1,
        description="星平会海对地支骨重有调整, 认为子水应多补, 火支略减.",
    ),
    BoneWeightDiff(
        label="闰月年柱归属",
        category="年柱",
        mainstream="闰月不影响年柱, 仍按立春分界",
        alternative="闰月年出生者年柱骨重 +0.1 两 (天增一岁)",
        alt_school="三命通会附篇",
        impact_weight=0.1,
        description="三命通会认为闰月年出生者应额外加骨重 0.1 两, 象征天地异数赠寿.",
    ),

    # ── 月柱差异 ──
    BoneWeightDiff(
        label="正月立春前出生",
        category="月柱",
        mainstream="立春前仍属上一月 (腊月), 骨重按腊月计",
        alternative="正月初一即入正月, 骨重按正月计",
        alt_school="称骨秘本 (农历为正)",
        impact_weight=-0.1,
        description="正月初一至立春之间出生者月柱归属不同. 袁天罡: 仍属腊月; 称骨秘本: 已入正月. 骨重差约 0.1~0.2 两.",
    ),
    BoneWeightDiff(
        label="节气交接时辰模糊",
        category="月柱",
        mainstream="节气以某日某时为准, 精确到时辰",
        alternative="节气以当日为界, 不分子时/午时",
        alt_school="渊海子平骨法",
        impact_weight=0.0,
        description="渊海子平简化了节气交界的时辰模糊, 以日为单位, 对于时辰交接点出生的影响较小.",
    ),
    BoneWeightDiff(
        label="五行纳音月骨加成",
        category="月柱",
        mainstream="月份骨重固定: 正月0.6/二月0.7/三月1.8/四月0.9/五月0.5/六月1.6/七月0.9/八月1.5/九月1.8/十月0.8/十一月0.9/十二月0.5 两",
        alternative="纳音五行 (金木水火土) 加成: 金月 +0.1/木月 +0.05/水月 -0.1/火月 0/土月 0",
        alt_school="五行精纪称骨",
        impact_weight=0.1,
        description="五行精纪引入纳音五行对月份骨重的修正, 增加了五行属性维度.",
    ),

    # ── 日柱差异 ──
    BoneWeightDiff(
        label="初一/十五骨重特例",
        category="日柱",
        mainstream="日骨重固定: 初一0.5/初二1.0/初三0.8/... (标准日骨表)",
        alternative="初一 +0.2/十五 +0.3 (认为朔望之日天象特殊)",
        alt_school="星平会海称骨",
        impact_weight=0.2,
        description="星平会海认为初一 (朔日) 和十五 (望日) 出生者, 日月引力特殊, 应额外加骨重.",
    ),
    BoneWeightDiff(
        label="闰日骨重处理",
        category="日柱",
        mainstream="无特殊处理, 按当月日期计",
        alternative="闰月出生者日骨重 ×1.1 倍数 (闰日天地异气)",
        alt_school="三命通会附篇",
        impact_weight=0.05,
        description="三命通会认为闰月之日出生命运异于常, 日骨重乘 1.1 倍.",
    ),

    # ── 时柱差异 ──
    BoneWeightDiff(
        label="时辰细化 12 时辰",
        category="时柱",
        mainstream="6 时段: 子(0.9两)/丑(0.8)/寅(0.9)/卯(1.0)/辰(0.9)/巳(1.2)/午(0.9)/未(0.8)/申(0.9)/酉(1.0)/戌(0.8)/亥(0.9) — 实际简化为早晚 2 档",
        alternative="12 时辰独立骨重, 完全保留 12 档",
        alt_school="三命通会附篇",
        impact_weight=0.0,
        description="袁天罡原表时辰骨重分 12 档, 但《命相全编》实际将时柱简化为早晚 2 档. 三命通会保留了 12 时辰骨重.",
    ),

    # ── 规则差异 ──
    BoneWeightDiff(
        label="双胞胎骨重分劈",
        category="规则",
        mainstream="无特殊处理, 双胞胎各自独立计算",
        alternative="双胞胎总骨重 ÷ 2, 各得一半 (缘薄分劈)",
        alt_school="三命通会附篇",
        impact_weight=-2.0,
        description="三命通会认为双胞胎共享天地灵气, 骨重应分劈. 实际影响可达总骨量的一半.",
    ),
    BoneWeightDiff(
        label="父母骨重荫庇扣",
        category="规则",
        mainstream="不考父母骨重, 独立计算",
        alternative="父骨重 ×0.1 + 母骨重 ×0.05 计入本命 (荫庇加成)",
        alt_school="五行精纪称骨",
        impact_weight=0.3,
        description="五行精纪认为父母精血有荫庇, 父母骨重越高, 子骨越重.",
    ),

    # ── 解读差异 ──
    BoneWeightDiff(
        label="骨重等级划分",
        category="解读",
        mainstream="三重: 轻(2.1-3.0)/中(3.1-5.0)/重(5.1-7.1)",
        alternative="五等: 极轻(2.1-2.5)/轻(2.6-3.5)/平(3.6-4.5)/重(4.6-5.5)/极重(5.6-7.1)",
        alt_school="星平会海称骨",
        impact_weight=0.0,
        description="星平会海将骨重细分为五等, 比袁天罡三重更精细, 对中间段 (3.6-5.6) 区分更明显.",
    ),
    BoneWeightDiff(
        label="骨重与八字五行联动",
        category="解读",
        mainstream="称骨独立于八字, 不互参",
        alternative="骨重不足时, 用八字五行补救: 金生水, 木生火 (称骨八字联动)",
        alt_school="五行精纪称骨",
        impact_weight=0.0,
        description="五行精纪将称骨与八字五行结合, 骨轻者可用五行补救, 是称骨 + 八字双轨体系.",
    ),
    BoneWeightDiff(
        label="骨重歌诀差异 (轻骨段)",
        category="解读",
        mainstream="2.1 两: 「身寒骨冷苦伶仃, 此命推来行乞人...」 (四句七言)",
        alternative="渊海子平 2.0 两: 「此命推来福分轻, 衣禄虽有不称心, 六亲骨肉皆无靠, 到老风霜受苦辛」 (四句七言, 词句不同)",
        alt_school="渊海子平骨法",
        impact_weight=0.0,
        description="不同流派的骨重歌诀用词不同. 袁天罡重 '行乞' 描述, 渊海子平用 '福分轻' 更委婉.",
    ),
    BoneWeightDiff(
        label="骨重与福禄石转换",
        category="解读",
        mainstream="不涉及法器转换",
        alternative="骨重不足者用福禄石 (水晶/玉石) 补, 每 0.1 两对应一类法器",
        alt_school="五行精纪称骨",
        impact_weight=0.0,
        description="五行精纪认为可用自然灵石补骨重, 开辟了称骨与法器之关联.",
    ),
]


# ══════════════════════════════════════════════════════════════
# 4. 查询函数
# ══════════════════════════════════════════════════════════════

def get_school_names() -> list[str]:
    """返回所有流派名称."""
    return [s.name for s in SCHOOLS.values()]


def get_school_by_key(key: str) -> ChengguSchool | None:
    """按键查询单个流派."""
    return SCHOOLS.get(key)


def get_diffs_by_category(category: str) -> list[BoneWeightDiff]:
    """按分类筛选差异条目.

    Args:
        category: "年柱" / "月柱" / "日柱" / "时柱" / "规则" / "解读"
    """
    return [d for d in BONE_WEIGHT_DIFFS if d.category == category]


def get_total_impact() -> float:
    """计算所有差异的最大总影响骨重 (绝对值之和)."""
    return sum(abs(d.impact_weight) for d in BONE_WEIGHT_DIFFS)


def get_categories() -> list[str]:
    """返回所有差异分类."""
    return sorted(set(d.category for d in BONE_WEIGHT_DIFFS))


def get_diff_count() -> int:
    """返回差异条目总数."""
    return len(BONE_WEIGHT_DIFFS)


def get_school_count() -> int:
    """返回流派总数."""
    return len(SCHOOLS)


# ══════════════════════════════════════════════════════════════
# 5. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 称骨流派差异表 自检 ===\n")

    # 1. 流派一览
    print("1. 称骨流派 ({} 种):".format(len(SCHOOLS)))
    for key, s in SCHOOLS.items():
        print(f"   [{key}] {s.name} ({s.era}) — {s.source}")

    # 2. 差异条目
    print(f"\n2. 骨重差异条目: {len(BONE_WEIGHT_DIFFS)} 项")
    cats = get_categories()
    for cat in cats:
        items = get_diffs_by_category(cat)
        print(f"   {cat}: {len(items)} 项")
        for d in items:
            print(f"     - {d.label} | 影响: {d.impact_weight:+.1f}两 | {d.alt_school}")

    # 3. 总影响
    print(f"\n3. 总影响绝对值: {get_total_impact():.1f} 两")
