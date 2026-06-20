"""占卜数据: 条文数据库、查找表等静态数据.

子模块:
    tieban_verses       铁板神数条文数据库 (MVP ~100 条)
    liuren_720_lessons  大六壬 720 课框架 (课体/神煞/速查)
    wuxing_tiaohou      八字调候规则 (穷通宝鉴体系)
    wuxing_geju         八字格局动态检测 (十神组合)
"""
from . import liuren_720_lessons, tieban_verses, wuxing_geju, wuxing_tiaohou

__all__ = ["liuren_720_lessons", "tieban_verses", "wuxing_geju", "wuxing_tiaohou"]
