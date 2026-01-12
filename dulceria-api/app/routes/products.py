from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Product
from ..authz import require_role


bp = Blueprint("products", __name__, url_prefix="/api/products")

@bp.get("")
def list_products():
    """
    Lista productos (catálogo).
    Por defecto solo regresa activos.
    ---
    tags:
      - Products
    produces:
      - application/json
    parameters:
      - in: query
        name: q
        type: string
        required: false
        description: Texto para buscar por nombre o sku (parcial)
        example: gomitas
      - in: query
        name: active
        type: string
        required: false
        description: true para solo activos; false para incluir inactivos
        example: "true"
    responses:
      200:
        description: Lista de productos
        schema:
          type: array
          items:
            type: object
            properties:
              id: {type: integer, example: 1}
              sku: {type: string, example: "GOM-001"}
              nombre: {type: string, example: "Gomitas enchiladas 1kg"}
              precio_mayoreo: {type: number, example: 85.0}
              stock: {type: integer, example: 120}
              activo: {type: boolean, example: true}
              created_at: {type: string, example: "2026-01-05T12:00:00Z"}
              updated_at: {type: string, example: "2026-01-05T12:00:00Z"}
    """

    q = (request.args.get("q") or "").strip().lower()
    only_active = (request.args.get("active") or "true").lower() != "false"

    query = Product.query
    if only_active:
        query = query.filter(Product.activo.is_(True))
    if q:
        query = query.filter((Product.nombre.ilike(f"%{q}%")) | (Product.sku.ilike(f"%{q}%")))

    products = query.order_by(Product.id.desc()).all()
    return jsonify([p.to_dict() for p in products])

@bp.get("/<int:product_id>")
def get_product(product_id: int):
    """
    Obtiene un producto por ID.
    ---
    tags:
      - Products
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
        description: Producto
        schema:
          type: object
          properties:
            id: {type: integer, example: 1}
            sku: {type: string, example: "GOM-001"}
            nombre: {type: string, example: "Gomitas enchiladas 1kg"}
            precio_mayoreo: {type: number, example: 85.0}
            stock: {type: integer, example: 120}
            activo: {type: boolean, example: true}
      404:
        description: Producto no encontrado
    """
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(p.to_dict())

@bp.post("")
@require_role("admin")
def create_product():
    """
    Crea un producto (solo admin).
    ---
    tags:
      - Products
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
          required: [sku, nombre, precio_mayoreo, stock]
          properties:
            sku: {type: string, example: "GOM-001"}
            nombre: {type: string, example: "Gomitas enchiladas 1kg"}
            precio_mayoreo: {type: number, example: 85.0}
            stock: {type: integer, example: 120}
            activo: {type: boolean, example: true}
    responses:
      201:
        description: Producto creado
      400:
        description: Faltan campos obligatorios
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      409:
        description: SKU duplicado
    """
    data = request.get_json(silent=True) or {}

    required = ["sku", "nombre", "precio_mayoreo", "stock"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": "Faltan campos", "missing": missing}), 400

    p = Product(
        sku=str(data["sku"]).strip(),
        nombre=str(data["nombre"]).strip(),
        precio_mayoreo=data["precio_mayoreo"],
        stock=int(data["stock"]),
        activo=bool(data.get("activo", True)),
    )

    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "SKU duplicado"}), 409

    return jsonify(p.to_dict()), 201

@bp.put("/<int:product_id>")
@require_role("admin")
def update_product(product_id: int):
    """
    Actualiza un producto (solo admin).
    ---
    tags:
      - Products
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
          properties:
            sku: {type: string, example: "GOM-001"}
            nombre: {type: string, example: "Gomitas enchiladas 1kg"}
            precio_mayoreo: {type: number, example: 85.0}
            stock: {type: integer, example: 120}
            activo: {type: boolean, example: true}
    responses:
      200:
        description: Producto actualizado
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      404:
        description: Producto no encontrado
      409:
        description: SKU duplicado
    """
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404

    data = request.get_json(silent=True) or {}

    if "sku" in data: p.sku = str(data["sku"]).strip()
    if "nombre" in data: p.nombre = str(data["nombre"]).strip()
    if "precio_mayoreo" in data: p.precio_mayoreo = data["precio_mayoreo"]
    if "stock" in data: p.stock = int(data["stock"])
    if "activo" in data: p.activo = bool(data["activo"])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "SKU duplicado"}), 409

    return jsonify(p.to_dict())

@bp.delete("/<int:product_id>")
@require_role("admin")
def delete_product(product_id: int):
    """
    Desactiva un producto (borrado lógico, solo admin).
    ---
    tags:
      - Products
    security:
      - Bearer: []
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
        description: Producto no encontrado
    """
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404

    
    p.activo = False
    db.session.commit()
    return jsonify({"ok": True})
