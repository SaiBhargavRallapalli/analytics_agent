from sqlalchemy import Column, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# Product Model
class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    brand = Column(String)
    price = Column(Numeric(10, 2)) # Numeric type for precise decimal representation

    # Relationship to Transaction - one product can be in many transactions
    transactions = relationship("Transaction", back_populates="product")

    def __repr__(self):
        return f"<Product(product_id='{self.product_id}', name='{self.name}', price={self.price})>"

# User Model
class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    location = Column(String)
    registration_date = Column(Date)

    # Relationship to Transaction - one user can make many transactions
    transactions = relationship("Transaction", back_populates="user")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', name='{self.name}', email='{self.email}')>"

# Transaction Model
class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    product_id = Column(String, ForeignKey("products.product_id"))
    quantity = Column(Numeric(10, 2))
    transaction_date = Column(Date)

    # Relationships to User and Product
    user = relationship("User", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")

    def __repr__(self):
        return (
            f"<Transaction(transaction_id='{self.transaction_id}', "
            f"user_id='{self.user_id}', product_id='{self.product_id}', "
            f"quantity={self.quantity}, date='{self.transaction_date}')>"
        )