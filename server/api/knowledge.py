"""GET /api/knowledge/books - 古籍推荐书单 API。

返回指定术法（或全部）的推荐古籍书单。
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from divination.knowledge import (
    BOOK_CATALOG,
    get_all_books,
    get_books_for_method,
    get_books_with_verification,
    get_method_labels,
    get_method_summary,
)
from divination.knowledge.rag import (
    assemble_prompt_context,
    get_corpus_for_method,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class BookEntry(BaseModel):
    title: str
    dynasty: str
    author: str
    priority: int
    difficulty: str
    description: str
    key_chapters: list[str]
    verified_examples: str = ""
    online_resources: list[str] = []
    book_file: str = ""
    notes: str = ""


class BookListResponse(BaseModel):
    method: str
    books: list[BookEntry]


SUPPORTED_METHODS = list(BOOK_CATALOG.keys())


def _to_entry(b: dict) -> BookEntry:
    """book dict → API Entry。剥离 relevant_rules（内部字段）。"""
    return BookEntry(**{k: v for k, v in b.items() if k != "relevant_rules"})


@router.get("/books", response_model=BookListResponse)
def list_books(
    method: str | None = Query(None, description="术法标识，如 bazi, liuren。不传则返回全部。"),
    max_priority: int = Query(1, ge=1, le=3, description="最高优先级（1=必修, 2=进阶, 3=拓展）"),
    verified_only: bool = Query(False, description="是否只返回已附 verified_examples 的书"),
):
    """返回推荐古籍书单。

    - priority=1（★）：foundational 必修
    - priority=2（★★）：advanced 进阶
    - priority=3（★）：supplemental 拓展
    - verified_only=true：仅返回已附验证案例的书
    """
    if verified_only:
        source = get_books_with_verification()
    else:
        source = {m: get_books_for_method(m, max_priority=max_priority) for m in SUPPORTED_METHODS}

    if method is not None:
        if method not in source:
            return BookListResponse(method=method, books=[])
        books = source[method]
    else:
        books = []
        for m, blist in source.items():
            books.extend(blist)

    return BookListResponse(
        method=method or "all",
        books=[_to_entry(b) for b in books],
    )


@router.get("/methods")
def list_supported_methods():
    """返回已收录书单的术法列表 + 中文标签 + 摘要统计。"""
    return {
        "methods": SUPPORTED_METHODS,
        "labels": get_method_labels(),
        "summary": get_method_summary(),
    }


@router.get("/labels")
def list_method_labels():
    """术法标识 → 中文标签（用于前端 select 选项）。"""
    return {"labels": get_method_labels()}


@router.get("/summary")
def list_method_summary():
    """每种术法的书单摘要（书数 / 已验证书数 / 朝代分布）。"""
    return {"summary": get_method_summary()}


class RagContextResponse(BaseModel):
    method: str
    max_priority: int
    books: list[dict]
    context_markdown: str
    book_count: int


@router.get("/rag-context", response_model=RagContextResponse)
def get_rag_context(
    method: str = Query(..., description="术法标识，如 bazi, ziwei"),
    max_priority: int = Query(2, ge=1, le=3, description="最高优先级（1=必修, 2=进阶, 3=拓展）"),
):
    """返回古籍 RAG 内容（结构化 markdown），用于 LLM prompt 注入。

    数据来源于 BOOK_CATALOG + CLASSICAL_RULES，由
    ``divination.knowledge.rag`` 程序化生成至
    ``server/llm/references/<method>/<slug>.md``。

    - max_priority=1：仅返回 ★★★ 必修典籍
    - max_priority=2：返回 ★★★ + ★★（默认；推荐 LLM 注入）
    - max_priority=3：返回全部
    """
    entries = get_corpus_for_method(method, max_priority=max_priority)
    books_payload: list[dict] = []
    for bid, entry in entries.items():
        books_payload.append({
            "book_id": bid,
            "title": entry["title"],
            "dynasty": entry["dynasty"],
            "author": entry["author"],
            "priority": entry["priority"],
            "path": entry["path"],
            "rule_ids": [r["id"] for r in entry["rules"]],
            "content": entry["content"],
        })
    ctx = assemble_prompt_context(method, max_priority=max_priority)
    return RagContextResponse(
        method=method,
        max_priority=max_priority,
        books=books_payload,
        context_markdown=ctx,
        book_count=len(books_payload),
    )
