from hashlib import sha3_256
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = "guilds"
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(String(1))
    users: Mapped[List["User"]] = relationship()
    horny_jail_role: Mapped[int] = mapped_column(nullable=True)
    horny_jail_seconds: Mapped[int] = mapped_column(default=600)


class User(Base):
    __tablename__ = "users"
    # Not the actual discord id, since we have to be scoped to a guild -> generate a new value instead
    # The discord id is scoped across all of discord
    id: Mapped[str] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column()
    bonks: Mapped[List["Bonk"]] = relationship()
    guild: Mapped["Guild"] = mapped_column(ForeignKey("guilds.id"))
    horny_jail_until: Mapped[datetime] = mapped_column(nullable=True)

    def bonk(self):
        self.bonks.append(Bonk())

    def bonk_amount(self):
        return len(self.bonks)

    def send_to_horny_jail(
        self, jail_start: datetime = datetime.now()
    ):
        self.horny_jail_until = jail_start + timedelta(seconds=self.guild.horny_jail_seconds)

    @staticmethod
    def get_id(discord_id: int, guild_id: int) -> str:
        return sha3_256(f"{discord_id}{guild_id}").hexdigest()


class Bonk(Base):
    __tablename__ = "bonks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user: Mapped["User"] = mapped_column(ForeignKey("users.id"))
    created: Mapped[datetime] = mapped_column(DateTime, default=func.now())
