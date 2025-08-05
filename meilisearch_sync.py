import os
from dotenv import load_dotenv
import meilisearch
import time
from database import SessionLocal
from models import Product, User

# Load environment variables
load_dotenv()

MEILI_HOST = os.getenv("MEILI_HOST")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY")

if not all([MEILI_HOST, MEILI_MASTER_KEY]):
    raise ValueError("Missing one or more environment variables: MEILI_HOST, MEILI_MASTER_KEY")

try:
    meili_client = meilisearch.Client(MEILI_HOST, MEILI_MASTER_KEY)
    meili_client.get_version() # Test connection
    print("Successfully connected to Meilisearch.")
except Exception as e:
    print(f"Failed to connect to Meilisearch: {e}")
    exit(1)

print("Starting Meilisearch configuration and data synchronization...")

# --- Products Index Configuration and Sync ---
products_index_uid = "products"
print(f"\nConfiguring and syncing '{products_index_uid}' index...")

# Define settings for products index
product_settings = {
    'filterableAttributes': ['category', 'price', 'brand'],
    'sortableAttributes': ['price'],
    'searchableAttributes': ['name', 'category', 'brand'],
    'displayedAttributes': ['product_id', 'name', 'category', 'brand', 'price']
}

try:
    products_index = meili_client.index(products_index_uid)
    update_task = products_index.update_settings(product_settings)
    meili_client.wait_for_task(update_task.task_uid)
    print(f"Meilisearch settings updated for '{products_index_uid}' index.")

    # Fetch products from PostgreSQL
    with SessionLocal() as db:
        products = db.query(Product).all()
        products_data = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "category": p.category,
                "brand": p.brand,
                "price": float(p.price) # Ensure price is a float for Meilisearch
            }
            for p in products
        ]

    # Add or update documents in Meilisearch
    if products_data:
        print(f"Adding {len(products_data)} product documents to Meilisearch.")
        add_docs_task = products_index.add_documents(products_data, primary_key="product_id")
        meili_client.wait_for_task(add_docs_task.task_uid)
        print(f"Successfully added {len(products_data)} products to '{products_index_uid}' index. Task UID: {add_docs_task.task_uid}")
    else:
        print(f"No products found in the database to add to '{products_index_uid}'.")

except Exception as e:
    print(f"Error syncing '{products_index_uid}' index: {e}")

# --- Users Index Configuration and Sync ---
users_index_uid = "users"
print(f"\nConfiguring and syncing '{users_index_uid}' index...")

# Define settings for users index
user_settings = {
    'filterableAttributes': ['location', 'registration_date', 'email'], # ADD 'email' HERE
    'sortableAttributes': ['registration_date'],
    'searchableAttributes': ['name', 'location', 'email'],
    'displayedAttributes': ['user_id', 'name', 'email', 'location', 'registration_date']
}

try:
    users_index = meili_client.index(users_index_uid)
    update_task = users_index.update_settings(user_settings)
    meili_client.wait_for_task(update_task.task_uid)
    print(f"Meilisearch settings updated for '{users_index_uid}' index.")

    # Fetch users from PostgreSQL
    with SessionLocal() as db:
        users = db.query(User).all()
        users_data = [
            {
                "user_id": u.user_id,
                "name": u.name,
                "email": u.email,
                "location": u.location,
                "registration_date": u.registration_date.isoformat() # Convert date to string
            }
            for u in users
        ]

    # Add or update documents in Meilisearch
    if users_data:
        print(f"Adding {len(users_data)} user documents to Meilisearch.")
        add_docs_task = users_index.add_documents(users_data, primary_key="user_id")
        meili_client.wait_for_task(add_docs_task.task_uid)
        print(f"Successfully added {len(users_data)} users to '{users_index_uid}' index. Task UID: {add_docs_task.task_uid}")
    else:
        print(f"No users found in the database to add to '{users_index_uid}'.")

except Exception as e:
    print(f"Error syncing '{users_index_uid}' index: {e}")

print("\nMeilisearch synchronization process complete.")