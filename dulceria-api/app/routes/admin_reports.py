from datetime import datetime, date, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..authz import require_role
from ..extensions import db
from ..models import Order, OrderItem, Product

bp = Blueprint("admin_reports", __name__, url_prefix="/api/admin")


def _parse_date(s: str) -> date:
    # Espera YYYY-MM-DD
    return datetime.fromisoformat(s).date()


def _date_range_from_args():
    """
    Query params:
      ?from=YYYY-MM-DD&to=YYYY-MM-DD
    Regresa (start_dt, end_dt_exclusive) o (None, None) si no vienen.
    """
    f = request.args.get("from")
    t = request.args.get("to")
    if not f and not t:
        return None, None

    if not f:
        # si solo viene to, asumimos desde muy atrás
        start = date(1970, 1, 1)
    else:
        start = _parse_date(f)

    if not t:
        # si solo viene from, asumimos hasta mañana (exclusivo)
        end = date.today() + timedelta(days=1)
    else:
        end = _parse_date(t) + timedelta(days=1)  # exclusivo

    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.min.time())
    return start_dt, end_dt


@bp.get("/dashboard")
@require_role("admin")
def dashboard():
    """
    Dashboard administrativo (solo admin).
    Métricas rápidas: conteos de pedidos, revenue (pedidos pagados), suma de pagos y pedidos por status.
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: query
        name: from
        type: string
        required: false
        description: Fecha inicio (YYYY-MM-DD)
        example: "2026-01-01"
      - in: query
        name: to
        type: string
        required: false
        description: Fecha fin (YYYY-MM-DD)
        example: "2026-01-31"
    responses:
      200:
        description: Métricas de dashboard
        schema:
          type: object
          properties:
            range:
              type: object
              properties:
                from: {type: string, nullable: true, example: "2026-01-01"}
                to: {type: string, nullable: true, example: "2026-01-31"}
            orders_count: {type: integer, example: 12}
            paid_orders_count: {type: integer, example: 7}
            revenue_from_paid_orders: {type: number, example: 5430.0}
            orders_by_status:
              type: object
              additionalProperties:
                type: integer
              example:
                pendiente: 3
                pagado: 7
                cancelado: 2
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
    """
    start_dt, end_dt = _date_range_from_args()

    order_filters = [Order.status != "cancelado"]
    paid_filters = [Order.status == "pagado"]

    if start_dt and end_dt:
        order_filters += [Order.created_at >= start_dt, Order.created_at < end_dt]
        paid_filters += [Order.created_at >= start_dt, Order.created_at < end_dt]

    # Órdenes (no canceladas)
    orders_count = db.session.query(func.count(Order.id)).filter(*order_filters).scalar() or 0

    # Órdenes pagadas
    paid_count = db.session.query(func.count(Order.id)).filter(*paid_filters).scalar() or 0
    revenue = db.session.query(func.sum(Order.total)).filter(*paid_filters).scalar() or 0


    # Órdenes por status
    status_rows = (
        db.session.query(Order.status, func.count(Order.id))
        .filter(*([Order.created_at >= start_dt, Order.created_at < end_dt] if start_dt and end_dt else []))
        .group_by(Order.status)
        .all()
    )
    by_status = {s: c for s, c in status_rows}

    return jsonify({
        "range": {
            "from": request.args.get("from"),
            "to": request.args.get("to"),
        },
        "orders_count": int(orders_count),
        "paid_orders_count": int(paid_count),
        "revenue_from_paid_orders": float(revenue),
        "orders_by_status": by_status,
    })


@bp.get("/reports/top-products")
@require_role("admin")
def top_products():
    """
    Reporte: productos más vendidos (solo pedidos pagados).
    Ordenado por revenue descendente.
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: query
        name: from
        type: string
        required: false
        description: Fecha inicio (YYYY-MM-DD)
        example: "2026-01-01"
      - in: query
        name: to
        type: string
        required: false
        description: Fecha fin (YYYY-MM-DD)
        example: "2026-01-31"
      - in: query
        name: limit
        type: integer
        required: false
        description: Máximo de productos a devolver (default 10)
        example: 10
    responses:
      200:
        description: Lista de productos top
        schema:
          type: array
          items:
            type: object
            properties:
              product_id: {type: integer, example: 1}
              sku: {type: string, example: "GOM-001"}
              nombre: {type: string, example: "Gomitas enchiladas 1kg"}
              qty_vendida: {type: integer, example: 120}
              revenue: {type: number, example: 9600.0}
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
    """
    start_dt, end_dt = _date_range_from_args()
    limit = int(request.args.get("limit") or 10)

    filters = [Order.status == "pagado"]
    if start_dt and end_dt:
        filters += [Order.created_at >= start_dt, Order.created_at < end_dt]

    rows = (
        db.session.query(
            Product.id,
            Product.sku,
            Product.nombre,
            func.sum(OrderItem.qty).label("qty"),
            func.sum(OrderItem.line_total).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(*filters)
        .group_by(Product.id, Product.sku, Product.nombre)
        .order_by(func.sum(OrderItem.line_total).desc())
        .limit(limit)
        .all()
    )

    return jsonify([{
        "product_id": r[0],
        "sku": r[1],
        "nombre": r[2],
        "qty_vendida": int(r[3] or 0),
        "revenue": float(r[4] or 0),
    } for r in rows])


@bp.get("/reports/low-stock")
@require_role("admin")
def low_stock():
    """
    Reporte: productos con stock bajo (solo admin).
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: query
        name: threshold
        type: integer
        required: false
        description: Umbral de stock (<= threshold). Default 10
        example: 10
    responses:
      200:
        description: Lista de productos con stock bajo
        schema:
          type: array
          items:
            type: object
            properties:
              id: {type: integer, example: 1}
              sku: {type: string, example: "GOM-001"}
              nombre: {type: string, example: "Gomitas enchiladas 1kg"}
              stock: {type: integer, example: 8}
              activo: {type: boolean, example: true}
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
    """
    threshold = int(request.args.get("threshold") or 10)

    products = (
        Product.query
        .filter(Product.activo.is_(True), Product.stock <= threshold)
        .order_by(Product.stock.asc(), Product.id.desc())
        .all()
    )

    return jsonify([p.to_dict() for p in products])


@bp.get("/reports/sales-summary")
@require_role("admin")
def sales_summary():
    """
    Resumen de ventas (solo pedidos pagados).
    Devuelve revenue, cantidad de pedidos pagados y ticket promedio.
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    produces:
      - application/json
    parameters:
      - in: query
        name: from
        type: string
        required: false
        description: Fecha inicio (YYYY-MM-DD)
        example: "2026-01-01"
      - in: query
        name: to
        type: string
        required: false
        description: Fecha fin (YYYY-MM-DD)
        example: "2026-01-31"
    responses:
      200:
        description: Resumen de ventas
        schema:
          type: object
          properties:
            range:
              type: object
              properties:
                from: {type: string, nullable: true, example: "2026-01-01"}
                to: {type: string, nullable: true, example: "2026-01-31"}
            paid_orders: {type: integer, example: 7}
            revenue: {type: number, example: 5430.0}
            avg_ticket: {type: number, example: 775.71}
      401:
        description: No autenticado
      403:
        description: No autorizado (no admin)
    """
    start_dt, end_dt = _date_range_from_args()

    paid_filters = [Order.status == "pagado"]
    if start_dt and end_dt:
        paid_filters += [Order.created_at >= start_dt, Order.created_at < end_dt]

    total_orders = db.session.query(func.count(Order.id)).filter(*paid_filters).scalar() or 0
    total_revenue = db.session.query(func.sum(Order.total)).filter(*paid_filters).scalar() or 0

    avg_ticket = 0.0
    if total_orders:
        avg_ticket = float(total_revenue) / int(total_orders)

    return jsonify({
        "range": {"from": request.args.get("from"), "to": request.args.get("to")},
        "paid_orders": int(total_orders),
        "revenue": float(total_revenue),
        "avg_ticket": float(avg_ticket),
    })
