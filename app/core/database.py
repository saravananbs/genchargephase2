# core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Example: postgresql+asyncpg for async support
DATABASE_URL = settings.DATABASE_URL

# Create an async engine
engine = create_async_engine(DATABASE_URL)

# Create async session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Base model class for ORM
Base = declarative_base()

# Dependency to get the async DB session
async def get_db():
    """
    Async database session dependency for FastAPI route handlers.

    Creates a new async SQLAlchemy session, yields it for route use,
    and ensures proper closure on completion or error.

    Yields:
        AsyncSession: Active async database session for query execution.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
