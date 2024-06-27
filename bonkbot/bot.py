import logging
import discord

from .db.user_service import UserService


class BonkBot(discord.Client):
    __user_service: UserService
    __logger = logging.getLogger("bot")

    def __init__(
        self,
        *,
        user_service: UserService,
        intents: discord.Intents,
        **options,
    ) -> None:
        self.__user_service = user_service
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        self.__logger.info(f"Logged on as {self.user}")

    async def on_message(self, message: discord.Message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == "ping":
            await message.channel.send("pong")
