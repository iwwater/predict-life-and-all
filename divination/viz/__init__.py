"""紫微斗数 SVG 可视化模块。

提供 8 种可视化:
- 4 种基础盘 (传统方盘/现代轮盘/宫位网格/星曜地图)
- 4 种运程盘 (本命/大限/流年/流月) — 古籍×仪器风
- 1 种小限盘 (xiaoxian) — 高亮小限所在宫位

签名: render_xxx(palaces, ...) -> str
不依赖任何第三方库, 全部使用 Python 标准库。
"""
from __future__ import annotations

import html as _html

from .ziwei_svg import (
    render_traditional_square_simple as render_traditional_square,
    render_modern_wheel_simple as render_modern_wheel,
    render_palace_grid_simple as render_palace_grid,
    render_star_map_simple as render_star_map,
    render_natal_chart,
    render_decadal_chart,
    render_yearly_chart,
    render_monthly_chart,
    render_xiaoxian_chart,
    render_xiaoxian_at_age,
    render_all_scopes,
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
    "render_natal_chart",
    "render_decadal_chart",
    "render_yearly_chart",
    "render_monthly_chart",
    "render_xiaoxian_chart",
    "render_xiaoxian_at_age",
    "render_all_scopes",
    "wrap_html",
    "render_all",
]