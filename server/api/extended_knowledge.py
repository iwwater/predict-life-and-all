# -*- coding: utf-8 -*-
"""Extended Knowledge API — 暴露 4 个 P2 数据模块的 HTTP 端点.

端点:
    GET /api/knowledge/pengzu?day_ganzhi=癸亥
    GET /api/knowledge/xingming?surname=李&given_name=梓涵
    GET /api/knowledge/sihua?year_gan=甲
    GET /api/knowledge/pailong?sitting=壬&facing=丙&dragon=子

所有响应都是纯数据,无 LLM 调用;输入验证失败 → 返回 422。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from divination.data.almanac_pengzu import (
    BRANCH_TABOOS,
    STEM_TABOOS,
    get_taboo_summary,
)
from divination.data.numerology_xingming import compute_wuge
from divination.data.xuankong_pailong import (
    SHAN_TO_GUA,
    judge_pai_long,
)
from divination.data.ziwei_sihua import (
    NATAL_SIHUA,
    SIHUA_MEANINGS,
    get_natal_sihua,
    get_sihua_meaning,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge-ext"])

_VALID_STEMS = set(STEM_TABOOS.keys())      # 10 天干
_VALID_BRANCHES = set(BRANCH_TABOOS.keys())  # 12 地支
_VALID_SHANS = set(SHAN_TO_GUA.keys())       # 24 山


def _validate_gan_zhi_pair(day_ganzhi: str) -> tuple[str, str]:
    """验证日干支字符串 (e.g. '癸亥') 并返回 (gan, zhi)."""
    if len(day_ganzhi) != 2:
        raise HTTPException(status_code=422, detail=f"日干支应为 2 字: {day_ganzhi!r}")
    gan, zhi = day_ganzhi[0], day_ganzhi[1]
    if gan not in _VALID_STEMS:
        raise HTTPException(status_code=422, detail=f"未知天干: {gan!r}")
    if zhi not in _VALID_BRANCHES:
        raise HTTPException(status_code=422, detail=f"未知地支: {zhi!r}")
    return gan, zhi


# ── 1. 彭祖百忌 ──────────────────────────────────────────────


@router.get("/pengzu")
def get_pengzu(day_ganzhi: str = Query(..., description="日干支，如 癸亥")):
    """彭祖百忌查询: 返回天干忌 + 地支忌 + 完整摘要."""
    gan, zhi = _validate_gan_zhi_pair(day_ganzhi)

    stem_taboo = STEM_TABOOS[gan]
    branch_taboo = BRANCH_TABOOS[zhi]

    # 四化含义字段兼容 Pydantic: dict 直接返回即可
    return {
        "day_gan": gan,
        "day_zhi": zhi,
        "stem_taboo": stem_taboo,
        "branch_taboo": branch_taboo,
        "summary": get_taboo_summary(gan, zhi),
    }


# ── 2. 三才五格 ──────────────────────────────────────────────


@router.get("/xingming")
def get_xingming(
    surname: str = Query(..., min_length=1, max_length=4, description="姓氏"),
    given_name: str = Query(..., min_length=1, max_length=4, description="名字"),
):
    """三才五格 (姓名学) 查询.

    Returns:
        完整五格 dict (含 天/人/地/外/总 + 三才关系 + overall).
    """
    if not surname or not given_name:
        raise HTTPException(status_code=422, detail="姓氏与名字均不能为空")
    if len(surname) > 4 or len(given_name) > 4:
        raise HTTPException(status_code=422, detail="姓氏或名字过长（> 4 字）")

    result = compute_wuge(surname, given_name)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


# ── 3. 紫微四化 ──────────────────────────────────────────────


@router.get("/sihua")
def get_sihua(year_gan: str = Query(..., min_length=1, max_length=1, description="年天干 (甲乙丙丁戊己庚辛壬癸)")):
    """紫微四化查询: 根据年干返回 禄/权/科/忌 对应主星.

    Returns:
        {year_gan, sihua: {禄,权,科,忌}, star_meanings: {...}}
    """
    if year_gan not in _VALID_STEMS:
        raise HTTPException(status_code=422, detail=f"未知年干: {year_gan!r}")

    sihua = get_natal_sihua(year_gan)
    if not sihua:
        raise HTTPException(status_code=404, detail=f"无 {year_gan} 年四化数据")

    # 提取每星的具体含义 (跨 '化禄/化权/化科/化忌' 4 种分类)
    meanings: dict[str, str] = {}
    for hua_type in ("化禄", "化权", "化科", "化忌"):
        star_key = hua_type.replace("化", "")
        star = sihua.get(star_key)
        if star:
            meanings[f"{hua_type}{star}"] = get_sihua_meaning(hua_type, star)

    return {
        "year_gan": year_gan,
        "sihua": sihua,
        "star_meanings": meanings,
    }


# ── 4. 玄空排龙诀 ────────────────────────────────────────────


@router.get("/pailong")
def get_pailong(
    sitting: str = Query(..., description="坐山 (24 山之一, 如 壬)"),
    facing: str = Query(..., description="向 (24 山之一, 如 丙)"),
    dragon: str = Query(..., description="来龙方位 (24 山之一, 如 子)"),
):
    """玄空排龙诀: 来龙 + 山 + 向 三者关系判断.

    Returns:
        judge_pai_long() 完整 dict (含 luck, pattern, meaning).
    """
    for name, val in (("坐山", sitting), ("向", facing), ("来龙", dragon)):
        if val not in _VALID_SHANS:
            raise HTTPException(status_code=422, detail=f"{name} 未知山向: {val!r}")

    return judge_pai_long(dragon, sitting, facing)