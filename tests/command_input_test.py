import asyncio
from datetime import datetime, timedelta
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import discord
from bonkbot.bot import BonkBot
from bonkbot.db.data_service import DataService
from bonkbot.config import BotConfig
from bonkbot.enums.bot_command import BotCommand
from bonkbot.constants.bot_message import BotMessage
from bonkbot.constants.bot_error import BotError
from bonkbot.models.models import Guild, User


def _run(coro) -> Any:
    return asyncio.run(coro)


@pytest.fixture
def data_service() -> DataService:
    return DataService()


@pytest.fixture
def bonk_bot(data_service: DataService) -> BonkBot:
    config = MagicMock(spec=BotConfig)
    config.guild_config = {}
    intents = discord.Intents.default()
    bot = BonkBot(data_service=data_service, intents=intents, config=config)
    return bot


@pytest.fixture
def cached_guild(data_service: DataService) -> Guild:
    guild = data_service.get_guild(1)
    guild.prefix = "!"
    guild.horny_jail_bonks = 10
    guild.horny_jail_seconds = 600
    guild.horny_jail_role = 12345
    guild.admin_role = 67890
    data_service.save_and_commit(guild)
    return guild


@pytest.fixture
def mock_member() -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = 99999
    member.display_name = "TestMember"
    member.name = "testmember"
    member.nick = None
    return member


@pytest.fixture
def mock_message(mock_member: MagicMock) -> MagicMock:
    message = MagicMock(spec=discord.Message)
    message.content = "!bonk"
    message.author = mock_member
    message.mentions = []
    message.role_mentions = []
    message.reference = None
    message.channel = MagicMock()
    message.channel.fetch_message = AsyncMock()
    message.channel.send = AsyncMock()
    message.guild = MagicMock()
    message.guild.id = 1
    message.guild.members = [mock_member]
    message.guild.fetch_member = AsyncMock(return_value=mock_member)
    message.channel.guild = message.guild
    return message


@pytest.fixture(autouse=True)
def patch_bot_side_effects(bonk_bot: BonkBot) -> Generator[None, None, None]:
    async def _mock_send_to_jail(user: User) -> None:
        user.horny_jail_until = datetime.now() + timedelta(seconds=600)

    with patch.object(bonk_bot, '_is_admin', AsyncMock(return_value=True)):
        with patch.object(
            bonk_bot, '_send_to_horny_jail',
            AsyncMock(side_effect=_mock_send_to_jail)
        ):
            with patch.object(bonk_bot, '_free_user_from_jail', AsyncMock()):
                yield


# ============================================================
# User resolution (_get_user_from_message) input tests
# ============================================================

class TestUserResolutionInputs:
    def test_reply_resolved_returns_author(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        referenced_author = MagicMock(spec=discord.User)
        referenced_author.id = 11111
        resolved = MagicMock(spec=discord.Message)
        resolved.author = referenced_author
        mock_message.reference = MagicMock()
        mock_message.reference.resolved = resolved

        result = _run(bonk_bot._get_user_from_message(mock_message, None))
        assert result == referenced_author

    def test_reply_unresolved_fetches_and_returns_author(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        referenced_author = MagicMock(spec=discord.User)
        referenced_author.id = 22222
        resolved_message = MagicMock()
        resolved_message.author = referenced_author
        mock_message.reference = MagicMock()
        mock_message.reference.resolved = None
        mock_message.reference.message_id = 555
        mock_message.channel.fetch_message = AsyncMock(return_value=resolved_message)

        result = _run(bonk_bot._get_user_from_message(mock_message, "ignored"))
        assert result == referenced_author
        mock_message.channel.fetch_message.assert_called_once_with(555)

    def test_mention_returns_first_mention(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        mentioned = MagicMock(spec=discord.Member)
        mentioned.id = 33333
        mock_message.mentions = [mentioned]

        result = _run(bonk_bot._get_user_from_message(mock_message, "ignored"))
        assert result == mentioned

    @pytest.mark.parametrize("search_arg", [None, ""])
    def test_no_args_returns_none(self, bonk_bot: BonkBot, mock_message: MagicMock, search_arg: str | None) -> None:
        result = _run(bonk_bot._get_user_from_message(mock_message, search_arg))
        assert result is None

    @pytest.mark.parametrize("keyword", ["self", "SELF", "Self", "sELF"])
    def test_self_keyword(self, bonk_bot: BonkBot, mock_message: MagicMock, mock_member: MagicMock, keyword: str) -> None:
        result = _run(bonk_bot._get_user_from_message(mock_message, keyword))
        assert result == mock_member

    @pytest.mark.parametrize("name", ["testmember", "test", "member", "testmem"])
    def test_name_matches(self, bonk_bot: BonkBot, mock_message: MagicMock, mock_member: MagicMock, name: str) -> None:
        result = _run(bonk_bot._get_user_from_message(mock_message, name))
        assert result == mock_member

    def test_nick_match_lowercase(self, bonk_bot: BonkBot, mock_message: MagicMock, mock_member: MagicMock) -> None:
        mock_member.nick = "fancynick"
        result = _run(bonk_bot._get_user_from_message(mock_message, "fancy"))
        assert result == mock_member

    @pytest.mark.parametrize("search_arg", ["nonexistent", "xyz", ""])
    def test_no_match_returns_none(self, bonk_bot: BonkBot, mock_message: MagicMock, search_arg: str) -> None:
        result = _run(bonk_bot._get_user_from_message(mock_message, search_arg))
        assert result is None

    def test_reply_preferred_over_mention(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        referenced_author = MagicMock(spec=discord.User)
        referenced_author.id = 444
        resolved = MagicMock(spec=discord.Message)
        resolved.author = referenced_author
        mock_message.reference = MagicMock()
        mock_message.reference.resolved = resolved

        mentioned = MagicMock(spec=discord.Member)
        mentioned.id = 555
        mock_message.mentions = [mentioned]

        result = _run(bonk_bot._get_user_from_message(mock_message, "ignored"))
        assert result == referenced_author


# ============================================================
# bonkprefix command input tests
# ============================================================

class TestBonkPrefixInputs:
    def test_no_args_returns_info(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PREFIX, None, cached_guild
        ))
        assert result == BotMessage.GUILD_PREFIX_INFO.format("!")

    @pytest.mark.parametrize("arg", ["", " "])
    def test_empty_or_blank_args_returns_info(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str | None) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PREFIX, arg, cached_guild
        ))
        assert result == BotMessage.GUILD_PREFIX_INFO.format("!")

    @pytest.mark.parametrize("char", ["?", ".", "$", "#", "@", "~"])
    def test_valid_single_char_sets_prefix(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, char: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PREFIX, char, cached_guild
        ))
        assert result == BotMessage.GUILD_PREFIX_SET.format(char)

    @pytest.mark.parametrize("reset_arg", ["reset", "RESET", "Reset", "RESET"])
    def test_reset_keyword(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, reset_arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PREFIX, reset_arg, cached_guild
        ))
        assert result == BotMessage.GUILD_PREFIX_SET.format("!")

    @pytest.mark.parametrize("bad_prefix", ["??", "...", "abc", "a b"])
    def test_invalid_prefix_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, bad_prefix: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PREFIX, bad_prefix, cached_guild
        ))
        assert result == BotError.INVALID_PREFIX.format(bad_prefix)


# ============================================================
# bonks command input tests
# ============================================================

class TestBonksInputs:
    def test_no_args_returns_leaderboard(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONKS, None, cached_guild
        ))
        assert result == "**TOP BONKS**\n"

    @pytest.mark.parametrize("arg", ["self", "testmember", "member", "test"])
    def test_user_resolution_returns_bonk_count(self, bonk_bot: BonkBot, mock_message: MagicMock, mock_member: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONKS, arg, cached_guild
        ))
        assert result == BotMessage.USER_BONKS_INFO.format(
            name=mock_member.display_name, amount=0
        )

    def test_with_mention_returns_bonk_count(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        mentioned = MagicMock(spec=discord.Member)
        mentioned.id = 777
        mentioned.display_name = "MentionedUser"
        mock_message.mentions = [mentioned]

        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONKS, "<@777>", cached_guild
        ))
        assert result == BotMessage.USER_BONKS_INFO.format(
            name=mentioned.display_name, amount=0
        )

    @pytest.mark.parametrize("arg", ["nonexistent", "xyzzy", "unknown"])
    def test_no_match_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONKS, arg, cached_guild
        ))
        assert result == BotError.NO_USER_FOUND.format(arg)


# ============================================================
# bonk command input tests
# ============================================================

class TestBonkInputs:
    def test_no_args_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONK, None, cached_guild
        ))
        assert result == BotError.NO_USER_FOUND.format(None)

    @pytest.mark.parametrize("arg", ["self", "testmember", "member", "test"])
    def test_user_resolution_bonks_user(self, bonk_bot: BonkBot, mock_message: MagicMock, mock_member: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONK, arg, cached_guild
        ))
        assert result == BotMessage.BONK.format(
            name=mock_member.display_name, amount=1
        )

    def test_with_mention_bonks_user(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        mentioned = MagicMock(spec=discord.Member)
        mentioned.id = 888
        mentioned.display_name = "MentionedUser"
        mock_message.mentions = [mentioned]

        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONK, "<@888>", cached_guild
        ))
        assert result == BotMessage.BONK.format(
            name=mentioned.display_name, amount=1
        )

    @pytest.mark.parametrize("arg", ["nonexistent", "xyzzy", "unknown"])
    def test_no_match_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONK, arg, cached_guild
        ))
        assert result == BotError.NO_USER_FOUND.format(arg)

    def test_reply_preferred_over_args(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        referenced_author = MagicMock(spec=discord.User)
        referenced_author.id = 111
        referenced_author.display_name = "RepliedUser"
        resolved = MagicMock(spec=discord.Message)
        resolved.author = referenced_author
        mock_message.reference = MagicMock()
        mock_message.reference.resolved = resolved

        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.BONK, "self", cached_guild
        ))
        assert result == BotMessage.BONK.format(
            name=referenced_author.display_name, amount=1
        )


# ============================================================
# bonkpardon command input tests
# ============================================================

class TestBonkPardonInputs:
    def test_no_args_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PARDON, None, cached_guild
        ))
        assert result == BotError.NO_USER_FOUND.format(None)

    @pytest.mark.parametrize("arg", ["self", "testmember", "member", "test"])
    def test_non_jailed_user_returns_none(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PARDON, arg, cached_guild
        ))
        assert result is None

    @pytest.mark.parametrize("arg", ["nonexistent", "xyzzy", "unknown"])
    def test_no_match_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.PARDON, arg, cached_guild
        ))
        assert result == BotError.NO_USER_FOUND.format(arg)


# ============================================================
# hornyjail command input tests
# ============================================================

class TestHornyJailInputs:
    def test_no_args_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAIL, None, cached_guild
        ))
        assert result == BotError.NO_USER_FOUND.format(None)

    @pytest.mark.parametrize("arg", ["self", "testmember", "member", "test"])
    def test_user_resolution_jails_user(self, bonk_bot: BonkBot, mock_message: MagicMock, mock_member: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAIL, arg, cached_guild
        ))
        assert isinstance(result, str)
        assert mock_member.display_name in result

    @pytest.mark.parametrize("arg", ["nonexistent", "xyzzy", "unknown"])
    def test_no_match_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAIL, arg, cached_guild
        ))
        assert result == BotError.NO_USER_FOUND.format(arg)


# ============================================================
# bonkadmin / bonkjail role command input tests
# ============================================================

class TestAdminRoleInputs:
    @pytest.mark.parametrize("arg", [None, ""])
    def test_no_or_empty_args_returns_info(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str | None) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.ADMINROLE, arg, cached_guild
        ))
        assert result == BotMessage.ADMIN_ROLE_INFO.format(cached_guild.admin_role)

    def test_one_role_mention_sets_role(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        role = MagicMock(spec=discord.Role)
        role.id = 123456
        mock_message.role_mentions = [role]

        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.ADMINROLE, "<@&123456>", cached_guild
        ))
        assert result == BotMessage.ADMIN_ROLE_SET.format(123456)

    def test_zero_role_mentions_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        mock_message.role_mentions = []
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.ADMINROLE, "somearg", cached_guild
        ))
        assert result == BotError.MISSING_ROLE_MENTION

    def test_multiple_role_mentions_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        mock_message.role_mentions = [
            MagicMock(spec=discord.Role),
            MagicMock(spec=discord.Role),
        ]
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.ADMINROLE, "somearg", cached_guild
        ))
        assert result == BotError.MISSING_ROLE_MENTION


class TestJailRoleInputs:
    def test_no_args_returns_info(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILROLE, None, cached_guild
        ))
        assert result == BotMessage.JAIL_ROLE_INFO.format(cached_guild.horny_jail_role)

    def test_one_role_mention_sets_role(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        role = MagicMock(spec=discord.Role)
        role.id = 789012
        mock_message.role_mentions = [role]

        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILROLE, "<@&789012>", cached_guild
        ))
        assert result == BotMessage.JAIL_ROLE_SET.format(789012)

    def test_zero_role_mentions_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        mock_message.role_mentions = []
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILROLE, "somearg", cached_guild
        ))
        assert result == BotError.MISSING_ROLE_MENTION


# ============================================================
# bonkjailtime / bonkjailamount numeric command input tests
# ============================================================

class TestJailTimeInputs:
    @pytest.mark.parametrize("arg", [None, ""])
    def test_no_or_empty_args_returns_info(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str | None) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILTIME, arg, cached_guild
        ))
        assert result == BotMessage.JAIL_TIME_INFO.format(cached_guild.horny_jail_seconds)

    @pytest.mark.parametrize("arg,expected", [("5", 5), ("0", 0), ("1", 1), ("9", 9), ("600", 600)])
    def test_valid_integer_sets_time(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str, expected: int) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILTIME, arg, cached_guild
        ))
        assert result == BotMessage.JAIL_TIME_SET.format(expected)

    @pytest.mark.parametrize("arg", ["abc", "5 4", "-5", "3.14"])
    def test_invalid_input_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILTIME, arg, cached_guild
        ))
        assert result == BotError.BAD_NUMBER


class TestJailAmountInputs:
    def test_no_args_returns_info(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILBONKS, None, cached_guild
        ))
        assert result == BotMessage.JAIL_BONKS_INFO.format(cached_guild.horny_jail_bonks)

    @pytest.mark.parametrize("arg,expected", [("5", 5), ("0", 0), ("1", 1), ("9", 9), ("600", 600)])
    def test_valid_integer_sets_amount(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str, expected: int) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILBONKS, arg, cached_guild
        ))
        assert result == BotMessage.JAIL_TIME_SET.format(expected)

    @pytest.mark.parametrize("arg", ["abc", "5 4", "-5", "3.14"])
    def test_invalid_input_returns_error(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.JAILBONKS, arg, cached_guild
        ))
        assert result == BotError.BAD_NUMBER


# ============================================================
# bonkhelp command input tests
# ============================================================

class TestHelpInput:
    @pytest.mark.parametrize("arg", [None, "", "anything", "help", "bonk"])
    def test_returns_help_message(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild, arg: str | None) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, BotCommand.HELP, arg, cached_guild
        ))
        assert result == BotMessage.HELP.format(prefix="!")


# ============================================================
# Unknown command input test
# ============================================================

class TestUnknownCommand:
    def test_unknown_command_returns_none(self, bonk_bot: BonkBot, mock_message: MagicMock, cached_guild: Guild) -> None:
        result = _run(bonk_bot._handle_command(
            mock_message, "nonexistentcommand", None, cached_guild
        ))
        assert result is None


# ============================================================
# on_message message routing tests
# ============================================================

class TestOnMessageRouting:
    def test_message_with_prefix_parses_command(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        mock_message.content = "!bonkprefix"
        with patch.object(bonk_bot, '_handle_command', AsyncMock(return_value=None)):
            _run(bonk_bot.on_message(mock_message))
            bonk_bot._handle_command.assert_called_once()
            args = bonk_bot._handle_command.call_args[0]
            assert args[1] == BotCommand.PREFIX
            assert args[2] is None

    def test_message_with_prefix_and_args(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        mock_message.content = "!bonkprefix ?"
        with patch.object(bonk_bot, '_handle_command', AsyncMock(return_value=None)):
            _run(bonk_bot.on_message(mock_message))
            bonk_bot._handle_command.assert_called_once()
            args = bonk_bot._handle_command.call_args[0]
            assert args[1] == BotCommand.PREFIX
            assert args[2] == "?"

    @pytest.mark.parametrize("content", ["hello world", "foo bar", "123", "test message"])
    def test_message_without_prefix_ignored(self, bonk_bot: BonkBot, mock_message: MagicMock, content: str) -> None:
        mock_message.content = content
        with patch.object(bonk_bot, '_handle_command', AsyncMock()) as mock:
            _run(bonk_bot.on_message(mock_message))
            mock.assert_not_called()

    def test_bare_bonk_allowed_without_prefix(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        mock_message.content = "bonk"
        cached_prefix = bonk_bot._BonkBot__data_service.get_guild_prefix(mock_message.guild.id)
        assert cached_prefix == "!"
        with patch.object(bonk_bot, '_handle_command', AsyncMock(return_value=None)):
            _run(bonk_bot.on_message(mock_message))
            bonk_bot._handle_command.assert_called_once()
            args = bonk_bot._handle_command.call_args[0]
            assert args[1] == BotCommand.BONK

    def test_bonk_with_args_allowed_without_prefix(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        mock_message.content = "bonk self"
        with patch.object(bonk_bot, '_handle_command', AsyncMock(return_value=None)):
            _run(bonk_bot.on_message(mock_message))
            bonk_bot._handle_command.assert_called_once()
            args = bonk_bot._handle_command.call_args[0]
            assert args[1] == BotCommand.BONK
            assert args[2] == "self"

    @pytest.mark.parametrize("content", ["!bonk", "bonk", "!bonkprefix", "hello world"])
    def test_self_messages_ignored(self, bonk_bot: BonkBot, mock_message: MagicMock, content: str) -> None:
        mock_message.content = content
        mock_message.author = bonk_bot.user
        with patch.object(bonk_bot, '_handle_command', AsyncMock()) as mock:
            _run(bonk_bot.on_message(mock_message))
            mock.assert_not_called()

    def test_prefix_stripped_before_parsing(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        mock_message.content = "!bonks"
        with patch.object(bonk_bot, '_handle_command', AsyncMock(return_value=None)):
            _run(bonk_bot.on_message(mock_message))
            bonk_bot._handle_command.assert_called_once()
            args = bonk_bot._handle_command.call_args[0]
            assert args[1] == BotCommand.BONKS
            assert args[2] is None

    def test_multiple_args_joined_correctly(self, bonk_bot: BonkBot, mock_message: MagicMock) -> None:
        mock_message.content = "!bonk very long user name"
        with patch.object(bonk_bot, '_handle_command', AsyncMock(return_value=None)):
            _run(bonk_bot.on_message(mock_message))
            bonk_bot._handle_command.assert_called_once()
            args = bonk_bot._handle_command.call_args[0]
            assert args[1] == BotCommand.BONK
            assert args[2] == "very long user name"

    @pytest.mark.parametrize("content", ["bonkhelp", "bonkxyz", "bonkfoo", "bonk123", "BONKhelp"])
    def test_non_bonk_messages_without_prefix_ignored(self, bonk_bot: BonkBot, mock_message: MagicMock, content: str) -> None:
        mock_message.content = content
        with patch.object(bonk_bot, '_handle_command', AsyncMock()) as mock:
            _run(bonk_bot.on_message(mock_message))
            mock.assert_not_called()
