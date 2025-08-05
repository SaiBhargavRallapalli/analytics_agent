import os
import json
from datetime import datetime, date
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder for datetime and date objects (Keep this as is)
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def execute_sql_query(sql_query: str):
    """
    Executes a given SQL query against the PostgreSQL database.
    Includes validation to ensure only safe SELECT queries are executed.
    Returns the results as a dictionary or an error message.
    """
    # --- SQL Query Validation---
    normalized_query = sql_query.strip().upper() # Normalize for case-insensitive checks

    # 1. Check for allowed operations (must start with SELECT)
    if not normalized_query.startswith("SELECT"):
        error_msg = f"SQL Validation Error: Only SELECT queries are allowed. Detected: '{sql_query[:50]}...'"
        logger.warning(error_msg)
        return {"success": False, "message": error_msg, "data": None}

    # 2. Prevent destructive DDL/DML operations
    forbidden_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
        "GRANT", "REVOKE", "RENAME", "ATTACH", "DETACH", "PRAGMA", "VACUUM",
        ";--", "--", "/*", "*/", # Basic comment/injection prevention
        "UNION ALL SELECT", "UNION SELECT", # Common in SQL injection, though not destructive on their own
        "OR 1=1", "OR '1'='1'" # Common injection patterns
    ]

    for keyword in forbidden_keywords:
        if keyword in normalized_query:
            error_msg = f"SQL Validation Error: Forbidden keyword '{keyword}' detected in query. Only analytical SELECT queries are permitted."
            logger.warning(error_msg)
            return {"success": False, "message": error_msg, "data": None}
            
    # --- End SQL Query Validation ---
    db_url = os.getenv("DATABASE_URL")

    try:
        engine = create_engine(db_url)
        logger.info(f"Executing SQL: {sql_query}")
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            connection.commit() 

            if result.returns_rows:
                rows = []
                for row in result:
                    row_dict = {}
                    for key, value in row._mapping.items():
                        row_dict[key] = value
                    rows.append(row_dict)
                return {"success": True, "message": "SQL query executed successfully.", "data": rows}
            else:
                return {"success": True, "message": f"SQL command executed. Rows affected: {result.rowcount}", "data": None}

    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return {"success": False, "message": f"Error executing SQL query: {e}", "data": None}