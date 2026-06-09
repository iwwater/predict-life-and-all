"""占卜引擎集合:每个 engine 实现 compute(birth: Birth) -> ChartResult。"""
from . import (
    bazi, bazi_v2, ziwei, qimen, western, vedic,
    liuyao, meihua, chenggu, bazhai, xuankong, tarot, numerology,
    lenormand, liuren, tieban,
    cross_validator, hour_calibrator,
)
