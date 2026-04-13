import asyncio
import logging

# !NOTE: FastAPI does not have a client. Bummer.
import httpx

from app.settings.config import settings


logger = logging.getLogger(__name__)


async def send_webhook(url: str, payload: dict) -> bool:
    delay = settings.webhook_retry_base_delay
    async with httpx.AsyncClient() as client:
        for attempt in range(1, settings.webhook_retry_attempts + 1):
            try:
                response = await client.post(url, json=payload, timeout=settings.webhook_timeout)
                response.raise_for_status()
                return True
            except (httpx.HTTPError, httpx.TimeoutException):
                logger.warning(
                    f"webhook attempt {attempt}/{settings.webhook_retry_attempts} failed for {url}"
                )
                if attempt < settings.webhook_retry_attempts:
                    await asyncio.sleep(delay)
                    delay *= 2
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.critical(
                    f"Unhandled exception happened: {e}"
                )

    return False
