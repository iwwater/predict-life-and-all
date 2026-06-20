"""占卜数据: 条文数据库、查找表等静态数据.

子模块:
    tieban_verses       铁板神数条文数据库 (MVP ~100 条)
    liuren_720_lessons  大六壬 720 课框架 (课体/神煞/速查)
"""
from . import liuren_720_lessons, tieban_verses

__all__ = ["liuren_720_lessons", "tieban_verses"]
