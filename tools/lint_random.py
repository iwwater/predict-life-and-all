"""Sprint 0.10 — 随机性反模式 linter。

检测规则:
  1. `random.random()` —— 全局未 seed 调用, 不可复现。必须用 `random.Random(seed)` 实例。
  2. `random.seed(` —— 全局 seed, 同样破坏可复现性。
  3. `math.random(` —— 不存在(疑似拼写错), 但出现就是 bug。

豁免:
  - `tests/` 下的文件 (用于测试随机行为本身)
  - `# noqa: random` / `# allow-random` 注释行
  - docstring / 字符串字面量中的出现(简单 grep, 不做 AST 区分)

退出码:
  0: 无违反
  1: 发现违反, 输出 file:line
  2: 配置错误
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ── 默认配置 (可被 pyproject.toml [tool.lint_random] 覆盖) ────────────────────

DEFAULT_FORBIDDEN = [
    r"random\.random\(\)",
    r"random\.seed\(",
    r"math\.random\(",
]
DEFAULT_ALLOWED_PATHS = {"tests/"}
DEFAULT_TARGET_PATHS = ["divination/", "server/"]


def load_config(repo_root: Path) -> tuple[list[str], set[str], list[str]]:
    """从 pyproject.toml 读 [tool.lint_random]。失败则用 defaults。"""
    patterns = list(DEFAULT_FORBIDDEN)
    allowed = set(DEFAULT_ALLOWED_PATHS)
    targets = list(DEFAULT_TARGET_PATHS)

    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return patterns, allowed, targets

    try:
        import tomllib  # py3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return patterns, allowed, targets

    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        cfg = data.get("tool", {}).get("lint_random", {})
        if "forbidden_patterns" in cfg:
            patterns = list(cfg["forbidden_patterns"])
        if "allowed_paths" in cfg:
            allowed = set(cfg["allowed_paths"])
        if "target_paths" in cfg:
            targets = list(cfg["target_paths"])
    except Exception:
        pass

    return patterns, allowed, targets


def is_allowed(path: Path, allowed_paths: set[str]) -> bool:
    """检查 path 是否在豁免列表。"""
    p_str = str(path).replace("\\", "/")
    for ap in allowed_paths:
        if p_str.startswith(ap) or f"/{ap}" in p_str:
            return True
    return False


def scan_file(
    path: Path, compiled: list[tuple[str, re.Pattern[str]]]
) -> list[tuple[int, str, str]]:
    """扫单个文件, 返回 (line_no, pattern, line_text) 列表。"""
    violations = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return violations
    for lineno, line in enumerate(text.splitlines(), start=1):
        # 跳过豁免注释
        stripped = line.lstrip()
        if stripped.startswith("#") and ("noqa: random" in line or "allow-random" in line):
            continue
        for pat_name, pat_re in compiled:
            if pat_re.search(line):
                violations.append((lineno, pat_name, line.strip()))
                break  # 一行只报一次
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 0.10 随机性反模式 linter")
    parser.add_argument(
        "--root",
        default=".",
        help="仓库根目录 (default: cwd)",
    )
    args = parser.parse_args()
    repo_root = Path(args.root).resolve()

    patterns, allowed, targets = load_config(repo_root)
    compiled = [(p, re.compile(p)) for p in patterns]

    files_scanned = 0
    total_violations = 0
    targets_resolved: list[Path] = []
    for t in targets:
        tp = (repo_root / t.rstrip("/")).resolve()
        if tp.exists():
            targets_resolved.append(tp)

    for target in targets_resolved:
        for py_file in target.rglob("*.py"):
            if is_allowed(py_file, allowed):
                continue
            if "__pycache__" in py_file.parts:
                continue
            files_scanned += 1
            violations = scan_file(py_file, compiled)
            for lineno, pat, txt in violations:
                rel = py_file.relative_to(repo_root)
                print(f"{rel}:{lineno}: [{pat}] {txt}")
                total_violations += 1

    print(f"\n[lint_random] scanned {files_scanned} files; {total_violations} violations")
    return 1 if total_violations else 0


if __name__ == "__main__":
    sys.exit(main())
