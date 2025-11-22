from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uvicorn

from database import engine, get_db, Base
import models
import schemas
import auth
import crud

app = FastAPI(title="StockMaster")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    admin_user = db.query(models.User).filter(models.User.email == "admin@example.com").first()
    if not admin_user:
        admin_user = models.User(
            name="Admin User",
            email="admin@example.com",
            password_hash=auth.get_password_hash("admin123"),
            role=models.UserRole.ADMIN
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
    
    if db.query(models.Warehouse).count() == 0:
        warehouses_data = [
            {"name": "Main Warehouse", "code": "WH/Stock", "address": "123 Main Street, Mumbai"},
            {"name": "North Warehouse", "code": "WH/North", "address": "456 North Avenue, Delhi"},
            {"name": "South Warehouse", "code": "WH/South", "address": "789 South Road, Bangalore"}
        ]
        
        warehouses = []
        for wh_data in warehouses_data:
            wh = models.Warehouse(**wh_data)
            db.add(wh)
            warehouses.append(wh)
        db.commit()
        
        for wh in warehouses:
            db.refresh(wh)
            locations_data = [
                {"warehouse_id": wh.id, "name": "Zone A", "code": "A"},
                {"warehouse_id": wh.id, "name": "Zone B", "code": "B"},
                {"warehouse_id": wh.id, "name": "Zone C", "code": "C"}
            ]
            for loc_data in locations_data:
                loc = models.Location(**loc_data)
                db.add(loc)
        db.commit()
    
    if db.query(models.Category).count() == 0:
        categories = ["Electronics", "Furniture", "Office Supplies", "Hardware"]
        for cat_name in categories:
            cat = models.Category(name=cat_name)
            db.add(cat)
        db.commit()
    
    if db.query(models.Product).count() == 0:
        category_map = {cat.name: cat.id for cat in db.query(models.Category).all()}
        
        products_data = [
            {"name": "Desk", "sku": "DESK001", "category_id": category_map["Furniture"], "uom": "Units", "cost": 3000.0, "reorder_level": 10},
            {"name": "Office Table", "sku": "TABLE001", "category_id": category_map["Furniture"], "uom": "Units", "cost": 3000.0, "reorder_level": 5},
            {"name": "Office Chair", "sku": "CHAIR001", "category_id": category_map["Furniture"], "uom": "Units", "cost": 1500.0, "reorder_level": 15},
            {"name": "Laptop", "sku": "LAP001", "category_id": category_map["Electronics"], "uom": "Units", "cost": 45000.0, "reorder_level": 5},
            {"name": "Monitor", "sku": "MON001", "category_id": category_map["Electronics"], "uom": "Units", "cost": 12000.0, "reorder_level": 8},
            {"name": "Keyboard", "sku": "KEY001", "category_id": category_map["Electronics"], "uom": "Units", "cost": 800.0, "reorder_level": 20},
            {"name": "Mouse", "sku": "MOU001", "category_id": category_map["Electronics"], "uom": "Units", "cost": 400.0, "reorder_level": 25},
            {"name": "Pen", "sku": "PEN001", "category_id": category_map["Office Supplies"], "uom": "Box", "cost": 50.0, "reorder_level": 100},
            {"name": "Paper A4", "sku": "PAP001", "category_id": category_map["Office Supplies"], "uom": "Ream", "cost": 200.0, "reorder_level": 50},
            {"name": "Stapler", "sku": "STA001", "category_id": category_map["Office Supplies"], "uom": "Units", "cost": 150.0, "reorder_level": 30}
        ]
        
        products = []
        for prod_data in products_data:
            prod = models.Product(**prod_data)
            db.add(prod)
            products.append(prod)
        db.commit()
        
        for prod in products:
            db.refresh(prod)
        
        main_wh = db.query(models.Warehouse).filter(models.Warehouse.code == "WH/Stock").first()
        zone_a = db.query(models.Location).filter(
            models.Location.warehouse_id == main_wh.id,
            models.Location.code == "A"
        ).first()
        
        receipt = models.Document(
            doc_type=models.DocType.RECEIPT,
            status=models.DocStatus.DONE,
            supplier_name="Aman Sharma",
            to_warehouse_id=main_wh.id,
            to_location_id=zone_a.id,
            created_by=admin_user.id,
            validated_at=datetime.utcnow()
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        
        receipt_lines = [
            {"document_id": receipt.id, "product_id": products[0].id, "quantity": 50},
            {"document_id": receipt.id, "product_id": products[1].id, "quantity": 50},
            {"document_id": receipt.id, "product_id": products[2].id, "quantity": 100},
            {"document_id": receipt.id, "product_id": products[3].id, "quantity": 30},
            {"document_id": receipt.id, "product_id": products[4].id, "quantity": 40}
        ]
        
        for line_data in receipt_lines:
            line = models.DocumentLine(**line_data)
            db.add(line)
            
            stock = models.StockLevel(
                product_id=line_data["product_id"],
                warehouse_id=main_wh.id,
                location_id=zone_a.id,
                quantity_on_hand=line_data["quantity"]
            )
            db.add(stock)
            
            move = models.StockMove(
                product_id=line_data["product_id"],
                to_warehouse_id=main_wh.id,
                to_location_id=zone_a.id,
                quantity=line_data["quantity"],
                move_type=models.MoveType.RECEIPT,
                document_id=receipt.id
            )
            db.add(move)
        
        db.commit()
        
        pending_receipt = models.Document(
            doc_type=models.DocType.RECEIPT,
            status=models.DocStatus.READY,
            supplier_name="Vendor ABC",
            to_warehouse_id=main_wh.id,
            to_location_id=zone_a.id,
            created_by=admin_user.id
        )
        db.add(pending_receipt)
        db.commit()
        db.refresh(pending_receipt)
        
        pending_lines = [
            {"document_id": pending_receipt.id, "product_id": products[5].id, "quantity": 50},
            {"document_id": pending_receipt.id, "product_id": products[6].id, "quantity": 60}
        ]
        
        for line_data in pending_lines:
            line = models.DocumentLine(**line_data)
            db.add(line)
        db.commit()
        
        delivery = models.Document(
            doc_type=models.DocType.DELIVERY,
            status=models.DocStatus.READY,
            customer_name="Aman Sharma",
            from_warehouse_id=main_wh.id,
            from_location_id=zone_a.id,
            created_by=admin_user.id
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        
        delivery_lines = [
            {"document_id": delivery.id, "product_id": products[0].id, "quantity": 5},
            {"document_id": delivery.id, "product_id": products[2].id, "quantity": 10}
        ]
        
        for line_data in delivery_lines:
            line = models.DocumentLine(**line_data)
            db.add(line)
        db.commit()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"}
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400
    )
    return response

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})

@app.post("/signup")
async def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Passwords do not match"}
        )
    
    if len(password) < 6:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Password must be at least 6 characters"}
        )
    
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Email already registered"}
        )
    
    hashed_password = auth.get_password_hash(password)
    new_user = models.User(
        name=name,
        email=email,
        password_hash=hashed_password,
        role=models.UserRole.STAFF
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth.create_access_token(data={"sub": new_user.email})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400
    )
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    kpis = crud.get_dashboard_kpis(db)
    recent_ops = crud.get_recent_operations(db)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "kpis": kpis,
            "recent_operations": recent_ops
        }
    )

@app.get("/products", response_class=HTMLResponse)
async def products_page(
    request: Request,
    search: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(models.Product.is_active == True)
    
    if search:
        query = query.filter(
            (models.Product.name.ilike(f"%{search}%")) |
            (models.Product.sku.ilike(f"%{search}%"))
        )
    
    products = query.all()
    categories = db.query(models.Category).all()
    
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "user": current_user,
            "products": products,
            "categories": categories,
            "search": search or ""
        }
    )

@app.post("/products")
async def create_product(
    request: Request,
    name: str = Form(...),
    sku: str = Form(...),
    category_id: Optional[int] = Form(None),
    uom: str = Form(...),
    cost: float = Form(0.0),
    reorder_level: float = Form(0.0),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.Product).filter(models.Product.sku == sku).first()
    if existing:
        return RedirectResponse(url="/products?error=SKU already exists", status_code=302)
    
    product = models.Product(
        name=name,
        sku=sku,
        category_id=category_id,
        uom=uom,
        cost=cost,
        reorder_level=reorder_level
    )
    db.add(product)
    db.commit()
    
    return RedirectResponse(url="/products", status_code=302)

@app.get("/stock", response_class=HTMLResponse)
async def stock_page(
    request: Request,
    search: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    stock_items = crud.get_stock_summary(db, search)
    
    return templates.TemplateResponse(
        "stock.html",
        {
            "request": request,
            "user": current_user,
            "stock_items": stock_items,
            "search": search or ""
        }
    )

@app.post("/stock/update")
async def update_stock(
    request: Request,
    product_id: int = Form(...),
    adjustment: float = Form(...),
    reason: Optional[str] = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        crud.update_stock_from_interface(db, product_id, adjustment, current_user.id, reason)
        return RedirectResponse(url="/stock", status_code=302)
    except ValueError as e:
        return RedirectResponse(url=f"/stock?error={str(e)}", status_code=302)

@app.get("/operations/receipts", response_class=HTMLResponse)
async def receipts_list(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    receipts = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.RECEIPT
    ).order_by(models.Document.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "receipts_list.html",
        {
            "request": request,
            "user": current_user,
            "receipts": receipts
        }
    )

@app.get("/operations/receipts/new", response_class=HTMLResponse)
async def receipt_form(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    warehouses = db.query(models.Warehouse).all()
    locations = db.query(models.Location).all()
    products = db.query(models.Product).filter(models.Product.is_active == True).all()
    
    return templates.TemplateResponse(
        "receipt_form.html",
        {
            "request": request,
            "user": current_user,
            "warehouses": warehouses,
            "locations": locations,
            "products": products
        }
    )

@app.post("/operations/receipts/new")
async def create_receipt(
    request: Request,
    supplier_name: str = Form(...),
    to_warehouse_id: int = Form(...),
    to_location_id: int = Form(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    
    document = models.Document(
        doc_type=models.DocType.RECEIPT,
        status=models.DocStatus.READY,
        supplier_name=supplier_name,
        to_warehouse_id=to_warehouse_id,
        to_location_id=to_location_id,
        created_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    product_ids = form_data.getlist("product_id[]")
    quantities = form_data.getlist("quantity[]")
    
    for product_id, quantity in zip(product_ids, quantities):
        if product_id and quantity:
            line = models.DocumentLine(
                document_id=document.id,
                product_id=int(product_id),
                quantity=float(quantity)
            )
            db.add(line)
    
    db.commit()
    
    return RedirectResponse(url="/operations/receipts", status_code=302)

@app.post("/operations/receipts/{receipt_id}/validate")
async def validate_receipt(
    receipt_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        crud.validate_receipt(db, receipt_id)
        return RedirectResponse(url="/operations/receipts", status_code=302)
    except ValueError as e:
        return RedirectResponse(url=f"/operations/receipts?error={str(e)}", status_code=302)

@app.get("/operations/deliveries", response_class=HTMLResponse)
async def deliveries_list(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    deliveries = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.DELIVERY
    ).order_by(models.Document.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "deliveries_list.html",
        {
            "request": request,
            "user": current_user,
            "deliveries": deliveries
        }
    )

@app.get("/operations/deliveries/new", response_class=HTMLResponse)
async def delivery_form(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    warehouses = db.query(models.Warehouse).all()
    locations = db.query(models.Location).all()
    products = db.query(models.Product).filter(models.Product.is_active == True).all()
    
    return templates.TemplateResponse(
        "delivery_form.html",
        {
            "request": request,
            "user": current_user,
            "warehouses": warehouses,
            "locations": locations,
            "products": products
        }
    )

@app.post("/operations/deliveries/new")
async def create_delivery(
    request: Request,
    customer_name: str = Form(...),
    from_warehouse_id: int = Form(...),
    from_location_id: int = Form(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    
    document = models.Document(
        doc_type=models.DocType.DELIVERY,
        status=models.DocStatus.READY,
        customer_name=customer_name,
        from_warehouse_id=from_warehouse_id,
        from_location_id=from_location_id,
        created_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    product_ids = form_data.getlist("product_id[]")
    quantities = form_data.getlist("quantity[]")
    
    for product_id, quantity in zip(product_ids, quantities):
        if product_id and quantity:
            line = models.DocumentLine(
                document_id=document.id,
                product_id=int(product_id),
                quantity=float(quantity)
            )
            db.add(line)
    
    db.commit()
    
    return RedirectResponse(url="/operations/deliveries", status_code=302)

@app.post("/operations/deliveries/{delivery_id}/validate")
async def validate_delivery(
    delivery_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        crud.validate_delivery(db, delivery_id)
        return RedirectResponse(url="/operations/deliveries", status_code=302)
    except ValueError as e:
        return RedirectResponse(url=f"/operations/deliveries?error={str(e)}", status_code=302)

@app.get("/operations/adjustments", response_class=HTMLResponse)
async def adjustments_list(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    adjustments = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.ADJUSTMENT
    ).order_by(models.Document.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "adjustments_list.html",
        {
            "request": request,
            "user": current_user,
            "adjustments": adjustments
        }
    )

@app.get("/operations/adjustments/new", response_class=HTMLResponse)
async def adjustment_form(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    warehouses = db.query(models.Warehouse).all()
    locations = db.query(models.Location).all()
    products = db.query(models.Product).filter(models.Product.is_active == True).all()
    
    return templates.TemplateResponse(
        "adjustment_form.html",
        {
            "request": request,
            "user": current_user,
            "warehouses": warehouses,
            "locations": locations,
            "products": products
        }
    )

@app.post("/operations/adjustments/new")
async def create_adjustment(
    request: Request,
    to_warehouse_id: int = Form(...),
    to_location_id: int = Form(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    
    document = models.Document(
        doc_type=models.DocType.ADJUSTMENT,
        status=models.DocStatus.READY,
        to_warehouse_id=to_warehouse_id,
        to_location_id=to_location_id,
        created_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    product_ids = form_data.getlist("product_id[]")
    quantities = form_data.getlist("quantity[]")
    
    for product_id, quantity in zip(product_ids, quantities):
        if product_id and quantity:
            line = models.DocumentLine(
                document_id=document.id,
                product_id=int(product_id),
                quantity=float(quantity)
            )
            db.add(line)
    
    db.commit()
    
    return RedirectResponse(url="/operations/adjustments", status_code=302)

@app.post("/operations/adjustments/{adjustment_id}/validate")
async def validate_adjustment(
    adjustment_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        crud.validate_adjustment(db, adjustment_id)
        return RedirectResponse(url="/operations/adjustments", status_code=302)
    except ValueError as e:
        return RedirectResponse(url=f"/operations/adjustments?error={str(e)}", status_code=302)

@app.get("/settings/warehouses", response_class=HTMLResponse)
async def warehouses_page(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    warehouses = db.query(models.Warehouse).all()
    
    return templates.TemplateResponse(
        "warehouses.html",
        {
            "request": request,
            "user": current_user,
            "warehouses": warehouses
        }
    )

@app.post("/settings/warehouses")
async def create_warehouse(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    address: Optional[str] = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.Warehouse).filter(models.Warehouse.code == code).first()
    if existing:
        return RedirectResponse(url="/settings/warehouses?error=Code already exists", status_code=302)
    
    warehouse = models.Warehouse(
        name=name,
        code=code,
        address=address
    )
    db.add(warehouse)
    db.commit()
    
    return RedirectResponse(url="/settings/warehouses", status_code=302)

@app.get("/settings/locations", response_class=HTMLResponse)
async def locations_page(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    warehouses = db.query(models.Warehouse).all()
    locations = db.query(models.Location).all()
    
    return templates.TemplateResponse(
        "locations.html",
        {
            "request": request,
            "user": current_user,
            "warehouses": warehouses,
            "locations": locations
        }
    )

@app.post("/settings/locations")
async def create_location(
    request: Request,
    warehouse_id: int = Form(...),
    name: str = Form(...),
    code: str = Form(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.Location).filter(
        models.Location.warehouse_id == warehouse_id,
        models.Location.code == code
    ).first()
    if existing:
        return RedirectResponse(url="/settings/locations?error=Code already exists in this warehouse", status_code=302)
    
    location = models.Location(
        warehouse_id=warehouse_id,
        name=name,
        code=code
    )
    db.add(location)
    db.commit()
    
    return RedirectResponse(url="/settings/locations", status_code=302)

@app.get("/operations/moves", response_class=HTMLResponse)
async def moves_history(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    moves = db.query(models.StockMove).order_by(
        models.StockMove.created_at.desc()
    ).limit(100).all()
    
    return templates.TemplateResponse(
        "moves_history.html",
        {
            "request": request,
            "user": current_user,
            "moves": moves
        }
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
