import hashlib
import uuid
import secrets
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, jsonify
)
import requests
from config import Config
import firebase_service as fb

auth_bp = Blueprint("auth", __name__)

DISCORD_API = "https://discord.com/api/v10"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def create_user_session(uid, email, name, avatar, role, method="email"):
    perms = fb.get_permissions(uid) or []
    session["user"] = {
        "uid": uid,
        "email": email,
        "name": name,
        "avatar": avatar,
        "role": role,
        "permissions": perms,
        "login_method": method
    }
    session.permanent = True


# ─── Login / Register ───────────────────────────────────────────────────────

@auth_bp.route("/login")
def login_page():
    if "user" in session:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if email == Config.OWNER_EMAIL.lower() and password == Config.OWNER_PASSWORD:
        uid = "owner"
        fb.log_login(uid, "email", request.remote_addr, True)
        create_user_session(uid, email, "Owner", "", "owner", "email")
        flash("Welcome back, Owner!", "success")
        return redirect(url_for("owner.owner_panel"))

    all_users = fb.get_all_users()
    user = next((u for u in all_users if u.get("email", "").lower() == email), None)
    if not user:
        flash("Invalid email or password.", "danger")
        fb.log_login("unknown", "email", request.remote_addr, False)
        return redirect(url_for("auth.login_page"))

    if user.get("password_hash") != hash_password(password):
        flash("Invalid email or password.", "danger")
        fb.log_login(user.get("uid", "?"), "email", request.remote_addr, False)
        return redirect(url_for("auth.login_page"))

    if not user.get("email_verified"):
        flash("Please verify your email first.", "warning")
        return redirect(url_for("auth.login_page"))

    uid = user["uid"]
    role = user.get("role", "user")
    fb.log_login(uid, "email", request.remote_addr, True)
    create_user_session(uid, email, user.get("name", ""), user.get("avatar", ""), role, "email")
    flash("Login successful!", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        all_users = fb.get_all_users()
        if any(u.get("email", "").lower() == email for u in all_users):
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        uid = str(uuid.uuid4())[:12]
        fb.set_user(uid, {
            "uid": uid,
            "name": name,
            "email": email,
            "password_hash": hash_password(password),
            "role": "user",
            "avatar": "",
            "email_verified": True,
            "created_at": datetime.utcnow().isoformat(),
            "login_method": "email"
        })
        flash("Account created! You can now login.", "success")
        return redirect(url_for("auth.login_page"))
    return render_template("auth/register.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login_page"))
    return render_template("auth/forgot_password.html")


# ─── Discord OAuth ───────────────────────────────────────────────────────────

@auth_bp.route("/discord")
def discord_login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    params = {
        "client_id": Config.DISCORD_CLIENT_ID,
        "redirect_uri": Config.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify email",
        "state": state
    }
    from urllib.parse import urlencode
    url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
    return redirect(url)


@auth_bp.route("/discord/callback")
def discord_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or state != session.pop("oauth_state", None):
        flash("Discord login failed. Please try again.", "danger")
        return redirect(url_for("auth.login_page"))

    token_data = {
        "client_id": Config.DISCORD_CLIENT_ID,
        "client_secret": Config.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": Config.DISCORD_REDIRECT_URI,
    }
    token_resp = requests.post(f"{DISCORD_API}/oauth2/token", data=token_data)
    if token_resp.status_code != 200:
        flash("Discord authentication error.", "danger")
        return redirect(url_for("auth.login_page"))

    token = token_resp.json().get("access_token")
    user_resp = requests.get(f"{DISCORD_API}/users/@me",
                             headers={"Authorization": f"Bearer {token}"})
    discord_user = user_resp.json()
    discord_id = discord_user.get("id")
    name = discord_user.get("global_name") or discord_user.get("username", "")
    email = discord_user.get("email", f"{discord_id}@discord.local")
    avatar_hash = discord_user.get("avatar")
    avatar = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png" if avatar_hash else ""

    all_users = fb.get_all_users()
    user = next((u for u in all_users if u.get("discord_id") == discord_id), None)

    if not user:
        uid = str(uuid.uuid4())[:12]
        fb.set_user(uid, {
            "uid": uid,
            "name": name,
            "email": email,
            "avatar": avatar,
            "discord_id": discord_id,
            "role": "user",
            "email_verified": True,
            "created_at": datetime.utcnow().isoformat(),
            "login_method": "discord"
        })
        role = "user"
    else:
        uid = user["uid"]
        role = user.get("role", "user")
        fb.update(f"users/{uid}", {"avatar": avatar, "name": name})

    fb.log_login(uid, "discord", request.remote_addr, True)
    create_user_session(uid, email, name, avatar, role, "discord")
    flash(f"Welcome, {name}!", "success")
    return redirect(url_for("main.index"))


# ─── Google OAuth ────────────────────────────────────────────────────────────

@auth_bp.route("/google")
def google_login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    from urllib.parse import urlencode
    params = {
        "client_id": Config.GOOGLE_CLIENT_ID,
        "redirect_uri": Config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline"
    }
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")


@auth_bp.route("/google/callback")
def google_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or state != session.pop("oauth_state", None):
        flash("Google login failed.", "danger")
        return redirect(url_for("auth.login_page"))

    token_resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code": code,
        "client_id": Config.GOOGLE_CLIENT_ID,
        "client_secret": Config.GOOGLE_CLIENT_SECRET,
        "redirect_uri": Config.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    })
    if token_resp.status_code != 200:
        flash("Google authentication error.", "danger")
        return redirect(url_for("auth.login_page"))

    access_token = token_resp.json().get("access_token")
    info_resp = requests.get(GOOGLE_USERINFO_URL,
                             headers={"Authorization": f"Bearer {access_token}"})
    guser = info_resp.json()
    google_id = guser.get("sub")
    name = guser.get("name", "")
    email = guser.get("email", "")
    avatar = guser.get("picture", "")

    all_users = fb.get_all_users()
    user = next((u for u in all_users if u.get("google_id") == google_id), None)

    if not user:
        uid = str(uuid.uuid4())[:12]
        fb.set_user(uid, {
            "uid": uid,
            "name": name,
            "email": email,
            "avatar": avatar,
            "google_id": google_id,
            "role": "user",
            "email_verified": True,
            "created_at": datetime.utcnow().isoformat(),
            "login_method": "google"
        })
        role = "user"
    else:
        uid = user["uid"]
        role = user.get("role", "user")
        fb.update(f"users/{uid}", {"avatar": avatar})

    fb.log_login(uid, "google", request.remote_addr, True)
    create_user_session(uid, email, name, avatar, role, "google")
    flash(f"Welcome, {name}!", "success")
    return redirect(url_for("main.index"))


# ─── Logout / Dashboard ──────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login_page"))
    user = session["user"]
    uid = user.get("uid")
    full_user = fb.get_user(uid) or user
    return render_template("auth/dashboard.html", user=full_user)


@auth_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect(url_for("auth.login_page"))
    user = session["user"]
    uid = user.get("uid")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        fb.set_user(uid, {"name": name})
        session["user"]["name"] = name
        flash("Settings updated.", "success")
        return redirect(url_for("auth.settings"))

    full_user = fb.get_user(uid) or user
    return render_template("auth/settings.html", user=full_user)
