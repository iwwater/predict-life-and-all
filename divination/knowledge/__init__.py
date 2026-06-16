"""Knowledge distillation module for profession-specific divination optimization.

Provides:
- Profession profiles mapped to Bazi/divination patterns
- Domain-specific interpretation rules (wealth, health, relationships)
- Classical text rule extraction from reference materials

Usage:
    from divination.knowledge import match_professions, get_domain_rules

    fits = match_professions(chart)  # returns [{profession, score, advice}, ...]
    rules = get_domain_rules("wealth")  # returns structured rules
"""

from .professions import PROFESSIONS, match_professions, get_profession_advice
from .domains import get_domain_rules, DOMAIN_RULES
from .classical import get_classical_rules, extract_rules_for_chart
from .books import BOOK_CATALOG, get_books_for_method, get_all_books
from .fate_modification import generate_plan as generate_fate_modification_plan
from .relationship_timing import (
    compute_peach_blossom_index,
    compute_relationship_timing,
    compute_compatibility,
)

__all__ = [
    "PROFESSIONS",
    "match_professions",
    "get_profession_advice",
    "get_domain_rules",
    "DOMAIN_RULES",
    "get_classical_rules",
    "extract_rules_for_chart",
    "BOOK_CATALOG",
    "get_books_for_method",
    "get_all_books",
    "generate_fate_modification_plan",
    "compute_peach_blossom_index",
    "compute_relationship_timing",
    "compute_compatibility",
]
