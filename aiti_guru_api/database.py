from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from .config import DB_URL, DB_CONFIG

engine = create_async_engine(DB_URL, pool_pre_ping=True, connect_args={
    "server_settings": {
        "search_path": f"{DB_CONFIG['schema']}"
    }
})

new_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with new_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
