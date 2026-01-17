from datetime import datetime
from flask import Blueprint, jsonify, request

from ..authz import require_role
from ..extensions import db
from ..models import Order, Payment

bp = Blueprint("admin_payments", __name__, url_prefix="/api/admin")

ALLOWED_METHODS = {"efectivo", "transferencia", "cheque", "tarjeta"}

def parse_paid_at(value):
    if not value:
        return datetime.utcnow()
    s = str(value).strip().replace("Z", "+00:00")
    return datetime.fromisoformat(s)

@bp.get("/orders/<int:order_id>/payment")
@require_role("admin")
def get_payment(order_id: int):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Pedido no encontrado"}), 404

    p = Payment.query.filter_by(order_id=order_id).first()
    return jsonify(p.to_dict() if p else None), 200

@bp.post("/orders/<int:order_id>/payment")
@require_role("admin")
def upsert_payment(order_id: int):
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Pedido no encontrado"}), 404

    if order.status == "cancelado":
        return jsonify({"error": "No se puede registrar pago en un pedido cancelado"}), 400

    if order.status == "pagado":
        return jsonify({"error": "El pedido ya está pagado. No se puede modificar."}), 400

    existing = Payment.query.filter_by(order_id=order_id).first()
    if existing:
        return jsonify({"error": "El pedido ya tiene pago registrado. No se puede modificar."}), 400

    data = request.get_json(silent=True) or {}

    method = str(data.get("method") or "").strip().lower()
    if method not in ALLOWED_METHODS:
        return jsonify({"error": f"method inválido. Usa: {sorted(ALLOWED_METHODS)}"}), 400

    received_by = str(data.get("received_by") or "").strip()
    if not received_by:
        return jsonify({"error": "received_by es obligatorio"}), 400

    paid_at = parse_paid_at(data.get("paid_at"))

    reference = data.get("reference")
    reference = str(reference).strip() if reference else None

    amount = float(order.total)

    p = Payment(
        order_id=order_id,
        amount=amount,
        method=method,
        paid_at=paid_at,
        received_by=received_by,
        reference=reference,
    )
    db.session.add(p)

    order.status = "pagado"
    db.session.commit()

    return jsonify({"ok": True, "payment": p.to_dict(), "order_status": order.status}), 201
