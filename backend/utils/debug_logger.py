"""
Debug logger for Text-to-SQL Chatbot.
Saves query context, prompts, and responses to JSON for debugging.
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any


# Create debug directory if it doesn't exist
DEBUG_DIR = "debug_logs"
os.makedirs(DEBUG_DIR, exist_ok=True)


def save_debug_info(
    question: str,
    schema_context: str,
    prompt: str,
    sql_query: Optional[str] = None,
    llm_response: Optional[str] = None,
    error: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save debug information to a JSON file.
    
    Returns the path to the saved debug file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{DEBUG_DIR}/debug_{timestamp}.json"
    
    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "schema_context": schema_context,
        "prompt_sent_to_llm": prompt,
        "llm_response": llm_response,
        "generated_sql": sql_query,
        "error": error,
        "query_result": result,
        "analysis": {
            "tables_in_schema": extract_tables_from_schema(schema_context),
            "question_keywords": extract_keywords(question),
            "potential_issue": analyze_potential_issue(question, schema_context, sql_query, error)
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"DEBUG: Saved debug info to {filename}")
    print(f"{'='*60}\n")
    
    return filename


def extract_tables_from_schema(schema_context: str) -> list:
    """Extract table names from schema context string."""
    tables = []
    for line in schema_context.split('\n'):
        if line.startswith('Table:'):
            table_name = line.replace('Table:', '').strip()
            tables.append(table_name)
    return tables


def extract_keywords(question: str) -> list:
    """Extract potential keywords from the question."""
    # Common table-related keywords
    keywords = []
    question_lower = question.lower()
    
    table_keywords = {
        'employee': ['employees', 'employee', 'staff', 'worker'],
        'department': ['departments', 'department', 'dept'],
        'project': ['projects', 'project'],
        'assignment': ['assignments', 'assignment', 'hours', 'allocated'],
        'review': ['reviews', 'review', 'performance', 'rating'],
        'salary': ['salary', 'salaries', 'pay', 'compensation'],
        'location': ['locations', 'location', 'office', 'city'],
        'product': ['products', 'product', 'item'],
        'customer': ['customers', 'customer', 'client'],
        'order': ['orders', 'order', 'purchase']
    }
    
    for category, words in table_keywords.items():
        for word in words:
            if word in question_lower:
                keywords.append(category)
                break
    
    return list(set(keywords))


def analyze_potential_issue(
    question: str,
    schema_context: str,
    sql_query: Optional[str],
    error: Optional[str]
) -> str:
    """Analyze what might have gone wrong."""
    issues = []
    
    # Check if UNABLE_TO_ANSWER was returned
    if sql_query and "UNABLE_TO_ANSWER" in sql_query:
        issues.append("LLM returned UNABLE_TO_ANSWER - couldn't generate SQL")
    
    # Check if schema context is empty or minimal
    if not schema_context or len(schema_context.strip()) < 100:
        issues.append("Schema context is empty or very small")
    
    # Check if relevant tables are in schema
    tables_in_schema = extract_tables_from_schema(schema_context)
    question_keywords = extract_keywords(question)
    
    if 'employee' in question_keywords and 'employees' not in tables_in_schema:
        issues.append("Question mentions employees but employees table not in schema")
    
    if 'project' in question_keywords and 'projects' not in tables_in_schema:
        issues.append("Question mentions projects but projects table not in schema")
    
    if 'assignment' in question_keywords and 'project_assignments' not in tables_in_schema:
        issues.append("Question mentions assignments/hours but project_assignments table not in schema")
    
    # Check for SQL errors
    if error:
        if "relation" in error.lower() and "does not exist" in error.lower():
            issues.append(f"Table doesn't exist: {error}")
        elif "column" in error.lower() and "does not exist" in error.lower():
            issues.append(f"Column doesn't exist: {error}")
        elif "syntax error" in error.lower():
            issues.append(f"SQL syntax error: {error}")
    
    if not issues:
        issues.append("No obvious issues detected - may be LLM confusion")
    
    return "; ".join(issues)


def get_latest_debug_file() -> Optional[str]:
    """Get the path to the most recent debug file."""
    if not os.path.exists(DEBUG_DIR):
        return None
    
    files = [f for f in os.listdir(DEBUG_DIR) if f.startswith('debug_') and f.endswith('.json')]
    if not files:
        return None
    
    # Sort by timestamp (filename)
    files.sort(reverse=True)
    return os.path.join(DEBUG_DIR, files[0])


def read_debug_file(filepath: str) -> Dict[str, Any]:
    """Read and return debug file contents."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
