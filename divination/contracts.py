"""统一数据契约：中西方所有术数共用这一套请求/结果结构。"""
from dataclasses import dataclass, field, asdict
from typing import Any, Literal, Optional

School = Literal["east", "west"]
Method = Literal[
    "bazi", "ziwei", "qimen", "liuyao", "meihua", "chenggu", "bazhai", "xuankong",
    "hepan", "western", "vedic", "tarot", "numerology", "lenormand", "liuren",
    "tieban", "xiaoliuren",
]


@dataclass
class Birth:
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: Literal["male", "female", "unspecified"] = "unspecified"
    calendar: Literal["gregorian", "lunar"] = "gregorian"
    lat: Optional[float] = None      # 纬度，西方排盘/真太阳时需要
    lng: Optional[float] = None      # 经度
    tz: str = "Asia/Shanghai"
    is_leap_month: bool = False      # 农历闰月


@dataclass
class ChartResult:
    method: Method
    school: School
    engine: str                       # 实际用的库名+版本
    normalized: dict[str, Any] = field(default_factory=dict)  # 跨法通用：五行/四元素强弱 + 时间轴
    raw: dict[str, Any] = field(default_factory=dict)         # 各法专属细节

    def to_dict(self) -> dict:
        return asdict(self)
