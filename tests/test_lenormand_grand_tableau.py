"""Tests for Lenormand Grand Tableau (divination/engines/lenormand.py)

文献：
  - Petit Lenormand 体系 (1799)
  - 法国/德国学派 Grand Tableau 传统

Test coverage: compute_grand_tableau() 宫位识别 + 邻近修饰 + 数据驱动
"""
from __future__ import annotations

import pytest

from divination.engines.lenormand import (
    LENORMAND_DECK,
    LENORMAND_BY_NAME,
    LENORMAND_BY_NUM,
    LENORMAND_NAMES,
    _GT_HOUSE_MEANINGS,
    _GT_CENTER_FOUR,
    _GT_CORNERS,
    _GT_MIND_PALACE_POSITIONS,
    _GT_FOUNDATION_PALACE_POSITIONS,
    _linear_to_row_col,
    _get_neighbors,
    _get_diagonal_neighbors,
    _get_knights,
    _combo_meaning,
    compute_grand_tableau,
)


# ── helpers ───────────────
def _make_mock_cards() -> list[dict]:
    """生成 36 张牌的 mock 列表 (按 LENORMAND_DECK 顺序)。"""
    cards = []
    for i, (num, name_en, zh, suit, core, extended, timing) in enumerate(LENORMAND_DECK):
        cards.append({
            "position": f"pos{i + 1}",
            "index": i + 1,
            "num": num,
            "name": name_en,
            "name_en": name_en,
            "name_zh": zh,
            "suit": suit,
            "core_meaning": core,
            "extended_meaning": extended,
            "timing": timing,
            "orient": "—",
        })
    return cards


def _make_custom_cards(positions: dict[int, str]) -> list[dict]:
    """生成自定义牌序。positions: {1-indexed-position: card_name_en}。

    未指定的位置用默认牌序填充。
    """
    default_cards = _make_mock_cards()
    # 交换指定位置的牌
    for pos, name in positions.items():
        # 找到该 name 的牌在默认序列中的位置
        target_idx = None
        for i, c in enumerate(default_cards):
            if c["name"] == name:
                target_idx = i
                break
        if target_idx is not None:
            # 交换
            src_idx = pos - 1
            default_cards[src_idx], default_cards[target_idx] = (
                default_cards[target_idx],
                default_cards[src_idx],
            )
    return default_cards


# ══════════════════════════════════════════════════════════════
# 1. 网格变换
# ══════════════════════════════════════════════════════════════
def test_linear_to_row_col_first():
    """位置1应映射到 (row=0, col=0)。"""
    assert _linear_to_row_col(1) == (0, 0)


def test_linear_to_row_col_last():
    """位置36应映射到 (row=3, col=8)。"""
    assert _linear_to_row_col(36) == (3, 8)


def test_linear_to_row_col_mid():
    """位置14应映射到 (row=1, col=4)。"""
    assert _linear_to_row_col(14) == (1, 4)


def test_linear_to_row_col_28():
    """位置28应映射到 (row=3, col=0)。"""
    assert _linear_to_row_col(28) == (3, 0)


# ══════════════════════════════════════════════════════════════
# 2. 邻近位置计算
# ══════════════════════════════════════════════════════════════
def test_neighbors_corner_top_left():
    """左上角(位置1)只有右和下邻。"""
    n = _get_neighbors(1)
    assert n["up"] is None
    assert n["left"] is None
    assert n["right"] == 2
    assert n["down"] == 10


def test_neighbors_center():
    """中心附近(位置14)应有四个邻。"""
    n = _get_neighbors(14)
    assert n["up"] == 5
    assert n["down"] == 23
    assert n["left"] == 13
    assert n["right"] == 15


def test_neighbors_corner_bottom_right():
    """右下角(位置36)只有左和上邻。"""
    n = _get_neighbors(36)
    assert n["down"] is None
    assert n["right"] is None
    assert n["left"] == 35
    assert n["up"] == 27


def test_diagonal_neighbors_center():
    """中心位置14应有4个对角邻。"""
    d = _get_diagonal_neighbors(14)
    assert d["ul"] == 4
    assert d["ur"] == 6
    assert d["dl"] == 22
    assert d["dr"] == 24


def test_diagonal_neighbors_corner():
    """角位置的对角邻有限。"""
    d = _get_diagonal_neighbors(1)
    assert d["ul"] is None
    assert d["ur"] is None
    assert d["dl"] is None
    assert d["dr"] == 11  # (0+1,0+1) = row1,col1 = pos12... wait: row1*9+col1+1=10+1=11


def test_knight_moves_center():
    """中心位置14应有骑士步。"""
    k = _get_knights(14)
    assert len(k) >= 1  # 在 4×9 网格中应有若干骑士步


# ══════════════════════════════════════════════════════════════
# 3. compute_grand_tableau 核心功能
# ══════════════════════════════════════════════════════════════
def test_grand_tableau_card_count():
    """Grand Tableau 必须有36张牌。"""
    cards = _make_mock_cards()
    result = compute_grand_tableau(cards)
    assert "error" not in result
    assert result["summary"]["total_cards"] == 36


def test_grand_tableau_rejects_wrong_count():
    """牌数不对应返回错误。"""
    result = compute_grand_tableau([{"name": "Rider"}] * 10)
    assert "error" in result


def test_grand_tableau_grid_shape():
    """网格应为 4 行 × 9 列。"""
    result = compute_grand_tableau(_make_mock_cards())
    assert len(result["grid"]) == 4
    assert all(len(row) == 9 for row in result["grid"])


def test_grand_tableau_center_four():
    """中心四张应为位置14,15,23,24。"""
    result = compute_grand_tableau(_make_mock_cards())
    cf = result["center_four"]
    assert cf["positions"] == [14, 15, 23, 24]
    assert len(cf["cards"]) == 4
    for c in cf["cards"]:
        assert c["name"] is not None


def test_grand_tableau_corners():
    """四角应为位置1,9,28,36。"""
    result = compute_grand_tableau(_make_mock_cards())
    assert result["corners"]["positions"] == [1, 9, 28, 36]
    assert len(result["corners"]["cards"]) == 4


def test_grand_tableau_mind_palace():
    """心智宫应含位置1-18。"""
    result = compute_grand_tableau(_make_mock_cards())
    mp = result["mind_palace"]
    assert mp["card_count"] == 18
    assert mp["positions"] == list(range(1, 19))


def test_grand_tableau_foundation_palace():
    """基础宫应含位置19-36。"""
    result = compute_grand_tableau(_make_mock_cards())
    fp = result["foundation_palace"]
    assert fp["card_count"] == 18
    assert fp["positions"] == list(range(19, 37))


def test_grand_tableau_house_meanings_coverage():
    """House meanings 应覆盖全部36个位置。"""
    assert len(_GT_HOUSE_MEANINGS) == 36
    assert set(_GT_HOUSE_MEANINGS.keys()) == set(range(1, 37))


def test_grand_tableau_cross_analysis():
    """十字轴：横轴=位置19-27，纵轴=位置5,14,23,32。"""
    result = compute_grand_tableau(_make_mock_cards())
    ca = result["cross_analysis"]
    # 横轴
    assert len(ca["horizontal_axis"]["cards"]) == 9
    assert ca["horizontal_axis"]["positions"] == list(range(19, 28))
    # 纵轴
    assert len(ca["vertical_axis"]["cards"]) == 4
    assert ca["vertical_axis"]["positions"] == [5, 14, 23, 32]


def test_grand_tableau_adjacency_all_cards():
    """每张牌都应有邻近修饰记录。"""
    result = compute_grand_tableau(_make_mock_cards())
    assert len(result["adjacency_modifiers"]) == 36


def test_grand_tableau_summary_fields():
    """Summary 应含基本字段。"""
    result = compute_grand_tableau(_make_mock_cards())
    s = result["summary"]
    assert s["layout"] == "9×4 Grand Tableau"
    assert s["total_cards"] == 36
    assert "overall_tone" in s
    assert s["overall_tone"] in ("吉", "凶", "平")
    assert "corner_overview" in s


# ══════════════════════════════════════════════════════════════
# 4. 确定性与数据驱动
# ══════════════════════════════════════════════════════════════
def test_grand_tableau_deterministic():
    """同一输入两次调用应返回相同结果（纯函数）。"""
    cards = _make_mock_cards()
    r1 = compute_grand_tableau(cards)
    r2 = compute_grand_tableau(cards)
    assert r1["grid"] == r2["grid"]
    assert r1["center_four"] == r2["center_four"]
    assert r1["summary"]["overall_tone"] == r2["summary"]["overall_tone"]


def test_grand_tableau_mansion_groups():
    """宫位分组应含完整的心智/基础/四角/中心。"""
    result = compute_grand_tableau(_make_mock_cards())
    mg = result["mansion_groups"]
    assert "心智宫" in mg
    assert "基础宫" in mg
    assert "四角" in mg
    assert "中心" in mg
    assert mg["心智宫"]["card_count"] == 18
    assert mg["基础宫"]["card_count"] == 18
    assert mg["四角"]["card_count"] == 4
    assert mg["中心"]["card_count"] == 4


def test_grand_tableau_querent_card_present():
    """如果 Man 或 Woman 牌在牌阵中，应出现在 key_positions。"""
    # 默认牌序中 Rider=pos1, Clover=pos2, ... Man=pos28, Woman=pos29
    result = compute_grand_tableau(_make_mock_cards())
    kp = result["key_positions"]
    # 默认顺序: num16=Stars(pos16), num17=Stork(pos17), num28=Man(pos28)
    assert "Man" in kp
    assert kp["Man"]["position"] == 28
    assert "Woman" in kp
    assert kp["Woman"]["position"] == 29


def test_grand_tableau_house_meanings_consistency():
    """House meanings 的 ID 与 GT 宫位定义应一致。"""
    # 心智宫 = 1-18
    mind_positions = set(_GT_MIND_PALACE_POSITIONS)
    assert mind_positions == set(range(1, 19))
    # 基础宫 = 19-36
    found_positions = set(_GT_FOUNDATION_PALACE_POSITIONS)
    assert found_positions == set(range(19, 37))
    # 四角
    assert set(_GT_CORNERS) == {1, 9, 28, 36}
    # 中心四张
    assert set(_GT_CENTER_FOUR) == {14, 15, 23, 24}


def test_grand_tableau_house_positions_all():
    """house_positions 应覆盖全部 36 个位置。"""
    result = compute_grand_tableau(_make_mock_cards())
    hp = result["house_positions"]
    assert len(hp) == 36
    for pos in range(1, 37):
        assert str(pos) in hp
        assert "meaning" in hp[str(pos)]
        assert "card_name" in hp[str(pos)]
