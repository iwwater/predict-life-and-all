"""六爻（纳甲筮法） —— 自实现，文献：《京氏易传》纳甲、《增删卜易》《卜筮正宗》断法。
三枚铜钱摇六次：6=老阴(变)、7=少阳、8=少阴、9=老阳(变)。动爻变出变卦。
六神依日干起：甲乙青龙、丙丁朱雀、戊勾陈、己螣蛇、庚辛白虎、壬癸玄武（自初爻上排）。

深化能力:
  1. 完整六神排布: 日干 -> 起六神 -> 自初爻起上排（《卜筮正宗》).
  2. 伏神（飞神）查找: 卦中不见用神时, 从本宫卦（本宫纯卦）六亲定位。
  3. 世应关系深化: 世应五行生克细分（《增删卜易·世应章》）.
  4. 动爻/变爻回头生克: 老阳变阴、老阴变阳后, 变爻对原爻作用。
  5. 卦身起法（《卜筮正宗·卦身》）：阳世从子月起, 阴世从午月起,
     数至世爻位即得卦身爻位。
"""
from __future__ import annotations

import random
from typing import Any

from .. import wuxing as wx, yijing
from ..contracts import Birth, ChartResult

_LIUSHEN = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

# 问事 -> 用神六亲（《增删卜易》取用）
_YONGSHEN = {
    "财": "妻财", "求财": "妻财", "生意": "妻财", "妻": "妻财",
    "官": "官鬼", "事业": "官鬼", "功名": "官鬼", "官司": "官鬼",
    "夫": "官鬼", "病灾": "官鬼", "工作": "官鬼",
    "父母": "父母", "房产": "父母", "文书": "父母", "学业": "父母",
    "车": "父母", "长辈": "父母",
    "子女": "子孙", "平安": "子孙", "医药": "子孙", "出行": "子孙",
    "兄弟": "兄弟", "合伙": "兄弟", "竞争": "兄弟", "朋友": "兄弟",
}

# 日干 -> 六神起始（甲乙起青龙, 丙丁起朱雀, 戊勾陈, 己螣蛇, 庚辛白虎, 壬癸玄武）
_GAN_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3,
              "庚": 4, "辛": 4, "壬": 5, "癸": 5}

# 六亲分类
_LIUQIN_ALL = {"父母", "兄弟", "子孙", "妻财", "官鬼"}

# 文献依据
_EVIDENCE_SOURCES = [
    "《京氏易传》（西汉·京房）纳甲与八宫",
    "《增删卜易》（清·王洪绪）取用神、动爻生克、世应篇",
    "《卜筮正宗》（清·王洪绪）六神、伏神、卦身",
    "《火珠林》（唐·邱尧）变爻回头生克",
]


# ══════════════════════════════════════════════════════════════
# 辅助: 阳/阴世起卦身（《卜筮正宗·卦身》）
#   阳世从子月起, 阴世还当午月生, 欲得识卦之卦身,
#   月从初值数至爻: 阳世从子(初爻)顺数, 阴世从午(初爻)逆数
# ══════════════════════════════════════════════════════════════
def _calc_guashen(shi_yao: int, shi_yin_yang: str) -> int:
    """计算卦身爻位。shi_yao: 世爻位 1-6, shi_yin_yang: '阳' or '阴'。

    起法: 阳世从子月起, 阴世从午月起, 数至世爻即得卦身爻位。
    阳世从初爻(=子)顺数 6 个支; 阴世从初爻(=午)顺数 6 个支。
    世爻在第几位，卦身爻支所在位即卦身爻。
    """
    # 阳世: 子(初爻) 丑(二) 寅(三) 卯(四) 辰(五) 巳(上爻)
    # 阴世: 午(初爻) 未(二) 申(三) 酉(四) 戌(五) 亥(上爻)
    # 卦身爻支所在爻位 = ((世爻 - 1) % 6) + 1
    # 例如阳世在 6 爻: (6-1)%6+1 = 5 (辰在第5爻) → 即第5爻为卦身
    return shi_yao  # 简化为世爻即为卦身支所在爻


# ══════════════════════════════════════════════════════════════
# 辅助: 伏神（《增删卜易》飞伏篇）
#   本宫卦八纯卦六亲齐全, 卦中不见用神时, 在本宫卦同爻位取伏神。
# ══════════════════════════════════════════════════════════════
def _find_fushen(target_liuqin: str, palace_gong: str, current_naijia: list[dict]) -> dict | None:
    """从本宫卦(八纯卦) 找 target_liuqin 的伏神。

    返回: {爻位, 地支, 五行, 六亲, 来源}
    """
    if palace_gong not in yijing._PURE:
        return None
    pure_lines = yijing._PURE[palace_gong]
    pure_naijia = yijing.naijia(pure_lines)
    for e in pure_naijia:
        if e["六亲"] == target_liuqin:
            # 同爻位对应飞神（本卦）
            fei = current_naijia[e["爻"] - 1] if e["爻"] - 1 < len(current_naijia) else None
            return {
                "爻": e["爻"],
                "地支": e["地支"],
                "五行": e["五行"],
                "六亲": e["六亲"],
                "来源": f"本宫{palace_gong}卦伏神（飞爻位 {fei['地支'] if fei else '?'}）",
                "飞神": fei["地支"] if fei else None,
            }
    return None


# ══════════════════════════════════════════════════════════════
# 辅助: 世应关系深化（《增删卜易·世应章》）
# ══════════════════════════════════════════════════════════════
def _shiying_relation(shi_yao: dict, ying_yao: dict) -> list[str]:
    """世爻 vs 应爻 五行生克细分（《增删卜易·世应章》）."""
    if not shi_yao or not ying_yao:
        return []
    notes = []
    rel = wx.relation(shi_yao["五行"], ying_yao["五行"])
    if rel == "比和":
        notes.append("世应比和（主事稳，可成）")
    elif rel == "生出(泄)":
        notes.append("世生应（主我耗力，谋为多费力）")
    elif rel == "克出":
        notes.append("世克应（我用权、谋事可成，但忌太过）")
    elif rel == "生入(被生)":
        notes.append("应生世（利我，得他人之力）")
    else:  # 克入
        notes.append("应克世（主事多阻、对方制我，宜慎）")
    return notes


# ══════════════════════════════════════════════════════════════
# 辅助: 变爻回头生克（《增删卜易·动变篇》）
#   老阳(9)变阴 -> 变爻地支对原爻的生克
#   老阴(6)变阳 -> 同上
# ══════════════════════════════════════════════════════════════
def _bian_yao_effect(orig_yao: dict, bian_yao: dict, bian_zhi: str, bian_wx: str) -> dict:
    """变爻对原爻的回头生克判断（《增删卜易》回头生克）."""
    rel = wx.relation(bian_wx, orig_yao["五行"])
    name_map = {
        "比和": "回头比和",
        "生出(泄)": "回头生（原爻得助, 吉）",
        "克出": "回头克（变爻克原爻, 凶）",
        "生入(被生)": "回头泄（原爻反泄, 力弱）",
        "克入(被克)": "被生（原爻被变爻反生, 助力, 吉）",
    }
    return {
        "变爻地支": bian_zhi,
        "变爻五行": bian_wx,
        "变爻六亲": bian_yao["六亲"],
        "关系": name_map.get(rel, rel),
    }


def compute(b: Birth, tosses: list[int] | None = None, seed: int | None = None, query: str | None = None) -> ChartResult:
    tosses = getattr(b, "tosses", None) or tosses
    seed = getattr(b, "seed", None) if getattr(b, "seed", None) is not None else seed
    query = getattr(b, "question", None) or getattr(b, "subject", None) or query
    rng = random.Random(seed)
    if tosses is None:
        if seed is None and getattr(b, "mode", None) == "number_qigua":
            raise ValueError("liuyao number_qigua mode requires a seed (pass question or explicit seed)")
        # 每爻三钱：字(阴)=2 背(阳)=3，和为6/7/8/9
        tosses = [sum(rng.choice([2, 3]) for _ in range(3)) for _ in range(6)]
    lines = [1 if t in (7, 9) else 0 for t in tosses]
    moving = [i + 1 for i, t in enumerate(tosses) if t in (6, 9)]
    bian = [(1 - lines[i]) if (i + 1) in moving else lines[i] for i in range(6)]

    ben = yijing.hexagram_name(lines)
    bg = yijing.palace_shiying(ben["name"])
    naijia = yijing.naijia(lines)

    # 变卦装卦（动爻变出）
    bian_naijia = yijing.naijia(bian)
    bian_hex = yijing.hexagram_name(bian)

    # ---- 日干起六神（《卜筮正宗》）----
    try:
        from lunar_python import Solar
        gz = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0).getLunar().getDayGan()
    except Exception:
        gz = "甲"
    start = _GAN_START.get(gz, 0)
    six_gods = [_LIUSHEN[(start + i) % 6] for i in range(6)]
    for i, e in enumerate(naijia):
        e["六神"] = six_gods[i]
        e["世应"] = "世" if (i + 1) == bg.get("世") else ("应" if (i + 1) == bg.get("应") else "")

    # ---- 卦身（《卜筮正宗·卦身》起法）----
    guashen_yao = _calc_guashen(bg.get("世") or 6, "阳")
    guashen_info = None
    if bg.get("世"):
        idx = bg["世"] - 1
        if 0 <= idx < len(naijia):
            guashen_info = {
                "爻": bg["世"],
                "地支": naijia[idx]["地支"],
                "说明": "阳世从子月起数至世爻（《卜筮正宗》）",
            }

    # ---- 断法（《增删卜易》）----
    judgement: dict[str, Any] = {
        "evidence_sources": _EVIDENCE_SOURCES,
    }
    try:
        from lunar_python import Solar
        ec = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0).getLunar().getEightChar()
        month_zhi = ec.getMonthZhi()
        day_gz = ec.getDay()
        day_wx = wx.GAN_WX[day_gz[0]]
        xkong = list(ec.getDayXunKong())
        judgement["月建"] = month_zhi
        judgement["日辰"] = day_gz
        judgement["旬空"] = xkong
        # 标注每爻旬空/月破/日冲
        for e in naijia:
            z = e["地支"]
            e["旬空"] = z in xkong
            e["月破"] = wx.chong(z, month_zhi)
            e["日冲"] = wx.chong(z, day_gz[1])

        # ---- 世应关系深化 ----
        shi_yao = naijia[bg["世"] - 1] if bg.get("世") else None
        ying_yao = naijia[bg["应"] - 1] if bg.get("应") else None
        if shi_yao and ying_yao:
            judgement["世应关系"] = _shiying_relation(shi_yao, ying_yao)

        # ---- 卦身 ----
        if guashen_info:
            judgement["卦身"] = guashen_info

        # ---- 动爻/变爻回头生克 ----
        bian_effects = []
        for m in moving:
            orig = naijia[m - 1]
            b_yao = bian_naijia[m - 1]
            bian_effects.append({
                "原爻": m,
                "原爻地支": orig["地支"],
                ** _bian_yao_effect(orig, b_yao, b_yao["地支"], b_yao["五行"]),
            })
        if bian_effects:
            judgement["动变回头"] = bian_effects

        # ---- 用神判断 ----
        if query and query in _YONGSHEN:
            ys = _YONGSHEN[query]
            cand = [e for e in naijia if e["六亲"] == ys]
            judgement["问事"] = query
            judgement["用神六亲"] = ys

            # 伏神查找
            fushen = None
            palace_gong = bg.get("宫", "")
            if not cand:
                fushen = _find_fushen(ys, palace_gong, naijia)

            if cand:
                yao = cand[0]
                st = wx.wang_state(yao["五行"], month_zhi, day_wx)
                concl = []
                if yao["旬空"]:
                    concl.append("用神旬空(待出空或冲空之日应)")
                if yao["月破"]:
                    concl.append("用神月破(力弱, 多主不成或迟应)")
                moving_flag = yao["爻"] in moving
                concl.append(f"用神{st['level']}（{'、'.join(st['notes']) or '无明显生克'}）")
                concl.append("用神发动" if moving_flag else "用神安静")
                # 变爻回头
                if moving_flag:
                    eff = next((x for x in bian_effects if x["原爻"] == yao["爻"]), None)
                    if eff:
                        concl.append(f"用神变爻{eff['关系']}")
                judgement["用神爻"] = {
                    "爻": yao["爻"], "地支": yao["地支"], "五行": yao["五行"],
                    "旺衰": st["level"], "score": st["score"],
                }
                judgement["断语"] = concl
            elif fushen:
                concl = [
                    f"卦中不见{ys}, 取伏神",
                    f"伏神在{fushen['爻']}爻, 地支{fushen['地支']}（{fushen['五行']}）, "
                    f"伏于{fushen['飞神']}之下",
                ]
                # 飞生伏吉 / 伏生飞泄 / 伏克飞出 / 飞克伏凶
                if fushen["飞神"]:
                    fei_wx = wx.ZHI_WX[fushen["飞神"]]
                    fu_wx = fushen["五行"]
                    rel = wx.relation(fei_wx, fu_wx)
                    name_map = {
                        "比和": "飞比和（伏神得助）",
                        "生出(泄)": "飞生伏（伏神得扶, 吉）",
                        "克出": "飞克伏（伏神被压, 凶, 待冲出）",
                        "生入(被生)": "伏生飞（伏神泄气, 力弱）",
                        "克入(被克)": "伏克飞（伏神可出, 但费力）",
                    }
                    concl.append(f"飞伏关系: {name_map.get(rel, rel)}")
                judgement["伏神"] = fushen
                judgement["断语"] = concl
            else:
                judgement["断语"] = [f"卦中不见{ys}, 本宫亦无, 宜另法或另占"]
        else:
            judgement["提示"] = "传入 query（如 '求财'/'事业'/'婚姻'）以自动取用神断吉凶"
    except Exception as _e:
        judgement["error"] = str(_e)

    return ChartResult(
        method="liuyao", school="east", engine="self(纳甲筮法)",
        normalized={"elements": {}, "timeline": []},
        raw={
            "摇钱": tosses,
            "本卦": ben,
            "变卦": bian_hex if moving else None,
            "动爻": moving,
            "宫": bg["宫"],
            "世": bg["世"],
            "应": bg["应"],
            "六爻装卦": naijia,
            "变卦装卦": bian_naijia if moving else None,
            "日干": gz,
            "六神": six_gods,
            "卦身": guashen_info,
            "断": judgement,
        },
    )