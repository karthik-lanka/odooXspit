# StockMaster - Inventory Management System

## Overview

StockMaster is a full-stack Inventory Management System built with FastAPI and PostgreSQL. It provides comprehensive inventory tracking across multiple warehouses and locations, with features for managing products, stock receipts, deliveries, transfers, and complete transaction history. The system uses server-side rendering with Jinja2 templates and implements JWT-based authentication with HttpOnly cookies for security.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **FastAPI** serves as the web framework, handling both API endpoints and server-side rendered pages
- **Uvicorn/Gunicorn** used as ASGI server for production deployment
- Single-repo structure designed to run identically on Replit and Render

### Authentication & Authorization
- **JWT tokens** stored in HttpOnly cookies for session management
- **Passlib with bcrypt** for password hashing
- Role-based access control with three user roles: ADMIN, MANAGER, and STAFF
- Token expiration set to 1 day by default
- Custom dependency injection (`get_current_user`) validates tokens on protected routes

### Database Architecture
- **PostgreSQL** as the primary relational database
- **SQLAlchemy ORM** for database operations with declarative models
- Connection string loaded from `DATABASE_URL` environment variable
- SSL mode automatically configured for external databases (Render, etc.)
- Connection pooling with pre-ping and 300-second recycle time

### Data Model Structure
The system uses a multi-entity relational model:
- **Users**: Authentication and role management
- **Warehouses & Locations**: Multi-warehouse support with hierarchical location tracking
- **Products**: Core inventory items with SKU, category, UoM, and reorder levels
- **Categories**: Product categorization (referenced but not fully shown in snippets)
- **Documents**: Master transaction records for receipts, deliveries, transfers, and adjustments
- **DocumentLines**: Line items within each document
- **StockLevels**: Current inventory quantities per product/warehouse/location
- **StockMoves**: Complete transaction ledger tracking all inventory movements

### Document Workflow System
- Documents progress through statuses: DRAFT → WAITING → READY → DONE (or CANCELED)
- Four document types: RECEIPT (incoming), DELIVERY (outgoing), TRANSFER (internal), ADJUSTMENT (corrections)
- Receipt validation automatically creates stock moves and updates stock levels
- Each stock move records source/destination warehouse and location for full traceability

### Frontend Architecture
- **Jinja2** template engine for server-side HTML rendering
- Static files (CSS, JS) served via FastAPI's StaticFiles mount
- Responsive layout with sidebar navigation
- Dashboard displays real-time KPIs calculated from database queries

### Business Logic Layer
- **crud.py** contains core database operations:
  - Dashboard KPI calculations (total products, low stock alerts, pending operations)
  - Receipt validation logic that creates stock moves and updates inventory
  - Recent operations queries
- Aggregate queries using SQLAlchemy functions for performance (e.g., low stock subqueries)

### Configuration Management
- **python-dotenv** loads environment variables from `.env` file
- Required environment variables:
  - `DATABASE_URL`: PostgreSQL connection string
  - `SECRET_KEY`: JWT signing secret
- `.env.example` provided as template (no secrets committed)

### Deployment Strategy
- Code designed to run identically on Replit (development) and Render (production)
- Database initialization creates default admin user and main warehouse on first run
- SSL configuration automatically applied for Render-hosted databases
- Single web service deployment model (no separate frontend/backend)

### Security Considerations
- Passwords never stored in plain text (bcrypt hashed)
- JWT tokens stored in HttpOnly cookies to prevent XSS attacks
- Token validation on all protected routes
- Database connection uses SSL for production environments
- SECRET_KEY must be changed from default in production