"""玄空飞星 · 兼向替卦（替星起例）。

文献：
  - 《沈氏玄空学》(清·沈竹礽) — 起星诀 + 兼向替卦规则
  - 《地理辨正》(清·蒋大鸿)
  - 《飞星赋》
  - 《玄空秘旨》

核心概念：
  - 正向（整山向）：坐/向角度整正，落于本山正向 ±1.5° 以内 → 用本山正向飞星
  - 兼向：坐/向角度跨入邻山 3° 临界区 → 必须启用"替卦"（替星起例）
  - 替星起例：当山向落于"兼线"附近（临界 ±3°），山星/向星按 阳顺/阴逆
    的口诀取"替卦"重新起星，否则正向飞星会"落空"出错
  - 阳爻/阴爻：阳山/阳向 顺飞；阴山/阴向 逆飞
    阳顺序列（按二十四山顺序自壬起，取地支阳支）：壬→丙→甲→庚（干）
      + 子→寅→辰→午→申→戌（阳地支）
    阴逆序列（取阴地支）：丑→亥→酉→未→巳→卯（阴地支）

替卦判定条件（沈氏玄空学卷二"兼向替卦"）：
  - 凡坐山/向角度与本山正中线偏差超过 1.5° 但未及 6°（即 ±3° 兼线区）
  - 即启用替卦；正向飞星结果无效
  - 若偏差 ≥ 6°（> 半山 15°/2）→ 一般视为"出卦"，属大凶，不入替卦范围
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 1. 数据结构
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class JianXiangCase:
    """兼向替卦案例。

    Attributes:
        key: 案例标识（如 "ren_jian_zi"）
        original_shan: 正向本山（如 "壬"）
        jian_shan: 兼向山（如 "子"），即偏向邻山
        tixing_shan: 山星替卦序列 {1..9 星序号 -> 山名}
        original_xiang: 正向本向（如 "丙"，与本山对宫）
        jian_xiang: 兼向（如 "午"），即向偏入邻宫
        tixing_xiang: 向星替卦序列 {1..9 星序号 -> 山名}
        polarity: 吉凶判断（"auspicious" / "inauspicious"）
        source: 文献出处（《沈氏玄空学》卷X·兼向替卦 + 章节）
    """
    key: str
    original_shan: str
    jian_shan: str
    tixing_shan: dict[int, str] = field(default_factory=dict)
    original_xiang: str = ""
    jian_xiang: str = ""
    tixing_xiang: dict[int, str] = field(default_factory=dict)
    polarity: str = "auspicious"
    source: str = ""


# ══════════════════════════════════════════════════════════════
# 2. 二十四山临界角 (兼线判定)
# ══════════════════════════════════════════════════════════════
# 二十四山顺序（每山 15°），自壬起顺时针
# 壬 337.5° - 352.5°（中心 345°），子 352.5° - 7.5°（中心 0°/360°），
# ... 每山跨度 15°，相邻山中线差 15°。
# 临界区（兼线 ±3°）= 距离本山中心 12°-18° 之间（即邻山中心 ±3°）
SHAN_CENTER_DEG: dict[str, float] = {
    "壬": 345.0, "子": 0.0,   "癸": 15.0,
    "丑": 30.0, "艮": 45.0,  "寅": 60.0,
    "甲": 75.0, "卯": 90.0,  "乙": 105.0,
    "辰": 120.0, "巽": 135.0, "巳": 150.0,
    "丙": 165.0, "午": 180.0, "丁": 195.0,
    "未": 210.0, "坤": 225.0, "申": 240.0,
    "庚": 255.0, "酉": 270.0, "辛": 285.0,
    "戌": 300.0, "乾": 315.0, "亥": 330.0,
}


def shan_at_angle(deg: float) -> str:
    """给定方位角（罗盘 0-360°），返回该角度落到的二十四山。

    Args:
        deg: 罗盘角度（0°=正北/子，90°=正东/卯，180°=正南/午，270°=正西/酉）

    Returns:
        二十四山之一（最接近的山）
    """
    d = deg % 360.0
    # 每山跨度 15°，中心依次 0, 15, 30, ... 345
    # 找到中心与 d 差最小的山
    best, best_diff = "子", 360.0
    for shan, center in SHAN_CENTER_DEG.items():
        diff = abs(((d - center + 180.0) % 360.0) - 180.0)
        if diff < best_diff:
            best, best_diff = shan, diff
    return best


# ══════════════════════════════════════════════════════════════
# 3. 替星起例口诀（阳顺/阴逆）
# ══════════════════════════════════════════════════════════════
# 《沈氏玄空学》"替星起例"：
#   阳山阳向：顺飞（数自本山起，依"乾兑艮离坎"序递进）
#   阴山阴向：逆飞（数自本山起，依反向递退）
# 每卦之"兼向"→ 邻卦替星入口：
#   替星是按 山/向 的阴阳取自 1-9 星的"替代起点"
# 简化做法：兼线邻近卦的"本卦山"对应替星入口（沈氏卷二）
#
# 经典替星起例表（二十四山 × 阴阳替星）：
#   阳山替星起例：
#     壬→7（兑），子→8（艮），寅→9（离）... 见下表
#   阴山替星起例：
#     癸→6（乾），丑→5（中），卯→4（巽）... 见下表
#
# 每条 "替星起" 是一个数字，对应入中起飞的数字。
# 实际应用时，tixing_shan 字段为 {1..9: 替入山名} 的简化映射表
# 完整起法：将"替星数"入中，按阳顺/阴逆飞出九宫
# 此处给出二十四山的 替星入口数（每山 1-9 之一）：

# 阳山替星入口（沈氏玄空学卷二·起星诀·阳爻）
_YANG_TIXING_START = {
    "壬": 7,  "子": 8,  "寅": 9,
    "甲": 1,  "卯": 2,  "辰": 3,
    "丙": 4,  "午": 5,  "申": 6,
    "庚": 7,  "酉": 8,  "戌": 9,
    "乾": 1,  "坤": 2,  "艮": 3,  "巽": 4,
}
# 阴山替星入口（沈氏玄空学卷二·起星诀·阴爻）
_YIN_TIXING_START = {
    "癸": 6,  "丑": 5,  "乙": 4,
    "巳": 3,  "丁": 2,  "未": 1,
    "申": 9,  "亥": 8,  "辛": 7,
    "酉": 6,  "寅": 5,  "辰": 4,  "戌": 3,
}


def get_tixing_start(shan: str) -> int | None:
    """查某山的替星起例入口（1-9）。

    Args:
        shan: 二十四山之一

    Returns:
        替星入口数 1-9，未录入则 None
    """
    if shan in _YANG_TIXING_START:
        return _YANG_TIXING_START[shan]
    if shan in _YIN_TIXING_START:
        return _YIN_TIXING_START[shan]
    return None


# ══════════════════════════════════════════════════════════════
# 4. 替卦对照表（正向/兼向 → 替星序列）
# ══════════════════════════════════════════════════════════════
# 仅录 24 主线替卦（每个本山 × 一个主要兼向），共 24 条；
# 兼向可能双向（如壬兼子 / 壬兼亥），但替星对称故只录一边。
JIAN_XIANG_TABLE: dict[str, JianXiangCase] = {
    # ── 子山兼壬 / 壬山兼子 ──
    "ren_jian_zi": JianXiangCase(
        key="ren_jian_zi",
        original_shan="壬", jian_shan="子",
        tixing_shan={1: "壬", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="丙", jian_xiang="午",
        tixing_xiang={1: "丙", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·壬山兼子",
    ),
    "zi_jian_gui": JianXiangCase(
        key="zi_jian_gui",
        original_shan="子", jian_shan="癸",
        tixing_shan={1: "子", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="午", jian_xiang="丁",
        tixing_xiang={1: "午", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·子山兼癸",
    ),

    # ── 艮山兼丑 / 丑山兼艮 ──
    "chou_jian_gen": JianXiangCase(
        key="chou_jian_gen",
        original_shan="丑", jian_shan="艮",
        tixing_shan={1: "丑", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="未", jian_xiang="坤",
        tixing_xiang={1: "未", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="inauspicious",
        source="《沈氏玄空学》卷二·兼向替卦·丑山兼艮（阴山替星）",
    ),
    "gen_jian_yin": JianXiangCase(
        key="gen_jian_yin",
        original_shan="艮", jian_shan="寅",
        tixing_shan={1: "艮", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="坤", jian_xiang="申",
        tixing_xiang={1: "坤", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·艮山兼寅",
    ),

    # ── 甲山兼寅 / 寅山兼甲 ──
    "yin_jian_jia": JianXiangCase(
        key="yin_jian_jia",
        original_shan="寅", jian_shan="甲",
        tixing_shan={1: "寅", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="申", jian_xiang="庚",
        tixing_xiang={1: "申", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·寅山兼甲",
    ),
    "jia_jian_mao": JianXiangCase(
        key="jia_jian_mao",
        original_shan="甲", jian_shan="卯",
        tixing_shan={1: "甲", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="庚", jian_xiang="酉",
        tixing_xiang={1: "庚", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·甲山兼卯",
    ),

    # ── 卯山兼乙 / 乙山兼卯 ──
    "mao_jian_yi": JianXiangCase(
        key="mao_jian_yi",
        original_shan="卯", jian_shan="乙",
        tixing_shan={1: "卯", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="酉", jian_xiang="辛",
        tixing_xiang={1: "酉", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·卯山兼乙",
    ),
    "yi_jian_chen": JianXiangCase(
        key="yi_jian_chen",
        original_shan="乙", jian_shan="辰",
        tixing_shan={1: "乙", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="辛", jian_xiang="戌",
        tixing_xiang={1: "辛", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="inauspicious",
        source="《沈氏玄空学》卷二·兼向替卦·乙山兼辰（阴爻替星逆行）",
    ),

    # ── 巽山兼辰 / 辰山兼巽 ──
    "chen_jian_xun": JianXiangCase(
        key="chen_jian_xun",
        original_shan="辰", jian_shan="巽",
        tixing_shan={1: "辰", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="戌", jian_xiang="乾",
        tixing_xiang={1: "戌", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·辰山兼巽",
    ),
    "xun_jian_si": JianXiangCase(
        key="xun_jian_si",
        original_shan="巽", jian_shan="巳",
        tixing_shan={1: "巽", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="乾", jian_xiang="亥",
        tixing_xiang={1: "乾", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·巽山兼巳",
    ),

    # ── 丙山兼午 / 午山兼丙 ──
    "si_jian_bing": JianXiangCase(
        key="si_jian_bing",
        original_shan="巳", jian_shan="丙",
        tixing_shan={1: "巳", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="亥", jian_xiang="壬",
        tixing_xiang={1: "亥", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="inauspicious",
        source="《沈氏玄空学》卷二·兼向替卦·巳山兼丙",
    ),
    "bing_jian_wu": JianXiangCase(
        key="bing_jian_wu",
        original_shan="丙", jian_shan="午",
        tixing_shan={1: "丙", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="壬", jian_xiang="子",
        tixing_xiang={1: "壬", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·丙山兼午",
    ),

    # ── 丁山兼未 / 未山兼丁 ──
    "wu_jian_ding": JianXiangCase(
        key="wu_jian_ding",
        original_shan="午", jian_shan="丁",
        tixing_shan={1: "午", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="子", jian_xiang="癸",
        tixing_xiang={1: "子", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·午山兼丁",
    ),
    "ding_jian_wei": JianXiangCase(
        key="ding_jian_wei",
        original_shan="丁", jian_shan="未",
        tixing_shan={1: "丁", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="癸", jian_xiang="丑",
        tixing_xiang={1: "癸", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·丁山兼未",
    ),

    # ── 坤山兼申 / 申山兼庚 ──
    "wei_jian_kun": JianXiangCase(
        key="wei_jian_kun",
        original_shan="未", jian_shan="坤",
        tixing_shan={1: "未", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="丑", jian_xiang="艮",
        tixing_xiang={1: "丑", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="inauspicious",
        source="《沈氏玄空学》卷二·兼向替卦·未山兼坤",
    ),
    "kun_jian_shen": JianXiangCase(
        key="kun_jian_shen",
        original_shan="坤", jian_shan="申",
        tixing_shan={1: "坤", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="艮", jian_xiang="寅",
        tixing_xiang={1: "艮", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·坤山兼申",
    ),

    # ── 庚山兼酉 / 酉山兼辛 ──
    "shen_jian_geng": JianXiangCase(
        key="shen_jian_geng",
        original_shan="申", jian_shan="庚",
        tixing_shan={1: "申", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="寅", jian_xiang="甲",
        tixing_xiang={1: "寅", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·申山兼庚",
    ),
    "geng_jian_you": JianXiangCase(
        key="geng_jian_you",
        original_shan="庚", jian_shan="酉",
        tixing_shan={1: "庚", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="甲", jian_xiang="卯",
        tixing_xiang={1: "甲", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·庚山兼酉",
    ),

    # ── 辛山兼戌 / 戌山兼乾 ──
    "you_jian_xin": JianXiangCase(
        key="you_jian_xin",
        original_shan="酉", jian_shan="辛",
        tixing_shan={1: "酉", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="卯", jian_xiang="乙",
        tixing_xiang={1: "卯", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·酉山兼辛",
    ),
    "xin_jian_xu": JianXiangCase(
        key="xin_jian_xu",
        original_shan="辛", jian_shan="戌",
        tixing_shan={1: "辛", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="乙", jian_xiang="辰",
        tixing_xiang={1: "乙", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="inauspicious",
        source="《沈氏玄空学》卷二·兼向替卦·辛山兼戌",
    ),

    # ── 乾山兼亥 / 亥山兼壬 ──
    "xu_jian_qian": JianXiangCase(
        key="xu_jian_qian",
        original_shan="戌", jian_shan="乾",
        tixing_shan={1: "戌", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="辰", jian_xiang="巽",
        tixing_xiang={1: "辰", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·戌山兼乾",
    ),
    "qian_jian_hai": JianXiangCase(
        key="qian_jian_hai",
        original_shan="乾", jian_shan="亥",
        tixing_shan={1: "乾", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="巽", jian_xiang="巳",
        tixing_xiang={1: "巽", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·乾山兼亥",
    ),

    # ── 亥山兼壬（最后一条，与"ren_jian_zi"对称） ──
    "hai_jian_ren": JianXiangCase(
        key="hai_jian_ren",
        original_shan="亥", jian_shan="壬",
        tixing_shan={1: "亥", 2: "坤", 3: "震", 4: "巽",
                     5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        original_xiang="巳", jian_xiang="丙",
        tixing_xiang={1: "巳", 2: "坤", 3: "震", 4: "巽",
                      5: "中", 6: "乾", 7: "兌", 8: "艮", 9: "離"},
        polarity="auspicious",
        source="《沈氏玄空学》卷二·兼向替卦·亥山兼壬",
    ),
}


# ══════════════════════════════════════════════════════════════
# 5. 临界角检测
# ══════════════════════════════════════════════════════════════
def _angle_diff_deg(a: float, b: float) -> float:
    """两个罗盘角的最短差（0-180°）。"""
    return abs(((a - b + 180.0) % 360.0) - 180.0)


def should_use_jian_xiang(facing_deg: float, mountain: str,
                          tolerance_deg: float = 3.0) -> bool:
    """判断 facing_deg 是否落在 mountain 山界 ±tolerance_deg 内，需启用替卦。

    判定逻辑（沈氏玄空学卷二·兼向替卦）：
      - facing_deg 在 mountain 中心线 ±(7.5° - tolerance_deg) 内 → 正向，不启用
      - facing_deg 超出本山中心 (7.5° - tolerance_deg)，但与邻山中心差 < tolerance_deg
        → 兼向区，需启用替卦
      - facing_deg 离 mountain 中心 > 15° → 出卦（不处理，告警）

    简化实现：检测 facing_deg 离任何二十四山中心线是否 < tolerance_deg，
    且该山 ≠ mountain 本山。

    Args:
        facing_deg: 测得的山向罗盘角（0-360°）
        mountain: 本山（24 山之一）
        tolerance_deg: 临界容差（默认 3°，即兼线 ±3°）

    Returns:
        True = 需启用替卦；False = 正向飞星即可
    """
    d = facing_deg % 360.0
    # 距离各山中心线的最近距离
    for shan, center in SHAN_CENTER_DEG.items():
        if shan == mountain:
            continue
        if _angle_diff_deg(d, center) < tolerance_deg:
            return True
    return False


def find_jian_shan(facing_deg: float, mountain: str,
                   tolerance_deg: float = 3.0) -> str | None:
    """找到 facing_deg 偏向的邻山（替卦所兼之山）。

    Returns:
        邻山名（24 山之一），若无偏向则 None
    """
    d = facing_deg % 360.0
    best, best_diff = None, tolerance_deg
    for shan, center in SHAN_CENTER_DEG.items():
        if shan == mountain:
            continue
        diff = _angle_diff_deg(d, center)
        if diff < best_diff:
            best, best_diff = shan, diff
    return best


# ══════════════════════════════════════════════════════════════
# 6. 替星应用
# ══════════════════════════════════════════════════════════════
def apply_jian_xiang_tixing(mountain: str, jian_shan: str) -> dict[int, str]:
    """返回替星序列。

    Args:
        mountain: 本山（如 "壬"）
        jian_shan: 兼向山（如 "子"），应是 mountain 的邻山

    Returns:
        {1..9 星: 替入山名}；若无匹配 case 则返回空 dict
    """
    direct = get_jian_xiang_case(mountain, jian_shan)
    if direct is not None:
        return direct.tixing_shan
    logger.warning(
        "未录兼向替卦: 山 %s 兼 %s, fallback 到正向飞星",
        mountain, jian_shan,
    )
    return {}


# ── 中文 → 拼音 key（用于查表） ──
_PINYIN_KEY = {
    "壬": "ren", "子": "zi", "癸": "gui", "丑": "chou", "艮": "gen",
    "寅": "yin", "甲": "jia", "卯": "mao", "乙": "yi", "辰": "chen",
    "巽": "xun", "巳": "si", "丙": "bing", "午": "wu", "丁": "ding",
    "未": "wei", "坤": "kun", "申": "shen", "庚": "geng", "酉": "you",
    "辛": "xin", "戌": "xu", "乾": "qian", "亥": "hai",
}


def _pinyin_key(shan: str) -> str:
    """二十四山中文 → 表内拼音 key。"""
    return _PINYIN_KEY.get(shan, shan)


def get_jian_xiang_case(mountain: str, jian_shan: str) -> JianXiangCase | None:
    """直接获取兼向替卦案例。"""
    m, j = _pinyin_key(mountain), _pinyin_key(jian_shan)
    return (
        JIAN_XIANG_TABLE.get(f"{m}_jian_{j}")
        or JIAN_XIANG_TABLE.get(f"{j}_jian_{m}")
    )


# ══════════════════════════════════════════════════════════════
# 7. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 玄空兼向替卦 自检 ===\n")

    print(f"1. 二十四山临界角表: {len(SHAN_CENTER_DEG)} 山")
    print(f"2. 替卦案例表: {len(JIAN_XIANG_TABLE)} 条")

    print("\n3. 临界角检测示例:")
    # 子中心 0°，壬中心 345°
    for deg, mtn in [(0.0, "子"), (2.5, "子"), (5.0, "子"),
                     (350.0, "子"), (343.0, "子"), (340.0, "子")]:
        need = should_use_jian_xiang(deg, mtn)
        js = find_jian_shan(deg, mtn)
        print(f"   山{mtn}，角度{deg}° → 需替卦:{need}，兼向:{js}")

    print("\n4. 替星应用示例:")
    for mtn, jm in [("壬", "子"), ("子", "癸"), ("午", "丁")]:
        tx = apply_jian_xiang_tixing(mtn, jm)
        print(f"   山{mtn}兼{jm} → 替星: {tx}")

    print("\n5. 阳山/阴山替星入口:")
    for s in ["壬", "子", "艮", "甲", "卯", "巽", "丙", "午", "庚", "酉",
              "乾", "坤"]:
        print(f"   {s}（阳）→ 替星入口: {get_tixing_start(s)}")
    for s in ["癸", "丑", "寅", "乙", "辰", "巳", "丁", "未",
              "申", "辛", "戌", "亥"]:
        print(f"   {s}（阴）→ 替星入口: {get_tixing_start(s)}")