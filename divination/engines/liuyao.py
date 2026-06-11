"""六爻（纳甲筮法） —— 自实现，文献：《京氏易传》纳甲、《增删卜易》《卜筮正宗》断法。
三枚铜钱摇六次：6=老阴(变)、7=少阳、8=少阴、9=老阳(变)。动爻变出变卦。
六神依日干起：甲乙青龙、丙丁朱雀、戊勾陈、己螣蛇、庚辛白虎、壬癸玄武（自初爻上排）。"""
import random
from ..contracts import Birth, ChartResult
from .. import yijing
from .. import wuxing as wx

_LIUSHEN = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

_YONGSHEN = {  # 问事类别 -> 用神六亲（《增删卜易》取用）
    "财": "妻财", "求财": "妻财", "生意": "妻财", "妻": "妻财",
    "官": "官鬼", "事业": "官鬼", "功名": "官鬼", "官司": "官鬼", "夫": "官鬼", "病灾": "官鬼",
    "父母": "父母", "房产": "父母", "文书": "父母", "学业": "父母", "车": "父母",
    "子女": "子孙", "平安": "子孙", "医药": "子孙", "出行": "子孙",
    "兄弟": "兄弟", "合伙": "兄弟", "竞争": "兄弟", "朋友": "兄弟",
}

_GAN_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3,
              "庚": 4, "辛": 4, "壬": 5, "癸": 5}


def compute(b: Birth, tosses: list[int] | None = None, seed: int | None = None, query: str | None = None) -> ChartResult:
    rng = random.Random(seed)
    if tosses is None:
        # 每爻三钱：字(阴)=2 背(阳)=3，和为6/7/8/9
        tosses = [sum(rng.choice([2, 3]) for _ in range(3)) for _ in range(6)]
    lines = [1 if t in (7, 9) else 0 for t in tosses]        # 本卦阴阳
    moving = [i + 1 for i, t in enumerate(tosses) if t in (6, 9)]
    bian = [(1 - lines[i]) if (i + 1) in moving else lines[i] for i in range(6)]

    ben = yijing.hexagram_name(lines)
    bg = yijing.palace_shiying(ben["name"])
    naijia = yijing.naijia(lines)

    # 日干起六神
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


    # ---- 断法（《增删卜易》）：月建、日辰、旬空、用神旺衰 ----
    judgement = {}
    try:
        from lunar_python import Solar
        ec = Solar.fromYmdHms(b.year, b.month, b.day, b.hour, b.minute, 0).getLunar().getEightChar()
        month_zhi = ec.getMonthZhi(); day_gz = ec.getDay(); day_wx = wx.GAN_WX[day_gz[0]]
        xkong = list(ec.getDayXunKong())   # 日空（两字）
        judgement["月建"] = month_zhi; judgement["日辰"] = day_gz; judgement["旬空"] = xkong
        # 标注每爻旬空/月破/日冲
        for e in naijia:
            z = e["地支"]
            e["旬空"] = z in xkong
            e["月破"] = wx.chong(z, month_zhi)
            e["日冲"] = wx.chong(z, day_gz[1])
        # 用神
        if query and query in _YONGSHEN:
            ys = _YONGSHEN[query]
            cand = [e for e in naijia if e["六亲"] == ys]
            judgement["问事"] = query; judgement["用神六亲"] = ys
            if cand:
                yao = cand[0]
                st = wx.wang_state(yao["五行"], month_zhi, day_wx)
                concl = []
                if yao["旬空"]: concl.append("用神旬空(待出空或冲空之日应)")
                if yao["月破"]: concl.append("用神月破(力弱，多主不成或迟应)")
                动 = yao["爻"] in moving
                concl.append(f"用神{st['level']}（{'、'.join(st['notes']) or '无明显生克'}）")
                concl.append("用神发动" if 动 else "用神安静")
                judgement["用神爻"] = {"爻": yao["爻"], "地支": yao["地支"], "五行": yao["五行"],
                                      "旺衰": st["level"], "score": st["score"]}
                judgement["断语"] = concl
            else:
                judgement["断语"] = [f"卦中不见{ys}（用神不上卦，多需伏神或另断）"]
        else:
            judgement["提示"] = "传入 query（如 '求财'/'事业'/'婚姻'）以自动取用神断吉凶"
    except Exception as _e:
        judgement["error"] = str(_e)

    bian_hex = yijing.hexagram_name(bian)
    return ChartResult(
        method="liuyao", school="east", engine="self(纳甲筮法)",
        normalized={"elements": {}, "timeline": []},
        raw={"摇钱": tosses, "本卦": ben, "变卦": bian_hex if moving else None,
             "动爻": moving, "宫": bg["宫"], "世": bg["世"], "应": bg["应"],
             "六爻装卦": naijia, "日干": gz, "断": judgement},
    )
