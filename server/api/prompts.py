"""GET /api/prompts/{method}  ——  返回该占卜方法的解读 Prompt 模板(markdown)。

前端直连 LLM 时,可以先调这个拿 prompt 模板,再拼装发给 LLM。
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

PROMPT_DIR = Path(__file__).parent.parent / "llm" / "prompts"


@router.get("/prompts/{method}")
def get_prompt(method: str):
    # 白名单校验：method 必须精确匹配 PROMPT_DIR 下某个 .md 文件的 stem。
    # 防路径穿越（Windows 下 ..%5C 编码可逃出目录读任意 .md 文件）。
    if method not in {p.stem for p in PROMPT_DIR.glob("*.md")}:
        raise HTTPException(404, f"no prompt for method: {method}")
    p = PROMPT_DIR / f"{method}.md"
    return {
        "method": method,
        "template": p.read_text(encoding="utf-8"),
        "format": "markdown",
    }


@router.get("/prompts")
def list_prompts():
    files = sorted([p.stem for p in PROMPT_DIR.glob("*.md")])
    return {"prompts": files}
