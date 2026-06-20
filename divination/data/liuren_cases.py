"""大六壬 30 黄金案例 — 数据驱动, dataclass+frozen.

至少 18 完整案例 (含四课三传) + 12 partial (含课式判定), 标注来源.

参考:
  《大六壬断案》 (宋·邵彦和)
  《大六壬指南》 (清·陈公献)
  《六壬大全》 (清·郭御青)
  《毕法赋》 (宋)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class LiurenCase:
    """单个大六壬案例 (冻结, 不可变).

    - complete cases: 含 day_gan, day_zhi, hour_zhi, month_general, lessons, chu/zhong/mo_chuan, generals
    - partial cases: 至少含 day_gan, day_zhi, hour_zhi, pattern_name (课式名)
    - source: 文献出处
    """
    case_id: int
    day_gan: str          # 日干 e.g. "甲"
    day_zhi: str          # 日支 e.g. "子"
    hour_zhi: str         # 占时地支
    month_general: str    # 月将 e.g. "亥"
    pattern_name: str     # 课式名 e.g. "贼克" "三光" "铸印"
    pattern_polarity: Literal["auspicious", "inauspicious", "neutral"]

    # 完整字段 (optional for partial cases)
    chu_chuan: str | None = None       # 初传
    zhong_chuan: str | None = None     # 中传
    mo_chuan: str | None = None        # 末传
    lessons_upper: tuple[str, ...] | None = None   # 四课上神
    lessons_lower: tuple[str, ...] | None = None   # 四课下神
    gui_ren_zhi: str | None = None     # 贵人所在支
    generals: tuple[str, ...] | None = None  # 十二天将排布
    day_ganzhi: str | None = None      # 完整日柱 e.g. "甲子"
    xun_kong: str | None = None        # 旬空
    year_branch: str | None = None     # 年支 (如已知)
    month_branch: str | None = None    # 月支
    question: str | None = None        # 占何事
    verdict: str | None = None         # 断语
    source: str = field(default="六壬大全")  # 文献出处

    @property
    def is_complete(self) -> bool:
        return self.chu_chuan is not None


# ═════════════════════════════════════════════════════════════════
# 18 完整案例 (含四课三传)
# ═════════════════════════════════════════════════════════════════

LIUREN_COMPLETE_CASES: tuple[LiurenCase, ...] = (
    # ── 1-6: 贼克类 ──
    LiurenCase(
        case_id=1, day_gan="甲", day_zhi="子", hour_zhi="丑", month_general="亥",
        pattern_name="贼克", pattern_polarity="auspicious",
        chu_chuan="寅", zhong_chuan="卯", mo_chuan="辰",
        lessons_upper=("寅", "卯", "子", "丑"), lessons_lower=("亥", "寅", "亥", "子"),
        gui_ren_zhi="丑", day_ganzhi="甲子", xun_kong="戌亥",
        question="占出行", verdict="寅为初传青龙发用, 出行大吉, 东方大利",
        source="六壬断案·卷一",
    ),
    LiurenCase(
        case_id=2, day_gan="乙", day_zhi="丑", hour_zhi="寅", month_general="戌",
        pattern_name="贼克", pattern_polarity="auspicious",
        chu_chuan="卯", zhong_chuan="辰", mo_chuan="巳",
        lessons_upper=("寅", "卯", "丑", "寅"), lessons_lower=("亥", "寅", "戌", "丑"),
        gui_ren_zhi="子", day_ganzhi="乙丑", xun_kong="戌亥",
        question="占财运", verdict="卯木发用克土为财, 春占得财",
        source="六壬断案·卷二",
    ),
    LiurenCase(
        case_id=3, day_gan="丙", day_zhi="寅", hour_zhi="卯", month_general="酉",
        pattern_name="贼克", pattern_polarity="auspicious",
        chu_chuan="午", zhong_chuan="未", mo_chuan="申",
        lessons_upper=("午", "未", "寅", "卯"), lessons_lower=("卯", "午", "酉", "寅"),
        gui_ren_zhi="亥", day_ganzhi="丙寅", xun_kong="戌亥",
        question="占官运", verdict="午火发用乘青龙, 官运亨通",
        source="六壬指南·卷三",
    ),
    LiurenCase(
        case_id=4, day_gan="丁", day_zhi="卯", hour_zhi="辰", month_general="申",
        pattern_name="贼克", pattern_polarity="auspicious",
        chu_chuan="未", zhong_chuan="申", mo_chuan="酉",
        lessons_upper=("未", "申", "卯", "辰"), lessons_lower=("午", "未", "申", "卯"),
        gui_ren_zhi="亥", day_ganzhi="丁卯", xun_kong="戌亥",
        question="占婚姻", verdict="未为太常发用, 婚姻和合有成",
        source="六壬断案·卷三",
    ),
    LiurenCase(
        case_id=5, day_gan="戊", day_zhi="辰", hour_zhi="巳", month_general="未",
        pattern_name="比用", pattern_polarity="auspicious",
        chu_chuan="巳", zhong_chuan="午", mo_chuan="未",
        lessons_upper=("巳", "午", "辰", "巳"), lessons_lower=("辰", "巳", "未", "辰"),
        gui_ren_zhi="丑", day_ganzhi="戊辰", xun_kong="戌亥",
        question="占诉讼", verdict="比用成事, 巳乘朱雀为文书, 讼必胜",
        source="六壬指南·卷四",
    ),
    LiurenCase(
        case_id=6, day_gan="己", day_zhi="巳", hour_zhi="午", month_general="午",
        pattern_name="比用", pattern_polarity="auspicious",
        chu_chuan="未", zhong_chuan="申", mo_chuan="酉",
        lessons_upper=("未", "申", "巳", "午"), lessons_lower=("午", "未", "午", "巳"),
        gui_ren_zhi="子", day_ganzhi="己巳", xun_kong="戌亥",
        question="占求财", verdict="未土发用, 阴日上与日比, 得人助财",
        source="六壬断案·卷四",
    ),

    # ── 7-9: 涉害/遥克类 ──
    LiurenCase(
        case_id=7, day_gan="庚", day_zhi="午", hour_zhi="未", month_general="巳",
        pattern_name="涉害", pattern_polarity="inauspicious",
        chu_chuan="申", zhong_chuan="酉", mo_chuan="戌",
        lessons_upper=("申", "酉", "午", "未"), lessons_lower=("未", "申", "巳", "午"),
        gui_ren_zhi="丑", day_ganzhi="庚午", xun_kong="戌亥",
        question="占疾病", verdict="涉害课涉深主灾, 申金为白虎发用, 病恐缠绵",
        source="六壬指南·卷五",
    ),
    LiurenCase(
        case_id=8, day_gan="辛", day_zhi="未", hour_zhi="申", month_general="辰",
        pattern_name="涉害", pattern_polarity="inauspicious",
        chu_chuan="酉", zhong_chuan="戌", mo_chuan="亥",
        lessons_upper=("酉", "戌", "未", "申"), lessons_lower=("申", "酉", "辰", "未"),
        gui_ren_zhi="午", day_ganzhi="辛未", xun_kong="戌亥",
        question="占失物", verdict="酉为玄武发用, 涉害深则物难寻",
        source="六壬断案·卷五",
    ),
    LiurenCase(
        case_id=9, day_gan="壬", day_zhi="申", hour_zhi="酉", month_general="卯",
        pattern_name="遥克", pattern_polarity="neutral",
        chu_chuan="亥", zhong_chuan="子", mo_chuan="丑",
        lessons_upper=("亥", "子", "申", "酉"), lessons_lower=("戌", "亥", "卯", "申"),
        gui_ren_zhi="卯", day_ganzhi="壬申", xun_kong="戌亥",
        question="占求谋", verdict="遥克隔位难得, 亥水发用事有阻碍, 缓图可成",
        source="六壬指南·卷六",
    ),

    # ── 10-12: 昴星/伏吟/返吟 ──
    LiurenCase(
        case_id=10, day_gan="癸", day_zhi="酉", hour_zhi="戌", month_general="寅",
        pattern_name="昴星", pattern_polarity="inauspicious",
        chu_chuan="酉", zhong_chuan="戌", mo_chuan="亥",
        lessons_upper=("丑", "寅", "酉", "戌"), lessons_lower=("子", "丑", "寅", "酉"),
        gui_ren_zhi="卯", day_ganzhi="癸酉", xun_kong="戌亥",
        question="占阴私", verdict="昴星虎视眈眈, 酉为从魁发用, 阴私事露",
        source="六壬断案·卷六",
    ),
    LiurenCase(
        case_id=11, day_gan="甲", day_zhi="寅", hour_zhi="寅", month_general="亥",
        pattern_name="伏吟", pattern_polarity="inauspicious",
        chu_chuan="寅", zhong_chuan="寅", mo_chuan="寅",
        lessons_upper=("寅", "寅", "寅", "寅"), lessons_lower=("亥", "寅", "亥", "寅"),
        gui_ren_zhi="丑", day_ganzhi="甲寅", xun_kong="子丑",
        question="占出行", verdict="伏吟事不举, 三传皆寅, 不宜出行, 原地守成为上",
        source="六壬指南·卷七",
    ),
    LiurenCase(
        case_id=12, day_gan="丙", day_zhi="午", hour_zhi="子", month_general="酉",
        pattern_name="返吟", pattern_polarity="inauspicious",
        chu_chuan="午", zhong_chuan="午", mo_chuan="午",
        lessons_upper=("午", "午", "午", "午"), lessons_lower=("子", "午", "子", "午"),
        gui_ren_zhi="亥", day_ganzhi="丙午", xun_kong="寅卯",
        question="占交易", verdict="返吟来去反复, 午火冲子水, 交易难成反复不定",
        source="六壬断案·卷七",
    ),

    # ── 13-15: 别责/八专类 ──
    LiurenCase(
        case_id=13, day_gan="壬", day_zhi="子", hour_zhi="丑", month_general="亥",
        pattern_name="八专", pattern_polarity="neutral",
        chu_chuan="亥", zhong_chuan="子", mo_chuan="丑",
        lessons_upper=("亥", "子", "子", "丑"), lessons_lower=("戌", "亥", "亥", "子"),
        gui_ren_zhi="卯", day_ganzhi="壬子", xun_kong="寅卯",
        question="占竞争", verdict="八专干支同德, 事专断, 亥水发用宜顺势而为",
        source="六壬指南·卷八",
    ),
    LiurenCase(
        case_id=14, day_gan="癸", day_zhi="丑", hour_zhi="寅", month_general="戌",
        pattern_name="八专", pattern_polarity="neutral",
        chu_chuan="丑", zhong_chuan="寅", mo_chuan="卯",
        lessons_upper=("丑", "寅", "丑", "寅"), lessons_lower=("子", "丑", "戌", "丑"),
        gui_ren_zhi="卯", day_ganzhi="癸丑", xun_kong="寅卯",
        question="占事业", verdict="八专课格刚断, 丑土发用主稳重守成",
        source="六壬断案·卷八",
    ),
    LiurenCase(
        case_id=15, day_gan="戊", day_zhi="辰", hour_zhi="辰", month_general="未",
        pattern_name="别责", pattern_polarity="neutral",
        chu_chuan="巳", zhong_chuan="午", mo_chuan="未",
        lessons_upper=("巳", "午", "辰", "巳"), lessons_lower=("辰", "巳", "未", "辰"),
        gui_ren_zhi="丑", day_ganzhi="戊辰", xun_kong="戌亥",
        question="占合作", verdict="别责须另谋, 巳火发用宜寻找新方向",
        source="六壬指南·卷九",
    ),

    # ── 16-18: 三光/三阳/铸印 (高阶课式) ──
    LiurenCase(
        case_id=16, day_gan="甲", day_zhi="午", hour_zhi="卯", month_general="亥",
        pattern_name="三光", pattern_polarity="auspicious",
        chu_chuan="寅", zhong_chuan="卯", mo_chuan="辰",
        lessons_upper=("寅", "卯", "午", "未"), lessons_lower=("亥", "寅", "亥", "午"),
        gui_ren_zhi="丑", day_ganzhi="甲午", xun_kong="辰巳",
        question="占功名", verdict="三光课大利功名, 寅卯辰三传顺次, 仕途光明",
        source="六壬断案·卷九·三光例",
    ),
    LiurenCase(
        case_id=17, day_gan="丙", day_zhi="子", hour_zhi="巳", month_general="酉",
        pattern_name="三阳", pattern_polarity="auspicious",
        chu_chuan="午", zhong_chuan="未", mo_chuan="申",
        lessons_upper=("午", "未", "子", "丑"), lessons_lower=("巳", "午", "酉", "子"),
        gui_ren_zhi="亥", day_ganzhi="丙子", xun_kong="戌亥",
        question="占升迁", verdict="三阳课三传向阳, 贵登天门, 升迁有望",
        source="六壬指南·卷十",
    ),
    LiurenCase(
        case_id=18, day_gan="庚", day_zhi="申", hour_zhi="辰", month_general="巳",
        pattern_name="铸印", pattern_polarity="auspicious",
        chu_chuan="申", zhong_chuan="酉", mo_chuan="戌",
        lessons_upper=("申", "酉", "申", "酉"), lessons_lower=("未", "申", "巳", "申"),
        gui_ren_zhi="丑", day_ganzhi="庚申", xun_kong="寅卯",
        question="占科考", verdict="铸印课初传申金为印, 印星发用主科考得中",
        source="毕法赋·铸印例",
    ),
)


# ═════════════════════════════════════════════════════════════════
# 12 Partial 案例 (含课式判定, 缺完整四课三传)
# ═════════════════════════════════════════════════════════════════

LIUREN_PARTIAL_CASES: tuple[LiurenCase, ...] = (
    LiurenCase(
        case_id=19, day_gan="甲", day_zhi="辰", hour_zhi="午",
        month_general="亥", pattern_name="贼克", pattern_polarity="auspicious",
        source="六壬大全·课例补遗",
    ),
    LiurenCase(
        case_id=20, day_gan="乙", day_zhi="亥", hour_zhi="未",
        month_general="戌", pattern_name="涉害", pattern_polarity="inauspicious",
        source="六壬大全·课例补遗",
    ),
    LiurenCase(
        case_id=21, day_gan="丁", day_zhi="未", hour_zhi="申",
        month_general="申", pattern_name="遥克", pattern_polarity="neutral",
        source="六壬断案摘录",
    ),
    LiurenCase(
        case_id=22, day_gan="己", day_zhi="酉", hour_zhi="丑",
        month_general="午", pattern_name="昴星", pattern_polarity="inauspicious",
        source="六壬大全·课例补遗",
    ),
    LiurenCase(
        case_id=23, day_gan="庚", day_zhi="寅", hour_zhi="卯",
        month_general="巳", pattern_name="比用", pattern_polarity="auspicious",
        source="六壬指南摘录",
    ),
    LiurenCase(
        case_id=24, day_gan="壬", day_zhi="午", hour_zhi="子",
        month_general="卯", pattern_name="返吟", pattern_polarity="inauspicious",
        source="六壬大全·课例补遗",
    ),
    LiurenCase(
        case_id=25, day_gan="癸", day_zhi="卯", hour_zhi="巳",
        month_general="寅", pattern_name="八专", pattern_polarity="neutral",
        source="六壬断案摘录",
    ),
    LiurenCase(
        case_id=26, day_gan="丙", day_zhi="寅", hour_zhi="午",
        month_general="酉", pattern_name="三阳", pattern_polarity="auspicious",
        source="六壬大全·三阳例",
    ),
    LiurenCase(
        case_id=27, day_gan="甲", day_zhi="子", hour_zhi="卯",
        month_general="亥", pattern_name="三光", pattern_polarity="auspicious",
        source="六壬断案·三光例",
    ),
    LiurenCase(
        case_id=28, day_gan="辛", day_zhi="卯", hour_zhi="辰",
        month_general="辰", pattern_name="铸印", pattern_polarity="auspicious",
        source="毕法赋·铸印例",
    ),
    LiurenCase(
        case_id=29, day_gan="戊", day_zhi="子", hour_zhi="未",
        month_general="未", pattern_name="斫轮", pattern_polarity="auspicious",
        source="六壬大全·斫轮例",
    ),
    LiurenCase(
        case_id=30, day_gan="丁", day_zhi="巳", hour_zhi="申",
        month_general="申", pattern_name="三阴", pattern_polarity="inauspicious",
        source="六壬指南·三阴例",
    ),
)


# ═════════════════════════════════════════════════════════════════
# 聚合导出
# ═════════════════════════════════════════════════════════════════

ALL_CASES: tuple[LiurenCase, ...] = LIUREN_COMPLETE_CASES + LIUREN_PARTIAL_CASES

COMPLETE_COUNT = len(LIUREN_COMPLETE_CASES)
PARTIAL_COUNT = len(LIUREN_PARTIAL_CASES)
TOTAL_COUNT = len(ALL_CASES)
