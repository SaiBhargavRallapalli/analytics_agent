import json
import os
import logging
from datetime import datetime, date
from decimal import Decimal

# Assuming these are in separate files and correctly implemented:
from llm_integration import get_llm_tool_response, get_llm_response
from meilisearch_tools import meilisearch_query
from sql_tools import execute_sql_query
from chart_tools import generate_chart

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Custom JSON Encoder for Datetime, Date, and Decimal Objects ---
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj) # Convert Decimal to float for JSON serialization
        return json.JSONEncoder.default(self, obj)

# --- Tool Definitions for LLM ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "meilisearch_query",
            "description": "Searches for products or users in Meilisearch. Use this for free-text search, fuzzy matching, or combined with filters on indexed attributes like category, brand, price for products, or location, registration_date, email for users. Index names are 'products' and 'users'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index_name": {
                        "type": "string",
                        "description": "The name of the Meilisearch index to query. Must be 'products' or 'users'.",
                        "enum": ["products", "users"]
                    },
                    "query": {
                        "type": "string",
                        "description": "The free-text search query string. Optional.",
                        "default": ""
                    },
                    "filters": {
                        "type": "string",
                        "description": "A Meilisearch filter string for structured filtering (e.g., 'category = \"Electronics\" AND price < 500'). Attributes: products (category, brand, price), users (location, registration_date, email). Use `CONTAINS` or `STARTS WITH` for partial string matches (e.g., 'email CONTAINS \".com\"').",
                        "default": ""
                    }
                },
                "required": ["index_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "Executes a SQL query against the PostgreSQL database. Use this for analytical queries, aggregations, joins, or when precise numerical or date-based filtering/grouping is needed across multiple tables (products, users, transactions).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "The full SQL query to execute, including SELECT, FROM, WHERE, GROUP BY, ORDER BY, etc."
                    }
                },
                "required": ["sql_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_chart",
            "description": "Generates a visual chart (e.g., bar chart, line chart) from provided tabular data. Use this when the user explicitly asks for a chart, graph, or visualization. Requires data, chart type, and columns for X and Y axes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "The tabular data as a list of dictionaries (e.g., the 'data' field from an execute_sql_query output). Each dictionary is a row."
                    },
                    "chart_type": {
                        "type": "string",
                        "enum": ["bar", "line"],
                        "description": "The type of chart to generate ('bar' for categorical comparisons, 'line' for trends over time)."
                    },
                    "x_column": {
                        "type": "string",
                        "description": "The name of the column from the 'data' to use for the X-axis (e.g., 'month', 'category')."
                    },
                    "y_column": {
                        "type": "string",
                        "description": "The name of the column from the 'data' to use for the Y-axis (e.g., 'total_sales_amount', 'average_price')."
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the chart."
                    },
                    "x_label": {
                        "type": "string",
                        "description": "Optional label for the X-axis."
                    },
                    "y_label": {
                        "type": "string",
                        "description": "Optional label for the Y-axis."
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the saved chart image (e.g., 'sales_by_month.png'). If not provided, a unique name will be generated."
                    }
                },
                "required": ["data", "chart_type", "x_column", "y_column", "title"]
            }
        }
    }
]

# --- Agent Logic ---
def run_agent_query(user_query: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful analytics assistant that can answer questions about an e-commerce platform. "
                "You have access to three tools:\n"
                "1. `meilisearch_query`: For free-text search, fuzzy matching, and filtering. "
                "   Use this for looking up specific items or users, or finding entities with certain characteristics. "
                "   Available indexes: `products` (attributes: name, category, brand, price), `users` (attributes: name, email, location, registration_date).\n"
                "2. `execute_sql_query`: For complex analytical queries, aggregations (COUNT, SUM, AVG, MIN, MAX), "
                "   joins across multiple tables, or precise numerical/date range filtering. "
                "   Available tables in the database with their columns:\n"
                "   - `products` (columns: product_id, name, category, brand, price)\n"
                "   - `users` (columns: user_id, name, email, location, registration_date)\n"
                "   - `transactions` (columns: order_id, user_id, product_id, amount, timestamp, status) - Note: The transaction date/time column is named `timestamp`.\n"
                "3. `generate_chart`: For creating visualizations (bar charts, line charts) from tabular data. "
                "   Use this when the user explicitly asks for a 'chart', 'graph', 'plot', or 'visualization'. "
                "   This tool requires the 'data' argument, which MUST be the *exact list of dictionaries* obtained from the 'data' key in the output of a successful `execute_sql_query` tool call.\n"
                "   For example, if `execute_sql_query` output was `{\"success\": true, \"data\": [{\"col1\": \"val1\", \"col2\": 10}, {\"col1\": \"val3\", \"col2\": 20}]}`, "
                "   then your `generate_chart` call should include `data=[{\"col1\": \"val1\", \"col2\": 10}, {\"col1\": \"val3\", \"col2\": 20}]`. Do NOT omit or reformat this list.\n\n"
                "**Tool Selection Guidelines:**\n"
                "- **Prioritize `meilisearch_query`** for direct search queries, fuzzy matching, or simple filtering on individual attributes where a list of results is expected. **Important Meilisearch Filter Syntax:** Use `attribute = \"value\"` (e.g., `location = \"Bengaluru\"`). For partial matches, use `attribute CONTAINS \"value\"`.\n"
                "- **Prioritize `execute_sql_query`** for questions involving:\n"
                "    - **Aggregations:** (e.g., 'total sales', 'average price', 'number of users').\n"
                "    - **Relationships across tables:** (e.g., 'products bought by a specific user').\n"
                "    - **Complex numerical/date logic:** (e.g., 'users registered between dates', 'products above a certain price threshold that also meet another criteria').\n"
                "    - **When using SQL, ensure column names match the schema provided (e.g., `timestamp` for transaction date/time).**\n"
                "- **Prioritize `generate_chart` when a visualization is requested.** You **MUST** call `execute_sql_query` first to get the data. Then, carefully extract the **`data` array (the list of dictionaries)** from the `execute_sql_query`'s *successful output* and pass that *exact array* as the `data` argument to the `generate_chart` tool.\n"
                "- **Multi-step Reasoning (Tool Chaining):** If a query requires information from one tool to inform another (e.g., 'find users in X, then calculate Y for their transactions'), perform the first tool call, analyze its output, and then make a subsequent tool call using the extracted relevant data (e.g., user IDs from Meilisearch to filter SQL queries). **When using SQL for intermediate steps, select only the columns strictly necessary for the next step (e.g., `product_id` if you need to join on products).** Continue making tool calls as long as necessary to fully answer the query. Do not provide a final answer until all necessary information is gathered.\n"
                "- When using `execute_sql_query`, always return a complete, valid SQL query.\n"
                "- If the query asks for both free-text search AND aggregation, consider if Meilisearch can filter first and then SQL can aggregate, but lean towards SQL if direct aggregation is requested.\n"
                "- If a user asks for information that cannot be retrieved by the available tools or is ambiguous, inform them of the limitation or ask for clarification.\n"
                "- When presenting results, summarize them clearly and concisely in natural language, referencing the data provided by the tools."
            )
        },
        {"role": "user", "content": user_query}
    ]

    max_total_steps = 5
    current_step = 0
    
    last_sql_query_data = None
    tools_executed_in_chain = set()

    while current_step < max_total_steps:
        current_step += 1
        print(f"Agent thinking... (Step {current_step}/{max_total_steps})")

        llm_response_message = get_llm_tool_response(messages=messages, tools=tools)
        
        if isinstance(llm_response_message, dict) and llm_response_message.get("role") == "assistant":
            return {
                "response": llm_response_message.get("content", "An unexpected error occurred with the AI response."),
                "tools_used": "None" if not tools_executed_in_chain else ", ".join(sorted(list(tools_executed_in_chain)))
            }

        tool_calls = llm_response_message.tool_calls

        if tool_calls:
            available_functions = {
                "meilisearch_query": meilisearch_query,
                "execute_sql_query": execute_sql_query,
                "generate_chart": generate_chart
            }

            messages.append(llm_response_message)

            tool_outputs = []
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                
                if function_to_call:
                    tools_executed_in_chain.add(function_name)
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        print(f"\nAgent decided to call: {function_name} with args: {function_args}")

                        tool_output_raw = function_to_call(**function_args)
                        
                        # --- FIX: Parse JSON string output from tools like meilisearch_query ---
                        if isinstance(tool_output_raw, str):
                            try:
                                tool_output_parsed = json.loads(tool_output_raw)
                            except json.JSONDecodeError:
                                # If it's a string but not valid JSON, treat as an error message
                                tool_output_parsed = {"success": False, "message": f"Tool returned invalid JSON string: {tool_output_raw}"}
                        else:
                            tool_output_parsed = tool_output_raw
                        # --- END FIX ---

                        # --- FIX: Intercept `generate_chart` call to ensure 'data' is present ---
                        if function_name == 'generate_chart' and 'data' not in function_args:
                            if last_sql_query_data is not None:
                                print("Fixing missing 'data' argument for generate_chart by injecting from previous SQL output.")
                                function_args['data'] = last_sql_query_data
                                # Re-call the function with corrected arguments
                                tool_output_raw = function_to_call(**function_args)
                                # Re-parse the (potentially new) raw output
                                if isinstance(tool_output_raw, str):
                                    try:
                                        tool_output_parsed = json.loads(tool_output_raw)
                                    except json.JSONDecodeError:
                                        tool_output_parsed = {"success": False, "message": f"Tool returned invalid JSON string after data injection: {tool_output_raw}"}
                                else:
                                    tool_output_parsed = tool_output_raw
                            else:
                                raise ValueError("Missing 'data' argument for generate_chart and no previous SQL query data available.")
                        # --- END FIX ---


                        print(f"Tool output: {json.dumps(tool_output_parsed, indent=2, cls=DateTimeEncoder)}")

                        # Store the data if the SQL query was successful
                        if function_name == "execute_sql_query" and tool_output_parsed.get("success", False):
                            last_sql_query_data = tool_output_parsed.get("data")
                        
                        if (function_name == "meilisearch_query" and
                            not tool_output_parsed.get("success", True) and
                            tool_output_parsed.get("code") == "invalid_search_filter"):
                            print("Meilisearch filter error detected. Asking LLM to correct filter.")
                        
                        if function_name == "execute_sql_query" and not tool_output_parsed.get("success", True):
                            error_message = tool_output_parsed.get("message", "An unknown SQL error occurred.")
                            print(f"SQL error detected: {error_message}. Asking LLM to correct SQL.")
                        
                        if function_name == "generate_chart" and tool_output_parsed.get("success", False):
                            chart_path = tool_output_parsed.get("file_path")
                            print(f"Chart successfully saved at: {chart_path}")
                        
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps(tool_output_parsed, cls=DateTimeEncoder),
                            }
                        )

                    except json.JSONDecodeError as e:
                        error_msg = f"Error parsing arguments for tool {function_name}: {e}. Arguments were: {tool_call.function.arguments}"
                        logger.error(error_msg)
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps({"error": error_msg}, cls=DateTimeEncoder),
                            }
                        )
                    except ValueError as e:
                        error_msg = f"Chart generation error: {e}"
                        logger.error(error_msg)
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps({"error": error_msg}, cls=DateTimeEncoder),
                            }
                        )
                    except Exception as e:
                        error_msg = f"Error executing tool {function_name}: {e}"
                        logger.error(error_msg)
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps({"error": error_msg}, cls=DateTimeEncoder),
                            }
                        )
                else:
                    error_msg = f"Error: Tool '{function_name}' not found."
                    logger.error(error_msg)
                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps({"error": error_msg}, cls=DateTimeEncoder),
                        }
                    )
            
            messages.extend(tool_outputs)

        else:
            return {
                "response": llm_response_message.content,
                "tools_used": "None" if not tools_executed_in_chain else ", ".join(sorted(list(tools_executed_in_chain)))
            }

    return {
        "response": "The agent could not fully resolve the query after multiple steps. Please try rephrasing your query.",
        "tools_used": "None" if not tools_executed_in_chain else ", ".join(sorted(list(tools_executed_in_chain)))
    }


# --- Interactive Loop (for CLI testing, not used by API directly) ---
if __name__ == "__main__":
    print("Hybrid Analytics Agent. Type 'exit' to quit.")
    while True:
        user_input = input("\nYour query: ")
        if user_input.lower() == 'exit':
            print("Exiting agent. Goodbye!")
            break

        agent_result = run_agent_query(user_input)
        print(f"\nAgent Response: {agent_result['response']}")
        print(f"Tools Used: {agent_result['tools_used']}")

