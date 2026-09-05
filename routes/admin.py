from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/status")
def status():
    configured_token = current_app.config.get("ADMIN_TOKEN", "")
    if not current_app.testing and configured_token:
        if request.headers.get("X-Admin-Token") != configured_token:
            return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"service": "mamabot", "admin": "restricted-by-deployment"})
