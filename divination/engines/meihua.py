"""梅花易数（时间起卦法） —— 自实现，文献：《梅花易数》（北宋·邵雍）。
上卦=(年支数+月+日)%8，下卦=(年支数+月+日+时支数)%8，动爻=(同上和)%6（余0取末）。
先天八卦数：乾1兑2离3震4巽5坎6艮7坤8。体用：动爻所在为用卦，另一为体卦。"""
from ..contracts import Birth, ChartResult
from .. import yijing
from .. import wuxing as wx

_XIANTIAN = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}
_DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _gua_lines(gua_name: str) -> list[int]:
    return list(yijing._NAME2BITS[gua_name])


def compute(b: Birth) -> ChartResult:
    try:
        from lunar_python import Solar
        lunar = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0).getLunar()
        yz = lunar.getYearZhi(); lmonth = abs(lunar.getMonth()); lday = lunar.getDay()
    except Exception:
        yz = _DIZHI[(b.year - 4) % 12]; lmonth = b.month; lday = b.day
    yzn = _DIZHI.index(yz) + 1
    hzn = (b.hour + 1) // 2 % 12 + 1               # 时支序 1..12（子=1）
    s_up = yzn + lmonth + lday
    s_all = s_up + hzn
    up = _XIANTIAN[s_up % 8 or 8]
    low = _XIANTIAN[s_all % 8 or 8]
    moving = s_all % 6 or 6

    lines = _gua_lines(low) + _gua_lines(up)        # 下卦在前三爻
    ben = yijing.hexagram_name(lines)
    # 互卦：234爻为下互，345爻为上互
    hu_lines = lines[1:4] + lines[2:5]
    hu = yijing.hexagram_name(hu_lines)
    # 变卦：动爻变
    bian_lines = [(1 - lines[i]) if (i + 1) == moving else lines[i] for i in range(6)]
    bian = yijing.hexagram_name(bian_lines)
    # 体用：动爻在下卦(1-3)则下卦为用，否则上卦为用
    yong, ti = (low, up) if moving <= 3 else (up, low)


    # ---- 体用生克断（《梅花易数》断卦总诀）----
    ti_wx = yijing.TRIGRAM[tuple(_gua_lines(ti))][1]
    yong_wx = yijing.TRIGRAM[tuple(_gua_lines(yong))][1]
    hu_low_wx = yijing.TRIGRAM[tuple(hu_lines[0:3])][1]
    hu_up_wx = yijing.TRIGRAM[tuple(hu_lines[3:6])][1]
    rel = wx.relation(yong_wx, ti_wx)   # 用对体
    # rel = relation(用,体)：生出=用生体, 克出=用克体, 生入=体生用, 克入=体克用
    JIXIONG = {
        "生出(泄)": ("吉", "用卦生体卦，得外力相助，事多顺遂"),
        "比和": ("吉", "体用比和，谋望称意，事易成"),
        "克出": ("凶", "用卦克体卦，受制受阻，谋事多逆"),
        "生入(被生)": ("平偏耗", "体卦生用卦，耗泄气力，先劳后得或破费"),
        "克入(被克)": ("吉可控", "体卦克用卦，体能制事，吉但费力"),
    }
    ji, shuo = JIXIONG[rel]
    judgement = {
        "体卦五行": f"{ti}({ti_wx})", "用卦五行": f"{yong}({yong_wx})",
        "体用关系": rel, "总断": ji, "断语": shuo,
        "互卦提示": f"互卦主事中过程（{hu['name']}，{hu_low_wx}/{hu_up_wx}）",
        "变卦提示": f"变卦主结果（{bian['name']}）—看变卦对体卦生克定终局",
    }

    return ChartResult(
        method="meihua", school="east", engine="self(梅花易数)",
        normalized={"elements": {}, "timeline": []},
        raw={"主卦": ben, "互卦": hu, "变卦": bian, "动爻": moving,
             "体卦": ti, "用卦": yong, "上卦": up, "下卦": low, "断": judgement},
    )
