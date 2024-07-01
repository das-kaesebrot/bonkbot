import logging
from discord.ext import tasks, commands

class JailSync(commands.Cog):
    def __init__(self, bot):
        logging.getLogger(__name__).info("Created sync job")
        self.bot = bot

    def cog_unload(self):
        self.sync_job.cancel()

    @tasks.loop(minutes=1)
    async def sync_job(self):
        await self.bot.sync_horny_jails()