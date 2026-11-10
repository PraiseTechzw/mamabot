"""
app/__init__.py
Flask application factory — Supabase version (no SQLAlchemy).
"""

import os
import secrets
from flask import Flask
from config import config
from datetime import timedelta


def create_app(config_name="default"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    if not app.config.get("SECRET_KEY"):
        if config_name == "production":
            raise RuntimeError("SECRET_KEY must be configured in production")
        app.config["SECRET_KEY"] = secrets.token_hex(32)
    if config_name == "production" and not app.config.get("ADMIN_PASSWORD"):
        raise RuntimeError("ADMIN_PASSWORD must be configured in production")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

    os.makedirs(app.instance_path, exist_ok=True)

    # Register blueprints
    from app.routes.auth      import auth_bp
    from app.routes.webhook   import webhook_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin     import admin_bp
    from app.routes.smspop    import smspop_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(smspop_bp)

    app.logger.info("MamaBot application initialized")
    return app
