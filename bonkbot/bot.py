import logging
import discord
from random import randrange

from .db.data_service import DataService
from .enums.bot_command import BotCommand
from .models.models import Guild, User
from .config import BotConfig
from .constants.bot_message import BotMessage
from .constants.bot_error import BotError
from .tasks.background_task_helper import BackgroundTaskHelper


class BonkBot(discord.Client):
    __data_service: DataService
    __config: BotConfig
    __logger: logging.Logger
    bg_task_helper: BackgroundTaskHelper
    __cached_activity: discord.Activity = None

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

        # synchronize settings to database in the beginning
        for guild_id, guild_config in config.guild_config.items():
            guild = self.__data_service.get_guild(guild_id)

            # only override props if unset or to be forced
            if guild_config.force_override or not guild.admin_role:
                guild.admin_role = guild_config.admin_role

            if guild_config.force_override or not guild.horny_jail_role:
                guild.horny_jail_role = guild_config.horny_jail_role

            if guild_config.force_override or not guild.horny_jail_seconds:
                guild.horny_jail_seconds = guild_config.horny_jail_seconds

            if guild_config.force_override or not guild.horny_jail_bonks:
                guild.horny_jail_bonks = guild_config.horny_jail_bonks

        self.bg_task_helper = BackgroundTaskHelper(self)
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        self.__logger.info(f"Logged on as '{self.user}'")

        # further debug info
        self.__logger.info(
            f"Serving {self.__data_service.get_total_guild_count()} guilds"
        )

        if self.__logger.level <= logging.DEBUG:
            guilds = []

            async for guild in self.fetch_guilds():
                guilds.append(
                    (guild.id, "no guild name" if not guild.name else guild.name)
                )

            self.__logger.debug(f"Registered guilds: {guilds}")

        await self.bg_task_helper.start_all()

    async def on_message(self, message: discord.Message):
        guild_prefix = self.__data_service.get_guild_prefix(message.guild.id)

        # get message with all whitespace around it removed
        message_content = message.content.strip().lower()

        # ignore all messages not starting with our prefix
        # but allow messages containing just the word bonk
        if (
            not message_content.startswith(guild_prefix)
            and not message_content == BotCommand.BONK
            and not message_content.startswith(f"{BotCommand.BONK} ")
        ):
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

        response = await self._handle_command(
            message, command, additional_args, cached_guild
        )

        if isinstance(response, str):
            await message.channel.send(response)
        elif isinstance(response, tuple):
            for msg in response:
                await message.channel.send(msg)

    async def _handle_command(
        self,
        message: discord.Message,
        command: BotCommand,
        additional_args: str | None,
        cached_guild: Guild,
    ) -> str | None:
        self.__logger.debug(f"Got command: {command=}, {additional_args=}")

        # the poor man's switch case
        # handle different bot commands, ignoring all others that don't fit

        if command == BotCommand.PREFIX:
            if not additional_args:
                # reply with prefix here
                return BotMessage.GUILD_PREFIX_INFO.format(cached_guild.prefix)

            # only allow admins to change prefix, ignore message otherwise
            if not await self._is_admin(
                self.__data_service.get_user(message.author.id, cached_guild.id)
            ):
                self.__logger.debug(
                    f"Ignoring privileged command '{command}' from unprivileged user '{message.author.id}'"
                )
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
                    users_string += f"\n**{username}**: {user.bonk_amount()} bonk{'' if user.bonk_amount() == 1 else 's'}"

                    if user.horny_jail_until:
                        users_string += f" - in horny jail until <t:{int(user.horny_jail_until.timestamp())}>"

                return f"**TOP BONKS**\n{users_string}"

            matched_user = await self._get_user_from_message(message, additional_args)

            if not matched_user:
                return BotError.NO_USER_FOUND.format(additional_args)

            user = self.__data_service.get_user(matched_user.id, cached_guild.id)

            return BotMessage.USER_BONKS_INFO.format(
                name=matched_user.display_name, amount=user.bonk_amount()
            )

        elif command == BotCommand.BONK:
            bonked_user = await self._get_user_from_message(message, additional_args)

            if not bonked_user:
                return BotError.NO_USER_FOUND.format(additional_args)

            user = self.__data_service.get_user(bonked_user.id, cached_guild.id)
            user.bonk()
            self.__data_service.save_and_commit(user)

            if not user.bonk_amount() % cached_guild.horny_jail_bonks == 0:
                return BotMessage.BONK.format(
                    name=bonked_user.display_name, amount=user.bonk_amount()
                )

            await self._send_to_horny_jail(user)
            return BotMessage.BONK.format(
                name=bonked_user.display_name, amount=user.bonk_amount()
            ), BotMessage.SENT_TO_JAIL.format(
                name=bonked_user.display_name,
                timestamp=int(user.horny_jail_until.timestamp()),
            )

        elif command == BotCommand.PARDON:
            # only allow admins to pardon, ignore message otherwise
            if not await self._is_admin(
                self.__data_service.get_user(message.author.id, cached_guild.id)
            ):
                self.__logger.debug(
                    f"Ignoring privileged command '{command}' from unprivileged user '{message.author.id}'"
                )
                return

            matched_user = await self._get_user_from_message(message, additional_args)

            if not matched_user:
                return BotError.NO_USER_FOUND.format(additional_args)

            user = self.__data_service.get_user(matched_user.id, cached_guild.id)
            if not user.horny_jail_until:
                return

            user.pardon()
            self.__data_service.save_and_commit(user)
            await self._free_user_from_jail(user)
            return BotMessage.PARDONED.format(matched_user.display_name)

        elif command == BotCommand.JAIL:
            # only allow admins to immediately send to jail, ignore message otherwise
            if not await self._is_admin(
                self.__data_service.get_user(message.author.id, cached_guild.id)
            ):
                self.__logger.debug(
                    f"Ignoring privileged command '{command}' from unprivileged user '{message.author.id}'"
                )
                return

            matched_user = await self._get_user_from_message(message, additional_args)

            if not matched_user:
                return BotError.NO_USER_FOUND.format(additional_args)

            user = self.__data_service.get_user(matched_user.id, cached_guild.id)
            await self._send_to_horny_jail(user)

            return BotMessage.SENT_TO_JAIL.format(
                name=matched_user.display_name,
                timestamp=int(user.horny_jail_until.timestamp()),
            )

        elif command == BotCommand.ADMINROLE or command == BotCommand.JAILROLE:
            # only allow admins to set roles, ignore message otherwise
            if not await self._is_admin(
                self.__data_service.get_user(message.author.id, cached_guild.id)
            ):
                self.__logger.debug(
                    f"Ignoring privileged command '{command}' from unprivileged user '{message.author.id}'"
                )
                return

            if not additional_args or len(additional_args) < 1:
                if command == BotCommand.ADMINROLE:
                    return BotMessage.ADMIN_ROLE_INFO.format(cached_guild.admin_role)
                return BotMessage.JAIL_ROLE_INFO.format(cached_guild.horny_jail_role)

            if len(message.role_mentions) != 1:
                return BotError.MISSING_ROLE_MENTION

            role_id = message.role_mentions[0].id

            if command == BotCommand.ADMINROLE:
                cached_guild.admin_role = role_id
            else:
                cached_guild.horny_jail_role = role_id

            self.__data_service.save_and_commit(cached_guild)

            if command == BotCommand.ADMINROLE:
                return BotMessage.ADMIN_ROLE_SET.format(cached_guild.admin_role)

            return BotMessage.JAIL_ROLE_SET.format(cached_guild.horny_jail_role)

        elif command == BotCommand.JAILTIME or command == BotCommand.JAILBONKS:
            # only allow admins, ignore message otherwise
            if not await self._is_admin(
                self.__data_service.get_user(message.author.id, cached_guild.id)
            ):
                self.__logger.debug(
                    f"Ignoring privileged command '{command}' from unprivileged user '{message.author.id}'"
                )
                return

            if not additional_args or len(additional_args) < 1:
                if command == BotCommand.JAILTIME:
                    return BotMessage.JAIL_TIME_INFO.format(
                        cached_guild.horny_jail_seconds
                    )
                return BotMessage.JAIL_BONKS_INFO.format(cached_guild.horny_jail_bonks)

            if len(additional_args) != 1:
                return BotError.MISSING_NUMBER

            number = 0
            try:
                number = int(additional_args)
            except ValueError:
                return BotError.MISSING_NUMBER

            if command == BotCommand.JAILTIME:
                cached_guild.horny_jail_seconds = number
            else:
                cached_guild.horny_jail_bonks = number

            self.__data_service.save_and_commit(cached_guild)

            if command == BotCommand.JAILTIME:
                return BotMessage.JAIL_TIME_SET.format(cached_guild.horny_jail_seconds)

            return BotMessage.JAIL_TIME_SET.format(cached_guild.horny_jail_bonks)

        elif command == BotCommand.HELP:
            return BotMessage.HELP.format(prefix=cached_guild.prefix)

    async def _get_user_from_message(
        self, message: discord.Message, additional_args: str
    ) -> discord.User | discord.Member | None:
        # if the message is a reference (reply) to another message,
        # return the author of the referenced message
        if message.reference:
            resolved_reference = message.reference.resolved

            # return author of the referenced message
            if resolved_reference:
                return resolved_reference.author

            # if the message is not resolved yet, resolve it and then return the author
            return (
                await message.channel.fetch_message(message.reference.message_id)
            ).author

        # if someone was mentioned, return the first mention
        if len(message.mentions) > 0:
            return message.mentions[0]

        # if we weren't able to identify anyone yet, check if a username string was in the message
        # --> return None if there is no additional info
        if not additional_args or len(additional_args) < 1:
            return

        if additional_args.lower() == "self":
            return message.author

        # try matching a user by querying members
        matched_user = discord.utils.find(
            lambda m: (m.name.find(additional_args.lower()) != -1)
            or ((m.nick is not None) and (m.nick.find(additional_args.lower()) != -1)),
            message.channel.guild.members,
        )

        return matched_user

    async def _is_admin(self, user: User):
        guild_id = user.guild
        admin_role = self.__data_service.get_guild(guild_id).admin_role

        # allow everyone to manage when there is no admin role set
        if not admin_role:
            return True

        guild = await self.fetch_guild(guild_id)
        if not guild:
            return True

        member = await guild.fetch_member(user.discord_id)
        if not member:
            raise ValueError(
                f"Couldn't find member with discord id '{user.discord_id}' in guild '{guild_id}'"
            )

        return member.get_role(admin_role) is not None

    async def sync_horny_jails(self):
        self.__logger.info("Running jail synchronisation")
        free_users = self.__data_service.get_all_pending_jail_releases()

        if len(free_users) < 1:
            return

        for user in free_users:
            self.__logger.debug(
                f"Freeing user '{user.discord_id}' in guild '{user.guild}' from jail"
            )
            await self._free_user_from_jail(user)

        self.__data_service.set_users_free(free_users)
        self.__logger.info(f"Freed {len(free_users)} from jail")

    async def update_presence(self):
        self.__logger.info("Updating presence")
        activity = discord.Activity()
        activity.name = "Bonking users"

        if randrange(0, 100) != 0:
            bonk_count = self.__data_service.get_total_bonk_count()
            horny_jail_count = self.__data_service.get_total_users_in_horny_jail_count()
            activity.state = f"{bonk_count:,} total bonk{'' if bonk_count == 1 else 's'} - {horny_jail_count:,} user{'' if horny_jail_count == 1 else 's'} in horny jail"
        else:
            activity.state = "Picking Donut's new fridge"
        activity.type = discord.ActivityType.custom

        # early bailout if nothing changed
        if self.__cached_activity and activity.state == self.__cached_activity:
            return

        self.__logger.info("Activity changed, updating presence via API")
        self.__cached_activity = activity.state
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def _free_user_from_jail(self, user: User):
        discord_guild = await self.fetch_guild(user.guild)
        guild = self.__data_service.get_guild(user.guild)
        horny_jail_role = guild.horny_jail_role

        if not (discord_guild or horny_jail_role):
            return

        member = await discord_guild.fetch_member(user.discord_id)
        role = discord_guild.get_role(horny_jail_role)
        await member.remove_roles(role)

    async def _send_to_horny_jail(self, user: User):
        guild = self.__data_service.get_guild(user.guild)

        # don't actually do anything if there is no horny jail role set yet
        if not guild.horny_jail_role:
            return

        user.send_to_horny_jail(guild.horny_jail_seconds)
        horny_jail_role = guild.horny_jail_role

        self.__data_service.save_and_commit(user)

        discord_guild = await self.fetch_guild(guild.id)
        if not discord_guild:
            return

        member = await discord_guild.fetch_member(user.discord_id)
        role = discord_guild.get_role(horny_jail_role)
        await member.add_roles(role)

    def _check_privileges(self, message: discord.Message, cached_guild: Guild):
        pass
