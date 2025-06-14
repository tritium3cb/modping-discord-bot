import os

# Print the first few characters of the token
token = os.environ.get("DISCORD_BOT_TOKEN")
print(f"Token: {token[:10]}... (length: {len(token) if token else 'None'})")
