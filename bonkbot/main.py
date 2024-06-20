import logging
import discord
from pydantic_core import ValidationError

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
        client = BonkBot(intents=intents)
        client.run(config.token)
        
    except ValidationError as e:
        logger.exception("Missing config setting(s)")
        exit(1)

    except Exception as e:
        logger.exception("Exception occured")
        exit(2)


if __name__ == "__main__":
    main()
