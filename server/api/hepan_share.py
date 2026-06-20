"""Sprint 2.4 — 合盘分享卡 API。

设计:
  GET /api/hepan-share/{case_id}
  返回:
    {
      "og": {
        "title": "...",
        "description": "...",
        "image": "/static/share-cards/{case_id}.png",  // 客户端渲染后产生
        "url": "https://mystic-hub.example/share/hepan/{case_id}",
      },
      "card": {
        "case_id": str,
        "person_a": { "animal": "鼠", "year": 1990, "label": "..." },
        "person_b": { "animal": "牛", "year": 1992, "label": "..." },
        "headline": "...",
        "key_signals": [{"key": "marriage_stability", "polarity": "positive", "method": "ziwei"}, ...],
        "dimension_judgments": {"long_term": "weak_support", "relationship": "strong_support", ...},
        "tally_summary": "...",
        "qr_payload": "https://mystic-hub.example/share/hepan/{case_id}",
      },
      "disclaimer": "...",
    }

限制:
  - 仅 hepan/compatibility 案例可分享 (避免泄露其他类型信息)
  - 不含真人姓名/具体生辰 (只到生肖年/动物)
  - OG image 由前端动态生成 (SVG → PNG, 不存盘)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from divination.aggregation.schema import DimensionPolarity
from divination.aggregation.signal_digest import parse_digest_from_verdict

from .cases import _CASES, _RESULTS

router = APIRouter()


# ── 12 生肖映射 ───────────────────────────────────────────────────────

_ZODIAC_ORDER = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]


def _animal_for_year(year: int) -> str:
    """公版: 子年起鼠, 12 循环. year % 12 == 4 → 鼠 (4 mod 12 = 4)?"""
    # 1900 是鼠年, 验证: 1900 % 12 = 4 → idx 0
    idx = (year - 1900) % 12
    return _ZODIAC_ORDER[idx]


# ── 响应模型 ───────────────────────────────────────────────────────────

class ShareOG(BaseModel):
    title: str
    description: str
    image: str
    url: str


class ShareCardPerson(BaseModel):
    animal: str
    year: int
    label: str = ""


class ShareCardSignal(BaseModel):
    key: str
    polarity: str  # positive/negative/neutral
    method: str
    description: str = ""


class ShareCard(BaseModel):
    case_id: str
    person_a: ShareCardPerson
    person_b: ShareCardPerson
    headline: str
    key_signals: list[ShareCardSignal]
    dimension_judgments: dict[str, str] = {}  # 5 档极性
    tally_summary: str = ""
    qr_payload: str = ""


class HepanShareResponse(BaseModel):
    og: ShareOG
    card: ShareCard
    disclaimer: str


# ── 主端点 ─────────────────────────────────────────────────────────────

@router.get("/hepan-share/{case_id}", response_model=HepanShareResponse)
def get_hepan_share(case_id: str, base_url: str = "https://mystic-hub.example"):
    """生成合盘分享卡 (OG meta + 卡片数据)."""
    case = _CASES.get(case_id)
    if case is None:
        raise HTTPException(404, f"case not found: {case_id}")
    if case.event_type not in ("compatibility", "hepan", "relationship"):
        raise HTTPException(400, f"case {case_id} is not hepan/compatibility, got '{case.event_type}'")

    # 取最近的 cast result
    if not case.result_session_id:
        raise HTTPException(409, f"case {case_id} has no result yet, please cast first")
    result = _RESULTS.get(case.result_session_id)
    if result is None:
        raise HTTPException(404, f"result not found for case {case_id}")

    # 抽关键 3 条 signal (按 strength 排序)
    top_signals = sorted(result.signals, key=lambda x: -x.strength)[:3]
    key_signals = [
        ShareCardSignal(
            key=s.signal_key,
            polarity=s.polarity,
            method=s.method,
            description=s.evidence[:80] if s.evidence else "",
        )
        for s in top_signals
    ]

    # 5 维 judgment
    dim_judgments: dict[str, str] = {}
    if result.validation and result.validation.dimension_polarity:
        for dim, pol in result.validation.dimension_polarity.items():
            dim_judgments[dim] = pol.value if isinstance(pol, DimensionPolarity) else str(pol)

    # tally 摘要
    tally_summary = ""
    if result.validation and result.validation.tally_by_scope:
        first_scope = next(iter(result.validation.tally_by_scope.values()), None)
        if first_scope:
            tally_summary = first_scope.summary

    # headline (来自 report)
    headline = result.report.free[:80] if result.report and result.report.free else "合盘参考"

    # person_a / person_b
    person_a = ShareCardPerson(
        animal=_animal_for_year(case.birth.year) if case.birth else "?",
        year=case.birth.year if case.birth else 0,
        label=case.subject or "我",
    )
    # person_b: 取 target_birth (hepan 用)
    target_birth = getattr(case, "target_birth", None)
    person_b = ShareCardPerson(
        animal=_animal_for_year(target_birth.year) if target_birth else "?",
        year=target_birth.year if target_birth else 0,
        label=case.target or "对方",
    )

    # OG
    share_url = f"{base_url}/share/hepan/{case_id}"
    og = ShareOG(
        title=f"合盘参考 · {person_a.label} × {person_b.label}",
        description=headline,
        image=f"{base_url}/static/share-cards/hepan-{case_id}.png",
        url=share_url,
    )

    card = ShareCard(
        case_id=case_id,
        person_a=person_a,
        person_b=person_b,
        headline=headline,
        key_signals=key_signals,
        dimension_judgments=dim_judgments,
        tally_summary=tally_summary,
        qr_payload=share_url,
    )

    return HepanShareResponse(
        og=og,
        card=card,
        disclaimer="本结果为文化视角参考, 不构成专业意见。",
    )


# ── 便捷 API (供 admin/debug) ───────────────────────────────────────

def list_shareable_cases() -> list[dict[str, Any]]:
    """返回所有可分享的 case 摘要。"""
    out: list[dict[str, Any]] = []
    for c in _CASES.values():
        if c.event_type in ("compatibility", "hepan", "relationship") and c.result_session_id:
            out.append({
                "case_id": c.case_id,
                "event_type": c.event_type,
                "result_session_id": c.result_session_id,
                "person_a_animal": _animal_for_year(c.birth.year) if c.birth else "?",
            })
    return out
