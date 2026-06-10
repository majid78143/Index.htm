from flask import Blueprint, jsonify, request
import firebase_service as fb
from config import Config

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "firebase": fb.check_firebase_connection()})


@api_bp.route("/analytics")
def analytics():
    data = fb.get_analytics() or {}
    return jsonify(data)


@api_bp.route("/announcements")
def announcements():
    items = fb.get_announcements()
    return jsonify(items)


@api_bp.route("/partners")
def partners():
    items = [p for p in fb.get_partners() if p.get("status") == "approved"]
    return jsonify(items)


@api_bp.route("/updates")
def updates():
    items = fb.get_updates()
    return jsonify(items)


@api_bp.route("/faq")
def faq():
    items = fb.get_faq()
    return jsonify(items)


@api_bp.route("/settings/public")
def public_settings():
    settings = fb.get_settings() or {}
    safe = {
        "website_name": settings.get("website_name", Config.WEBSITE_NAME),
        "primary_color": settings.get("primary_color", "#0d6efd"),
        "secondary_color": settings.get("secondary_color", "#6c757d"),
        "logo_url": settings.get("logo_url", ""),
        "favicon_url": settings.get("favicon_url", ""),
        "footer_text": settings.get("footer_text", ""),
        "maintenance_mode": settings.get("maintenance_mode", False),
        "ads_enabled": settings.get("ads_enabled", False),
    }
    return jsonify(safe)
