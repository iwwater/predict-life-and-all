"""GET /api/prompts/{method}  ——  返回该占卜方法的解读 Prompt 模板(markdown)。

前端直连 LLM 时,可以先调这个拿 prompt 模板,再拼装发给 LLM。
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

PROMPT_DIR = Path(__file__).parent.parent / "llm" / "prompts"


@router.get("/prompts/{method}")
def get_prompt(method: str):
    p = PROMPT_DIR / f"{method}.md"
    if not p.exists():
        raise HTTPException(404, f"no prompt for method: {method}")
    return {
        "method": method,
        "template": p.read_text(encoding="utf-8"),
        "format": "markdown",
    }


@router.get("/prompts")
def list_prompts():
    files = sorted([p.stem for p in PROMPT_DIR.glob("*.md")])
    return {"prompts": files}
