"""合盘/合婚（第13法）—— 中西合并：八字合婚 + 西方 Synastry + 紫微合参。
文献：八字合婚（天干五合/地支六合三合六冲相刑、用神互补，《三命通会》合婚论）；
     西方 Synastry（跨盘相位，重点 Sun-Moon / Venus-Mars 轴）。
输出维度评级（高/中/低）而非单一分数——多体系不可通约，避免虚假精确。"""
from .. import wuxing as wx
from ..contracts import Birth, ChartResult

# 天干五合
_WUHE = {frozenset(p): h for p, h in [(("甲","己"),"土"),(("乙","庚"),"金"),
         (("丙","辛"),"水"),(("丁","壬"),"木"),(("戊","癸"),"火")]}
# 地支六合
_LIUHE = {frozenset(p) for p in [("子","丑"),("寅","亥"),("卯","戌"),
                                  ("辰","酉"),("巳","申"),("午","未")]}
# 三合局
_SANHE = {"水": {"申","子","辰"}, "火": {"寅","午","戌"},
          "金": {"巳","酉","丑"}, "木": {"亥","卯","未"}}
_SHENGXIAO = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]


def _gan_rel(g1: str, g2: str) -> dict:
    """日干关系：五合 > 相生 > 比和 > 相克。"""
    if frozenset((g1, g2)) in _WUHE:
        return {"关系": "天干五合", "化": _WUHE[frozenset((g1, g2))], "评": "上",
                "义": "如胶似漆，天然亲和"}
    w1, w2 = wx.GAN_WX[g1], wx.GAN_WX[g2]
    if w1 == w2:
        return {"关系": "比和", "评": "中", "义": "同气相求，亦易争锋"}
    if wx.SHENG[w1] == w2 or wx.SHENG[w2] == w1:
        who = f"{g1}生{g2}" if wx.SHENG[w1] == w2 else f"{g2}生{g1}"
        return {"关系": f"相生({who})", "评": "上", "义": "一方滋养一方，付出与受益宜平衡"}
    who = f"{g1}克{g2}" if wx.KE[w1] == w2 else f"{g2}克{g1}"
    return {"关系": f"相克({who})", "评": "下", "义": "易有制约张力，需经营化解"}


def _zhi_rel(z1: str, z2: str) -> dict:
    rels, ji, xiong = [], 0, 0
    if frozenset((z1, z2)) in _LIUHE:
        rels.append("六合"); ji += 2
    for wxn, grp in _SANHE.items():
        if z1 in grp and z2 in grp and z1 != z2:
            rels.append(f"三合({wxn}局半合)"); ji += 1
    if wx.chong(z1, z2):
        rels.append("六冲"); xiong += 2
    if wx.xing(z1, z2):
        rels.append("相刑"); xiong += 1
    if not rels:
        rels.append("无明显合冲")
    ping = "上" if ji > xiong else ("下" if xiong > ji else "中")
    return {"关系": rels, "评": ping}


def _favorable(pillars: dict) -> list[str]:
    """由旺衰模型导出喜五行（扶抑）。"""
    s = wx.day_master_strength(pillars)
    dm_wx = wx.GAN_WX[pillars["day"][0]]
    yin = next(w for w in wx.SHENG if wx.SHENG[w] == dm_wx)
    if s["score"] <= 2:
        return [yin, dm_wx]                       # 弱喜印比
    if s["score"] >= 4:
        return [wx.SHENG[dm_wx], wx.KE[dm_wx],
                next(w for w in wx.KE if wx.KE[w] == dm_wx)]  # 强喜食伤财官
    return []                                      # 中和


def analyze_bazi_hehun(pa: dict, pb: dict) -> dict:
    """纯函数：两套四柱 -> 合婚分析（可独立golden测试）。"""
    day = {"日干": _gan_rel(pa["day"][0], pb["day"][0]),
           "日支": _zhi_rel(pa["day"][1], pb["day"][1])}
    year = _zhi_rel(pa["year"][1], pb["year"][1])
    sx = (_SHENGXIAO[wx.ZHI.index(pa["year"][1])], _SHENGXIAO[wx.ZHI.index(pb["year"][1])])
    # 鸳鸯合：日柱干支双合
    yuanyang = (day["日干"]["关系"] == "天干五合"
                and "六合" in day["日支"]["关系"])
    # 用神互补：对方旺五行是否补我所喜
    fa, fb = _favorable(pa), _favorable(pb)
    ea = wx.element_strength(pa)["scored"]
    eb = wx.element_strength(pb)["scored"]
    top_a = sorted(ea, key=ea.get, reverse=True)[:2]
    top_b = sorted(eb, key=eb.get, reverse=True)[:2]
    bu_a = [w for w in fa if w in top_b]   # B 补 A
    bu_b = [w for w in fb if w in top_a]   # A 补 B
    hubu = {"A喜": fa or ["中和"], "B喜": fb or ["中和"],
            "B补A": bu_a, "A补B": bu_b,
            "评": "上" if (bu_a and bu_b) else ("中" if (bu_a or bu_b) else "平")}
    return {"日柱": day, "鸳鸯合": yuanyang, "年支(属相)": {"属相": sx, **year},
            "用神互补": hubu}


# ── 西方 Synastry ──
_KEY_PAIRS = [("太阳", "月亮"), ("金星", "火星"), ("太阳", "太阳"),
              ("月亮", "月亮"), ("月亮", "金星"), ("太阳", "土星"), ("月亮", "土星")]
_ASPECTS = {0: ("合相", 8), 60: ("六分相", 4), 90: ("刑相", 6),
            120: ("拱相", 6), 180: ("冲相", 8)}
_HARMONIC = {"合相", "六分相", "拱相"}


def _cross_aspects(pos_a: dict, pos_b: dict) -> list[dict]:
    out = []
    for na, la in pos_a.items():
        for nb, lb in pos_b.items():
            d = abs((la - lb) % 360)
            sep = min(d, 360 - d)
            for ang, (label, orb) in _ASPECTS.items():
                if abs(sep - ang) <= orb:
                    out.append({"A": na, "B": nb, "相位": label,
                                "谐和": label in _HARMONIC,
                                "orb": round(abs(sep - ang), 2)})
                    break
    return out


def compute(b: Birth, partner: Birth = None, **_) -> ChartResult:
    if partner is None:
        raise ValueError("hepan 需要 partner=Birth(...) 第二人出生信息")
    from .bazi import compute as bazi_c
    from .western import compute as west_c
    from .ziwei import compute as ziwei_c

    ba, bb = bazi_c(b), bazi_c(partner)
    hehun = analyze_bazi_hehun(ba.raw["pillars"], bb.raw["pillars"])

    wa, wb = west_c(b), west_c(partner)
    pos_a = {k: v["lon"] for k, v in wa.raw["planets"].items()}
    pos_b = {k: v["lon"] for k, v in wb.raw["planets"].items()}
    cross = _cross_aspects(pos_a, pos_b)
    key = [c for c in cross if (c["A"], c["B"]) in _KEY_PAIRS
           or (c["B"], c["A"]) in _KEY_PAIRS]
    n_h = sum(1 for c in cross if c["谐和"])
    n_t = sum(1 for c in cross if not c["谐和"])

    try:
        za, zb = ziwei_c(b), ziwei_c(partner)
        ziwei = {"A命主/身主": (za.raw["soul"], za.raw["body"]),
                 "B命主/身主": (zb.raw["soul"], zb.raw["body"])}
    except Exception:
        ziwei = {}

    # 维度评级（档位制，多体系印证）
    def grade(*marks):
        s = sum({"上": 2, "中": 1, "平": 1, "下": 0}.get(m, 1) for m in marks)
        avg = s / (2 * len(marks))
        return "高" if avg >= 0.7 else ("低" if avg <= 0.35 else "中")

    sun_moon = any({c["A"], c["B"]} == {"太阳", "月亮"} and c["谐和"] for c in key)
    venus_mars = any({c["A"], c["B"]} == {"金星", "火星"} and c["谐和"] for c in key)
    dims = {
        "性格相处": grade(hehun["日柱"]["日干"]["评"], "上" if sun_moon else "中"),
        "情感吸引": grade(hehun["日柱"]["日支"]["评"], "上" if venus_mars else "中"),
        "长期稳定": grade(hehun["年支(属相)"]["评"],
                       "上" if n_h > n_t else ("下" if n_t > n_h * 2 else "中")),
        "互补成长": grade(hehun["用神互补"]["评"]),
    }
    # 印证/分歧
    east_good = hehun["日柱"]["日干"]["评"] == "上" or hehun["鸳鸯合"]
    west_good = n_h > n_t
    if east_good == west_good:
        agree = "中西印证：" + ("两套体系均偏吉" if east_good else "两套体系均提示需经营")
        diverge = None
    else:
        agree = None
        diverge = (f"中西分歧：八字侧{'偏吉' if east_good else '有张力'}，"
                   f"西方跨盘{'谐和居多' if west_good else '硬相位居多'}——并陈两视角，不强合")

    return ChartResult(
        method="hepan", school="east", engine="self(八字合婚+Synastry)",
        normalized={"elements": {}, "timeline": []},
        raw={"八字合婚": hehun, "西方合盘": {"关键相位": key, "谐和数": n_h, "张力数": n_t},
             "紫微合参": ziwei, "维度评级": dims,
             "印证": agree, "分歧": diverge,
             "说明": "档位制评级（高/中/低），多体系不可通约故不给单一分数"},
    )
