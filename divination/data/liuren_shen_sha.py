"""大六壬 十二神煞落宫断语表 — dataclass+frozen, 数据驱动.

参考:
  《大六壬大全·神煞篇》
  《六壬指南·神煞章》
  《协纪辨方书》
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShenShaEntry:
    """单个神煞落宫断语.

    Attributes:
        shen_sha: 神煞名 (e.g. "贵人", "腾蛇")
        zhi: 落宫地支 (e.g. "子", "寅")
        gong_name: 宫名 (e.g. "子宫", "寅宫")
        wuxing: 五行
        trigram: 八卦
        judgment: 落宫断语
        category: 分类 ("吉神", "凶煞", "中性")
    """
    shen_sha: str
    zhi: str
    gong_name: str
    wuxing: str
    trigram: str
    judgment: str
    category: str


# ── 宫位信息 ──────────────────────────────────────────────────────

GONG_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

GONG_TRIGRAM = {
    "子": "坎", "丑": "艮", "寅": "艮", "卯": "震",
    "辰": "巽", "巳": "巽", "午": "离", "未": "坤",
    "申": "坤", "酉": "兑", "戌": "乾", "亥": "乾",
}


# ═════════════════════════════════════════════════════════════════
# 十二神煞落宫断语表 (12 神 × 关键宫位)
# ═════════════════════════════════════════════════════════════════

SHEN_SHA_JUDGMENTS: tuple[ShenShaEntry, ...] = (
    # ── 1. 贵人 ──
    ShenShaEntry(
        shen_sha="贵人", zhi="子", gong_name="子宫", wuxing="水", trigram="坎",
        category="吉神",
        judgment="贵人临子(神后), 水官相助, 暗中有贵人提携。利于求官、诉讼。",
    ),
    ShenShaEntry(
        shen_sha="贵人", zhi="寅", gong_name="寅宫", wuxing="木", trigram="艮",
        category="吉神",
        judgment="贵人临寅(功曹), 青龙之地, 文书得助, 考试/升迁大利。",
    ),
    ShenShaEntry(
        shen_sha="贵人", zhi="午", gong_name="午宫", wuxing="火", trigram="离",
        category="吉神",
        judgment="贵人临午(胜光), 光明正大, 得上级赏识, 名声显扬。",
    ),
    ShenShaEntry(
        shen_sha="贵人", zhi="申", gong_name="申宫", wuxing="金", trigram="坤",
        category="吉神",
        judgment="贵人临申(传送), 驿马动, 主得远方贵人相助或调动升迁。",
    ),
    ShenShaEntry(
        shen_sha="贵人", zhi="亥", gong_name="亥宫", wuxing="水", trigram="乾",
        category="吉神",
        judgment="贵登天门(亥), 大吉。百事皆利, 所求遂心, 上达天听。",
    ),

    # ── 2. 腾蛇 ──
    ShenShaEntry(
        shen_sha="腾蛇", zhi="巳", gong_name="巳宫", wuxing="火", trigram="巽",
        category="凶煞",
        judgment="腾蛇归穴(巳), 凶焰暂伏但暗流涌动, 防范口舌阴谋。",
    ),
    ShenShaEntry(
        shen_sha="腾蛇", zhi="午", gong_name="午宫", wuxing="火", trigram="离",
        category="凶煞",
        judgment="腾蛇乘火(午), 火上加火凶势大增, 主火灾、诉讼、突发惊变。",
    ),
    ShenShaEntry(
        shen_sha="腾蛇", zhi="未", gong_name="未宫", wuxing="土", trigram="坤",
        category="凶煞",
        judgment="腾蛇入墓(未), 凶势稍减但仍有余悸, 谨防虚惊怪梦。",
    ),

    # ── 3. 朱雀 ──
    ShenShaEntry(
        shen_sha="朱雀", zhi="午", gong_name="午宫", wuxing="火", trigram="离",
        category="中性",
        judgment="朱雀归位(午), 文书消息通畅, 但火过旺则口舌是非多。",
    ),
    ShenShaEntry(
        shen_sha="朱雀", zhi="卯", gong_name="卯宫", wuxing="木", trigram="震",
        category="中性",
        judgment="朱雀乘木(卯), 木火相生, 考试文书大利, 但防虚言夸大。",
    ),
    ShenShaEntry(
        shen_sha="朱雀", zhi="子", gong_name="子宫", wuxing="水", trigram="坎",
        category="凶煞",
        judgment="朱雀投江(子), 火被水克, 文书遗失、消息断绝、音讯不通。",
    ),

    # ── 4. 六合 ──
    ShenShaEntry(
        shen_sha="六合", zhi="卯", gong_name="卯宫", wuxing="木", trigram="震",
        category="吉神",
        judgment="六合归位(卯), 婚姻和合、合作顺利、中介得力。",
    ),
    ShenShaEntry(
        shen_sha="六合", zhi="申", gong_name="申宫", wuxing="金", trigram="坤",
        category="中性",
        judgment="六合临申, 金克木, 合作有波折, 须防契约纠纷。",
    ),
    ShenShaEntry(
        shen_sha="六合", zhi="亥", gong_name="亥宫", wuxing="水", trigram="乾",
        category="吉神",
        judgment="六合乘水(亥), 水生木, 婚姻和合有成, 人缘佳。",
    ),

    # ── 5. 勾陈 ──
    ShenShaEntry(
        shen_sha="勾陈", zhi="辰", gong_name="辰宫", wuxing="土", trigram="巽",
        category="凶煞",
        judgment="勾陈归位(辰), 田土纠纷、官司牵连、事多迟滞。",
    ),
    ShenShaEntry(
        shen_sha="勾陈", zhi="丑", gong_name="丑宫", wuxing="土", trigram="艮",
        category="凶煞",
        judgment="勾陈入墓(丑), 凶势稍缓, 但仍主拖沓不决。",
    ),
    ShenShaEntry(
        shen_sha="勾陈", zhi="寅", gong_name="寅宫", wuxing="木", trigram="艮",
        category="中性",
        judgment="勾陈临寅, 木克土, 官司有化解之机但过程漫长。",
    ),

    # ── 6. 青龙 ──
    ShenShaEntry(
        shen_sha="青龙", zhi="寅", gong_name="寅宫", wuxing="木", trigram="艮",
        category="吉神",
        judgment="青龙归位(寅), 大喜之兆, 财禄双收, 升迁在即。",
    ),
    ShenShaEntry(
        shen_sha="青龙", zhi="午", gong_name="午宫", wuxing="火", trigram="离",
        category="吉神",
        judgment="青龙吐火(午), 木火通明, 声名大噪, 事业兴旺。",
    ),
    ShenShaEntry(
        shen_sha="青龙", zhi="申", gong_name="申宫", wuxing="金", trigram="坤",
        category="中性",
        judgment="青龙折足(申), 金克木, 升迁有阻, 喜庆打折。",
    ),
    ShenShaEntry(
        shen_sha="青龙", zhi="戌", gong_name="戌宫", wuxing="土", trigram="乾",
        category="中性",
        judgment="青龙入墓(戌), 吉力减弱, 财运受阻, 宜守成。",
    ),

    # ── 7. 天空 ──
    ShenShaEntry(
        shen_sha="天空", zhi="丑", gong_name="丑宫", wuxing="土", trigram="艮",
        category="凶煞",
        judgment="天空临丑, 虚言虚语、文书落空、计划泡汤。",
    ),
    ShenShaEntry(
        shen_sha="天空", zhi="未", gong_name="未宫", wuxing="土", trigram="坤",
        category="凶煞",
        judgment="天空临未, 空话连篇、承诺不兑现, 防欺诈。",
    ),
    ShenShaEntry(
        shen_sha="天空", zhi="卯", gong_name="卯宫", wuxing="木", trigram="震",
        category="中性",
        judgment="天空乘木(卯), 木克土, 虚妄稍减但信息仍不可信。",
    ),

    # ── 8. 白虎 ──
    ShenShaEntry(
        shen_sha="白虎", zhi="申", gong_name="申宫", wuxing="金", trigram="坤",
        category="凶煞",
        judgment="白虎归位(申), 金气最旺, 凶丧血光、车祸手术、权威威严并存。",
    ),
    ShenShaEntry(
        shen_sha="白虎", zhi="午", gong_name="午宫", wuxing="火", trigram="离",
        category="凶煞",
        judgment="白虎衔尸(午), 火克金, 血光之灾暂缓但需防火伤。",
    ),
    ShenShaEntry(
        shen_sha="白虎", zhi="寅", gong_name="寅宫", wuxing="木", trigram="艮",
        category="凶煞",
        judgment="白虎临寅, 金克木, 伤灾在外, 出行须格外小心。",
    ),
    ShenShaEntry(
        shen_sha="白虎", zhi="子", gong_name="子宫", wuxing="水", trigram="坎",
        category="中性",
        judgment="白虎溺水(子), 金生水, 凶势稍泄但仍须防备。",
    ),

    # ── 9. 太常 ──
    ShenShaEntry(
        shen_sha="太常", zhi="未", gong_name="未宫", wuxing="土", trigram="坤",
        category="吉神",
        judgment="太常归位(未), 宴乐嘉会、衣帛之喜、祭祀吉昌。",
    ),
    ShenShaEntry(
        shen_sha="太常", zhi="巳", gong_name="巳宫", wuxing="火", trigram="巽",
        category="中性",
        judgment="太常乘火(巳), 火生土, 宴会得宜但防过度铺张。",
    ),
    ShenShaEntry(
        shen_sha="太常", zhi="卯", gong_name="卯宫", wuxing="木", trigram="震",
        category="中性",
        judgment="太常临卯, 木克土, 礼仪有缺, 宴饮须节制。",
    ),

    # ── 10. 玄武 ──
    ShenShaEntry(
        shen_sha="玄武", zhi="亥", gong_name="亥宫", wuxing="水", trigram="乾",
        category="凶煞",
        judgment="玄武归位(亥), 盗贼水厄、阴谋诡计最旺之时。",
    ),
    ShenShaEntry(
        shen_sha="玄武", zhi="子", gong_name="子宫", wuxing="水", trigram="坎",
        category="凶煞",
        judgment="玄武乘水(子), 水势滔天, 防盗防骗、水上安全、机密泄露。",
    ),
    ShenShaEntry(
        shen_sha="玄武", zhi="丑", gong_name="丑宫", wuxing="土", trigram="艮",
        category="中性",
        judgment="玄武入墓(丑), 土克水, 盗贼难逞但暗昧之事仍需提防。",
    ),
    ShenShaEntry(
        shen_sha="玄武", zhi="未", gong_name="未宫", wuxing="土", trigram="坤",
        category="中性",
        judgment="玄武入墓(未), 凶势受制, 机密可保。",
    ),

    # ── 11. 太阴 ──
    ShenShaEntry(
        shen_sha="太阴", zhi="酉", gong_name="酉宫", wuxing="金", trigram="兑",
        category="吉神",
        judgment="太阴归位(酉), 阴私得助、暗中贵人、女性相助。",
    ),
    ShenShaEntry(
        shen_sha="太阴", zhi="巳", gong_name="巳宫", wuxing="火", trigram="巽",
        category="中性",
        judgment="太阴乘火(巳), 火克金, 暗中助力打折扣, 宜明面行事。",
    ),
    ShenShaEntry(
        shen_sha="太阴", zhi="丑", gong_name="丑宫", wuxing="土", trigram="艮",
        category="吉神",
        judgment="太阴临丑, 土生金, 暗助有力, 密谋可成。",
    ),

    # ── 12. 天后 ──
    ShenShaEntry(
        shen_sha="天后", zhi="子", gong_name="子宫", wuxing="水", trigram="坎",
        category="吉神",
        judgment="天后归位(子), 婚姻佳期、女性掌权、恩泽降临。",
    ),
    ShenShaEntry(
        shen_sha="天后", zhi="午", gong_name="午宫", wuxing="火", trigram="离",
        category="中性",
        judgment="天后临午, 水被火冲, 婚姻有波折, 女性须防口舌。",
    ),
    ShenShaEntry(
        shen_sha="天后", zhi="申", gong_name="申宫", wuxing="金", trigram="坤",
        category="吉神",
        judgment="天后临申, 金生水, 婚姻得女性长辈成全。",
    ),
)


# ═════════════════════════════════════════════════════════════════
# 查表函数 (engine 调此, 纯查表)
# ═════════════════════════════════════════════════════════════════

def get_shen_sha_judgments(generals: list[dict]) -> list[dict]:
    """根据十二天将排布, 查找各神煞落宫的断语.

    Args:
        generals: 十二天将排布列表, 每项含 'general' (神煞名) 和 'position' (落宫地支)

    Returns:
        匹配的断语列表, 每项 {shen_sha, zhi, gong_name, judgment, category}
        （一个神煞可能在地支表中出现多次, 取第一个匹配）
    """
    # 建立索引: (shen_sha, zhi) → entry
    idx: dict[tuple[str, str], ShenShaEntry] = {}
    for entry in SHEN_SHA_JUDGMENTS:
        idx[(entry.shen_sha, entry.zhi)] = entry

    results: list[dict] = []
    for gen in generals:
        gen_name = gen.get("general", "")
        position = gen.get("position", "")
        key = (gen_name, position)
        if key in idx:
            e = idx[key]
            results.append({
                "shen_sha": e.shen_sha,
                "zhi": e.zhi,
                "gong_name": e.gong_name,
                "wuxing": e.wuxing,
                "trigram": e.trigram,
                "judgment": e.judgment,
                "category": e.category,
            })

    return results
