"""
Database query executor for multiple SQL databases.
Handles safe query execution, validation, and retry logic.
Supports PostgreSQL, MySQL, SQLite, SQL Server via SQLAlchemy.
"""
import re
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings, sync_engine


def enforce_limit(sql_query: str, dialect: str = "postgresql", limit: int = 50) -> str:
    """
    Adds LIMIT clause if not already present.
    Prevents huge result sets from crashing the app.
    
    Handles dialect-specific syntax:
    - PostgreSQL, MySQL, SQLite: LIMIT n
    - SQL Server: TOP n or OFFSET/FETCH
    """
    sql_clean = sql_query.strip().rstrip(";")

    # Check if LIMIT/TOP already exists (case-insensitive)
    if re.search(r'\bLIMIT\b', sql_clean, re.IGNORECASE):
        return sql_clean + ";"
    if re.search(r'\bTOP\b', sql_clean, re.IGNORECASE):
        return sql_clean + ";"
    if re.search(r'\bFETCH\b', sql_clean, re.IGNORECASE):
        return sql_clean + ";"

    # Add dialect-specific limit
    if dialect == "mssql":
        # SQL Server uses TOP n after SELECT
        sql_clean = re.sub(
            r'^(SELECT\s+)',
            f'SELECT TOP {limit} ',
            sql_clean,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # PostgreSQL, MySQL, SQLite use LIMIT n at the end
        sql_clean += f" LIMIT {limit}"

    return sql_clean + ";"


async def validate_sql_against_schema(session: AsyncSession, sql_query: str) -> tuple[bool, str]:
    """
    Basic check: verifies table names in the SQL exist in the database.
    Returns (is_valid, error_message).
    Uses SQLAlchemy inspect for universal database support.
    """
    try:
        # Use sync engine for inspection (inspect doesn't work well with async)
        inspector = inspect(sync_engine)
        real_tables = {table.lower() for table in inspector.get_table_names()}

        # Extract table names from SQL (basic regex — good enough for SELECT queries)
        mentioned = re.findall(r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)', sql_query, re.IGNORECASE)
        mentioned_tables = {name.lower() for pair in mentioned for name in pair if name}

        invalid = mentioned_tables - real_tables
        if invalid:
            return False, f"Table(s) not found in database: {', '.join(invalid)}"
        return True, ""
    except Exception as e:
        # If inspection fails, skip validation (query will fail anyway if table doesn't exist)
        return True, ""


async def run_query(session: AsyncSession, sql_query: str):
    """
    Safely runs a SELECT query and returns results.
    Uses read-only database user for true security.
    Uses SQLAlchemy async session with connection pooling.
    Returns data in {"columns": [...], "rows": [...]} format.
    """
    try:
        result = await session.execute(text(sql_query))

        # Get column names
        columns = list(result.keys())

        # Fetch rows
        rows = result.fetchall()

        # Convert to list of lists for JSON serialization
        rows_list = [list(row) for row in rows]

        return {"columns": columns, "rows": rows_list}, None
    except Exception as e:
        return None, str(e)


async def run_query_with_retry(
    session: AsyncSession,
    sql_query: str,
    user_question: str,
    schema_context: str,
    dialect: str = "postgresql",
    max_retries: int = 2
):
    """
    Runs a SQL query. If it fails, tells the LLM what went wrong
    and asks it to fix the query. Retries up to max_retries times.
    Uses SQLAlchemy async session with connection pooling.
    """
    from backend.llm.groq_client import generate_sql
    from backend.llm.prompt_builder import build_retry_prompt

    current_sql = sql_query

    for attempt in range(max_retries + 1):
        # Enforce LIMIT before running (dialect-aware)
        current_sql = enforce_limit(current_sql, dialect=dialect)

        # Validate against schema
        is_valid, validation_error = await validate_sql_against_schema(session, current_sql)
        if not is_valid:
            if attempt < max_retries:
                retry_prompt = build_retry_prompt(
                    schema_context=schema_context,
                    failed_sql=current_sql,
                    error_message=validation_error,
                    original_question=user_question,
                    dialect=dialect
                )
                current_sql = generate_sql(retry_prompt)
                continue
            else:
                return None, current_sql, validation_error

        # Run the query
        result, error = await run_query(session, current_sql)

        if result is not None:
            return result, current_sql, None  # Success

        if attempt < max_retries:
            # Build a retry prompt with the error context
            retry_prompt = build_retry_prompt(
                schema_context=schema_context,
                failed_sql=current_sql,
                error_message=error,
                original_question=user_question,
                dialect=dialect
            )
            current_sql = generate_sql(retry_prompt)
        else:
            return None, current_sql, error  # All retries exhausted

    return None, current_sql, "Max retries reached"
