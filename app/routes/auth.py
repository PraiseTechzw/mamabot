"""
app/routes/auth.py
Simple session-based admin authentication.
No user database needed — single admin password set via environment variable.
"""

from flask import (Blueprint, render_template_string, request,
                   session, redirect, url_for, jsonify, current_app)
from functools import wraps
import hmac
from urllib.parse import urlparse

auth_bp = Blueprint("auth", __name__)

# ── Login required decorator ──────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            if request.path.startswith("/admin/"):
                return jsonify({"error": "Unauthorised"}), 401
            # API endpoints return JSON 401
            if request.path.startswith("/api/") and \
               not request.path in ("/api/messages", "/api/stats", "/api/health"):
                return jsonify({"error": "Unauthorised"}), 401
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


# ── Login page ────────────────────────────────────────────────────────────────
LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MamaBot Admin Login</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#1F4E79 0%,#2E74B5 100%);
       min-height:100vh;display:flex;align-items:center;justify-content:center;}
  .card{background:#fff;border-radius:16px;padding:2.5rem 2rem;width:100%;max-width:380px;
        box-shadow:0 20px 60px rgba(0,0,0,.25);}
  .logo{text-align:center;margin-bottom:1.5rem;}
  .logo .emoji{font-size:3rem;display:block;margin-bottom:.5rem;}
  .logo h1{font-size:1.4rem;font-weight:700;color:#1F4E79;}
  .logo p{font-size:.85rem;color:#6B7280;margin-top:4px;}
  label{display:block;font-size:.82rem;font-weight:600;color:#374151;margin-bottom:6px;}
  input[type=password]{width:100%;padding:.7rem 1rem;border:1.5px solid #DDE3EE;border-radius:10px;
    font-size:.95rem;outline:none;transition:border .2s;}
  input[type=password]:focus{border-color:#2E74B5;}
  .btn{width:100%;padding:.8rem;background:#1F4E79;color:#fff;border:none;border-radius:10px;
       font-size:1rem;font-weight:600;cursor:pointer;margin-top:1.25rem;transition:background .2s;}
  .btn:hover{background:#2E74B5;}
  .error{background:#FFEBEE;color:#C00000;border-radius:8px;padding:.6rem .9rem;
          font-size:.83rem;margin-bottom:1rem;display:{% if error %}block{% else %}none{% endif %};}
  .public-link{text-align:center;margin-top:1.25rem;font-size:.82rem;color:#6B7280;}
  .public-link a{color:#1F4E79;font-weight:600;text-decoration:none;}
  .public-link a:hover{text-decoration:underline;}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <span class="emoji">🔐</span>
    <h1>MamaBot Admin</h1>
    <p>Enter your admin password to continue</p>
  </div>
  {% if error %}
  <div class="error">❌ {{ error }}</div>
  {% endif %}
  <form method="POST">
    <label for="password">Admin Password</label>
    <input type="password" id="password" name="password"
           placeholder="Enter password" autofocus autocomplete="current-password">
    <button type="submit" class="btn">Sign In →</button>
  </form>
  <div class="public-link">
    Looking for the chat?
    <a href="/chat">Open MamaBot Chat ↗</a>
  </div>
</div>
</body>
</html>"""


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        pwd = request.form.get("password", "")
        admin_password = current_app.config.get("ADMIN_PASSWORD")
        if admin_password and hmac.compare_digest(pwd, admin_password):
            session["admin_logged_in"] = True
            session.permanent = True
            next_url = request.args.get("next", "/")
            parsed_next = urlparse(next_url)
            if parsed_next.scheme or parsed_next.netloc or not next_url.startswith("/"):
                next_url = "/"
            return redirect(next_url)
        error = (
            "Admin login is not configured."
            if not admin_password
            else "Incorrect password. Please try again."
        )
    return render_template_string(LOGIN_HTML, error=error)


@auth_bp.route("/admin/logout")
def logout():
    session.clear()
    return redirect("/chat")
