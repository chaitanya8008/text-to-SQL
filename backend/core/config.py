"""
Configuration management for Text-to-SQL Chatbot.
Handles environment variables, database connection, and few-shot examples.
Supports multiple database dialects: PostgreSQL, MySQL, SQLite, SQL Server.
"""
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()


def extract_dialect(database_url: str) -> str:
    """
    Extract database dialect from DATABASE_URL.
    Supports: postgresql, mysql, sqlite, mssql
    """
    if not database_url:
        return "postgresql"  # Default
    
    parsed = urlparse(database_url)
    scheme = parsed.scheme.lower()
    
    # Handle various URL schemes
    if "postgresql" in scheme or "postgres" in scheme:
        return "postgresql"
    elif "mysql" in scheme:
        return "mysql"
    elif "sqlite" in scheme:
        return "sqlite"
    elif "mssql" in scheme or "sqlserver" in scheme:
        return "mssql"
    else:
        return "postgresql"  # Default fallback


class Settings:
    """Application settings loaded from environment variables."""
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_DIALECT: str = extract_dialect(DATABASE_URL)
    MAX_QUERY_LIMIT: int = 50
    MAX_RETRIES: int = 2

    # Few-shot examples for better SQL generation
    FEW_SHOT_EXAMPLES = [
        {
            "question": "What is the price of product ID 1?",
            "sql": "SELECT price FROM products WHERE product_id = 1;"
        },
        {
            "question": "How many products are in the Electronics category?",
            "sql": "SELECT COUNT(*) FROM products WHERE category = 'Electronics';"
        },
        {
            "question": "Which customer placed the most orders?",
            "sql": "SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id ORDER BY order_count DESC LIMIT 1;"
        },
        {
            "question": "Show all orders with product names",
            "sql": "SELECT o.order_id, p.name, o.quantity FROM orders o JOIN products p ON o.product_id = p.product_id;"
        },
        {
            "question": "What is the total revenue from all orders?",
            "sql": "SELECT SUM(p.price * o.quantity) as total_revenue FROM orders o JOIN products p ON o.product_id = p.product_id;"
        }
    ]


settings = Settings()


def get_sync_database_url(async_url: str) -> str:
    """
    Convert async database URL to sync URL for schema inspection.
    Handles postgresql+asyncpg -> postgresql, mysql+aiomysql -> mysql, etc.
    """
    if "+asyncpg" in async_url:
        return async_url.replace("+asyncpg", "")
    elif "+aiomysql" in async_url:
        return async_url.replace("+aiomysql", "")
    elif "+aiosqlite" in async_url:
        return async_url.replace("+aiosqlite", "")
    elif "+aioodbc" in async_url:
        return async_url.replace("+aioodbc", "")
    return async_url


# Create async engine with connection pooling
# SQLAlchemy handles connection pooling automatically out of the box
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_size=5,  # Number of connections to keep in pool
    max_overflow=10,  # Additional connections when pool is full
    pool_timeout=30,  # Seconds to wait for a connection
    pool_recycle=1800,  # Recycle connections after 30 minutes
)

# Create sync engine for schema inspection (inspect doesn't work with async)
sync_engine = create_engine(
    get_sync_database_url(settings.DATABASE_URL),
    echo=False,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency for FastAPI endpoints
async def get_db():
    """
    FastAPI dependency that provides a database session.
    Uses async context manager for proper cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
