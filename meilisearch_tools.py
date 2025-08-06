import os
from dotenv import load_dotenv
import meilisearch
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

MEILI_HOST = os.getenv("MEILI_HOST")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY")

if not all([MEILI_HOST, MEILI_MASTER_KEY]):
    logger.error("Missing one or more environment variables: MEILI_HOST, MEILI_MASTER_KEY")
    exit(1)

try:
    meili_client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
    version = meili_client.get_version()
    logger.info(f"Meilisearch client initialized successfully. Server version: {version['pkgVersion']}")
except Exception as e:
    logger.error(f"Failed to initialize Meilisearch client: {e}")
    exit(1)


def meilisearch_query(index_name: str, query: str = None, filters: str = None, limit: int = 10, offset: int = 0) -> str:
    """
    Performs a search query against a specified Meilisearch index using the Meilisearch Python SDK.
    
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
        error_msg = f"Invalid index_name. Must be 'products' or 'users'. Got: {index_name}"
        logger.warning(error_msg)
        return json.dumps({"error": error_msg})

    try:
        index = meili_client.index(index_name)
        
        # All search options (except the main query string) go into this dictionary
        search_options = {
            "limit": limit,
            "offset": offset
        }
        if filters:
            search_options["filter"] = filters

        logger.info(f"Performing Meilisearch query on index '{index_name}' with query='{query}', options={search_options}")
        
        # Pass the query string as the first positional argument,
        # and search_options as the second (unpacked) argument.
        results = index.search(query, search_options) 

        return json.dumps({
            "hits": results.get("hits", []),
            "estimatedTotalHits": results.get("estimatedTotalHits", 0)
        }, indent=2)

    except meilisearch.errors.MeilisearchApiError as e:
        logger.error(f"Meilisearch API error during query: {e}")
        return json.dumps({
            "error": "Meilisearch API error",
            "code": e.code,
            "message": e.message,
            "type": e.type,
            "link": e.link
        })
    except Exception as e:
        logger.error(f"Unexpected error during Meilisearch query: {e}", exc_info=True)
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
        # Corrected method to get indexes and access results
        indexes_response = meili_client.get_indexes() 
        print("Available indexes:", [index.uid for index in indexes_response.results])
    except Exception as e:
        print("Failed to get indexes:", str(e))

    tests = [
        {"name": "Fuzzy product search", "params": {"index_name": "products", "query": "lapto"}},
        {"name": "Filter products", "params": {"index_name": "products", "filters": "category = 'Electronics' AND price < 500"}},
        {"name": "User search with typo", "params": {"index_name": "users", "query": "benaluru"}},
        {"name": "Invalid index", "params": {"index_name": "invalid_index", "query": "test"}},
        {"name": "Combined query", "params": {"index_name": "products", "query": "T-Shirt", "filters": "category = 'Apparel'"}},
        {"name": "Users from Bengaluru", "params": {"index_name": "users", "filters": "location = 'Bengaluru'"}}
    ]

    for test in tests:
        print(f"\nTest: {test['name']}")
        print(f"Params: {test['params']}")
        result = meilisearch_query(**test['params'])
        print("Result:", result)