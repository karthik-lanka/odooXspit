from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from datetime import datetime

def get_dashboard_kpis(db: Session):
    total_products = db.query(models.Product).filter(models.Product.is_active == True).count()
    
    low_stock_subquery = db.query(
        models.StockLevel.product_id,
        func.sum(models.StockLevel.quantity_on_hand).label('total_stock')
    ).group_by(models.StockLevel.product_id).subquery()
    
    low_stock_items = db.query(models.Product).join(
        low_stock_subquery,
        models.Product.id == low_stock_subquery.c.product_id
    ).filter(
        low_stock_subquery.c.total_stock < models.Product.reorder_level,
        models.Product.reorder_level > 0
    ).count()
    
    pending_receipts = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.RECEIPT,
        models.Document.status.notin_([models.DocStatus.DONE, models.DocStatus.CANCELED])
    ).count()
    
    total_receipts = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.RECEIPT
    ).count()
    
    late_receipts = 0
    
    pending_deliveries = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.DELIVERY,
        models.Document.status.notin_([models.DocStatus.DONE, models.DocStatus.CANCELED])
    ).count()
    
    total_deliveries = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.DELIVERY
    ).count()
    
    waiting_deliveries = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.DELIVERY,
        models.Document.status == models.DocStatus.WAITING
    ).count()
    
    internal_transfers = db.query(models.Document).filter(
        models.Document.doc_type == models.DocType.TRANSFER,
        models.Document.status.in_([models.DocStatus.WAITING, models.DocStatus.READY])
    ).count()
    
    return {
        "total_products": total_products,
        "low_stock_items": low_stock_items,
        "pending_receipts": pending_receipts,
        "total_receipts": total_receipts,
        "late_receipts": late_receipts,
        "pending_deliveries": pending_deliveries,
        "total_deliveries": total_deliveries,
        "waiting_deliveries": waiting_deliveries,
        "internal_transfers": internal_transfers
    }

def get_recent_operations(db: Session, limit: int = 10):
    return db.query(models.Document).order_by(
        models.Document.created_at.desc()
    ).limit(limit).all()

def validate_receipt(db: Session, document_id: int):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found")
    
    if document.status == models.DocStatus.DONE:
        raise ValueError("Document already validated")
    
    if document.status == models.DocStatus.CANCELED:
        raise ValueError("Cannot validate a canceled document")
    
    if not document.lines or len(document.lines) == 0:
        raise ValueError("Document has no line items")
    
    for line in document.lines:
        stock_level = db.query(models.StockLevel).filter(
            models.StockLevel.product_id == line.product_id,
            models.StockLevel.warehouse_id == document.to_warehouse_id,
            models.StockLevel.location_id == document.to_location_id
        ).first()
        
        if stock_level:
            stock_level.quantity_on_hand += line.quantity
        else:
            stock_level = models.StockLevel(
                product_id=line.product_id,
                warehouse_id=document.to_warehouse_id,
                location_id=document.to_location_id,
                quantity_on_hand=line.quantity
            )
            db.add(stock_level)
        
        stock_move = models.StockMove(
            product_id=line.product_id,
            from_warehouse_id=None,
            from_location_id=None,
            to_warehouse_id=document.to_warehouse_id,
            to_location_id=document.to_location_id,
            quantity=line.quantity,
            move_type=models.MoveType.RECEIPT,
            document_id=document.id
        )
        db.add(stock_move)
    
    document.status = models.DocStatus.DONE
    document.validated_at = datetime.utcnow()
    db.commit()
    
    return document

def get_stock_summary(db: Session, search: str = None):
    query = db.query(
        models.Product,
        func.sum(models.StockLevel.quantity_on_hand).label('total_quantity')
    ).join(
        models.StockLevel,
        models.Product.id == models.StockLevel.product_id,
        isouter=True
    ).group_by(models.Product.id).filter(
        models.Product.is_active == True
    )
    
    if search:
        query = query.filter(
            (models.Product.name.ilike(f"%{search}%")) |
            (models.Product.sku.ilike(f"%{search}%"))
        )
    
    results = query.all()
    
    stock_items = []
    for product, total_qty in results:
        stock_items.append({
            'product': product,
            'total_quantity': total_qty or 0.0
        })
    
    return stock_items

def validate_delivery(db: Session, document_id: int):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found")
    
    if document.status == models.DocStatus.DONE:
        raise ValueError("Document already validated")
    
    if document.status == models.DocStatus.CANCELED:
        raise ValueError("Cannot validate a canceled document")
    
    if not document.lines or len(document.lines) == 0:
        raise ValueError("Document has no line items")
    
    for line in document.lines:
        stock_level = db.query(models.StockLevel).filter(
            models.StockLevel.product_id == line.product_id,
            models.StockLevel.warehouse_id == document.from_warehouse_id,
            models.StockLevel.location_id == document.from_location_id
        ).first()
        
        if stock_level:
            if stock_level.quantity_on_hand < line.quantity:
                raise ValueError(f"Insufficient stock for product {line.product.name}")
            stock_level.quantity_on_hand -= line.quantity
        else:
            raise ValueError(f"No stock found for product {line.product.name}")
        
        stock_move = models.StockMove(
            product_id=line.product_id,
            from_warehouse_id=document.from_warehouse_id,
            from_location_id=document.from_location_id,
            to_warehouse_id=None,
            to_location_id=None,
            quantity=line.quantity,
            move_type=models.MoveType.DELIVERY,
            document_id=document.id
        )
        db.add(stock_move)
    
    document.status = models.DocStatus.DONE
    document.validated_at = datetime.utcnow()
    db.commit()
    
    return document

def validate_adjustment(db: Session, document_id: int):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found")
    
    if document.status == models.DocStatus.DONE:
        raise ValueError("Document already validated")
    
    if document.status == models.DocStatus.CANCELED:
        raise ValueError("Cannot validate a canceled document")
    
    if not document.lines or len(document.lines) == 0:
        raise ValueError("Document has no line items")
    
    for line in document.lines:
        stock_level = db.query(models.StockLevel).filter(
            models.StockLevel.product_id == line.product_id,
            models.StockLevel.warehouse_id == document.to_warehouse_id,
            models.StockLevel.location_id == document.to_location_id
        ).first()
        
        if stock_level:
            stock_level.quantity_on_hand += line.quantity
        else:
            stock_level = models.StockLevel(
                product_id=line.product_id,
                warehouse_id=document.to_warehouse_id,
                location_id=document.to_location_id,
                quantity_on_hand=line.quantity
            )
            db.add(stock_level)
        
        stock_move = models.StockMove(
            product_id=line.product_id,
            from_warehouse_id=None,
            from_location_id=None,
            to_warehouse_id=document.to_warehouse_id,
            to_location_id=document.to_location_id,
            quantity=line.quantity,
            move_type=models.MoveType.ADJUSTMENT,
            document_id=document.id
        )
        db.add(stock_move)
    
    document.status = models.DocStatus.DONE
    document.validated_at = datetime.utcnow()
    db.commit()
    
    return document

def update_stock_from_interface(db: Session, product_id: int, adjustment: float, user_id: int, reason: str = None):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise ValueError("Product not found")
    
    stock_level = db.query(models.StockLevel).filter(
        models.StockLevel.product_id == product_id
    ).first()
    
    if not stock_level:
        main_wh = db.query(models.Warehouse).first()
        if not main_wh:
            raise ValueError("No warehouse found")
        zone_a = db.query(models.Location).filter(models.Location.warehouse_id == main_wh.id).first()
        if not zone_a:
            raise ValueError("No location found")
        
        stock_level = models.StockLevel(
            product_id=product_id,
            warehouse_id=main_wh.id,
            location_id=zone_a.id,
            quantity_on_hand=0
        )
        db.add(stock_level)
        db.commit()
        db.refresh(stock_level)
    
    new_quantity = stock_level.quantity_on_hand + adjustment
    if new_quantity < 0:
        raise ValueError(f"Cannot reduce stock below 0. Current: {stock_level.quantity_on_hand}, Adjustment: {adjustment}")
    
    stock_level.quantity_on_hand = new_quantity
    
    move = models.StockMove(
        product_id=product_id,
        to_warehouse_id=stock_level.warehouse_id if adjustment > 0 else None,
        to_location_id=stock_level.location_id if adjustment > 0 else None,
        from_warehouse_id=stock_level.warehouse_id if adjustment < 0 else None,
        from_location_id=stock_level.location_id if adjustment < 0 else None,
        quantity=abs(adjustment),
        move_type=models.MoveType.ADJUSTMENT
    )
    db.add(move)
    
    db.commit()
    return stock_level
