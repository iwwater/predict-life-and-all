# -*- coding: utf-8 -*-
"""Tests for RAG corpus builder + API endpoint."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from divination.knowledge.rag import (
    _REFERENCES_DIR,
    assemble_prompt_context,
    build_rag_corpus,
    get_corpus_for_method,
)


def test_build_rag_corpus_creates_files(tmp_path: Path):
    """build_rag_corpus() should write markdown files under references/."""
    corpus = build_rag_corpus(references_dir=tmp_path, max_priority=3)
    assert len(corpus) > 0
    # Every entry must have a path that exists.
    for bid, entry in corpus.items():
        p = Path(entry["path"])
        assert p.exists(), f"missing file for {bid}"
        assert p.suffix == ".md"
        # Markdown must contain key sections.
        content = entry["content"]
        assert "## 元信息" in content
        assert "## 核心篇章" in content
        assert "## 验证状态" in content


def test_bazi_corpus_has_yhz_rules(tmp_path: Path):
    """Bazi RAG corpus should include rules from classical.py."""
    entries = get_corpus_for_method("bazi", max_priority=2, references_dir=tmp_path)
    # Find 渊海子平 entry
    yhz_keys = [bid for bid in entries if "渊海子平" in bid]
    assert yhz_keys, "expected 渊海子平 entry"
    yhz = entries[yhz_keys[0]]
    rule_ids = [r["id"] for r in yhz["rules"]]
    assert "yhz_001" in rule_ids
    assert "yhz_002" in rule_ids


def test_priority_filter(tmp_path: Path):
    """max_priority=1 should only include foundational books."""
    corpus_p1 = build_rag_corpus(references_dir=tmp_path, max_priority=1)
    corpus_p3 = build_rag_corpus(references_dir=tmp_path, max_priority=3)
    # p1 must be a strict subset of p3 (or equal if all are priority=1).
    p1_titles = {e["title"] for e in corpus_p1.values()}
    p3_titles = {e["title"] for e in corpus_p3.values()}
    assert p1_titles.issubset(p3_titles)
    assert len(p1_titles) < len(p3_titles)


def test_assemble_prompt_context(tmp_path: Path):
    """assemble_prompt_context should produce a concatenated markdown string."""
    ctx = assemble_prompt_context("bazi", max_priority=2, references_dir=tmp_path)
    assert isinstance(ctx, str)
    assert "古籍参考 · bazi" in ctx
    assert "元信息" in ctx
    assert "渊海子平" in ctx or "滴天髓" in ctx


def test_method_with_no_books_returns_empty(tmp_path: Path):
    """An unknown method should produce empty corpus, not error."""
    entries = get_corpus_for_method("unknown_method_xyz", references_dir=tmp_path)
    assert entries == {}


def test_default_references_dir_is_repo():
    """Default references dir should be the project's server/llm/references."""
    p = Path(_REFERENCES_DIR)
    assert p.name == "references"
    assert p.parent.name == "llm"
    assert p.parent.parent.name == "server"


# ── API endpoint tests ──────────────────────────────────────────────


def test_api_rag_context_returns_markdown():
    """GET /api/knowledge/rag-context?method=bazi should return markdown."""
    # Lazy import the app to avoid import-time side effects.
    from server.main import app

    client = TestClient(app)
    r = client.get("/api/knowledge/rag-context", params={"method": "bazi", "max_priority": 2})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["method"] == "bazi"
    assert body["max_priority"] == 2
    assert body["book_count"] > 0
    assert "古籍参考" in body["context_markdown"]
    # books should be list of dicts
    assert isinstance(body["books"], list)
    assert all("title" in b for b in body["books"])


def test_api_rag_context_invalid_method():
    """Unknown method should return empty (graceful)."""
    from server.main import app

    client = TestClient(app)
    r = client.get("/api/knowledge/rag-context", params={"method": "nonsense_xyz"})
    assert r.status_code == 200
    body = r.json()
    assert body["book_count"] == 0


def test_api_rag_context_priority_levels():
    """Different priorities return different counts."""
    from server.main import app

    client = TestClient(app)
    r1 = client.get("/api/knowledge/rag-context", params={"method": "bazi", "max_priority": 1})
    r2 = client.get("/api/knowledge/rag-context", params={"method": "bazi", "max_priority": 3})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["book_count"] <= r2.json()["book_count"]