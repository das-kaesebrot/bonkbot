from typing import List
from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


user_guild = Table(
    "user_guild",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("guild_id", ForeignKey("guilds.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    # Not the actual discord id, since we have to be scoped to a guild -> generate a new value instead
    # The discord id is scoped across all of discord
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column()
    bonks: Mapped[List["Bonk"]] = relationship()
    guild: Mapped["Guild"] = mapped_column(ForeignKey("guilds.id"))
    horny_jail_until: Mapped[datetime] = mapped_column(nullable=True)
    
    def bonk(self):
        self.bonks.append(Bonk())
        
    def bonk_amount(self):
        return len(self.bonks)
    
    def send_to_horny_jail(self, jail_time_seconds: int, jail_start: datetime = datetime.now()):
        self.horny_jail_until = jail_start + timedelta(seconds=jail_time_seconds)
        
    @staticmethod
    def get_id(discord_id: int, guild_id: int) -> int:
        digest = hashlib.shake_256(f"{discord_id}{guild_id}").digest(32) # collision free?
        return int.from_bytes(digest)

class Guild(Base):
    __tablename__ = "guilds"
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(String(1))
    users: Mapped[List["User"]] = relationship(
        secondary=user_guild, back_populates="guilds"
    )
