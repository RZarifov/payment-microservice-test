import asyncio
import logging

import httpx

from app.settings.config import settings


logger = logging.getLogger(__name__)


async def send_webhook(url: str, payload: dict) -> bool:
    delay = settings.webhook_retry_base_delay
    async with httpx.AsyncClient() as client:
        for attempt in range(1, settings.webhook_retry_attempts + 1):
            try:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                return True
            except Exception:
                logger.warning("webhook attempt %d/%d failed for %s", attempt, settings.webhook_retry_attempts, url)
                if attempt < settings.webhook_retry_attempts:
                    await asyncio.sleep(delay)
                    delay *= 2
    return False
