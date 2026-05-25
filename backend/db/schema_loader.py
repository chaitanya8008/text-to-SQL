"""
Universal schema loader for multiple SQL databases.
Loads table schemas and sample rows to provide context for LLM SQL generation.
Supports PostgreSQL, MySQL, SQLite, SQL Server via SQLAlchemy inspect.
"""
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import sync_engine


def get_all_tables() -> list[str]:
    """
    Get all table names from the database using SQLAlchemy inspect.
    Works with any database dialect.
    """
    inspector = inspect(sync_engine)
    return inspector.get_table_names()


def get_table_columns(table_name: str) -> list[dict]:
    """
    Get column information for a specific table using SQLAlchemy inspect.
    Returns list of dicts with 'name' and 'type' keys.
    Works with any database dialect.
    """
    inspector = inspect(sync_engine)
    columns = inspector.get_columns(table_name)
    return [{"name": col["name"], "type": str(col["type"])} for col in columns]


async def get_schema_context(session: AsyncSession, sample_rows: int = 3) -> str:
    """
    Reads all tables and returns a context string with column names + sample rows.
    Uses SQLAlchemy inspect for universal database support.
    """
    # Get all table names using inspect (works with any database)
    tables = get_all_tables()

    schema_context = ""

    for table in tables:
        # Get column names and types using inspect
        columns_info = get_table_columns(table)
        columns = [col["name"] for col in columns_info]
        column_types = {col["name"]: col["type"] for col in columns_info}

        # Get sample rows using async session
        try:
            result = await session.execute(text(f"SELECT * FROM {table} LIMIT :limit;"), {"limit": sample_rows})
            rows = result.fetchall()
        except Exception:
            # Fallback for SQL Server which uses TOP instead of LIMIT
            try:
                result = await session.execute(text(f"SELECT TOP {sample_rows} * FROM {table};"))
                rows = result.fetchall()
            except Exception:
                rows = []

        schema_context += f"\nTable: {table}\n"
        schema_context += f"Columns: {', '.join(columns)}\n"
        schema_context += f"Column types: {column_types}\n"
        schema_context += "Sample rows:\n"
        for row in rows:
            schema_context += f"  {dict(row._mapping)}\n"
        schema_context += "\n"

    return schema_context


async def get_relevant_schema(session: AsyncSession, user_question: str, sample_rows: int = 3) -> str:
    """
    Only loads schema for tables relevant to the user's question.
    Uses smart keyword matching with fallback to all tables.
    Uses SQLAlchemy inspect for universal database support.
    """
    # Get all table names using inspect (works with any database)
    all_tables = get_all_tables()

    question_lower = user_question.lower()

    # Smart keyword matching - check for partial matches and related keywords
    relevant_tables = []
    
    # Define keyword mappings for better matching
    keyword_mappings = {
        'employee': ['employees', 'employee', 'staff', 'worker'],
        'department': ['departments', 'department', 'dept'],
        'project': ['projects', 'project'],
        'assignment': ['project_assignments', 'assignment', 'hours', 'allocated'],
        'review': ['performance_reviews', 'review', 'performance', 'rating'],
        'salary': ['salary_history', 'salary', 'pay', 'compensation'],
        'location': ['locations', 'location', 'office', 'city'],
        'product': ['products', 'product', 'item'],
        'customer': ['customers', 'customer', 'client'],
        'order': ['orders', 'order', 'purchase']
    }
    
    # Check each table against question keywords
    for table in all_tables:
        table_lower = table.lower()
        
        # Direct match - table name appears in question
        if table_lower in question_lower:
            relevant_tables.append(table)
            continue
        
        # Check if any keyword variant matches
        for keyword, variants in keyword_mappings.items():
            if any(variant in question_lower for variant in variants):
                # Check if this table is related to the keyword
                if keyword in table_lower or table_lower in keyword:
                    if table not in relevant_tables:
                        relevant_tables.append(table)
                    break
    
    # If no matches found, load all tables (fallback)
    if not relevant_tables:
        relevant_tables = all_tables

    schema_context = ""
    for table in relevant_tables:
        # Get column names and types using inspect
        columns_info = get_table_columns(table)
        columns = [col["name"] for col in columns_info]

        # Get sample rows using async session
        try:
            result = await session.execute(text(f"SELECT * FROM {table} LIMIT :limit;"), {"limit": sample_rows})
            rows = result.fetchall()
        except Exception:
            # Fallback for SQL Server which uses TOP instead of LIMIT
            try:
                result = await session.execute(text(f"SELECT TOP {sample_rows} * FROM {table};"))
                rows = result.fetchall()
            except Exception:
                rows = []

        schema_context += f"\nTable: {table}\n"
        schema_context += f"Columns: {', '.join(columns)}\n"
        schema_context += "Sample rows:\n"
        for row in rows:
            schema_context += f"  {dict(row._mapping)}\n"
        schema_context += "\n"

    return schema_context
