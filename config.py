import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "owner@example.com")
    OWNER_PASSWORD = os.environ.get("OWNER_PASSWORD", "change-this-password")

    DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
    DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "http://localhost:5000/auth/discord/callback")
    DISCORD_BOT_TOKEN = os.environ.get("TOKEN", "")

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

    FIREBASE_DATABASE_URL = os.environ.get("FIREBASE_DATABASE_URL", "https://web-massaging-589b7-default-rtdb.firebaseio.com")
    FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "web-massaging-589b7")
    FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET", "web-massaging-589b7.firebasestorage.app")

    FREEFIRE_API_BASE = "https://freefiremobile.com"
    BOOYAH_API_BASE = "https://booyah.live/api"

    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    RATE_LIMIT = "100 per minute"

    ADSTERRA_BANNER_ID = os.environ.get("ADSTERRA_BANNER_ID", "")
    ADSTERRA_NATIVE_ID = os.environ.get("ADSTERRA_NATIVE_ID", "")
    ADSTERRA_SOCIAL_BAR = os.environ.get("ADSTERRA_SOCIAL_BAR", "")
    ADSTERRA_SMART_LINK = os.environ.get("ADSTERRA_SMART_LINK", "")
    ADSTERRA_POPUP = os.environ.get("ADSTERRA_POPUP", "")

    WEBSITE_NAME = "MJ Developer Platform"
    WEBSITE_DESCRIPTION = "The Ultimate Free Fire Utility Platform"
    WEBSITE_VERSION = "1.0.0"
