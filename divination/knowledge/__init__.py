"""Knowledge distillation module for profession-specific divination optimization.

Provides:
- Profession profiles mapped to Bazi/divination patterns
- Domain-specific interpretation rules (wealth, health, relationships)
- Classical text rule extraction from reference materials
- Curated classical book catalog per method (18 methods, 60+ books)

Usage:
    from divination.knowledge import match_professions, get_domain_rules

    fits = match_professions(chart)  # returns [{profession, score, advice}, ...]
    rules = get_domain_rules("wealth")  # returns structured rules
    books = get_books_for_method("bazi", max_priority=2)
"""

from .books import (
    BOOK_CATALOG,
    METHOD_LABELS_CN,
    get_all_books,
    get_books_for_method,
    get_books_with_verification,
    get_method_labels,
    get_method_summary,
)
from .classical import extract_rules_for_chart, get_classical_rules
from .domains import DOMAIN_RULES, get_domain_rules
from .fate_modification import generate_plan as generate_fate_modification_plan
from .professions import PROFESSIONS, get_profession_advice, match_professions
from .relationship_timing import (
    compute_compatibility,
    compute_peach_blossom_index,
    compute_relationship_timing,
)

__all__ = [
    "BOOK_CATALOG",
    "DOMAIN_RULES",
    "METHOD_LABELS_CN",
    "PROFESSIONS",
    "compute_compatibility",
    "compute_peach_blossom_index",
    "compute_relationship_timing",
    "extract_rules_for_chart",
    "generate_fate_modification_plan",
    "get_all_books",
    "get_books_for_method",
    "get_books_with_verification",
    "get_classical_rules",
    "get_domain_rules",
    "get_method_labels",
    "get_method_summary",
    "get_profession_advice",
    "match_professions",
]
