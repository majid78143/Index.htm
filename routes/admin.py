from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import firebase_service as fb
from app import admin_required, has_permission

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@admin_required
def admin_panel():
    analytics = fb.get_analytics()
    users = fb.get_all_users()
    admins = fb.get_all_admins()
    return render_template("admin/dashboard.html",
                           analytics=analytics,
                           user_count=len(users),
                           admin_count=len(admins))


# ─── Users ───────────────────────────────────────────────────────────────────

@admin_bp.route("/users")
@admin_required
@has_permission("manage_users")
def users():
    all_users = fb.get_all_users()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<uid>/role", methods=["POST"])
@admin_required
@has_permission("manage_users")
def set_user_role(uid):
    role = request.form.get("role", "user")
    fb.set_user(uid, {"role": role})
    fb.log_action("set_role", session["user"]["uid"], f"Set {uid} role to {role}")
    flash("User role updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<uid>/ban", methods=["POST"])
@admin_required
@has_permission("manage_users")
def ban_user(uid):
    fb.set_user(uid, {"banned": True})
    fb.log_action("ban_user", session["user"]["uid"], f"Banned {uid}")
    flash("User banned.", "warning")
    return redirect(url_for("admin.users"))


# ─── Admins ──────────────────────────────────────────────────────────────────

@admin_bp.route("/admins")
@admin_required
def admins():
    all_admins = fb.get_all_admins()
    return render_template("admin/admins.html", admins=all_admins)


@admin_bp.route("/admins/add", methods=["POST"])
@admin_required
def add_admin():
    uid = request.form.get("uid", "").strip()
    role = request.form.get("role", "admin")
    name = request.form.get("name", "")
    if uid:
        fb.set_admin(uid, {
            "uid": uid, "name": name, "role": role,
            "added_at": datetime.utcnow().isoformat(),
            "added_by": session["user"]["uid"]
        })
        fb.set_user(uid, {"role": role})
        fb.log_action("add_admin", session["user"]["uid"], f"Added admin {uid}")
        flash("Admin added.", "success")
    return redirect(url_for("admin.admins"))


@admin_bp.route("/admins/<uid>/remove", methods=["POST"])
@admin_required
def remove_admin(uid):
    fb.delete_admin(uid)
    fb.set_user(uid, {"role": "user"})
    fb.log_action("remove_admin", session["user"]["uid"], f"Removed admin {uid}")
    flash("Admin removed.", "success")
    return redirect(url_for("admin.admins"))


# ─── Permissions ─────────────────────────────────────────────────────────────

@admin_bp.route("/permissions/<uid>", methods=["GET", "POST"])
@admin_required
def permissions(uid):
    all_perms = [
        "manage_users", "manage_pages", "manage_announcements",
        "manage_partners", "manage_guilds", "manage_tools",
        "manage_ads", "manage_settings", "manage_media",
        "manage_logs", "manage_analytics"
    ]
    if request.method == "POST":
        selected = request.form.getlist("permissions")
        fb.set_permissions(uid, selected)
        fb.log_action("edit_permissions", session["user"]["uid"], f"Edited permissions for {uid}")
        flash("Permissions updated.", "success")
        return redirect(url_for("admin.admins"))
    current = fb.get_permissions(uid) or []
    return render_template("admin/permissions.html", uid=uid, all_perms=all_perms, current=current)


# ─── Announcements ───────────────────────────────────────────────────────────

@admin_bp.route("/announcements")
@admin_required
@has_permission("manage_announcements")
def announcements():
    items = fb.get_announcements()
    return render_template("admin/announcements.html", announcements=items)


@admin_bp.route("/announcements/create", methods=["GET", "POST"])
@admin_required
@has_permission("manage_announcements")
def create_announcement():
    if request.method == "POST":
        data = {
            "title": request.form.get("title", ""),
            "content": request.form.get("content", ""),
            "type": request.form.get("type", "info"),
            "pinned": bool(request.form.get("pinned")),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": session["user"]["uid"]
        }
        fb.create_announcement(data)
        fb.log_action("create_announcement", session["user"]["uid"], data["title"])
        flash("Announcement created.", "success")
        return redirect(url_for("admin.announcements"))
    return render_template("admin/announcement_form.html", announcement=None)


@admin_bp.route("/announcements/<aid>/edit", methods=["GET", "POST"])
@admin_required
@has_permission("manage_announcements")
def edit_announcement(aid):
    item = fb.get_announcement(aid) or {}
    if request.method == "POST":
        data = {
            "title": request.form.get("title", ""),
            "content": request.form.get("content", ""),
            "type": request.form.get("type", "info"),
            "pinned": bool(request.form.get("pinned")),
            "updated_at": datetime.utcnow().isoformat()
        }
        fb.update_announcement(aid, data)
        flash("Announcement updated.", "success")
        return redirect(url_for("admin.announcements"))
    return render_template("admin/announcement_form.html", announcement={"id": aid, **item})


@admin_bp.route("/announcements/<aid>/delete", methods=["POST"])
@admin_required
@has_permission("manage_announcements")
def delete_announcement(aid):
    fb.delete_announcement(aid)
    flash("Announcement deleted.", "success")
    return redirect(url_for("admin.announcements"))


# ─── Partners ────────────────────────────────────────────────────────────────

@admin_bp.route("/partners")
@admin_required
@has_permission("manage_partners")
def partners():
    items = fb.get_partners()
    return render_template("admin/partners.html", partners=items)


@admin_bp.route("/partners/<pid>/approve", methods=["POST"])
@admin_required
@has_permission("manage_partners")
def approve_partner(pid):
    fb.update_partner(pid, {"status": "approved", "approved_by": session["user"]["uid"]})
    flash("Partner approved.", "success")
    return redirect(url_for("admin.partners"))


@admin_bp.route("/partners/<pid>/reject", methods=["POST"])
@admin_required
@has_permission("manage_partners")
def reject_partner(pid):
    fb.update_partner(pid, {"status": "rejected"})
    flash("Partner rejected.", "warning")
    return redirect(url_for("admin.partners"))


@admin_bp.route("/partners/<pid>/feature", methods=["POST"])
@admin_required
@has_permission("manage_partners")
def feature_partner(pid):
    partner = fb.get_partner(pid) or {}
    fb.update_partner(pid, {"featured": not partner.get("featured", False)})
    flash("Partner featured status toggled.", "success")
    return redirect(url_for("admin.partners"))


@admin_bp.route("/partners/<pid>/delete", methods=["POST"])
@admin_required
@has_permission("manage_partners")
def delete_partner(pid):
    fb.delete_partner(pid)
    flash("Partner deleted.", "success")
    return redirect(url_for("admin.partners"))


# ─── Pages ───────────────────────────────────────────────────────────────────

@admin_bp.route("/pages")
@admin_required
@has_permission("manage_pages")
def pages():
    data = fb.get_pages() or {}
    return render_template("admin/pages.html", pages=data)


@admin_bp.route("/pages/<slug>/edit", methods=["GET", "POST"])
@admin_required
@has_permission("manage_pages")
def edit_page(slug):
    page = fb.get_page(slug) or {"slug": slug, "title": slug.title(), "content": ""}
    if request.method == "POST":
        fb.set_page(slug, {
            "slug": slug,
            "title": request.form.get("title", ""),
            "content": request.form.get("content", ""),
            "updated_at": datetime.utcnow().isoformat()
        })
        flash("Page saved.", "success")
        return redirect(url_for("admin.pages"))
    return render_template("admin/page_form.html", page=page)


# ─── Updates ─────────────────────────────────────────────────────────────────

@admin_bp.route("/updates")
@admin_required
def updates():
    items = fb.get_updates()
    return render_template("admin/updates.html", updates=items)


@admin_bp.route("/updates/create", methods=["GET", "POST"])
@admin_required
def create_update():
    if request.method == "POST":
        data = {
            "title": request.form.get("title", ""),
            "content": request.form.get("content", ""),
            "version": request.form.get("version", ""),
            "type": request.form.get("type", "website"),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": session["user"]["uid"]
        }
        fb.create_update(data)
        flash("Update published.", "success")
        return redirect(url_for("admin.updates"))
    return render_template("admin/update_form.html", update=None)


@admin_bp.route("/updates/<uid>/delete", methods=["POST"])
@admin_required
def delete_update(uid):
    fb.delete_update(uid)
    flash("Update deleted.", "success")
    return redirect(url_for("admin.updates"))


# ─── FAQ ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/faq")
@admin_required
def faq():
    items = fb.get_faq()
    return render_template("admin/faq.html", faq=items)


@admin_bp.route("/faq/create", methods=["GET", "POST"])
@admin_required
def create_faq():
    if request.method == "POST":
        data = {
            "question": request.form.get("question", ""),
            "answer": request.form.get("answer", ""),
            "order": int(request.form.get("order", 99)),
            "created_at": datetime.utcnow().isoformat()
        }
        fb.create_faq(data)
        flash("FAQ added.", "success")
        return redirect(url_for("admin.faq"))
    return render_template("admin/faq_form.html", item=None)


@admin_bp.route("/faq/<fid>/edit", methods=["GET", "POST"])
@admin_required
def edit_faq(fid):
    item = fb.get(f"faq/{fid}") or {}
    if request.method == "POST":
        fb.update_faq(fid, {
            "question": request.form.get("question", ""),
            "answer": request.form.get("answer", ""),
            "order": int(request.form.get("order", 99))
        })
        flash("FAQ updated.", "success")
        return redirect(url_for("admin.faq"))
    return render_template("admin/faq_form.html", item={"id": fid, **item})


@admin_bp.route("/faq/<fid>/delete", methods=["POST"])
@admin_required
def delete_faq(fid):
    fb.delete_faq(fid)
    flash("FAQ deleted.", "success")
    return redirect(url_for("admin.faq"))


# ─── Media ───────────────────────────────────────────────────────────────────

@admin_bp.route("/media")
@admin_required
@has_permission("manage_media")
def media():
    items = fb.get_media()
    return render_template("admin/media.html", media=items)


@admin_bp.route("/media/add", methods=["POST"])
@admin_required
@has_permission("manage_media")
def add_media():
    url_input = request.form.get("url", "").strip()
    label = request.form.get("label", "")
    media_type = request.form.get("media_type", "image")
    if url_input:
        fb.add_media({
            "url": url_input,
            "label": label,
            "type": media_type,
            "uploaded_at": datetime.utcnow().isoformat(),
            "uploaded_by": session["user"]["uid"]
        })
        flash("Media added.", "success")
    return redirect(url_for("admin.media"))


@admin_bp.route("/media/<mid>/delete", methods=["POST"])
@admin_required
@has_permission("manage_media")
def delete_media(mid):
    fb.delete_media(mid)
    flash("Media deleted.", "success")
    return redirect(url_for("admin.media"))


# ─── Ads ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/ads", methods=["GET", "POST"])
@admin_required
@has_permission("manage_ads")
def ads():
    ads_data = fb.get_ads()
    if request.method == "POST":
        fb.update_ads({
            "enabled": bool(request.form.get("enabled")),
            "banner_id": request.form.get("banner_id", ""),
            "native_id": request.form.get("native_id", ""),
            "social_bar": request.form.get("social_bar", ""),
            "smart_link": request.form.get("smart_link", ""),
            "popup": request.form.get("popup", ""),
            "show_banner": bool(request.form.get("show_banner")),
            "show_native": bool(request.form.get("show_native")),
            "show_popup": bool(request.form.get("show_popup")),
            "show_social_bar": bool(request.form.get("show_social_bar"))
        })
        flash("Ads settings saved.", "success")
        return redirect(url_for("admin.ads"))
    return render_template("admin/ads.html", ads=ads_data)


# ─── Analytics ───────────────────────────────────────────────────────────────

@admin_bp.route("/analytics")
@admin_required
@has_permission("manage_analytics")
def analytics():
    data = fb.get_analytics()
    return render_template("admin/analytics.html", analytics=data)


# ─── Logs ────────────────────────────────────────────────────────────────────

@admin_bp.route("/logs")
@admin_required
@has_permission("manage_logs")
def logs():
    action_logs = fb.get_logs()
    login_logs = fb.get_login_logs()
    return render_template("admin/logs.html", logs=action_logs, login_logs=login_logs)
