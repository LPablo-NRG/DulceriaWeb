from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from ..extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..authz import require_role
from ..models import Order, OrderItem, Customer, Product, User, PriceTier

bp = Blueprint("orders", __name__, url_prefix="/api/orders")

VALID_STATUSES = {"pendiente", "pagado", "cancelado"}

def get_unit_price_for_qty(product_id: int, qty: int) -> float:
    tier = (
        PriceTier.query
        .filter(PriceTier.product_id == product_id, PriceTier.min_qty <= qty)
        .order_by(PriceTier.min_qty.desc())
        .first()
    )
    if tier:
        return float(tier.unit_price)

    p = Product.query.get(product_id)
    return float(p.precio_mayoreo)

def load_order_full(order_id: int):
    return (
        Order.query
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .get(order_id)
    )


@bp.get("")
@jwt_required()
def list_orders():
    """
    Lista pedidos.
    - Admin: ve todos.
    - Cliente: ve solo sus pedidos (según su customer_id).
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: query
        name: status
        type: string
        required: false
        description: Filtra por estatus (pendiente|pagado|cancelado)
        example: pagado
    responses:
      200:
        description: Lista de pedidos (sin items)
        schema:
          type: array
          items:
            type: object
            properties:
              id: {type: integer, example: 1}
              customer_id: {type: integer, example: 2}
              status: {type: string, example: pendiente}
              total: {type: number, example: 350.0}
              created_at: {type: string, example: "2026-01-05T12:00:00Z"}
              updated_at: {type: string, example: "2026-01-05T12:00:00Z"}
      401:
        description: No autenticado (token faltante o inválido)
    """
    claims = get_jwt()
    role = claims.get("role")

    query = Order.query

    if role != "admin":
        user = User.query.get(int(get_jwt_identity()))
        if not user or not user.customer_id:
            return jsonify([])  # cliente sin customer ligado
        query = query.filter(Order.customer_id == user.customer_id)

    status = (request.args.get("status") or "").strip().lower()
    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.id.desc()).all()
    return jsonify([o.to_dict(include_items=False) for o in orders])


@bp.get("/<int:order_id>")
@jwt_required()
def get_order(order_id: int):
    """
    Obtiene un pedido por ID (incluye items).
    - Admin: puede ver cualquiera.
    - Cliente: solo puede ver pedidos de su customer_id.
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
        description: ID del pedido
        example: 1
    responses:
      200:
        description: Pedido con items y datos del cliente
        schema:
          type: object
          properties:
            id: {type: integer, example: 1}
            customer_id: {type: integer, example: 2}
            status: {type: string, example: pendiente}
            total: {type: number, example: 350.0}
            items:
              type: array
              items:
                type: object
                properties:
                  id: {type: integer, example: 10}
                  order_id: {type: integer, example: 1}
                  product_id: {type: integer, example: 3}
                  qty: {type: integer, example: 12}
                  unit_price: {type: number, example: 80.0}
                  line_total: {type: number, example: 960.0}
            customer:
              type: object
              nullable: true
              properties:
                id: {type: integer, example: 2}
                nombre: {type: string, example: "Abarrotes La Esquina"}
                email: {type: string, example: "ventas@esquina.com"}
      401:
        description: No autenticado
      403:
        description: No autorizado (cliente intentando ver pedido ajeno)
      404:
        description: Pedido no encontrado
    """
    o = load_order_full(order_id)
    if not o:
        return jsonify({"error": "Pedido no encontrado"}), 404

    claims = get_jwt()
    if claims.get("role") != "admin":
        user = User.query.get(int(get_jwt_identity()))
        if not user or user.customer_id != o.customer_id:
            return jsonify({"error": "No autorizado"}), 403

    data = o.to_dict(include_items=True)
    data["customer"] = o.customer.to_dict() if o.customer else None
    return jsonify(data)


@bp.post("")
@jwt_required()
def create_order():
    """
    Crea un pedido.
    - Cliente: crea pedido para su customer_id (ligado al usuario).
    Notas:
    - Valida stock.
    - Calcula precio por volumen (PriceTier) si aplica.
    - Descuenta inventario.
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - items
          properties:
            customer_id:
              type: integer
              example: 1
              description: Obligatorio solo si el usuario es admin
            items:
              type: array
              minItems: 1
              items:
                type: object
                required: [product_id, qty]
                properties:
                  product_id:
                    type: integer
                    example: 1
                  qty:
                    type: integer
                    example: 12
    responses:
      201:
        description: Pedido creado (incluye items)
        schema:
          type: object
          properties:
            id: {type: integer, example: 1}
            customer_id: {type: integer, example: 2}
            status: {type: string, example: pendiente}
            total: {type: number, example: 350.0}
            items:
              type: array
              items:
                type: object
                properties:
                  product_id: {type: integer, example: 1}
                  qty: {type: integer, example: 12}
                  unit_price: {type: number, example: 80.0}
                  line_total: {type: number, example: 960.0}
      400:
        description: Error de validación (items vacíos, stock insuficiente, qty inválida, etc.)
      401:
        description: No autenticado
      403:
        description: No autorizado (casos de acceso indebido)
      409:
        description: Error de integridad al guardar el pedido
    """

    data = request.get_json(silent=True) or {}
    items = data.get("items")

    if not isinstance(items, list) or not items:
        return jsonify({"error": "items debe ser una lista con al menos 1 elemento"}), 400

    claims = get_jwt()
    role = claims.get("role")

    if role == "admin":
        return jsonify({"error": "Solo los clientes pueden crear pedidos."}), 403

    else:
        user = User.query.get(int(get_jwt_identity()))
        if not user or not user.customer_id:
            return jsonify({"error": "Este usuario no tiene cliente ligado"}), 400
        customer = Customer.query.get(int(user.customer_id))

    if not customer or not customer.activo:
        return jsonify({"error": "Cliente inválido o inactivo"}), 400

    # Transacción
    try:
        order = Order(customer_id=customer.id, status="pendiente", total=0)
        db.session.add(order)
        db.session.flush()  # para tener order.id

        total = 0.0

        for it in items:
            product_id = it.get("product_id")
            qty = it.get("qty")

            if product_id is None or qty is None:
                raise ValueError("Cada item debe incluir product_id y qty")

            qty = int(qty)
            if qty <= 0:
                raise ValueError("qty debe ser > 0")

            p = Product.query.get(int(product_id))
            if not p or not p.activo:
                raise ValueError(f"Producto inválido o inactivo: {product_id}")

            if p.stock < qty:
                raise ValueError(f"Stock insuficiente para {p.sku}. Disponible: {p.stock}, solicitado: {qty}")

            unit_price = get_unit_price_for_qty(p.id, qty)

            line_total = unit_price * qty

            # descuenta inventario
            p.stock -= qty

            oi = OrderItem(
                order_id=order.id,
                product_id=p.id,
                qty=qty,
                unit_price=unit_price,
                line_total=line_total
            )
            db.session.add(oi)

            total += line_total

        order.total = total
        db.session.commit()

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error de integridad al guardar el pedido"}), 409

    full = load_order_full(order.id)
    return jsonify(full.to_dict(include_items=True)), 201


@bp.put("/<int:order_id>/status")
@require_role("admin")
def update_order_status(order_id: int):
    """
    Actualiza el estatus de un pedido (solo admin).
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
        description: ID del pedido
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [status]
          properties:
            status:
              type: string
              enum: [pendiente, pagado, cancelado]
              example: pagado
    responses:
      200:
        description: Pedido actualizado
      400:
        description: status inválido
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      404:
        description: Pedido no encontrado
    """

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().lower()

    if status not in VALID_STATUSES:
        return jsonify({"error": f"status inválido. Usa: {sorted(list(VALID_STATUSES))}"}), 400

    o = Order.query.get(order_id)
    if not o:
        return jsonify({"error": "Pedido no encontrado"}), 404

    o.status = status
    db.session.commit()
    return jsonify(o.to_dict(include_items=True))
