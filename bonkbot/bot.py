import logging
import discord

from .db.data_service import DataService
from .enums.bot_command import BotCommand


class BonkBot(discord.Client):
    __data_service: DataService
    __logger = logging.getLogger("bot")

    def __init__(
        self,
        *,
        data_service: DataService,
        intents: discord.Intents,
        **options,
    ) -> None:
        self.__data_service = data_service
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        self.__logger.info(f"Logged on as {self.user}")

    async def on_message(self, message: discord.Message):
        prefix = self.__data_service.get_guild(message.guild.id).prefix
        
        # get message with all whitespace around it removed
        message_content = message.content.strip()
        
        # ignore all messages not starting with our prefix
        if not message_content.startswith(prefix):
            return
        
        # remove the prefix
        message_content = message_content.removeprefix(prefix)
        
        # don't respond to ourselves
        if message.author == self.user:
            return
        
        # the poor man's switch case
        # handle different bot commands, ignoring all others that don't fit
        if message_content.startswith(BotCommand.PREFIX):
            # get or set prefix here
            pass
        elif message_content.startswith(BotCommand.BONKS):
            # get a users bonks here
            # message.guild.query_members()
            pass
        elif message_content.startswith(BotCommand.BONK):
            # bonk a user here
            pass
        