from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    sku: str
    category_id: Optional[int] = None
    uom: str
    reorder_level: float = 0.0

class Product(BaseModel):
    id: int
    name: str
    sku: str
    uom: str
    reorder_level: float
    is_active: bool
    
    class Config:
        from_attributes = True

class DocumentLineCreate(BaseModel):
    product_id: int
    quantity: float

class ReceiptCreate(BaseModel):
    supplier_name: str
    to_warehouse_id: int
    to_location_id: int
    lines: List[DocumentLineCreate]
