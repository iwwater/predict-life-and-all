"""统一数据契约：中西方所有术数共用这一套请求/结果结构。"""
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

School = Literal["east", "west"]
Method = Literal["bazi", "ziwei", "qimen", "liuyao", "meihua", "chenggu", "bazhai", "xuankong", "hepan", "western", "vedic", "tarot", "qian", "numerology"]


@dataclass
class Birth:
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: Literal["male", "female", "unspecified"] = "unspecified"
    calendar: Literal["gregorian", "lunar"] = "gregorian"
    lat: float | None = None      # 纬度，西方排盘/真太阳时需要
    lng: float | None = None      # 经度
    tz: str = "Asia/Shanghai"
    is_leap_month: bool = False      # 农历闰月
    # ── 空间维度 (风水/八宅/玄空) ──
    sitting: str | None = None       # 坐山 (24 山 e.g. "子", "卯")
    facing: str | None = None        # 朝向 (8 方位 e.g. "正南")
    construction_year: int | None = None  # 建造/起造年
    period: int | None = None        # 玄空运 (1-9)
    address: str | None = None       # 地址 (用于地理方位估算)


@dataclass
class ChartResult:
    method: Method
    school: School
    engine: str                       # 实际用的库名+版本
    normalized: dict[str, Any] = field(default_factory=dict)  # 跨法通用：五行/四元素强弱 + 时间轴
    raw: dict[str, Any] = field(default_factory=dict)         # 各法专属细节

    def to_dict(self) -> dict:
        return asdict(self)
