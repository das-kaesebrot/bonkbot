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
    id: Mapped[int] = mapped_column(primary_key=True)
    bonks: Mapped[int] = mapped_column()
    guilds: Mapped[List["Guild"]] = relationship(
        secondary=user_guild, back_populates="users"
    )


class Guild(Base):
    __tablename__ = "guilds"
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(String(1))
    users: Mapped[List["User"]] = relationship(
        secondary=user_guild, back_populates="guilds"
    )
