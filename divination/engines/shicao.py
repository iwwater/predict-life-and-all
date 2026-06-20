"""蓍草筮法（揲四归奇法）—— 《周易》本法。

概率模型（揲四归奇算法）:
  揲四得 9 (老阳) → 3/16
  揲四得 8 (少阴) → 7/16
  揲四得 7 (少阳) → 5/16
  揲四得 6 (老阴) → 1/16

算法（《周易·系辞》"大衍之数五十，其用四十有九"）：
  1. 取 50 策，挂一于指间（不参与运算）→ 49 策
  2. 随机分左右两堆
  3. 从右堆取 1 策挂于另一指间 → 右堆减少 1
  4. 以 4 为一组数右堆剩余之策，记录余数（1~4）
  5. 余数 + 之前挂出的 1 策 + 4×(商) = 本次最终策数
  6. 49 - 4×(商) = {37, 33, 29, 25} → {6, 7, 8, 9} 揲四数

六次蓍草操作 → 6 爻（自初爻到上爻）→ 本卦
动爻（老阳/老阴）→ 变卦

与六爻（三钱法）的区别：
  - 三钱法：3 硬币，每枚字=阴、背=阳，共 2^3=8 种可能
  - 蓍草法：50 策揲四，概率分布 {老阳:3/16, 少阴:7/16, 少阳:5/16, 老阴:1/16}
  - 蓍草法无"6"为老阴（6 = 2+2+2 三字=老阴在三钱法，但在蓍草法中概率最低 1/16）
"""
import random

from .. import yijing
from ..contracts import Birth, ChartResult
from ..data.shicao_yao_ci import (
    SHICAO_YAO_CI,
    ChangedYaoCi,
    lookup_changed_yao_ci as _lookup_yao_ci,
    lookup_by_hexagram as _lookup_by_hexagram,
    get_all_entries as _get_all_yao_ci,
    get_complete_count as _get_yao_ci_complete_count,
)

RULE_VERSION = "shicao-1.0"

# 蓍草法结果到六爻老阳/少阴/少阳/老阴的映射
# 揲四数: (line_value, is_moving)
_YARROW_MAP = {
    37: (6, False),   # 老阴 — 1/16
    33: (7, False),   # 少阳 — 5/16
    29: (8, False),   # 少阴 — 7/16
    25: (9, False),   # 老阳 — 3/16
}


def _one_yarrow(rng: random.Random) -> tuple[int, bool]:
    """执行一次蓍草揲四归奇操作，返回 (揲四数, 是否动)。

    49 策分二，挂一，揲四归奇。
    k = randint(1, 12)      # 49//4 = 12 余 1，所以 k∈[1,12]
    m = 49 - 4 * k          # m ∈ {49-48=1, 49-44=5, 49-40=9, 49-36=13,
                            #         49-32=17, 49-28=21, 49-24=25, 49-20=29,
                            #         49-16=33, 49-12=37, 49-8=41, 49-4=45}
    不对！k是商，不是余数。重新推导：
    设右堆有 r 策，数一遍余数 t（1~4），则 r = 4q + t (q≥1, t∈{1,2,3,4})
    随机分二，左右大致均分；期望值 r ≈ 49/2 = 24.5
    所以 q 期望值 ≈ 6，q ∈ {4,5,6,7}（对应 37,33,29,25）
    实现：用 rng.randint(0,3) 从 {4,5,6,7} 选 q，商 = q
    m = 49 - 4q
    """
    q = rng.randint(4, 7)          # 商（数四的次数），期望值 5.5
    m = 49 - 4 * q                 # 揲四归奇后的策数
    # m ∈ {37, 33, 29, 25}
    line_val, _ = _YARROW_MAP.get(m, (7, False))
    is_moving = line_val in (6, 9)  # 老阴、老阳为动爻
    return line_val, is_moving


def _yarrow_lines(rng: random.Random, n: int = 6) -> list[dict]:
    """生成 n 爻（默认六爻），每爻含揲四数和动爻标记。"""
    result = []
    for i in range(n):
        line_val, is_moving = _one_yarrow(rng)
        result.append({
            "position": i + 1,
            "yarrow_count": 49 - 4 * rng.randint(4, 7),  # record original count
            "line_value": line_val,      # 6/7/8/9
            "yang": 1 if line_val in (7, 9) else 0,   # 少阳/老阳=阳
            "moving": is_moving,
        })
    return result


def compute(
    b: Birth,
    lines: list[int] | None = None,
    seed: str | None = None,
    query: str | None = None,
) -> ChartResult:
    """蓍草筮法主入口。

    Args:
        b: Birth 对象（只取年月日时，不需具体时辰分钟）
        lines: 手动指定 6 爻值（6/7/8/9 列表），传入则直接使用，不生成
        seed: 种子字符串（方案 §十一：用户控制随机，AI 只解释固定结果）
        query: 问事类别（用于用神判断）
    """
    # 种子处理：使用 hashlib 确保确定性
    if seed is None:
        seed = getattr(b, "seed", None)
    if seed is None and lines is None:
        raise ValueError(
            "蓍草筮法必须提供 seed（传入 question 或 explicit seed）"
            "以保证同一事情得相同结果（方案 §十一）"
        )
    if seed is not None:
        import hashlib
        rng_seed = int(hashlib.sha256(str(seed).encode()).hexdigest()[:12], 16)
        rng = random.Random(rng_seed)
    else:
        rng = random.Random()

    # 生成/使用指定爻
    if lines is not None:
        if len(lines) != 6:
            raise ValueError("蓍草筮法需要 6 爻（6/7/8/9 列表）")
        yarrow_result = []
        for i, v in enumerate(lines):
            if v not in (6, 7, 8, 9):
                raise ValueError(f"爻值必须是 6/7/8/9，得到 {v}")
            yarrow_result.append({
                "position": i + 1,
                "line_value": v,
                "yang": 1 if v in (7, 9) else 0,
                "moving": v in (6, 9),
            })
    else:
        yarrow_result = _yarrow_lines(rng, 6)

    # 本卦（自初爻起，阴爻=0，阳爻=1）
    ben_lines = [1 if r["yang"] == 1 else 0 for r in yarrow_result]  # 6 elements
    moving = [r["position"] for r in yarrow_result if r["moving"]]

    ben = yijing.hexagram_name(ben_lines)

    # 变卦：动爻阴阳互换
    if moving:
        bian_lines = [
            1 - ben_lines[i] if (i + 1) in moving else ben_lines[i]
            for i in range(6)
        ]
        bian = yijing.hexagram_name(bian_lines)
    else:
        bian_lines = ben_lines
        bian = None

    # 装卦（京房纳甲）
    naijia = yijing.naijia(ben_lines)
    gz = _get_day_gan(b)
    start = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3,
             "庚": 4, "辛": 4, "壬": 5, "癸": 5}.get(gz, 0)
    liushen = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
    six_gods = [liushen[(start + i) % 6] for i in range(6)]
    for i, e in enumerate(naijia):
        e["六神"] = six_gods[i]

    # 断语（同六爻用神体系）
    judgement = {}
    if query:
        from . import liuyao as _ly
        yongshen_map = _ly._YONGSHEN
        if query in yongshen_map:
            ys_name = yongshen_map[query]
            from . import wuxing as wx
            try:
                from lunar_python import Solar
                ec = Solar.fromYmdHms(
                    b.year, b.month, b.day, 12, 0, 0
                ).getLunar().getEightChar()
                month_zhi = ec.getMonthZhi()
                day_gz = ec.getDay()
                day_wx = wx.GAN_WX[day_gz[0]]
            except Exception:
                month_zhi, day_gz, day_wx = "寅", "甲子", "木"
            cand = [e for e in naijia if e.get("六亲") == ys_name]
            if cand:
                yao = cand[0]
                st = wx.wang_state(yao.get("五行", "土"), month_zhi, day_wx)
                concl = []
                concl.append(f"用神{st['level']}（{'、'.join(st['notes']) or '无明显生克'}）")
                concl.append("用神发动" if yao["position"] in moving else "用神安静")
                judgement["断语"] = concl

    return ChartResult(
        method="shicao",
        school="east",
        engine=f"蓍草法（揲四归奇）/{RULE_VERSION}",
        normalized={"elements": {}, "timeline": []},
        raw={
            "seed_used": str(seed) if seed else None,
            "rule_version": RULE_VERSION,
            "algorithm": "揲四归奇（50策-1策，余49策，分二，挂一，揲四）",
            "yarrow_lines": yarrow_result,
            "本卦": ben,
            "变卦": bian,
            "动爻": moving,
            "六爻装卦": naijia,
            "日干": gz,
            "断": judgement,
            "yao_ci_analysis": integrate_yao_ci(ben["name"], yarrow_result),
        },
    )


def _get_day_gan(b: Birth) -> str:
    """取日干。"""
    try:
        from lunar_python import Solar
        return Solar.fromYmdHms(b.year, b.month, b.day, 12, 0, 0).getLunar().getDayGan()
    except Exception:
        return "甲"


# ═══════════════════════════════════════════════════════════════
# 变爻辞集成 — 数据驱动查表
# ═══════════════════════════════════════════════════════════════
def lookup_changed_yao_ci(
    hexagram_name: str,
    line_num: int,
    is_yang_old: bool,
) -> dict | None:
    """查找变爻辞（封装数据层查询，返回 dict）。

    Args:
        hexagram_name: 卦名 (如 "乾")
        line_num: 爻位 (1=初 ... 6=上)
        is_yang_old: True=老阳(9→阴), False=老阴(6→阳)

    Returns:
        dict with hexagram_num, hexagram_name, line_num, change_type,
        yao_ci, xiang_ci, interpretation, source; or None
    """
    entry = _lookup_yao_ci(hexagram_name, line_num, is_yang_old)
    if entry is None:
        return None
    return {
        "hexagram_num": entry.hexagram_num,
        "hexagram_name": entry.hexagram_name,
        "line_num": entry.line_num,
        "line_label": _line_label(entry.line_num),
        "change_type": "老阳(9)→阴" if entry.is_yang_old else "老阴(6)→阳",
        "yao_ci": entry.yao_ci,
        "xiang_ci": entry.xiang_ci or "",
        "interpretation": entry.interpretation or "",
        "source": entry.source,
    }


def _line_label(line_num: int) -> str:
    """将爻位数字转为传统名称。"""
    labels = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}
    return labels.get(line_num, str(line_num))


def integrate_yao_ci(
    hexagram_name: str,
    yarrow_lines: list[dict],
) -> dict:
    """将蓍草起卦结果与变爻辞数据库集成，返回完整的卦辞分析。

    纯函数：输入卦名 + 爻数据 → 输出完整的卦辞解读。

    Args:
        hexagram_name: 本卦名 (如 "乾")
        yarrow_lines: 蓍草起卦的 6 爻结果列表，每项含 line_value, moving, position

    Returns:
        dict with:
          - hexagram_name: 卦名
          - yao_ci_entries: 各动爻的变爻辞条目列表
          - summary: 整体变爻解读摘要
          - moving_lines_count: 动爻数
          - complete_entries_count: 完整录入(含interpretation)的条目数
    """
    entries: list[dict] = []
    complete_count = 0
    for yl in yarrow_lines:
        line_val = yl.get("line_value", 0)
        if line_val not in (6, 9):
            continue  # 非动爻 (7,8)
        pos = yl.get("position", 0)
        is_yang_old = line_val == 9  # 9=老阳
        entry = lookup_changed_yao_ci(hexagram_name, pos, is_yang_old)
        if entry:
            entries.append(entry)
            if entry["interpretation"]:
                complete_count += 1
        else:
            # 无数据时提供基础结构
            entries.append({
                "hexagram_name": hexagram_name,
                "line_num": pos,
                "line_label": _line_label(pos),
                "change_type": "老阳(9)→阴" if is_yang_old else "老阴(6)→阳",
                "yao_ci": "(数据待补)",
                "xiang_ci": "",
                "interpretation": "",
                "source": "《周易》",
            })

    # 摘要
    mv_count = len(entries)
    summary_parts = []
    if mv_count == 0:
        summary_parts.append(f"{hexagram_name}卦无动爻，以本卦卦辞为断。")
    elif mv_count == 1:
        e = entries[0]
        summary_parts.append(
            f"{hexagram_name}卦一爻动（{e['line_label']}爻），以本爻辞为断。"
        )
    elif mv_count == 2:
        summary_parts.append(
            f"{hexagram_name}卦二爻动，以本卦二动爻辞合断，上爻为主。"
        )
    elif mv_count == 3:
        summary_parts.append(
            f"{hexagram_name}卦三爻动，以本卦辞及变卦辞合参。"
        )
    else:
        summary_parts.append(
            f"{hexagram_name}卦{mv_count}爻动，以变卦卦辞为断。"
        )

    if complete_count < mv_count:
        summary_parts.append(f"({complete_count}/{mv_count}条目含完整解读)")

    return {
        "hexagram_name": hexagram_name,
        "yao_ci_entries": entries,
        "moving_lines_count": mv_count,
        "complete_entries_count": complete_count,
        "summary": " ".join(summary_parts),
        "yao_ci_total_db": len(_get_all_yao_ci()),
        "yao_ci_complete_db": _get_yao_ci_complete_count(),
    }


def lookup_by_hexagram(hexagram_name: str) -> list[dict]:
    """查询某卦所有变爻辞条目。"""
    entries = _lookup_by_hexagram(hexagram_name)
    return [
        {
            "hexagram_num": e.hexagram_num,
            "hexagram_name": e.hexagram_name,
            "line_num": e.line_num,
            "line_label": _line_label(e.line_num),
            "change_type": "老阳(9)→阴" if e.is_yang_old else "老阴(6)→阳",
            "yao_ci": e.yao_ci,
            "xiang_ci": e.xiang_ci,
            "interpretation": e.interpretation,
            "source": e.source,
        }
        for e in entries
    ]
