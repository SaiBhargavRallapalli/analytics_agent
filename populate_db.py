import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
import uuid
import random
from decimal import Decimal

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file or environment variables.")

# Import model classes from db_setup.py
from db_setup import Base, User, Product, Transaction, engine

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

def generate_users(num_users=200):
    users = []
    locations = ["Bengaluru", "Mumbai", "Delhi", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad"]
    start_date = date(2021, 1, 1)

    print(f"Generating {num_users} users...")
    for i in range(num_users):
        user_id = str(uuid.uuid4())[:8]
        name = f"User{i+1}"
        email = f"user{i+1}@example.com"
        location = random.choices(locations, weights=[20, 20, 20, 10, 10, 10, 5, 5])[0]
        reg_date = start_date + timedelta(days=random.randint(0, (date.today() - start_date).days))

        user = User(
            user_id=user_id,
            name=name,
            email=email,
            location=location,
            registration_date=reg_date
        )
        users.append(user)
    return users

def generate_products(num_products=100):
    products = []
    sample_products = [
        ("iPhone 14", "Electronics", "Apple"),
        ("Samsung Galaxy S22", "Electronics", "Samsung"),
        ("MacBook Air", "Electronics", "Apple"),
        ("Kindle Paperwhite", "Books", "Amazon"),
        ("Adidas Running Shoes", "Apparel", "Adidas"),
        ("Sony WH-1000XM5", "Electronics", "Sony"),
        ("Levi's Jeans", "Apparel", "Levi's"),
        ("iPad Pro", "Electronics", "Apple"),
        ("Dell XPS 13", "Electronics", "Dell"),
        ("Canon DSLR", "Electronics", "Canon"),
        ("Samsung Refrigerator", "Home Goods", "Samsung"),
        ("LG Washing Machine", "Home Goods", "LG"),
        ("Apple Watch Series 8", "Electronics", "Apple"),
        ("Nike Shoes", "Apparel", "Nike"),
        ("HP Pavilion", "Electronics", "HP"),
        ("Asus ROG Phone", "Electronics", "Asus"),
    ]

    print(f"Generating {num_products} products...")
    for i in range(num_products):
        product_id = str(uuid.uuid4())[:8]
        if i < len(sample_products):
            name, category, brand = sample_products[i]
        else:
            name = f"Product{i+1}"
            category = random.choice(["Electronics", "Books", "Apparel", "Home Goods", "Groceries", "Sports"])
            brand = random.choice(["BrandX", "BrandY", "BrandZ", "BrandA", "BrandB"])
        price = round(random.uniform(100.0, 1500.0), 2)

        product = Product(
            product_id=product_id,
            name=name,
            category=category,
            brand=brand,
            price=price
        )
        products.append(product)
    return products

def generate_transactions(users, products, num_transactions=1000):
    transactions = []
    status_options = ["completed", "pending", "cancelled"]
    now = datetime.now()
    start_timestamp = now - timedelta(days=365)

    print(f"Generating {num_transactions} transactions...")
    for i in range(num_transactions):
        order_id = str(uuid.uuid4())[:8]

        # Biases to ensure useful patterns
        if random.random() < 0.02:
            product = next((p for p in products if "iPhone 14" in p.name), random.choice(products))
            user = random.choice([u for u in users if u.location == "Delhi"])
            timestamp = now.replace(month=((now.month - 3) % 12 or 12), day=random.randint(1, 28))
        elif random.random() < 0.02:
            product = next((p for p in products if "Samsung" in p.name), random.choice(products))
            user = random.choice(users)
            timestamp = start_timestamp + timedelta(days=random.randint(0, 365))
        else:
            user = random.choice(users)
            product = random.choice(products)
            delta_seconds = (now - start_timestamp).total_seconds()
            timestamp = start_timestamp + timedelta(seconds=random.randint(0, int(delta_seconds)))

        quantity = random.randint(1, 3)
        random_factor = Decimal(str(round(random.uniform(0.8, 1.2), 2)))
        amount = Decimal(str(product.price)) * random_factor * quantity
        status = random.choices(status_options, weights=[0.85, 0.1, 0.05])[0]

        transaction = Transaction(
            order_id=order_id,
            user_id=user.user_id,
            product_id=product.product_id,
            amount=round(amount, 2),
            timestamp=timestamp,
            status=status
        )
        transactions.append(transaction)
    return transactions

if __name__ == "__main__":
    print("Populating database with dummy data...")
    try:
        # Clear existing data before populating to avoid duplicates on re-run
        session.query(Transaction).delete()
        session.query(User).delete()
        session.query(Product).delete()
        session.commit()
        print("Existing data cleared (if any).")

        users_data = generate_users(200)
        products_data = generate_products(100)
        session.add_all(users_data)
        session.add_all(products_data)
        session.commit()
        print("Users and Products added.")

        transactions_data = generate_transactions(users_data, products_data, 1000)
        session.add_all(transactions_data)
        session.commit()
        print("Transactions added.")

        print("Database population complete.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred during database population: {e}")
    finally:
        session.close()
