from functools import lru_cache

from backend.core.config import get_settings
from backend.service.platform_service import PlatformService


@lru_cache(maxsize=1)
def get_platform() -> PlatformService:
    settings = get_settings()
    return PlatformService(settings)
