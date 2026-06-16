"""Divination engines package — one module per school.

Engines registered here are wired into ``divination.router._ENGINES``.
"""
from . import (
    bazi, ziwei, qimen, liuyao, shicao, meihua, chenggu, bazhai, xuankong,
    western, vedic, tarot, numerology, hepan, liuren, lenormand,
    tieban, xiaoliuren,
)

__all__ = [
    "bazi", "ziwei", "qimen", "liuyao", "shicao", "meihua", "chenggu",
    "bazhai", "xuankong", "western", "vedic", "tarot", "numerology",
    "hepan", "liuren", "lenormand", "tieban", "xiaoliuren",
]
