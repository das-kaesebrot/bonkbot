
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='BONKBOT_')
    
    token: str
    log_level: str = "info"