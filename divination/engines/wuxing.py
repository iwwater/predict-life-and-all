"""五行生克 / 干支属性 / 刑冲合 / 墓库 / 旺衰 —— 各法断法层共用。
文献：五行生克制化、十二地支刑冲、五行墓库（辰戌丑未四库）。"""

SHENG = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}   # 我生
KE = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}       # 我克

GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
ZHI_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
          "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行墓库：木墓未 火土墓戌 金墓丑 水墓辰（干入墓宫）
MU = {"木": "未", "火": "戌", "土": "戌", "金": "丑", "水": "辰"}
GAN_MU = {g: MU[wx] for g, wx in GAN_WX.items()}


def relation(a: str, b: str) -> str:
    """a 对 b 的五行关系（a 视角）。"""
    if a == b:
        return "比和"
    if SHENG[a] == b:
        return "生出(泄)"
    if KE[a] == b:
        return "克出"
    if SHENG[b] == a:
        return "生入(被生)"
    return "克入(被克)"


def chong(z1: str, z2: str) -> bool:
    """地支六冲：子午 丑未 寅申 卯酉 辰戌 巳亥（相差6位）。"""
    return abs(ZHI.index(z1) - ZHI.index(z2)) == 6


# 地支三刑 + 自刑
_XING = [{"寅", "巳", "申"}, {"丑", "戌", "未"}, {"子", "卯"}]
_ZIXING = {"辰", "午", "酉", "亥"}


def xing(z1: str, z2: str) -> bool:
    if z1 == z2:
        return z1 in _ZIXING
    for grp in _XING:
        if z1 in grp and z2 in grp:
            return True
    return False


def in_mu(gan: str, palace_zhi: str) -> bool:
    """天干是否入墓于该地支宫。"""
    return GAN_MU.get(gan) == palace_zhi


def wang_state(target_wx: str, month_zhi: str, day_wx: str) -> dict:
    """用神/体卦旺衰：看月建、日辰对其五行的生克。"""
    m = ZHI_WX[month_zhi]
    score = 0
    notes = []
    rm = relation(m, target_wx)
    if rm == "生入(被生)": score += 2; notes.append("月建生扶")
    elif rm == "比和": score += 2; notes.append("月建临旺")
    elif rm == "克入(被克)": score -= 2; notes.append("月建克制(月破险)")
    elif rm == "生出(泄)": score -= 1; notes.append("月建泄气")
    rd = relation(day_wx, target_wx)
    if rd == "生入(被生)": score += 1; notes.append("日辰生扶")
    elif rd == "比和": score += 1; notes.append("日辰帮扶")
    elif rd == "克入(被克)": score -= 1; notes.append("日辰克制")
    elif rd == "生出(泄)": score -= 1; notes.append("日辰泄气")
    level = "旺相" if score >= 2 else ("休囚" if score <= -2 else "中平")
    return {"score": score, "level": level, "notes": notes}


# ===== 地支藏干（权重：本气1.0 / 中气0.6 / 余气0.3，通行计权，流派或异）=====
CANGGAN = {
    "子": [("癸", 1.0)],
    "丑": [("己", 1.0), ("癸", 0.6), ("辛", 0.3)],
    "寅": [("甲", 1.0), ("丙", 0.6), ("戊", 0.3)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 1.0), ("乙", 0.6), ("癸", 0.3)],
    "巳": [("丙", 1.0), ("庚", 0.6), ("戊", 0.3)],
    "午": [("丁", 1.0), ("己", 0.6)],
    "未": [("己", 1.0), ("丁", 0.6), ("乙", 0.3)],
    "申": [("庚", 1.0), ("壬", 0.6), ("戊", 0.3)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 1.0), ("辛", 0.6), ("丁", 0.3)],
    "亥": [("壬", 1.0), ("甲", 0.6)],
}

# 月令五行旺相休囚死（当令者旺、令生者相、生令者休、克令者囚、令克者死）
def wang_xiang(target_wx: str, month_wx: str) -> tuple[str, float]:
    if target_wx == month_wx:
        return "旺", 1.0
    if SHENG[month_wx] == target_wx:
        return "相", 0.8
    if SHENG[target_wx] == month_wx:
        return "休", 0.5
    if KE[target_wx] == month_wx:
        return "囚", 0.4
    return "死", 0.3   # 月令克之


def element_strength(pillars: dict[str, str]) -> dict:
    """四柱五行力量：天干各1.0 + 地支藏干按权重，再乘月令旺相系数。
    pillars: {'year':'庚午',...}。返回 {五行: 加权分} + 明细。"""
    month_wx = ZHI_WX[pillars["month"][1]]
    raw = {w: 0.0 for w in "木火土金水"}
    detail = []
    for pos, gz in pillars.items():
        g, z = gz[0], gz[1]
        raw[GAN_WX[g]] += 1.0
        detail.append((pos, g, GAN_WX[g], 1.0, "天干"))
        for cg, wt in CANGGAN[z]:
            raw[GAN_WX[cg]] += wt
            detail.append((pos, cg, GAN_WX[cg], wt, f"{z}藏"))
    scored = {}
    states = {}
    for w, v in raw.items():
        st, k = wang_xiang(w, month_wx)
        scored[w] = round(v * k, 2)
        states[w] = st
    return {"raw": {k: round(v, 2) for k, v in raw.items()},
            "scored": scored, "month_wx": month_wx, "states": states, "detail": detail}


def day_master_strength(pillars: dict[str, str]) -> dict:
    """日主旺衰多因子：得令(月令旺相) + 得地(通根:日主在四支藏干有根,按权重与柱位) + 
    得势(同党[比劫+印]总分 vs 异党[财官食伤])。输出五级。"""
    dm = pillars["day"][0]
    dm_wx = GAN_WX[dm]
    month_wx = ZHI_WX[pillars["month"][1]]
    # 1) 得令
    st, _k = wang_xiang(dm_wx, month_wx)
    de_ling = st in ("旺", "相")
    # 2) 得地（通根）：四支藏干中与日主同五行者；月支根加倍，本气根重于余气
    pos_w = {"year": 0.8, "month": 2.0, "day": 1.2, "hour": 0.8}
    root = 0.0
    roots = []
    for pos, gz in pillars.items():
        for cg, wt in CANGGAN[gz[1]]:
            if GAN_WX[cg] == dm_wx:
                root += wt * pos_w[pos]
                roots.append(f"{pos}支{gz[1]}藏{cg}({wt}×{pos_w[pos]})")
    de_di = root >= 1.0
    # 3) 得势：同党 = 比劫(同我) + 印(生我)；异党 = 其余
    es = element_strength(pillars)["scored"]
    yin_wx = next(w for w in SHENG if SHENG[w] == dm_wx)   # 生我者
    tong = es[dm_wx] + es[yin_wx]
    yi = sum(v for k, v in es.items() if k not in (dm_wx, yin_wx))
    de_shi = tong > yi
    score = (2 if de_ling else 0) + (2 if de_di else 0) + (1 if de_shi else 0)
    level = ["从弱(极弱)", "身弱", "偏弱", "中和", "偏强", "身强"][min(score, 5)]
    # 4) 扶抑取用（粗）：弱则用印比，强则用财官食伤
    if score <= 2:
        yong = f"扶抑：身弱宜生扶，喜{yin_wx}(印)、{dm_wx}(比劫)"
    elif score >= 4:
        xie = SHENG[dm_wx]
        cai = KE[dm_wx]
        guan = next(w for w in KE if KE[w] == dm_wx)
        yong = f"扶抑：身强宜克泄耗，喜{xie}(食伤)、{cai}(财)、{guan}(官杀)"
    else:
        yong = "中和：随大运流年取舍，需调候细参"
    return {"日主": f"{dm}({dm_wx})", "得令": de_ling, "月令状态": st,
            "得地": de_di, "通根分": round(root, 2), "通根明细": roots,
            "得势": de_shi, "同党分": round(tong, 2), "异党分": round(yi, 2),
            "强弱": level, "score": score, "取用建议": yong,
            "说明": "多因子粗模型（藏干计权+通根+党势），调候与格局例外未含，断语层细参"}
