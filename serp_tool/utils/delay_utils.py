import asyncio
from typing import Optional

from config import config as app_config


async def async_delay(default_ms: int = 1000) -> None:
    try:
        delay_s = max(0, float(app_config.behavior_settings.get("delay_ms", default_ms)) / 1000.0)
    except Exception:
        delay_s = default_ms / 1000.0
    await asyncio.sleep(delay_s)


