from datetime import datetime
from .extensions import db
from sqlalchemy import UniqueConstraint


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(200), nullable=False, index=True)
    precio_mayoreo = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    price_tiers = db.relationship("PriceTier", back_populates="product", cascade="all, delete-orphan", lazy=True)


    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "nombre": self.nombre,
            "precio_mayoreo": float(self.precio_mayoreo),
            "stock": self.stock,
            "activo": self.activo,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

from datetime import datetime
from .extensions import db

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(200), unique=True, nullable=True, index=True)
    telefono = db.Column(db.String(50), nullable=True)
    rfc = db.Column(db.String(20), nullable=True)
    razon_social = db.Column(db.String(250), nullable=True)

    activo = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = db.relationship("Order", back_populates="customer", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "rfc": self.rfc,
            "razon_social": self.razon_social,
            "activo": self.activo,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="pendiente", index=True) 

    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy=True)

    def to_dict(self, include_items: bool = False):
        data = {
            "id": self.id,
            "customer_id": self.customer_id,
            "status": self.status,
            "total": float(self.total),
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }
        if include_items:
            data["items"] = [i.to_dict() for i in self.items]
        return data


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)

    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_sku": self.product.sku if self.product else None,
            "product_nombre": self.product.nombre if self.product else None,
            "qty": self.qty,
            "unit_price": float(self.unit_price),
            "line_total": float(self.line_total),
        }

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="cliente")  

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True, index=True)
    customer = db.relationship("Customer")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "customer_id": self.customer_id,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

class PriceTier(db.Model):
    __tablename__ = "price_tiers"
    __table_args__ = (
        UniqueConstraint("product_id", "min_qty", name="uq_price_tier_product_minqty"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)

    min_qty = db.Column(db.Integer, nullable=False)  # desde cuántas unidades aplica
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    product = db.relationship("Product", back_populates="price_tiers")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "min_qty": self.min_qty,
            "unit_price": float(self.unit_price),
        }

from datetime import datetime
from .extensions import db

class Payment(db.Model):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_payment_order_id"),  
    )

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(30), nullable=False)  
    paid_at = db.Column(db.DateTime, nullable=False)
    received_by = db.Column(db.String(120), nullable=False)
    reference = db.Column(db.String(120), nullable=True)   

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    order = db.relationship("Order", backref=db.backref("payment", uselist=False))

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "amount": float(self.amount),
            "method": self.method,
            "paid_at": self.paid_at.isoformat() + "Z",
            "received_by": self.received_by,
            "reference": self.reference,
            "created_at": self.created_at.isoformat() + "Z",
        }