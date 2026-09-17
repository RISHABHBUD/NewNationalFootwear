from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class PaymentMethod(str, enum.Enum):
    cod = "cod"
    online = "online"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    # customer info (guest or logged-in)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(15), nullable=False)
    customer_email = Column(String(150), nullable=True)

    # address
    address_line = Column(String(300), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)

    # payment
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True)

    # amounts
    subtotal = Column(Float, nullable=False)
    delivery_charge = Column(Float, default=150.0)
    total_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=False)  # 150 for COD, full for online

    # status
    order_status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)  # snapshot at order time
    product_image = Column(String(500), nullable=True)
    size = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)  # snapshot at order time

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
