from enum import StrEnum


class BotCommand(StrEnum):
    BONK = "bonk"
    BONKS = "bonks"
    PREFIX = "bonkprefix"
    HELP = "bonkhelp"
    PARDON = "bonkpardon"
    ADMINROLE = "bonkadmin"
    JAILROLE = "bonkjail"
    JAILTIME = "bonkjailtime"
    JAILBONKS = "bonkjailamount"
    JAIL = "hornyjail"

    @staticmethod
    def list():
        return [c.value for c in BotCommand]
