"""GET /api/methods - list methods with subjects, modes, and required inputs."""
from fastapi import APIRouter

from divination import supported_methods
from divination.meta import METHOD_META

router = APIRouter()


@router.get("/methods")
def list_methods():
    return [
        {"id": method, **METHOD_META[method]}
        for method in supported_methods()
    ]
