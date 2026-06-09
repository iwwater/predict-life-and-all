"""divination:中西方统一算命引擎(B 路 / 纯 MIT)。

一个接口,中西通吃。东方用成熟开源库,西方走 skyfield + 自算星座/相位/宫位,
全程 MIT/BSD,零 AGPL,可闭源商用。
"""
from .contracts import Birth, ChartResult, School, Method
from . import astro_math
from .router import compute, compute_all, supported_methods

__version__ = "0.1.0"
__all__ = [
    "Birth", "ChartResult", "School", "Method",
    "compute", "compute_all", "supported_methods",
    "astro_math",
]
