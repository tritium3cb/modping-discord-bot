# 🛡️ ModPingBot - A Simple Mod Notification Bot for Discord

ModPingBot is a lightweight Discord bot that allows users to alert moderators privately using a simple slash command `/modping`. The alert is sent to a hidden channel with mod roles pinged, making it ideal for sensitive or urgent concerns.

---

## 🌐 Features

- Slash command `/modping` with required reason  
- Sends alert to a designated private mod channel  
- Automatically pings specific moderator/admin roles  
- Sends user a confirmation via DM  
- Per-server configuration using `config.json`  
- Hosted for free using Render + UptimeRobot  

---

## ⚙️ Setup Instructions (Render Hosting)

### 1. 🔧 Fork or Clone this Repository

Click the fork button or run:

{```bash
git clone https://github.com/yourusername/modpingbot.git
cd modpingbot
}
---

###  2. 🧠 Set Up Your config.json
Create or edit config.json in the root directory. Example:
{
  "default": {
    "notification_channels": ["bot-notifs"],
    "ping_roles": ["Moderator", "Admin"]
  },
  "123456789012345678": {
    "notification_channels": ["staff-alerts"],
    "ping_roles": ["ModTeam"]
  }
}
Replace 123456789012345678 with your Discord server’s ID.

notification_channels is a list of channel names where alerts will be sent.

ping_roles is a list of roles that will be tagged in the alert.

The "default" config is used if a server-specific entry isn't found.

---

### 3. 🚀 Deploy to Render (Free Plan)
Go to https://render.com and create a free account.

Click New Web Service.

Connect your GitHub repo containing this bot.

Fill in Render’s setup:

Environment: Python

Build Command:
pip install -r requirements.txt

Start Command:
python main.py

Add an Environment Variable:

Key: DISCORD_TOKEN

Value: your actual bot token (from https://discord.com/developers)

---

### 4. 🔁 Keep the Bot Awake with UptimeRobot
Render free plans go idle after 15 minutes of inactivity. Fix this with UptimeRobot:

Create a free account at https://uptimerobot.com

Add a New Monitor:

Monitor Type: HTTP(s)

Friendly Name: ModPingBot

URL: Use your Render service's public URL (e.g. https://yourbot.onrender.com)

Monitoring Interval: Every 5 minutes

Click Create Monitor

Your bot will now stay awake 24/7.

---

### ❗ Important Notes
Never publish your DISCORD_TOKEN to GitHub.

Do not include config.json if it contains sensitive server data.

The bot does not need Administrator permissions.

Required Discord bot permissions:

View Channels

Send Messages

Read Message History

Use Slash Commands

Send Direct Messages (to DM the user)

### 📄 License
This project is licensed under the MIT License.

You can freely use, modify, and distribute it, even commercially, as long as attribution is preserved.

---

### 🤝 Contributing
Contributions are welcome. Open an issue or submit a pull request if you’d like to improve the project.
