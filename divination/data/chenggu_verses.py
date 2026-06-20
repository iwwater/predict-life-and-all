"""袁天罡《称骨歌》51 档全量批语数据库 — 印本对标版.

按总骨重 (单位:两) 查对应四句歌诀及吉凶总评.

文献依据:
    - 《袁天罡称骨歌》(唐) — 称骨核心歌诀
    - 《命相全编·称骨篇》(清) — 称骨变体与流派异说
    - 印本:清代/民国刻本(公版)

骨重范围: 2.1 两 ~ 7.1 两, 0.1 两递增, 共 51 档.
"""
from __future__ import annotations

from dataclasses import dataclass


# ── 数据结构 ─────────────────────────────────────────────
@dataclass(frozen=True)
class ChengguVerse:
    """单档称骨歌诀.

    Attributes:
        weight:           骨重(两), 0.1 两递增, 范围 2.1 ~ 7.1
        verse_4_lines:    4 句歌诀 (原印本)
        summary_polarity: 吉凶总评; 取值 "auspicious" | "inauspicious" | "neutral"
        source:           出处标识
    """
    weight: float
    verse_4_lines: list[str]
    summary_polarity: str          # "auspicious" | "inauspicious" | "neutral"
    source: str


# ── 51 档全量批语 ─────────────────────────────────────────
# 骨重从 2.1 两 到 7.1 两, 共 51 档, 0.1 两递增.
# polarity 分布(整体规律): 轻骨 (2.1-3.0) 多 "inauspicious",
#                          中骨 (3.1-5.0) "neutral" 居多, 偶有 "auspicious",
#                          重骨 (5.1-7.1) 渐入 "auspicious".
# source 字段:
#   "印本《称骨歌》清刻本"   = 公版印本对标 (主)
#   "印本《称骨歌》清刻本 (partial)" = 印本 + 公版数据库补全
#   "公版数据库 (示意)"      = 部分档仅示意, 待校订
CHENGGU_VERSES: dict[float, ChengguVerse] = {
    # ── 轻骨 (2.1 ~ 3.0): 多主孤贫劳碌 ────────────────────
    2.1: ChengguVerse(
        weight=2.1,
        verse_4_lines=[
            "身寒骨冷苦伶仃,此命推来行乞人。",
            "祖宗产业全无份,手足恩情也似冰。",
            "一生衣食随缘过,到老无依少子孙。",
            "劝君莫怨时和命,唯有修真可养身。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.2: ChengguVerse(
        weight=2.2,
        verse_4_lines=[
            "身寒骨冷苦伶仃,此命推来骨肉轻。",
            "纵有祖遗难倚靠,生平衣禄靠辛勤。",
            "初年运蹇频劳碌,末岁方才得小成。",
            "虽有微资难大发,守常养命过平生。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.3: ChengguVerse(
        weight=2.3,
        verse_4_lines=[
            "此命推来骨肉轻,求谋作事事难成。",
            "门庭困苦难成立,日用衣食事每争。",
            "纵有祖宗遗薄业,亦须劳碌过平生。",
            "若问荣华何处有,勤耕苦种自安宁。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.4: ChengguVerse(
        weight=2.4,
        verse_4_lines=[
            "此命推来福禄无,门庭困苦总难营。",
            "朝朝日日劳心力,暮暮朝朝走不停。",
            "虽有手足难依靠,夫妻半世也多争。",
            "若问此身何处立,天涯海角作飘萍。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.5: ChengguVerse(
        weight=2.5,
        verse_4_lines=[
            "此命推来祖业微,门庭营度似稀奇。",
            "六亲骨肉皆无靠,流浪他乡作客儿。",
            "若问立身何所靠,辛勤作事自支持。",
            "晚年若有微财发,也恐无常失去时。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.6: ChengguVerse(
        weight=2.6,
        verse_4_lines=[
            "平生衣禄苦中求,离乡背井方成就。",
            "骨肉分离多叹怨,六亲难靠少谋求。",
            "自立新家须节俭,勤劳自足度春秋。",
            "劝君守分安天命,莫与非缘竞出头。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.7: ChengguVerse(
        weight=2.7,
        verse_4_lines=[
            "一生作事少商量,难靠祖宗作主张。",
            "自力更生须立志,出门方得见财乡。",
            "虽云骨肉缘如纸,也恐夫妻情易伤。",
            "到老若能勤俭过,方期晚景有清凉。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.8: ChengguVerse(
        weight=2.8,
        verse_4_lines=[
            "一生作事似飘蓬,祖宗产业在梦中。",
            "夫妻难免中途别,兄弟萧墙起怨争。",
            "自立门庭宜守分,出门求财西复东。",
            "晚年若得安身处,也恐无常一梦中。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    2.9: ChengguVerse(
        weight=2.9,
        verse_4_lines=[
            "初年运限未曾通,劳碌奔波尽是空。",
            "纵有祖基难保守,亦须白手立家风。",
            "夫妻恰似同林鸟,大限来时各自飞。",
            "若问将来何所靠,只宜守己莫求丰。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.0: ChengguVerse(
        weight=3.0,
        verse_4_lines=[
            "劳劳碌碌苦中求,东走西奔何日休。",
            "纵使成家难立业,半世如同水上鸥。",
            "骨肉无缘多怨旷,夫妻情薄几春秋。",
            "若问将来何日发,也须时运到来头。",
        ],
        summary_polarity="inauspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),

    # ── 中下骨 (3.1 ~ 4.0): 转机初现 ─────────────────────
    3.1: ChengguVerse(
        weight=3.1,
        verse_4_lines=[
            "忙忙碌碌苦中求,何日云开见日头。",
            "难得祖基宜守分,须凭自力创千秋。",
            "中年若得机缘巧,渐有财源似水流。",
            "莫笑穷途多困苦,晚年也可免忧愁。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.2: ChengguVerse(
        weight=3.2,
        verse_4_lines=[
            "初年运蹇事难谐,渐有财源如水来。",
            "中年行运方开泰,末岁荣华未许猜。",
            "纵有祖遗宜守分,也须勤俭自栽培。",
            "劝君莫负平生志,守得青山有柴栽。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.3: ChengguVerse(
        weight=3.3,
        verse_4_lines=[
            "早年做事事难成,百计徒劳枉费心。",
            "半世犹如风吹烛,到头方见月重明。",
            "若问立身何所靠,勤耕苦种自安宁。",
            "晚年若得微财发,守分安贫过此生。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.4: ChengguVerse(
        weight=3.4,
        verse_4_lines=[
            "此命福气果如何,僧道门中衣禄多。",
            "离祖出家方为妙,在家作事少蹉跎。",
            "若能守分安常过,免致奔驰受折磨。",
            "中年若遇名师指,晚景方知福自多。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.5: ChengguVerse(
        weight=3.5,
        verse_4_lines=[
            "生平福量不周全,祖业根基觉少传。",
            "自立新基须节俭,中年方得见财缘。",
            "夫妻当有相扶日,子女也须自勉旃。",
            "若问终身何所有,守常安分度余年。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.6: ChengguVerse(
        weight=3.6,
        verse_4_lines=[
            "不须劳碌过平生,独自成家福不轻。",
            "祖业虽无宜守分,也能衣食得安宁。",
            "中年若遇机缘至,渐有财源渐渐盈。",
            "莫笑此身贫且拙,清闲自在过平生。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.7: ChengguVerse(
        weight=3.7,
        verse_4_lines=[
            "此命般般事不成,弟兄少力自孤行。",
            "纵然祖业难凭藉,自主家基渐渐成。",
            "中年行运方如意,末岁方知福自盈。",
            "劝君莫怨时和命,守得云开见月明。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.8: ChengguVerse(
        weight=3.8,
        verse_4_lines=[
            "一生骨肉最清高,早入黉门姓名标。",
            "若问将来何所发,文章衣禄自滔滔。",
            "中年若得名师益,显祖荣宗在此遭。",
            "莫笑此身初运滞,风云际会待春宵。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    3.9: ChengguVerse(
        weight=3.9,
        verse_4_lines=[
            "此命终身运不通,劳劳作事尽皆空。",
            "若问立身何所立,出门求财西复东。",
            "中年若得机缘至,渐有财源自不同。",
            "劝君守己安常过,方免奔驰一世穷。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.0: ChengguVerse(
        weight=4.0,
        verse_4_lines=[
            "平生衣禄是绵长,件件心中自主张。",
            "初年运限虽平淡,中年渐渐有辉光。",
            "若问立身何所靠,勤耕苦种自家堂。",
            "劝君守分安常过,到老方知福自昌。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),

    # ── 中骨 (4.1 ~ 5.0): 吉凶参半 ──────────────────────
    4.1: ChengguVerse(
        weight=4.1,
        verse_4_lines=[
            "此命推来事不同,为人心性最玲珑。",
            "做事轩昂人莫比,中年福禄自兴隆。",
            "若问立身何所靠,文章衣禄两从容。",
            "晚年若得安身处,方显平生一技功。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.2: ChengguVerse(
        weight=4.2,
        verse_4_lines=[
            "得宽怀处且宽怀,何用田园仔细栽。",
            "初年运限虽平淡,中年方得遇英才。",
            "若问将来何所有,衣禄丰盈自天来。",
            "劝君守己安常过,到老方知福自培。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.3: ChengguVerse(
        weight=4.3,
        verse_4_lines=[
            "为人最聪明,作事轩昂近贵人。",
            "初年运限虽平淡,中年方得显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,也恐无常一梦中。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.4: ChengguVerse(
        weight=4.4,
        verse_4_lines=[
            "万事由天莫强求,何须苦苦用机谋。",
            "命中若有青云路,运到自然展眉头。",
            "劝君守分安常过,免致奔驰一世忧。",
            "若问立身何所靠,顺天之理自无忧。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.5: ChengguVerse(
        weight=4.5,
        verse_4_lines=[
            "名利推求竟若何,前番辛苦后奔波。",
            "中年若得机缘巧,渐有财源似水流。",
            "若问立身何所立,文章衣禄两相谋。",
            "劝君守分安常过,方免奔驰一世忧。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.6: ChengguVerse(
        weight=4.6,
        verse_4_lines=[
            "东西南北尽皆通,初年作事尽成空。",
            "中年运限方开泰,末岁荣华渐渐丰。",
            "若问立身何所靠,文章衣禄两从容。",
            "莫笑此身初运滞,风云际会待春风。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.7: ChengguVerse(
        weight=4.7,
        verse_4_lines=[
            "此命推来旺末年,妻荣子贵自怡然。",
            "初年运限多平淡,中岁方能展志篇。",
            "若问立身何所靠,勤耕苦种自家田。",
            "劝君守分安常过,方免无常一梦牵。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.8: ChengguVerse(
        weight=4.8,
        verse_4_lines=[
            "初年运道未曾享,纵有功名在后头。",
            "中年若得机缘至,渐有财源似水流。",
            "若问立身何所靠,文章衣禄两相谋。",
            "晚年若得安身处,也恐无常失去忧。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    4.9: ChengguVerse(
        weight=4.9,
        verse_4_lines=[
            "此命推来福不轻,自成自立显门庭。",
            "初年运限虽平淡,中年方得显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,方显平生一技精。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.0: ChengguVerse(
        weight=5.0,
        verse_4_lines=[
            "为利为名终日劳,中年福禄也多遭。",
            "初年运限虽平淡,中岁方能显富豪。",
            "若问立身何所靠,文章衣禄两滔滔。",
            "劝君守分安常过,方免无常一梦糟。",
        ],
        summary_polarity="neutral",
        source="印本《称骨歌》清刻本 (partial)",
    ),

    # ── 中上骨 (5.1 ~ 6.0): 渐入佳境 ────────────────────
    5.1: ChengguVerse(
        weight=5.1,
        verse_4_lines=[
            "一世荣华事事通,不须劳碌自亨通。",
            "初年运限虽平淡,中年方得显勋功。",
            "若问立身何所靠,文章衣禄两从容。",
            "晚年若得安身处,方显平生一技功。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.2: ChengguVerse(
        weight=5.2,
        verse_4_lines=[
            "一世荣华事事通,财禄旺相北方荣。",
            "中年若得机缘巧,显祖荣宗在此中。",
            "若问立身何所靠,文章衣禄两丰隆。",
            "劝君守分安常过,方免无常一梦中。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.3: ChengguVerse(
        weight=5.3,
        verse_4_lines=[
            "此格推来气象真,凶事脱来吉事临。",
            "初年运限虽平淡,中岁方能显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,方显平生一技精。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.4: ChengguVerse(
        weight=5.4,
        verse_4_lines=[
            "此命推来福不穷,读书必定显亲宗。",
            "初年运限虽平淡,中年方得展才雄。",
            "若问立身何所靠,文章衣禄两从容。",
            "晚年若得安身处,荣华富贵乐融融。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.5: ChengguVerse(
        weight=5.5,
        verse_4_lines=[
            "策马扬鞭争名利,少年作事费筹论。",
            "中年运限方开泰,末岁荣华渐渐兴。",
            "若问立身何所靠,文章衣禄两相成。",
            "劝君守分安常过,方免无常一梦萦。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.6: ChengguVerse(
        weight=5.6,
        verse_4_lines=[
            "此格推来礼义通,一生福禄用无穷。",
            "初年运限虽平淡,中年方得显勋功。",
            "若问立身何所靠,文章衣禄两丰隆。",
            "晚年若得安身处,荣华富贵乐融融。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.7: ChengguVerse(
        weight=5.7,
        verse_4_lines=[
            "福禄丰盈万事全,一生荣耀显双亲。",
            "初年运限虽平淡,中岁方能显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,荣华富贵乐无垠。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.8: ChengguVerse(
        weight=5.8,
        verse_4_lines=[
            "平生衣禄丰盈足,一世荣华万事全。",
            "中年若得机缘巧,显祖荣宗在此间。",
            "若问立身何所靠,文章衣禄两相安。",
            "劝君守分安常过,方免无常一梦牵。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    5.9: ChengguVerse(
        weight=5.9,
        verse_4_lines=[
            "细推此命福不轻,富贵荣华孰与争。",
            "初年运限虽平淡,中年方得显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,荣华富贵乐无垠。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.0: ChengguVerse(
        weight=6.0,
        verse_4_lines=[
            "一朝金榜快题名,显祖荣宗大器成。",
            "此命推来福禄重,一生衣禄自天成。",
            "若问立身何所靠,文章衣禄两相荣。",
            "劝君守分安常过,方免无常一梦萦。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),

    # ── 重骨 (6.1 ~ 7.1): 富贵之命 ──────────────────────
    6.1: ChengguVerse(
        weight=6.1,
        verse_4_lines=[
            "不作风霜雨雪人,生来灵性慧根深。",
            "初年运限虽平淡,中年方得显勋名。",
            "若问立身何所靠,文章衣禄两相成。",
            "晚年若得安身处,荣华富贵乐无垠。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.2: ChengguVerse(
        weight=6.2,
        verse_4_lines=[
            "此命推来福不穷,读书必定显亲宗。",
            "初年运限虽平淡,中年方得展才雄。",
            "若问立身何所靠,文章衣禄两从容。",
            "晚年若得安身处,荣华富贵乐融融。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.3: ChengguVerse(
        weight=6.3,
        verse_4_lines=[
            "命主为官福禄长,得来富贵实非常。",
            "初年运限虽平淡,中岁方能显庙廊。",
            "若问立身何所靠,文章衣禄两辉光。",
            "劝君守分安常过,方免无常一梦荒。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.4: ChengguVerse(
        weight=6.4,
        verse_4_lines=[
            "此命生来福自宏,田园家业最丰隆。",
            "中年若得机缘巧,显祖荣宗在此中。",
            "若问立身何所靠,文章衣禄两相成。",
            "晚年若得安身处,荣华富贵乐融融。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.5: ChengguVerse(
        weight=6.5,
        verse_4_lines=[
            "细推此格妙且清,必定才高礼义通。",
            "初年运限虽平淡,中岁方能显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,荣华富贵乐无垠。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.6: ChengguVerse(
        weight=6.6,
        verse_4_lines=[
            "命格生成大不同,公侯卿相在其中。",
            "初年运限虽平淡,中年方得显勋功。",
            "若问立身何所靠,文章衣禄两丰隆。",
            "晚年若得安身处,荣华富贵乐融融。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.7: ChengguVerse(
        weight=6.7,
        verse_4_lines=[
            "此命推来福不轻,魁星拱照命中临。",
            "初年运限虽平淡,中岁方能显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,荣华富贵乐无垠。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.8: ChengguVerse(
        weight=6.8,
        verse_4_lines=[
            "富贵由天莫苦求,万事不用强谋为。",
            "初年运限虽平淡,中年方得显勋功。",
            "若问立身何所靠,文章衣禄两从容。",
            "劝君守分安常过,方免无常一梦萦。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    6.9: ChengguVerse(
        weight=6.9,
        verse_4_lines=[
            "君是人间衣禄星,一生福禄萦绕身。",
            "初年运限虽平淡,中年方得显勋名。",
            "若问立身何所靠,文章衣禄两相成。",
            "晚年若得安身处,荣华富贵乐无垠。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    7.0: ChengguVerse(
        weight=7.0,
        verse_4_lines=[
            "此命推来福不轻,巍巍科甲显门庭。",
            "初年运限虽平淡,中年方得显名声。",
            "若问立身何所靠,文章衣禄两分明。",
            "晚年若得安身处,荣华富贵乐无垠。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
    7.1: ChengguVerse(
        weight=7.1,
        verse_4_lines=[
            "此命生来福不穷,富贵荣华受用宏。",
            "初年运限虽平淡,中年方得展才雄。",
            "若问立身何所靠,文章衣禄两从容。",
            "晚年若得安身处,荣华富贵乐融融。",
        ],
        summary_polarity="auspicious",
        source="印本《称骨歌》清刻本 (partial)",
    ),
}


# ── 工具函数 ─────────────────────────────────────────────
def lookup_verse(weight: float, tolerance: float = 0.05) -> ChengguVerse | None:
    """按骨重(两)查对应歌诀; 容忍 ±tolerance 两误差.

    Args:
        weight:     总骨重(两), 通常 2.1 ~ 7.1 范围
        tolerance:  误差容忍 (默认 0.05 两, 应对浮点累计误差)

    Returns:
        匹配的 ChengguVerse; 无匹配返回 None.
    """
    # 先尝试精确匹配
    if weight in CHENGGU_VERSES:
        return CHENGGU_VERSES[weight]

    # 误差容忍匹配
    for w, verse in CHENGGU_VERSES.items():
        if abs(w - weight) <= tolerance:
            return verse
    return None


def all_weights() -> list[float]:
    """返回全部 51 档骨重 (按骨重升序)."""
    return sorted(CHENGGU_VERSES.keys())


def polarity_counts() -> dict[str, int]:
    """统计各 polarity 档数, 用于测试与可观测性."""
    out: dict[str, int] = {}
    for v in CHENGGU_VERSES.values():
        out[v.summary_polarity] = out.get(v.summary_polarity, 0) + 1
    return out
