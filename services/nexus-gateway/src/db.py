"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.config import settings


# Create async engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    pool_size=10,
    max_overflow=20,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


class Database:
    """Database connection manager."""
    
    async def connect(self) -> None:
        """Establish database connection."""
        # Connection is lazy, this just validates the URL
        async with engine.begin() as conn:
            pass
    
    async def disconnect(self) -> None:
        """Close database connections."""
        await engine.dispose()
    
    async def get_session(self) -> AsyncSession:
        """Get an async database session."""
        async with async_session_maker() as session:
            yield session


database = Database()


async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with async_session_maker() as session:
        yield session
