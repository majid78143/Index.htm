import os
import sys
import asyncio
import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
import firebase_service as fb

logging.basicConfig(level=logging.INFO, format="[BOT] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ──────────────────────────────────────────────────
# Events
# ──────────────────────────────────────────────────

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user} ({bot.user.id})")
    try:
        synced = await tree.sync()
        logger.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Command sync failed: {e}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="MJ Developer Platform")
    )


# ──────────────────────────────────────────────────
# Permission Check Helper
# ──────────────────────────────────────────────────

def is_owner_or_admin(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    admins = fb.get_all_admins()
    admin_ids = [a.get("discord_id") for a in admins if a.get("discord_id")]
    return str(interaction.user.id) in admin_ids


# ──────────────────────────────────────────────────
# /admin commands
# ──────────────────────────────────────────────────

admin_group = app_commands.Group(name="admin", description="Manage admins")


@admin_group.command(name="add", description="Add an admin by user ID")
@app_commands.describe(uid="Firebase user UID", name="Display name", role="Admin role")
@app_commands.choices(role=[
    app_commands.Choice(name="Super Admin", value="super_admin"),
    app_commands.Choice(name="Admin", value="admin"),
    app_commands.Choice(name="Moderator", value="moderator"),
    app_commands.Choice(name="Partner Manager", value="partner_manager"),
    app_commands.Choice(name="Content Manager", value="content_manager"),
    app_commands.Choice(name="Support Staff", value="support_staff"),
])
async def admin_add(interaction: discord.Interaction, uid: str, name: str, role: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.set_admin(uid, {
        "uid": uid, "name": name, "role": role,
        "added_at": datetime.utcnow().isoformat(),
        "added_by": str(interaction.user.id)
    })
    fb.set_user(uid, {"role": role})
    fb.log_action("add_admin", str(interaction.user.id), f"Added {role}: {uid} via bot")
    embed = discord.Embed(title="✅ Admin Added", color=discord.Color.green())
    embed.add_field(name="UID", value=uid, inline=True)
    embed.add_field(name="Name", value=name, inline=True)
    embed.add_field(name="Role", value=role, inline=True)
    await interaction.response.send_message(embed=embed)


@admin_group.command(name="remove", description="Remove an admin by user ID")
@app_commands.describe(uid="Firebase user UID")
async def admin_remove(interaction: discord.Interaction, uid: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.delete_admin(uid)
    fb.set_user(uid, {"role": "user"})
    fb.log_action("remove_admin", str(interaction.user.id), f"Removed admin {uid} via bot")
    await interaction.response.send_message(f"✅ Admin `{uid}` removed.")


@admin_group.command(name="list", description="List all admins")
async def admin_list(interaction: discord.Interaction):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    admins = fb.get_all_admins()
    if not admins:
        return await interaction.response.send_message("No admins found.")
    embed = discord.Embed(title="👑 Admin List", color=discord.Color.blue())
    for a in admins[:25]:
        embed.add_field(name=a.get("name", "Unknown"), value=f"Role: {a.get('role')}\nUID: {a.get('uid')}", inline=False)
    await interaction.response.send_message(embed=embed)


tree.add_command(admin_group)


# ──────────────────────────────────────────────────
# /announce commands
# ──────────────────────────────────────────────────

announce_group = app_commands.Group(name="announce", description="Manage announcements")


@announce_group.command(name="create", description="Create a new announcement")
@app_commands.describe(title="Title", content="Content", pinned="Pin this announcement")
async def announce_create(interaction: discord.Interaction, title: str, content: str, pinned: bool = False):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    data = {
        "title": title,
        "content": content,
        "pinned": pinned,
        "type": "info",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": str(interaction.user.id)
    }
    result = fb.create_announcement(data)
    embed = discord.Embed(title="📢 Announcement Created", description=title, color=discord.Color.green())
    embed.add_field(name="Pinned", value="Yes" if pinned else "No")
    await interaction.response.send_message(embed=embed)


@announce_group.command(name="delete", description="Delete an announcement by ID")
@app_commands.describe(aid="Announcement Firebase ID")
async def announce_delete(interaction: discord.Interaction, aid: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.delete_announcement(aid)
    await interaction.response.send_message(f"✅ Announcement `{aid}` deleted.")


tree.add_command(announce_group)


# ──────────────────────────────────────────────────
# /partner commands
# ──────────────────────────────────────────────────

partner_group = app_commands.Group(name="partner", description="Manage partners")


@partner_group.command(name="add", description="Add/approve a partner server")
@app_commands.describe(name="Server name", invite="Discord invite URL", description="Short description")
async def partner_add(interaction: discord.Interaction, name: str, invite: str, description: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    data = {
        "server_name": name,
        "server_invite": invite,
        "description": description,
        "status": "approved",
        "featured": False,
        "created_at": datetime.utcnow().isoformat(),
        "approved_by": str(interaction.user.id)
    }
    fb.create_partner(data)
    embed = discord.Embed(title="🤝 Partner Added", color=discord.Color.green())
    embed.add_field(name="Server", value=name, inline=True)
    embed.add_field(name="Invite", value=invite, inline=True)
    await interaction.response.send_message(embed=embed)


@partner_group.command(name="list", description="List all approved partners")
async def partner_list(interaction: discord.Interaction):
    partners = [p for p in fb.get_partners() if p.get("status") == "approved"]
    if not partners:
        return await interaction.response.send_message("No partners found.")
    embed = discord.Embed(title="🤝 Partners", color=discord.Color.blue())
    for p in partners[:15]:
        embed.add_field(name=p.get("server_name", "Unknown"), value=p.get("server_invite", "No invite"), inline=False)
    await interaction.response.send_message(embed=embed)


@partner_group.command(name="featured", description="Toggle featured status of a partner")
@app_commands.describe(pid="Partner Firebase ID")
async def partner_featured(interaction: discord.Interaction, pid: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    partner = fb.get_partner(pid) or {}
    new_val = not partner.get("featured", False)
    fb.update_partner(pid, {"featured": new_val})
    await interaction.response.send_message(f"✅ Partner `{pid}` featured: {new_val}")


tree.add_command(partner_group)


# ──────────────────────────────────────────────────
# /page commands
# ──────────────────────────────────────────────────

page_group = app_commands.Group(name="page", description="Manage website pages")


@page_group.command(name="create", description="Create a new website page")
@app_commands.describe(slug="URL slug (e.g. privacy)", title="Page title", content="Page content")
async def page_create(interaction: discord.Interaction, slug: str, title: str, content: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.set_page(slug, {
        "slug": slug, "title": title, "content": content,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": str(interaction.user.id)
    })
    await interaction.response.send_message(f"✅ Page `/{slug}` created.")


@page_group.command(name="delete", description="Delete a website page")
@app_commands.describe(slug="URL slug to delete")
async def page_delete(interaction: discord.Interaction, slug: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.delete_page(slug)
    await interaction.response.send_message(f"✅ Page `/{slug}` deleted.")


tree.add_command(page_group)


# ──────────────────────────────────────────────────
# /theme commands
# ──────────────────────────────────────────────────

theme_group = app_commands.Group(name="theme", description="Manage website theme")


@theme_group.command(name="logo", description="Set the website logo URL")
@app_commands.describe(url="Direct image URL")
async def theme_logo(interaction: discord.Interaction, url: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_settings({"logo_url": url})
    await interaction.response.send_message(f"✅ Logo updated.")


@theme_group.command(name="favicon", description="Set the favicon URL")
@app_commands.describe(url="Direct image URL")
async def theme_favicon(interaction: discord.Interaction, url: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_settings({"favicon_url": url})
    await interaction.response.send_message(f"✅ Favicon updated.")


@theme_group.command(name="color", description="Set the primary color")
@app_commands.describe(color="Hex color (e.g. #0d6efd)")
async def theme_color(interaction: discord.Interaction, color: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_settings({"primary_color": color})
    await interaction.response.send_message(f"✅ Primary color set to `{color}`.")


@theme_group.command(name="hero", description="Set the hero banner image URL")
@app_commands.describe(url="Direct image URL")
async def theme_hero(interaction: discord.Interaction, url: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_settings({"hero_image": url})
    await interaction.response.send_message(f"✅ Hero image updated.")


tree.add_command(theme_group)


# ──────────────────────────────────────────────────
# /ads commands
# ──────────────────────────────────────────────────

ads_group = app_commands.Group(name="ads", description="Manage Adsterra ads")


@ads_group.command(name="enable", description="Enable ads on the website")
async def ads_enable(interaction: discord.Interaction):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_ads({"enabled": True})
    fb.update_settings({"ads_enabled": True})
    await interaction.response.send_message("✅ Ads enabled.")


@ads_group.command(name="disable", description="Disable ads on the website")
async def ads_disable(interaction: discord.Interaction):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_ads({"enabled": False})
    fb.update_settings({"ads_enabled": False})
    await interaction.response.send_message("✅ Ads disabled.")


@ads_group.command(name="popup", description="Set popup ad code")
@app_commands.describe(code="Adsterra popup script URL or code")
async def ads_popup(interaction: discord.Interaction, code: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_ads({"popup": code})
    await interaction.response.send_message("✅ Popup ad set.")


@ads_group.command(name="socialbar", description="Set Social Bar ad code")
@app_commands.describe(code="Adsterra social bar script URL")
async def ads_socialbar(interaction: discord.Interaction, code: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_ads({"social_bar": code})
    await interaction.response.send_message("✅ Social bar ad set.")


@ads_group.command(name="smartlink", description="Set Smart Link URL")
@app_commands.describe(url="Adsterra smart link URL")
async def ads_smartlink(interaction: discord.Interaction, url: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_ads({"smart_link": url})
    await interaction.response.send_message("✅ Smart link set.")


tree.add_command(ads_group)


# ──────────────────────────────────────────────────
# /permission commands
# ──────────────────────────────────────────────────

permission_group = app_commands.Group(name="permission", description="Manage admin permissions")


@permission_group.command(name="add", description="Add a permission to a user")
@app_commands.describe(uid="Firebase user UID", perm="Permission name")
async def perm_add(interaction: discord.Interaction, uid: str, perm: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    current = fb.get_permissions(uid) or []
    if perm not in current:
        current.append(perm)
        fb.set_permissions(uid, current)
    await interaction.response.send_message(f"✅ Permission `{perm}` added to `{uid}`.")


@permission_group.command(name="remove", description="Remove a permission from a user")
@app_commands.describe(uid="Firebase user UID", perm="Permission name")
async def perm_remove(interaction: discord.Interaction, uid: str, perm: str):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    current = fb.get_permissions(uid) or []
    current = [p for p in current if p != perm]
    fb.set_permissions(uid, current)
    await interaction.response.send_message(f"✅ Permission `{perm}` removed from `{uid}`.")


tree.add_command(permission_group)


# ──────────────────────────────────────────────────
# /stats command
# ──────────────────────────────────────────────────

@tree.command(name="stats", description="View platform statistics")
async def stats(interaction: discord.Interaction):
    data = fb.get_analytics() or {}
    embed = discord.Embed(title="📊 MJ Developer Platform Stats", color=discord.Color.blue())
    embed.add_field(name="👥 Total Users", value=str(data.get("total_users", 0)), inline=True)
    embed.add_field(name="🔍 Total Searches", value=str(data.get("total_searches", 0)), inline=True)
    embed.add_field(name="👤 Profile Searches", value=str(data.get("total_profile_searches", 0)), inline=True)
    embed.add_field(name="🏰 Guild Searches", value=str(data.get("total_guild_searches", 0)), inline=True)
    embed.add_field(name="🤝 Partners", value=str(data.get("total_partners", 0)), inline=True)
    embed.set_footer(text="MJ Developer Platform")
    await interaction.response.send_message(embed=embed)


# ──────────────────────────────────────────────────
# /maintenance command
# ──────────────────────────────────────────────────

@tree.command(name="maintenance", description="Toggle website maintenance mode")
@app_commands.describe(enabled="Enable or disable maintenance mode")
async def maintenance(interaction: discord.Interaction, enabled: bool):
    if not is_owner_or_admin(interaction):
        return await interaction.response.send_message("❌ No permission.", ephemeral=True)
    fb.update_settings({"maintenance_mode": enabled})
    fb.log_action("maintenance_toggle", str(interaction.user.id), f"Maintenance: {enabled} via bot")
    status = "🔴 ENABLED" if enabled else "🟢 DISABLED"
    await interaction.response.send_message(f"Maintenance mode {status}.")


# ──────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────

def run_bot():
    token = Config.DISCORD_BOT_TOKEN
    if not token:
        logger.error("Discord bot TOKEN not set. Bot will not start.")
        return
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token. Check your TOKEN environment variable.")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")


if __name__ == "__main__":
    run_bot()
