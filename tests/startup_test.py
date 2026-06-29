import asyncio
import json
import logging
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import discord
from pydantic_core import ValidationError

from bonkbot.main import main
from bonkbot.bot import BonkBot
from bonkbot.db.data_service import DataService
from bonkbot.config import BotConfig, GuildConfig
from bonkbot.enums.default_values import HORNY_JAIL_SECONDS, HORNY_JAIL_BONKS
from bonkbot.tasks.background_task_helper import BackgroundTaskHelper


# Exit codes used in main()
EXIT_CONFIG_ERROR = 1
EXIT_GENERIC_ERROR = 2

# BotConfig defaults (mirrors bonkbot/config.py)
DEFAULT_LOG_LEVEL = "info"
DEFAULT_DB_CONNECTION = "sqlite://"

# Test tokens
TEST_TOKEN = "test-token-123"
ALT_TOKEN = "some-long-jwt-token"
JSON_TOKEN = "json-token"
ENV_TOKEN = "env-token"

# Values pre-populated in the database for guild config sync tests
DB_ADMIN_ROLE = 999
DB_JAIL_ROLE = 888
DB_JAIL_SECONDS = 999
DB_JAIL_BONKS = 999

# Values pushed from GuildConfig during sync override tests
CFG_ADMIN_ROLE = 111
CFG_JAIL_ROLE = 222
CFG_JAIL_SECONDS = 300
CFG_JAIL_BONKS = 5

# Guild IDs used in tests
TEST_GUILD_ID = 1
ALT_GUILD_ID = 2

# Guild config values parsed from JSON file
JSON_GUILD_1_ADMIN_ROLE = 11111
JSON_GUILD_1_JAIL_ROLE = 22222
JSON_GUILD_2_ADMIN_ROLE = 33333
JSON_GUILD_2_JAIL_ROLE = 44444

# On_ready debug guild
TEST_DEBUG_GUILD_ID = 1
TEST_DEBUG_GUILD_NAME = "Test Guild"


def _run(coro) -> Any:
    return asyncio.run(coro)


class AsyncIter:
    """Wraps items into an async iterable for mocking async generators."""
    def __init__(self, items):
        self._items = list(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return self._items.pop(0)
        except IndexError:
            raise StopAsyncIteration


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def mock_config() -> MagicMock:
    config = MagicMock(spec=BotConfig)
    config.token = "test-token-123"
    config.log_level = "info"
    config.db_connection_string = "sqlite://"
    config.clean_up_stale_guilds = False
    config.guild_config = {}
    return config


@pytest.fixture
def data_service() -> DataService:
    return DataService()


@pytest.fixture
def bonk_bot(data_service: DataService, mock_config: MagicMock) -> BonkBot:
    intents = discord.Intents.default()
    bot = BonkBot(data_service=data_service, intents=intents, config=mock_config)
    return bot


# ============================================================
# TestMainFunction
# ============================================================

class TestMainFunction:
    """Tests for the main() entry point in bonkbot/main.py."""

    def test_main_successful_startup(self):
        with (
            patch("bonkbot.main.logging.basicConfig"),
            patch("bonkbot.main.BotConfig") as mock_bot_config_cls,
            patch("bonkbot.main.DataService") as mock_ds_cls,
            patch("bonkbot.main.BonkBot") as mock_bot_cls,
        ):
            mock_config = MagicMock(spec=BotConfig)
            mock_config.token = TEST_TOKEN
            mock_config.log_level = DEFAULT_LOG_LEVEL
            mock_config.db_connection_string = DEFAULT_DB_CONNECTION
            mock_config.clean_up_stale_guilds = False
            mock_bot_config_cls.return_value = mock_config

            mock_ds = MagicMock(spec=DataService)
            mock_ds_cls.return_value = mock_ds

            mock_client = MagicMock(spec=discord.Client)
            mock_bot_cls.return_value = mock_client

            main()

            mock_bot_config_cls.assert_called_once()
            mock_ds_cls.assert_called_once_with(
                connection_string=mock_config.db_connection_string
            )
            _, kwargs = mock_bot_cls.call_args
            assert kwargs["data_service"] is mock_ds
            assert kwargs["config"] is mock_config

            mock_client.run.assert_called_once_with(
                mock_config.token, log_handler=None
            )

    def test_main_validation_error_exits_with_config_error_code(self):
        with (
            patch("bonkbot.main.BotConfig", side_effect=ValidationError.from_exception_data("test", line_errors=[])),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == EXIT_CONFIG_ERROR

    def test_main_generic_exception_exits_with_generic_error_code(self):
        with (
            patch("bonkbot.main.BotConfig", side_effect=RuntimeError("unexpected")),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == EXIT_GENERIC_ERROR

    def test_main_log_level_set_from_config(self):
        with (
            patch("bonkbot.main.logging.basicConfig"),
            patch("bonkbot.main.BotConfig") as mock_cls,
            patch("bonkbot.main.DataService"),
            patch("bonkbot.main.BonkBot") as mock_bot_cls,
        ):
            mock_config = MagicMock()
            mock_config.token = TEST_TOKEN
            mock_config.log_level = "debug"
            mock_config.db_connection_string = DEFAULT_DB_CONNECTION
            mock_config.clean_up_stale_guilds = False
            mock_cls.return_value = mock_config

            mock_logger = MagicMock()
            with patch("bonkbot.main.logging.getLogger", return_value=mock_logger):
                mock_client = MagicMock()
                mock_bot_cls.return_value = mock_client

                main()

                mock_logger.setLevel.assert_called_once_with(logging.DEBUG)

    def test_main_intents_message_content_enabled(self):
        with (
            patch("bonkbot.main.logging.basicConfig"),
            patch("bonkbot.main.BotConfig") as mock_cls,
            patch("bonkbot.main.DataService"),
            patch("bonkbot.main.BonkBot") as mock_bot_cls,
        ):
            mock_config = MagicMock()
            mock_config.token = TEST_TOKEN
            mock_config.log_level = DEFAULT_LOG_LEVEL
            mock_config.db_connection_string = DEFAULT_DB_CONNECTION
            mock_config.clean_up_stale_guilds = False
            mock_cls.return_value = mock_config

            mock_intents = MagicMock()
            with patch("bonkbot.main.discord.Intents") as mock_intents_cls:
                mock_intents_cls.default.return_value = mock_intents
                mock_client = MagicMock()
                mock_bot_cls.return_value = mock_client

                main()

                assert mock_intents.message_content is True


# ============================================================
# TestConfigLoading
# ============================================================

class TestConfigLoading:
    """Tests for BotConfig loading behavior."""

    @pytest.fixture(autouse=True)
    def _clean_config_env(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        for key in list(os.environ):
            if key.startswith("BONKBOT_"):
                monkeypatch.delenv(key, raising=False)

    def test_default_values(self, monkeypatch):
        monkeypatch.setenv("BONKBOT_TOKEN", TEST_TOKEN)
        config = BotConfig()
        assert config.token == TEST_TOKEN
        assert config.log_level == DEFAULT_LOG_LEVEL
        assert config.db_connection_string == DEFAULT_DB_CONNECTION
        assert config.clean_up_stale_guilds is False
        assert config.guild_config == {}

    def test_env_var_overrides(self, monkeypatch):
        monkeypatch.setenv("BONKBOT_TOKEN", TEST_TOKEN)
        monkeypatch.setenv("BONKBOT_LOG_LEVEL", "debug")
        monkeypatch.setenv("BONKBOT_DB_CONNECTION_STRING", "sqlite:///test.db")
        monkeypatch.setenv("BONKBOT_CLEAN_UP_STALE_GUILDS", "true")

        config = BotConfig()
        assert config.log_level == "debug"
        assert config.db_connection_string == "sqlite:///test.db"
        assert config.clean_up_stale_guilds is True

    def test_jwt_token_round_trip(self, monkeypatch):
        monkeypatch.setenv("BONKBOT_TOKEN", ALT_TOKEN)
        config = BotConfig()
        assert config.token == ALT_TOKEN

    def test_missing_token_raises_validation_error(self):
        with pytest.raises(ValidationError):
            BotConfig()

    def test_guild_config_from_json_file(self, monkeypatch, tmp_path):
        config_data = {
            "token": JSON_TOKEN,
            "guild_config": {
                str(TEST_GUILD_ID): {
                    "admin_role": JSON_GUILD_1_ADMIN_ROLE,
                    "horny_jail_role": JSON_GUILD_1_JAIL_ROLE,
                    "horny_jail_seconds": CFG_JAIL_SECONDS,
                    "horny_jail_bonks": CFG_JAIL_BONKS,
                    "force_override": True,
                },
                str(ALT_GUILD_ID): {
                    "admin_role": JSON_GUILD_2_ADMIN_ROLE,
                    "horny_jail_role": JSON_GUILD_2_JAIL_ROLE,
                },
            },
        }
        (tmp_path / "config.json").write_text(json.dumps(config_data))

        config = BotConfig()
        assert config.token == JSON_TOKEN
        assert TEST_GUILD_ID in config.guild_config
        assert ALT_GUILD_ID in config.guild_config

        gc1 = config.guild_config[TEST_GUILD_ID]
        assert gc1.admin_role == JSON_GUILD_1_ADMIN_ROLE
        assert gc1.horny_jail_role == JSON_GUILD_1_JAIL_ROLE
        assert gc1.horny_jail_seconds == CFG_JAIL_SECONDS
        assert gc1.horny_jail_bonks == CFG_JAIL_BONKS
        assert gc1.force_override is True

        gc2 = config.guild_config[ALT_GUILD_ID]
        assert gc2.admin_role == JSON_GUILD_2_ADMIN_ROLE
        assert gc2.horny_jail_role == JSON_GUILD_2_JAIL_ROLE
        assert gc2.horny_jail_seconds == HORNY_JAIL_SECONDS
        assert gc2.horny_jail_bonks == HORNY_JAIL_BONKS
        assert gc2.force_override is False

    def test_env_takes_priority_over_json(self, monkeypatch, tmp_path):
        monkeypatch.setenv("BONKBOT_TOKEN", ENV_TOKEN)
        monkeypatch.setenv("BONKBOT_LOG_LEVEL", "warning")

        config_data = {
            "token": JSON_TOKEN,
            "log_level": "debug",
        }
        (tmp_path / "config.json").write_text(json.dumps(config_data))

        config = BotConfig()
        assert config.token == ENV_TOKEN
        assert config.log_level == "warning"


# ============================================================
# TestBonkBotInitialization
# ============================================================

class TestBonkBotInitialization:
    """Tests for BonkBot.__init__()."""

    def test_stores_data_service(self, bonk_bot: BonkBot, data_service: DataService):
        assert bonk_bot._BonkBot__data_service is data_service

    def test_stores_config(self, bonk_bot: BonkBot, mock_config: MagicMock):
        assert bonk_bot._BonkBot__config is mock_config

    def test_creates_bg_task_helper(self, bonk_bot: BonkBot):
        assert isinstance(bonk_bot.bg_task_helper, BackgroundTaskHelper)
        assert bonk_bot.bg_task_helper.bot is bonk_bot

    def test_guild_config_sync_force_override(self, data_service: DataService):
        guild = data_service.get_guild(TEST_GUILD_ID)
        guild.admin_role = DB_ADMIN_ROLE
        guild.horny_jail_role = DB_JAIL_ROLE
        guild.horny_jail_seconds = DB_JAIL_SECONDS
        guild.horny_jail_bonks = DB_JAIL_BONKS
        data_service.save_and_commit(guild)

        config = MagicMock(spec=BotConfig)
        config.guild_config = {
            TEST_GUILD_ID: GuildConfig(
                admin_role=CFG_ADMIN_ROLE,
                horny_jail_role=CFG_JAIL_ROLE,
                horny_jail_seconds=CFG_JAIL_SECONDS,
                horny_jail_bonks=CFG_JAIL_BONKS,
                force_override=True,
            )
        }

        intents = discord.Intents.default()
        BonkBot(data_service=data_service, intents=intents, config=config)

        updated = data_service.get_guild(TEST_GUILD_ID)
        assert updated.admin_role == CFG_ADMIN_ROLE
        assert updated.horny_jail_role == CFG_JAIL_ROLE
        assert updated.horny_jail_seconds == CFG_JAIL_SECONDS
        assert updated.horny_jail_bonks == CFG_JAIL_BONKS

    def test_guild_config_sync_no_override_db_none(self, data_service: DataService):
        guild = data_service.get_guild(TEST_GUILD_ID)
        data_service.save_and_commit(guild)
        guild = data_service.get_guild(TEST_GUILD_ID)
        guild.admin_role = None
        guild.horny_jail_role = None
        guild.horny_jail_seconds = None
        guild.horny_jail_bonks = None
        data_service.save_and_commit(guild)

        config = MagicMock(spec=BotConfig)
        config.guild_config = {
            TEST_GUILD_ID: GuildConfig(
                admin_role=CFG_ADMIN_ROLE,
                horny_jail_role=CFG_JAIL_ROLE,
                horny_jail_seconds=CFG_JAIL_SECONDS,
                horny_jail_bonks=CFG_JAIL_BONKS,
                force_override=False,
            )
        }

        intents = discord.Intents.default()
        BonkBot(data_service=data_service, intents=intents, config=config)

        updated = data_service.get_guild(TEST_GUILD_ID)
        assert updated.admin_role == CFG_ADMIN_ROLE
        assert updated.horny_jail_role == CFG_JAIL_ROLE
        assert updated.horny_jail_seconds == CFG_JAIL_SECONDS
        assert updated.horny_jail_bonks == CFG_JAIL_BONKS

    def test_guild_config_sync_no_override_db_exists(self, data_service: DataService):
        guild = data_service.get_guild(TEST_GUILD_ID)
        guild.admin_role = DB_ADMIN_ROLE
        guild.horny_jail_role = DB_JAIL_ROLE
        guild.horny_jail_seconds = DB_JAIL_SECONDS
        guild.horny_jail_bonks = DB_JAIL_BONKS
        data_service.save_and_commit(guild)

        config = MagicMock(spec=BotConfig)
        config.guild_config = {
            TEST_GUILD_ID: GuildConfig(
                admin_role=CFG_ADMIN_ROLE,
                horny_jail_role=CFG_JAIL_ROLE,
                horny_jail_seconds=CFG_JAIL_SECONDS,
                horny_jail_bonks=CFG_JAIL_BONKS,
                force_override=False,
            )
        }

        intents = discord.Intents.default()
        BonkBot(data_service=data_service, intents=intents, config=config)

        updated = data_service.get_guild(TEST_GUILD_ID)
        assert updated.admin_role == DB_ADMIN_ROLE
        assert updated.horny_jail_role == DB_JAIL_ROLE
        assert updated.horny_jail_seconds == DB_JAIL_SECONDS
        assert updated.horny_jail_bonks == DB_JAIL_BONKS

    def test_no_guild_config_skips_sync(self, data_service: DataService):
        guild = data_service.get_guild(TEST_GUILD_ID)
        guild.admin_role = DB_ADMIN_ROLE
        data_service.save_and_commit(guild)

        config = MagicMock(spec=BotConfig)
        config.guild_config = {}

        intents = discord.Intents.default()
        BonkBot(data_service=data_service, intents=intents, config=config)

        updated = data_service.get_guild(TEST_GUILD_ID)
        assert updated.admin_role == DB_ADMIN_ROLE


# ============================================================
# TestOnReady
# ============================================================

class TestOnReady:
    """Tests for BonkBot.on_ready()."""

    def test_starts_background_tasks(self, bonk_bot: BonkBot):
        bonk_bot._BonkBot__logger.setLevel(logging.INFO)
        bonk_bot.bg_task_helper = AsyncMock()

        _run(bonk_bot.on_ready())

        bonk_bot.bg_task_helper.start_all.assert_called_once()

    def test_logs_guild_count(self, bonk_bot: BonkBot, data_service: DataService):
        bonk_bot._BonkBot__logger.setLevel(logging.INFO)
        bonk_bot.bg_task_helper = AsyncMock()

        _run(bonk_bot.on_ready())

        assert data_service.get_total_guild_count() == 0

    def test_debug_mode_fetches_guilds(self, bonk_bot: BonkBot):
        bonk_bot._BonkBot__logger.setLevel(logging.DEBUG)

        fake_guild = MagicMock()
        fake_guild.id = TEST_DEBUG_GUILD_ID
        fake_guild.name = TEST_DEBUG_GUILD_NAME
        bonk_bot.fetch_guilds = MagicMock(return_value=AsyncIter([fake_guild]))
        bonk_bot.bg_task_helper = AsyncMock()

        _run(bonk_bot.on_ready())

        bonk_bot.fetch_guilds.assert_called_once()
        bonk_bot.bg_task_helper.start_all.assert_called_once()

    def test_info_mode_skips_guild_fetch(self, bonk_bot: BonkBot):
        bonk_bot._BonkBot__logger.setLevel(logging.INFO)
        bonk_bot.fetch_guilds = MagicMock()
        bonk_bot.bg_task_helper = AsyncMock()

        _run(bonk_bot.on_ready())

        bonk_bot.fetch_guilds.assert_not_called()


# ============================================================
# TestBackgroundTaskHelper
# ============================================================

class TestBackgroundTaskHelper:
    """Tests for BackgroundTaskHelper."""

    def test_start_all_starts_all_jobs(self):
        bot = MagicMock()
        helper = BackgroundTaskHelper(bot)
        helper.jail_sync_job = MagicMock()
        helper.jail_sync_job.is_running.return_value = False
        helper.bot_presence_job = MagicMock()
        helper.bot_presence_job.is_running.return_value = False
        helper.guild_cleanup_job = MagicMock()
        helper.guild_cleanup_job.is_running.return_value = False

        _run(helper.start_all())

        helper.jail_sync_job.start.assert_called_once()
        helper.bot_presence_job.start.assert_called_once()
        helper.guild_cleanup_job.start.assert_called_once()

    def test_start_all_skips_running_jobs(self):
        bot = MagicMock()
        helper = BackgroundTaskHelper(bot)
        helper.jail_sync_job = MagicMock()
        helper.jail_sync_job.is_running.return_value = True
        helper.bot_presence_job = MagicMock()
        helper.bot_presence_job.is_running.return_value = False
        helper.guild_cleanup_job = MagicMock()
        helper.guild_cleanup_job.is_running.return_value = True

        _run(helper.start_all())

        helper.jail_sync_job.start.assert_not_called()
        helper.bot_presence_job.start.assert_called_once()
        helper.guild_cleanup_job.start.assert_not_called()

    def test_cog_unload_cancels_all_jobs(self):
        bot = MagicMock()
        helper = BackgroundTaskHelper(bot)
        helper.jail_sync_job = MagicMock()
        helper.bot_presence_job = MagicMock()
        helper.guild_cleanup_job = MagicMock()

        helper.cog_unload()

        helper.jail_sync_job.cancel.assert_called_once()
        helper.bot_presence_job.cancel.assert_called_once()
        helper.guild_cleanup_job.cancel.assert_called_once()

    def test_jail_sync_job_calls_bot_method(self):
        bot = MagicMock()
        bot.sync_horny_jails = AsyncMock()
        helper = BackgroundTaskHelper(bot)

        _run(helper.jail_sync_job())

        bot.sync_horny_jails.assert_called_once()

    def test_presence_job_calls_bot_method(self):
        bot = MagicMock()
        bot.update_presence = AsyncMock()
        helper = BackgroundTaskHelper(bot)

        _run(helper.bot_presence_job())

        bot.update_presence.assert_called_once()

    def test_cleanup_job_calls_bot_method(self):
        bot = MagicMock()
        bot.clean_up_unused_guilds = AsyncMock()
        helper = BackgroundTaskHelper(bot)

        _run(helper.guild_cleanup_job())

        bot.clean_up_unused_guilds.assert_called_once()
