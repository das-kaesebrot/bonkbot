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
        return list(map(lambda c: c.value, BotCommand))