"""GET /api/almanac — 老黄历(农历日历+宜忌+冲煞+吉神+星宿+建除+彭祖百忌).

端点:
    GET /api/almanac?date=YYYY-MM-DD          — 单日完整黄历
    GET /api/almanac/month?year=YYYY&month=M  — 整月概览(每天关键信息)

设计原则:
    - 纯数据,不调 LLM
    - 基于 lunar-python + 传统规则
    - 文案温和,避免迷信恐吓
"""
import logging
from datetime import date as date_cls
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from lunar_python import Solar, Lunar
from pydantic import BaseModel, Field

router = APIRouter()
log = logging.getLogger("almanac")

# 十二建除 + 黄道黑道对应
JIAN_CHU_HUANG_HEI: dict[str, str] = {
    "建": "黑道", "除": "黄道", "满": "黑道", "平": "黄道",
    "定": "黄道", "执": "黄道", "破": "黑道", "危": "黄道",
    "成": "黄道", "收": "黑道", "开": "黄道", "闭": "黑道",
}

# 黄道吉日标识映射 (建除十二神)
JIAN_CHU = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]

# 二十八星宿列表
XIU_LIST = [
    "角", "亢", "氐", "房", "心", "尾", "箕",  # 东方青龙
    "斗", "牛", "女", "虚", "危", "室", "壁",  # 北方玄武
    "奎", "娄", "胃", "昴", "毕", "觜", "参",  # 西方白虎
    "井", "鬼", "柳", "星", "张", "翼", "轸",  # 南方朱雀
]

# 五行色标记
WUXING_COLOR: dict[str, str] = {
    "金": "#C9A24B", "木": "#4FB3A0", "水": "#5B8DEF",
    "火": "#C8553D", "土": "#8A8F98",
}

STEM_WX: dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

BRANCH_WX: dict[str, str] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

BRANCH_ANIMAL: dict[str, str] = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
    "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
    "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}


def _parse_date(s: Optional[str]) -> date_cls:
    if not s:
        return date_cls.today()
    try:
        return date_cls.fromisoformat(s)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"date must be YYYY-MM-DD, got: {s!r}")


def _build_single(d: date_cls) -> dict:
    """构造单日完整黄历数据."""
    solar = Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    # 干支
    year_gz = ec.getYear()
    month_gz = ec.getMonth()
    day_gz = ec.getDay()
    day_gan = ec.getDayGan()
    day_zhi = ec.getDayZhi()

    # 干支拆解
    ganzhi_year_parts = list(year_gz) if len(year_gz) >= 2 else ["", ""]
    ganzhi_month_parts = list(month_gz) if len(month_gz) >= 2 else ["", ""]
    ganzhi_day_parts = list(day_gz) if len(day_gz) >= 2 else ["", ""]

    # 五行
    day_wx = STEM_WX.get(day_gan, "")
    day_zhi_wx = BRANCH_WX.get(day_zhi, "")
    na_yin = lunar.getDayNaYin() or ""

    # 宜忌
    yi = lunar.getDayYi() or []
    ji = lunar.getDayJi() or []

    # 吉神凶煞
    ji_shen = lunar.getDayJiShen() or []
    xiong_sha = lunar.getDayXiongSha() or []

    # 冲煞
    chong = lunar.getDayChong() or ""
    chong_desc = lunar.getDayChongDesc() or ""
    chong_sx = lunar.getDayChongShengXiao() or ""
    sha = lunar.getDaySha() or ""

    # 天神 / 黄道黑道
    tian_shen = lunar.getDayTianShen() or ""
    tian_shen_type = lunar.getDayTianShenType() or ""
    tian_shen_luck = lunar.getDayTianShenLuck() or ""

    # 建除
    zhi_xing = lunar.getZhiXing() or ""
    jian_chu_huang_hei = JIAN_CHU_HUANG_HEI.get(zhi_xing, "")

    # 星宿
    xiu = lunar.getXiu() or ""
    xiu_luck = lunar.getXiuLuck() or ""
    xiu_song = lunar.getXiuSong() or ""

    # 彭祖百忌
    pengzu_gan = lunar.getPengZuGan() or ""
    pengzu_zhi = lunar.getPengZuZhi() or ""

    # 胎神
    tai_shen = lunar.getDayPositionTai() or ""

    # 生肖
    shengxiao_year = ""
    try:
        shengxiao_year = lunar.getYearShengXiao() or ""
    except Exception:
        pass
    day_shengxiao = lunar.getDayShengXiao() or ""

    # 节气
    jie_qi = lunar.getJieQi() or ""
    jie = lunar.getJie() or ""

    # 数九 / 伏天
    shu_jiu = lunar.getShuJiu() or ""

    # 太岁方位
    tai_sui_pos = lunar.getDayPositionTaiSuiDesc() or ""
    year_tai_sui = ""
    try:
        year_tai_sui = lunar.getYearPositionTaiSuiDesc() or ""
    except Exception:
        pass

    # 纳音
    year_na_yin = ""
    try:
        year_na_yin = lunar.getYearNaYin() or ""
    except Exception:
        pass

    # 阴贵 / 阳贵
    yin_gui = lunar.getDayPositionYinGuiDesc() or ""

    return {
        "solar_date": d.isoformat(),
        "lunar": {
            "year": lunar.getYear(),
            "month": abs(lunar.getMonth()),
            "day": lunar.getDay(),
            "is_leap": lunar.getMonth() < 0,
            "date_str": lunar.toString(),
            "year_in_ganzhi": year_gz,
            "month_in_ganzhi": month_gz,
            "day_in_ganzhi": day_gz,
            "year_shengxiao": shengxiao_year,
            "day_shengxiao": day_shengxiao,
        },
        "ganzhi": {
            "year": {
                "full": year_gz,
                "gan": ganzhi_year_parts[0] if len(ganzhi_year_parts) > 0 else "",
                "zhi": ganzhi_year_parts[1] if len(ganzhi_year_parts) > 1 else "",
                "animal": BRANCH_ANIMAL.get(ganzhi_year_parts[1], "") if len(ganzhi_year_parts) > 1 else "",
            },
            "month": {
                "full": month_gz,
                "gan": ganzhi_month_parts[0] if len(ganzhi_month_parts) > 0 else "",
                "zhi": ganzhi_month_parts[1] if len(ganzhi_month_parts) > 1 else "",
            },
            "day": {
                "full": day_gz,
                "gan": day_gan,
                "zhi": day_zhi,
                "animal": BRANCH_ANIMAL.get(day_zhi, ""),
            },
        },
        "wuxing": {
            "day_gan": day_wx,
            "day_zhi": day_zhi_wx,
            "day_gan_color": WUXING_COLOR.get(day_wx, ""),
        },
        "na_yin": {
            "day": na_yin,
            "year": year_na_yin,
        },
        "yi_ji": {
            "yi": yi,
            "ji": ji,
        },
        "shen_sha": {
            "ji_shen": ji_shen,
            "xiong_sha": xiong_sha,
        },
        "chong_sha": {
            "chong": chong,
            "chong_desc": chong_desc,
            "chong_shengxiao": chong_sx,
            "sha": sha,
        },
        "tian_shen": {
            "name": tian_shen,
            "type": tian_shen_type,  # 黄道/黑道
            "luck": tian_shen_luck,  # 吉/凶
        },
        "jian_chu": {
            "name": zhi_xing,
            "type": jian_chu_huang_hei,
            "is_huangdao": jian_chu_huang_hei == "黄道",
        },
        "xing_xiu": {
            "name": xiu,
            "luck": xiu_luck,
            "song": xiu_song,
        },
        "pengzu_baiji": {
            "gan": pengzu_gan,
            "zhi": pengzu_zhi,
        },
        "tai_shen": tai_shen,
        "tai_sui": {
            "day": tai_sui_pos,
            "year": year_tai_sui,
        },
        "yin_gui": yin_gui,
        "jie_qi": jie_qi,
        "jie": jie,
        "shu_jiu": shu_jiu,
        "jie_qi_note": _jie_qi_note(jie_qi, jie),
        "calculation_basis": {
            "method": "almanac_v1",
            "rule_version": "v1",
            "input_source": "lunar-python",
            "calendar_input": "solar",
            "limits": "本接口为传统黄历数据展示,仅供参考,不构成决策建议。",
        },
    }


def _jie_qi_note(jie_qi: str, jie: str) -> str:
    """生成节气友好提示."""
    if not jie_qi and not jie:
        return ""
    parts = []
    if jie:
        parts.append(f"当前节气: {jie}")
    if jie_qi:
        parts.append(f"今日: {jie_qi}")
    return " · ".join(parts)


@router.get("/almanac")
def get_almanac(
    date: Optional[str] = Query(None, description="YYYY-MM-DD; defaults to today"),
):
    """返回单日完整老黄历数据."""
    d = _parse_date(date)
    return _build_single(d)


@router.get("/almanac/month")
def get_almanac_month(
    year: int = Query(..., ge=1500, le=2100, description="公历年份"),
    month: int = Query(..., ge=1, le=12, description="公历月份"),
):
    """返回整月概览: 每天的关键黄历信息."""
    import calendar as cal_mod

    days_in_month = cal_mod.monthrange(year, month)[1]
    days = []
    for day in range(1, days_in_month + 1):
        d = date_cls(year, month, day)
        try:
            solar = Solar.fromYmdHms(year, month, day, 12, 0, 0)
            lunar = solar.getLunar()
            ec = lunar.getEightChar()
            day_gz = ec.getDay()
            day_gan = ec.getDayGan()

            yi = lunar.getDayYi() or []
            ji = lunar.getDayJi() or []
            ji_shen = lunar.getDayJiShen() or []
            xiong_sha = lunar.getDayXiongSha() or []
            zhi_xing = lunar.getZhiXing() or ""
            chong = lunar.getDayChongShengXiao() or ""
            sha = lunar.getDaySha() or ""
            jie_qi = lunar.getJieQi() or ""

            is_huangdao = JIAN_CHU_HUANG_HEI.get(zhi_xing) == "黄道"

            days.append({
                "solar_day": day,
                "lunar_day": lunar.getDay(),
                "lunar_month": abs(lunar.getMonth()),
                "day_ganzhi": day_gz,
                "day_gan": day_gan,
                "day_wuxing": STEM_WX.get(day_gan, ""),
                "zhi_xing": zhi_xing,
                "is_huangdao": is_huangdao,
                "chong_shengxiao": chong,
                "sha": sha,
                "yi": yi[:6],  # 最多6条, 节省传输
                "ji": ji[:4],
                "ji_shen": ji_shen[:3],
                "xiong_sha": xiong_sha[:3],
                "jie_qi": jie_qi,
                "lunar_date_short": f"{'闰' if (lunar.getMonth() < 0) else ''}{['正','二','三','四','五','六','七','八','九','十','冬','腊'][abs(lunar.getMonth())-1]}月{['','初一','初二','初三','初四','初五','初六','初七','初八','初九','初十','十一','十二','十三','十四','十五','十六','十七','十八','十九','二十','廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十'][lunar.getDay()]}",
            })
        except Exception as exc:
            log.warning("Failed to build almanac day %s-%s-%s: %s", year, month, day, exc)
            days.append({
                "solar_day": day,
                "error": str(exc),
            })

    return {
        "year": year,
        "month": month,
        "days": days,
    }
