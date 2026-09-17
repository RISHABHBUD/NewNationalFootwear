import base64
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)
from app.config import settings
from app.models.order import Order


def _build_html(order: Order) -> str:
    items_rows = "".join(
        f"""<tr>
            <td style="padding:8px;border:1px solid #eee">{item.product_name}</td>
            <td style="padding:8px;border:1px solid #eee;text-align:center">{item.size}</td>
            <td style="padding:8px;border:1px solid #eee;text-align:center">{item.quantity}</td>
            <td style="padding:8px;border:1px solid #eee;text-align:right">&#8377;{item.price:.0f}</td>
            <td style="padding:8px;border:1px solid #eee;text-align:right">&#8377;{item.price * item.quantity:.0f}</td>
        </tr>"""
        for item in order.items
    )
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px">
      <h2 style="color:#111;border-bottom:3px solid #2ecc71;padding-bottom:8px">
        {settings.APP_NAME}
      </h2>
      <h3 style="color:#333">Order #{order.id} Confirmed &#9989;</h3>
      <p style="color:#555">
        <strong>Customer:</strong> {order.customer_name}<br>
        <strong>Phone:</strong> {order.customer_phone}<br>
        <strong>Address:</strong> {order.address_line}, {order.city}, {order.state} - {order.pincode}
      </p>
      <p style="color:#555">
        <strong>Payment:</strong> {order.payment_method.value.upper()} &nbsp;|&nbsp;
        <strong>Status:</strong> {order.payment_status.value.upper()}
      </p>
      <table style="width:100%;border-collapse:collapse;margin:16px 0">
        <thead>
          <tr style="background:#f5f5f5">
            <th style="padding:8px;border:1px solid #eee;text-align:left">Product</th>
            <th style="padding:8px;border:1px solid #eee">Size</th>
            <th style="padding:8px;border:1px solid #eee">Qty</th>
            <th style="padding:8px;border:1px solid #eee;text-align:right">Price</th>
            <th style="padding:8px;border:1px solid #eee;text-align:right">Total</th>
          </tr>
        </thead>
        <tbody>{items_rows}</tbody>
      </table>
      <table style="width:100%;max-width:300px;margin-left:auto">
        <tr><td>Subtotal</td><td style="text-align:right">&#8377;{order.subtotal:.0f}</td></tr>
        <tr><td>Delivery</td><td style="text-align:right">&#8377;{order.delivery_charge:.0f}</td></tr>
        <tr style="font-weight:bold;font-size:1.1em">
          <td>Total</td><td style="text-align:right">&#8377;{order.total_amount:.0f}</td>
        </tr>
      </table>
      <p style="color:#888;font-size:0.85em;margin-top:24px;text-align:center">
        Thank you for shopping with {settings.APP_NAME}!
      </p>
    </div>
    """


def send_order_email(order: Order, pdf_path: str) -> None:
    """Send order confirmation email to admin and customer via SendGrid."""
    if not settings.SENDGRID_API_KEY or not settings.SENDGRID_FROM_EMAIL:
        print("[EMAIL] SendGrid credentials not configured, skipping.")
        return

    recipients = [settings.NOTIFY_ADMIN_EMAIL or settings.ADMIN_EMAIL]
    if order.customer_email and order.customer_email not in recipients:
        recipients.append(order.customer_email)

    subject = f"Order #{order.id} Confirmed — {settings.APP_NAME}"
    html_body = _build_html(order)

    # Read and encode PDF once
    pdf_data = None
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode()

    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

    for recipient in recipients:
        if not recipient:
            continue
        try:
            message = Mail(
                from_email=(settings.SENDGRID_FROM_EMAIL, settings.APP_NAME),
                to_emails=recipient,
                subject=subject,
                html_content=html_body,
            )

            if pdf_data:
                attachment = Attachment(
                    file_content=FileContent(pdf_data),
                    file_name=FileName(f"invoice_order_{order.id}.pdf"),
                    file_type=FileType("application/pdf"),
                    disposition=Disposition("attachment"),
                )
                message.attachment = attachment

            sg.send(message)
            print(f"[EMAIL] Sent to {recipient} for order #{order.id}")
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send to {recipient}: {e}")

    # Clean up local PDF
    try:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
    except Exception:
        pass
