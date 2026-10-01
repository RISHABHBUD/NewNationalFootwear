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


def generate_order_pdf(order: Order) -> str:
    pdf = FPDF(orientation="L", unit="mm", format="A5")
    pdf.add_font("NotoSans", "", FONT_PATH, uni=True)
    pdf.add_page()
    pdf.set_margins(0, 0, 0)
    pdf.set_auto_page_break(False)

    PAGE_W = 210
    PAGE_H = 148
    LEFT_W = 100
    PAD    = 6

    # Outer border - right side only
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(PAGE_W - 2, 2, PAGE_W - 2, PAGE_H - 2)

    # Vertical divider
    pdf.set_line_width(0.4)
    pdf.line(LEFT_W, 2, LEFT_W, PAGE_H - 2)

    y = [4]

    def ln_left(text, bold=False, size=9, gap=5.5):
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.set_xy(PAD, y[0])
        pdf.multi_cell(LEFT_W - PAD * 2, gap, text, align="L")
        y[0] = pdf.get_y()

    def divider():
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.25)
        pdf.line(PAD, y[0] + 1, LEFT_W - PAD, y[0] + 1)
        pdf.set_draw_color(0, 0, 0)
        y[0] += 3.5

    # PAYMENT HEADER
    method = order.payment_method.value.upper()
    label  = "Cash ON DELIVERY" if method == "COD" else "PAID ONLINE"
    ln_left(label, bold=True, size=12, gap=7)

    amt = int(order.subtotal)
    ln_left(f"Rs. {amt}", bold=True, size=14, gap=8)
    ln_left(num_to_words(amt) + " Rupees only (in words)", size=10, gap=4.5)

    divider()

    # NOTE (red)
    pdf.set_text_color(220, 0, 0)
    ln_left("NOTE : This Delivery is not Open Delivery", bold=True, size=8.5, gap=5)
    pdf.set_text_color(0, 0, 0)

    divider()

    # RECEIVER
    ln_left("To:", bold=True, size=9)
    ln_left("RECEIVER:", bold=True, size=9)
    y[0] += 1
    ln_left(f"Name         -  {order.customer_name}", size=9, gap=5)
    ln_left(f"Address      -  {order.address_line}", size=9, gap=5)
    ln_left(f"City             -  {order.city}", size=9, gap=5)
    ln_left(f"State           -  {order.state}", size=9, gap=5)
    ln_left(f"Pin Code     -  {order.pincode}", size=9, gap=5)
    ln_left(f"Mobile        -  {order.customer_phone}", size=9, gap=5)
    for item in order.items:
        ln_left(f"Size             -  {item.size}  {item.product_name}  x{item.quantity}", size=9, gap=5)

    divider()

    # SENDER
    ln_left(f"CUSTOMER'S ID  -  1567641470", bold=True, size=8.5, gap=5)
    ln_left("OM FOOTWEAR", bold=True, size=9, gap=5)
    ln_left("3, PRINCE YASHWANT ROAD", size=8.5, gap=4.5)
    ln_left("NEAR PANDARINATH MANDIR, INDORE - 452007", size=8.5, gap=4.5)
    ln_left("Mobile: +91 89822 02734", size=8.5, gap=4.5)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"label_{order.id}_")
    pdf.output(tmp.name)
    return tmp.name
