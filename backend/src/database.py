import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

def get_asyncpg_url(url: str) -> tuple[str, dict]:
    if not url:
        return "", {}
    
    url = url.replace("postgresql://", "postgresql+asyncpg://")
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    connect_args = {}
    if "sslmode" in query_params:
        sslmode = query_params.pop("sslmode")[0]
        if sslmode in ("require", "verify-ca", "verify-full"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_context
    
    new_query = urlencode({k: v[0] for k, v in query_params.items()})
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed), connect_args

DATABASE_URL, CONNECT_ARGS = get_asyncpg_url(settings.database_url)

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=CONNECT_ARGS) if DATABASE_URL else None
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) if engine else None

class Base(DeclarativeBase):
    pass

async def get_db():
    if async_session is None:
        raise RuntimeError("Database not configured")
    async with async_session() as session:
        yield session
