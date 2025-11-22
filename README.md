# StockMaster - Inventory Management System

A full-stack Inventory Management System built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- **Authentication**: JWT-based login with HttpOnly cookies
- **Dashboard**: Real-time KPIs showing receipts, deliveries, and stock status
- **Product Management**: Complete product catalog with cost tracking
- **Stock Management**: View and update inventory levels directly
- **Receipts**: Track incoming stock with automatic inventory updates
- **Deliveries**: Manage outgoing shipments
- **Adjustments**: Make inventory corrections with audit trail
- **Multi-warehouse Support**: Manage multiple warehouses and locations
- **Complete Audit Trail**: All stock movements tracked in history

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Templates**: Jinja2 (server-side rendering)
- **Authentication**: JWT with passlib/bcrypt
- **Deployment**: Render.com ready

## Quick Start

### Running on Replit

1. Click the "Run" button
2. Access the app at the provided URL
3. Login with default credentials:
   - Email: `admin@example.com`
   - Password: `admin123`

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (copy `.env.example` to `.env`):
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/stockmaster
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=10080
   ```

3. Run the application:
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 5000 --reload
   ```

4. Access at `http://localhost:5000`

## Deploying to Render

For complete deployment instructions, see **[DEPLOYMENT.md](./DEPLOYMENT.md)**

### Quick Deploy Summary:

1. **Create PostgreSQL Database** on Render
2. **Create Web Service** connected to your GitHub repo
3. **Set Environment Variables**:
   - `DATABASE_URL` (from your Render PostgreSQL)
   - `SECRET_KEY` (generate with: `openssl rand -hex 32`)
   - `ALGORITHM=HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES=10080`
4. Deploy and access your application

**See [DEPLOYMENT.md](./DEPLOYMENT.md) for step-by-step guide with screenshots and troubleshooting.**

## Default Credentials

- **Email**: admin@example.com
- **Password**: admin123

**⚠️ Change these credentials immediately after first login in production!**

## Project Structure

```
.
├── app.py              # FastAPI application and routes
├── database.py         # Database configuration
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic schemas
├── auth.py             # Authentication (JWT, password hashing)
├── crud.py             # Database operations
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── stock.html
│   ├── products.html
│   ├── receipts_list.html
│   ├── deliveries_list.html
│   ├── adjustments_list.html
│   ├── warehouses.html
│   └── locations.html
├── static/
│   └── style.css       # Application styling
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment config
├── DEPLOYMENT.md       # Comprehensive deployment guide
└── README.md
```

## Database Schema

### Core Tables

- `users` - User accounts and authentication
- `warehouses` - Warehouse master data
- `locations` - Storage locations within warehouses
- `categories` - Product categories
- `products` - Product catalog with costs
- `stock_levels` - Current inventory levels per product/location
- `documents` - Stock operation headers (receipts, deliveries, transfers, adjustments)
- `document_lines` - Line items for documents
- `stock_moves` - Complete transaction ledger

## Key Features

### Stock Management
- View all products with current quantities and costs
- Update stock levels directly from the stock page
- Real-time inventory tracking across warehouses

### Operations
- **Receipts**: Record incoming stock with automatic inventory updates
- **Deliveries**: Process outgoing shipments
- **Adjustments**: Make manual inventory corrections

### Settings
- **Warehouses**: Manage multiple warehouse locations
- **Locations**: Define storage zones within warehouses

### Dashboard
- Total products count
- Low stock alerts
- Pending operations tracking
- Recent operations history

## Environment Variables

Required environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing secret (min 32 characters)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 10080 = 7 days)

See `.env.example` for template.

## Sample Data

The application includes comprehensive sample data:
- 3 warehouses (Main, North, South)
- 6 locations (3 zones per warehouse)
- 10 products across 4 categories
- Sample receipts and deliveries
- Pre-populated stock levels

Perfect for testing all features immediately after deployment!

## Security Features

- JWT tokens stored in HttpOnly cookies (XSS protection)
- Password hashing with bcrypt
- Role-based access control (ADMIN, MANAGER, STAFF)
- Database connection pooling with SSL support
- Environment-based configuration

## License

MIT License

---

**Need help deploying? Check out [DEPLOYMENT.md](./DEPLOYMENT.md) for the complete guide!**
