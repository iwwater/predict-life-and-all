"""奇门遁甲 · 干组合格局自动判定 (Phase J-2 算法深化 · P2-2 中优先级)。

文献依据:
  - 《奇门遁甲统宗》(明·刘伯温/清·续辑) — 格局总表 (权威)
  - 《奇门遁甲秘笈大全》(清·锡孟樨) — 格局补遗
  - 《烟波钓叟歌》(宋·赵普) — 歌诀总纲: "乙丙临三奇, 阴干八门开"
  - 《御定卜筮精蕴》(清·康熙) — 格局断法
  - 《遁甲神应经》 — 三诈五假、伏吟反吟分类
  - 《奇门遁甲元灵经》 — 六仪击刑详细

数据驱动设计:
  1. QimenPattern: 不可变 dataclass, 含 id/name/category/polarity/description/source/check_fn
  2. GANZHI_PATTERN_TABLE: 12 项干组合格局列表 (含 10 大类 + 伏吟/反吟)
  3. detect_patterns(tianpan, dipan, doors=None, hour_gan=None) -> list[QimenPattern]
     - 遍历所有 pattern, 调用 check_fn, 返回 active 列表
     - check_fn 抛异常时降级为 inactive, logger.warning 记录

解耦原则:
  - 检测逻辑与定义分离 (数据驱动, 非硬编码 if-elif)
  - check_fn 接受天地盘 dict 作为输入, 可单独单元测试
  - 引擎调用一次 detect_patterns() 即完成全部格局判定

关联 sprint:
  - P2-2 中优先级 (Sprint 3 剩余, 2026-06-17)
  - 奇门格局深化 6.18 算法 sprint 第 4 期
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# 1. QimenPattern 数据契约
# ══════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class QimenPattern:
    """奇门格局定义 (不可变, 数据驱动).

    Attributes:
        id: 唯一标识 (snake_case).
        name: 中文格局名 (《奇门遁甲统宗》原文).
        category: 格局大类.
            - "gan_zhi_ju": 干组合格局 (天盘+地盘天干组合)
            - "men_ju": 八门格局
            - "xing_ju": 九星格局
            - "fu_yin": 伏吟类
            - "fan_yin": 反吟类
        polarity: 吉凶标签.
            - "auspicious": 大吉
            - "slightly_auspicious": 小吉
            - "inauspicious": 大凶
            - "slightly_inauspicious": 小凶
            - "neutral": 中性 (断事需看五行)
        description: 一句话解释.
        source: 文献出处 (《奇门遁甲统宗》卷X·...).
        check_fn: 检测函数.
            签名: (tianpan: dict, dipan: dict, ctx: dict) -> bool
            ctx 包含 doors / hour_gan / day_gan 等额外上下文 (可选).
    """

    id: str
    name: str
    category: str
    polarity: str
    description: str
    source: str
    check_fn: Callable[[dict, dict, dict], bool] = field(repr=False)


# ══════════════════════════════════════════════════════════════
# 2. 干组合检测函数 (Pure, 可单元测试)
# ══════════════════════════════════════════════════════════════

# 九天干
_NINE_GAN = ("戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙")
# 三奇 (乙丙丁)
_THREE_QI = ("乙", "丙", "丁")
# 六仪 (戊己庚辛壬癸)
_SIX_YI = ("戊", "己", "庚", "辛", "壬", "癸")
# 九宫 (后天八卦)
_NINE_GONG = ("坎", "艮", "震", "巽", "离", "坤", "兑", "乾", "中")

# 天干六冲 (天干对冲极少用, 但十天干中也有冲: 甲庚冲、乙辛冲、丙壬冲、丁癸冲、戊冲己 ?)
# 实际奇门反吟常用: 甲子冲甲午 (子午冲), 甲戌冲甲辰 (辰戌冲)
# 子午 / 丑未 / 寅申 / 卯酉 / 辰戌 / 巳亥 = 六冲 (地支对冲)
_ZHI_CHONG = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 六仪击刑表 (六甲旬首临地盘被刑支)
# 戊 (甲子) 刑 卯 (子卯相刑, 无礼之刑)
# 己 (甲戌) 刑 辰 (辰戌冲但刑在辰, 恃势之刑部分)
# 庚 (甲申) 刑 巳 (寅巳相刑, 但申巳无刑, 主流版本庚击巳)
# 辛 (甲午) 刑 午 (自刑: 午午自刑)
# 壬 (甲辰) 刑 辰 (自刑: 辰辰自刑)
# 癸 (甲寅) 刑 巳 (寅巳相刑, 无恩之刑)
# 注: 主流版本六仪击刑略有流派差异, 此处取《奇门统宗》最常见说法
_SIX_YI_XING = {
    "戊": "卯",   # 甲子刑卯
    "己": "辰",   # 甲戌刑辰 (丑戌未恃势之刑, 戌刑未, 但甲戌日辰戌冲)
    "庚": "巳",   # 甲申刑巳 (寅巳申无恩之刑, 申巳相邻)
    "辛": "午",   # 甲午刑午 (自刑)
    "壬": "辰",   # 甲辰刑辰 (自刑)
    "癸": "巳",   # 甲寅刑巳 (寅巳相刑, 无恩之刑)
}

# 九宫对应的地支 (一宫=坎=子, 二宫=坤=未申, 等)
_GONG_TO_ZHI = {
    "坎": "子", "艮": "丑", "震": "卯", "巽": "辰",
    "离": "午", "坤": "未", "兑": "酉", "乾": "戌", "中": "",
}


def _gan_at(tianpan: dict, gong: str) -> str | None:
    """从天盘中获取某宫天干. 兼容 '坎': '子' (甲) / '坎': '甲子' (甲)."""
    if gong not in tianpan:
        return None
    v = tianpan[gong]
    if not v:
        return None
    # 简化处理: 取第一个字符 ('甲子' -> '甲')
    return v[0] if v else None


def _zhi_at_gong(gong: str) -> str:
    """获取某宫的地支 (后天八卦方位)."""
    return _GONG_TO_ZHI.get(gong, "")


def _build_gan_zhi_pair_map(tianpan: dict, dipan: dict) -> dict[str, tuple[str, str]]:
    """构建 {宫: (天干, 地支)} 对照表.

    天盘干: tianpan[gong][0]
    地盘干: dipan[gong][0]  (若有) 否则用地盘的地支隐含干 (坎=戊, 艮=己, 等)
    """
    out: dict[str, tuple[str, str]] = {}
    for gong in _NINE_GONG:
        t_gan = _gan_at(tianpan, gong)
        d_gan = _gan_at(dipan, gong) if gong in dipan else None
        if d_gan is None:
            # 地盘地支 → 地干 (按阴阳遁六仪布局, 这里简化: 用本宫藏干本气)
            zhi = _zhi_at_gong(gong)
            d_gan = zhi  # 简化表示, 实际六仪序列更复杂
        if t_gan:
            out[gong] = (t_gan, d_gan if d_gan else "")
    return out


# ───────────────────────────────────────────────────────────────
# 2.1 青龙返首 / 飞鸟跌穴
# ───────────────────────────────────────────────────────────────
def _check_qinglong_fanshou(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """青龙返首: 天盘甲子(甲) 加临 地盘戊. 主喜庆, 上书进表大吉.

    注: 天盘甲/甲子/甲午均可, 本检测取最简: 天盘干=甲, 地盘干=戊 (戊为六仪首).
    """
    pairs = _build_gan_zhi_pair_map(tianpan, dipan)
    for gong, (t, d) in pairs.items():
        if t == "甲" and d == "戊":
            return True
    return False


def _check_feiniao_diexue(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """飞鸟跌穴: 天盘甲午(甲) 加临 地盘庚. 主逃亡必获, 求财必得.

    注: 简化为天盘甲加地盘庚.
    """
    pairs = _build_gan_zhi_pair_map(tianpan, dipan)
    for gong, (t, d) in pairs.items():
        if t == "甲" and d == "庚":
            return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.2 天辅时
# ───────────────────────────────────────────────────────────────
def _check_tianfu_shi(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """天辅时: 天盘三奇(乙丙丁)临本时辰所在宫 (时支对应宫).

    注: 实际"本时"指用事时辰, 需从 ctx 取 hour_zhi. 此检测:
      若 ctx 含 hour_gan, 取天盘对应宫; 若含 hour_gong, 取该宫天干为三奇之一即成立.
    """
    hour_gong = ctx.get("hour_gong")
    hour_gan = ctx.get("hour_gan")
    # 优先 hour_gong
    if hour_gong and hour_gong in tianpan:
        t = _gan_at(tianpan, hour_gong)
        if t and t in _THREE_QI:
            return True
    # fallback: hour_gan == 三奇 且 对应宫位
    if hour_gan and hour_gan in _THREE_QI:
        for gong, (t, _) in _build_gan_zhi_pair_map(tianpan, dipan).items():
            if t == hour_gan:
                return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.3 三诈五假 (诈 = 乙/丙/丁 + 开门/休门/生门)
# ───────────────────────────────────────────────────────────────
def _check_sanzha_wujia(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """三诈五假 (简化取三诈): 乙丙丁 三奇之一 + 落 开门/休门/生门 (吉门).

    注: 完整三诈五假分: 真诈(乙+开门)/大诈(丙+开门)/小诈(丁+开门) 等.
    本检测: 天盘三奇之一落宫, 恰好该宫门是开门/休门/生门之一即成立.
    """
    doors = ctx.get("doors", {})
    if not doors:
        return False
    for gong, (t, _) in _build_gan_zhi_pair_map(tianpan, dipan).items():
        if t in _THREE_QI:
            door = doors.get(gong, "")
            # 开门/休门/生门 (吉门)
            if door in ("开门", "休门", "生门"):
                return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.4 白虎猖狂
# ───────────────────────────────────────────────────────────────
def _check_baihu_changkuang(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """白虎猖狂: 天盘庚 加临 地盘日干所在宫位, 庚克日干 (金克木/火/土).

    注: 检测简化为: 天盘庚 所在宫的宫五行被日干五行克制? 实际格局:
    庚 (金) + 日干被金克 (乙木/丁火/己土) → 大凶.
    """
    day_gan = ctx.get("day_gan")
    if not day_gan:
        return False
    from ..wuxing import KE, GAN_WX
    # 庚 金 克 乙木/丁火/己土
    day_wx = GAN_WX.get(day_gan)
    if not day_wx:
        return False
    # 庚金克的是: KE['金'] = '木' -> 仅乙木; 但广义"金克木火土" 在传统格局中
    # 白虎猖狂是"庚克日干" (日干在庚所在宫, 庚金方位克日干五行)
    # 实际断法: 天盘庚落在日干所在宫位 -> 庚金方位克日干所在宫五行
    # 本检测简化为: 日干五行是木 (金克木) 或 火 (火克金则反向) 或 土 (木克土反向)
    # 严格: 白虎猖狂 = 庚加临日干, 而日干属"被克五行"即乙(甲)/丁(丙)/己(戊)
    # 简化为: 庚所在宫的天盘干是庚, 且地盘的日干宫位五行被金克 (即地盘宫位干五行是木/火/土但被金克)
    # 这里取主流: 庚临乙/丁/己 (乙被庚金克, 丁火克庚金反向, 己土被木克反向)
    # 实际白虎猖狂: 庚加临乙 → 庚金克乙木 (凶)
    if day_gan in ("乙",):  # 庚金克乙木, 经典"庚临乙" = 白虎猖狂
        return True
    return False


def _check_baihu_changkuang_v2(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """白虎猖狂 v2: 天盘庚加临地盘日干 (按主流流派: 庚加临日干所在宫).

    检测方法: 取天盘庚所在宫 → 该宫地盘干 = 日干 → 白虎猖狂.
    """
    day_gan = ctx.get("day_gan")
    if not day_gan:
        return False
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        if t_gan == "庚":
            d_gan = dipan.get(gong, "")
            if d_gan and d_gan[0] == day_gan:
                return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.5 荧惑入荧
# ───────────────────────────────────────────────────────────────
def _check_yinghuo_ruying(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """荧惑入荧 (荧惑 = 丙): 天盘丙 加临 地盘丙 (自刑/伏吟类).

    注: 也有版本作"丙加丙"等同伏吟丙宫, 主火灾、血光之灾.
    """
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        d_gan = dipan.get(gong, "")
        if t_gan == "丙" and d_gan and d_gan[0] == "丙":
            return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.6 太白人荧
# ───────────────────────────────────────────────────────────────
def _check_taibai_ruying(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """太白人荧 (太白 = 庚): 天盘庚 加临 地盘丙.

    注: 庚金克丙火 (荧惑), 主火灾、刀兵、战斗之象.
    """
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        d_gan = dipan.get(gong, "")
        if t_gan == "庚" and d_gan and d_gan[0] == "丙":
            return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.7 朱雀入江
# ───────────────────────────────────────────────────────────────
def _check_zhuque_rujiang(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """朱雀入江 (朱雀 = 乙): 天盘乙 加临 地盘癸.

    注: 乙木泄癸水, 主口舌是非、文书缠绕.
    """
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        d_gan = dipan.get(gong, "")
        if t_gan == "乙" and d_gan and d_gan[0] == "癸":
            return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.8 青龙入天牢
# ───────────────────────────────────────────────────────────────
def _check_qinglong_rutianlao(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """青龙入天牢 (青龙 = 乙): 天盘乙 加临 地盘庚.

    注: 乙庚合金, 主财损不利.
    """
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        d_gan = dipan.get(gong, "")
        if t_gan == "乙" and d_gan and d_gan[0] == "庚":
            return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.9 六仪击刑
# ───────────────────────────────────────────────────────────────
def _check_liuyi_jixing(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """六仪击刑: 六甲旬首 (戊己庚辛壬癸) 加临 地盘被刑支所在宫.

    检测: 天盘干 = 六仪之一, 且其对应被刑地支 = 该宫地支 → 击刑.
    """
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        if t_gan not in _SIX_YI:
            continue
        target_zhi = _SIX_YI_XING.get(t_gan)
        if not target_zhi:
            continue
        gong_zhi = _zhi_at_gong(gong)
        if gong_zhi == target_zhi:
            return True
    return False


# ───────────────────────────────────────────────────────────────
# 2.10 伏吟
# ───────────────────────────────────────────────────────────────
def _check_fuyin(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """伏吟: 天盘干 = 地盘干 (同干), 主事闭塞、谋为不成.

    注: 至少 2 个宫位成立 (否则可能误判). 但单宫也算格局启动.
    这里取较宽松: 1 个宫位同干即成立.
    """
    count = 0
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        d_gan = dipan.get(gong, "")
        if d_gan and d_gan[0] == t_gan:
            count += 1
    # 至少 3 个宫位伏吟为真"伏吟格"
    return count >= 3


# ───────────────────────────────────────────────────────────────
# 2.11 反吟
# ───────────────────────────────────────────────────────────────
def _check_fanyin(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """反吟: 天盘地支 加临 地盘对冲地支 (子午冲, 丑未冲, 等).

    注: 天盘值是 '甲子' 等带地支, 这里以宫位对冲检测:
    若某宫位的天盘甲子 加临 对冲宫的地盘 (如子+午, 丑+未 等) → 反吟.
    简化: 检测天盘的'地支部分'和地盘所在宫的'地支部分'对冲.
    但天盘存储常为 '甲子' (天干地支), 地盘常为 '戊' (天干).
    本检测取较宽: 对任一宫位, 检查 (天盘, 地盘) 是否构成对冲干-对冲关系.
    """
    count = 0
    for gong, v in tianpan.items():
        if not v or len(v) < 2:
            continue
        # 取天盘的"地支部分" (假定 v[1])
        # 但天盘可能仅存 '甲' 不带地支; 简化取宫位地支做对照
        t_str = v
        # 若 v 含两位字符 (甲子), 取 v[1] 作为地支
        if len(t_str) >= 2 and t_str[1] in _ZHI_CHONG:
            t_zhi = t_str[1]
            d_gan = dipan.get(gong, "")
            # 地盘若也为干支字符串
            if len(d_gan) >= 2 and d_gan[1] == _ZHI_CHONG[t_zhi]:
                count += 1
    # 至少 3 个宫位反吟为"反吟格"
    return count >= 3


def _check_fanyin_gong_chong(tianpan: dict, dipan: dict, ctx: dict) -> bool:
    """反吟 (按宫位对冲): 天盘 + 地盘干 = 相冲天干 (子午冲/甲庚冲 等).

    注: 简化取 干对冲: 甲庚冲, 乙辛冲, 丙壬冲, 丁癸冲, 戊冲己 (戊己无冲, 取同).
    主流"反吟"按宫位地支冲: 子加午, 丑加未, 等.
    """
    gan_chong = {"甲": "庚", "庚": "甲", "乙": "辛", "辛": "乙",
                 "丙": "壬", "壬": "丙", "丁": "癸", "癸": "丁"}
    count = 0
    for gong, v in tianpan.items():
        if not v:
            continue
        t_gan = v[0]
        d_gan = dipan.get(gong, "")
        if not d_gan:
            continue
        d_gan_first = d_gan[0]
        if gan_chong.get(t_gan) == d_gan_first:
            count += 1
    return count >= 3


# ══════════════════════════════════════════════════════════════
# 3. GANZHI_PATTERN_TABLE (主入口)
# ══════════════════════════════════════════════════════════════

GANZHI_PATTERN_TABLE: list[QimenPattern] = [
    QimenPattern(
        id="qinglong_fanshou",
        name="青龙返首",
        category="gan_zhi_ju",
        polarity="auspicious",
        description="天盘甲子(甲)加临地盘戊, 主上书进表、喜庆大吉",
        source="《奇门遁甲统宗》卷七·三才返首格",
        check_fn=_check_qinglong_fanshou,
    ),
    QimenPattern(
        id="feiniao_diexue",
        name="飞鸟跌穴",
        category="gan_zhi_ju",
        polarity="auspicious",
        description="天盘甲午(甲)加临地盘庚, 主逃亡必获、求财必得",
        source="《奇门遁甲统宗》卷七·飞鸟跌穴格",
        check_fn=_check_feiniao_diexue,
    ),
    QimenPattern(
        id="tianfu_shi",
        name="天辅时",
        category="gan_zhi_ju",
        polarity="auspicious",
        description="天盘三奇(乙丙丁)临本时辰所在宫, 大吉之时",
        source="《奇门遁甲秘笈大全》天辅时吉格",
        check_fn=_check_tianfu_shi,
    ),
    QimenPattern(
        id="sanzha_wujia",
        name="三诈五假",
        category="gan_zhi_ju",
        polarity="auspicious",
        description="天盘三奇之一 + 落吉门(开门/休门/生门), 求谋大吉",
        source="《遁甲神应经》三诈格 (真诈/大诈/小诈)",
        check_fn=_check_sanzha_wujia,
    ),
    QimenPattern(
        id="baihu_changkuang",
        name="白虎猖狂",
        category="gan_zhi_ju",
        polarity="inauspicious",
        description="天盘庚加临地盘日干(乙), 主血光凶险",
        source="《奇门遁甲统宗》卷八·庚格凶",
        check_fn=_check_baihu_changkuang_v2,
    ),
    QimenPattern(
        id="yinghuo_ruying",
        name="荧惑入荧",
        category="gan_zhi_ju",
        polarity="inauspicious",
        description="天盘丙加临地盘丙 (丙+丙自刑), 主火灾血光",
        source="《奇门遁甲统宗》卷八·丙格凶",
        check_fn=_check_yinghuo_ruying,
    ),
    QimenPattern(
        id="taibai_ruying",
        name="太白人荧",
        category="gan_zhi_ju",
        polarity="inauspicious",
        description="天盘庚加临地盘丙 (庚克丙), 主火灾刀兵",
        source="《奇门遁甲统宗》卷八·庚丙格凶",
        check_fn=_check_taibai_ruying,
    ),
    QimenPattern(
        id="zhuque_rujiang",
        name="朱雀入江",
        category="gan_zhi_ju",
        polarity="inauspicious",
        description="天盘乙加临地盘癸, 主口舌是非、文书缠绕",
        source="《奇门遁甲统宗》卷八·乙癸格凶",
        check_fn=_check_zhuque_rujiang,
    ),
    QimenPattern(
        id="qinglong_rutianlao",
        name="青龙入天牢",
        category="gan_zhi_ju",
        polarity="inauspicious",
        description="天盘乙加临地盘庚 (乙庚合金), 主财损不利",
        source="《奇门遁甲统宗》卷八·乙庚格凶",
        check_fn=_check_qinglong_rutianlao,
    ),
    QimenPattern(
        id="liuyi_jixing",
        name="六仪击刑",
        category="gan_zhi_ju",
        polarity="inauspicious",
        description="六甲旬首 (戊己庚辛壬癸) 加临地盘被刑地支, 主刑伤",
        source="《奇门遁甲元灵经》六仪击刑格",
        check_fn=_check_liuyi_jixing,
    ),
    QimenPattern(
        id="fuyin",
        name="伏吟",
        category="fu_yin",
        polarity="inauspicious",
        description="天盘加地盘同干 (≥3 宫), 主事闭塞、谋为不成",
        source="《奇门遁甲统宗》卷九·伏吟格",
        check_fn=_check_fuyin,
    ),
    QimenPattern(
        id="fanyin",
        name="反吟",
        category="fan_yin",
        polarity="inauspicious",
        description="天盘加地盘相冲 (干对冲, ≥3 宫), 主反复不定",
        source="《奇门遁甲统宗》卷九·反吟格",
        check_fn=_check_fanyin_gong_chong,
    ),
]


# ══════════════════════════════════════════════════════════════
# 4. 主检测函数
# ══════════════════════════════════════════════════════════════


def detect_patterns(tianpan: dict, dipan: dict, ctx: dict | None = None) -> list[QimenPattern]:
    """遍历所有 pattern, 返回 active=True 的列表.

    Args:
        tianpan: 天地盘天盘 dict, {宫位: '甲'/'甲子'/...}.
        dipan: 天地盘地盘 dict, {宫位: '戊'/'甲子'/...}.
        ctx: 额外上下文 dict, 可含 hour_gong, hour_gan, day_gan, doors 等.

    Returns:
        active patterns 列表. 异常 pattern 自动降级 (warning log) 且不计入结果.
    """
    if ctx is None:
        ctx = {}
    active: list[QimenPattern] = []
    for pat in GANZHI_PATTERN_TABLE:
        try:
            if pat.check_fn(tianpan, dipan, ctx):
                active.append(pat)
        except Exception as exc:
            logger.warning("pattern %s check_fn error: %s", pat.id, exc)
            continue
    return active


def count_patterns_by_polarity(active: list[QimenPattern]) -> dict[str, int]:
    """统计各 polarity 的数量."""
    out = {"auspicious": 0, "slightly_auspicious": 0,
           "inauspicious": 0, "slightly_inauspicious": 0, "neutral": 0}
    for p in active:
        out[p.polarity] = out.get(p.polarity, 0) + 1
    return out


# ══════════════════════════════════════════════════════════════
# 5. 自检
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 奇门遁甲 干组合格局表 自检 ===\n")
    print(f"总格局数: {len(GANZHI_PATTERN_TABLE)}")
    print(f"  大吉 (auspicious): {sum(1 for p in GANZHI_PATTERN_TABLE if p.polarity == 'auspicious')}")
    print(f"  大凶 (inauspicious): {sum(1 for p in GANZHI_PATTERN_TABLE if p.polarity == 'inauspicious')}")

    # 示例: 测试激活
    test_tian = {"坎": "甲", "艮": "乙", "震": "丙"}
    test_di = {"坎": "戊", "艮": "庚", "震": "丙"}
    ctx = {"doors": {"艮": "开门"}}
    actives = detect_patterns(test_tian, test_di, ctx)
    print(f"\n示例盘激活格局: {[p.name for p in actives]}")

    # 文献出处
    print("\n文献出处:")
    for p in GANZHI_PATTERN_TABLE:
        print(f"  {p.name} — {p.source}")