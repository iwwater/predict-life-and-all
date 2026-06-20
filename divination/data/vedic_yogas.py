"""吠陀占星 · 常见 Yogas (瑜伽) 体系。

文献:
  - *Brihat Parashara Hora Shastra* (BPHS) — 吠陀占星核心典籍
  - *Phaladeepika* (Mantreswar) — 详解 Yogas
  - *Brihat Jataka* (Varahamihira)

Yogas 概念:
  Yogas = 行星 + 宫位 + 星座 的特定组合, 产生特定吉凶效果。
  已知 Yogas 数百种, 本表收录最常见 ~25 种。

分类:
  - Raj Yoga (王瑜伽) - 富贵 / 权力
  - Dhana Yoga (财瑜伽) - 财富
  - Pancha Mahapurusha Yoga (五大伟人瑜伽) - 火星/水星/木星/金星/土星入庙
  - Neecha Bhanga Raja Yoga (陷位解除王瑜伽) - 陷位反成大贵
  - Viparita Raja Yoga (逆境王瑜伽) - 第 6/8/12 宫主入特定宫位
  - Gaja Kesari Yoga (象-狮瑜伽) - 木星与月亮同宫或对望
  - Budhaditya Yoga (水日瑜伽) - 水星与太阳同宫
  - Chandra-Mangal Yoga (月-火瑜伽) - 月亮与火星同宫
  - 其他特殊 Yoga

计算:
  简化判断: 给定本命盘行星位置 + 庙旺关系 → 触发条件 → 列出 Yogas。
"""
from __future__ import annotations

from typing import Any


# ══════════════════════════════════════════════════════════════
# 1. 行星庙旺 (Own/Exaltation) 表
# ══════════════════════════════════════════════════════════════
# Own Signs: 行星守护的星座 (Ruler)
# Exaltation: 入庙星座

PLANET_OWN_SIGNS: dict[str, list[int]] = {
    "太阳": [4],       # 狮子 (Leo, idx 4)
    "月亮": [3],       # 巨蟹 (Cancer, idx 3)
    "火星": [0, 7],    # 白羊 + 天蝎
    "水星": [2, 5],    # 双子 + 处女
    "木星": [8, 11],   # 射手 + 双鱼
    "金星": [1, 6],    # 金牛 + 天秤
    "土星": [9, 10],   # 摩羯 + 水瓶
    "罗睺": [],        # 北交点无庙
    "计都": [],        # 南交点无庙
}

PLANET_EXALT_SIGN: dict[str, int] = {
    "太阳": 0,    # 白羊 (Aries) — 入庙白羊 10°
    "月亮": 1,    # 金牛 (Taurus) — 入庙金牛 3°
    "火星": 9,    # 摩羯 (Capricorn) — 入庙摩羯 28°
    "水星": 5,    # 处女 (Virgo) — 入庙处女 15°
    "木星": 3,    # 巨蟹 (Cancer) — 入庙巨蟹 5°
    "金星": 11,   # 双鱼 (Pisces) — 入庙双鱼 27°
    "土星": 6,    # 天秤 (Libra) — 入庙天秤 20°
}

PLANET_DEBIL_SIGN: dict[str, int] = {
    "太阳": 6,    # 天秤 — 落陷
    "月亮": 7,    # 天蝎 — 落陷
    "火星": 3,    # 巨蟹 — 落陷
    "水星": 11,   # 双鱼 — 落陷
    "木星": 9,    # 摩羯 — 落陷
    "金星": 5,    # 处女 — 落陷 (经典)
    "土星": 0,    # 白羊 — 落陷
}


# 12 星座中文
SIGN_CN = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
           "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]


def _sign_idx_to_cn(idx: int) -> str:
    return SIGN_CN[idx % 12]


# ══════════════════════════════════════════════════════════════
# 2. 常见 Yogas 触发条件
# ══════════════════════════════════════════════════════════════

YOGAS: list[dict[str, Any]] = [
    # ── Raj Yoga (王瑜伽) ──
    {
        "name": "Raja Yoga (王瑜伽)",
        "category": "权力",
        "condition": "Kendra (1/4/7/10宫) 主与 Trikona (1/5/9宫) 主形成相位",
        "meaning": "最尊贵的 Yoga, 主大富贵、权力、地位。",
        "rarity": "稀有",
    },
    {
        "name": "Neecha Bhanga Raja Yoga (陷位解除王瑜伽)",
        "category": "权力",
        "condition": "落陷行星的宫主位于其他强宫, 或与其守护星形成相位",
        "meaning": "大难不死必有后福, 落陷反成大贵。",
        "rarity": "稀有",
    },
    {
        "name": "Viparita Raja Yoga (逆境王瑜伽)",
        "category": "权力",
        "condition": "第 6/8/12 宫主位于第 8/12/6 宫（互相落入凶宫）",
        "meaning": "逆境中崛起, 大器晚成。",
        "rarity": "稀有",
    },

    # ── Dhana Yoga (财瑜伽) ──
    {
        "name": "Dhana Yoga (财瑜伽)",
        "category": "财富",
        "condition": "第 2/11 宫主 与第 1/5/9/10 宫主形成相位或合相",
        "meaning": "主大富, 财源广进。",
        "rarity": "常见",
    },
    {
        "name": "Chandra-Mangal Yoga (月-火瑜伽)",
        "category": "财富",
        "condition": "月亮与火星同宫或对望",
        "meaning": "通过不动产、地产、矿业积累财富。",
        "rarity": "常见",
    },
    {
        "name": "Lakshmi Yoga (吉祥天瑜伽)",
        "category": "财富",
        "condition": "第 9 宫主强旺 (入庙/旺) 且第 1/2/5/10 宫有吉星",
        "meaning": "主大富贵, 福泽深厚。",
        "rarity": "稀有",
    },

    # ── Pancha Mahapurusha Yoga (五大伟人瑜伽) ──
    {
        "name": "Ruchaka Yoga (战神瑜伽)",
        "category": "伟人",
        "condition": "火星位于白羊/天蝎 (庙) 或摩羯 (入庙), 且在 Kendra (1/4/7/10)",
        "meaning": "主勇敢、领导力、武将之命。",
        "rarity": "常见",
    },
    {
        "name": "Bhadra Yoga (贤者瑜伽)",
        "category": "伟人",
        "condition": "水星位于双子/处女 (庙), 且在 Kendra",
        "meaning": "主聪慧、善辩、文学/商业天赋。",
        "rarity": "常见",
    },
    {
        "name": "Hamsa Yoga (天鹅瑜伽)",
        "category": "伟人",
        "condition": "木星位于射手/双鱼 (庙) 或巨蟹 (入庙), 且在 Kendra",
        "meaning": "主智慧、灵性、导师。",
        "rarity": "常见",
    },
    {
        "name": "Malavya Yoga (莲花瑜伽)",
        "category": "伟人",
        "condition": "金星位于金牛/天秤 (庙) 或双鱼 (入庙), 且在 Kendra",
        "meaning": "主美貌、艺术、财富。",
        "rarity": "常见",
    },
    {
        "name": "Sasa Yoga (兔瑜伽)",
        "category": "伟人",
        "condition": "土星位于摩羯/水瓶 (庙) 或天秤 (入庙), 且在 Kendra",
        "meaning": "主权力、领导、长寿。",
        "rarity": "常见",
    },

    # ── 月亮相关 Yoga ──
    {
        "name": "Gaja Kesari Yoga (象-狮瑜伽)",
        "category": "智慧",
        "condition": "木星与月亮同宫或对望 (相差 0° 或 180°), 木星非落陷",
        "meaning": "主智慧、声望、长寿、富贵。",
        "rarity": "常见",
    },
    {
        "name": "Sunapha Yoga (太阳增力瑜伽)",
        "category": "声望",
        "condition": "月亮位于太阳前 1-12 宫位（即月亮与太阳同宫, 月在 0-12° 内）",
        "meaning": "主声望、自力更生、权威。",
        "rarity": "常见",
    },
    {
        "name": "Anapha Yoga (太阳左侧瑜伽)",
        "category": "声望",
        "condition": "月亮位于太阳后 1-12 宫位",
        "meaning": "主健康、美德、长寿。",
        "rarity": "常见",
    },
    {
        "name": "Kemadruma Yoga (孤月瑜伽)",
        "category": "孤克",
        "condition": "月亮两侧 (前 2 宫 / 后 2 宫) 无行星, 也无与罗睺/计都形成相位",
        "meaning": "主孤克、贫困、心理不安 (但若有吉星解救则反成大贵)。",
        "rarity": "常见",
    },

    # ── 太阳 + 水星 Yoga ──
    {
        "name": "Budhaditya Yoga (水日瑜伽)",
        "category": "智慧",
        "condition": "水星与太阳同宫 (3° 容许度内)",
        "meaning": "主聪慧、口才、商业天赋。但若水星被太阳灼伤则反成狡诈。",
        "rarity": "常见",
    },

    # ── Rahu/Ketu 相关 ──
    {
        "name": "Rahu Aditya Yoga (罗睺日瑜伽)",
        "category": "异途",
        "condition": "罗睺与太阳同宫或对望",
        "meaning": "主异途成名、技术天赋、但易遭误解。",
        "rarity": "稀有",
    },
    {
        "name": "Kala Sarpa Yoga (时蛇瑜伽)",
        "category": "特殊",
        "condition": "所有行星位于罗睺与计都之间",
        "meaning": "主命运多舛, 但若有吉星解救则反成大业。",
        "rarity": "稀有",
    },

    # ── 婚姻相关 ──
    {
        "name": "Parivartana Yoga (互换瑜伽)",
        "category": "互换",
        "condition": "两颗行星互换星座 (A 在 B 庙, B 在 A 庙)",
        "meaning": "主互换互利, 该领域大吉。",
        "rarity": "常见",
    },
    {
        "name": "Mangal Dosha (火星煞)",
        "category": "婚姻",
        "condition": "火星位于第 1/2/4/7/8/12 宫",
        "meaning": "传统上主婚姻不顺, 现代占星认为非绝对, 应综合判断。",
        "rarity": "常见",
    },

    # ── 健康相关 ──
    {
        "name": "Kemadruma Dosha (孤月煞)",
        "category": "孤克",
        "condition": "月亮无吉星相位, 两侧 2 宫空",
        "meaning": "主心理孤独, 易陷忧郁。",
        "rarity": "常见",
    },

    # ── 学业相关 ──
    {
        "name": "Saraswati Yoga (辩才天瑜伽)",
        "category": "智慧",
        "condition": "木星/水星/金星 三吉星中两颗或以上强旺且与第 5 宫相关",
        "meaning": "主文学、艺术、音乐、辩论天赋。",
        "rarity": "常见",
    },

    # ── 长寿 ──
    {
        "name": "Ayush Yoga (长寿瑜伽)",
        "category": "长寿",
        "condition": "第 8 宫主强旺且与吉星形成相位",
        "meaning": "主长寿, 但若第 8 宫主受克则反之。",
        "rarity": "常见",
    },
]


# ══════════════════════════════════════════════════════════════
# 3. Yoga 检测函数
# ══════════════════════════════════════════════════════════════
def check_gaja_kesari(moon_sign: int, jupiter_sign: int, jupiter_house: int) -> bool:
    """检查 Gaja Kesari Yoga。

    Args:
        moon_sign: 月亮所在星座 (0-11)
        jupiter_sign: 木星所在星座 (0-11)
        jupiter_house: 木星所在宫位 (1-12)

    Returns:
        True if 木星与月亮同宫或对望, 且木星非落陷
    """
    if jupiter_house not in (1, 4, 7, 10):
        # Kendra 宫位才作数
        return False
    if jupiter_sign == PLANET_DEBIL_SIGN["木星"]:
        return False  # 木星落陷
    # 同宫 (差 0) 或对望 (差 6)
    diff = abs(moon_sign - jupiter_sign) % 12
    return diff == 0 or diff == 6


def check_budhaditya(sun_sign: int, sun_degree: float,
                     mercury_sign: int, mercury_degree: float,
                     orb: float = 3.0) -> bool:
    """检查 Budhaditya Yoga (水日同宫)。"""
    if sun_sign != mercury_sign:
        return False
    diff = abs(sun_degree - mercury_degree)
    return diff <= orb


def check_mangal_dosha(mars_house: int) -> bool:
    """检查火星煞 (火星位于第 1/2/4/7/8/12 宫)。"""
    return mars_house in {1, 2, 4, 7, 8, 12}


def check_kemadruma(moon_sign: int, planets_in_chart: dict[str, int]) -> bool:
    """检查 Kemadruma Yoga (孤月)。

    Args:
        moon_sign: 月亮所在星座
        planets_in_chart: {planet: sign_idx} 所有行星 + 罗睺/计都 的星座

    Returns:
        True if 月亮两侧 2 宫 (前后各 2 宫) 无任何行星
    """
    moon_neighbors = {(moon_sign - 2) % 12, (moon_sign - 1) % 12,
                       (moon_sign + 1) % 12, (moon_sign + 2) % 12}
    planets_in_neighbors = {s for p, s in planets_in_chart.items()
                            if p != "月亮" and s in moon_neighbors}
    return len(planets_in_neighbors) == 0


def check_pancha_mahapurusha(planet: str, sign: int, house: int) -> str | None:
    """检查 Pancha Mahapurusha Yoga (五大伟人瑜伽)。

    Returns:
        Yoga 名称 (如 'Hamsa Yoga') 或 None
    """
    if house not in (1, 4, 7, 10):
        return None
    own_signs = PLANET_OWN_SIGNS.get(planet, [])
    exalt_sign = PLANET_EXALT_SIGN.get(planet)
    if sign in own_signs or sign == exalt_sign:
        mapping = {
            "火星": "Ruchaka Yoga (战神瑜伽)",
            "水星": "Bhadra Yoga (贤者瑜伽)",
            "木星": "Hamsa Yoga (天鹅瑜伽)",
            "金星": "Malavya Yoga (莲花瑜伽)",
            "土星": "Sasa Yoga (兔瑜伽)",
        }
        return mapping.get(planet)


# ══════════════════════════════════════════════════════════════
# 4. Yogas 列表查询
# ══════════════════════════════════════════════════════════════
def list_yogas_by_category(category: str) -> list[dict[str, Any]]:
    """按分类查询 Yogas。"""
    return [y for y in YOGAS if y["category"] == category]


def list_yogas_by_rarity(rarity: str) -> list[dict[str, Any]]:
    """按稀有度查询。"""
    return [y for y in YOGAS if y["rarity"] == rarity]


def get_yoga_count() -> dict[str, int]:
    """按分类统计 Yogas。"""
    counts: dict[str, int] = {}
    for y in YOGAS:
        cat = y.get("category", "其他")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


# ══════════════════════════════════════════════════════════════
# 5. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 吠陀 Yogas (瑜伽) 体系自检 ===\n")

    # 1. Yogas 统计
    counts = get_yoga_count()
    print(f"1. Yogas 总数: {len(YOGAS)} 种")
    print(f"   按分类: {counts}")

    # 2. 五星伟人瑜伽示例
    print("\n2. Pancha Mahapurusha Yoga 检查:")
    test_cases = [
        ("火星", 0, 1, "白羊座第 1 宫"),    # 庙 + Kendra
        ("木星", 8, 4, "射手座第 4 宫"),    # 庙 + Kendra
        ("金星", 11, 10, "双鱼座第 10 宫"),  # 入庙 + Kendra
        ("火星", 0, 2, "白羊座第 2 宫"),    # 庙但非 Kendra
    ]
    for planet, sign, house, desc in test_cases:
        result = check_pancha_mahapurusha(planet, sign, house)
        print(f"   {desc}: {result or '无'}")

    # 3. 象-狮瑜伽示例
    print("\n3. Gaja Kesari Yoga 检查:")
    cases = [
        (0, 0, 1, "月亮木星同白羊, Kendra"),  # 同宫 + Kendra
        (0, 6, 7, "月亮白羊, 木星天秤, Kendra"),  # 对望 + Kendra
        (0, 0, 2, "月亮木星同白羊, 但非 Kendra"),  # 同宫但非 Kendra
        (0, 9, 4, "月亮白羊, 木星摩羯(落陷), Kendra"),  # 木星落陷
    ]
    for ms, js, jh, desc in cases:
        result = check_gaja_kesari(ms, js, jh)
        print(f"   {desc}: {'✓' if result else '✗'}")

    # 4. 水日瑜伽
    print("\n4. Budhaditya Yoga 检查:")
    print(f"   水星与太阳同白羊, 度数差 1°: {check_budhaditya(0, 5.0, 0, 6.0)}")
    print(f"   水星与太阳同白羊, 度数差 5°: {check_budhaditya(0, 5.0, 0, 10.0)}")
    print(f"   水星与太阳不同宫: {check_budhaditya(0, 5.0, 1, 10.0)}")

    # 5. 火星煞
    print("\n5. Mangal Dosha 检查:")
    for h in [1, 2, 3, 4, 5, 7, 9, 12]:
        is_dosha = check_mangal_dosha(h)
        print(f"   火星第 {h} 宫: {'✗ 火星煞' if is_dosha else '✓ 无煞'}")
