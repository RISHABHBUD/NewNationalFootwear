from fastapi import APIRouter, Request, Form, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.auth import require_admin
from app.services.cloudinary_service import upload_image

router = APIRouter(prefix="/admin")


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    from app.models.order import PaymentStatus
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.order_status == OrderStatus.pending).count()
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_revenue = db.query(Order).filter(Order.payment_status == PaymentStatus.paid).all()
    revenue = sum(o.total_amount for o in total_revenue)
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request, "user": admin,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_products": total_products,
        "revenue": revenue,
        "recent_orders": recent_orders,
    })


# ── PRODUCTS ──────────────────────────────────────────────────────────────────

@router.get("/products", response_class=HTMLResponse)
def admin_products(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return templates.TemplateResponse("admin/products.html", {
        "request": request, "user": admin, "products": products,
    })


# IMPORTANT: /add must come BEFORE /{product_id} to avoid route conflict
@router.get("/products/add", response_class=HTMLResponse)
def add_product_page(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    return templates.TemplateResponse("admin/product_form.html", {
        "request": request, "user": admin, "product": None,
    })


@router.post("/products/add")
async def add_product(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    description: str = Form(None),
    category: str = Form(...),
    price: float = Form(...),
    sizes: str = Form(...),
    is_featured: str = Form("off"),
    images: list[UploadFile] = File(default=[]),
):
    admin = require_admin(request, db)
    size_list = [int(s.strip()) for s in sizes.split(",") if s.strip().isdigit()]
    image_urls = []
    for img in images:
        if img.filename:
            data = await img.read()
            try:
                url = upload_image(data, f"{name}_{img.filename}")
                image_urls.append(url)
            except Exception:
                pass  # skip failed uploads

    product = Product(
        name=name, description=description, category=category,
        price=price, sizes=size_list, images=image_urls,
        is_featured=(is_featured == "on"),
    )
    db.add(product)
    db.commit()
    return RedirectResponse("/admin/products", status_code=302)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
def edit_product_page(request: Request, product_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("admin/product_form.html", {
        "request": request, "user": admin, "product": product,
    })


@router.post("/products/{product_id}/edit")
async def edit_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    description: str = Form(None),
    category: str = Form(...),
    price: float = Form(...),
    sizes: str = Form(...),
    is_featured: str = Form("off"),
    remove_images: str = Form(""),   # comma-separated indices to remove
    images: list[UploadFile] = File(default=[]),
):
    admin = require_admin(request, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404)

    product.name = name
    product.description = description
    product.category = category
    product.price = price
    product.sizes = [int(s.strip()) for s in sizes.split(",") if s.strip().isdigit()]
    product.is_featured = (is_featured == "on")

    # Handle new image uploads
    current_images = list(product.images or [])
    for img in images:
        if img.filename:
            data = await img.read()
            try:
                url = upload_image(data, f"{name}_{img.filename}")
                current_images.append(url)
            except Exception:
                pass
    product.images = current_images
    db.commit()
    return RedirectResponse("/admin/products", status_code=302)


@router.post("/products/{product_id}/delete")
def delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    require_admin(request, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.is_active = False
        db.commit()
    return RedirectResponse("/admin/products", status_code=302)


# ── ORDERS ────────────────────────────────────────────────────────────────────

@router.get("/orders", response_class=HTMLResponse)
def admin_orders(
    request: Request,
    db: Session = Depends(get_db),
    status: str = Query(None),
):
    admin = require_admin(request, db)
    q = db.query(Order).order_by(Order.created_at.desc())
    if status:
        try:
            q = q.filter(Order.order_status == OrderStatus(status))
        except ValueError:
            pass
    orders = q.all()
    return templates.TemplateResponse("admin/orders.html", {
        "request": request, "user": admin,
        "orders": orders, "status_filter": status,
        "statuses": [s.value for s in OrderStatus],
    })


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def admin_order_detail(request: Request, order_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("admin/order_detail.html", {
        "request": request, "user": admin, "order": order,
        "statuses": [s.value for s in OrderStatus],
    })


@router.post("/orders/{order_id}/update-status")
def update_order_status(
    request: Request, order_id: int,
    db: Session = Depends(get_db),
    order_status: str = Form(...),
):
    require_admin(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        try:
            order.order_status = OrderStatus(order_status)
            db.commit()
        except ValueError:
            pass
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=302)
