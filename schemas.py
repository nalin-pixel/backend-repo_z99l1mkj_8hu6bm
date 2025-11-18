"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Class name is converted to lowercase for the collection name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Store "surf shirts" as products
class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in USD")
    category: str = Field("surf-shirts", description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
    sizes: List[str] = Field(default_factory=lambda: ["S","M","L","XL"], description="Available sizes")
    colors: List[str] = Field(default_factory=lambda: ["black","white","navy"], description="Available colors")
    image_url: Optional[str] = Field(None, description="Primary image URL")
    featured: bool = Field(False, description="Show as featured on homepage")
    stock_count: int = Field(50, ge=0, description="Quantity available")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product document id")
    title: str
    price: float
    size: str
    color: str
    quantity: int = Field(1, ge=1)
    image_url: Optional[str] = None

class Customer(BaseModel):
    name: str
    email: EmailStr
    address: str
    phone: Optional[str] = None

class Order(BaseModel):
    items: List[OrderItem]
    subtotal: float = Field(..., ge=0)
    shipping: float = Field(0, ge=0)
    total: float = Field(..., ge=0)
    customer: Customer
    status: str = Field("pending", description="Order status")
