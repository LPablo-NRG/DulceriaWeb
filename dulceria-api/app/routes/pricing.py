from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..authz import require_role
from ..extensions import db
from ..models import Product, PriceTier

bp = Blueprint("pricing", __name__, url_prefix="/api")

@bp.get("/products/<int:product_id>/price-tiers")
def list_price_tiers(product_id: int):
    """
    Lista los tiers de precio por volumen de un producto.
    (Público: sirve para mostrar reglas de mayoreo en el catálogo)
    ---
    tags:
      - Pricing
    produces:
      - application/json
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
        description: ID del producto
        example: 1
    responses:
      200:
        description: Lista de tiers ordenados por min_qty asc
        schema:
          type: array
          items:
            type: object
            properties:
              id: {type: integer, example: 10}
              product_id: {type: integer, example: 1}
              min_qty: {type: integer, example: 10}
              unit_price: {type: number, example: 80.0}
      404:
        description: Producto no encontrado
    """
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404

    tiers = PriceTier.query.filter_by(product_id=product_id).order_by(PriceTier.min_qty.asc()).all()
    return jsonify([t.to_dict() for t in tiers])

@bp.post("/products/<int:product_id>/price-tiers")
@require_role("admin")
def create_price_tier(product_id: int):
    """
    Crea un tier de precio por volumen para un producto (solo admin).
    Regla: unit_price aplica cuando qty >= min_qty.
    ---
    tags:
      - Pricing
    security:
      - Bearer: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
        description: ID del producto
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [min_qty, unit_price]
          properties:
            min_qty:
              type: integer
              example: 10
              description: Cantidad mínima para aplicar este precio
            unit_price:
              type: number
              example: 80.0
              description: Precio unitario cuando se cumple min_qty
    responses:
      201:
        description: Tier creado
      400:
        description: Validación (min_qty/unit_price faltantes o min_qty <= 0)
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      404:
        description: Producto no encontrado
      409:
        description: Ya existe un tier con ese min_qty para este producto
    """
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404

    data = request.get_json(silent=True) or {}
    min_qty = data.get("min_qty")
    unit_price = data.get("unit_price")

    if min_qty is None or unit_price is None:
        return jsonify({"error": "min_qty y unit_price son obligatorios"}), 400

    min_qty = int(min_qty)
    if min_qty <= 0:
        return jsonify({"error": "min_qty debe ser > 0"}), 400

    tier = PriceTier(product_id=product_id, min_qty=min_qty, unit_price=unit_price)
    db.session.add(tier)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un tier con ese min_qty para este producto"}), 409

    return jsonify(tier.to_dict()), 201

@bp.put("/price-tiers/<int:tier_id>")
@require_role("admin")
def update_price_tier(tier_id: int):
    """
    Actualiza un tier de precio por volumen (solo admin).
    ---
    tags:
      - Pricing
    security:
      - Bearer: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: path
        name: tier_id
        type: integer
        required: true
        description: ID del tier
        example: 10
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            min_qty:
              type: integer
              example: 25
            unit_price:
              type: number
              example: 78.0
    responses:
      200:
        description: Tier actualizado
      400:
        description: Validación (min_qty <= 0)
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      404:
        description: Tier no encontrado
      409:
        description: Conflicto min_qty duplicado para este producto
    """
    tier = PriceTier.query.get(tier_id)
    if not tier:
        return jsonify({"error": "Tier no encontrado"}), 404

    data = request.get_json(silent=True) or {}

    if "min_qty" in data:
        min_qty = int(data["min_qty"])
        if min_qty <= 0:
            return jsonify({"error": "min_qty debe ser > 0"}), 400
        tier.min_qty = min_qty

    if "unit_price" in data:
        tier.unit_price = data["unit_price"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Conflicto: min_qty duplicado para este producto"}), 409

    return jsonify(tier.to_dict())

@bp.delete("/price-tiers/<int:tier_id>")
@require_role("admin")
def delete_price_tier(tier_id: int):
    """
    Elimina un tier de precio por volumen (solo admin).
    ---
    tags:
      - Pricing
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: path
        name: tier_id
        type: integer
        required: true
        description: ID del tier
        example: 10
    responses:
      200:
        description: OK
        schema:
          type: object
          properties:
            ok: {type: boolean, example: true}
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      404:
        description: Tier no encontrado
    """
    tier = PriceTier.query.get(tier_id)
    if not tier:
        return jsonify({"error": "Tier no encontrado"}), 404

    db.session.delete(tier)
    db.session.commit()
    return jsonify({"ok": True})
