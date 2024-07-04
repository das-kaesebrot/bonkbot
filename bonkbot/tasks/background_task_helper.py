import logging
from discord.ext import tasks, commands

class BackgroundTaskHelper(commands.Cog):
    def __init__(self, bot):
        logging.getLogger(__name__).info("Created background task helper")
        self.bot = bot

    def cog_unload(self):
        self.jail_sync_job.cancel()

    @tasks.loop(minutes=1)
    async def jail_sync_job(self):
        await self.bot.sync_horny_jails()
        
    @tasks.loop(minutes=1)
    async def bot_presence_job(self):
        await self.bot.update_presence()
    