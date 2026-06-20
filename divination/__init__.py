from .contracts import Birth, ChartResult
from .router import _ENGINES, compute, compute_all


def supported_methods():
    """Return the list of supported method IDs."""
    return list(_ENGINES.keys())
