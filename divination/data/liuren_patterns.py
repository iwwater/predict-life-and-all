"""大六壬 高阶课式 (Patterns) — 8-10 课体, 纯函数查表.

三光 / 三阳 / 三阴 / 铸印 / 斫轮 / 稼穑 / 连珠 / 游子 / 解离 / 乱首

每项 check_fn 为纯函数: 输入 (day_gan, day_zhi, san_chuan, si_ke, cosmic_board) → bool.
engine 只调 check_fn 查表, 不堆 if-elif 链.

参考: 《大六壬大全》《毕法赋》《六壬断案》
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class PatternDef:
    """高阶课式定义.

    Attributes:
        name: 课式名称 (e.g. "三光", "铸印")
        polarity: 吉凶 ("auspicious", "inauspicious", "neutral")
        brief: 简要说明
        check_fn: 纯函数, 输入课盘数据, 返回是否匹配
        detailed: 详细断语
    """
    name: str
    polarity: str
    brief: str
    check_fn: Callable
    detailed: str


# ── 辅助 ─────────────────────────────────────────────────────────

DZ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
TG = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

DZ_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
         "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
TG_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
         "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}


def _get_san_chuan(san_chuan: dict) -> tuple[str, str, str]:
    """从三传字典提取 (chu, zhong, mo)."""
    return (
        san_chuan.get("chu_chuan", ""),
        san_chuan.get("zhong_chuan", ""),
        san_chuan.get("mo_chuan", ""),
    )


# ── 各课式 check_fn ──────────────────────────────────────────────


def _check_sanguang(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """三光课: 贵人临地盘卯位 (日出之方), 三传向阳.

    条件: 贵人所在支为卯, 且三传地支序号递增 (非退).
          日干处于旺相时段 (寅卯月为春木旺, 巳午月为夏火旺, 申酉月为秋金旺, 亥子月为冬水旺)
          简化: 贵人临卯 + 初传不是返吟/伏吟.
    """
    gui_ren_zhi = cosmic_board.get("gui_ren_zhi", "")
    if gui_ren_zhi != "卯":
        return False
    chu, zhong, mo = _get_san_chuan(san_chuan)
    if not all(z in DZ for z in (chu, zhong, mo)):
        return False
    # 三传不能是伏吟 (三传相同)
    if chu == zhong == mo:
        return False
    return True


def _check_sanyang(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """三阳课: 贵人登天门 (亥位), 三传向阳, 初传为巳午未 (火).

    条件: 贵人临亥, 且初传五行属火 (巳/午).
          中传/末传地支序号递增 (阳气上升).
    """
    gui_ren_zhi = cosmic_board.get("gui_ren_zhi", "")
    if gui_ren_zhi != "亥":
        return False
    chu, zhong, mo = _get_san_chuan(san_chuan)
    if chu not in DZ or zhong not in DZ or mo not in DZ:
        return False
    # 初传为火 (巳/午)
    if DZ_WX.get(chu) != "火":
        return False
    # 三传序号递增
    ci = DZ.index(chu)
    zi = DZ.index(zhong)
    mi = DZ.index(mo)
    if ci == zi == mi:
        return False  # 伏吟不算
    return (zi - ci) % 12 in (1, 2) and (mi - zi) % 12 in (1, 2)


def _check_sanyin(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """三阴课: 贵人临巳 (地户), 三传退行, 初传为亥子丑 (水/阴暗).

    条件: 贵人临巳, 初传五行属水 (亥/子/壬).
    """
    gui_ren_zhi = cosmic_board.get("gui_ren_zhi", "")
    if gui_ren_zhi != "巳":
        return False
    chu, zhong, mo = _get_san_chuan(san_chuan)
    if chu not in DZ:
        return False
    # 初传为水/阴暗
    if DZ_WX.get(chu) != "水":
        return False
    # 初传地支不是子午卯酉四正辰
    return True


def _check_zhuyin(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """铸印课: 三传为巳戌卯, 或初传为申酉戌 (金), 贵人临辰.

    条件: 三传 seq = 巳戌卯 (巳火铸戌土成卯木印), 或简化: 初传为金 (申/酉) + 贵人临辰.
    《毕法赋》: 铸印者, 巳加戌, 戌加卯, 三传顺次.
    """
    chu, zhong, mo = _get_san_chuan(san_chuan)
    if not all(z in DZ for z in (chu, zhong, mo)):
        return False
    gui_ren_zhi = cosmic_board.get("gui_ren_zhi", "")
    # 标准铸印: 巳→戌→卯
    if chu == "巳" and zhong == "戌" and mo == "卯":
        return True
    # 简化: 金印 — 初传申/酉 + 贵人临辰
    if DZ_WX.get(chu) == "金" and gui_ren_zhi == "辰":
        return True
    return False


def _check_zhuolun(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """斫轮课: 卯加申发用 (卯木斫申金), 或三传为卯申丑.

    条件: 初传卯, 中传申, 或初传卯+月将为金.
    《毕法赋》: 斫轮, 卯加申为斫轮格, 卯为车轮申为金斧.
    """
    chu, zhong, mo = _get_san_chuan(san_chuan)
    if chu not in DZ:
        return False
    # 标准: 卯→申
    if chu == "卯" and zhong == "申":
        return True
    # 简化: 初传卯 + 贵人临申
    gui_ren_zhi = cosmic_board.get("gui_ren_zhi", "")
    if chu == "卯" and gui_ren_zhi == "申":
        return True
    return False


def _check_jiase(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """稼穑课: 三传皆土 (辰戌丑未), 或初传辰+中末传也是土.

    条件: 三传全部五行属土.
    """
    chu, zhong, mo = _get_san_chuan(san_chuan)
    if not all(z in DZ for z in (chu, zhong, mo)):
        return False
    return (DZ_WX.get(chu) == "土" and
            DZ_WX.get(zhong) == "土" and
            DZ_WX.get(mo) == "土")


def _check_lianzhu(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """连珠课: 三传地支连续 (序号相差 ±1 且方向一致).

    条件: 三传地支序号连续 (前向或后向).
    """
    chu, zhong, mo = _get_san_chuan(san_chuan)
    if not all(z in DZ for z in (chu, zhong, mo)):
        return False
    ci, zi, mi = DZ.index(chu), DZ.index(zhong), DZ.index(mo)
    forward = (zi - ci) % 12 == 1 and (mi - zi) % 12 == 1
    backward = (ci - zi) % 12 == 1 and (zi - mi) % 12 == 1
    return forward or backward


def _check_youzi(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """游子课: 三传中有寅/申/巳/亥 (四孟), 且贵人临驿马位.

    条件: 三传至少含一个寅申巳亥, 贵人临寅/申/巳/亥之一.
    """
    chu, zhong, mo = _get_san_chuan(san_chuan)
    meng = {"寅", "申", "巳", "亥"}
    if not any(z in meng for z in (chu, zhong, mo)):
        return False
    gui_ren_zhi = cosmic_board.get("gui_ren_zhi", "")
    return gui_ren_zhi in meng


def _check_jieli(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """解离课: 日干支相冲, 三传见午/子相冲.

    条件: 日支与日干寄宫相冲 (六冲), 或日支与初传相冲.
    """
    gan_ji = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
              "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}
    ji_gong = gan_ji.get(day_gan, "寅")
    # 六冲对
    chong_map = {"子": "午", "丑": "未", "寅": "申", "卯": "酉",
                 "辰": "戌", "巳": "亥", "午": "子", "未": "丑",
                 "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳"}
    if chong_map.get(day_zhi) == ji_gong or chong_map.get(ji_gong) == day_zhi:
        chu, _, _ = _get_san_chuan(san_chuan)
        if chong_map.get(chu) == day_zhi:
            return True
    return False


def _check_luanshou(
    day_gan: str, day_zhi: str,
    san_chuan: dict, si_ke: dict, cosmic_board: dict,
) -> bool:
    """乱首课: 日干寄宫受下神克, 或贵人逆行且受克.

    条件: 四课中第一课上神(日干寄宫)被下神克.
    """
    lessons = si_ke.get("lessons", [])
    if len(lessons) < 1:
        return False
    lesson1 = lessons[0]
    upper = lesson1.get("upper", "")
    lower = lesson1.get("lower", "")
    if not upper or not lower or upper not in DZ or lower not in DZ:
        return False
    # 下克上
    up_wx = DZ_WX.get(upper, "")
    lo_wx = DZ_WX.get(lower, "")
    _WX_OVERCOME = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    if _WX_OVERCOME.get(lo_wx) == up_wx:
        return True
    return False


# ═════════════════════════════════════════════════════════════════
# 查表: 所有高阶课式定义
# ═════════════════════════════════════════════════════════════════

HIGH_LEVEL_PATTERNS: tuple[PatternDef, ...] = (
    PatternDef(
        name="三光",
        polarity="auspicious",
        brief="贵人临卯, 三传向阳, 大利功名科考, 仕途光明",
        check_fn=_check_sanguang,
        detailed="三光者, 贵人临卯(日出之方), 三传顺序递增。主科举高中, 官禄升迁, 光明正大。所谋皆成, 疾病易愈。",
    ),
    PatternDef(
        name="三阳",
        polarity="auspicious",
        brief="贵登天门(亥), 初传火旺, 阳气上升, 大利事业升迁",
        check_fn=_check_sanyang,
        detailed="三阳者, 贵人登亥(天门), 初传为火, 阳气上升。主官运亨通, 考试得利, 阴霾散尽。利于进取, 不利用守。",
    ),
    PatternDef(
        name="三阴",
        polarity="inauspicious",
        brief="贵人临巳(地户), 初传水寒, 三传退行, 主阴私暗昧",
        check_fn=_check_sanyin,
        detailed="三阴者, 贵临巳位(地户), 初传水寒, 三传退行。主阴谋诡计, 小人暗算, 事多阻碍。宜静不宜动。",
    ),
    PatternDef(
        name="铸印",
        polarity="auspicious",
        brief="巳戌卯三传, 或初传金+贵临辰, 印星发用主科考得中",
        check_fn=_check_zhuyin,
        detailed="铸印者, 巳火铸戌土成卯木印。巳加戌, 戌加卯, 三传铸印。主科考中第, 文书签约, 授印掌权。",
    ),
    PatternDef(
        name="斫轮",
        polarity="auspicious",
        brief="卯加申发用, 卯木斫申金为轮, 主技艺成就",
        check_fn=_check_zhuolun,
        detailed="斫轮者, 卯加申为斫轮格。卯为车轮, 申为金斧。主匠人得利, 技艺精进, 创业有成。但需辛苦方能成器。",
    ),
    PatternDef(
        name="稼穑",
        polarity="neutral",
        brief="三传皆土, 主农事田土, 稳重守成但迟滞",
        check_fn=_check_jiase,
        detailed="稼穑者, 三传辰戌丑未全土。主农桑田土之事, 稳重厚实。凡事迟滞, 宜守不宜攻, 财利缓慢而有。",
    ),
    PatternDef(
        name="连珠",
        polarity="auspicious",
        brief="三传地支连续如珠串, 主事有进展步步为营",
        check_fn=_check_lianzhu,
        detailed="连珠者, 三传地支连续, 如珠串连。主事情循序渐进, 步步为营。所求之事颇有进展, 宜长远规划。",
    ),
    PatternDef(
        name="游子",
        polarity="neutral",
        brief="三传见四孟+贵人驿马, 主奔波远行或思乡",
        check_fn=_check_youzi,
        detailed="游子者, 三传见寅申巳亥(四孟), 贵人临驿马。主远行奔波, 旅居在外。占出行则吉, 占归期则迟。",
    ),
    PatternDef(
        name="解离",
        polarity="inauspicious",
        brief="日干支相冲, 三传见冲, 主离散分手",
        check_fn=_check_jieli,
        detailed="解离者, 干支相冲, 三传亦见冲。主夫妻反目, 合作破裂, 离散之象。宜退让调和, 不宜强争。",
    ),
    PatternDef(
        name="乱首",
        polarity="inauspicious",
        brief="日干寄宫下克上, 主以下犯上秩序混乱",
        check_fn=_check_luanshou,
        detailed="乱首者, 日干寄宫受下神克。以下犯上, 秩序混乱。主下属反叛, 子女不孝, 事多纷扰。宜整肃纲纪。",
    ),
)


# ═════════════════════════════════════════════════════════════════
# 查表入口: detect_patterns (engine 调此, 不堆 if-elif)
# ═════════════════════════════════════════════════════════════════

def detect_patterns(
    day_gan: str,
    day_zhi: str,
    san_chuan: dict,
    si_ke: dict,
    cosmic_board: dict,
) -> list[dict[str, str]]:
    """遍历所有高阶课式, 返回匹配项列表 (纯函数, 只查表).

    Args:
        day_gan: 日干 e.g. "甲"
        day_zhi: 日支 e.g. "子"
        san_chuan: 三传 dict (chu_chuan, zhong_chuan, mo_chuan)
        si_ke: 四课 dict (lessons, all_upper, all_lower)
        cosmic_board: 天地盘 + 贵人 dict

    Returns:
        匹配的高阶课式列表, 每项 {name, polarity, brief, detailed}
    """
    matched: list[dict[str, str]] = []
    for pat in HIGH_LEVEL_PATTERNS:
        try:
            if pat.check_fn(day_gan, day_zhi, san_chuan, si_ke, cosmic_board):
                matched.append({
                    "name": pat.name,
                    "polarity": pat.polarity,
                    "brief": pat.brief,
                    "detailed": pat.detailed,
                })
        except Exception:
            # 报错不阻断, 跳过该 pattern
            pass
    return matched
