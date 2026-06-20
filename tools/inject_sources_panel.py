# -*- coding: utf-8 -*-
"""Inject MethodSourcesPanel into method pages.

Strategy per file:
  1. Add `import { MethodSourcesPanel } from "...";` if missing.
  2. Insert `<MethodSourcesPanel method="<id>" />` right before the very last
     top-level `</div>` of the main page component.

Run: `python tools/inject_sources_panel.py`
"""
from __future__ import annotations

import re
from pathlib import Path

# (filename, method_id)
TARGETS: list[tuple[str, str]] = [
    ("BaziPage.tsx", "bazi"),
    ("ZiweiPage.tsx", "ziwei"),
    ("LiuyaoPage.tsx", "liuyao"),
    ("LiurenPage.tsx", "liuren"),
    ("QimenPage.tsx", "qimen"),
    ("WesternPage.tsx", "western"),
    ("HePanPage.tsx", "hepan"),  # may not exist; will skip
    ("TarotPage.tsx", "tarot"),
    ("XiaoliurenPage.tsx", "xiaoliuren"),
    ("TiebanPage.tsx", "tieban"),
    ("NumerologyPage.tsx", "numerology"),
    ("MeihuaPage.tsx", "meihua"),
    ("VedicPage.tsx", "vedic"),
    ("LenormandPage.tsx", "lenormand"),
    ("ChengguPage.tsx", "chenggu"),
    ("XuankongPage.tsx", "fengshui"),  # fengshui is the book-category key
    ("BaziV2Page.tsx", "bazi_v2"),    # bazi v2 → bazi corpus
    ("BazhaiPage.tsx", "fengshui"),   # bazhai maps to fengshui
]

PAGES_DIR = Path("E:/work/predict life and all/apps/web/src/pages/methods")

# Map panel prop "method" to api's "method". Most are 1:1.
# Special mappings:
METHOD_OVERRIDES = {
    "BaziV2Page.tsx": "bazi",
    "BazhaiPage.tsx": "fengshui",
    "XuankongPage.tsx": "fengshui",
}


def _insert_import(text: str, component: str, import_path: str) -> str:
    """Insert a default + named import after the last existing import line."""
    if f"import {{ MethodSourcesPanel }}" in text or f'from "{import_path}"' in text and "MethodSourcesPanel" in text:
        return text
    # Find last `import` line and append.
    lines = text.splitlines(keepends=True)
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line.lstrip().startswith("import "):
            last_import_idx = i
    if last_import_idx < 0:
        return text  # no imports; skip
    new_import = f'import {{ MethodSourcesPanel }} from "{import_path}";\n'
    lines.insert(last_import_idx + 1, new_import)
    return "".join(lines)


def _insert_panel(text: str, method: str) -> str:
    """Insert <MethodSourcesPanel method="..." /> before final `</div>` of the page."""
    # Skip if already injected.
    if "MethodSourcesPanel" in text and "文献出处" in text:
        return text
    # Find last occurrence of `    </div>` (4-space indent = topmost wrapper close)
    # but avoid inner small divs. We target the deepest outermost div which is
    # at indent 4 (matches the wrapper opening).
    # The last 4-space-indented `</div>` in the file before the final `  );` is
    # usually the wrapper close.
    lines = text.splitlines(keepends=True)
    # Find the very last 4-space-indented `</div>` that is followed (eventually) by
    # `  );` (the function return).
    return_close_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i]
        if line.rstrip() == "    </div>":
            return_close_idx = i
            break
    if return_close_idx < 0:
        # Fallback: any 4-space-indented </div>
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("    </div>"):
                return_close_idx = i
                break
    if return_close_idx < 0:
        return text
    panel = f"      <MethodSourcesPanel method=\"{method}\" />\n"
    lines.insert(return_close_idx, panel)
    return "".join(lines)


def process_file(filename: str, method: str) -> bool:
    path = PAGES_DIR / filename
    if not path.exists():
        print(f"  SKIP (not found): {filename}")
        return False
    text = path.read_text(encoding="utf-8")
    if "MethodSourcesPanel" in text and "文献出处" in text:
        print(f"  ALREADY DONE: {filename}")
        return True
    text2 = _insert_import(text, "MethodSourcesPanel", "../../components/MethodSourcesPanel")
    text3 = _insert_panel(text2, method)
    if text3 == text:
        print(f"  NO CHANGE: {filename}")
        return False
    path.write_text(text3, encoding="utf-8")
    print(f"  INJECTED: {filename} (method={method})")
    return True


def main():
    print("=== Injecting MethodSourcesPanel ===\n")
    n_changed = 0
    for fname, default_method in TARGETS:
        method = METHOD_OVERRIDES.get(fname, default_method)
        if process_file(fname, method):
            n_changed += 1
    print(f"\nTotal changed: {n_changed}/{len(TARGETS)}")


if __name__ == "__main__":
    main()