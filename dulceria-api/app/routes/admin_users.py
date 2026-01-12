from flask import Blueprint, jsonify
from ..authz import require_role
from ..models import User

bp = Blueprint("admin_users", __name__, url_prefix="/api/admin/users")

@bp.get("")
@require_role("admin")
def list_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([u.to_dict() for u in users])
