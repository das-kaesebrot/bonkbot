import logging
import discord

from .db.data_service import DataService
from .enums.bot_command import BotCommand
from .models.models import Guild, User
from .config import BotConfig
from .constants.bot_message import BotMessage
from .constants.bot_error import BotError


class BonkBot(discord.Client):
    __data_service: DataService
    __config: BotConfig
    __logger = logging.getLogger("bot")

    def __init__(
        self,
        *,
        data_service: DataService,
        intents: discord.Intents,
        config: BotConfig,
        **options,
    ) -> None:
        self.__data_service = data_service
        self.__config = config
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        self.__logger.info(f"Logged on as '{self.user}'")

    async def on_message(self, message: discord.Message):
        cached_guild = self.__data_service.get_guild(message.guild)

        # get message with all whitespace around it removed
        message_content = message.content.strip().lower()

        # ignore all messages not starting with our prefix
        # but allow messages containing just the word bonk
        if not message_content.startswith(cached_guild.prefix) and message_content != BotCommand.BONK:
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
                return BotMessage.GUILD_PREFIX_INFO.format(cached_guild.prefix)

            # only allow admins to change prefix, ignore message otherwise
            if not self._is_admin(self.__data_service.get_user(message.author.id)):
                self.__logger.debug(f"Ignoring privileged command '{command}' from unprivileged user '{message.author.id}'")
                return
            
            if len(additional_args) != 1 or additional_args == " ":
                return BotError.INVALID_PREFIX.format(additional_args)

            cached_guild.prefix = additional_args
            self.__data_service.save_and_commit(cached_guild)
            return BotMessage.GUILD_PREFIX_SET.format(additional_args)

        elif command == BotCommand.BONKS:
            if not additional_args or len(additional_args) < 1:
                top_users = self.__data_service.get_top_bonked_users(cached_guild.id)
                users_string = ""
                for user in top_users:
                    username = (
                        await message.guild.fetch_member(user.discord_id)
                    ).display_name
                    users_string += f"\n**{username}**: {user.bonk_amount()} bonk(s)"

                return f"**TOP BONKS**{users_string}"

            matched_users = await message.guild.query_members(additional_args.lower())

            if len(matched_users) < 1:
                return BotError.NO_USER_FOUND.format(additional_args)

            matched_user = matched_users[0]
            user = self.__data_service.get_user(matched_user.id, cached_guild.id)

            return BotMessage.USER_BONKS_INFO.format(name=matched_user.display_name, amount=user.bonk_amount())

        elif command == BotCommand.BONK:
            bonked_user = None
            if message.reference:
                resolved_reference = message.reference.resolved

                if resolved_reference:
                    bonked_user = resolved_reference.author
                else:
                    bonked_user = (
                        await message.channel.fetch_message(
                            message.reference.message_id
                        )
                    ).author

            elif len(message.mentions) > 0:
                bonked_user = message.mentions[0]

            elif not additional_args or len(additional_args) < 1:
                return BotError.MISSING_USER

            if not bonked_user:
                matched_users = await message.guild.query_members(
                    additional_args.lower()
                )

                if len(matched_users) < 1:
                    return BotError.NO_USER_FOUND.format(additional_args)

                bonked_user = matched_users[0]

            user = self.__data_service.get_user(bonked_user.id, cached_guild.id)
            user.bonk()
            self.__data_service.save_and_commit(user)

            return f"**🔨 bonk {bonked_user.display_name}**\n\n_user has been bonked {user.bonk_amount()} times so far_"

        elif command == BotCommand.HELP:
            return BotMessage.HELP
        
    async def _is_admin(self, user: User):
        guild_id = user.guild.id
        guild_config = self.__config.guild_config.get(guild_id)
        
        # allow everyone to manage when there is no guild config
        if not guild_config: return True
        
        admin_role = guild_config.admin_role
        
        guild = self.get_guild(guild_id)
        if not guild:
            return True
        
        member = guild.get_member(user.discord_id)
        if not member:
            raise ValueError(f"Couldn't find member with discord id '{user.discord_id}' in guild '{guild_id}'")
        
        return member.get_role(admin_role) is not None
    
