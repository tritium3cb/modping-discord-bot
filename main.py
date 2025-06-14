import os
import discord
from discord import app_commands
from discord.ext import commands

# --- Bot setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Use the already-attached CommandTree
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
    guild = interaction.guild
    author = interaction.user

    # Find the #bot-notifs channel
    channel = (
    discord.utils.get(guild.text_channels, name="bot-notifs") or
    discord.utils.get(guild.text_channels, name="moderators")
)
    
    if not channel:
        await interaction.response.send_message("❌ Couldn't find the #bot-notifs channel.", ephemeral=True)
        return

    # Find Moderator/Admin roles
    mod_roles = ["Moderator", "Admin", "Moderators"]
    role_mentions = [role.mention for role in guild.roles if role.name in mod_roles]

    if not role_mentions:
        await interaction.response.send_message("❌ No mod roles found.", ephemeral=True)
        return

    # Compose and send message
    ping_message = f"🔔 **Mod Ping from {author.mention}**\n\n**Reason:** {reason}\n{', '.join(role_mentions)}"

    await channel.send(ping_message)
    await interaction.response.send_message("✅ Your message was sent privately to the mods.", ephemeral=True)

try:
    await author.send("✅ Your mod alert has been sent. A moderator will assist you shortly.")
except discord.Forbidden:
    pass  # User has DMs off

token = os.environ.get("DISCORD_TOKEN")

from keep_alive import keep_alive

keep_alive()  # starts the webserver

# --- Run the bot ---
bot.run(token)
