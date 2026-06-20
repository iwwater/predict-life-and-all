"""小六壬数字课经 — 多数字组合课式判定规则。

文献依据:
  - 《小六壬课经》(佚名·民间传承) — 核心课式分类
  - 《六壬金口诀》(明·佚名) — 数字五行配法
  - 《易数钩隐图》(宋·刘牧) — 数理依据
  - 《三才图会》(明·王圻) — 天地人数配

数据驱动设计:
  1. NumberKeRule: 不可变 dataclass, 含 rule_id/name/category/condition/interpretation/tone/advice/source
  2. NUMBER_KE_RULES: 15 条规则列表, 覆盖 5 大分类
  3. evaluate_number_rules(): 遍历所有规则, 返回匹配的规则列表
  4. get_number_wuxing(): 三数五行分布

分类:
  - 三传数字模式: 顺数/逆数/三数相同 (3 rules)
  - 五行属性模式: 三木/三火/三金/三水 (4 rules)
  - 奇偶组合: 三奇/三偶/两奇一偶 (3 rules)
  - 大小组合: 全大数/全小数/大中小分布 (3 rules)
  - 特殊数: 含7/含9 (2 rules)
"""

from __future__ import annotations

from dataclasses import dataclass

# ══════════════════════════════════════════════════════════════
# 1. NumberKeRule 数据契约
# ══════════════════════════════════════════════════════════════

WUXING_MAP: dict[int, str] = {0: "水", 1: "木", 2: "火", 3: "土", 4: "金"}


@dataclass(frozen=True)
class NumberKeRule:
    """小六壬数字课经规则 (不可变, 数据驱动).

    Attributes:
        rule_id: 唯一标识 (snake_case).
        name: 规则中文名.
        category: 分类.
            - "数字模式": 三传数字递变模式
            - "组合课式": 阴阳奇偶组合课式
            - "特殊格局": 特殊数格局
        condition_description: 触发条件描述 (中文).
        interpretation: 解读 (中文).
        tone: 吉凶标签.
            - "auspicious": 吉
            - "inauspicious": 凶
            - "mixed": 吉凶参半
            - "neutral": 中性
        advice: 建议 (中文).
        source: 文献出处, 默认《小六壬课经》.
    """

    rule_id: str
    name: str
    category: str
    condition_description: str
    interpretation: str
    tone: str
    advice: str
    source: str = "《小六壬课经》"


# ══════════════════════════════════════════════════════════════
# 2. 纯检测函数 (Pure, 可单元测试)
# ══════════════════════════════════════════════════════════════


def _check_shunshu(nums: list[int]) -> bool:
    """三传顺数: n1 < n2 < n3."""
    return len(nums) == 3 and nums[0] < nums[1] < nums[2]


def _check_nishu(nums: list[int]) -> bool:
    """三传逆数: n1 > n2 > n3."""
    return len(nums) == 3 and nums[0] > nums[1] > nums[2]


def _check_sanshu_xiangtong(nums: list[int]) -> bool:
    """三数相同: n1 == n2 == n3."""
    return len(nums) == 3 and nums[0] == nums[1] == nums[2]


def _check_sanmu(nums: list[int]) -> bool:
    """三木: 三数五行皆属木 (n%5=1)."""
    return len(nums) == 3 and all(n % 5 == 1 for n in nums)


def _check_sanhuo(nums: list[int]) -> bool:
    """三火: 三数五行皆属火 (n%5=2)."""
    return len(nums) == 3 and all(n % 5 == 2 for n in nums)


def _check_sanjin(nums: list[int]) -> bool:
    """三金: 三数五行皆属金 (n%5=4)."""
    return len(nums) == 3 and all(n % 5 == 4 for n in nums)


def _check_sanshui(nums: list[int]) -> bool:
    """三水: 三数五行皆属水 (n%5=0)."""
    return len(nums) == 3 and all(n % 5 == 0 for n in nums)


def _check_sanqi(nums: list[int]) -> bool:
    """三奇: 三数皆为奇数."""
    return len(nums) == 3 and all(n % 2 == 1 for n in nums)


def _check_sanou(nums: list[int]) -> bool:
    """三偶: 三数皆为偶数."""
    return len(nums) == 3 and all(n % 2 == 0 for n in nums)


def _check_liangqiyiou(nums: list[int]) -> bool:
    """两奇一偶: 两个奇数, 一个偶数."""
    if len(nums) != 3:
        return False
    odds = sum(1 for n in nums if n % 2 == 1)
    return odds == 2


def _check_quandashu(nums: list[int]) -> bool:
    """全大数: 三数均大于 50."""
    return len(nums) == 3 and all(n > 50 for n in nums)


def _check_quanxiaoshu(nums: list[int]) -> bool:
    """全小数: 三数均小于 10."""
    return len(nums) == 3 and all(n < 10 for n in nums)


def _check_dazhongxiao(nums: list[int]) -> bool:
    """大中小分布: 一数<20, 一数20-50, 一数>50."""
    if len(nums) != 3:
        return False
    has_small = any(n < 20 for n in nums)
    has_medium = any(20 <= n <= 50 for n in nums)
    has_large = any(n > 50 for n in nums)
    return has_small and has_medium and has_large


def _check_han7(nums: list[int]) -> bool:
    """含7数: 任一数为 7."""
    return any(n == 7 for n in nums)


def _check_han9(nums: list[int]) -> bool:
    """含9数: 任一数为 9."""
    return any(n == 9 for n in nums)


# ══════════════════════════════════════════════════════════════
# 3. NUMBER_KE_RULES 规则表
# ══════════════════════════════════════════════════════════════

NUMBER_KE_RULES: list[NumberKeRule] = [
    # ── 三传数字模式 (3 rules) ──
    NumberKeRule(
        rule_id="shunshu",
        name="顺数格",
        category="数字模式",
        condition_description="三数递增 (n1 < n2 < n3)",
        interpretation="事态发展顺利, 步步推进, 由浅入深。初传为因, 中传为变, 末传为果, 三传递进有序, 主事有进展、层次分明。",
        tone="auspicious",
        advice="顺势而为, 按部就班推进。此时不宜冒进, 但可逐步扩大规模。",
    ),
    NumberKeRule(
        rule_id="nishu",
        name="逆数格",
        category="数字模式",
        condition_description="三数递减 (n1 > n2 > n3)",
        interpretation="事态逆转或退步, 由盛转衰之象。初传势大而末传势微, 主事情开头热闹但后续乏力, 或需回头审视初心。",
        tone="inauspicious",
        advice="宜守不宜攻, 先稳住现有局面。检查前期是否有遗漏, 回补短板后再图进取。",
    ),
    NumberKeRule(
        rule_id="sanshu_xiangtong",
        name="三同数格",
        category="数字模式",
        condition_description="三数相同 (n1 == n2 == n3)",
        interpretation="事态重复或极度加强之象。三传归一, 主事情反复出现、循环往复。若数值大则事大且固执, 若数值小则琐事缠身。",
        tone="mixed",
        advice="审视是否为同一问题反复出现。若是好事, 则加倍巩固; 若是坏事, 则需打破循环模式。",
    ),
    # ── 五行属性模式 (4 rules) ──
    NumberKeRule(
        rule_id="sanmu",
        name="三木格",
        category="五行属性",
        condition_description="三数五行皆属木 (n%5=1)",
        interpretation="木气过旺, 主生长、发展、扩张之势太盛。木多则刚, 过犹不及, 易有枝叶繁茂而根基不牢之患。",
        tone="mixed",
        advice="宜金制木, 借助外力约束边界, 聚焦核心, 剪除旁枝。不宜同时铺开多条战线。",
    ),
    NumberKeRule(
        rule_id="sanhuo",
        name="三火格",
        category="五行属性",
        condition_description="三数五行皆属火 (n%5=2)",
        interpretation="火气炎上, 主热情高涨、行动力强。但火多则焦, 易冲动行事、耗能过快、半途而废。需水济火以调和中庸。",
        tone="mixed",
        advice="需水济火, 冷静行事, 避免冲动决策。适当放慢节奏, 注意休息和精力分配。",
    ),
    NumberKeRule(
        rule_id="sanjin",
        name="三金格",
        category="五行属性",
        condition_description="三数五行皆属金 (n%5=4)",
        interpretation="金气肃杀, 主义气、决断、刚猛。金多则脆, 缺乏柔韧性, 易与人冲突、刚极易折。待火炼方可成器。",
        tone="inauspicious",
        advice="待火炼金, 借助外力打磨自身。避免独断专行, 多听取意见, 以柔克刚。",
    ),
    NumberKeRule(
        rule_id="sanshui",
        name="三水格",
        category="五行属性",
        condition_description="三数五行皆属水 (n%5=0)",
        interpretation="水势泛滥, 主流动、变化、智慧。但水多则泛, 缺乏定力, 念头太多难于聚焦, 易陷入犹豫不决。宜土制水以固本。",
        tone="inauspicious",
        advice="宜土制水, 建立稳固根基和计划。减少信息摄入, 聚焦一个方向深耕。",
    ),
    # ── 奇偶组合 (3 rules) ──
    NumberKeRule(
        rule_id="sanqi",
        name="三奇格",
        category="组合课式",
        condition_description="三数皆为奇数",
        interpretation="阳数过盛, 主动、进取、外向之力太强。阳主动而阴主静, 全阳则急功近利, 缺乏沉淀和内省。宜以阴调之。",
        tone="mixed",
        advice="宜阴调阳, 在行动中留出反思时间。大事可进, 但需兼顾细节和人际关系。",
    ),
    NumberKeRule(
        rule_id="sanou",
        name="三偶格",
        category="组合课式",
        condition_description="三数皆为偶数",
        interpretation="阴数过重, 主静、内敛、被动。阴主藏而阳主发, 全阴则思多行少、错失良机。宜以阳补之。",
        tone="mixed",
        advice="宜阳补阴, 化想法为行动。勇敢迈出第一步, 不必追求完美。",
    ),
    NumberKeRule(
        rule_id="liangqiyiou",
        name="两奇一偶格",
        category="组合课式",
        condition_description="两奇一偶",
        interpretation="阳中有阴, 刚柔相济。主力为阳而辅以阴柔, 进取之中不失审慎, 是为中正之象。",
        tone="auspicious",
        advice="刚柔并济, 该进则进, 该守则守。大局求进, 细节求稳, 此为最佳状态。",
    ),
    # ── 大小组合 (3 rules) ──
    NumberKeRule(
        rule_id="quandashu",
        name="全大数格",
        category="组合课式",
        condition_description="三数均大于 50",
        interpretation="事大而远, 所谋之事规模宏大、影响深远, 但非一朝一夕可成。大局已定, 但细节尚需铺陈。",
        tone="auspicious",
        advice="着眼长远布局, 耐心推进。大的方向已明朗, 专注执行即可。",
    ),
    NumberKeRule(
        rule_id="quanxiaoshu",
        name="全小数格",
        category="组合课式",
        condition_description="三数均小于 10",
        interpretation="事小而近, 所问之事属于眼前琐务, 影响范围小、时间短。宜以小见大, 从小处着手逐步扩大。",
        tone="neutral",
        advice="小事速决, 不宜拖沓。先解决眼前, 再考虑长远。",
    ),
    NumberKeRule(
        rule_id="dazhongxiao",
        name="三才分布格",
        category="组合课式",
        condition_description="三数分布均匀: 一数<20, 一数20-50, 一数>50",
        interpretation="天地人三才各安其位。小数为地, 主根基; 中数为人, 主作用; 大数为天, 主格局。三才齐备, 格局完善, 为大吉之数。",
        tone="auspicious",
        advice="天时地利人和皆备, 可大胆行事。根基稳、人脉广、格局大, 全面出击。",
    ),
    # ── 特殊数 (2 rules) ──
    NumberKeRule(
        rule_id="han7",
        name="含七变数格",
        category="特殊格局",
        condition_description="任一数等于 7",
        interpretation="七为变数, 有变动、转折之象。七为艮卦之数, 主止而复行、静极而动。事将变而未变, 正是调整方向的时机。",
        tone="mixed",
        advice="关注即将到来的变化信号。主动求变优于被动应变, 提前布局。",
    ),
    NumberKeRule(
        rule_id="han9",
        name="含九极数格",
        category="特殊格局",
        condition_description="任一数等于 9",
        interpretation="九为极数, 物极必反。九为乾卦之数, 主阳极阴生, 盛极而衰。事已至顶峰, 需防盛极之后的回落。",
        tone="mixed",
        advice="盛时思危, 高处不胜寒。把握当前高点, 适时收手或转向, 避免盈满之患。",
    ),
]


# ══════════════════════════════════════════════════════════════
# 4. evaluate_number_rules — 规则评估主函数
# ══════════════════════════════════════════════════════════════


def evaluate_number_rules(nums: list[int]) -> list[dict]:
    """遍历所有数字课经规则, 返回匹配的规则列表.

    Args:
        nums: 三个数字的列表 (长度应为 3).

    Returns:
        匹配规则列表, 每条为 dict 含 rule_id/name/category/condition_description/
        interpretation/tone/advice/source.
    """
    if len(nums) != 3:
        return []

    # 构建 check_fn 查找表
    check_map: dict[str, callable] = {
        "shunshu": _check_shunshu,
        "nishu": _check_nishu,
        "sanshu_xiangtong": _check_sanshu_xiangtong,
        "sanmu": _check_sanmu,
        "sanhuo": _check_sanhuo,
        "sanjin": _check_sanjin,
        "sanshui": _check_sanshui,
        "sanqi": _check_sanqi,
        "sanou": _check_sanou,
        "liangqiyiou": _check_liangqiyiou,
        "quandashu": _check_quandashu,
        "quanxiaoshu": _check_quanxiaoshu,
        "dazhongxiao": _check_dazhongxiao,
        "han7": _check_han7,
        "han9": _check_han9,
    }

    matched: list[dict] = []
    for rule in NUMBER_KE_RULES:
        fn = check_map.get(rule.rule_id)
        if fn is None:
            continue
        try:
            if fn(nums):
                matched.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "category": rule.category,
                    "condition_description": rule.condition_description,
                    "interpretation": rule.interpretation,
                    "tone": rule.tone,
                    "advice": rule.advice,
                    "source": rule.source,
                })
        except Exception:
            continue

    return matched


# ══════════════════════════════════════════════════════════════
# 5. get_number_wuxing — 数字五行分布
# ══════════════════════════════════════════════════════════════


def get_number_wuxing(nums: list[int]) -> dict:
    """返回三数五行分布.

    n%5 映射: 0=水, 1=木, 2=火, 3=土, 4=金.

    Args:
        nums: 三个数字的列表.

    Returns:
        {
            "distribution": [{"number": n, "remainder": n%5, "wuxing": "水/木/火/土/金"}, ...],
            "wuxing_counts": {"水": count, "木": count, "火": count, "土": count, "金": count},
            "dominant_wuxing": "火" or "balanced",
        }
    """
    if len(nums) != 3:
        return {
            "distribution": [],
            "wuxing_counts": {},
            "dominant_wuxing": "unknown",
        }

    distribution = [
        {
            "number": n,
            "remainder": n % 5,
            "wuxing": WUXING_MAP[n % 5],
        }
        for n in nums
    ]

    wuxing_counts: dict[str, int] = {"水": 0, "木": 0, "火": 0, "土": 0, "金": 0}
    for item in distribution:
        wuxing_counts[item["wuxing"]] += 1

    max_count = max(wuxing_counts.values())
    if max_count >= 3:
        dominant = "balanced"  # 三数同五行 → 其实也是一种主导, 但标注 balanced 表示均匀
        # 实际上应找同五行: 若 max_count==3 则主导五行明确
        for wx, cnt in wuxing_counts.items():
            if cnt == max_count:
                dominant = wx
                break
    elif max_count == 2:
        for wx, cnt in wuxing_counts.items():
            if cnt == max_count:
                dominant = wx
                break
    else:
        dominant = "balanced"

    return {
        "distribution": distribution,
        "wuxing_counts": wuxing_counts,
        "dominant_wuxing": dominant,
    }


# ══════════════════════════════════════════════════════════════
# 6. 自检
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 小六壬数字课经 规则表 自检 ===\n")
    print(f"总规则数: {len(NUMBER_KE_RULES)}")
    print(f"  数字模式: {sum(1 for r in NUMBER_KE_RULES if r.category == '数字模式')}")
    print(f"  五行属性: {sum(1 for r in NUMBER_KE_RULES if r.category == '五行属性')}")
    print(f"  组合课式: {sum(1 for r in NUMBER_KE_RULES if r.category == '组合课式')}")
    print(f"  特殊格局: {sum(1 for r in NUMBER_KE_RULES if r.category == '特殊格局')}")
    print(f"  吉 (auspicious): {sum(1 for r in NUMBER_KE_RULES if r.tone == 'auspicious')}")
    print(f"  凶 (inauspicious): {sum(1 for r in NUMBER_KE_RULES if r.tone == 'inauspicious')}")
    print(f"  吉凶参半 (mixed): {sum(1 for r in NUMBER_KE_RULES if r.tone == 'mixed')}")
    print(f"  中性 (neutral): {sum(1 for r in NUMBER_KE_RULES if r.tone == 'neutral')}")

    # 测试 1: 顺数
    print("\n--- 测试 1: 顺数 [10, 25, 88] ---")
    nums1 = [10, 25, 88]
    matched1 = evaluate_number_rules(nums1)
    for m in matched1:
        print(f"  {m['name']} ({m['tone']}): {m['interpretation'][:40]}...")
    wx1 = get_number_wuxing(nums1)
    print(f"  五行分布: {wx1['dominant_wuxing']} — {wx1['distribution']}")

    # 测试 2: 逆数
    print("\n--- 测试 2: 逆数 [99, 55, 3] ---")
    nums2 = [99, 55, 3]
    matched2 = evaluate_number_rules(nums2)
    for m in matched2:
        print(f"  {m['name']} ({m['tone']}): {m['interpretation'][:40]}...")

    # 测试 3: 三数相同
    print("\n--- 测试 3: 三同数 [7, 7, 7] ---")
    nums3 = [7, 7, 7]
    matched3 = evaluate_number_rules(nums3)
    for m in matched3:
        print(f"  {m['name']} ({m['tone']}): {m['interpretation'][:40]}...")

    # 测试 4: 三火
    print("\n--- 测试 4: 三火 [2, 7, 12] (all n%5=2) ---")
    nums4 = [2, 7, 12]
    matched4 = evaluate_number_rules(nums4)
    for m in matched4:
        print(f"  {m['name']} ({m['tone']}): {m['interpretation'][:40]}...")

    # 测试 5: 三奇
    print("\n--- 测试 5: 三奇 [1, 3, 5] ---")
    nums5 = [1, 3, 5]
    matched5 = evaluate_number_rules(nums5)
    for m in matched5:
        print(f"  {m['name']} ({m['tone']}): {m['interpretation'][:40]}...")

    # 测试 6: 含9
    print("\n--- 测试 6: 含9 [9, 45, 78] ---")
    nums6 = [9, 45, 78]
    matched6 = evaluate_number_rules(nums6)
    for m in matched6:
        print(f"  {m['name']} ({m['tone']}): {m['interpretation'][:40]}...")

    # 测试 7: 大中小 + 两奇一偶
    print("\n--- 测试 7: 大中小 [5, 35, 80] ---")
    nums7 = [5, 35, 80]
    matched7 = evaluate_number_rules(nums7)
    for m in matched7:
        print(f"  {m['name']} ({m['tone']}): {m['interpretation'][:40]}...")

    # 汇总
    print("\n=== 文献出处 ===")
    seen_sources = set()
    for r in NUMBER_KE_RULES:
        if r.source not in seen_sources:
            seen_sources.add(r.source)
            print(f"  {r.source}")
