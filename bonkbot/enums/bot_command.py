from enum import StrEnum


class BotCommand(StrEnum):
    BONK = "bonk"
    BONKS = "bonks"
    PREFIX = "bonkprefix"
    HELP = "bonkhelp"
    
    @staticmethod
    def list():
        return list(map(lambda c: c.value, BotCommand))