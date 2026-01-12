from pathlib import Path
from flask import Blueprint, send_from_directory

bp = Blueprint("site", __name__)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

@bp.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@bp.get("/admin")
def admin():
    return send_from_directory(FRONTEND_DIR, "admin.html")

@bp.get("/<path:path>")
def assets(path: str):
    return send_from_directory(FRONTEND_DIR, path)
