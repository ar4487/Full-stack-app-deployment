# app/database.py
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import ssl

# Load .env explicitly from the same folder as this file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
print("Loaded DB URL:", os.getenv("DATABASE_URL"))
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Check app/.env location/content.")

# RDS typically enforces SSL; asyncpg needs an SSL context
ssl_ctx = ssl.create_default_context(cafile=os.path.join(os.path.dirname(__file__), "global-bundle.pem"))

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_ctx},  # <-- IMPORTANT for RDS
)



AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
