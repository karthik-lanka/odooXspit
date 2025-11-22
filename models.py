from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"

class DocType(str, enum.Enum):
    RECEIPT = "RECEIPT"
    DELIVERY = "DELIVERY"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"

class DocStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    WAITING = "WAITING"
    READY = "READY"
    DONE = "DONE"
    CANCELED = "CANCELED"

class MoveType(str, enum.Enum):
    RECEIPT = "RECEIPT"
    DELIVERY = "DELIVERY"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STAFF)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = relationship("Document", back_populates="creator")

class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    locations = relationship("Location", back_populates="warehouse")

class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint('warehouse_id', 'code', name='uq_warehouse_location_code'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    warehouse = relationship("Warehouse", back_populates="locations")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False, unique=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    uom = Column(String, nullable=False)
    cost = Column(Float, default=0.0)
    reorder_level = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("Category", back_populates="products")
    stock_levels = relationship("StockLevel", back_populates="product")

class StockLevel(Base):
    __tablename__ = "stock_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity_on_hand = Column(Float, default=0.0)
    
    product = relationship("Product", back_populates="stock_levels")
    warehouse = relationship("Warehouse")
    location = relationship("Location")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(SQLEnum(DocType), nullable=False)
    status = Column(SQLEnum(DocStatus), default=DocStatus.DRAFT)
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"))
    supplier_name = Column(String)
    customer_name = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validated_at = Column(DateTime)
    
    creator = relationship("User", back_populates="documents")
    lines = relationship("DocumentLine", back_populates="document", cascade="all, delete-orphan")

class DocumentLine(Base):
    __tablename__ = "document_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    
    document = relationship("Document", back_populates="lines")
    product = relationship("Product")

class StockMove(Base):
    __tablename__ = "stock_moves"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"))
    quantity = Column(Float, nullable=False)
    move_type = Column(SQLEnum(MoveType), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    document = relationship("Document")
