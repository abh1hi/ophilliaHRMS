from fastapi.responses import JSONResponse
from typing import Any


def ok(data: Any, meta: Any = None) -> JSONResponse:
    """Wrap a success payload in the standard API envelope."""
    return JSONResponse({"success": True, "data": data, "meta": meta, "error": None})
