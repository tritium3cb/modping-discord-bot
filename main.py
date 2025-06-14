import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import discord.utils


# --- Load server config ---
with open("config.json", "r") as f:
    config = json.load(f)

# --- Bot setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
modping_tree = bot.tree

# --- Event: When the bot starts up ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("📡 Syncing command tree...")
    await modping_tree.sync()
    print("✅ Command tree synced.")

# --- Slash command: /modping ---
@modping_tree.command(name="modping", description="Alert the moderators privately with a reason")
@app_commands.describe(reason="Why are you pinging the mods?")
async def modping(interaction: discord.Interaction, reason: str):
    guild_id = str(interaction.guild.id)
    author = interaction.user
    origin_channel = interaction.channel

    # --- Escalation keyword detection ---
    priority_keywords = ["suicide", "self-harm", "urgent", "help now", "danger", "immediate help"]
    is_high_priority = any(word in reason.lower() for word in priority_keywords)

    if is_high_priority:
        print("[ALERT] High-priority keyword detected.")

    # Optional debug print
    print(f"[DEBUG] Origin Channel: {origin_channel.name} (ID: {origin_channel.id})")

    # Get server-specific config, or fallback to 'default'
    server_config = config.get(guild_id, config.get("default", {}))

    # Try all configured channel names
    channel = None
    for channel_name in server_config.get("notification_channels", []):
        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        if channel:
            break

    if not channel:
        await interaction.response.send_message("❌ Couldn't find a valid notification channel.", ephemeral=True)
        return

    # Find the configured mod roles
    role_mentions = [
        role.mention for role in interaction.guild.roles
        if role.name in server_config.get("ping_roles", [])
    ]

    if not role_mentions:
        await interaction.response.send_message("❌ No mod roles found.", ephemeral=True)
        return

    # Compose and send message
    timestamp = discord.utils.format_dt(datetime.utcnow(), style='F')  # Full date and time
   
    # Compose and send message with timestamp
    prefix = "🚨 **HIGH PRIORITY ALERT**\n\n" if is_high_priority else ""
    ping_message = (
        f"{prefix}"
        f"🔔 **Mod Ping from {author.mention}**\n\n"
        f"**Reason:** {reason}\n"
        f"{', '.join(role_mentions)}\n\n"
        f"📍 **Origin Channel:** {origin_channel.mention}\n"
        f"📅 **Sent:** {timestamp}"
    )

    await channel.send(ping_message)
    await interaction.response.send_message("✅ Your message was sent privately to the mods.", ephemeral=True)


    # Send DM confirmation
    try:
        await author.send("✅ Your mod alert has been sent. A moderator will assist you shortly.")
    except discord.Forbidden:
        pass  # User has DMs disabled

# --- Keep Alive (for UptimeRobot) ---
from keep_alive import keep_alive
keep_alive()

# --- Run the bot ---
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)

