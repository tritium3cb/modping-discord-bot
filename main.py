import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from discord.ui import View, Select

# Supported languages
LANGUAGES = {
    "en": "🇬🇧 English",
    "de": "🇩🇪 German",
    "es": "🇪🇸 Spanish",
    "zh-CN": "🇨🇳 Chinese (Simplified)",
    "ja": "🇯🇵 Japanese",
    "fr": "🇫🇷 French",
    "pt": "🇵🇹 Portuguese",
    "ru": "🇷🇺 Russian",
    "in": "🇮🇩 Indonesian",
    "tr": "🇹🇷 Turkish",
    "ko": "🇰🇷 Korean",
    "it": "🇮🇹 Italian",
    "ar": "🇪🇬 Arabic (Egyptian Arabic)"
}

# Load language translations
with open("languages.json", "r", encoding="utf-8") as f:
    translations = json.load(f)

# Load server config
with open("config.json", "r") as f:
    config = json.load(f)

# Cooldown tracking
cooldowns = {}

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
modping_tree = bot.tree

def t(key, server_config):
    lang = server_config.get("language", "en")
    return translations.get(lang, translations["en"]).get(key, key)

# --- Language selector ---
class LanguageSelect(Select):
    def __init__(self, guild_id):
        self.guild_id = guild_id
        options = [discord.SelectOption(label=name, value=code) for code, name in LANGUAGES.items()]
        super().__init__(placeholder="🌍 Choose a language", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        config[str(self.guild_id)] = config.get(str(self.guild_id), {})
        config[str(self.guild_id)]["language"] = selected

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        await interaction.response.send_message(
            f"✅ Language set to **{LANGUAGES[selected]}** for this server.",
            ephemeral=True
        )

class LanguageView(View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.add_item(LanguageSelect(guild_id))

@modping_tree.command(name="setlanguage", description="Set the bot's language for this server")
async def setlanguage(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ You need the 'Manage Server' permission to do this.",
            ephemeral=True
        )
        return

    view = LanguageView(interaction.guild.id)
    await interaction.response.send_message(
        "🌐 Please choose a language for the bot below:",
        view=view,
        ephemeral=True
    )

# --- Dynamic ModPing Command Creator ---
def create_modping_command(name: str):
    @app_commands.command(name=name, description="Alert the moderators privately with a reason")
    @app_commands.describe(reason="Why are you pinging the mods?")
    async def dynamic_modping(interaction: discord.Interaction, reason: str):
        guild_id = str(interaction.guild.id)
        author = interaction.user
        origin_channel = interaction.channel
        server_config = config.get(guild_id, config.get("default", {}))

        # Cooldown logic
        now = datetime.utcnow().timestamp()
        last_used = cooldowns.get((guild_id, author.id), 0)
        cooldown_seconds = server_config.get("cooldown_seconds", 300)
        priority_keywords = ["suicide", "self-harm", "urgent", "help now", "danger", "immediate help"]
        is_high_priority = any(word in reason.lower() for word in priority_keywords)

        if not is_high_priority and now - last_used < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_used))
            await interaction.response.send_message(f"⏳ {t('cooldown_active', server_config)} {remaining}s", ephemeral=True)
            return

        cooldowns[(guild_id, author.id)] = now

        # Find channel
        channel = None
        for channel_name in server_config.get("notification_channels", []):
            channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
            if channel:
                break

        if not channel:
            await interaction.response.send_message("❌ Couldn't find a valid notification channel.", ephemeral=True)
            return

        # Role mentions
        role_mentions = [
            role.mention for role in interaction.guild.roles
            if role.name in server_config.get("ping_roles", [])
        ]

        if not role_mentions:
            await interaction.response.send_message("❌ No mod roles found.", ephemeral=True)
            return

        timestamp = discord.utils.format_dt(datetime.utcnow(), style='F')
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

        message = await channel.send(content=prefix + ', '.join(role_mentions), embed=embed)
        await message.add_reaction("✅")

        await interaction.response.send_message(t("public_confirm", server_config), ephemeral=True)

        try:
            await author.send(t("dm_confirm", server_config))
        except discord.Forbidden:
            pass

    return dynamic_modping

# --- Acknowledge Reactions ---
@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == "✅":
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if not member:
            return
        ping_roles = config.get(str(guild.id), {}).get("ping_roles", [])
        if any(role.name in ping_roles for role in member.roles):
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.reply(f"✅ Acknowledged by {member.mention}")

# --- Bot Startup ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("📡 Syncing command tree...")

    # Register custom modping command per guild
    registered_names = set()
    for guild_id, settings in config.items():
        if guild_id == "default":
            continue
        command_name = settings.get("command_name", config["default"].get("command_name", "modping"))
        if command_name in registered_names:
            continue  # Prevent duplicate names
        registered_names.add(command_name)
        command = create_modping_command(command_name)
        modping_tree.add_command(command)

    # Fallback global modping
    if config["default"].get("command_name", "modping") not in registered_names:
        modping_tree.add_command(create_modping_command("modping"))

    await modping_tree.sync()
    print("✅ Command tree synced.")

# --- Optional Keep-Alive for Render/UptimeRobot ---
from keep_alive import keep_alive
keep_alive()

# --- Run the bot ---
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)

# --- Made in Australia, on Wiradjuri land ---
