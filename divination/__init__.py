from .contracts import Birth, ChartResult
from .router import compute, compute_all, _ENGINES

def supported_methods():
    """Return the list of supported method IDs."""
    return list(_ENGINES.keys())

