import os
import json
import uuid
import hashlib
import traceback
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, abort, g
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests

from config import Config
import firebase_service as fb

app = Flask(__name__)
app.config.from_object(Config)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://"
)

# ──────────────────────────────────────────────
# Helpers / Decorators
# ──────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user", {})
        if user.get("role") != "owner":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user", {})
        if user.get("role") not in ("owner", "super_admin", "admin"):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def has_permission(perm):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = session.get("user", {})
            role = user.get("role", "")
            if role == "owner":
                return f(*args, **kwargs)
            perms = user.get("permissions", [])
            if perm not in perms:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_site_settings():
    try:
        settings = fb.get("settings") or {}
        return settings
    except Exception:
        return {}


@app.context_processor
def inject_globals():
    settings = get_site_settings()
    user = session.get("user", None)
    return dict(
        site=settings,
        current_user=user,
        website_name=settings.get("website_name", Config.WEBSITE_NAME),
        primary_color=settings.get("primary_color", "#0d6efd"),
        secondary_color=settings.get("secondary_color", "#6c757d"),
        ads_enabled=settings.get("ads_enabled", False),
        maintenance_mode=settings.get("maintenance_mode", False),
    )


@app.before_request
def check_maintenance():
    allowed = [
        "static", "auth.login_page", "auth.login_post",
        "auth.discord_login", "auth.discord_callback",
        "auth.google_login", "auth.google_callback",
        "owner.owner_panel",
    ]
    settings = get_site_settings()
    if settings.get("maintenance_mode") and request.endpoint not in allowed:
        user = session.get("user", {})
        if user.get("role") != "owner":
            return render_template("maintenance.html"), 503


# ──────────────────────────────────────────────
# Blueprints
# ──────────────────────────────────────────────

from routes.main import main_bp
from routes.auth import auth_bp
from routes.tools import tools_bp
from routes.admin import admin_bp
from routes.owner import owner_bp
from routes.api import api_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(tools_bp, url_prefix="/tools")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(owner_bp, url_prefix="/owner")
app.register_blueprint(api_bp, url_prefix="/api")


# ──────────────────────────────────────────────
# Error Handlers
# ──────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


@app.errorhandler(503)
def service_unavailable(e):
    return render_template("maintenance.html"), 503


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
