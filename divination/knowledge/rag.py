# -*- coding: utf-8 -*-
"""RAG corpus builder for LLM prompt injection.

Scans BOOK_CATALOG + CLASSICAL_RULES to generate structured reference markdown
files under ``server/llm/references/<method>/<book_id>.md``.

Output schema per book:
    # <书名> · RAG 引用
    ## 元信息
    - 朝代: ...
    - 作者: ...
    - 优先级: ★★★ / ★★ / ★
    - 难度: ...
    ## 核心篇章
    ...
    ## 主要规则
    ...
    ## 验证状态
    ...
    ## 简介
    ...

This module is used by:
  - Tests (verify file generation)
  - The /api/knowledge/rag-context endpoint
  - Manual dev runs (`python -m divination.knowledge.rag`)

⚖️ Copyright: All content is *original synthesis* of public-domain classical
rules already encoded in ``classical.py``. No copyrighted text is reproduced.
"""
from __future__ import annotations

import re
from pathlib import Path

from divination.knowledge.books import BOOK_CATALOG
from divination.knowledge.classical import CLASSICAL_RULES

# Repository root — absolute reference for output.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_REFERENCES_DIR = _REPO_ROOT / "server" / "llm" / "references"

# Stable per-book id slug (used as filename).
def _book_slug(title: str) -> str:
    """Convert a book title into a stable, filesystem-safe slug."""
    slug = re.sub(r"[^\w一-鿿]+", "_", title).strip("_")
    # Strip parentheses fragments like (清) etc.
    return slug


def _priority_stars(p: int) -> str:
    return "★" * (4 - p) if 1 <= p <= 3 else "?"


def _build_book_md(book: dict, rules: list[dict]) -> str:
    """Compose a single book markdown file body."""
    title = book.get("title", "未知")
    dynasty = book.get("dynasty", "不详")
    author = book.get("author", "不详")
    priority = book.get("priority", 3)
    difficulty = book.get("difficulty", "intermediate")
    description = book.get("description", "")
    key_chapters = book.get("key_chapters", [])
    verified = book.get("verified_examples", "") or "—"
    notes = book.get("notes", "")
    online = book.get("online_resources", []) or []

    lines = [
        f"# {title} · RAG 引用",
        "",
        f"> {description}",
        "",
        "## 元信息",
        "",
        f"- **书名**: {title}",
        f"- **朝代**: {dynasty}",
        f"- **作者**: {author}",
        f"- **优先级**: {_priority_stars(priority)}",
        f"- **难度**: {difficulty}",
        "",
        "## 核心篇章",
        "",
    ]
    for ch in key_chapters:
        lines.append(f"- {ch}")
    if not key_chapters:
        lines.append("- （暂无）")
    lines.append("")
    lines.append("## 主要规则（结构化）")
    lines.append("")
    if rules:
        for r in rules:
            lines.append(f"### {r['id']} · {r.get('category', '')}")
            lines.append("")
            lines.append(f"- **条件**: {r.get('condition', '')}")
            lines.append(f"- **结论**: {r.get('conclusion', '')}")
            lines.append(f"- **原文**: {r.get('passage', '')}")
            lines.append(f"- **出处**: {r.get('source', '')}")
            lines.append(f"- **置信度**: {r.get('confidence', 0)}/100")
            lines.append("")
    else:
        lines.append("（该书暂未结构化为可注入规则；详见原文篇章。）")
        lines.append("")
    lines.append("## 验证状态")
    lines.append("")
    lines.append(f"{verified}")
    lines.append("")
    lines.append("## 简介")
    lines.append("")
    lines.append(description or "（无简介）")
    lines.append("")
    if notes:
        lines.append("## 备注")
        lines.append("")
        lines.append(notes)
        lines.append("")
    if online:
        lines.append("## 在线资源（公共版本）")
        lines.append("")
        for r in online:
            lines.append(f"- {r}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("⚖️ *本文档由 divination.knowledge.rag 程序化生成，仅为公共领域规则的结构化整理；"
                 "请以原典为准；不构成决策依据。*")
    lines.append("")
    return "\n".join(lines)


def build_rag_corpus(
    references_dir: str | Path | None = None,
    max_priority: int = 3,
) -> dict[str, dict]:
    """Generate structured RAG markdown files for all books in BOOK_CATALOG.

    Args:
        references_dir: Output directory. Defaults to ``server/llm/references``.
        max_priority: Skip books whose priority exceeds this (1=foundational,
            2=advanced, 3=supplemental). Default 3 (all).

    Returns:
        Flat dict mapping ``book_id`` (method/slug) to:
            {
                "method": str,
                "title": str,
                "dynasty": str,
                "author": str,
                "priority": int,
                "content": str (full markdown),
                "path": str (absolute path to written file),
                "rules": list[dict] (rule dicts that were injected),
            }
    """
    out_dir = Path(references_dir) if references_dir else _REFERENCES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # Index rules by id for fast lookup.
    rule_by_id = {r["id"]: r for r in CLASSICAL_RULES}

    corpus: dict[str, dict] = {}
    for method, books in BOOK_CATALOG.items():
        for book in books:
            if book.get("priority", 3) > max_priority:
                continue
            slug = _book_slug(book.get("title", ""))
            book_id = f"{method}/{slug}"
            relevant_ids = book.get("relevant_rules") or []
            rules = [rule_by_id[rid] for rid in relevant_ids if rid in rule_by_id]
            md_body = _build_book_md(book, rules)
            method_dir = out_dir / method
            method_dir.mkdir(parents=True, exist_ok=True)
            out_path = method_dir / f"{slug}.md"
            out_path.write_text(md_body, encoding="utf-8")
            corpus[book_id] = {
                "method": method,
                "title": book.get("title"),
                "dynasty": book.get("dynasty"),
                "author": book.get("author"),
                "priority": book.get("priority"),
                "content": md_body,
                "path": str(out_path),
                "rules": rules,
            }
    return corpus


def get_corpus_for_method(
    method: str,
    max_priority: int = 3,
    references_dir: str | Path | None = None,
) -> dict[str, dict]:
    """Return RAG entries for a single method.

    Args:
        method: method identifier (e.g. "bazi").
        max_priority: priority cutoff.
        references_dir: override output directory (defaults to references/).

    Returns:
        {book_id: corpus_entry, ...} for the requested method.
    """
    full = build_rag_corpus(references_dir=references_dir, max_priority=max_priority)
    return {bid: entry for bid, entry in full.items() if entry["method"] == method}


def assemble_prompt_context(
    method: str,
    max_priority: int = 2,
    references_dir: str | Path | None = None,
) -> str:
    """Assemble a single concatenated markdown block suitable for LLM prompt
    injection for a given method.

    Args:
        method: method identifier.
        max_priority: priority cutoff (default 2 = foundational + advanced).
        references_dir: override directory.

    Returns:
        Markdown string with all book sections concatenated.
    """
    entries = get_corpus_for_method(
        method,
        max_priority=max_priority,
        references_dir=references_dir,
    )
    blocks = [f"## 古籍参考 · {method}", ""]
    for bid, entry in entries.items():
        blocks.append(f"\n---\n\n{entry['content']}")
    return "\n".join(blocks) if entries else "（无相关古籍条目）"


if __name__ == "__main__":  # pragma: no cover
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    corpus = build_rag_corpus()
    print(f"已生成 {len(corpus)} 个古籍 RAG 引用文件。")
    by_method: dict[str, int] = {}
    for entry in corpus.values():
        m = entry["method"]
        by_method[m] = by_method.get(m, 0) + 1
    for m, n in sorted(by_method.items()):
        print(f"  {m}: {n} 本")