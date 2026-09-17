import razorpay
from app.config import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_order(amount_rupees: float, receipt: str) -> dict:
    """Create a Razorpay order. Amount is in rupees, converted to paise."""
    data = {
        "amount": int(amount_rupees * 100),  # paise
        "currency": "INR",
        "receipt": receipt,
    }
    return client.order.create(data=data)


def verify_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
        return True
    except Exception:
        return False
