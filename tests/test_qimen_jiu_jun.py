"""Tests for 奇门遁甲 72 局定局 (divination/data/qimen_jiu_jun.py)

来源：docs/CLASSICAL_SOURCES.md §9 奇门遁甲
文献：《烟波钓叟歌》《奇门遁甲统宗》
"""
from __future__ import annotations

import pytest

from divination.data.qimen_jiu_jun import (
    SANYUAN_RANGES,
    SOLAR_TERM_DATES_2026,
    SOLAR_TERM_JIUJUN,
    get_dun_type,
    get_sanyuan_jun,
    get_term_jun,
    infer_term_and_sanyuan,
    list_all_jun,
    list_yang_jun,
    list_yin_jun,
)


# ── 1. 节气定局表完整性 ─────────────────────────────
def test_solar_term_count():
    """24 节气全覆盖。"""
    assert len(SOLAR_TERM_JIUJUN) == 24


def test_yang_term_count():
    """阳遁节气 = 12 (冬至 → 夏至前)。"""
    yang_terms = [t for t, v in SOLAR_TERM_JIUJUN.items() if v["dun_type"] == "阳遁"]
    assert len(yang_terms) == 12


def test_yin_term_count():
    """阴遁节气 = 12 (夏至 → 冬至前)。"""
    yin_terms = [t for t, v in SOLAR_TERM_JIUJUN.items() if v["dun_type"] == "阴遁"]
    assert len(yin_terms) == 12


def test_term_required_fields():
    """每节气必须有 dun_type, shang, zhong, xia。"""
    required = {"dun_type", "shang", "zhong", "xia"}
    for term, info in SOLAR_TERM_JIUJUN.items():
        missing = required - set(info.keys())
        assert not missing, f"{term} 缺失: {missing}"


def test_jun_number_range():
    """局数必须在 1-9 范围。"""
    for term, info in SOLAR_TERM_JIUJUN.items():
        for field in ["shang", "zhong", "xia"]:
            n = info[field]
            assert 1 <= n <= 9, f"{term}.{field}={n}"


# ── 2. 经典对标（与《烟波钓叟歌》三元定局表） ──────────
def test_classical_dongzhi_shang_yang_1():
    """冬至上元 = 阳遁 1 局（经典）。"""
    assert get_sanyuan_jun("冬至", "上元") == 1


def test_classical_dongzhi_zhong_yang_7():
    """冬至中元 = 阳遁 7 局（经典）。"""
    assert get_sanyuan_jun("冬至", "中元") == 7


def test_classical_dongzhi_xia_yang_4():
    """冬至下元 = 阳遁 4 局（经典）。"""
    assert get_sanyuan_jun("冬至", "下元") == 4


def test_classical_xiazhi_shang_yin_9():
    """夏至上元 = 阴遁 9 局（经典）。"""
    assert get_sanyuan_jun("夏至", "上元") == 9


def test_classical_xiazhi_zhong_yin_3():
    """夏至中元 = 阴遁 3 局（经典）。"""
    assert get_sanyuan_jun("夏至", "中元") == 3


def test_classical_xiazhi_xia_yin_6():
    """夏至下元 = 阴遁 6 局（经典）。"""
    assert get_sanyuan_jun("夏至", "下元") == 6


def test_classical_lichun_shang_yang_8():
    """立春上元 = 阳遁 8 局（经典）。"""
    assert get_sanyuan_jun("立春", "上元") == 8


def test_classical_chunfen_shang_yang_3():
    """春分上元 = 阳遁 3 局（经典）。"""
    assert get_sanyuan_jun("春分", "上元") == 3


def test_classical_qingming_shang_yang_4():
    """清明上元 = 阳遁 4 局（经典）。"""
    assert get_sanyuan_jun("清明", "上元") == 4


def test_classical_lixia_shang_yang_6():
    """立夏上元 = 阳遁 6 局（经典）。"""
    assert get_sanyuan_jun("立夏", "上元") == 6


def test_classical_liqiu_shang_yin_2():
    """立秋上元 = 阴遁 2 局（经典）。"""
    assert get_sanyuan_jun("立秋", "上元") == 2


def test_classical_qiufen_shang_yin_3():
    """秋分上元 = 阴遁 3 局（经典）。"""
    assert get_sanyuan_jun("秋分", "上元") == 3


def test_classical_lidong_shang_yin_6():
    """立冬上元 = 阴遁 6 局（经典）。"""
    assert get_sanyuan_jun("立冬", "上元") == 6


# ── 3. 阳遁 12 节气 / 阴遁 12 节气 ──────────────────
def test_yang_terms():
    """阳遁节气集合: 冬至/小寒/大寒/立春/雨水/惊蛰/春分/清明/谷雨/立夏/小满/芒种。"""
    expected = {"冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
                "春分", "清明", "谷雨", "立夏", "小满", "芒种"}
    actual = {t for t, v in SOLAR_TERM_JIUJUN.items() if v["dun_type"] == "阳遁"}
    assert actual == expected


def test_yin_terms():
    """阴遁节气集合。"""
    expected = {"夏至", "小暑", "大暑", "立秋", "处暑", "白露",
                "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"}
    actual = {t for t, v in SOLAR_TERM_JIUJUN.items() if v["dun_type"] == "阴遁"}
    assert actual == expected


# ── 4. 72 局枚举 ────────────────────────────────
def test_total_72_jun():
    """24 节气 × 3 元 = 72 局。"""
    assert len(list_all_jun()) == 72


def test_yang_36_jun():
    """阳遁 12 节气 × 3 元 = 36 局。"""
    assert len(list_yang_jun()) == 36


def test_yin_36_jun():
    """阴遁 12 节气 × 3 元 = 36 局。"""
    assert len(list_yin_jun()) == 36


def test_each_term_has_3_jun():
    """每节气必须恰好 3 局（上/中/下元各 1）。"""
    counts: dict[str, int] = {}
    for j in list_all_jun():
        counts[j["term"]] = counts.get(j["term"], 0) + 1
    for term, n in counts.items():
        assert n == 3, f"{term}: {n} 局"


# ── 5. 三元范围 ──────────────────────────────────
def test_sanyuan_ranges():
    """三元范围: 上元 1-5, 中元 6-10, 下元 11-15。"""
    assert SANYUAN_RANGES["上元"] == (1, 5)
    assert SANYUAN_RANGES["中元"] == (6, 10)
    assert SANYUAN_RANGES["下元"] == (11, 15)


# ── 6. 查询函数 ─────────────────────────────────
def test_get_term_jun():
    """获取节气完整定局。"""
    info = get_term_jun("冬至")
    assert info["dun_type"] == "阳遁"
    assert info["shang"] == 1
    assert info["zhong"] == 7
    assert info["xia"] == 4


def test_get_dun_type_yang():
    """阳遁节气。"""
    assert get_dun_type("冬至") == "阳遁"
    assert get_dun_type("立春") == "阳遁"


def test_get_dun_type_yin():
    """阴遁节气。"""
    assert get_dun_type("夏至") == "阴遁"
    assert get_dun_type("立秋") == "阴遁"


def test_get_dun_type_invalid():
    """非法节气 → 空字符串。"""
    assert get_dun_type("无") == ""


def test_get_sanyuan_jun_invalid_term():
    """非法节气 → 0。"""
    assert get_sanyuan_jun("无", "上元") == 0


# ── 7. 日期推算 ────────────────────────────────
def test_infer_jan_10_2026():
    """2026-01-10: 小寒后第 6 天 → 小寒中元 → 阳遁 8 局。"""
    r = infer_term_and_sanyuan(2026, 1, 10)
    assert r["term"] == "小寒"
    assert r["dun_type"] == "阳遁"
    assert r["sanyuan"] == "中元"
    assert r["jun_num"] == 8


def test_infer_jun_25_2026():
    """2026-06-25: 夏至后第 5 天 → 夏至上元 → 阴遁 9 局。"""
    r = infer_term_and_sanyuan(2026, 6, 25)
    assert r["term"] == "夏至"
    assert r["dun_type"] == "阴遁"
    assert r["sanyuan"] == "上元"
    assert r["jun_num"] == 9


def test_infer_dec_25_2026():
    """2026-12-25: 冬至后第 4 天 → 冬至上元 → 阳遁 1 局。"""
    r = infer_term_and_sanyuan(2026, 12, 25)
    assert r["term"] == "冬至"
    assert r["dun_type"] == "阳遁"
    assert r["sanyuan"] == "上元"
    assert r["jun_num"] == 1


def test_infer_result_fields():
    """返回必须含 term, dun_type, sanyuan, jun_num, days_into_term。"""
    r = infer_term_and_sanyuan(2026, 6, 25)
    for k in ["term", "dun_type", "sanyuan", "jun_num", "days_into_term"]:
        assert k in r


def test_infer_days_into_term():
    """节内天数必须 >= 1。"""
    r = infer_term_and_sanyuan(2026, 1, 10)
    assert r["days_into_term"] >= 1


# ── 8. 节气日期表完整性 ──────────────────────────
def test_term_dates_count():
    """节气日期表 = 24。"""
    assert len(SOLAR_TERM_DATES_2026) == 24


def test_term_dates_valid_months():
    """节气日期的月份应在合理范围 (1-12)。"""
    for term, (y, m, d) in SOLAR_TERM_DATES_2026.items():
        assert 1 <= m <= 12
        assert 1 <= d <= 31


# ── 9. 阴阳局分布 ──────────────────────────────
def test_jun_1_to_9_each_yang():
    """阳遁 36 局中, 1-9 局合计 = 36。"""
    from collections import Counter
    counts = Counter(j["jun_num"] for j in list_yang_jun())
    assert sum(counts.values()) == 36
    # 每局至少 3 次（不会 < 3）
    for n in range(1, 10):
        assert counts[n] >= 3, f"阳遁 {n} 局: 仅 {counts[n]} 次"
        assert counts[n] <= 5, f"阳遁 {n} 局: {counts[n]} 次, 上限 5"


def test_jun_1_to_9_each_yin():
    """阴遁 36 局中, 1-9 局合计 = 36。"""
    from collections import Counter
    counts = Counter(j["jun_num"] for j in list_yin_jun())
    assert sum(counts.values()) == 36
    for n in range(1, 10):
        assert counts[n] >= 3, f"阴遁 {n} 局: 仅 {counts[n]} 次"
        assert counts[n] <= 5, f"阴遁 {n} 局: {counts[n]} 次, 上限 5"


def test_yang_yin_mirror():
    """阳遁与阴遁的局数分布应一致（镜像）。"""
    from collections import Counter
    yang = Counter(j["jun_num"] for j in list_yang_jun())
    yin = Counter(j["jun_num"] for j in list_yin_jun())
    assert dict(yang) == dict(yin), f"阳遁与阴遁分布不一致: 阳{yang} vs 阴{yin}"
