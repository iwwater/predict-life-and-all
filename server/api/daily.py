"""GET/POST /api/daily - daily personalised summary.

输入:
    GET  /api/daily?date=YYYY-MM-DD        无生日,只给今日摘要 + 今日塔罗
    POST /api/daily  body={birth?, date?}  有生日时附加用户日主与五行互动

输出:
    {
      date: "2026-06-06",
      today: {
        ganzhi_day, ganzhi_year, shengxiao, day_wuxing,
        lunar_date, jie_qi, tarot_card, question_seed,
      },
      user?: { day_master, day_wuxing },
      interaction?: { relation, label, focus, action, watch, subject_hint },
      calculation_basis: { method, rule_version, input_source, limits, ... }
    }

设计原则:
    - 不调用 LLM,纯模板 + 干支 + 随机数(同种子稳定)
    - 只用日柱 + 用户日主,不做年运/大运/长期预测
    - 文案温和,避免恐吓/绝对判断
"""
import logging
import random
from datetime import date as date_cls
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from lunar_python import Solar
from pydantic import BaseModel, Field

from divination import Birth
from lunar_python import Solar as LunarSolar


# Lenormand 36 cards — names + core meanings for daily draw
LENORMAND_DAILY = [
    ("Rider", "骑士", "消息、来者、运动、新事物"),
    ("Clover", "三叶草", "幸运、小确幸、机会、乐观"),
    ("Ship", "船", "旅程、远行、探索、过渡"),
    ("House", "房子", "家、稳定、安全、根基"),
    ("Tree", "树", "健康、生长、扎根、因果"),
    ("Clouds", "云", "困惑、不明、阴霾、不确定"),
    ("Snake", "蛇", "欺骗、复杂、聪明、绕路"),
    ("Coffin", "棺材", "结束、终结、放下、转型"),
    ("Bouquet", "花束", "礼物、赞美、邀请、愉悦"),
    ("Scythe", "镰刀", "切割、决断、危险、收获"),
    ("Whip", "鞭子", "冲突、重复、争论、纪律"),
    ("Birds", "鸟", "交谈、焦虑、沟通、流言"),
    ("Child", "小孩", "开始、天真、新阶段、小"),
    ("Fox", "狐狸", "狡猾、警惕、自保、谋略"),
    ("Bear", "熊", "力量、权威、保护、母亲"),
    ("Stars", "星星", "希望、指引、清晰、目标"),
    ("Stork", "鹳", "转变、搬迁、升级、新生"),
    ("Dog", "狗", "忠诚、朋友、信任、陪伴"),
    ("Tower", "高塔", "孤独、权威、界限、机构"),
    ("Garden", "花园", "社交、公开、名声、圈子"),
    ("Mountain", "山", "障碍、延迟、卡住、挑战"),
    ("Crossroads", "十字路口", "选择、岔路、多线、自由"),
    ("Mice", "老鼠", "侵蚀、损耗、偷窃、焦虑"),
    ("Heart", "心", "爱、感情、仁慈、核心"),
    ("Ring", "戒指", "承诺、契约、循环、约定"),
    ("Book", "书", "秘密、知识、学习、隐藏"),
    ("Letter", "信", "消息、文件、沟通、契约"),
    ("Man", "男人", "男性/阳性、重要男性、主动力"),
    ("Woman", "女人", "女性/阴性、重要女性、感受力"),
    ("Lily", "百合", "和平、美德、成熟、性/感性"),
    ("Sun", "太阳", "成功、活力、胜利、正能量"),
    ("Moon", "月亮", "直觉、潜意识、名声、情绪"),
    ("Key", "钥匙", "解决、答案、关键、确定性"),
    ("Fish", "鱼", "财富、流动、生意、丰盛"),
    ("Anchor", "锚", "稳定、坚持、安全、持久"),
    ("Cross", "十字架", "考验、命运、信仰、负担"),
]

router = APIRouter()
log = logging.getLogger("daily")

STEM_WX = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# X 生 Y
GENERATES = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}
# X 克 Y
OVERCOMES = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}

RELATION_TEMPLATES = {
    "比和": {
        "label": "比和·平稳",
        "focus": "回顾与稳态",
        "action": "宜把过去几天的小事串起来看,节奏放慢一点。",
        "watch": "别因为平稳就放下警觉,小细节仍要留心。",
    },
    "印": {
        "label": "今日助你",
        "focus": "长线思考、学习、复盘",
        "action": "适合做中长期规划、整理资料,和信任的人深谈。",
        "watch": "资源是脚手架,不是终点,别把它当成答案。",
    },
    "食伤": {
        "label": "今日外放",
        "focus": "表达、创作、输出",
        "action": "宜把想说的话写下来,把拖延的项目往前推一步。",
        "watch": "表达欲强,说完之前留几秒想一下是否需要。",
    },
    "官杀": {
        "label": "今日有压",
        "focus": "守规矩、按流程办",
        "action": "宜把待办按优先级排,先做完再谈优化。",
        "watch": "外部压力影响情绪,先睡好觉再应对。",
    },
    "财": {
        "label": "今日可推进",
        "focus": "推进、谈判、做决定",
        "action": "宜把犹豫的事往前推一步,把握今天的主动权。",
        "watch": "推进不等于冒进,先看清水再下脚。",
    },
}

QUESTION_POOL = [
    "今天你心里最想回应的那个念头是什么?",
    "今天你愿意为自己做的一件小事是?",
    "今天最让你'好奇'的一句话或场景是什么?",
    "今天你想把哪个'搁置'的想法再翻出来看一眼?",
    "今天你有没有注意到一个反复出现的小信号?",
    "今天你身边哪个人让你'想停下来'?",
]

SUBJECT_BY_RELATION = {
    "比和": "self_life",
    "印": "decision",
    "食伤": "career",
    "官杀": "relationship",
    "财": "career",
}


def _relation(today_wx: str, user_wx: str) -> str:
    if not today_wx or not user_wx:
        return "比和"
    if today_wx == user_wx:
        return "比和"
    if GENERATES.get(today_wx) == user_wx:
        return "印"
    if GENERATES.get(user_wx) == today_wx:
        return "食伤"
    if OVERCOMES.get(today_wx) == user_wx:
        return "官杀"
    if OVERCOMES.get(user_wx) == today_wx:
        return "财"
    return "比和"


def _user_day_master(birth: Birth) -> tuple[str, str]:
    solar = LunarSolar.fromYmdHms(birth.year, birth.month, birth.day, birth.hour, birth.minute, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    day_gan = ec.getDayGan()
    return day_gan, STEM_WX.get(day_gan, "")


def _tarot_card_for_day(date_str: str, birth: Optional[Birth]) -> dict:
    from divination.engines.tarot import ALL_CARDS, ALL_KEYWORDS
    if birth is not None:
        seed = f"daily-{date_str}-{birth.year}-{birth.month}-{birth.day}"
    else:
        seed = f"daily-{date_str}"
    rng = random.Random(seed)
    name = rng.choice(ALL_CARDS)
    orient = "正位" if rng.random() < 0.65 else "逆位"
    kw = ALL_KEYWORDS.get(name, {"upright": "", "reversed": "", "image_hint": ""})
    keywords = kw["upright"] if orient == "正位" else kw["reversed"]
    return {
        "position": "今日指引",
        "position_meaning": "回应当前最需要看见的重点",
        "name": name,
        "orient": orient,
        "keywords": keywords,
        "seed_used": seed,
    }


def _lenormand_card_for_day(date_str: str, birth: Optional[Birth]) -> dict:
    """今日雷诺曼 — 无逆位, 直接具体。"""
    if birth is not None:
        seed = f"daily-lenormand-{date_str}-{birth.year}-{birth.month}-{birth.day}"
    else:
        seed = f"daily-lenormand-{date_str}"
    rng = random.Random(seed)
    name_en, name_zh, core_meaning = rng.choice(LENORMAND_DAILY)
    return {
        "position": "今日雷诺曼",
        "position_meaning": "今日具体关注点 (无逆位)",
        "name": name_zh,
        "name_en": name_en,
        "keywords": core_meaning,
        "seed_used": seed,
    }


class BirthModel(BaseModel):
    year: int = Field(..., ge=1500, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(12, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: str = "unspecified"
    calendar: str = "gregorian"
    lat: Optional[float] = None
    lng: Optional[float] = None
    tz: str = "Asia/Shanghai"
    is_leap_month: bool = False


def _parse_date(s: Optional[str]) -> date_cls:
    if not s:
        return date_cls.today()
    try:
        return date_cls.fromisoformat(s)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"date must be YYYY-MM-DD, got: {s!r}")


@router.get("/daily")
def get_daily(
    date: Optional[str] = Query(None, description="YYYY-MM-DD; defaults to today"),
    card_type: Literal["tarot", "lenormand", "both"] = "both",
):
    d = _parse_date(date)
    return _build_daily(d, birth=None, card_type=card_type)


class DailyRequest(BaseModel):
    birth: Optional[BirthModel] = None
    date: Optional[str] = None
    card_type: Literal["tarot", "lenormand", "both"] = "both"


@router.post("/daily")
def post_daily(body: DailyRequest):
    d = _parse_date(body.date)
    birth: Optional[Birth] = None
    if body.birth is not None:
        b = body.birth
        birth = Birth(
            year=b.year, month=b.month, day=b.day,
            hour=b.hour, minute=b.minute,
            gender=b.gender, calendar=b.calendar,
            lat=b.lat, lng=b.lng, tz=b.tz, is_leap_month=b.is_leap_month,
        )
    return _build_daily(d, birth=birth, card_type=body.card_type)


def _build_daily(d: date_cls, birth: Optional[Birth], card_type: str = "both") -> dict:
    solar = Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    day_gz = ec.getDay()
    day_gan = ec.getDayGan()
    day_wx = STEM_WX.get(day_gan, "")
    year_gz = ec.getYear()
    try:
        shengxiao = lunar.getYearShengXiao()
    except Exception:
        shengxiao = ""
    jie_qi = lunar.getJieQi() or ""
    date_str = d.isoformat()

    q_seed = f"daily-q-{date_str}"
    if birth is not None:
        q_seed += f"-{birth.year}-{birth.month}-{birth.day}"
    question = random.Random(q_seed).choice(QUESTION_POOL)

    basis = {
        "method": "daily_v1",
        "rule_version": "v1",
        "input_source": "lunar-python",
        "card_type": card_type,
        "calendar_input": "solar",
        "solar_date": date_str,
        "lunar_date": lunar.toString(),
        "jie_qi": jie_qi,
        "limits": (
            "本接口只基于日柱 + 用户日主 + 模板建议;"
            "不做年运/大运/长期预测,不做健康/法律/投资判断。"
        ),
    }

    today_data: dict = {
        "ganzhi_day": day_gz,
        "ganzhi_year": year_gz,
        "shengxiao": shengxiao,
        "day_wuxing": day_wx,
        "lunar_date": lunar.toString(),
        "jie_qi": jie_qi,
        "question_seed": question,
    }
    if card_type in ("tarot", "both"):
        today_data["tarot_card"] = _tarot_card_for_day(date_str, birth)
    if card_type in ("lenormand", "both"):
        today_data["lenormand_card"] = _lenormand_card_for_day(date_str, birth)

    result: dict = {
        "date": date_str,
        "today": today_data,
        "calculation_basis": basis,
    }

    if birth is not None:
        user_gan, user_wx = _user_day_master(birth)
        rel = _relation(day_wx, user_wx)
        tmpl = RELATION_TEMPLATES[rel]
        result["user"] = {
            "day_master": user_gan,
            "day_wuxing": user_wx,
        }
        result["interaction"] = {
            "relation": rel,
            "label": tmpl["label"],
            "focus": tmpl["focus"],
            "action": tmpl["action"],
            "watch": tmpl["watch"],
            "subject_hint": SUBJECT_BY_RELATION[rel],
        }

    return result
