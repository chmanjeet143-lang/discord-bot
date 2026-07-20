# Discord Bot

A Python Discord bot with welcome messages and moderation commands.

## Commands

All commands use the `!` prefix.

| Command | Permission | Description |
|---|---|---|
| `!kick @user [reason]` | Kick Members | Kick a member from the server |
| `!ban @user [reason]` | Ban Members | Ban a member from the server |
| `!unban username#0000` | Ban Members | Unban a user |
| `!clear [1-100]` | Manage Messages | Delete messages (default: 10) |
| `!mute @user [minutes] [reason]` | Moderate Members | Timeout a member (default: 10 min) |
| `!unmute @user` | Moderate Members | Remove a timeout |

## Welcome Messages

When a new member joins, the bot sends an embed to the server's **System Channel** (configured in Server Settings → Overview).

## Setup

1. Add your bot token as the `DISCORD_TOKEN` secret.
2. Enable these **Privileged Gateway Intents** in your bot's application page on discord.com/developers:
   - **Server Members Intent** (required for welcome messages)
   - **Message Content Intent** (required for prefix commands)
3. Invite the bot with these permissions: Kick Members, Ban Members, Manage Messages, Moderate Members, Send Messages, Embed Links, Read Message History.
