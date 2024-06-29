import logging
import discord

from .db.data_service import DataService
from .enums.bot_command import BotCommand
from .models.models import Guild


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

        response = await self.__handle_command(
            message, command, additional_args, cached_guild
        )

        if response:
            await message.channel.send(response)

    async def __handle_command(
        self,
        message: discord.Message,
        command: BotCommand,
        additional_args: str | None,
        cached_guild: Guild,
    ) -> str | None:
        # the poor man's switch case
        # handle different bot commands, ignoring all others that don't fit
        if command == BotCommand.PREFIX:
            if not additional_args:
                # reply with prefix here
                return f"Guild is using prefix `{cached_guild.prefix}`"

            if len(additional_args) != 1 or additional_args == " ":
                return f"Invalid prefix supplied! Prefix has to be a single non-white space character. Given value: `{additional_args}`"

            cached_guild.prefix = additional_args
            self.__data_service.save_and_commit(cached_guild)
            return f"Set guild command prefix to `{additional_args}`"

        elif command == BotCommand.BONKS:
            if not additional_args or len(additional_args) < 1:
                top_users = self.__data_service.get_top_bonked_users(cached_guild.id)

                # TODO
                # await message.channel.send(f"**TOP BONKS**")
                return

            matched_users = await message.guild.query_members(additional_args.lower())

            if len(matched_users) < 1:
                return f"Couldn't find any users by `{additional_args}`!"

            matched_user = matched_users[0]
            user = self.__data_service.get_user(matched_user.id)

            return f"user {matched_user.display_name} has been bonked {user.bonks} times so far"

        elif command == BotCommand.BONK:
            if not additional_args or len(additional_args) < 1:
                return "User needs to be specified!"

            matched_users = await message.guild.query_members(additional_args.lower())

            if len(matched_users) < 1:
                return f"Couldn't find any users by `{additional_args}`!"

            matched_user = matched_users[0]
            user = self.__data_service.get_user(matched_user.id)
            user.bonk()
            self.__data_service.save_and_commit(user)

            return f"**bonk {matched_user.display_name}**\n\n_user has been bonked {user.bonks} times so far_"

        elif command == BotCommand.HELP:
            available_commands = [
                cached_guild.prefix + command_enum for command_enum in BotCommand.list()
            ]
            return f"Available commands: `{'`, `'.join(available_commands)}`"
