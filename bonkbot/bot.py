import asyncio
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
    __logger: logging.Logger

    def __init__(
        self,
        *,
        data_service: DataService,
        intents: discord.Intents,
        config: BotConfig,
        **options,
    ) -> None:
        self.__logger = logging.getLogger(__name__)
        self.__data_service = data_service
        self.__config = config
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        self.__logger.info(f"Logged on as '{self.user}'")

    async def on_message(self, message: discord.Message):
        guild_prefix = self.__data_service.get_guild_prefix(message.guild.id)

        # get message with all whitespace around it removed
        message_content = message.content.strip().lower()

        # ignore all messages not starting with our prefix
        # but allow messages containing just the word bonk
        if not message_content.startswith(guild_prefix) and message_content != BotCommand.BONK:
            return
        
        cached_guild = self.__data_service.get_guild(message.guild.id)

        # remove the prefix
        message_content = message_content.removeprefix(guild_prefix)

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
            if not await self._is_admin(self.__data_service.get_user(message.author.id, cached_guild.id)):
                self.__logger.debug(f"Ignoring privileged command '{command}' from unprivileged user '{message.author.id}'")
                return
            
            # special case, allow reset as a keyword to go back to the exclamation mark
            if additional_args.lower() == "reset":
                additional_args = "!"
            
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

            matched_user = await self.__get_user_from_message(message, additional_args)
            
            if not matched_user:
                return BotError.NO_USER_FOUND.format(additional_args)

            user = self.__data_service.get_user(matched_user.id, cached_guild.id)

            return BotMessage.USER_BONKS_INFO.format(name=matched_user.display_name, amount=user.bonk_amount())

        elif command == BotCommand.BONK:
            bonked_user = await self.__get_user_from_message(message, additional_args)
            
            if not bonked_user:
                return BotError.NO_USER_FOUND.format(additional_args)

            user = self.__data_service.get_user(bonked_user.id, cached_guild.id)
            user.bonk()
            self.__data_service.save_and_commit(user)

            return BotMessage.BONK.format(name=bonked_user.display_name, amount=user.bonk_amount())

        elif command == BotCommand.HELP:
            return BotMessage.HELP
        
    async def __get_user_from_message(self, message: discord.Message, additional_args: str) -> discord.User | discord.Member | None:
        # if the message is a reference (reply) to another message,
        # return the author of the referenced message
        if message.reference:
            resolved_reference = message.reference.resolved
            
            # return author of the referenced message
            if resolved_reference:
                return resolved_reference.author
            
            # if the message is not resolved yet, resolve it and then return the author
            return (
                await message.channel.fetch_message(
                    message.reference.message_id
                )
            ).author
            
        # if someone was mentioned, return the first mention
        if len(message.mentions) > 0:
            return message.mentions[0]
        
        # if we weren't able to identify anyone yet, check if a username string was in the message
        # --> return None if there is no additional info
        if not additional_args or len(additional_args) < 1:
            return

        # try matching a user by querying members
        matched_users = await message.guild.query_members(
            additional_args.lower()
        )
        
        # if there was a match, return the first result
        if len(matched_users) > 0:
            return matched_users[0]
        
    
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
    
    def sync_horny_jails(self):
        loop = asyncio.get_event_loop()        
        loop.run_until_complete(self.__async_horny_jails())
        
    async def __async_horny_jails(self):
        free_users = self.__data_service.get_all_pending_jail_releases()
        
        for user in free_users:
            guild = self.get_guild(user.guild.id)
            horny_jail_role = user.guild.horny_jail_role
            
            if not guild or not horny_jail_role:
                continue
            
            member = guild.get_member(user.discord_id)
            await member.remove_roles([horny_jail_role])
        
        self.__data_service.set_users_free(free_users)
    
    async def _send_to_horny_jail(self, user: User):
        # don't actually do anything if there is no horny jail role set yet
        if not user.guild.horny_jail_role:
            return
        
        user.send_to_horny_jail()
        
        guild = self.get_guild(user.guild.id)
        horny_jail_role = user.guild.horny_jail_role
        
        if not guild:
            return
        
        member = guild.get_member(user.discord_id)
        await member.add_roles([horny_jail_role])
        