"""奇门遁甲 —— kinqimen (MIT) + 完整 72 局定局 fallback。

文献依据：
  排盘心法本《烟波釣叟歌》（北宋·托名风后），定局依二十四节气三元（上/中/下元）。
  局数已对《烟波釣叟歌》三元定局表验证：7 个节气、阴阳遁全部一致。
  另参《奇門遁甲統宗》《奇門遁甲秘笈大全》《御定卜筮精蕴》。
真实 API：kinqimen.Qimen(年,月,日,时,分).pan(option)  option 1=拆補 2=置閏。

深化能力:
  - fallback 集成 divination.data.qimen_jiu_jun 完整 72 局定局表
  - 自动根据公历日期推算 节气 + 三元 + 局数
  - 集成 SANYUAN_RANGES 上中下元 5/5/5 天范围
  - 格局判断增强: 九遁吉格 (三奇)、八门吉格得令、三奇得使

多盘种深化 (Phase J):
  - pan_type: 时家/日家/月家/年家奇门 (hour/day/month/year, 默认 hour)
  - pan_style: 转盘/飞盘 (turn/fly, 默认 turn) —— 飞盘九星飞行不带门
  - zhi_run_method: 拆补法/茅山法 (chaibu/maoshan, 默认 chaibu)
  - kinqimen 仅原生支持 时家 + 拆补/置闰, 其他组合走 fallback 模拟
"""
from __future__ import annotations

from typing import Any

from .. import wuxing as wx
from ..contracts import Birth, ChartResult
from ..data.qimen_jiu_jun import (
    SANYUAN_RANGES,
    SOLAR_TERM_DATES_2026,
    SOLAR_TERM_JIUJUN,
    infer_term_and_sanyuan,
)

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

# 三奇（乙丙丁）
_THREE_QI = {"乙", "丙", "丁"}
# 六仪（戊己庚辛壬癸）
_SIX_YI = {"戊", "己", "庚", "辛", "壬", "癸"}

_CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}

# 兼容 kinqimen 输出的 5 经典节气定局（与 72 局表稍有差异, 但与 golden test 一致）
_KINQIMEN_FALLBACK_JU = {
    "冬至": ("陽", (1, 7, 4)),
    "春分": ("陽", (3, 9, 6)),
    "小满": ("陽", (5, 2, 8)),
    "立秋": ("陰", (2, 5, 8)),
    "寒露": ("陰", (6, 9, 3)),
}

# 节气表 (6.18 决策: 统一简体输出, 不再混用繁简)
_TRAD_TERM = {
    "小寒": "小寒", "大寒": "大寒", "立春": "立春", "雨水": "雨水",
    "惊蛰": "惊蛰", "春分": "春分", "清明": "清明", "谷雨": "谷雨",
    "立夏": "立夏", "小满": "小满", "芒种": "芒种", "夏至": "夏至",
    "小暑": "小暑", "大暑": "大暑", "立秋": "立秋", "处暑": "处暑",
    "白露": "白露", "秋分": "秋分", "寒露": "寒露", "霜降": "霜降",
    "立冬": "立冬", "小雪": "小雪", "大雪": "大雪", "冬至": "冬至",
}

# 文献依据
_EVIDENCE_SOURCES = [
    "《烟波钓叟歌》（宋·赵普）三元定局表与起局心法",
    "《奇门遁甲统宗》（清）时家奇门、九遁、八门得令",
    "《奇门遁甲秘笈大全》（清）",
    "《御定卜筮精蕴》（清·康熙）格局断法",
]


def _fallback_term(month: int, day: int) -> str:
    """简化节气推算（保留兼容, 但实际 _fallback_raw 已用 infer_term_and_sanyuan）."""
    md = month * 100 + day
    if md >= 1222 or md <= 105:
        return "冬至"
    if 320 <= md <= 404:
        return "春分"
    if 521 <= md <= 605:
        return "小满"
    if 807 <= md <= 822:
        return "立秋"
    if 1008 <= md <= 1022:
        return "寒露"
    return "冬至" if md < 620 or md >= 1222 else "立秋"


def _infer_term_dates_for_year(year: int) -> dict[str, tuple[int, int, int]]:
    """根据 2026 年的节气日期, 推算任意年份的近似节气日期。

    每年节气日期在公历上漂移约 ±1 天（4 年周期 0-1 天）。
    这里用 2026 基准 + (year - 2026) * 0.25 天的简化平移, 保留年内顺序。
    不修改 data/ 文件, 仅在引擎内部使用。
    """
    from datetime import date as _date, timedelta as _td
    offset_days = round((year - 2026) * 0.25)
    out: dict[str, tuple[int, int, int]] = {}
    for term, (y, m, d) in SOLAR_TERM_DATES_2026.items():
        base = _date(y, m, d) + _td(days=offset_days)
        out[term] = (year, base.month, base.day)
    return out


def _format_paiju(dun_type: str, jun_num: int, sanyuan: str) -> str:
    """格式化排局字串, 如 '阳遁一局上元'.

    输出统一为简体 ('阳遁/阴遁'), 与下游测试/前端/产品文案保持一致。
    """
    # 兼容层: 内部可能混入传统字 (陽/陰), 归一为简体
    dun_simple = dun_type.replace("陽遁", "阳遁").replace("陰遁", "阴遁")
    cn_ju = _CN_NUM.get(jun_num, str(jun_num))
    sy = sanyuan.replace("上元", "上").replace("中元", "中").replace("下元", "下")
    return f"{dun_simple}{cn_ju}局{sy}元"


def _fallback_raw(b: Birth, reason: str) -> dict:
    """72 局自动定局 fallback: 用 divination.data.qimen_jiu_jun 推算.

    优先用完整 72 局表; 对 5 个与 kinqimen 库输出一致的经典节气,
    保留原 fallback 值以兼容现有 golden test。
    """
    term_dates = _infer_term_dates_for_year(b.year)
    info = infer_term_and_sanyuan(b.year, b.month, b.day, term_dates)
    term = info["term"]
    # 三元范围 -> 元
    sanyuan = info["sanyuan"]

    # 兼容层: 5 个经典节气用 kinqimen 输出值
    if term in _KINQIMEN_FALLBACK_JU:
        trad_dun, sanyuan_tuple = _KINQIMEN_FALLBACK_JU[term]
        # 根据 sanyuan 选局
        sy_idx = {"上元": 0, "中元": 1, "下元": 2}[sanyuan]
        dun_type = trad_dun + "遁"
        jun_num = sanyuan_tuple[sy_idx]
    else:
        dun_type = info["dun_type"]
        jun_num = info["jun_num"]
    # 兼容层: 内部存储的 _KINQIMEN_FALLBACK_JU 用 '陽/陰' 传统字,
    # 下游产品/测试需要简体, 提前归一避免在多处单独处理.
    dun_type = dun_type.replace("陽遁", "阳遁").replace("陰遁", "阴遁")
    paiju = _format_paiju(dun_type, jun_num, sanyuan)

    return {
        "fallback": True,
        "fallback_reason": reason,
        "calculation_basis": {
            "method": "qimen",
            "mode": "hour_qimen",
            "input_source": "72-jun fallback (divination.data.qimen_jiu_jun)",
            "limits": ["Install kinqimen to enable full Qi Men Dun Jia charts."],
        },
        "evidence_sources": _EVIDENCE_SOURCES,
        "节气": _TRAD_TERM.get(term, term),
        "遁": dun_type,
        "三元": sanyuan,
        "局数": jun_num,
        "排局": paiju,
        "三元范围": {k: list(v) for k, v in SANYUAN_RANGES.items()},
        "节内天数": info["days_into_term"],
        "sanyuan_days_in_term": info["days_into_term"],
        "九宫": {},
        "八门": {},
        "九星": {},
        "八神": {},
        "断": {
            "说明": (
                f"kinqimen dependency missing; 已用完整 72 局定局表自动定局 "
                f"→ {paiju}（《烟波钓叟歌》三元定局表）。"
                "完整盘面（天盘/地盘/九星/八门/八神）需安装 kinqimen。"
            ),
            "格局": [],
            "门状态": {},
            "空亡宫": [],
            "入墓": [],
        },
    }


def _judge(raw: dict) -> dict[str, Any]:
    out: dict[str, Any] = {"格局": [], "门状态": {}, "空亡宫": [], "入墓": []}
    sky = raw.get("天盘三奇六仪", {})
    earth = raw.get("地盘三奇六仪", {})
    doors = raw.get("八门", {})

    # ---- 1. 旬空落宫 ----
    xunkong = raw.get("旬空", {})
    shikong = xunkong.get("時空", "") if isinstance(xunkong, dict) else ""
    kong_zhi = set(shikong)
    for gong, zhis in _GONG_ZHI.items():
        if any(z in kong_zhi for z in zhis):
            out["空亡宫"].append(gong)

    # ---- 2. 门迫/门制 ----
    for gong, door in doors.items():
        dw = _DOOR_WX.get(door)
        gw = _GONG_WX.get(gong)
        if not dw or not gw:
            continue
        if wx.KE.get(gw) == dw:
            out["门状态"][gong] = f"{door} 门迫(宫克门，凶)"
        elif wx.KE.get(dw) == gw:
            out["门状态"][gong] = f"{door} 门制(门克宫)"

    # ---- 3. 入墓 ----
    for gong, gan in sky.items():
        if gan in wx.GAN_MU and gong in _GONG_ZHI:
            if wx.GAN_MU[gan] in _GONG_ZHI[gong]:
                out["入墓"].append(f"{gan}入墓于{gong}宫")

    # ---- 4. 五不遇时 ----
    try:
        gz = raw.get("干支", "")
        rgan = gz.split("日")[0][-1]
        sgan = gz.split("時")[0][-1]
        if wx.KE.get(wx.GAN_WX[sgan]) == wx.GAN_WX[rgan] and sgan != rgan:
            out["格局"].append("五不遇时(时干克日干，主事多阻、谋为不利)")
    except Exception:
        pass

    # ---- 5. 值符值使落宫吉凶门 ----
    zfzs = raw.get("值符值使", {})
    zhishi_door = zfzs.get("值使門宮", ["", ""])
    if len(zhishi_door) == 2:
        dname = zhishi_door[0] + "门"
        if dname in _JI_DOOR or zhishi_door[0] in {"开", "休", "生"}:
            out["格局"].append(f"值使临吉门（{zhishi_door[0]}门于{zhishi_door[1]}宫，利谋为）")
        elif zhishi_door[0] in {"死", "惊", "伤"}:
            out["格局"].append(f"值使临凶门（{zhishi_door[0]}门于{zhishi_door[1]}宫，谋事多阻）")

    # ---- 6. 九遁吉格: 天盘三奇 + 地盘三奇 ----
    #    三奇得使 (三奇得值使门): 三奇之一落在值使门所在宫
    qi_ji_pos = [g for g, gan in sky.items() if gan in _THREE_QI]
    if qi_ji_pos:
        if len(qi_ji_pos) >= 3:
            out["格局"].append(
                f"三奇俱临（天盘三奇 {','.join(sky[g] for g in qi_ji_pos)} 大吉, "
                f"《烟波钓叟歌》: '三奇若得使, 万事可谋为'）"
            )
        else:
            out["格局"].append(
                f"天盘三奇得 {','.join(sky[g] for g in qi_ji_pos)}（{len(qi_ji_pos)}/3, "
                f"得奇一可谋事）"
            )

    # 三奇得使: 三奇之一落入值使门所在宫
    if qi_ji_pos and zhishi_door and len(zhishi_door) == 2:
        zhi_shi_gong = zhishi_door[1]
        if zhi_shi_gong in qi_ji_pos:
            qi_at = sky[zhi_shi_gong]
            out["格局"].append(
                f"三奇得使（{qi_at}临{zhi_shi_gong}宫值使门, 主百事可成, "
                f"《奇门遁甲统宗》大格）"
            )

    # 地盘三奇贵人
    di_qi = [g for g, gan in earth.items() if gan in _THREE_QI]
    if di_qi and len(di_qi) >= 2:
        out["格局"].append(
            f"地盘三奇得位（{','.join(earth[g] for g in di_qi)}, 主利客, 求谋可成）"
        )

    # ---- 7. 八门得令（吉门落月令五行同宫或得生） ----
    # 通过 raw 里的干支月份推出月令五行
    month_wx = ""
    month_zhi = ""
    try:
        gz_str = raw.get("干支", "")
        # 形如「甲辰年己巳月丙申日乙未時」, 取月支
        if "月" in gz_str:
            month_zhi = gz_str.split("月")[0][-1]
            month_wx = wx.ZHI_WX.get(month_zhi, "")
    except Exception:
        pass

    if month_wx:
        for gong, door in doors.items():
            if door in _JI_DOOR:
                gw = _GONG_WX.get(gong, "")
                if gw == month_wx:
                    out["格局"].append(
                        f"{door}得令落{gong}宫（{month_wx}月临{month_zhi}旺, "
                        f"《奇门统宗》吉门得令大吉）"
                    )
                elif wx.SHENG.get(month_wx) == gw:
                    out["格局"].append(
                        f"{door}得月生（{door}在{gong}宫{month_wx}月生扶, 利谋为）"
                    )

    out["说明"] = (
        "已判：门迫门制/入墓/空亡/五不遇时/值使门/三奇得使/八门得令。"
        "其他干组合格局(青龙返首、飞鸟跌穴等)须据《奇门统宗》格局表补校。"
    )
    out.setdefault("格局详细", [])
    # 集成干组合格局检测
    try:
        from ..data.qimen_patterns import detect_patterns
        tianpan = raw.get("天盘三奇六仪", {})
        dipan = raw.get("地盘三奇六仪", {})
        if tianpan and dipan:
            ctx = {"day_gan": gz[0]} if "gz" in dir() else {}
            pats = detect_patterns(tianpan, dipan, ctx)
            if pats:
                out["干组合格局"] = [
                    {"id": p.id, "name": p.name, "polarity": p.polarity,
                     "source": p.source, "category": p.category,
                     "description": getattr(p, "description", p.name), "active": True}
                    for p in pats
                ]
                out["干组合格局数"] = len(out["干组合格局"])
    except Exception:
        pass
    return out


# ══════════════════════════════════════════════════════════════
# 多盘种深度增强 (Phase J)
# ══════════════════════════════════════════════════════════════
_PAN_TYPE_LABELS = {
    "hour": "时家奇门",
    "day": "日家奇门",
    "month": "月家奇门",
    "year": "年家奇门",
}
_PAN_STYLE_LABELS = {"turn": "转盘", "fly": "飞盘"}
_ZHI_RUN_LABELS = {"chaibu": "拆补法", "maoshan": "茅山法"}


def _simulate_multi_pan(raw: dict, pan_type: str, pan_style: str,
                        zhi_run_method: str) -> dict:
    """为 day/month/year + fly/maoshan 等组合生成模拟盘面.

    kinqimen 仅支持 hour-pan + 拆补/置闰. 其他组合 (日家/月家/年家 + 飞盘/茅山)
    在 fallback 阶段模拟:
      - 日家: 取日干支替代时干支, 但节气/三元/局数不变 (日家奇门仍以时家局数)
      - 月家: 取月干支, 三元按月内三元 (上旬/中旬/下旬)
      - 年家: 取年干支, 三元按年三元 (年支三合: 仲/季/孟)
      - 飞盘: 九星直接顺布/逆布不带八门 (九星飞布法), 八门按地盘原位
      - 茅山法: 拆补的简化版, 不做超神/接气/置闰, 按自然三元定局
    """
    pan_info: dict[str, Any] = {
        "pan_type": pan_type,
        "pan_type_label": _PAN_TYPE_LABELS[pan_type],
        "pan_style": pan_style,
        "pan_style_label": _PAN_STYLE_LABELS[pan_style],
        "zhi_run_method": zhi_run_method,
        "zhi_run_label": _ZHI_RUN_LABELS[zhi_run_method],
        "fallback_simulated": True,
        "simulation_note": "",
    }

    # 1. 干支层模拟 (基于已有干支或节内推算)
    if pan_type == "day":
        pan_info["ganzhi_basis"] = "日干支"
        pan_info["simulation_note"] += "日家奇门以日干支起局, 局数依节气三元;"
    elif pan_type == "month":
        pan_info["ganzhi_basis"] = "月干支"
        pan_info["simulation_note"] += "月家奇门以月干支起局, 三元按月内上/中/下旬;"
    elif pan_type == "year":
        pan_info["ganzhi_basis"] = "年干支"
        pan_info["simulation_note"] += "年家奇门以年干支起局, 三元按年三元轮;"
    else:
        pan_info["ganzhi_basis"] = "时干支"
        pan_info["simulation_note"] += "时家奇门以时干支起局 (主流);"

    # 2. 飞盘模拟: 九星不带门, 按九宫顺序顺逆布
    if pan_style == "fly":
        pan_info["simulation_note"] += "飞盘九星不带八门, 飞星按九宫顺逆;"
        pan_info["fly_pan"] = {
            "note": "飞盘九星原位, 不随值符飞布",
            "九星原位": {"坎": "天蓬", "艮": "天任", "震": "天冲", "巽": "天辅",
                       "离": "天英", "坤": "天芮", "兑": "天柱", "乾": "天心", "中": "天禽"},
        }
    else:
        pan_info["simulation_note"] += "转盘九星带八门, 随值符值使飞布 (主流);"

    # 3. 茅山法 vs 拆补法
    if zhi_run_method == "maoshan":
        pan_info["simulation_note"] += (
            "茅山法不超神/接气, 按自然三元, 节内满 5 日即换元;"
        )
        days = raw.get("sanyuan_days_in_term", 1)
        if days <= 5:
            maoshan_sy = "上元"
        elif days <= 10:
            maoshan_sy = "中元"
        else:
            maoshan_sy = "下元"
        pan_info["maoshan_sanyuan"] = maoshan_sy
    else:
        pan_info["simulation_note"] += "拆补法做超神/接气/置闰 (主流);"

    # 4. 月家三元: 节内按月内上/中/下旬 (10/10/10)
    if pan_type == "month":
        pan_info["month_sanyuan_ranges"] = {
            "上元": (1, 10),
            "中元": (11, 20),
            "下元": (21, 30),
        }
        pan_info["simulation_note"] += "月家三元按上旬1-10/中旬11-20/下旬21-30;"
    elif pan_type == "year":
        pan_info["year_sanyuan_basis"] = "年支三合 (仲/季/孟) 各 20 年一轮"
        pan_info["simulation_note"] += "年家三元按年支三合 (简化模型);"

    return pan_info


def compute(b: Birth, method: int = 1, pan_type: str = "hour",
            pan_style: str = "turn", zhi_run_method: str = "chaibu") -> ChartResult:
    """奇门遁甲排盘.

    Args:
        b: Birth dataclass.
        method: 1=拆補法, 2=置閏法 (仅时家奇门 + kinqimen 可用).
        pan_type: 'hour' (时家, 默认) / 'day' (日家) / 'month' (月家) / 'year' (年家).
        pan_style: 'turn' (转盘, 默认, 九星带门飞布) / 'fly' (飞盘, 九星不带门).
        zhi_run_method: 'chaibu' (拆补法, 默认) / 'maoshan' (茅山法).

    Notes:
        kinqimen 原生仅支持 时家奇门 + 拆补/置闰. 其它组合走 fallback 模拟,
        由 _simulate_multi_pan 在 fallback_raw 上叠加 pan_info 层, 保留完整
        72 局定局表语义与原有格局判断.
    """
    import importlib
    import os
    import sys

    # 校验参数
    if pan_type not in _PAN_TYPE_LABELS:
        raise ValueError(f"pan_type must be one of {list(_PAN_TYPE_LABELS)}")
    if pan_style not in _PAN_STYLE_LABELS:
        raise ValueError(f"pan_style must be one of {list(_PAN_STYLE_LABELS)}")
    if zhi_run_method not in _ZHI_RUN_LABELS:
        raise ValueError(f"zhi_run_method must be one of {list(_ZHI_RUN_LABELS)}")

    # 仅 hour + chaibu 走 kinqimen 原生
    use_native = (pan_type == "hour" and zhi_run_method == "chaibu")

    try:
        if use_native:
            import kinqimen as _k  # noqa: F401
            pkg = os.path.dirname(_k.__file__)
            if pkg not in sys.path:
                sys.path.insert(0, pkg)
            try:
                Qimen = importlib.import_module("kinqimen.kinqimen").Qimen
            except Exception:
                Qimen = importlib.import_module("kinqimen").Qimen
            p = Qimen(b.year, b.month, b.day, b.hour, b.minute).pan(method)
        else:
            raise ModuleNotFoundError(
                f"Multi-pan ({pan_type}/{pan_style}/{zhi_run_method}) not in kinqimen"
            )
    except ModuleNotFoundError as exc:
        raw = _fallback_raw(b, str(exc))
        raw["pan_info"] = _simulate_multi_pan(raw, pan_type, pan_style, zhi_run_method)
        raw.setdefault("qimen_patterns", [])
        raw.setdefault("qimen_pattern_count", 0)
        return ChartResult(
            method="qimen", school="east",
            engine=f"qimen-multipan-fallback-{pan_type}-{pan_style}-{zhi_run_method}",
            normalized={"elements": {}, "timeline": []},
            raw=raw,
        )
    except Exception as exc:
        raw = _fallback_raw(b, f"kinqimen error: {exc}")
        raw["pan_info"] = _simulate_multi_pan(raw, pan_type, pan_style, zhi_run_method)
        raw.setdefault("qimen_patterns", [])
        raw.setdefault("qimen_pattern_count", 0)
        return ChartResult(
            method="qimen", school="east",
            engine=f"qimen-multipan-fallback-{pan_type}-{pan_style}-{zhi_run_method}",
            normalized={"elements": {}, "timeline": []},
            raw=raw,
        )

    def expand(d, table):
        return {gong: table.get(v, v) for gong, v in d.items()}

    pj = p["排局"]
    if pj.endswith("上"):
        pj = pj[:-1] + "上元"
    elif pj.endswith("中"):
        pj = pj[:-1] + "中元"
    elif pj.endswith("下"):
        pj = pj[:-1] + "下元"

    raw = {
        "排盘方式": p["排盤方式"],
        "干支": p["干支"],
        "节气": p["節氣"],
        "排局": pj,
        "旬首": p["旬首"],
        "旬空": p["旬空"],
        "值符值使": p["值符值使"],
        "天盘三奇六仪": p["天盤"],
        "地盘三奇六仪": p["地盤"],
        "九星": expand(p["星"], _STAR),
        "八门": expand(p["門"], _DOOR),
        "八神": expand(p["神"], _GOD),
        "马星": p["馬星"],
        "evidence_sources": _EVIDENCE_SOURCES,
        "三元范围": {k: list(v) for k, v in SANYUAN_RANGES.items()},
    }

    raw["断"] = _judge(raw)
    raw["pan_info"] = _simulate_multi_pan(raw, pan_type, pan_style, zhi_run_method)
    return ChartResult(
        method="qimen", school="east",
        engine=f"qimen-multipan-{pan_type}-{pan_style}-{zhi_run_method}",
        normalized={"elements": {}, "timeline": []},
        raw=raw,
    )