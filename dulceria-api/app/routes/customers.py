from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Customer
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models import Customer, User
from ..authz import require_role


bp = Blueprint("customers", __name__, url_prefix="/api/customers")

@bp.get("")
@require_role("admin")
def list_customers():
    """
    Lista clientes (solo admin).
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: query
        name: q
        type: string
        required: false
        description: Búsqueda por nombre o email (parcial)
        example: esquina
      - in: query
        name: active
        type: string
        required: false
        description: true para solo activos; false para incluir inactivos
        example: "true"
    responses:
      200:
        description: Lista de clientes
        schema:
          type: array
          items:
            type: object
            properties:
              id: {type: integer, example: 1}
              nombre: {type: string, example: "Abarrotes La Esquina"}
              email: {type: string, nullable: true, example: "ventas@esquina.com"}
              telefono: {type: string, nullable: true, example: "5512345678"}
              rfc: {type: string, nullable: true, example: "XAXX010101000"}
              razon_social: {type: string, nullable: true, example: "Abarrotes La Esquina SA de CV"}
              activo: {type: boolean, example: true}
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
    """
    q = (request.args.get("q") or "").strip().lower()
    only_active = (request.args.get("active") or "true").lower() != "false"

    query = Customer.query
    if only_active:
        query = query.filter(Customer.activo.is_(True))
    if q:
        query = query.filter(
            (Customer.nombre.ilike(f"%{q}%")) |
            (Customer.email.ilike(f"%{q}%"))
        )

    customers = query.order_by(Customer.id.desc()).all()
    return jsonify([c.to_dict() for c in customers])

@bp.get("/<int:customer_id>")
@require_role("admin") #esto podria ser publico?
def get_customer(customer_id: int):
    """
    Obtiene un cliente por ID (solo admin).
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
        description: ID del cliente
        example: 1
    responses:
      200:
        description: Cliente
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      404:
        description: Cliente no encontrado
    """
    c = Customer.query.get(customer_id)
    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify(c.to_dict())

@bp.post("")
@require_role("admin")
def create_customer():
    """
    Crea un cliente (solo admin).
    ---
    tags:
      - Customers
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
          required: [nombre]
          properties:
            nombre:
              type: string
              example: "Abarrotes La Esquina"
            email:
              type: string
              nullable: true
              example: "ventas@esquina.com"
            telefono:
              type: string
              nullable: true
              example: "5512345678"
            rfc:
              type: string
              nullable: true
              example: "XAXX010101000"
            razon_social:
              type: string
              nullable: true
              example: "Abarrotes La Esquina SA de CV"
            activo:
              type: boolean
              example: true
    responses:
      201:
        description: Cliente creado
      400:
        description: Validación (nombre obligatorio, etc.)
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      409:
        description: Email duplicado
    """
    data = request.get_json(silent=True) or {}
    nombre = str(data.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "nombre es obligatorio"}), 400

    c = Customer(
        nombre=nombre,
        email=(str(data.get("email")).strip().lower() if data.get("email") else None),
        telefono=(str(data.get("telefono")).strip() if data.get("telefono") else None),
        rfc=(str(data.get("rfc")).strip().upper() if data.get("rfc") else None),
        razon_social=(str(data.get("razon_social")).strip() if data.get("razon_social") else None),
        activo=bool(data.get("activo", True)),
    )

    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email duplicado"}), 409

    return jsonify(c.to_dict()), 201

@bp.put("/<int:customer_id>")
@require_role("admin")
def update_customer(customer_id: int):
    """
    Actualiza un cliente (solo admin).
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
        description: ID del cliente
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nombre: {type: string, example: "Abarrotes La Esquina"}
            email: {type: string, nullable: true, example: "ventas@esquina.com"}
            telefono: {type: string, nullable: true, example: "5512345678"}
            rfc: {type: string, nullable: true, example: "XAXX010101000"}
            razon_social: {type: string, nullable: true, example: "Abarrotes La Esquina SA de CV"}
            activo: {type: boolean, example: true}
    responses:
      200:
        description: Cliente actualizado
      400:
        description: Validación (nombre vacío, etc.)
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      404:
        description: Cliente no encontrado
      409:
        description: Email duplicado
    """
    c = Customer.query.get(customer_id)
    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404

    data = request.get_json(silent=True) or {}

    if "nombre" in data:
        nombre = str(data.get("nombre") or "").strip()
        if not nombre:
            return jsonify({"error": "nombre no puede estar vacío"}), 400
        c.nombre = nombre

    if "email" in data:
        c.email = (str(data.get("email")).strip().lower() if data.get("email") else None)

    if "telefono" in data:
        c.telefono = (str(data.get("telefono")).strip() if data.get("telefono") else None)

    if "rfc" in data:
        c.rfc = (str(data.get("rfc")).strip().upper() if data.get("rfc") else None)

    if "razon_social" in data:
        c.razon_social = (str(data.get("razon_social")).strip() if data.get("razon_social") else None)

    if "activo" in data:
        c.activo = bool(data.get("activo"))

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email duplicado"}), 409

    return jsonify(c.to_dict())

@bp.delete("/<int:customer_id>")
@require_role("admin")
def delete_customer(customer_id: int):
    """
    Desactiva un cliente (borrado lógico, solo admin).
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
        description: ID del cliente
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
        description: Cliente no encontrado
    """
    c = Customer.query.get(customer_id)
    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404

    c.activo = False
    db.session.commit()
    return jsonify({"ok": True})

@bp.get("/me")
@jwt_required()
def get_my_customer():
    """
    Devuelve el cliente ligado al usuario autenticado.
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    produces:
      - application/json
    responses:
      200:
        description: Cliente del usuario
      400:
        description: El usuario no tiene cliente ligado
      401:
        description: No autenticado
      404:
        description: Cliente no encontrado o inactivo
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.customer_id:
        return jsonify({"error": "Este usuario no tiene cliente ligado"}), 400

    c = Customer.query.get(user.customer_id)
    if not c or not c.activo:
        return jsonify({"error": "Cliente no encontrado o inactivo"}), 404
    return jsonify(c.to_dict())

@bp.put("/me")
@jwt_required()
def update_my_customer():
    """
    Actualiza datos del cliente del usuario autenticado (solo campos seguros).
    Campos permitidos: telefono, rfc, razon_social.
    ---
    tags:
      - Customers
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
          properties:
            telefono: {type: string, nullable: true, example: "5512345678"}
            rfc: {type: string, nullable: true, example: "XAXX010101000"}
            razon_social: {type: string, nullable: true, example: "Abarrotes La Esquina SA de CV"}
    responses:
      200:
        description: Cliente actualizado
      400:
        description: El usuario no tiene cliente ligado
      401:
        description: No autenticado
      404:
        description: Cliente no encontrado o inactivo
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.customer_id:
        return jsonify({"error": "Este usuario no tiene cliente ligado"}), 400

    c = Customer.query.get(user.customer_id)
    if not c or not c.activo:
        return jsonify({"error": "Cliente no encontrado o inactivo"}), 404

    data = request.get_json(silent=True) or {}

    # Solo campos “seguros” para cliente
    if "telefono" in data:
        c.telefono = (str(data.get("telefono")).strip() if data.get("telefono") else None)
    if "razon_social" in data:
        c.razon_social = (str(data.get("razon_social")).strip() if data.get("razon_social") else None)
    if "rfc" in data:
        c.rfc = (str(data.get("rfc")).strip().upper() if data.get("rfc") else None)

    db.session.commit()
    return jsonify(c.to_dict())

