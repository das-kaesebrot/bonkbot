
from typing import Dict, Tuple, Type
from pydantic_settings import BaseSettings, JsonConfigSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict

class GuildConfig(BaseSettings):
    admin_role: int | None = None
    horny_jail_role: int | None = None
    horny_jail_seconds: int = 600
    horny_jail_bonks: int = 10
    force_override: bool = False
    
class BotConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='BONKBOT_', json_file="config.json")
    
    token: str
    log_level: str = "info"
    db_connection_string: str = "sqlite://"
    
    guild_config: Dict[int, GuildConfig] = {}
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            JsonConfigSettingsSource(settings_cls=settings_cls),
            file_secret_settings,
        )