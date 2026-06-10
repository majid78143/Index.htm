"""
start.py — Unified startup script for Render Free Plan.
Runs the Discord bot in a background thread and Flask in the main thread.
Usage: python start.py
"""
import os
import sys
import threading
import logging

logging.basicConfig(level=logging.INFO, format="[MAIN] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def validate_env():
    """Check required environment variables before starting."""
    required = {
        "FIREBASE_DATABASE_URL": "Firebase Realtime Database URL",
        "SECRET_KEY": "Flask secret key",
    }
    missing = []
    for key, desc in required.items():
        if not os.environ.get(key):
            missing.append(f"  • {key} — {desc}")
    if missing:
        logger.warning("Missing environment variables (app will still start):")
        for m in missing:
            logger.warning(m)


def run_bot():
    """Start the Discord bot in a background thread."""
    token = os.environ.get("TOKEN", "")
    if not token:
        logger.warning("Discord bot TOKEN not set — bot will not start.")
        return
    try:
        logger.info("Starting Discord bot...")
        import bot
        bot.run_bot()
    except Exception as e:
        logger.error(f"Bot startup error: {e}")


def run_web():
    """Start the Flask web server (gunicorn or dev server)."""
    from app import app
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"Starting Flask web server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    validate_env()

    # Start Discord bot in background thread (daemon so it dies with the process)
    bot_thread = threading.Thread(target=run_bot, daemon=True, name="DiscordBot")
    bot_thread.start()
    logger.info("Discord bot thread started.")

    # Run Flask in the main thread
    run_web()
