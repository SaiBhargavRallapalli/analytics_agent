import os
from dotenv import load_dotenv
import meilisearch
import json
import requests

# Load environment variables
load_dotenv()

MEILI_HOST = os.getenv("MEILI_HOST")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY")

if not all([MEILI_HOST, MEILI_MASTER_KEY]):
    raise ValueError("Missing one or more environment variables: MEILI_HOST, MEILI_MASTER_KEY")

# Initialize Meilisearch client
try:
    meili_client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
    version = meili_client.get_version()
    print(f"Meilisearch client initialized successfully. Server version: {version['pkgVersion']}")
except Exception as e:
    print(f"Failed to initialize Meilisearch client: {e}")
    exit(1)


def meilisearch_query(index_name: str, query: str = None, filters: str = None, limit: int = 10, offset: int = 0) -> str:
    """
    Performs a search query against a specified Meilisearch index.
    
    Args:
        index_name (str): The UID of the Meilisearch index to search (e.g., "products" or "users").
        query (str, optional): The search query string.
        filters (str, optional): A Meilisearch filter string.
        limit (int, optional): The maximum number of results to return.
        offset (int, optional): The number of results to skip.

    Returns:
        str: JSON string representing the search results or error message.
    """
    if index_name not in ["products", "users"]:
        return json.dumps({"error": f"Invalid index_name. Must be 'products' or 'users'. Got: {index_name}"})

    try:
        search_url = f"{MEILI_HOST}/indexes/{index_name}/search"
        headers = {
            "Authorization": f"Bearer {MEILI_MASTER_KEY}",
            "Content-Type": "application/json"
        }
        
        search_params = {
            "limit": limit,
            "offset": offset
        }
        
        if query:
            search_params["q"] = query
        if filters:
            # For Meilisearch 1.15.2, we need to handle email filtering differently
            if "email" in filters and ("ENDS WITH" in filters or "CONTAINS" in filters):
                return json.dumps({
                    "error": "Filter limitation",
                    "message": "Email domain filtering requires Meilisearch v1.3+ with experimental features enabled",
                    "suggestion": "Upgrade Meilisearch or use exact email matching"
                })
            search_params["filter"] = filters

        response = requests.post(search_url, headers=headers, json=search_params)
        response.raise_for_status()
        results = response.json()
        
        return json.dumps({
            "hits": results.get("hits", []),
            "estimatedTotalHits": results.get("estimatedTotalHits", 0)
        }, indent=2)

    except requests.exceptions.RequestException as e:
        if e.response is not None:
            try:
                error_details = e.response.json()
                return json.dumps({
                    "error": "Meilisearch API error",
                    "code": error_details.get("code"),
                    "message": error_details.get("message"),
                    "type": error_details.get("type"),
                    "link": error_details.get("link")
                })
            except ValueError:
                return json.dumps({
                    "error": "HTTP error",
                    "status_code": e.response.status_code,
                    "message": str(e)
                })
        return json.dumps({
            "error": "HTTP request failed",
            "message": str(e)
        })
    except Exception as e:
        return json.dumps({
            "error": "Unexpected error",
            "message": str(e),
            "type": type(e).__name__,
            "details": f"Occurred while searching index '{index_name}'"
        })


# Testing with more detailed output
if __name__ == "__main__":
    print("--- Testing meilisearch_query ---")
    
    try:
        indexes = meili_client.get_raw_indexes()
        print("Available indexes:", [index['uid'] for index in indexes['results']])
    except Exception as e:
        print("Failed to get indexes:", str(e))

    tests = [
        {"name": "Fuzzy product search", "params": {"index_name": "products", "query": "lapto"}},
        {"name": "Filter products", "params": {"index_name": "products", "filters": "category = 'Electronics' AND price < 500"}},
        {"name": "User search with typo", "params": {"index_name": "users", "query": "benaluru"}},
        {"name": "Invalid index", "params": {"index_name": "invalid_index", "query": "test"}},
        {"name": "Combined query", "params": {"index_name": "products", "query": "T-Shirt", "filters": "category = 'Apparel'"}}
    ]

    for test in tests:
        print(f"\nTest: {test['name']}")
        print(f"Params: {test['params']}")
        result = meilisearch_query(**test['params'])
        print("Result:", result)