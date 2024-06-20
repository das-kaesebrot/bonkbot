
from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    token: str