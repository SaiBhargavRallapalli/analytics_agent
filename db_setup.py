import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import OperationalError, ProgrammingError
import psycopg2 
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file or environment variables.")

# --- Database Creation (Handle if not exists) ---
def create_database_if_not_exists(db_url):
    parsed_url = urlparse(db_url)
    db_name = parsed_url.path.lstrip('/')
    
    # Connection details for connecting to the default 'postgres' database
    # to create the target database.
    conn_params = {
        "host": parsed_url.hostname,
        "port": parsed_url.port,
        "user": parsed_url.username,
        "password": parsed_url.password,
        "dbname": "hybrid_analytics_db"
    }

    print(f"Attempting to ensure database '{db_name}' exists...")
    conn = None # Initialize conn to None
    try:
        # First, try to connect to the target database directly.
        # If successful, it means the database already exists.
        test_conn = psycopg2.connect(db_url)
        test_conn.close()
        print(f"Database '{db_name}' already exists.")
        return # Database exists, nothing more to do
    except psycopg2.OperationalError:
        print(f"Database '{db_name}' does not exist. Attempting to create it...")
        # If connecting to the target DB failed, try to create it via 'postgres' DB
        try:
            # Establish a connection in autocommit mode explicitly for CREATE DATABASE
            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database already exists using a query
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f'CREATE DATABASE "{db_name}" ENCODING \'UTF8\' TEMPLATE template0')
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists (checked before creation).")
            
            cursor.close()
        except psycopg2.Error as e:
            print(f"Error creating database '{db_name}': {e}")
            raise # Re-raise the exception after printing
        finally:
            if conn:
                conn.close() # Ensure the connection is closed
    except Exception as e:
        print(f"An unexpected error occurred during database existence check: {e}")
        raise


# --- SQLAlchemy Setup for Table Creation (Remains the same) ---
Base = declarative_base()
engine = create_engine(DATABASE_URL)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    location = Column(String)
    registration_date = Column(Date)

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', name='{self.name}')>"

class Product(Base):
    __tablename__ = 'products'
    product_id = Column(String, primary_key=True)
    name = Column(String)
    category = Column(String)
    brand = Column(String)
    price = Column(Numeric)

    def __repr__(self):
        return f"<Product(product_id='{self.product_id}', name='{self.name}')>"

class Transaction(Base):
    __tablename__ = 'transactions'
    order_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    product_id = Column(String, ForeignKey('products.product_id'))
    amount = Column(Numeric)
    timestamp = Column(DateTime)
    status = Column(String)

    def __repr__(self):
        return f"<Transaction(order_id='{self.order_id}', amount={self.amount})>"

# --- Main execution (Remains the same) ---
if __name__ == "__main__":
    print("Starting database setup...")
    
    # 1. Ensure the database exists
    try:
        create_database_if_not_exists(DATABASE_URL)
    except Exception as e:
        print(f"Failed to ensure database existence: {e}")
        exit(1)

    # 2. Create tables
    print("Creating tables...")
    try:
        Base.metadata.create_all(engine)
        print("Tables created or already exist.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        exit(1)

    print("Database setup complete.")