"""梅花易数（时间起卦法 + 数字起卦法） —— 自实现。
文献：《梅花易数》（北宋·邵雍）；《周易本经》《说卦传》。

起卦方式:
  - 时间起卦 (mode="time"):  上卦=(年支数+月+日)%8，下卦=(同上+时支数)%8，动爻=(全和)%6
  - 数字起卦 (mode="number"): 上卦=n1%8，下卦=n2%8，动爻=(n1+n2)%6

先天八卦数：乾1兑2离3震4巽5坎6艮7坤8。

核心断法（5 卦系统）:
  - 本卦: 主事之初
  - 互卦: 主事之中过程（234爻+345爻）
  - 变卦: 主事之结果（动爻变）
  - 错卦: 阴阳互变（每爻 1↔0）— 主事之反对面/否定面
  - 综卦: 上下颠倒（爻序 1→6, 2→5, 3→4）— 主事之另一视角

体用生克：动爻所在卦为用，另一为体；用对体的生克定吉凶。
卦气旺衰：以月令地支论五行旺相休囚死。
万物类象：参《说卦传》《梅花易数》卷三的八卦万物类象。
"""
from .. import wuxing as wx, yijing
from ..contracts import Birth, ChartResult

_XIANTIAN = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}
_DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# ── 八卦万物类象（《说卦传》《梅花易数》卷三）──────────────
# 字段: 自然 / 人物(六亲) / 身体 / 属性 / 情志 / 其他类象
TRIGRAM_ATTRIBUTES = {
    "乾": {
        "自然": "天", "人物": "父 / 君 / 老人", "身体": "头 / 骨",
        "五行": "金", "属性": "健 / 刚 / 圆", "情志": "刚健 / 奋进",
        "类象": ["马", "珠宝", "玉", "金", "寒", "冰", "大赤色", "首都", "政府", "名门"],
        "方位": "西北", "季节": "秋冬之交",
    },
    "兑": {
        "自然": "泽 / 湖", "人物": "少女 / 妾 / 歌妓", "身体": "口 / 舌 / 牙",
        "五行": "金", "属性": "悦 / 缺", "情志": "喜悦 / 言语",
        "类象": ["羊", "酒", "胡琴", "破损", "小金属", "白", "西方", "秋季", "沼泽"],
        "方位": "西", "季节": "秋",
    },
    "离": {
        "自然": "火 / 日 / 闪电", "人物": "中女 / 武将", "身体": "目 / 心 / 血液",
        "五行": "火", "属性": "文明 / 丽 / 光明", "情志": "依附 / 急躁",
        "类象": ["雉 / 龟", "甲胄 / 戈兵", "干燥", "红色", "紫色", "南方", "夏季", "文书", "礼节"],
        "方位": "南", "季节": "夏",
    },
    "震": {
        "自然": "雷", "人物": "长男 / 贵胄", "身体": "足 / 肝",
        "五行": "木", "属性": "动 / 决 / 奋", "情志": "惊恐 / 愤怒",
        "类象": ["龙", "竹 / 芦苇", "车辆", "马嘶", "青色", "绿色", "东方", "春季", "决断"],
        "方位": "东", "季节": "春",
    },
    "巽": {
        "自然": "风 / 木", "人物": "长女 / 寡妇 / 僧道", "身体": "股 / 肱 / 神经",
        "五行": "木", "属性": "入 / 散", "情志": "柔顺 / 反复",
        "类象": ["鸡", "丝帛 / 绳", "长物", "白色", "草木", "东南", "春夏之交", "文书", "命令"],
        "方位": "东南", "季节": "春夏之交",
    },
    "坎": {
        "自然": "水 / 雨 / 月", "人物": "中男 / 渔人", "身体": "耳 / 肾 / 膀胱",
        "五行": "水", "属性": "陷 / 隐 / 暗", "情志": "忧愁 / 险陷",
        "类象": ["猪", "弓 / 轮", "黑", "红色", "正北", "冬季", "聪明 / 智谋", "奸诈"],
        "方位": "北", "季节": "冬",
    },
    "艮": {
        "自然": "山 / 径路", "人物": "少男 / 童子 / 贵族", "身体": "手 / 指 / 背 / 鼻",
        "五行": "土", "属性": "止 / 笃", "情志": "保守 / 安宁",
        "类象": ["狗 / 鼠", "石 / 木", "坚硬物", "黄色", "东北", "冬春之交", "止步", "诚信"],
        "方位": "东北", "季节": "冬春之交",
    },
    "坤": {
        "自然": "地", "人物": "母 / 后 / 众人", "身体": "腹 / 脾 / 胃",
        "五行": "土", "属性": "顺 / 众 / 柔", "情志": "柔顺 / 包容",
        "类象": ["牛", "布 / 帛", "五谷", "黑色", "西南", "夏秋之交", "母性", "吝啬"],
        "方位": "西南", "季节": "夏秋之交",
    },
}

_EVIDENCE_SOURCES = [
    "《梅花易数》北宋·邵雍 卷一·起卦法",
    "《梅花易数》北宋·邵雍 卷二·体用生克断法",
    "《梅花易数》北宋·邵雍 卷三·八卦万物类象",
    "《周易·说卦传》",
    "《皇极经世》北宋·邵雍",
]


def _gua_lines(gua_name: str) -> list[int]:
    return list(yijing._NAME2BITS[gua_name])


def _lines_to_trigrams(lines: list[int]) -> tuple[str, str]:
    """6 爻 → (下卦, 上卦)"""
    lower = yijing.TRIGRAM[tuple(lines[0:3])][0]
    upper = yijing.TRIGRAM[tuple(lines[3:6])][0]
    return lower, upper


def _cuo_gua(lines: list[int]) -> list[int]:
    """错卦：阴阳互变（每爻 1↔0），主事之反对面 / 否定面。
    文献：《梅花易数》卷二 '错综复杂' 之错。"""
    return [1 - x for x in lines]


def _zong_gua(lines: list[int]) -> list[int]:
    """综卦：上下颠倒（爻序 1→6, 2→5, 3→4），主事之另一视角。
    文献：《梅花易数》卷二 '错综复杂' 之综。"""
    return list(reversed(lines))


def _gua_qi_wang_shuai(gua_name: str, month_zhi: str) -> dict:
    """卦气旺衰：以卦宫五行 + 月令地支，参《卜筮正宗》'卦气旺衰'。
    返回: {五行, 月令状态(state), 系数(k), 旺衰(level)}
    """
    gwx = yijing._GONG_WUXING[gua_name]
    mwx = wx.ZHI_WX[month_zhi]
    state, k = wx.wang_xiang(gwx, mwx)
    if k >= 0.8:
        level = "旺相"
    elif k >= 0.5:
        level = "中平"
    else:
        level = "休囚"
    return {"卦": gua_name, "五行": gwx, "月令地支": month_zhi,
            "月令五行": mwx, "状态": state, "系数": k, "旺衰": level}


def _gua_attributes(gua_name: str) -> dict:
    """八卦万物类象（《梅花易数》卷三 / 《说卦传》）"""
    return TRIGRAM_ATTRIBUTES.get(gua_name, {})


def _qigua_time(year: int, month: int, day: int, hour: int, minute: int = 0) -> dict:
    """时间起卦法（《梅花易数》卷一）：
    上卦 = (年支数 + 月 + 日) % 8
    下卦 = (上 + 时支数) % 8
    动爻 = 全和 % 6 (余 0 取末)
    """
    try:
        from lunar_python import Solar
        lunar = Solar.fromYmdHms(year, month, day, hour, minute, 0).getLunar()
        yz = lunar.getYearZhi(); lmonth = abs(lunar.getMonth()); lday = lunar.getDay()
        month_zhi = lunar.getMonthZhi()
    except Exception:
        yz = _DIZHI[(year - 4) % 12]; lmonth = month; lday = day
        # 回退月支：用格里高利月近似
        month_zhi = _DIZHI[(month + 1) % 12]  # 简化为节气月
    yzn = _DIZHI.index(yz) + 1
    hzn = (hour + 1) // 2 % 12 + 1   # 时支序 1..12（子=1）
    s_up = yzn + lmonth + lday
    s_all = s_up + hzn
    up = _XIANTIAN[s_up % 8 or 8]
    low = _XIANTIAN[s_all % 8 or 8]
    moving = s_all % 6 or 6
    return {"up": up, "low": low, "moving": moving,
            "yzn": yzn, "lmonth": lmonth, "lday": lday, "hzn": hzn,
            "month_zhi": month_zhi}


def _qigua_number(n1: int, n2: int, n3: int | None = None) -> dict:
    """数字起卦法（《梅花易数》卷一）：
    上卦 = n1 % 8 (余 0 取 8)
    下卦 = n2 % 8 (余 0 取 8)
    动爻 = (n1 + n2) % 6 或 n3 % 6 (余 0 取 6)
    """
    up_n = n1 % 8 or 8
    low_n = n2 % 8 or 8
    if n3 is not None:
        moving = n3 % 6 or 6
    else:
        moving = (n1 + n2) % 6 or 6
    return {"up": _XIANTIAN[up_n], "low": _XIANTIAN[low_n],
            "moving": moving, "n1": n1, "n2": n2, "n3": n3}


def _five_hexagrams(up: str, low: str, moving: int) -> dict:
    """由上下卦+动爻生成 5 卦系统（本/互/变/错/综）"""
    lines = _gua_lines(low) + _gua_lines(up)        # 下卦在前三爻
    # 本卦
    ben = yijing.hexagram_name(lines)
    # 互卦：234 爻为下互，345 爻为上互
    hu_lines = lines[1:4] + lines[2:5]
    hu = yijing.hexagram_name(hu_lines)
    # 变卦：动爻变
    bian_lines = [(1 - lines[i]) if (i + 1) == moving else lines[i] for i in range(6)]
    bian = yijing.hexagram_name(bian_lines)
    # 错卦：每爻互变
    cuo_lines = _cuo_gua(lines)
    cuo = yijing.hexagram_name(cuo_lines)
    # 综卦：上下颠倒
    zong_lines = _zong_gua(lines)
    zong = yijing.hexagram_name(zong_lines)
    return {
        "本卦": ben, "互卦": hu, "变卦": bian,
        "错卦": cuo, "综卦": zong,
        "本爻线": lines, "互爻线": hu_lines,
        "变爻线": bian_lines, "错爻线": cuo_lines, "综爻线": zong_lines,
        "动爻": moving,
    }


def _ti_yong_judgement(ben_lower: str, ben_upper: str, moving: int,
                       ti: str, yong: str, hu_name: str, bian_name: str,
                       hu_wx_lower: str, hu_wx_upper: str) -> dict:
    """体用生克断（《梅花易数》卷二 + 《增删卜易》变通）"""
    ti_wx = yijing._GONG_WUXING[ti]
    yong_wx = yijing._GONG_WUXING[yong]
    rel = wx.relation(yong_wx, ti_wx)   # 用对体
    JIXIONG = {
        "生出(泄)": ("吉", "用卦生体卦，得外力相助，事多顺遂"),
        "比和": ("吉", "体用比和，谋望称意，事易成"),
        "克出": ("凶", "用卦克体卦，受制受阻，谋事多逆"),
        "生入(被生)": ("平偏耗", "体卦生用卦，耗泄气力，先劳后得或破费"),
        "克入(被克)": ("吉可控", "体卦克用卦，体能制事，吉但费力"),
    }
    ji, shuo = JIXIONG[rel]
    return {
        "体卦": f"{ti}({ti_wx})", "用卦": f"{yong}({yong_wx})",
        "体用关系": rel, "总断": ji, "断语": shuo,
        "互卦提示": f"互卦主事中过程（{hu_name}，{hu_wx_lower}/{hu_wx_upper}）",
        "变卦提示": f"变卦主结果（{bian_name}）—看变卦对体卦生克定终局",
    }


def _comprehensive_narrative(result: dict) -> str:
    """综合解读：把本/互/变/错/综 + 体用 + 卦气串成完整故事线。
    文献：《梅花易数》卷三 '万物类象' 与卷二 '体用生克' 综合应用。
    """
    ben = result["五卦系统"]["本卦"]["name"]
    hu = result["五卦系统"]["互卦"]["name"]
    bian = result["五卦系统"]["变卦"]["name"]
    cuo = result["五卦系统"]["错卦"]["name"]
    zong = result["五卦系统"]["综卦"]["name"]

    ti = result["断法"]["体卦"]
    yong = result["断法"]["用卦"]
    relation = result["断法"]["体用关系"]
    jixiong = result["断法"]["总断"]

    qi_lines = []
    for k in ("本卦", "互卦", "变卦", "错卦", "综卦"):
        info = result["卦气旺衰"][k]
        qi_lines.append(f"{k}({info['卦']}){info['状态']}")

    return (
        f"【梅花易数综合解读】\n"
        f"起卦: {result['起卦方式']}, 上卦{result['上下卦']['上卦']}/下卦{result['上下卦']['下卦']}/动爻第{result['五卦系统']['动爻']}爻。\n"
        f"五卦链路: 本『{ben}』→ 互『{hu}』(事中)→ 变『{bian}』(结局), "
        f"错『{cuo}』(否定面)/综『{zong}』(镜像)。\n"
        f"体用: {ti} 为体、{yong} 为用, 关系={relation}, 总断={jixiong}。\n"
        f"卦气: {' / '.join(qi_lines)}。\n"
        f"提示: 变卦对体卦生克定终局, 互卦主过程, 错综两卦为反向校验。"
    )


def compute(b: Birth, mode: str = "time", n1: int = 0, n2: int = 0, n3: int | None = None) -> ChartResult:
    """梅花易数起卦入口。

    Args:
        b: Birth 输入
        mode: "time" (时间起卦) 或 "number" (数字起卦)
        n1, n2: 数字起卦的两个数字
        n3: 数字起卦的动爻数字（可选, 默认 n1+n2）
    """
    if mode == "time":
        qigua = _qigua_time(b.year, b.month, b.day, b.hour, b.minute)
        method_desc = f"时间起卦(年支{qigua['yzn']}+月{qigua['lmonth']}+日{qigua['lday']}+时支{qigua['hzn']})"
    elif mode == "number":
        qigua = _qigua_number(n1, n2, n3)
        method_desc = f"数字起卦(n1={n1}/n2={n2}/n3={n3})"
    else:
        raise ValueError(f"meihua mode 不支持: {mode!r}（仅 time/number）")

    up, low, moving = qigua["up"], qigua["low"], qigua["moving"]
    month_zhi = qigua.get("month_zhi", "")

    five = _five_hexagrams(up, low, moving)

    # 体用：动爻在下卦(1-3)则下卦为用，否则上卦为用
    yong, ti = (low, up) if moving <= 3 else (up, low)

    # 体用生克
    judgement = _ti_yong_judgement(
        ben_lower=five["本卦"]["lower"], ben_upper=five["本卦"]["upper"],
        moving=moving, ti=ti, yong=yong,
        hu_name=five["互卦"]["name"], bian_name=five["变卦"]["name"],
        hu_wx_lower=yijing._GONG_WUXING[five["互卦"]["lower"]],
        hu_wx_upper=yijing._GONG_WUXING[five["互卦"]["upper"]],
    )

    # 卦气旺衰（5 卦）
    if not month_zhi:
        month_zhi = "寅"  # fallback 占位
    wangshuai = {
        "本卦": _gua_qi_wang_shuai(five["本卦"]["upper"], month_zhi),
        "互卦": _gua_qi_wang_shuai(five["互卦"]["upper"], month_zhi),
        "变卦": _gua_qi_wang_shuai(five["变卦"]["upper"], month_zhi),
        "错卦": _gua_qi_wang_shuai(five["错卦"]["upper"], month_zhi),
        "综卦": _gua_qi_wang_shuai(five["综卦"]["upper"], month_zhi),
    }

    # 万物类象（本卦上下 + 动爻所在）
    wanywu = {
        "本卦上卦": _gua_attributes(five["本卦"]["upper"]),
        "本卦下卦": _gua_attributes(five["本卦"]["lower"]),
        "互卦上卦": _gua_attributes(five["互卦"]["upper"]),
        "互卦下卦": _gua_attributes(five["互卦"]["lower"]),
        "变卦上卦": _gua_attributes(five["变卦"]["upper"]),
        "变卦下卦": _gua_attributes(five["变卦"]["lower"]),
        "错卦上卦": _gua_attributes(five["错卦"]["upper"]),
        "综卦上卦": _gua_attributes(five["综卦"]["upper"]),
    }

    # 综合解读
    raw = {
        "起卦方式": method_desc,
        "上下卦": {"上卦": up, "下卦": low},
        "五卦系统": {
            "本卦": five["本卦"], "互卦": five["互卦"], "变卦": five["变卦"],
            "错卦": five["错卦"], "综卦": five["综卦"], "动爻": moving,
        },
        "断法": judgement,
        "卦气旺衰": wangshuai,
        "万物类象": wanywu,
        "evidence_sources": _EVIDENCE_SOURCES,
    }
    # 兼容层: 旧契约 top-level 主卦/互卦/变卦/错卦/综卦 + 断
    # (不破坏新结构, 仅作为别名, 旧测试/前端可继续访问)
    raw["主卦"] = five["本卦"]
    raw["互卦"] = five["互卦"]
    raw["变卦"] = five["变卦"]
    raw["错卦"] = five["错卦"]
    raw["综卦"] = five["综卦"]
    raw["断"] = judgement
    raw["综合解读"] = _comprehensive_narrative(raw)

    return ChartResult(
        method="meihua", school="east", engine="self(梅花易数)",
        normalized={"elements": {}, "timeline": []},
        raw=raw,
    )