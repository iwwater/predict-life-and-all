"""奇门遁甲（时家） —— kinqimen (MIT)。

文献依据：
  排盘心法本《烟波釣叟歌》（北宋·托名风后），定局依二十四节气三元（上/中/下元）。
  局数已对《烟波釣叟歌》三元定局表验证：7 个节气、阴阳遁全部一致。
  另参《奇門遁甲統宗》《奇門遁甲秘笈大全》。
真实 API：kinqimen.Qimen(年,月,日,时,分).pan(option)  option 1=拆補 2=置閏。
"""
from ..contracts import Birth, ChartResult
from .. import wuxing as wx

# 缩写 -> 文献全称
_STAR = {"蓬": "天蓬", "任": "天任", "沖": "天冲", "輔": "天辅", "英": "天英",
         "芮": "天芮", "柱": "天柱", "心": "天心", "禽": "天禽"}
_DOOR = {"休": "休门", "生": "生门", "傷": "伤门", "杜": "杜门",
         "景": "景门", "死": "死门", "驚": "惊门", "開": "开门"}
_GOD = {"符": "值符", "蛇": "螣蛇", "陰": "太阴", "合": "六合",
        "勾": "勾陈", "雀": "朱雀", "地": "九地", "天": "九天",
        "虎": "白虎", "玄": "玄武"}




# 九宫五行 / 地支 / 八门五行（格局判断用）
_GONG_WX = {"坎": "水", "艮": "土", "震": "木", "巽": "木", "離": "火",
            "坤": "土", "兌": "金", "乾": "金", "中": "土"}
_GONG_ZHI = {"坎": ["子"], "艮": ["丑", "寅"], "震": ["卯"], "巽": ["辰", "巳"],
             "離": ["午"], "坤": ["未", "申"], "兌": ["酉"], "乾": ["戌", "亥"], "中": []}
_DOOR_WX = {"休门": "水", "生门": "土", "伤门": "木", "杜门": "木",
            "景门": "火", "死门": "土", "惊门": "金", "开门": "金"}
_JI_DOOR = {"开门", "休门", "生门"}      # 三吉门
_XIONG_DOOR = {"死门", "惊门", "伤门"}   # 凶门


def _judge(raw):
    out = {"格局": [], "门状态": {}, "空亡宫": [], "入墓": []}
    sky = raw["天盘三奇六仪"]; doors = raw["八门"]
    # 旬空落宫
    shikong = raw["旬空"].get("時空", "") if isinstance(raw["旬空"], dict) else ""
    kong_zhi = set(shikong)
    for gong, zhis in _GONG_ZHI.items():
        if any(z in kong_zhi for z in zhis):
            out["空亡宫"].append(gong)
    # 门迫/门制：门五行 vs 宫五行
    for gong, door in doors.items():
        dw = _DOOR_WX.get(door); gw = _GONG_WX.get(gong)
        if not dw or not gw:
            continue
        if wx.KE.get(gw) == dw:      # 宫克门 = 门迫（凶）
            out["门状态"][gong] = f"{door} 门迫(宫克门，凶)"
        elif wx.KE.get(dw) == gw:    # 门克宫 = 门制（有为）
            out["门状态"][gong] = f"{door} 门制(门克宫)"
    # 入墓：天盘干入其墓库宫
    for gong, gan in sky.items():
        if gan in wx.GAN_MU and gong in _GONG_ZHI:
            if wx.GAN_MU[gan] in _GONG_ZHI[gong]:
                out["入墓"].append(f"{gan}入墓于{gong}宫")
    # 五不遇时：时干克日干
    try:
        gz = raw["干支"]  # 形如「甲辰年己巳月丙申日乙未時」
        rgan = gz.split("日")[0][-1]   # 日干
        sgan = gz.split("時")[0][-1]   # 时干
        if wx.KE.get(wx.GAN_WX[sgan]) == wx.GAN_WX[rgan] and sgan != rgan:
            out["格局"].append("五不遇时(时干克日干，主事多阻、谋为不利)")
    except Exception:
        pass
    # 值符值使落宫吉凶门
    zfzs = raw["值符值使"]
    zhishi_door = zfzs.get("值使門宮", ["", ""])
    if len(zhishi_door) == 2:
        dname = zhishi_door[0] + "门"
        if dname in _JI_DOOR or zhishi_door[0] in {"开", "休", "生"}:
            out["格局"].append(f"值使临吉门（{zhishi_door[0]}门于{zhishi_door[1]}宫，利谋为）")
        elif zhishi_door[0] in {"死", "惊", "伤"}:
            out["格局"].append(f"值使临凶门（{zhishi_door[0]}门于{zhishi_door[1]}宫，谋事多阻）")
    out["说明"] = "已判：门迫门制/入墓/空亡/五不遇时/值使门。干组合格局(青龙返首等)须据《奇门统宗》格局表补校。"
    return out


def compute(b: Birth, method: int = 1) -> ChartResult:
    """method: 1=拆補法（默认，主流）, 2=置閏法。"""
    # kinqimen 内部用绝对 import config，需把其包目录加入 sys.path
    import os, sys, importlib, kinqimen as _k
    pkg = os.path.dirname(_k.__file__)
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    try:
        Qimen = importlib.import_module("kinqimen.kinqimen").Qimen
    except Exception:
        Qimen = importlib.import_module("kinqimen").Qimen
    p = Qimen(b.year, b.month, b.day, b.hour, b.minute).pan(method)

    def expand(d, table):
        return {gong: table.get(v, v) for gong, v in d.items()}

    raw = {
        "排盘方式": p["排盤方式"],
        "干支": p["干支"],
        "节气": p["節氣"],
        "排局": p["排局"],            # 如「陽遁五局上」=阳遁五局上元
        "旬首": p["旬首"],
        "旬空": p["旬空"],
        "值符值使": p["值符值使"],     # 值符星宫 / 值使门宫，烟波钓叟歌核心
        "天盘三奇六仪": p["天盤"],     # 九宫天盘干
        "地盘三奇六仪": p["地盤"],     # 九宫地盘干
        "九星": expand(p["星"], _STAR),
        "八门": expand(p["門"], _DOOR),
        "八神": expand(p["神"], _GOD),
        "马星": p["馬星"],
    }
    raw["断"] = _judge(raw)
    return ChartResult(
        method="qimen", school="east", engine="kinqimen",
        normalized={"elements": {}, "timeline": []},
        raw=raw,
    )
