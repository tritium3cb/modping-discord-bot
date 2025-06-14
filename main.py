import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import discord.utils

# --- Load language translations ---
with open("languages.json", "r", encoding="utf-8") as f:
    translations = json.load(f)

# --- Load server config ---
with open("config.json", "r") as f:
    config = json.load(f)

# --- Cooldown tracking dictionary ---
cooldowns = {}

# --- Bot setup ---
intents = discord.Intents.default()
intents.message_content = True  # Optional: only if you plan to read message content later
bot = commands.Bot(command_prefix="!", intents=intents)
modping_tree = bot.tree

def t(key, server_config):
    lang = server_config.get("language", "en")
    return translations.get(lang, translations["en"]).get(key, key)

# --- Event: When the bot starts up ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("📡 Syncing command tree...")
    await modping_tree.sync()
    print("✅ Command tree synced.")

# --- Slash command: /modping ---
@modping_tree.command(name="modping", description="Alert the moderators privately with a reason")  # Static in code
@app_commands.describe(reason="Why are you pinging the mods?")
async def modping(interaction: discord.Interaction, reason: str):
    guild_id = str(interaction.guild.id)
    author = interaction.user
    origin_channel = interaction.channel

    # --- Cooldown check ---
    now = datetime.utcnow().timestamp()
    last_used = cooldowns.get((guild_id, author.id), 0)
    server_config = config.get(guild_id, config.get("default", {}))
    cooldown_seconds = server_config.get("cooldown_seconds", 300)

    priority_keywords = ["suicide", "self-harm", "urgent", "help now", "danger", "immediate help"]
    is_high_priority = any(word in reason.lower() for word in priority_keywords)

    if not is_high_priority:
        if now - last_used < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_used))
            await interaction.response.send_message(f"⏳ {t('cooldown_active', server_config)} {remaining}s", ephemeral=True)
            return

    # --- Update cooldown tracker ---
    cooldowns[(guild_id, author.id)] = now

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
    prefix = f"{t('high_priority', server_config)}\n\n" if is_high_priority else ""
    embed = discord.Embed(
    title=f"{t('mod_ping', server_config)} {author.display_name}",
    description=reason,
    color=discord.Color.red() if is_high_priority else discord.Color.orange()
)
embed.add_field(name=t("origin_channel", server_config), value=origin_channel.mention, inline=False)
embed.add_field(name=t("sent", server_config), value=timestamp, inline=False)
embed.set_footer(text=f"User ID: {author.id}")
embed.set_thumbnail(url=author.display_avatar.url)

message = await channel.send(
    content=prefix + ', '.join(role_mentions),
    embed=embed
)

await message.add_reaction("✅")

await interaction.response.send_message(t("public_confirm", server_config), ephemeral=True)

# Send DM confirmation
try:
    await author.send(t("dm_confirm", server_config))
except discord.Forbidden:
    pass  # User has DMs disabled

@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == "✅":
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member and any(role.name in config.get(str(guild.id), {}).get("ping_roles", []) for role in member.roles):
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.reply(f"✅ Acknowledged by {member.mention}")

# --- Keep Alive (for UptimeRobot) ---
from keep_alive import keep_alive
keep_alive()

# --- Run the bot ---
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)

