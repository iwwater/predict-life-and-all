"""Zi Wei Dou Shu SVG visualization (4 styles).

4 renderers, all using Python stdlib only:
  1. render_traditional_square  - 经典方盘 (4×3 palace grid)
  2. render_modern_wheel       - 现代轮盘 (12 palace radial layout)
  3. render_palace_grid        - 宫位网格 (modern flat 4×3 grid)
  4. render_star_map           - 星曜地图 (scatter stars on full chart)

输入数据: ``divination.engines.ziwei._palaces`` 返回的 list[dict].
每个 dict 包含 name/index/is_body/is_body_palace/is_original_palace/
heavenly_stem/earthly_branch/major_stars/minor_stars/adjective_stars/
changsheng12/boshi12/jiangqian12/suiqian12.
"""

from __future__ import annotations

import html
import math
from typing import Any, Mapping, Sequence

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 紫微 12 宫固定顺序 (左下→右下→上排, 传统方盘 4×3 布局)
TRADITIONAL_GRID_ORDER = [
    # 4×4 网格, 中间 2×2 合并为中宫
    # 12 宫分布在 16 - 4 = 12 个外圈格
    # row 0: 4 格顶排
    # row 1: 左 2 格 + 中宫 + 右 1 格
    # row 2: 左 1 格 + 中宫 + 右 2 格
    # row 3: 4 格底排
]

PALACE_LAYOUT_4x3 = [
    # (row, col) -> palace index 0..11
    # 顶排 4 格: row 0 全占
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    # 中间上: 左右各 1 格 (中间 2 列为中宫)
    [(1, 0), None,    None,    (1, 3)],
    # 中间下: 左右各 1 格
    [(2, 0), None,    None,    (2, 3)],
    # 底排 4 格: row 3 全占
    [(3, 0), (3, 1), (3, 2), (3, 3)],
]

# 12 宫在方盘的固定位置 (4×4 网格, 中宫 2×2 合并)
# 宫位索引: 0=命, 1=兄弟, 2=夫妻, 3=子女, 4=财帛, 5=疾厄,
#           6=迁移, 7=交友, 8=官禄, 9=田宅, 10=福德, 11=父母
PALACE_POSITIONS = {
    # 上排 (顶) 4 格: 父母(10) 福德(11) 田宅(9) 官禄(8)
    (0, 0): 10, (0, 1): 11, (0, 2): 9, (0, 3): 8,
    # 中间左 + 右侧: 命宫(0) 左 | 迁移(6) 右 (row 1)
    (1, 0): 0,                       (1, 3): 6,
    # 次中间: 疾厄(5) 左 | 交友(7) 右 (row 2)
    (2, 0): 5,                       (2, 3): 7,
    # 底排 4 格: 兄弟(1) 夫妻(2) 子女(3) 财帛(4)
    (3, 0): 1,  (3, 1): 2,  (3, 2): 3,  (3, 3): 4,
}

# 现代轮盘 12 宫, 从 12 点开始顺时针 (命宫为顶)
# 但更传统的是命宫在下方
WHEEL_PALACE_ORDER = list(range(12))  # palace index in clockwise order

# 颜色调色板 (宣纸墨色)
COLORS = {
    "bg": "#f7f3e8",
    "ink": "#2b2b2b",
    "border": "#3a3a3a",
    "body_palace": "#c8102e",      # 朱砂红
    "original_palace": "#1e3a8a",  # 靛蓝
    "major_star": "#7a1f1f",
    "minor_star": "#5a5a5a",
    "adj_star": "#9a7b3a",
    "mutagen": "#c8102e",
    "star_hua_lu": "#1f7a3a",
    "star_hua_quan": "#1e3a8a",
    "star_hua_ke": "#7a4a1f",
    "star_hua_ji": "#7a1f1f",
    "grid_line": "#7a6a4a",
    "title": "#2b2b2b",
    "cell_bg": "#fdfaf2",
    "cell_bg_body": "#fde8e8",
}


def _esc(text: Any) -> str:
    """HTML escape a value."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def _palace_index(palace: Mapping[str, Any]) -> int:
    """Safely get palace index."""
    idx = palace.get("index")
    if idx is None:
        return -1
    try:
        return int(idx)
    except (TypeError, ValueError):
        return -1


def _sort_palaces(palaces: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Sort palaces by index, filling missing indexes with placeholder."""
    out: list[dict[str, Any]] = []
    by_idx: dict[int, dict[str, Any]] = {}
    for p in palaces or []:
        idx = _palace_index(p)
        if idx >= 0:
            by_idx[idx] = dict(p)
    for i in range(12):
        if i in by_idx:
            out.append(by_idx[i])
        else:
            out.append({
                "name": "",
                "index": i,
                "is_body": False,
                "is_body_palace": False,
                "is_original_palace": False,
                "heavenly_stem": "",
                "earthly_branch": "",
                "major_stars": [],
                "minor_stars": [],
                "adjective_stars": [],
                "changsheng12": "",
                "boshi12": "",
                "jiangqian12": "",
                "suiqian12": "",
            })
    return out


# ---------------------------------------------------------------------------
# 公共辅助
# ---------------------------------------------------------------------------

def _mutagen_lookup(palace: Mapping[str, Any]) -> set[str]:
    """从宫位 metadata 提取四化标记 (禄/权/科/忌), 简化为 star_name+hua 的 set."""
    result: set[str] = set()
    for key in ("major_stars", "minor_stars"):
        for s in palace.get(key) or []:
            for h in ("化禄", "化权", "化科", "化忌"):
                if h in str(s):
                    result.add(f"{s}")
    return result


def _render_stars_lines(
    palace: Mapping[str, Any],
    star_color_key: str = "major_star",
    max_chars_per_line: int = 6,
) -> str:
    """Render major + minor + adj stars as text lines, with optional hua markers."""
    lines: list[str] = []

    major = list(palace.get("major_stars") or [])
    minor = list(palace.get("minor_stars") or [])
    adj = list(palace.get("adjective_stars") or [])

    for star in major:
        lines.append(f'<text class="star-{star_color_key}">{_esc(star)}</text>')
    for star in minor:
        lines.append(f'<text class="star-minor_star">{_esc(star)}</text>')
    for star in adj[:4]:  # 限缩避免过长
        lines.append(f'<text class="star-adj_star">{_esc(star)}</text>')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. 传统方盘
# ---------------------------------------------------------------------------

def render_traditional_square(
    palaces: Sequence[Mapping[str, Any]],
    *,
    title: str = "紫微斗数 · 传统方盘",
    size: int = 720,
) -> str:
    """Render the classic 4×4 square chart (传统方盘) with 2×2 中宫."""
    sorted_pcs = _sort_palaces(palaces)
    cell = size / 4  # 4 列, 4 行 (中宫占中间 2×2)
    mid_x = cell * 2  # 中宫中心 X
    mid_y = 30 + cell * 2  # 中宫中心 Y (顶部留 30 标题)
    center_radius = cell

    # 4 行布局: 总高度 = 30 (标题) + 4*cell (网格)
    grid_height = cell * 4
    total_height = 30 + grid_height + 10

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {total_height}" width="{size}" height="{total_height}" '
        f'class="ziwei-traditional-square">'
    )
    parts.append(f'<rect width="{size}" height="{total_height}" fill="{COLORS["bg"]}" />')
    parts.append(
        f'<text x="{size / 2}" y="22" text-anchor="middle" '
        f'font-size="18" font-weight="bold" fill="{COLORS["title"]}">{_esc(title)}</text>'
    )

    # 网格背景 (整 4×4)
    parts.append(
        f'<rect x="0" y="30" width="{size}" height="{grid_height}" '
        f'fill="{COLORS["cell_bg"]}" stroke="{COLORS["border"]}" stroke-width="3" />'
    )
    # 横线 1 (row 0/1 分界)
    parts.append(
        f'<line x1="0" y1="{30 + cell}" x2="{size}" y2="{30 + cell}" '
        f'stroke="{COLORS["border"]}" stroke-width="2" />'
    )
    # 横线 2 (row 1/2 分界 = 中宫顶)
    parts.append(
        f'<line x1="0" y1="{30 + cell * 2}" x2="{size}" y2="{30 + cell * 2}" '
        f'stroke="{COLORS["border"]}" stroke-width="2" />'
    )
    # 横线 3 (row 2/3 分界 = 中宫底)
    parts.append(
        f'<line x1="0" y1="{30 + cell * 3}" x2="{size}" y2="{30 + cell * 3}" '
        f'stroke="{COLORS["border"]}" stroke-width="2" />'
    )
    # 竖线 1
    parts.append(
        f'<line x1="{cell}" y1="30" x2="{cell}" y2="{30 + grid_height}" '
        f'stroke="{COLORS["border"]}" stroke-width="2" />'
    )
    # 竖线 2 (中宫左)
    parts.append(
        f'<line x1="{cell * 2}" y1="30" x2="{cell * 2}" y2="{30 + grid_height}" '
        f'stroke="{COLORS["border"]}" stroke-width="2" />'
    )
    # 竖线 3 (中宫右)
    parts.append(
        f'<line x1="{cell * 3}" y1="30" x2="{cell * 3}" y2="{30 + grid_height}" '
        f'stroke="{COLORS["border"]}" stroke-width="2" />'
    )

    # 中宫 (中央 2×2 合并, 显示命主信息)
    five_class = ""
    parts.append(
        f'<rect x="{cell}" y="{30 + cell}" width="{cell * 2}" height="{cell * 2}" '
        f'fill="{COLORS["bg"]}" stroke="{COLORS["border"]}" stroke-width="1" />'
    )
    parts.append(
        f'<text x="{mid_x}" y="{mid_y - 10}" text-anchor="middle" '
        f'font-size="22" fill="{COLORS["title"]}" font-weight="bold">中宫</text>'
    )
    parts.append(
        f'<text x="{mid_x}" y="{mid_y + 14}" text-anchor="middle" '
        f'font-size="13" fill="{COLORS["adj_star"]}">{_esc(five_class)}</text>'
    )
    parts.append(
        f'<circle cx="{mid_x}" cy="{mid_y}" r="{center_radius * 0.7}" '
        f'fill="none" stroke="{COLORS["grid_line"]}" stroke-dasharray="4 3" />'
    )
    # 中宫八卦方位提示
    parts.append(
        f'<text x="{mid_x}" y="{mid_y - center_radius * 0.55}" text-anchor="middle" '
        f'font-size="10" fill="{COLORS["adj_star"]}">离</text>'
    )
    parts.append(
        f'<text x="{mid_x}" y="{mid_y + center_radius * 0.65}" text-anchor="middle" '
        f'font-size="10" fill="{COLORS["adj_star"]}">坎</text>'
    )

    # 12 宫位 (PALACE_POSITIONS 排布)
    for (row, col), p_idx in PALACE_POSITIONS.items():
        if p_idx < 0 or p_idx >= len(sorted_pcs):
            continue
        p = sorted_pcs[p_idx]
        x = col * cell
        y = 30 + row * cell
        cx = x + cell / 2
        cy = y + cell / 2

        is_body = bool(p.get("is_body_palace") or p.get("is_body"))
        is_orig = bool(p.get("is_original_palace"))
        fill = COLORS["cell_bg_body"] if is_body else COLORS["cell_bg"]

        parts.append(
            f'<rect x="{x + 1}" y="{y + 1}" width="{cell - 2}" height="{cell - 2}" '
            f'fill="{fill}" stroke="{COLORS["border"]}" stroke-width="0.5" />'
        )

        # 宫名 (顶部)
        accent = ""
        if is_body:
            accent = " ●"
        elif is_orig:
            accent = " ☆"
        parts.append(
            f'<text x="{x + 8}" y="{y + 18}" font-size="13" font-weight="bold" '
            f'fill="{COLORS["body_palace"] if is_body else COLORS["ink"]}">'
            f'{_esc(p.get("name", ""))}{accent}</text>'
        )
        # 干支 (右上)
        stem_branch = f'{p.get("heavenly_stem", "")}{p.get("earthly_branch", "")}'
        if stem_branch:
            parts.append(
                f'<text x="{x + cell - 8}" y="{y + 18}" text-anchor="end" '
                f'font-size="11" fill="{COLORS["adj_star"]}">{_esc(stem_branch)}</text>'
            )

        # 星曜 (主体)
        major = list(p.get("major_stars") or [])
        minor = list(p.get("minor_stars") or [])
        adj = list(p.get("adjective_stars") or [])

        text_y = y + 36
        for star in major:
            parts.append(
                f'<text x="{cx}" y="{text_y}" text-anchor="middle" font-size="13" '
                f'font-weight="bold" fill="{COLORS["major_star"]}">{_esc(star)}</text>'
            )
            text_y += 16
        for star in minor:
            parts.append(
                f'<text x="{cx}" y="{text_y}" text-anchor="middle" font-size="11" '
                f'fill="{COLORS["minor_star"]}">{_esc(star)}</text>'
            )
            text_y += 14
        for star in adj[:3]:
            parts.append(
                f'<text x="{cx}" y="{text_y}" text-anchor="middle" font-size="10" '
                f'fill="{COLORS["adj_star"]}">{_esc(star)}</text>'
            )
            text_y += 12

        # 12 神杀 (底部)
        c12 = p.get("changsheng12") or ""
        if c12:
            parts.append(
                f'<text x="{x + 8}" y="{y + cell - 10}" font-size="10" '
                f'fill="{COLORS["adj_star"]}">{_esc(c12)}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 2. 现代轮盘
# ---------------------------------------------------------------------------

def render_modern_wheel(
    palaces: Sequence[Mapping[str, Any]],
    *,
    title: str = "紫微斗数 · 现代轮盘",
    size: int = 720,
) -> str:
    """Render the modern 12-palace radial wheel chart (现代轮盘)."""
    sorted_pcs = _sort_palaces(palaces)
    cx = size / 2
    cy = (size + 40) / 2
    r_outer = size / 2 - 10
    r_inner = r_outer * 0.55
    r_center = r_outer * 0.25

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size + 40}" width="{size}" height="{size + 40}" '
        f'class="ziwei-modern-wheel">'
    )
    parts.append(f'<rect width="{size}" height="{size + 40}" fill="{COLORS["bg"]}" />')
    parts.append(
        f'<text x="{cx}" y="22" text-anchor="middle" '
        f'font-size="18" font-weight="bold" fill="{COLORS["title"]}">{_esc(title)}</text>'
    )

    # 圆环背景
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" '
        f'fill="{COLORS["cell_bg"]}" stroke="{COLORS["border"]}" stroke-width="3" />'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" '
        f'fill="{COLORS["bg"]}" stroke="{COLORS["border"]}" stroke-width="2" />'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_center}" '
        f'fill="{COLORS["bg"]}" stroke="{COLORS["border"]}" stroke-width="1" />'
    )

    # 12 宫扇形 + 文本
    for i, p in enumerate(sorted_pcs[:12]):
        # 从 12 点钟方向开始, 顺时针
        start_angle = -90 + (i * 30)
        end_angle = start_angle + 30

        is_body = bool(p.get("is_body_palace") or p.get("is_body"))
        fill = COLORS["cell_bg_body"] if is_body else COLORS["cell_bg"]

        # 扇形
        a1 = math.radians(start_angle)
        a2 = math.radians(end_angle)
        x1_o = cx + r_outer * math.cos(a1)
        y1_o = cy + r_outer * math.sin(a1)
        x2_o = cx + r_outer * math.cos(a2)
        y2_o = cy + r_outer * math.sin(a2)
        x1_i = cx + r_inner * math.cos(a1)
        y1_i = cy + r_inner * math.sin(a1)
        x2_i = cx + r_inner * math.cos(a2)
        y2_i = cy + r_inner * math.sin(a2)

        path_d = (
            f"M {x1_o:.2f} {y1_o:.2f} "
            f"A {r_outer} {r_outer} 0 0 1 {x2_o:.2f} {y2_o:.2f} "
            f"L {x2_i:.2f} {y2_i:.2f} "
            f"A {r_inner} {r_inner} 0 0 0 {x1_i:.2f} {y1_i:.2f} Z"
        )
        parts.append(
            f'<path d="{path_d}" fill="{fill}" stroke="{COLORS["border"]}" stroke-width="1" />'
        )

        # 文本位置 (扇形中部)
        mid_angle = math.radians(start_angle + 15)
        text_r = (r_outer + r_inner) / 2
        tx = cx + text_r * math.cos(mid_angle)
        ty = cy + text_r * math.sin(mid_angle)

        # 宫名 (外环)
        outer_r = r_outer - 18
        ox = cx + outer_r * math.cos(mid_angle)
        oy = cy + outer_r * math.sin(mid_angle)
        parts.append(
            f'<text x="{ox:.2f}" y="{oy:.2f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-size="13" font-weight="bold" '
            f'fill="{COLORS["body_palace"] if is_body else COLORS["ink"]}">'
            f'{_esc(p.get("name", ""))}</text>'
        )

        # 干支
        stem_branch = f'{p.get("heavenly_stem", "")}{p.get("earthly_branch", "")}'
        sb_r = r_outer - 36
        sb_x = cx + sb_r * math.cos(mid_angle)
        sb_y = cy + sb_r * math.sin(mid_angle)
        if stem_branch:
            parts.append(
                f'<text x="{sb_x:.2f}" y="{sb_y:.2f}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="11" fill="{COLORS["adj_star"]}">'
                f'{_esc(stem_branch)}</text>'
            )

        # 主星 (扇区中部)
        major = list(p.get("major_stars") or [])
        for j, star in enumerate(major[:3]):
            star_r = (r_outer + r_inner) / 2 + (j - 1) * 14
            sx = cx + star_r * math.cos(mid_angle)
            sy = cy + star_r * math.sin(mid_angle)
            parts.append(
                f'<text x="{sx:.2f}" y="{sy:.2f}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="12" font-weight="bold" '
                f'fill="{COLORS["major_star"]}">{_esc(star)}</text>'
            )

        # 副星 (内圈附近)
        minor = list(p.get("minor_stars") or [])
        for j, star in enumerate(minor[:3]):
            m_r = r_inner + 14 + j * 11
            mx = cx + m_r * math.cos(mid_angle)
            my = cy + m_r * math.sin(mid_angle)
            parts.append(
                f'<text x="{mx:.2f}" y="{my:.2f}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="10" fill="{COLORS["minor_star"]}">'
                f'{_esc(star)}</text>'
            )

    # 中宫
    parts.append(
        f'<text x="{cx}" y="{cy - 8}" text-anchor="middle" font-size="14" '
        f'font-weight="bold" fill="{COLORS["title"]}">紫微斗数</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" font-size="11" '
        f'fill="{COLORS["adj_star"]}">12 宫轮盘</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 3. 宫位网格 (现代扁平 4×3)
# ---------------------------------------------------------------------------

def render_palace_grid(
    palaces: Sequence[Mapping[str, Any]],
    *,
    title: str = "紫微斗数 · 宫位网格",
    size: int = 720,
) -> str:
    """Render a modern flat 4×3 palace grid with detailed cards."""
    sorted_pcs = _sort_palaces(palaces)
    cell_w = size / 4
    cell_h = (size - 40) / 3

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size + 10}" width="{size}" height="{size + 10}" '
        f'class="ziwei-palace-grid">'
    )
    parts.append(f'<rect width="{size}" height="{size + 10}" fill="{COLORS["bg"]}" />')
    parts.append(
        f'<text x="{size / 2}" y="22" text-anchor="middle" '
        f'font-size="18" font-weight="bold" fill="{COLORS["title"]}">{_esc(title)}</text>'
    )

    # 卡片背景
    parts.append(
        f'<rect x="0" y="32" width="{size}" height="{size - 32}" '
        f'fill="{COLORS["cell_bg"]}" stroke="{COLORS["border"]}" stroke-width="2" />'
    )

    for i, p in enumerate(sorted_pcs[:12]):
        row = i // 4
        col = i % 4
        x = col * cell_w
        y = 32 + row * cell_h

        is_body = bool(p.get("is_body_palace") or p.get("is_body"))
        is_orig = bool(p.get("is_original_palace"))
        fill = COLORS["cell_bg_body"] if is_body else COLORS["cell_bg"]

        # 卡片
        parts.append(
            f'<rect x="{x + 4}" y="{y + 4}" width="{cell_w - 8}" height="{cell_h - 8}" '
            f'rx="6" ry="6" fill="{fill}" stroke="{COLORS["border"]}" stroke-width="1" />'
        )

        # 卡片头部 (宫名 + 干支)
        accent = ""
        if is_body:
            accent = " ●"
        elif is_orig:
            accent = " ☆"
        parts.append(
            f'<rect x="{x + 4}" y="{y + 4}" width="{cell_w - 8}" height="28" '
            f'rx="6" ry="6" fill="{COLORS["bg"]}" stroke="none" />'
        )
        parts.append(
            f'<text x="{x + 14}" y="{y + 24}" font-size="14" font-weight="bold" '
            f'fill="{COLORS["body_palace"] if is_body else COLORS["ink"]}">'
            f'{_esc(p.get("name", ""))}{accent}</text>'
        )
        stem_branch = f'{p.get("heavenly_stem", "")}{p.get("earthly_branch", "")}'
        if stem_branch:
            parts.append(
                f'<text x="{x + cell_w - 14}" y="{y + 24}" text-anchor="end" '
                f'font-size="12" fill="{COLORS["adj_star"]}">{_esc(stem_branch)}</text>'
            )

        # 星曜列表
        body_y = y + 38
        major = list(p.get("major_stars") or [])
        minor = list(p.get("minor_stars") or [])
        adj = list(p.get("adjective_stars") or [])

        for star in major[:3]:
            parts.append(
                f'<text x="{x + 14}" y="{body_y}" font-size="13" font-weight="bold" '
                f'fill="{COLORS["major_star"]}">★ {_esc(star)}</text>'
            )
            body_y += 18

        for star in minor[:3]:
            parts.append(
                f'<text x="{x + 14}" y="{body_y}" font-size="11" '
                f'fill="{COLORS["minor_star"]}">· {_esc(star)}</text>'
            )
            body_y += 15

        for star in adj[:2]:
            parts.append(
                f'<text x="{x + 14}" y="{body_y}" font-size="10" '
                f'fill="{COLORS["adj_star"]}">· {_esc(star)}</text>'
            )
            body_y += 13

        # 12 神杀 (底部)
        c12 = p.get("changsheng12") or ""
        if c12:
            parts.append(
                f'<text x="{x + 14}" y="{y + cell_h - 14}" font-size="10" '
                f'fill="{COLORS["adj_star"]}">{_esc(c12)}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 4. 星曜地图 (scatter 散点)
# ---------------------------------------------------------------------------

def render_star_map(
    palaces: Sequence[Mapping[str, Any]],
    *,
    title: str = "紫微斗数 · 星曜地图",
    size: int = 720,
) -> str:
    """Render all stars as scatter points on a circular star map.

    紫微星系 (major) -> 内圈
    天府星系 -> 外圈
    其他星曜 -> 中圈散点
    """
    sorted_pcs = _sort_palaces(palaces)
    cx = size / 2
    cy = (size + 40) / 2
    r_inner = size * 0.18
    r_outer = size * 0.40
    r_mid = (r_inner + r_outer) / 2

    # 14 主星分组
    ZIWEI_SYSTEM = {
        "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
        "天府", "太阴", "贪狼", "巨门", "天相", "天梁",
        "七杀", "破军",
    }

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size + 40}" width="{size}" height="{size + 40}" '
        f'class="ziwei-star-map">'
    )
    parts.append(f'<rect width="{size}" height="{size + 40}" fill="{COLORS["bg"]}" />')
    parts.append(
        f'<text x="{cx}" y="22" text-anchor="middle" '
        f'font-size="18" font-weight="bold" fill="{COLORS["title"]}">{_esc(title)}</text>'
    )

    # 三圈背景
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" '
        f'fill="none" stroke="{COLORS["border"]}" stroke-width="2" />'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" '
        f'fill="none" stroke="{COLORS["border"]}" stroke-width="1.5" />'
    )

    # 12 宫位锚点 (12 方向)
    anchor_radius = (r_outer + size * 0.46) / 2
    for i in range(12):
        angle = math.radians(-90 + i * 30)
        ax = cx + anchor_radius * math.cos(angle)
        ay = cy + anchor_radius * math.sin(angle)
        p = sorted_pcs[i] if i < len(sorted_pcs) else {}
        parts.append(
            f'<circle cx="{ax:.2f}" cy="{ay:.2f}" r="3" '
            f'fill="{COLORS["adj_star"]}" />'
        )
        parts.append(
            f'<text x="{ax:.2f}" y="{ay - 10:.2f}" text-anchor="middle" '
            f'font-size="11" fill="{COLORS["title"]}">{_esc(p.get("name", ""))}</text>'
        )

    # 收集所有主星 + 副星, 按系统定位
    ziwei_stars: list[tuple[str, int]] = []   # (star_name, palace_idx)
    tianfu_stars: list[tuple[str, int]] = []
    other_majors: list[tuple[str, int]] = []
    minor_stars: list[tuple[str, int]] = []

    for i, p in enumerate(sorted_pcs[:12]):
        for s in p.get("major_stars") or []:
            if s in ZIWEI_SYSTEM:
                # 紫微 / 天府 分系
                if s in ("紫微", "天机", "太阳", "武曲", "天同", "廉贞"):
                    ziwei_stars.append((s, i))
                elif s in ("天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"):
                    tianfu_stars.append((s, i))
                else:
                    other_majors.append((s, i))
            else:
                other_majors.append((s, i))
        for s in p.get("minor_stars") or []:
            minor_stars.append((s, i))

    def _place_stars(
        star_list: list[tuple[str, int]],
        base_r: float,
        color: str,
        radius: float = 4.0,
    ) -> None:
        if not star_list:
            return
        # 在 12 宫方向上分布
        for idx, (star, p_idx) in enumerate(star_list):
            base_angle = -90 + p_idx * 30
            spread = 14.0 if len(star_list) > 12 else 20.0
            offset = ((idx % 3) - 1) * spread
            angle = math.radians(base_angle + offset)
            jitter_r = base_r + ((idx % 2) - 0.5) * 16
            sx = cx + jitter_r * math.cos(angle)
            sy = cy + jitter_r * math.sin(angle)
            parts.append(
                f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="{radius}" '
                f'fill="{color}" stroke="{COLORS["border"]}" stroke-width="0.5" />'
            )
            # 星名 (下方)
            parts.append(
                f'<text x="{sx:.2f}" y="{sy + radius + 11:.2f}" text-anchor="middle" '
                f'font-size="9" fill="{COLORS["ink"]}">{_esc(star)}</text>'
            )

    # 紫微系 -> 内圈 (核心)
    _place_stars(ziwei_stars, r_inner + 20, COLORS["major_star"], radius=5.0)
    # 天府系 -> 外圈
    _place_stars(tianfu_stars, r_outer - 24, COLORS["major_star"], radius=5.0)
    # 其他主星 -> 中圈
    _place_stars(other_majors, r_mid, COLORS["adj_star"], radius=4.0)
    # 副星 -> 散布
    _place_stars(minor_stars, r_mid - 30, COLORS["minor_star"], radius=3.0)

    # 中宫
    parts.append(
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="13" '
        f'font-weight="bold" fill="{COLORS["title"]}">星曜地图</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" font-size="10" '
        f'fill="{COLORS["adj_star"]}">紫微 / 天府 双系</text>'
    )

    # 图例
    legend_y = size + 10
    parts.append(
        f'<circle cx="20" cy="{legend_y}" r="4" fill="{COLORS["major_star"]}" />'
    )
    parts.append(
        f'<text x="30" y="{legend_y + 4}" font-size="11" fill="{COLORS["ink"]}">主星</text>'
    )
    parts.append(
        f'<circle cx="80" cy="{legend_y}" r="3" fill="{COLORS["minor_star"]}" />'
    )
    parts.append(
        f'<text x="90" y="{legend_y + 4}" font-size="11" fill="{COLORS["ink"]}">辅星</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 顶层入口 (4 种一键渲染)
# ---------------------------------------------------------------------------

STYLES = ("traditional", "wheel", "grid", "star_map")


def wrap_html(
    svg: str,
    *,
    css_class: str = "ziwei-chart",
    background: str | None = None,
) -> str:
    """Wrap a single SVG string in an HTML container div for embedding.

    Provides optional CSS class hook and background color override.
    """
    style_parts = []
    if background:
        style_parts.append(f"background:{background}")
    style_attr = f' style="{";".join(style_parts)}"' if style_parts else ""
    return f'<div class="{css_class}"{style_attr}>{svg}</div>'


def render_all(
    palaces: Sequence[Mapping[str, Any]],
    *,
    title_prefix: str = "紫微斗数",
    size: int = 720,
) -> dict[str, str]:
    """Render all 4 SVG styles. Returns dict {style_name: svg_string}."""
    return {
        "traditional": render_traditional_square(
            palaces, title=f"{title_prefix} · 传统方盘", size=size
        ),
        "wheel": render_modern_wheel(
            palaces, title=f"{title_prefix} · 现代轮盘", size=size
        ),
        "grid": render_palace_grid(
            palaces, title=f"{title_prefix} · 宫位网格", size=size
        ),
        "star_map": render_star_map(
            palaces, title=f"{title_prefix} · 星曜地图", size=size
        ),
    }


# ---------------------------------------------------------------------------
# 高层入口 (兼容 Sprint 任务规范)
# ---------------------------------------------------------------------------
#
# 任务要求签名: render_xxx(palaces, soul, body, five_elements) -> str
# 与上面的 (palaces, *, title, size) 略有不同. 这里追加 4 个高层包装
# 函数, 保持向后兼容; 它们把 soul/body/five_elements 注入到 SVG 中央.

_CENTER_INFO_BLOCK = (
    '<g class="zw-center-info">'
    '<text x="{cx}" y="{cy1}" text-anchor="middle" font-size="13" '
    'fill="{five_color}" font-weight="bold">{five_label}</text>'
    '<text x="{cx}" y="{cy2}" text-anchor="middle" font-size="12" '
    'fill="{soul_color}">命主 {soul}</text>'
    '<text x="{cx}" y="{cy3}" text-anchor="middle" font-size="12" '
    'fill="{body_color}">身主 {body}</text>'
    '</g>'
)


def _inject_center(svg: str, soul: str, body: str, five_elements: str,
                   *, cx: float, cy: float, dy: float = 18,
                   five_color: str = COLORS["adj_star"],
                   soul_color: str = COLORS["body_palace"],
                   body_color: str = COLORS["major_star"]) -> str:
    """在 SVG ``</svg>`` 前注入命主/身主/五行局 文本.

    通过字符串注入避免修改原 4 个渲染函数.
    """
    if not (soul or body or five_elements):
        return svg
    five_label = f"{five_elements}局" if five_elements else ""
    block = _CENTER_INFO_BLOCK.format(
        cx=cx, cy1=cy - dy, cy2=cy, cy3=cy + dy,
        five_color=five_color, soul_color=soul_color, body_color=body_color,
        five_label=_esc(five_label), soul=_esc(soul), body=_esc(body),
    )
    return svg.replace("</svg>", f"{block}</svg>", 1)


def _has_text(svg: str, needle: str) -> bool:
    """检查 SVG 中是否包含某文本 (XML 转义后比较)."""
    return _esc(needle) in svg or needle in svg


# --- 4 个高层包装函数 (任务规范签名) ---------------------------------

def render_traditional_square_simple(
    palaces: Sequence[Mapping[str, Any]],
    soul: str = "",
    body: str = "",
    five_elements: str = "",
    *,
    title: str = "紫微斗数 · 传统方盘",
    size: int = 720,
) -> str:
    """任务规范签名: (palaces, soul, body, five_elements) -> str.

    渲染传统方盘, 在中央 2×2 中宫注入命主/身主/五行局.
    """
    svg = render_traditional_square(palaces, title=title, size=size)
    # 中宫中心: 4×4 网格, 中宫中心 = (size/2, 30 + size*2/4)
    cx = size / 2
    cy = 30 + size / 2  # 30 标题 + 2 cell
    return _inject_center(svg, soul, body, five_elements,
                          cx=cx, cy=cy, dy=18)


def render_modern_wheel_simple(
    palaces: Sequence[Mapping[str, Any]],
    soul: str = "",
    body: str = "",
    five_elements: str = "",
    *,
    title: str = "紫微斗数 · 现代轮盘",
    size: int = 720,
) -> str:
    """任务规范签名: (palaces, soul, body, five_elements) -> str.

    渲染现代轮盘, 在中心圆注入命主/身主/五行局.
    """
    svg = render_modern_wheel(palaces, title=title, size=size)
    cx = size / 2
    cy = (size + 40) / 2
    return _inject_center(svg, soul, body, five_elements,
                          cx=cx, cy=cy, dy=14,
                          five_color=COLORS["adj_star"],
                          soul_color=COLORS["body_palace"],
                          body_color=COLORS["major_star"])


def render_palace_grid_simple(
    palaces: Sequence[Mapping[str, Any]],
    soul: str = "",
    body: str = "",
    five_elements: str = "",
    *,
    title: str = "紫微斗数 · 宫位网格",
    size: int = 720,
) -> str:
    """任务规范签名: (palaces, soul, body, five_elements) -> str.

    渲染宫位网格, 在中央 2×2 信息区注入命主/身主/五行局.
    """
    svg = render_palace_grid(palaces, title=title, size=size)
    cx = size / 2
    cy = 32 + (size - 32) / 2
    return _inject_center(svg, soul, body, five_elements,
                          cx=cx, cy=cy, dy=18)


def render_star_map_simple(
    palaces: Sequence[Mapping[str, Any]],
    soul: str = "",
    body: str = "",
    five_elements: str = "",
    *,
    title: str = "紫微斗数 · 星曜地图",
    size: int = 720,
) -> str:
    """任务规范签名: (palaces, soul, body, five_elements) -> str.

    渲染星曜地图, 在中心点注入命主/身主/五行局.
    """
    svg = render_star_map(palaces, title=title, size=size)
    cx = size / 2
    cy = (size + 40) / 2 + 22  # 中宫下方留 22px 间距
    return _inject_center(svg, soul, body, five_elements,
                          cx=cx, cy=cy, dy=14)