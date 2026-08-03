from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class GuildConfig(BaseSettings):
    admin_role: int | None = None
    horny_jail_role: int | None = None
    horny_jail_seconds: int = 600
    horny_jail_bonks: int = 10
    force_override: bool = False


class BotConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BONKBOT_", json_file="config.json")

    token: str
    log_level: str = "info"
    db_connection_string: str = "sqlite://"
    clean_up_stale_guilds: bool = False

    guild_config: dict[int, GuildConfig] = {}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            JsonConfigSettingsSource(settings_cls=settings_cls),
            file_secret_settings,
        )
