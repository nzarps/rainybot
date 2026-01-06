
import discord
import logging
from config import VC_STATS_CHANNEL_ID # fallback or new config
import os

logger = logging.getLogger("NotificationService")

class NotificationService:
    def __init__(self):
        # Allow env var override for public log channel
        self.public_log_channel_id = os.getenv("PUBLIC_LOG_CHANNEL_ID")

    async def send_dm(self, user: discord.User, content: str = None, embed: discord.Embed = None):
        """Safe DM sending with error handling"""
        if not user:
            return False
        
        try:
            await user.send(content=content, embed=embed)
            return True
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to {user.id} (DMs closed or blocked).")
            return False
        except Exception as e:
            logger.error(f"Failed to send DM to {user.id}: {e}")
            return False

    async def post_public_log(self, guild: discord.Guild, embed: discord.Embed):
        """Post completed deal to public channel"""
        if not self.public_log_channel_id:
            return

        try:
            channel = guild.get_channel(int(self.public_log_channel_id))
            if channel:
                await channel.send(embed=embed)
            else:
                logger.warning(f"Public log channel {self.public_log_channel_id} not found.")
        except Exception as e:
            logger.error(f"Failed to post public log: {e}")

notification_service = NotificationService()
