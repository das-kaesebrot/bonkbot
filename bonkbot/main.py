import logging
import discord

from .bot import BonkBot


def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=logging.DEBUG,
    )
    logger = logging.getLogger()

    try:

        intents = discord.Intents.default()
        intents.message_content = True
        client = BonkBot(intents=intents)
        client.run("token")

    except Exception as e:
        logger.exception("Exception occured")
        exit(1)


if __name__ == "__main__":
    main()
