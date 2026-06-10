import os
import json
import requests
from config import Config

FIREBASE_DB_URL = Config.FIREBASE_DATABASE_URL.rstrip("/")


def _url(path):
    return f"{FIREBASE_DB_URL}/{path.strip('/')}.json"


def get(path):
    try:
        r = requests.get(_url(path), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[Firebase GET Error] {path}: {e}")
        return None


def set(path, data):
    try:
        r = requests.put(_url(path), json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[Firebase SET Error] {path}: {e}")
        return None


def push(path, data):
    try:
        r = requests.post(_url(path), json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[Firebase PUSH Error] {path}: {e}")
        return None


def update(path, data):
    try:
        r = requests.patch(_url(path), json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[Firebase UPDATE Error] {path}: {e}")
        return None


def delete(path):
    try:
        r = requests.delete(_url(path), timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[Firebase DELETE Error] {path}: {e}")
        return False


def get_all_users():
    data = get("users") or {}
    return [{"uid": k, **v} for k, v in data.items()]


def get_user(uid):
    return get(f"users/{uid}")


def set_user(uid, data):
    return update(f"users/{uid}", data)


def get_all_admins():
    data = get("admins") or {}
    return [{"uid": k, **v} for k, v in data.items()]


def get_admin(uid):
    return get(f"admins/{uid}")


def set_admin(uid, data):
    return update(f"admins/{uid}", data)


def delete_admin(uid):
    return delete(f"admins/{uid}")


def get_announcements():
    data = get("announcements") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def get_announcement(aid):
    return get(f"announcements/{aid}")


def create_announcement(data):
    return push("announcements", data)


def update_announcement(aid, data):
    return update(f"announcements/{aid}", data)


def delete_announcement(aid):
    return delete(f"announcements/{aid}")


def get_partners():
    data = get("partners") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    return items


def get_partner(pid):
    return get(f"partners/{pid}")


def create_partner(data):
    return push("partners", data)


def update_partner(pid, data):
    return update(f"partners/{pid}", data)


def delete_partner(pid):
    return delete(f"partners/{pid}")


def get_guilds():
    data = get("guilds") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    return items


def get_pages():
    data = get("pages") or {}
    return data


def get_page(slug):
    return get(f"pages/{slug}")


def set_page(slug, data):
    return set(f"pages/{slug}", data)


def delete_page(slug):
    return delete(f"pages/{slug}")


def get_updates():
    data = get("updates") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def create_update(data):
    return push("updates", data)


def update_update(uid, data):
    return update(f"updates/{uid}", data)


def delete_update(uid):
    return delete(f"updates/{uid}")


def get_faq():
    data = get("faq") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    items.sort(key=lambda x: x.get("order", 999))
    return items


def create_faq(data):
    return push("faq", data)


def update_faq(fid, data):
    return update(f"faq/{fid}", data)


def delete_faq(fid):
    return delete(f"faq/{fid}")


def get_media():
    data = get("media") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    items.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return items


def add_media(data):
    return push("media", data)


def delete_media(mid):
    return delete(f"media/{mid}")


def get_analytics():
    return get("analytics") or {}


def increment_analytics(key, amount=1):
    data = get(f"analytics/{key}") or 0
    return set(f"analytics/{key}", data + amount)


def log_action(action_type, user_id, details=""):
    from datetime import datetime
    import uuid
    log_id = str(uuid.uuid4())[:8]
    data = {
        "type": action_type,
        "user_id": user_id,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    return set(f"logs/{log_id}", data)


def log_login(user_id, method, ip, success=True):
    from datetime import datetime
    import uuid
    log_id = str(uuid.uuid4())[:8]
    data = {
        "user_id": user_id,
        "method": method,
        "ip": ip,
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    }
    return set(f"login_logs/{log_id}", data)


def get_logs():
    data = get("logs") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items[:200]


def get_login_logs():
    data = get("login_logs") or {}
    items = [{"id": k, **v} for k, v in data.items()]
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items[:200]


def get_permissions(uid):
    return get(f"permissions/{uid}") or []


def set_permissions(uid, perms):
    return set(f"permissions/{uid}", perms)


def get_settings():
    return get("settings") or {}


def update_settings(data):
    return update("settings", data)


def get_ads():
    return get("ads") or {}


def update_ads(data):
    return update("ads", data)


def get_subscriptions():
    data = get("subscriptions") or {}
    return [{"id": k, **v} for k, v in data.items()]


def check_firebase_connection():
    try:
        r = requests.get(_url(".info/connected"), timeout=5)
        return r.status_code == 200
    except Exception:
        return False
