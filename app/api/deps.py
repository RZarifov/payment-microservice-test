from fastapi import Header, HTTPException, status

from app.db.session import async_session_factory
from app.settings.config import settings


async def get_db():
    async with async_session_factory() as session:
        yield session


async def verify_api_key(x_api_key: str = Header(...)) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
