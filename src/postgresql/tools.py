import os
import logging
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Record
from dotenv import load_dotenv
from asyncpg.connection import Connection
from mcp.server.fastmcp import FastMCP, Context
from asyncpg.exceptions import InvalidSQLStatementNameError

from utils import is_valid_query, format_select_query_results, is_select_query


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


@asynccontextmanager
async def lifespan(_: FastMCP):
    """
    Manage database connection lifecycle for FastMCP server.

    This context manager handles:
    - Database credential validation
    - Connection establishment and testing
    - Proper connection cleanup on server shutdown

    Args:
        _: FastMCP instance (unused in this implementation)

    Yields:
        Connection: Active asyncpg database connection

    Raises:
        Exception: If database connection fails
    """

    if any(var in {None, ""} for var in [DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT]):
        raise ValueError("Database credentials are not configured")

    conn = None

    try:
        conn: Connection = await asyncpg.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )

        await conn.fetchval("SELECT 1")

        logger.info("Successfully connected to the database")

        yield conn

    except Exception as exc:
        logger.error("Error caught %s", str(exc))
        raise exc
    finally:
        if conn and not conn.is_closed():
            await conn.close()
            logger.info("Database connection closed")


# Initialize FastMCP server
mcp = FastMCP("postgresql", lifespan=lifespan)


class SqlExecutionError(Exception):
    """Raised when SQL query execution fails."""


@mcp.tool(
    name="Execute SQL",
    title="Execute PostgreSQL Query",
    annotations={"readOnlyHint": True}
)
async def execute_sql(ctx: Context, query: str) -> str:
    """
    Execute PostgreSQL query with validation and proper error handling.

    This function:
    1. Validates the SQL query syntax and safety
    2. Executes SELECT queries and returns formatted results
    3. Executes non-SELECT queries and returns execution status
    4. Provides detailed error messages for debugging

    Args:
        ctx (Context): MCP context object containing database connection
        query (str): PostgreSQL query to execute

    Returns:
        str: Query results formatted as markdown or execution status message

    Raises:
        SqlExecutionError: If query validation or execution fails
    """

    conn: Connection = ctx.request_context.lifespan_context

    if conn.is_closed():
        raise SqlExecutionError("Database connection is closed")

    try:
        logger.info("Validating SQL query: %s",
                    query[:100] + "..." if len(query) > 100 else query)

        validation_result = await is_valid_query(query, conn)
        if not validation_result["status"]:
            raise InvalidSQLStatementNameError(validation_result["msg"])

        logger.info("Query validation passed, executing...")

        if is_select_query(query):
            records: list[Record] = await conn.fetch(query)
            logger.info("SELECT query returned %d records", len(records))
            response = format_select_query_results(records)
        else:
            async with conn.transaction():
                result_msg = await conn.execute(query)
                logger.info("Non-SELECT query executed: %s", result_msg)
                response = f"Query executed successfully: {result_msg}"

        return response

    except Exception as e:
        raise SqlExecutionError(
            f"Error while executing the given query: {str(e)}") from e
