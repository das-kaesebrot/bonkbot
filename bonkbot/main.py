import discord

from .bot import BonkBot


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    client = BonkBot(intents=intents)
    client.run("token")


if __name__ == "__main__":
    main()
