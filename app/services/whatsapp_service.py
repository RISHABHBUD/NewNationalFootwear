from twilio.rest import Client
from app.config import settings
from app.models.order import Order
import cloudinary.uploader
import json
import os


def _upload_pdf_to_cloudinary(pdf_path: str, order_id: int) -> str:
    """Upload PDF to Cloudinary and return a public URL."""
    result = cloudinary.uploader.upload(
        pdf_path,
        folder="newnational/invoices",
        public_id=f"order_{order_id}_invoice",
        resource_type="raw",
        overwrite=True,
    )
    return result["secure_url"]


def send_order_whatsapp(order: Order, pdf_path: str) -> None:
    """
    Send order confirmation + PDF invoice to admin via Twilio WhatsApp sandbox.
    - Upload PDF to Cloudinary to get a public URL (WhatsApp needs a URL, not raw bytes)
    - Send to OWNER_WHATSAPP (your number, which must have joined the sandbox)
    """
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Upload PDF and get public URL
    pdf_url = _upload_pdf_to_cloudinary(pdf_path, order.id)

    client.messages.create(
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=settings.OWNER_WHATSAPP,
        content_sid=settings.TWILIO_CONTENT_SID,
        content_variables=json.dumps({
            "1": str(order.id),
            "2": order.customer_name,
            "3": f"{order.payment_method.value.upper()} | {order.payment_status.value.upper()}",
            "4": str(int(order.total_amount)),
            "5": pdf_url,
        }),
    )

    # Clean up local temp PDF
    try:
        os.unlink(pdf_path)
    except Exception:
        pass
