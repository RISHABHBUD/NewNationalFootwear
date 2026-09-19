import json
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.order import Order, OrderItem, PaymentMethod, PaymentStatus, OrderStatus
from app.auth import get_current_user
from app.config import settings
# from app.services import razorpay_service  # BYPASSED — uncomment when Razorpay creds are ready
from app.services import razorpay_service, pdf_service, email_service

router = APIRouter()


@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("store/checkout.html", {
        "request": request, "user": user,
        "delivery_charge": settings.DELIVERY_CHARGE,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    })


@router.post("/checkout/create-order")
async def create_order(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(None),
    address_line: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    pincode: str = Form(...),
    payment_method: str = Form(...),
    cart_data: str = Form(...),  # JSON string from frontend
):
    user = get_current_user(request, db)
    cart = json.loads(cart_data)

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Build order items + calculate subtotal
    subtotal = 0.0
    items_data = []
    for item in cart:
        product = db.query(Product).filter(Product.id == item["product_id"], Product.is_active == True).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item['product_id']} not found")
        subtotal += product.price * item["quantity"]
        items_data.append({
            "product": product,
            "size": item["size"],
            "quantity": item["quantity"],
        })

    total = subtotal + settings.DELIVERY_CHARGE
    amount_to_pay = settings.DELIVERY_CHARGE if payment_method == "cod" else total

    # Create Razorpay order
    receipt = f"order_{phone}_{len(cart)}"
    rz_order = razorpay_service.create_order(amount_to_pay, receipt)

    # Save pending order in DB
    order = Order(
        user_id=user.id if user else None,
        customer_name=name,
        customer_phone=phone,
        customer_email=email,
        address_line=address_line,
        city=city, state=state, pincode=pincode,
        payment_method=PaymentMethod(payment_method),
        payment_status=PaymentStatus.pending,
        razorpay_order_id=rz_order["id"],
        subtotal=subtotal,
        delivery_charge=settings.DELIVERY_CHARGE,
        total_amount=total,
        amount_paid=amount_to_pay,
    )
    db.add(order)
    db.flush()

    for itm in items_data:
        p = itm["product"]
        db.add(OrderItem(
            order_id=order.id,
            product_id=p.id,
            product_name=p.name,
            product_image=p.images[0] if p.images else None,
            size=itm["size"],
            quantity=itm["quantity"],
            price=p.price,
        ))

    db.commit()
    db.refresh(order)

    return {
        "razorpay_order_id": rz_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": int(amount_to_pay * 100),
        "order_db_id": order.id,
        "name": name, "phone": phone, "email": email or "",
    }


@router.post("/checkout/verify-payment")
async def verify_payment(
    request: Request,
    db: Session = Depends(get_db),
    razorpay_order_id: str = Form(...),
    razorpay_payment_id: str = Form(...),
    razorpay_signature: str = Form(...),
    order_db_id: int = Form(...),
):
    order = db.query(Order).filter(Order.id == order_db_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify Razorpay payment signature
    verified = razorpay_service.verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    if not verified:
        order.payment_status = PaymentStatus.failed
        db.commit()
        raise HTTPException(status_code=400, detail="Payment verification failed")

    order.payment_status = PaymentStatus.paid
    order.razorpay_payment_id = razorpay_payment_id
    order.order_status = OrderStatus.confirmed
    db.commit()
    db.refresh(order)

    # Email — send invoice to admin + customer on order confirmation
    try:
        print(f"[EMAIL] Generating PDF for order #{order.id}...")
        pdf_path = pdf_service.generate_order_pdf(order)
        print(f"[EMAIL] PDF generated at: {pdf_path}")
        email_service.send_order_email(order, pdf_path)
    except Exception as e:
        print(f"[EMAIL ERROR] Order #{order.id} — {type(e).__name__}: {e}")

    from fastapi.responses import JSONResponse
    return JSONResponse({"redirect": f"/order-confirmation/{order.id}"})


@router.get("/order-confirmation/{order_id}", response_class=HTMLResponse)
def order_confirmation(request: Request, order_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("store/order_confirmation.html", {
        "request": request, "user": user, "order": order,
    })
