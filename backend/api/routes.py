"""
API routes for Text-to-SQL Chatbot.
Defines the query endpoint that processes natural language questions.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from backend.core.config import get_db, settings
from backend.db.schema_loader import get_schema_context
from backend.db.database import run_query_with_retry
from backend.llm.prompt_builder import build_prompt
from backend.llm.groq_client import generate_sql, generate_natural_response, detect_ambiguity
from backend.utils.debug_logger import save_debug_info

router = APIRouter()

# Request/Response models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str
    last_sql: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str
    sql_query: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    clarification_needed: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Process a natural language question and return SQL results.
    Uses async database operations with connection pooling.
    """
    try:
        # Step 1: Check for ambiguity
        clarification = detect_ambiguity(request.question)
        if clarification:
            # Save debug info for clarification
            save_debug_info(
                question=request.question,
                schema_context="",
                prompt="",
                sql_query=None,
                llm_response=clarification,
                error=None,
                result=None
            )
            return QueryResponse(
                answer="",
                clarification_needed=clarification
            )

        # Step 2: Get relevant schema (async)
        schema_context = await get_schema_context(session)

        # Step 3: Build prompt with few-shot examples (dialect-aware)
        prompt = build_prompt(
            schema_context=schema_context,
            user_question=request.question,
            dialect=settings.DB_DIALECT,
            last_sql=request.last_sql
        )

        # Step 4: Generate SQL
        sql_query = generate_sql(prompt)

        # Save debug info after SQL generation
        debug_file = save_debug_info(
            question=request.question,
            schema_context=schema_context,
            prompt=prompt,
            sql_query=sql_query,
            llm_response=sql_query,
            error=None,
            result=None
        )

        if sql_query == "UNABLE_TO_ANSWER":
            return QueryResponse(
                answer="🤔 I wasn't able to figure out a query for that question. Try being more specific — for example, mention the table name (products, orders, customers) or exact column values.",
                sql_query=None
            )

        # Step 5: Run query with retry logic (async, dialect-aware)
        result, final_sql, error = await run_query_with_retry(
            session=session,
            sql_query=sql_query,
            user_question=request.question,
            schema_context=schema_context,
            dialect=settings.DB_DIALECT,
            max_retries=settings.MAX_RETRIES
        )

        if error:
            # Save debug info for error
            save_debug_info(
                question=request.question,
                schema_context=schema_context,
                prompt=prompt,
                sql_query=final_sql,
                llm_response=sql_query,
                error=error,
                result=None
            )
            return QueryResponse(
                answer=f"There was an issue running the query: {error}",
                sql_query=final_sql,
                error=error
            )

        if not result["rows"]:
            # Save debug info for no results
            save_debug_info(
                question=request.question,
                schema_context=schema_context,
                prompt=prompt,
                sql_query=final_sql,
                llm_response=sql_query,
                error=None,
                result=result
            )
            return QueryResponse(
                answer="🔍 No matching records found for your question. Try rephrasing — for example, check if the product ID or name is correct.",
                sql_query=final_sql,
                data=result
            )

        # Step 6: Generate natural language response
        natural_response = generate_natural_response(
            sql_query=final_sql,
            results=result["rows"],
            question=request.question
        )

        # Save debug info for successful query
        save_debug_info(
            question=request.question,
            schema_context=schema_context,
            prompt=prompt,
            sql_query=final_sql,
            llm_response=natural_response,
            error=None,
            result=result
        )

        return QueryResponse(
            answer=natural_response,
            sql_query=final_sql,
            data=result
        )

    except Exception as e:
        # Print detailed error to console for debugging
        print("\n" + "="*60)
        print("ERROR in process_query:")
        print("="*60)
        print(traceback.format_exc())
        print("="*60 + "\n")
        
        # Save debug info for exception
        save_debug_info(
            question=request.question,
            schema_context="",
            prompt="",
            sql_query=None,
            llm_response=None,
            error=str(e),
            result=None
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
