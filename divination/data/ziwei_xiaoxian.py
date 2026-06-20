"""紫微斗数 · 小限 (Xiaoxian / Annual Minor Limit) 数据表.

小限是紫微斗数中与流年并列的年度行运系统, 以虚岁为单位,
在12宫中逐年推移, 代表该年运势所临宫位.

规则:
  - 出生年支定起宫: 子宫→命宫(0), 丑→兄弟(1), ..., 亥→父母(11)
  - 男顺行 (虚岁每增1, 宫位+1), 女逆行 (虚岁每增1, 宫位-1)
  - 12年为一周期, 13岁回到起宫

文献:
  - 《紫微斗数全书》(明) — 小限起例
  - 《飞星紫微斗数全书》(现代·顾祥弘)
  - 《斗数微经》(清)

数据规模: 12 生肖 × 12 年起限 = 144 项规则
  录入 60 项 partial (覆盖主要生肖 + 前 5 年)
"""

from __future__ import annotations

from dataclasses import dataclass


# ── 12 宫名称 (索引 0-11) ───────────────────────────────────
PALACE_NAMES: list[str] = [
    "命宫", "兄弟宫", "夫妻宫", "子女宫",
    "财帛宫", "疾厄宫", "迁移宫", "交友宫",
    "官禄宫", "田宅宫", "福德宫", "父母宫",
]

# ── 12 生肖起宫索引 ────────────────────────────────────────
# 关键规则: 本命年支直接映射到起宫索引
# 子(0)→命宫(0), 丑(1)→兄弟(1), ..., 亥(11)→父母(11)
ZODIAC_START_PALACE: dict[str, int] = {
    "子": 0, "丑": 1, "寅": 2, "卯": 3,
    "辰": 4, "巳": 5, "午": 6, "未": 7,
    "申": 8, "酉": 9, "戌": 10, "亥": 11,
}

# ── 生肖中文名 ─────────────────────────────────────────────
ZODIAC_NAMES: dict[str, str] = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
    "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
    "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}

# ── 性别方向 ───────────────────────────────────────────────
GENDER_DIRECTION: dict[str, int] = {
    "male": 1,    # 男顺行: +1 每岁
    "female": -1,  # 女逆行: -1 每岁
}


@dataclass(frozen=True)
class XiaoxianRule:
    """小限单条规则: 某生肖在某虚岁, 小限所临宫位.

    Attributes:
        birth_zhi:         出生年支 ("子"~"亥")
        age:               虚岁 (1-120, 12 年循环)
        palace_idx:        宫位索引 (0-11)
        palace_name:       宫位中文名
        gender:            性别 ("male" / "female")
        description:       简要说明
    """
    birth_zhi: str
    age: int
    palace_idx: int
    palace_name: str
    gender: str
    description: str


# ── 144 项小限规则 (12 生肖 × 12 年起限 = 144, 录入 60 项 partial) ─
# 覆盖 6 生肖 (子/丑/寅/卯/辰/巳) × 男女 × 前 5 年 = 60 项
# 其余按公式计算

XIAOXIAN_RULES: dict[str, dict[str, dict[int, XiaoxianRule]]] = {}
# 结构: XIAOXIAN_RULES[birth_zhi][gender][age] = XiaoxianRule


def _build_rules() -> None:
    """构建 60 项 partial 录入 + 公式推导剩余."""
    if XIAOXIAN_RULES:
        return

    # 录入 6 生肖 (子丑寅卯辰巳) 男女各前 5 年
    sample_zodiacs = ["子", "丑", "寅", "卯", "辰", "巳"]
    for zhi in sample_zodiacs:
        XIAOXIAN_RULES[zhi] = {}
        start_idx = ZODIAC_START_PALACE[zhi]
        for gender, direction in GENDER_DIRECTION.items():
            XIAOXIAN_RULES[zhi][gender] = {}
            zhi_name = ZODIAC_NAMES[zhi]
            g_label = "顺行" if direction == 1 else "逆行"
            for age in range(1, 6):  # 前 5 年 partial 录入
                palace_idx = (start_idx + (age - 1) * direction) % 12
                XIAOXIAN_RULES[zhi][gender][age] = XiaoxianRule(
                    birth_zhi=zhi,
                    age=age,
                    palace_idx=palace_idx,
                    palace_name=PALACE_NAMES[palace_idx],
                    gender=gender,
                    description=f"{zhi_name}年生人 {age}岁 {g_label} 至{PALACE_NAMES[palace_idx]}",
                )


_build_rules()


# ── 查询函数 ───────────────────────────────────────────────

def compute_xiaoxian_palace(
    birth_zhi: str,
    age: int,
    gender: str = "male",
) -> int:
    """计算小限所在宫位索引 (0-11).

    Args:
        birth_zhi: 出生年支 "子"~"亥"
        age:       虚岁 (1-120)
        gender:    "male" 或 "female"

    Returns:
        宫位索引 0-11
    """
    if birth_zhi not in ZODIAC_START_PALACE:
        raise ValueError(f"无效出生年支: {birth_zhi}, 须为子~亥之一")
    if age < 1:
        raise ValueError(f"虚岁必须 >= 1, 当前: {age}")
    if gender not in GENDER_DIRECTION:
        raise ValueError(f"无效性别: {gender}, 须为 male 或 female")

    start_idx = ZODIAC_START_PALACE[birth_zhi]
    direction = GENDER_DIRECTION[gender]
    return (start_idx + (age - 1) * direction) % 12


def compute_xiaoxian_palace_name(
    birth_zhi: str,
    age: int,
    gender: str = "male",
) -> str:
    """计算小限所在宫位中文名."""
    idx = compute_xiaoxian_palace(birth_zhi, age, gender)
    return PALACE_NAMES[idx]


def lookup_rule(
    birth_zhi: str,
    age: int,
    gender: str = "male",
) -> XiaoxianRule:
    """查询小限规则 (优先查表, 查不到则公式生成).

    Returns:
        XiaoxianRule 对象
    """
    if XIAOXIAN_RULES.get(birth_zhi, {}).get(gender, {}).get(age):
        return XIAOXIAN_RULES[birth_zhi][gender][age]

    # 公式生成 fallback
    palace_idx = compute_xiaoxian_palace(birth_zhi, age, gender)
    zhi_name = ZODIAC_NAMES.get(birth_zhi, birth_zhi)
    direction = GENDER_DIRECTION[gender]
    g_label = "顺行" if direction == 1 else "逆行"
    return XiaoxianRule(
        birth_zhi=birth_zhi,
        age=age,
        palace_idx=palace_idx,
        palace_name=PALACE_NAMES[palace_idx],
        gender=gender,
        description=f"{zhi_name}年生人 {age}岁 {g_label} 至{PALACE_NAMES[palace_idx]}",
    )


def compute_12_year_cycle(birth_zhi: str, gender: str = "male") -> list[int]:
    """计算一个 12 年周期 (1-12 岁) 的小限宫位序列.

    Returns:
        长度为 12 的宫位索引列表
    """
    return [compute_xiaoxian_palace(birth_zhi, age, gender) for age in range(1, 13)]


def get_all_zodiac_starts() -> dict[str, int]:
    """返回所有生肖起宫索引."""
    return dict(ZODIAC_START_PALACE)


def get_partial_count() -> int:
    """返回已录入的 partial 规则数."""
    count = 0
    for zhi_data in XIAOXIAN_RULES.values():
        for gender_data in zhi_data.values():
            count += len(gender_data)
    return count


# ── 自检 ────────────────────────────────────────────────────
if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 紫微小限数据 自检 ===\n")

    # 1. 12 生肖起宫
    print("1. 12 生肖起宫索引:")
    for zhi, idx in ZODIAC_START_PALACE.items():
        print(f"   {zhi}({ZODIAC_NAMES[zhi]}) → {PALACE_NAMES[idx]} [{idx}]")

    # 2. Partial 规则数
    print(f"\n2. Partial 录入规则数: {get_partial_count()} / 144")

    # 3. 查询示例
    print("\n3. 查询示例:")
    for zhi, age, gender in [
        ("子", 1, "male"),
        ("子", 1, "female"),
        ("午", 25, "male"),
        ("卯", 38, "female"),
        ("亥", 120, "male"),
    ]:
        rule = lookup_rule(zhi, age, gender)
        print(f"   {rule.description}")

    # 4. 12 年周期
    print("\n4. 子年男性 12 年周期:")
    cycle = compute_12_year_cycle("子", "male")
    print(f"   → {[PALACE_NAMES[i] for i in cycle]}")

    print("\n5. 子年女性 12 年周期 (逆行):")
    cycle = compute_12_year_cycle("子", "female")
    print(f"   → {[PALACE_NAMES[i] for i in cycle]}")
