from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url, echo=(settings.app_env == "development"))


def get_async_session() -> async_sessionmaker:
    return async_sessionmaker(get_engine(), expire_on_commit=False)
