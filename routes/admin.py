from flask import Blueprint, jsonify

bp = Blueprint("admin", __name__, url_prefix="/admin")
@bp.get("/status")
def status(): return jsonify({"service": "mamabot", "admin": "restricted-by-deployment"})
