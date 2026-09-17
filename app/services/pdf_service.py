from fpdf import FPDF
from app.models.order import Order
from app.config import settings
import tempfile, os


def generate_order_pdf(order: Order) -> str:
    """Generate order invoice PDF and return file path."""
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, settings.APP_NAME, ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Order Invoice", ln=True, align="C")
    pdf.ln(4)

    # Divider
    pdf.set_draw_color(46, 204, 113)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Order info
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Order #{order.id}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Date: {order.created_at.strftime('%d %b %Y, %I:%M %p')}", ln=True)
    pdf.cell(0, 6, f"Status: {order.order_status.value.upper()}", ln=True)
    pdf.cell(0, 6, f"Payment: {order.payment_method.value.upper()} | {order.payment_status.value.upper()}", ln=True)
    pdf.ln(4)

    # Customer info
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Customer Details", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Name: {order.customer_name}", ln=True)
    pdf.cell(0, 6, f"Phone: {order.customer_phone}", ln=True)
    if order.customer_email:
        pdf.cell(0, 6, f"Email: {order.customer_email}", ln=True)
    pdf.cell(0, 6, f"Address: {order.address_line}, {order.city}, {order.state} - {order.pincode}", ln=True)
    pdf.ln(4)

    # Items table header
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Order Items", ln=True)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(80, 8, "Product", border=1, fill=True)
    pdf.cell(20, 8, "Size", border=1, fill=True, align="C")
    pdf.cell(20, 8, "Qty", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Price", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Total", border=1, fill=True, align="C")
    pdf.ln()

    # Items
    pdf.set_font("Helvetica", "", 10)
    for item in order.items:
        pdf.cell(80, 7, item.product_name[:40], border=1)
        pdf.cell(20, 7, str(item.size), border=1, align="C")
        pdf.cell(20, 7, str(item.quantity), border=1, align="C")
        pdf.cell(35, 7, f"Rs {item.price:.0f}", border=1, align="C")
        pdf.cell(35, 7, f"Rs {item.price * item.quantity:.0f}", border=1, align="C")
        pdf.ln()

    pdf.ln(4)

    # Totals
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(155, 7, "Subtotal", align="R")
    pdf.cell(35, 7, f"Rs {order.subtotal:.0f}", border=1, align="C")
    pdf.ln()
    pdf.cell(155, 7, "Delivery Charge", align="R")
    pdf.cell(35, 7, f"Rs {order.delivery_charge:.0f}", border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(155, 8, "TOTAL AMOUNT", align="R")
    pdf.cell(35, 8, f"Rs {order.total_amount:.0f}", border=1, align="C")
    pdf.ln()

    if order.payment_method.value == "cod":
        pdf.set_font("Helvetica", "I", 9)
        pdf.ln(3)
        pdf.cell(0, 6, f"Delivery charge paid: Rs {order.delivery_charge:.0f} | Remaining (COD): Rs {order.subtotal:.0f}", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "Thank you for shopping with NewNational Footwear!", ln=True, align="C")

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"order_{order.id}_")
    pdf.output(tmp.name)
    return tmp.name
