"""Shared data contracts for all divination engines."""
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

School = Literal["east", "west"]
Method = Literal[
    "bazi",
    "bazi_v2",
    "ziwei",
    "qimen",
    "liuyao",
    "meihua",
    "chenggu",
    "bazhai",
    "xuankong",
    "western",
    "vedic",
    "tarot",
    "numerology",
    "lenormand",
    "liuren",
    "tieban",
    "cross_validator",
    "hour_calibrator",
    "compatibility",
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
    lat: Optional[float] = None
    lng: Optional[float] = None
    tz: str = "Asia/Shanghai"
    is_leap_month: bool = False
    mode: Optional[str] = None
    subject: Optional[str] = None
    question: Optional[str] = None
    seed: Optional[int | str] = None
    spread: Optional[str] = None
    sitting: Optional[str] = None
    period: Optional[int] = None
    construction_year: Optional[int] = None
    tosses: Optional[list[Any]] = None


@dataclass
class ChartResult:
    method: Method
    school: School
    engine: str
    normalized: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
