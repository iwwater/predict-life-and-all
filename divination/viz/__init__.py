"""紫微斗数 SVG 可视化模块。

提供 4 种命盘可视化:
- render_traditional_square: 传统方盘 (12 宫固定位置, 中间留空)
- render_modern_wheel: 现代轮盘 (圆形布局)
- render_palace_grid: 宫位网格 (4 行 3 列)
- render_star_map: 星曜地图 (星曜散布)

签名: render_xxx(palaces, soul, body, five_elements) -> str
不依赖任何第三方库, 全部使用 Python 标准库。
"""
from __future__ import annotations

import html as _html

from .ziwei_svg import (
    render_traditional_square_simple as render_traditional_square,
    render_modern_wheel_simple as render_modern_wheel,
    render_palace_grid_simple as render_palace_grid,
    render_star_map_simple as render_star_map,
    wrap_html as _wrap_html_div,
    render_all,
)


def wrap_html(svg: str, title: str = "紫微斗数命盘") -> str:
    """用完整 HTML 包裹 SVG (含 DOCTYPE/head/style).

    这是顶层 API, 返回独立可打开的 HTML 文档.
    """
    return (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n'
        '<head>\n'
        '  <meta charset="UTF-8">\n'
        f'  <title>{_html.escape(title)}</title>\n'
        '  <style>\n'
        '    body { background: #F4EFE6; font-family: serif; margin: 0; padding: 20px; }\n'
        '    .ziwei-chart { display: flex; justify-content: center; }\n'
        '    svg { max-width: 100%; height: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }\n'
        '  </style>\n'
        '</head>\n'
        '<body>\n'
        f'  {_wrap_html_div(svg)}\n'
        '</body>\n'
        '</html>\n'
    )


__all__ = [
    "render_traditional_square",
    "render_modern_wheel",
    "render_palace_grid",
    "render_star_map",
    "wrap_html",
    "render_all",
]