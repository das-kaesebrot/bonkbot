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
        cached_guild = self.__data_service.get_guild(message.guild)
        user = self.__data_service.get_user(message.author.id)
        
        # get message with all whitespace around it removed
        message_content = message.content.strip()
        
        # ignore all messages not starting with our prefix
        if not message_content.startswith(cached_guild.prefix):
            return
        
        # remove the prefix
        message_content = message_content.removeprefix(cached_guild.prefix)
        
        # don't respond to ourselves
        if message.author == self.user:
            return
        
        # split on whitespace
        split_message_content = message_content.split()
        
        if len(split_message_content) < 1:
            return
        
        command = split_message_content[0]
        additional_args = None
        
        if len(split_message_content) > 1:
            additional_args = " ".join(split_message_content[1:])
        
        # the poor man's switch case
        # handle different bot commands, ignoring all others that don't fit
        if command == BotCommand.PREFIX:            
            if not additional_args:
                # reply with prefix here
                await message.channel.send(f"Guild is using prefix `{cached_guild.prefix}`")
                return
            
            if len(additional_args) != 1 or additional_args == " ":
                await message.channel.send(f"Invalid prefix supplied! Prefix has to be a single non-white space character. Given value: `{additional_args}`")
                return
            
            cached_guild.prefix = additional_args
            self.__data_service.save_and_commit(cached_guild)
            await message.channel.send(f"Set guild command prefix to `{additional_args}`")
            return
