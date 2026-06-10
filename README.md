# MJ Developer Platform

A complete Free Fire Utility Platform built with Flask, Firebase, and Discord.

## Features

- 🎮 Free Fire Tools (Profile Lookup, Guild Search, Rankings, Region Checker, Player Search, UID Info)
- 🔐 Multi-auth (Discord OAuth, Google OAuth, Email/Password)
- 👑 Owner Panel (full control, theme, backup/restore, maintenance mode)
- 🛡️ Admin Panel (users, partners, announcements, pages, media, ads, FAQ, updates, logs)
- 🤖 Discord Bot with slash commands to control the website
- 📢 Announcements & Partner System
- 📊 Analytics Dashboard
- 🎨 Light/Professional Theme with customizable colors
- 💰 Adsterra Ads Integration
- 🔥 Firebase Realtime Database backend

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run locally

```bash
# Run website only
python app.py

# Run website + bot together
python start.py
```

## Structure

```
app.py              # Flask app factory + blueprints
bot.py              # Discord bot (slash commands)
config.py           # All configuration from environment
firebase_service.py # Firebase REST API wrapper (no SDK required)
start.py            # Combined startup script (bot + web)
routes/
  main.py           # Public pages
  auth.py           # Login/Register/OAuth
  tools.py          # Free Fire tools
  admin.py          # Admin panel
  owner.py          # Owner panel
  api.py            # Public JSON API
templates/          # Jinja2 HTML templates
static/             # CSS, JS, images
```

## Deployment on Render (Free Plan)

1. Push this project to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Connect your GitHub repo
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
6. Add all environment variables from `.env.example` in the Render dashboard
7. Deploy!

> **Bot + Web on Free Plan**: Use `start.py` as your start command to run both the bot and web server in the same process:
> `python start.py`
> 
> Or use `Procfile` if Render detects it automatically.

## Discord OAuth Setup

1. Go to [discord.com/developers](https://discord.com/developers/applications)
2. Create a new application
3. Add redirect URI: `https://your-domain.onrender.com/auth/discord/callback`
4. Copy Client ID and Client Secret to your `.env`

## Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials
3. Add redirect URI: `https://your-domain.onrender.com/auth/google/callback`
4. Copy Client ID and Client Secret to your `.env`

## Owner Login

The owner account is hardcoded via environment variables:
- `OWNER_EMAIL` — your owner email
- `OWNER_PASSWORD` — your owner password

Login at `/auth/login` with these credentials to access the Owner Panel.

## Discord Bot Commands

| Command | Description |
|---------|-------------|
| `/admin add` | Add a new admin |
| `/admin remove` | Remove an admin |
| `/admin list` | List all admins |
| `/announce create` | Create announcement |
| `/partner add` | Add partner server |
| `/partner list` | List partners |
| `/partner featured` | Toggle featured |
| `/page create` | Create page |
| `/page delete` | Delete page |
| `/theme logo` | Set logo URL |
| `/theme color` | Set primary color |
| `/theme hero` | Set hero image |
| `/ads enable` | Enable ads |
| `/ads disable` | Disable ads |
| `/permission add` | Add permission |
| `/permission remove` | Remove permission |
| `/stats` | View platform stats |
| `/maintenance` | Toggle maintenance mode |

## Firebase Database Structure

```
/users            — Registered user accounts
/admins           — Admin accounts
/permissions      — Per-user permission arrays
/partners         — Partner server records
/announcements    — Platform announcements
/guilds           — Guild directory cache
/pages            — Editable page content
/updates          — Changelog entries
/faq              — FAQ items
/media            — Media library
/ads              — Adsterra ad configuration
/settings         — Global site settings
/logs             — Action logs
/login_logs       — Login history
/security_logs    — Security events
/analytics        — Usage counters
/subscriptions    — Future payment records
```

## License

MIT — Free to use and modify.
