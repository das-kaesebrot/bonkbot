import logging
import discord

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

    except Exception as e:
        logger.exception("Exception occured")
        exit(1)


if __name__ == "__main__":
    main()
