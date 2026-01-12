from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timedelta
import random

from app import create_app
from app.extensions import db
from app.models import Product, PriceTier, Customer, User, Order, OrderItem


def money(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"))


def pick_tier_price(product_id: int, qty: int) -> Decimal:
    tier = (
        PriceTier.query
        .filter(PriceTier.product_id == product_id, PriceTier.min_qty <= qty)
        .order_by(PriceTier.min_qty.desc())
        .first()
    )
    if tier:
        return money(tier.unit_price)
    p = Product.query.get(product_id)
    return money(p.precio_mayoreo)


def clear_all():
    # Orden importa por FKs
    db.session.query(OrderItem).delete()
    db.session.query(Order).delete()

    db.session.query(PriceTier).delete()
    db.session.query(Product).delete()

    db.session.query(User).delete()
    db.session.query(Customer).delete()


def create_order(customer_id: int, items: list[dict], created_at: datetime, status: str) -> Order:
    """
    items = [{"product_id": 1, "qty": 12}, ...]
    Descuenta stock y calcula total con tiers.
    """
    order = Order(customer_id=customer_id, status=status, total=money(0))
    order.created_at = created_at
    order.updated_at = created_at
    db.session.add(order)
    db.session.flush()

    total = money(0)

    for it in items:
        product_id = int(it["product_id"])
        qty = int(it["qty"])

        p = Product.query.get(product_id)
        if not p or not p.activo:
            raise ValueError(f"Producto inválido/inactivo: {product_id}")

        if p.stock < qty:
            # Si no alcanza, baja qty a lo disponible (para que el seed no truene)
            qty = max(0, int(p.stock))
        if qty <= 0:
            continue

        unit_price = pick_tier_price(p.id, qty)
        line_total = money(unit_price * qty)

        # descuenta stock
        p.stock -= qty

        oi = OrderItem(
            order_id=order.id,
            product_id=p.id,
            qty=qty,
            unit_price=unit_price,
            line_total=line_total,
        )
        db.session.add(oi)
        total = money(total + line_total)

    order.total = total
    order.updated_at = created_at
    return order


def seed():
    random.seed(42)
    now = datetime.utcnow()

    clear_all()
    db.session.commit()

    # -----------------------------
    # Productos (más reales)
    # -----------------------------
    products_data = [
        # Gomitas / enchilados
        ("GOM-001", "Gomitas enchiladas 1kg", 82.00, 220),
        ("GOM-002", "Gomitas mangomitas 1kg", 78.00, 180),
        ("GOM-003", "Gomitas ositos 1kg", 74.00, 200),
        ("GOM-004", "Gusanos ácidos 1kg", 79.00, 160),
        ("GOM-005", "Aros durazno 1kg", 76.00, 140),

        # Paletas
        ("PAL-001", "Rockaleta 24pz", 165.00, 90),
        ("PAL-002", "Paleta Tutsi Pop 100pz", 150.00, 120),
        ("PAL-003", "Paleta Payaso 24pz", 260.00, 60),
        ("PAL-004", "Bola de tamarindo 50pz", 145.00, 80),
        ("PAL-005", "Pulparindo 20pz", 150.00, 100),

        # Chocolates
        ("CHO-001", "Chocolate Carlos V 24pz", 185.00, 85),
        ("CHO-002", "Bubulubu 24pz", 200.00, 80),
        ("CHO-003", "Duvalín 18pz", 170.00, 90),
        ("CHO-004", "Hershey's barra 12pz", 210.00, 70),
        ("CHO-005", "KitKat 12pz", 235.00, 60),
        ("CHO-006", "Snickers 12pz", 255.00, 55),
        ("CHO-007", "M&M's 10pz", 240.00, 50),

        # Clásicos
        ("CLA-001", "Mazapán 30pz", 160.00, 120),
        ("CLA-002", "Pelón Pelo Rico 24pz", 190.00, 90),
        ("CLA-003", "Lucas Muecas 20pz", 175.00, 95),
        ("CLA-004", "Miguelito 50 sobres", 145.00, 110),
        ("CLA-005", "Ricaleta 40pz", 185.00, 70),

        # Chicles / caramelos
        ("CHI-001", "Chicle Trident 12pz", 145.00, 80),
        ("CHI-002", "Chicle Bubbaloo 60pz", 170.00, 100),
        ("CAR-001", "Caramelo macizo 1kg", 68.00, 200),
        ("CAR-002", "Caramelo de café 1kg", 72.00, 150),
        ("CAR-003", "Halls 20pz", 125.00, 140),

        # Botanas dulces / snacks
        ("SNK-001", "Skittles 12pz", 210.00, 70),
        ("SNK-002", "Skwinkles 12pz", 195.00, 85),
        ("SNK-003", "Panditas 12pz", 180.00, 100),
        ("SNK-004", "Ruffles 8pz", 175.00, 65),

        # Insumos “dulcería”
        ("INS-001", "Chamoy 1L", 68.00, 90),
        ("INS-002", "Chile en polvo 1kg", 95.00, 75),
        ("INS-003", "Tamarindo natural 1kg", 85.00, 60),
        ("INS-004", "Gomitas a granel 500g", 45.00, 160),
    ]

    products = []
    for sku, nombre, precio, stock in products_data:
        p = Product(sku=sku, nombre=nombre, precio_mayoreo=money(precio), stock=stock, activo=True)
        db.session.add(p)
        products.append(p)
    db.session.flush()

    # -----------------------------
    # Tiers por producto
    # Reglas típicas: 1 / 5 / 10 / 25 / 50 (depende del tipo)
    # -----------------------------
    def add_tiers(p: Product, steps: list[tuple[int, float]]):
        for min_qty, unit_price in steps:
            db.session.add(PriceTier(product_id=p.id, min_qty=min_qty, unit_price=money(unit_price)))

    for p in products:
        base = float(p.precio_mayoreo)

        # Heurística simple según tipo
        if p.sku.startswith(("GOM", "CAR", "INS")):
            # a granel: más escalones
            add_tiers(p, [
                (1, base),
                (5, base * 0.97),
                (10, base * 0.94),
                (25, base * 0.91),
                (50, base * 0.88),
            ])
        elif p.sku.startswith(("PAL", "CHI", "CLA", "SNK", "CHO")):
            # cajas: escalones menos agresivos
            add_tiers(p, [
                (1, base),
                (3, base * 0.98),
                (6, base * 0.95),
                (12, base * 0.92),
                (24, base * 0.90),
            ])
        else:
            add_tiers(p, [
                (1, base),
                (10, base * 0.95),
                (50, base * 0.90),
            ])

    db.session.commit()

    # -----------------------------
    # Clientes (más “negocio real”)
    # -----------------------------
    customers_data = [
        ("Abarrotes La Esquina", "ventas@esquina.com", "5512345678"),
        ("Dulcería Lupita", "contacto@lupita.com", "5587654321"),
        ("Miscelánea Don Chuy", "admin@donchuy.com", "5522233344"),
        ("Papelería y Regalos Mar", "hola@mar.com", "5511122233"),
        ("Abarrotes San José", "pedidos@sanjose.com", "5544455566"),
        ("Tienda La Hormiga", "compras@hormiga.com", "5577711122"),
        ("Dulces y Botanas El Puente", "ventas@elpuente.com", "5533399988"),
        ("Mini Súper La Terminal", "contacto@terminal.com", "5555500011"),
        ("Abarrotes La Bodega", "pedidos@labodega.com", "5520091000"),
        ("Dulcería La Estrella", "hola@estrella.com", "5530012200"),
    ]

    customers = []
    for nombre, email, telefono in customers_data:
        c = Customer(nombre=nombre, email=email, telefono=telefono, activo=True)
        db.session.add(c)
        customers.append(c)
    db.session.flush()

    # -----------------------------
    # Usuarios (varios)
    # -----------------------------
    admin1 = User(email="admin@dulceria.com", role="admin")
    admin1.set_password("Admin123!")
    db.session.add(admin1)

    admin2 = User(email="admin2@dulceria.com", role="admin")
    admin2.set_password("Admin123!")
    db.session.add(admin2)

    client_users = []
    for c in customers:
        u = User(email=f"cliente+{c.id}@demo.com", role="cliente", customer_id=c.id)
        u.set_password("Cliente123!")
        db.session.add(u)
        client_users.append(u)

    # Un cliente extra para el primer customer (para “varios usuarios por cliente”)
    u_extra = User(email="compras@esquina.com", role="cliente", customer_id=customers[0].id)
    u_extra.set_password("Cliente123!")
    db.session.add(u_extra)

    db.session.commit()

    # -----------------------------
    # Pedidos (más volumen, fechas, estatus)
    # -----------------------------
    # Pool de productos por “tipo”
    def sample_products(k: int):
        return random.sample(products, k)

    statuses = ["pendiente", "pagado", "pendiente", "pendiente", "cancelado"]  # más pendientes
    orders_created = 0

    # 45 pedidos en últimos 35 días
    for _ in range(45):
        c = random.choice(customers)
        created_at = now - timedelta(days=random.randint(0, 35), hours=random.randint(0, 23))
        status = random.choice(statuses)

        # 2 a 5 items por pedido
        n_items = random.randint(2, 5)
        picks = sample_products(n_items)

        items = []
        for p in picks:
            # cantidades "realistas": a granel más cantidad, cajas menos
            if p.sku.startswith(("GOM", "CAR", "INS")):
                qty = random.choice([2, 5, 10, 15, 25, 50])
            else:
                qty = random.choice([1, 2, 3, 6, 12, 24])

            items.append({"product_id": p.id, "qty": qty})

        o = create_order(customer_id=c.id, items=items, created_at=created_at, status=status)
        db.session.add(o)
        orders_created += 1

    db.session.commit()

    print("✅ Seed FULL listo.")
    print("Credenciales:")
    print("  Admin:   admin@dulceria.com / Admin123!")
    print("  Admin2:  admin2@dulceria.com / Admin123!")
    print("  Clientes: cliente+<id>@demo.com / Cliente123!  (id = customer_id)")
    print("  Cliente extra (mismo customer): compras@esquina.com / Cliente123!")
    print(f"Productos: {Product.query.count()} | Tiers: {PriceTier.query.count()} | Clientes: {Customer.query.count()} | Usuarios: {User.query.count()} | Pedidos: {Order.query.count()}")


def main():
    app = create_app()
    with app.app_context():
        seed()


if __name__ == "__main__":
    main()
