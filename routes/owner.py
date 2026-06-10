from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import firebase_service as fb
from app import owner_required
from config import Config

owner_bp = Blueprint("owner", __name__)


@owner_bp.route("/")
@owner_required
def owner_panel():
    analytics = fb.get_analytics()
    settings = fb.get_settings()
    users = fb.get_all_users()
    admins = fb.get_all_admins()
    return render_template("owner/panel.html",
                           analytics=analytics,
                           settings=settings,
                           user_count=len(users),
                           admin_count=len(admins))


# ─── Settings ────────────────────────────────────────────────────────────────

@owner_bp.route("/settings", methods=["GET", "POST"])
@owner_required
def settings():
    current = fb.get_settings()
    if request.method == "POST":
        fb.update_settings({
            "website_name": request.form.get("website_name", Config.WEBSITE_NAME),
            "website_description": request.form.get("website_description", ""),
            "primary_color": request.form.get("primary_color", "#0d6efd"),
            "secondary_color": request.form.get("secondary_color", "#6c757d"),
            "footer_text": request.form.get("footer_text", ""),
            "custom_css": request.form.get("custom_css", ""),
            "maintenance_mode": bool(request.form.get("maintenance_mode")),
            "updated_at": datetime.utcnow().isoformat()
        })
        flash("Settings saved.", "success")
        return redirect(url_for("owner.settings"))
    return render_template("owner/settings.html", settings=current)


# ─── Theme ───────────────────────────────────────────────────────────────────

@owner_bp.route("/theme", methods=["GET", "POST"])
@owner_required
def theme():
    settings = fb.get_settings()
    if request.method == "POST":
        updates = {
            "logo_url": request.form.get("logo_url", ""),
            "favicon_url": request.form.get("favicon_url", ""),
            "hero_image": request.form.get("hero_image", ""),
            "primary_color": request.form.get("primary_color", "#0d6efd"),
            "secondary_color": request.form.get("secondary_color", "#6c757d"),
            "footer_text": request.form.get("footer_text", ""),
        }
        fb.update_settings(updates)
        flash("Theme updated.", "success")
        return redirect(url_for("owner.theme"))
    return render_template("owner/theme.html", settings=settings)


# ─── Admins ──────────────────────────────────────────────────────────────────

@owner_bp.route("/admins")
@owner_required
def admins():
    all_admins = fb.get_all_admins()
    roles = ["super_admin", "admin", "moderator", "partner_manager", "content_manager", "support_staff"]
    return render_template("owner/admins.html", admins=all_admins, roles=roles)


@owner_bp.route("/admins/add", methods=["POST"])
@owner_required
def add_admin():
    uid = request.form.get("uid", "").strip()
    role = request.form.get("role", "admin")
    name = request.form.get("name", "").strip()
    if uid:
        fb.set_admin(uid, {
            "uid": uid, "name": name, "role": role,
            "added_at": datetime.utcnow().isoformat(),
            "added_by": "owner"
        })
        fb.set_user(uid, {"role": role})
        fb.log_action("add_admin", "owner", f"Added {role}: {uid}")
        flash(f"Admin {name or uid} added.", "success")
    return redirect(url_for("owner.admins"))


@owner_bp.route("/admins/<uid>/remove", methods=["POST"])
@owner_required
def remove_admin(uid):
    fb.delete_admin(uid)
    fb.set_user(uid, {"role": "user"})
    fb.log_action("remove_admin", "owner", f"Removed admin {uid}")
    flash("Admin removed.", "success")
    return redirect(url_for("owner.admins"))


# ─── Analytics ───────────────────────────────────────────────────────────────

@owner_bp.route("/analytics")
@owner_required
def analytics():
    data = fb.get_analytics()
    return render_template("owner/analytics.html", analytics=data)


# ─── Logs ────────────────────────────────────────────────────────────────────

@owner_bp.route("/logs")
@owner_required
def logs():
    action_logs = fb.get_logs()
    login_logs = fb.get_login_logs()
    return render_template("owner/logs.html", logs=action_logs, login_logs=login_logs)


# ─── Maintenance ─────────────────────────────────────────────────────────────

@owner_bp.route("/maintenance", methods=["POST"])
@owner_required
def toggle_maintenance():
    settings = fb.get_settings()
    new_val = not settings.get("maintenance_mode", False)
    fb.update_settings({"maintenance_mode": new_val})
    fb.log_action("maintenance_toggle", "owner", f"Maintenance: {new_val}")
    flash(f"Maintenance mode {'enabled' if new_val else 'disabled'}.", "info")
    return redirect(url_for("owner.owner_panel"))


# ─── Backup / Restore ────────────────────────────────────────────────────────

@owner_bp.route("/backup")
@owner_required
def backup():
    import json
    all_data = {
        "users": fb.get("users"),
        "admins": fb.get("admins"),
        "permissions": fb.get("permissions"),
        "partners": fb.get("partners"),
        "announcements": fb.get("announcements"),
        "guilds": fb.get("guilds"),
        "pages": fb.get("pages"),
        "updates": fb.get("updates"),
        "faq": fb.get("faq"),
        "media": fb.get("media"),
        "ads": fb.get("ads"),
        "settings": fb.get("settings"),
    }
    from flask import Response
    return Response(
        json.dumps(all_data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=backup.json"}
    )


@owner_bp.route("/restore", methods=["POST"])
@owner_required
def restore():
    import json
    f = request.files.get("backup_file")
    if not f:
        flash("No file uploaded.", "danger")
        return redirect(url_for("owner.owner_panel"))
    try:
        data = json.loads(f.read())
        for key, value in data.items():
            if value:
                fb.set(key, value)
        fb.log_action("restore_backup", "owner", "Backup restored")
        flash("Backup restored successfully.", "success")
    except Exception as e:
        flash(f"Restore failed: {str(e)}", "danger")
    return redirect(url_for("owner.owner_panel"))


# ─── API Management ──────────────────────────────────────────────────────────

@owner_bp.route("/apis", methods=["GET", "POST"])
@owner_required
def apis():
    settings = fb.get_settings()
    if request.method == "POST":
        fb.update_settings({
            "ff_api_key": request.form.get("ff_api_key", ""),
            "discord_webhook": request.form.get("discord_webhook", ""),
        })
        flash("API settings saved.", "success")
        return redirect(url_for("owner.apis"))
    return render_template("owner/apis.html", settings=settings)


# ─── Firebase Info ───────────────────────────────────────────────────────────

@owner_bp.route("/firebase")
@owner_required
def firebase_info():
    connected = fb.check_firebase_connection()
    db_url = Config.FIREBASE_DATABASE_URL
    project_id = Config.FIREBASE_PROJECT_ID
    bucket = Config.FIREBASE_STORAGE_BUCKET
    return render_template("owner/firebase.html",
                           connected=connected,
                           db_url=db_url,
                           project_id=project_id,
                           bucket=bucket)


# ─── Security ────────────────────────────────────────────────────────────────

@owner_bp.route("/security")
@owner_required
def security():
    security_logs = fb.get("security_logs") or {}
    items = [{"id": k, **v} for k, v in security_logs.items()]
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template("owner/security.html", security_logs=items[:100])
