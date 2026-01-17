from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User, Customer
from ..authz import require_role

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@bp.post("/login")
def login():
    """
    Login y obtención de JWT.
    ---
    tags:
      - Auth
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
          required: [email, password]
          properties:
            email:
              type: string
              example: admin@dulceria.com
            password:
              type: string
              example: Admin123!
    responses:
      200:
        description: Token JWT + datos del usuario
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            user:
              type: object
              properties:
                id: {type: integer, example: 1}
                email: {type: string, example: admin@dulceria.com}
                role: {type: string, example: admin}
                customer_id: {type: integer, nullable: true, example: null}
      400:
        description: email y/o password faltantes
      401:
        description: Credenciales inválidas
    """

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email y password son obligatorios"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    return jsonify({"access_token": token, "user": user.to_dict()})

@bp.get("/me")
@jwt_required()
def me():
    """
    Devuelve el usuario autenticado (según el JWT).
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    produces:
      - application/json
    responses:
      200:
        description: Usuario actual
        schema:
          type: object
          properties:
            id: {type: integer, example: 1}
            email: {type: string, example: admin@dulceria.com}
            role: {type: string, example: admin}
            customer_id: {type: integer, nullable: true, example: null}
      401:
        description: No autenticado (token faltante o inválido)
      404:
        description: Usuario no encontrado
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user.to_dict())

@bp.post("/users")
@require_role("admin")
def create_user():
    """
    Crea un usuario (solo admin).
    Útil para crear usuarios tipo "cliente" ligados a un Customer.
    ---
    tags:
      - Auth
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
          required: [email, password]
          properties:
            email:
              type: string
              example: cliente@esquina.com
            password:
              type: string
              example: Cliente123!
            role:
              type: string
              enum: [admin, cliente]
              example: cliente
            customer_id:
              type: integer
              description: Opcional, recomendable si role=cliente
              example: 1
    responses:
      201:
        description: Usuario creado
        schema:
          type: object
          properties:
            id: {type: integer, example: 3}
            email: {type: string, example: cliente@esquina.com}
            role: {type: string, example: cliente}
            customer_id: {type: integer, nullable: true, example: 1}
      400:
        description: Error de validación (role inválido, email/password faltantes, customer_id inválido)
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
      409:
        description: Email duplicado
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "cliente").strip().lower()
    customer_id = data.get("customer_id")

    if role not in ("admin", "cliente"):
        return jsonify({"error": "role inválido (admin|cliente)"}), 400
    if not email or not password:
        return jsonify({"error": "email y password son obligatorios"}), 400

    if customer_id is not None:
        c = Customer.query.get(int(customer_id))
        if not c or not c.activo:
            return jsonify({"error": "customer_id inválido o cliente inactivo"}), 400
    else:
        c = None

    u = User(email=email, role=role, customer_id=(c.id if c else None))
    u.set_password(password)

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email duplicado"}), 409

    return jsonify(u.to_dict()), 201

@bp.post("/register")
def register():
    """
    Registro de clientes (NO admin).
    Body:
    {
      "nombre": "Abarrotes X",
      "email": "ventas@x.com",
      "password": "Secret123!",
      "telefono": "5512345678" (opcional),
      "rfc": "..." (opcional),
      "razon_social": "..." (opcional)
    }
    """
    data = request.get_json(silent=True) or {}

    nombre = str(data.get("nombre") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    telefono = (str(data.get("telefono")).strip() if data.get("telefono") else None)
    rfc = (str(data.get("rfc")).strip().upper() if data.get("rfc") else None)
    razon_social = (str(data.get("razon_social")).strip() if data.get("razon_social") else None)

    if not nombre:
        return jsonify({"error": "nombre es obligatorio"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "email inválido"}), 400
    if len(password) < 6:
        return jsonify({"error": "password debe tener al menos 6 caracteres"}), 400

    try:
        # crea Customer + User en una sola transacción
        c = Customer(
            nombre=nombre,
            email=email,
            telefono=telefono,
            rfc=rfc,
            razon_social=razon_social,
            activo=True,
        )
        db.session.add(c)
        db.session.flush()  # para tener c.id

        u = User(email=email, role="cliente", customer_id=c.id)
        u.set_password(password)
        db.session.add(u)

        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ese email ya está registrado"}), 409

    token = create_access_token(identity=str(u.id), additional_claims={"role": u.role})
    return jsonify({"access_token": token, "user": u.to_dict()}), 201