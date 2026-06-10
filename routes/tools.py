import requests
from flask import Blueprint, render_template, request, jsonify, flash
import firebase_service as fb
from config import Config

tools_bp = Blueprint("tools", __name__)

FF_REGIONS = {
    "IND": "India",
    "BR": "Brazil",
    "SG": "Singapore",
    "RU": "Russia",
    "ID": "Indonesia",
    "TW": "Taiwan",
    "US": "North America",
    "VN": "Vietnam",
    "TH": "Thailand",
    "ME": "Middle East",
    "PK": "Pakistan",
    "BD": "Bangladesh",
    "CIS": "CIS",
    "NA": "North America",
    "SAC": "South America",
    "FFAC": "Africa"
}

def ff_api_call(endpoint, params=None):
    base = "https://profile.freefire.gg/api"
    try:
        r = requests.get(f"{base}{endpoint}", params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@tools_bp.route("/")
def tools_index():
    return render_template("tools/index.html", regions=FF_REGIONS)


@tools_bp.route("/profile", methods=["GET", "POST"])
def profile_lookup():
    result = None
    error = None
    uid = request.form.get("uid") or request.args.get("uid", "")
    region = request.form.get("region") or request.args.get("region", "IND")

    if uid:
        fb.increment_analytics("total_searches")
        fb.increment_analytics("total_profile_searches")
        data = ff_api_call(f"/players/{uid}", {"region": region})
        if data:
            result = data
        else:
            data2 = _mock_profile(uid, region)
            result = data2

    return render_template("tools/profile_lookup.html",
                           result=result, error=error,
                           uid=uid, region=region, regions=FF_REGIONS)


@tools_bp.route("/guild", methods=["GET", "POST"])
def guild_search():
    result = None
    error = None
    guild_id = request.form.get("guild_id") or request.args.get("guild_id", "")
    region = request.form.get("region") or request.args.get("region", "IND")

    if guild_id:
        fb.increment_analytics("total_searches")
        fb.increment_analytics("total_guild_searches")
        data = ff_api_call(f"/guilds/{guild_id}", {"region": region})
        if data:
            result = data
        else:
            result = _mock_guild(guild_id, region)

    return render_template("tools/guild_search.html",
                           result=result, error=error,
                           guild_id=guild_id, region=region, regions=FF_REGIONS)


@tools_bp.route("/player-search", methods=["GET", "POST"])
def player_search():
    results = []
    query = request.form.get("query") or request.args.get("q", "")
    region = request.form.get("region") or request.args.get("region", "IND")
    if query:
        data = ff_api_call("/players/search", {"name": query, "region": region})
        results = data.get("players", []) if data else []
    return render_template("tools/player_search.html",
                           results=results, query=query,
                           region=region, regions=FF_REGIONS)


@tools_bp.route("/region-checker", methods=["GET", "POST"])
def region_checker():
    result = None
    uid = request.form.get("uid") or request.args.get("uid", "")
    if uid:
        data = ff_api_call(f"/players/{uid}/region")
        result = data or {"uid": uid, "region": "Unknown", "region_name": "Could not determine"}
    return render_template("tools/region_checker.html",
                           result=result, uid=uid, regions=FF_REGIONS)


@tools_bp.route("/rankings")
def rankings():
    category = request.args.get("cat", "players")
    region = request.args.get("region", "IND")
    data = ff_api_call(f"/rankings/{category}", {"region": region}) or {"rankings": []}
    return render_template("tools/rankings.html",
                           rankings=data.get("rankings", []),
                           category=category, region=region, regions=FF_REGIONS)


@tools_bp.route("/uid-info", methods=["GET", "POST"])
def uid_info():
    result = None
    uid = request.form.get("uid") or request.args.get("uid", "")
    if uid:
        data = ff_api_call(f"/players/{uid}")
        result = data or _mock_profile(uid, "IND")
    return render_template("tools/uid_info.html",
                           result=result, uid=uid, regions=FF_REGIONS)


# ── Mock Fallbacks ────────────────────────────────────────────────────────────

def _mock_profile(uid, region):
    return {
        "uid": uid,
        "nickname": "Player_" + uid[-4:],
        "region": region,
        "region_name": FF_REGIONS.get(region, region),
        "level": "??",
        "likes": "??",
        "guild": "No Guild",
        "avatar": "",
        "banner": "",
        "account_created": "Unknown",
        "is_mock": True
    }


def _mock_guild(gid, region):
    return {
        "guild_id": gid,
        "guild_name": "Guild_" + gid[-4:],
        "region": region,
        "region_name": FF_REGIONS.get(region, region),
        "owner": "Unknown",
        "level": "??",
        "members": "??",
        "max_members": 30,
        "verified": False,
        "created_at": "Unknown",
        "logo": "",
        "banner": "",
        "is_mock": True
    }
