from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.order import Order
from app.auth import get_current_user

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    featured = db.query(Product).filter(
        Product.is_active == True, Product.is_featured == True
    ).limit(8).all()
    sports = db.query(Product).filter(
        Product.is_active == True, Product.category == "sports"
    ).limit(8).all()
    sneakers = db.query(Product).filter(
        Product.is_active == True, Product.category == "sneakers"
    ).limit(8).all()
    return templates.TemplateResponse("store/home.html", {
        "request": request, "user": user,
        "featured": featured, "sports": sports, "sneakers": sneakers,
    })


@router.get("/products", response_class=HTMLResponse)
def product_list(
    request: Request,
    db: Session = Depends(get_db),
    category: str = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1),
):
    user = get_current_user(request, db)
    PAGE_SIZE = 12
    q = db.query(Product).filter(Product.is_active == True)
    if category:
        q = q.filter(Product.category == category)
    if sort == "price_asc":
        q = q.order_by(Product.price.asc())
    elif sort == "price_desc":
        q = q.order_by(Product.price.desc())
    else:
        q = q.order_by(Product.created_at.desc())

    total = q.count()
    products = q.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    return templates.TemplateResponse("store/product_list.html", {
        "request": request, "user": user,
        "products": products, "category": category,
        "sort": sort, "page": page, "total_pages": total_pages,
    })


@router.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    product = db.query(Product).filter(
        Product.id == product_id, Product.is_active == True
    ).first()
    if not product:
        return templates.TemplateResponse("store/404.html", {"request": request}, status_code=404)
    related = db.query(Product).filter(
        Product.is_active == True,
        Product.category == product.category,
        Product.id != product.id,
    ).limit(4).all()
    return templates.TemplateResponse("store/product_detail.html", {
        "request": request, "user": user,
        "product": product, "related": related,
    })


@router.get("/account", response_class=HTMLResponse)
def account(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("store/account.html", {
        "request": request, "user": user, "orders": orders,
    })
