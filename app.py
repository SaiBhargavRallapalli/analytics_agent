from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
import os

# Import the core agent function from your main.py
from main import run_agent_query 

# Configure logging for the API
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hybrid Analytics Agent API",
    description="API for an intelligent agent capable of performing hybrid analytics queries on e-commerce data.",
    version="1.0.0",
)

# Pydantic model for request body validation
class QueryRequest(BaseModel):
    query: str

# Pydantic model for response body
class QueryResponse(BaseModel):
    response: str
    tools_used: str # New field for tools used

@app.get("/")
async def read_root():
    """
    Root endpoint for a health check.
    """
    return {"message": "Hybrid Analytics Agent API is running!"}

@app.post("/query", response_model=QueryResponse) # Specify response_model
async def process_query(request: QueryRequest):
    """
    Processes a natural language query using the Hybrid Analytics Agent.
    Returns the agent's response and information about the tools used.
    """
    user_query = request.query
    logger.info(f"Received query: '{user_query}'")

    try:
        # Call the core agent logic, which now returns a dictionary
        agent_result = run_agent_query(user_query)
        
        agent_response_text = agent_result.get("response", "No response from agent.")
        tools_info = agent_result.get("tools_used", "Unknown")

        logger.info(f"Agent response for '{user_query}': {agent_response_text}")
        logger.info(f"Tools used: {tools_info}")

        return QueryResponse(response=agent_response_text, tools_used=tools_info)
    except Exception as e:
        logger.error(f"Error processing query '{user_query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

if __name__ == "__main__":
    required_env_vars = ["OPENAI_API_KEY", "DATABASE_URL", "MEILI_HOST", "MEILI_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            logger.warning(f"Environment variable '{var}' is not set. The agent might not function correctly.")

    logger.info("Starting FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

