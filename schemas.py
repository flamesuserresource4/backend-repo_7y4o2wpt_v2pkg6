"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in INR")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
    stock_qty: int = Field(10, ge=0, description="Units available")
    image: Optional[str] = Field(None, description="Image URL")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product ObjectId as string")
    quantity: int = Field(..., ge=1, description="Quantity ordered")

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    shipping_address: str
    items: List[OrderItem]
    subtotal: float
    total: float
    status: str = Field("pending", description="Order status: pending, paid, shipped, delivered")
