"""GET /api/cases  ——  公开案例库。"""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional
import json

router = APIRouter()

CASES_FILE = Path(__file__).parent.parent / "data" / "celebrity_cases.json"


@router.get("/cases")
def list_cases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页条数"),
    search: Optional[str] = Query(None, description="按姓名模糊搜索"),
):
    if not CASES_FILE.exists():
        return {"cases": [], "page": page, "page_size": page_size, "total": 0}
    try:
        data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    if search:
        s = search.lower()
        data = [c for c in data if s in (c.get("name", "") or "").lower()]
    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "cases": data[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/cases/{case_id}")
def get_case(case_id: str):
    if not CASES_FILE.exists():
        raise HTTPException(404, "case db not found")
    try:
        data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(500, "failed to read cases")
    for c in data:
        if c.get("id") == case_id:
            return c
    raise HTTPException(404, f"case {case_id} not found")
