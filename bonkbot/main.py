import logging
import discord
from pydantic_core import ValidationError

from .db.data_service import DataService
from .bot import BonkBot
from .config import BotConfig


def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger()

    try:
        config = BotConfig()
        logger.setLevel(logging.getLevelName(config.log_level.upper()))

        intents = discord.Intents.default()
        intents.message_content = True
        data_service = DataService(connection_string=config.db_connection_string)
        client = BonkBot(data_service=data_service, intents=intents, config=config)
        client.run(config.token, log_handler=None)
        
    except ValidationError as e:
        logger.exception("Missing config setting(s)")
        exit(1)

    except Exception as e:
        logger.exception("Exception occured")
        exit(2)


if __name__ == "__main__":
    main()
