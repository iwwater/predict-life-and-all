"""GET /api/knowledge/books - 古籍推荐书单 API。

返回指定术法（或全部）的推荐古籍书单。
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from divination.knowledge import get_books_for_method, get_all_books, BOOK_CATALOG

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class BookEntry(BaseModel):
    title: str
    dynasty: str
    author: str
    priority: int
    difficulty: str
    description: str
    key_chapters: list[str]
    notes: str = ""


class BookListResponse(BaseModel):
    method: str
    books: list[BookEntry]


SUPPORTED_METHODS = list(BOOK_CATALOG.keys())


@router.get("/books", response_model=BookListResponse)
def list_books(
    method: str | None = Query(None, description=f"术法标识，如 bazi, liuren。不传则返回全部。"),
    max_priority: int = Query(1, ge=1, le=3, description="最高优先级（1=必修, 2=进阶, 3=拓展）"),
):
    """返回推荐古籍书单。

    - priority=1（★）：foundational 必修
    - priority=2（★★）：advanced 进阶
    - priority=3（★）：supplemental 拓展
    """
    if method is not None:
        if method not in SUPPORTED_METHODS:
            return BookListResponse(method=method, books=[])
        books = get_books_for_method(method, max_priority=max_priority)
    else:
        # All methods
        all_books = get_all_books()
        books = []
        for m, blist in all_books.items():
            books.extend([b for b in blist if b["priority"] <= max_priority])

    return BookListResponse(
        method=method or "all",
        books=[BookEntry(**{k: v for k, v in b.items() if k != "relevant_rules"}) for b in books],
    )


@router.get("/methods")
def list_supported_methods():
    """返回已收录书单的术法列表。"""
    return {"methods": SUPPORTED_METHODS}
