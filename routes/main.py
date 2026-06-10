from flask import Blueprint, render_template, request
import firebase_service as fb

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    announcements = fb.get_announcements()[:5]
    partners = [p for p in fb.get_partners() if p.get("status") == "approved"][:6]
    updates = fb.get_updates()[:5]
    faq = fb.get_faq()[:6]
    analytics = fb.get_analytics()
    guilds = fb.get_guilds()[:6]
    return render_template("index.html",
                           announcements=announcements,
                           partners=partners,
                           updates=updates,
                           faq=faq,
                           analytics=analytics,
                           guilds=guilds)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/faq")
def faq():
    q = request.args.get("q", "").lower()
    items = fb.get_faq()
    if q:
        items = [f for f in items if q in f.get("question", "").lower() or q in f.get("answer", "").lower()]
    return render_template("faq.html", faq=items, query=q)


@main_bp.route("/updates")
def updates():
    items = fb.get_updates()
    return render_template("updates.html", updates=items)


@main_bp.route("/announcements")
def announcements():
    items = fb.get_announcements()
    return render_template("announcements.html", announcements=items)


@main_bp.route("/partners")
def partners():
    items = [p for p in fb.get_partners() if p.get("status") == "approved"]
    featured = [p for p in items if p.get("featured")]
    regular = [p for p in items if not p.get("featured")]
    return render_template("partners.html", featured=featured, partners=regular)


@main_bp.route("/guilds")
def guilds():
    items = fb.get_guilds()
    return render_template("guilds.html", guilds=items)


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")


@main_bp.route("/privacy")
def privacy():
    page = fb.get_page("privacy") or {}
    return render_template("privacy.html", page=page)


@main_bp.route("/terms")
def terms():
    page = fb.get_page("terms") or {}
    return render_template("terms.html", page=page)


@main_bp.route("/partner/apply", methods=["GET", "POST"])
def partner_apply():
    from flask import flash, redirect, url_for, session
    from datetime import datetime
    if request.method == "POST":
        data = {
            "server_name": request.form.get("server_name", ""),
            "server_invite": request.form.get("server_invite", ""),
            "owner_discord_id": request.form.get("owner_discord_id", ""),
            "description": request.form.get("description", ""),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "submitted_by": session.get("user", {}).get("uid", "anonymous")
        }
        fb.create_partner(data)
        flash("Partner application submitted! We will review it soon.", "success")
        return redirect(url_for("main.partners"))
    return render_template("partner_apply.html")
