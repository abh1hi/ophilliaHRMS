import httpx
from app.core.config import settings

HTTP_TIMEOUT = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=5.0)


def get_http_client(**kwargs) -> httpx.AsyncClient:
    defaults = {
        "timeout": HTTP_TIMEOUT,
        "headers": {"X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN},
    }
    defaults.update(kwargs)
    return httpx.AsyncClient(**defaults)
