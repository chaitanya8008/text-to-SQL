"""
Prompt builder for LLM SQL generation.
Constructs context-rich prompts with few-shot examples for better SQL generation.
Supports multiple SQL dialects: PostgreSQL, MySQL, SQLite, SQL Server.
"""
from backend.core.config import settings


def get_dialect_instructions(dialect: str) -> str:
    """
    Returns dialect-specific SQL instructions for the LLM.
    """
    dialect_map = {
        "postgresql": """
DIALECT-SPECIFIC RULES (PostgreSQL):
- Use PostgreSQL syntax
- Use LIMIT n for pagination (e.g., SELECT * FROM table LIMIT 50)
- Use SERIAL for auto-incrementing primary keys
- Use DATE, TIMESTAMP for date/time types
- Use ILIKE for case-insensitive pattern matching
- Use :: for type casting (e.g., column::INTEGER)
""",
        "mysql": """
DIALECT-SPECIFIC RULES (MySQL):
- Use MySQL syntax
- Use LIMIT n for pagination (e.g., SELECT * FROM table LIMIT 50)
- Use AUTO_INCREMENT for auto-incrementing primary keys
- Use DATETIME, DATE for date/time types
- Use LIKE for pattern matching (case-insensitive by default with collation)
- Use CAST() for type casting
""",
        "sqlite": """
DIALECT-SPECIFIC RULES (SQLite):
- Use SQLite syntax
- Use LIMIT n for pagination (e.g., SELECT * FROM table LIMIT 50)
- Use INTEGER PRIMARY KEY for auto-incrementing
- Use TEXT, INTEGER, REAL, BLOB for data types
- Use LIKE for pattern matching (case-insensitive for ASCII)
- Use CAST() for type casting
""",
        "mssql": """
DIALECT-SPECIFIC RULES (SQL Server):
- Use SQL Server (T-SQL) syntax
- Use TOP n for limiting results (e.g., SELECT TOP 50 * FROM table)
- Use IDENTITY(1,1) for auto-incrementing primary keys
- Use DATETIME, DATE for date/time types
- Use LIKE for pattern matching
- Use CAST() or CONVERT() for type casting
- Use [brackets] for identifiers with special characters
- Use OFFSET/FETCH for pagination when needed
"""
    }
    return dialect_map.get(dialect, dialect_map["postgresql"])


def build_prompt(schema_context: str, user_question: str, dialect: str = "postgresql", last_sql: str = None) -> str:
    """
    Builds the instruction prompt with few-shot examples for better SQL generation.
    Supports multiple SQL dialects.
    """
    # Build few-shot examples section
    few_shot_section = "EXAMPLES (for reference):\n"
    for example in settings.FEW_SHOT_EXAMPLES:
        few_shot_section += f"Question: {example['question']}\n"
        few_shot_section += f"SQL: {example['sql']}\n\n"

    # Add context from previous query if available
    context_block = ""
    if last_sql:
        context_block = f"""
PREVIOUS QUERY CONTEXT:
The user's last query was: {last_sql}
If the new question is a follow-up or refinement, build on this query.
"""

    # Get dialect-specific instructions
    dialect_instructions = get_dialect_instructions(dialect)

    prompt = f"""You are a SQL expert helping non-technical users query a {dialect.upper()} database.

{few_shot_section}

DATABASE SCHEMA (with sample data to understand relationships):
{schema_context}

{context_block}

{dialect_instructions}

STRICT RULES:
1. Return ONLY a valid SQL SELECT query — no explanation, no markdown, no backticks.
2. Use correct JOINs when the answer requires data from multiple tables.
   - Match foreign keys exactly as shown in the sample data (e.g. orders.product_id = products.product_id).
3. Always limit results to 50 rows unless the user asks for a specific count.
4. NEVER use DROP, DELETE, UPDATE, INSERT, ALTER, or TRUNCATE.
5. If the question cannot be answered with the available schema, return exactly: UNABLE_TO_ANSWER
6. Never invent column names or table names — use only what exists in the schema above.
7. Use strictly {dialect.upper()} syntax as specified above.

USER QUESTION: {user_question}

SQL QUERY:
"""
    return prompt


def build_retry_prompt(schema_context: str, failed_sql: str, error_message: str, original_question: str, dialect: str = "postgresql") -> str:
    """
    Builds a retry prompt when the initial SQL query fails.
    Supports multiple SQL dialects.
    """
    dialect_instructions = get_dialect_instructions(dialect)

    return f"""You are a SQL expert. A previous query you generated failed.

Database schema:
{schema_context}

Original question: {original_question}

Failed SQL query:
{failed_sql}

Error message:
{error_message}

{dialect_instructions}

Fix the SQL query using strictly {dialect.upper()} syntax. Return ONLY the corrected SQL — no explanation.

Corrected SQL:
"""
