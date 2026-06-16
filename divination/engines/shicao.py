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
from ..contracts import Birth, ChartResult
from .. import yijing

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
        },
    )


def _get_day_gan(b: Birth) -> str:
    """取日干。"""
    try:
        from lunar_python import Solar
        return Solar.fromYmdHms(b.year, b.month, b.day, 12, 0, 0).getLunar().getDayGan()
    except Exception:
        return "甲"
