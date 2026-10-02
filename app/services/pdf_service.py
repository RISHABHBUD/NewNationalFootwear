from fpdf import FPDF
from app.models.order import Order
from app.config import settings
import tempfile
import os

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "NotoSans.ttf")


def num_to_words(n: int) -> str:
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _below_1000(num):
        if num == 0:
            return ""
        elif num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (" " + ones[num % 10] if num % 10 else "")
        else:
            return ones[num // 100] + " Hundred" + (" " + _below_1000(num % 100) if num % 100 else "")

    if n == 0:
        return "Zero"
    parts = []
    if n >= 100000:
        parts.append(_below_1000(n // 100000) + " Lakh")
        n %= 100000
    if n >= 1000:
        parts.append(_below_1000(n // 1000) + " Thousand")
        n %= 1000
    if n > 0:
        parts.append(_below_1000(n))
    return " ".join(parts)


def _draw_label(pdf, order, x_offset, col_w):
    """Draw the label content in a column starting at x_offset with given width."""
    PAD = 4
    y = [4]

    def ln(text, bold=False, size=8, gap=4.5, color=(0, 0, 0)):
        pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.set_xy(x_offset + PAD, y[0])
        pdf.multi_cell(col_w - PAD * 2, gap, text, align="L")
        y[0] = pdf.get_y()

    def divider():
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.2)
        pdf.line(x_offset + PAD, y[0] + 1, x_offset + col_w - PAD, y[0] + 1)
        pdf.set_draw_color(0, 0, 0)
        y[0] += 3

    # PAYMENT
    method = order.payment_method.value.upper()
    if method == "COD":
        ln("Cash ON DELIVERY", bold=True, size=10, gap=6)
        amt = int(order.subtotal)
        ln(f"Rs. {amt}", bold=True, size=12, gap=7)
        ln(num_to_words(amt) + " Rupees only", size=7.5, gap=4)
        divider()
    else:
        divider()

    # NOTE
    ln("NOTE: This Delivery is not Open Delivery", bold=True, size=7.5, gap=4.5, color=(220, 0, 0))

    divider()

    # RECEIVER
    ln("RECEIVER:", bold=True, size=8)
    y[0] += 1
    ln(f"Name     - {order.customer_name}", size=7.5, gap=4)
    ln(f"Address  - {order.address_line}", size=7.5, gap=4)
    ln(f"City        - {order.city}", size=7.5, gap=4)
    ln(f"State      - {order.state}", size=7.5, gap=4)
    ln(f"Pincode  - {order.pincode}", size=7.5, gap=4)
    ln(f"Mobile   - {order.customer_phone}", size=7.5, gap=4)
    for item in order.items:
        ln(f"Size       - {item.size}  {item.product_name}  x{item.quantity}", size=7.5, gap=4)

    divider()

    # SENDER
    ln("CUSTOMER'S ID  -  1567641470", bold=True, size=7.5, gap=4)
    ln("OM FOOTWEAR", bold=True, size=8, gap=4)
    ln("3, PRINCE YASHWANT ROAD", size=7.5, gap=3.5)
    ln("NEAR PANDARINATH MANDIR, INDORE - 452007", size=7.5, gap=3.5)
    ln("Mobile: +91 89822 02734", size=7.5, gap=3.5)


def generate_order_pdf(order: Order) -> str:
    pdf = FPDF(orientation="P", unit="mm", format="A5")
    pdf.add_font("NotoSans", "", FONT_PATH, uni=True)
    pdf.add_page()
    pdf.set_margins(0, 0, 0)
    pdf.set_auto_page_break(False)

    PAGE_W = 148
    PAGE_H = 210
    MID    = PAGE_W / 2  # 74mm

    # Center vertical divider line
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.4)
    pdf.line(MID, 2, MID, PAGE_H - 2)

    # Draw same content on left and right
    _draw_label(pdf, order, x_offset=0,   col_w=MID)
    _draw_label(pdf, order, x_offset=MID, col_w=MID)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"label_{order.id}_")
    pdf.output(tmp.name)
    return tmp.name
